"""Read saved evaluations without starting a scrape or expanding professor scope."""
from . import db_utils
from .analysis import extract_course_metadata
from .course_grouping_service import CourseGroupingService
from .instructor_names import recorded_instructor_name
from .period_logic import get_current_period, is_course_up_to_date
from .workflow_helpers import scrape_course_data_core

grouping_service = CourseGroupingService()


def iso(value):
    return value.isoformat() if hasattr(value, 'isoformat') else value


def course_refresh_status(code):
    metadata = db_utils.get_refresh_metadata(code) or {}
    return {
        'course_code': code,
        'current_period': get_current_period(),
        'in_progress': bool(metadata.get('in_progress')),
        'needs_refresh': not is_course_up_to_date(metadata.get('last_period_gathered'), metadata),
        'needs_warning': bool(metadata.get('last_scrape_during_grace_period')),
        'last_scrape_date': iso(metadata.get('last_scrape_during_grace_period') or metadata.get('updated_at')),
        'last_updated': iso(metadata.get('updated_at')),
        'data_revision': iso(metadata.get('data_updated_at')),
        'last_period_failed': bool(metadata.get('last_period_failed')),
    }


def enrich_records(records):
    instances = {}
    for key, code, data in records:
        if not isinstance(data, dict):
            continue
        members = grouping_service.get_group_info(code).get('courses') or [code]
        instances[key] = {
            **data,
            'course_code': code,
            'source_evaluation_id': key,
            'instructor_name': recorded_instructor_name(data),
            'course_group_id': '|'.join(sorted(members)),
        }
    # Display only the codes that contribute to this result, but retain stable
    # group identity from the existing grouping service.
    labels = {}
    for record in instances.values():
        labels.setdefault(record['course_group_id'], set()).add(record['course_code'])
    for record in instances.values():
        record['course_group'] = '/'.join(sorted(labels[record['course_group_id']]))
    return instances


def cached_course_result(code):
    info = grouping_service.get_group_info(code)
    codes = info.get('courses') or [code]
    instances = enrich_records(db_utils.get_records_for_courses(codes))
    actual_codes = sorted({record['course_code'] for record in instances.values()})
    names = {key: record['course_name'] for key, record in instances.items() if record.get('course_name')}
    metadata = extract_course_metadata(names, code, {}, primary_course_code=code,
                                       primary_course_has_no_data=code not in actual_codes)
    metadata['result_type'] = 'course'
    return {
        'raw_data': {
            'instances': instances,
            'metadata': metadata,
            'grouping_metadata': {
                'grouped_courses': actual_codes,
                'group_description': info.get('description', ''),
                'is_grouped': len(actual_codes) > 1,
            },
        },
        'refresh': {'courses': [course_refresh_status(member) for member in codes]},
    }


def cached_professor_result(name):
    # Do not fetch grouped courses and accidentally include their other teachers.
    records = [r for r in db_utils.get_professor_records(name)
               if isinstance(r[2], dict) and name == recorded_instructor_name(r[2])]
    instances = enrich_records(records)
    codes = sorted({record['course_code'] for record in instances.values()})
    # Historical title separation stays distinct from actual course separation.
    names_by_code = {}
    for record in instances.values():
        if record.get('course_name'):
            names_by_code.setdefault(record['course_code'], set()).add(record['course_name'])
    return {
        'raw_data': {
            'instances': instances,
            'metadata': {
                'result_type': 'professor', 'professor_name': name, 'current_name': name,
                'former_names': [], 'has_former_names': any(len(names) > 1 for names in names_by_code.values()),
            },
            'grouping_metadata': {'grouped_courses': codes, 'is_grouped': False},
        },
        'refresh': {'courses': [course_refresh_status(code) for code in codes]},
    }


def refresh_course(code, force=False):
    before = course_refresh_status(code)
    if before['in_progress']:
        return {**before, 'state': 'in_progress'}, 202
    if not force and not before['needs_refresh']:
        return {**before, 'state': 'complete', 'new_data_found': False}, 200
    result = scrape_course_data_core(code, skip_grace_period_logic=force)
    if result.get('in_progress'):
        return {**course_refresh_status(code), 'state': 'in_progress'}, 202
    status = course_refresh_status(code)
    if not result.get('success'):
        return {**status, 'state': 'failed', 'error': result.get('error', 'Unable to check for new evaluations.')}, 500
    return {**status, 'state': 'complete', 'new_data_found': bool(result.get('new_data_found'))}, 200
