"""Serve the real built app/API with disposable in-memory evaluation fixtures.

Never connects to a database or the upstream evaluation site. Optional --snapshot
reads a local JSON export for a second smoke test against real saved records.
"""
import argparse
from datetime import date, datetime, timezone
import importlib
import json
from pathlib import Path
import re
import sys
from threading import Lock
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend import db_utils, result_service
from backend.instructor_names import recorded_instructor_names
from backend.period_logic import get_current_period
from backend.percentiles import build_benchmark


def fixtures():
    records = {}
    def add(code, section, period, title, name, counts):
        key = f'{code}.{section:02d}.{period}'
        quality = dict(zip(['Poor', 'Weak', 'Satisfactory', 'Good', 'Excellent'], counts))
        records[key] = {
            'course_name': title, 'instructor_name': name,
            'overall_quality_frequency': quality,
            'instructor_effectiveness_frequency': quality,
            'intellectual_challenge_frequency': quality,
            'ta_frequency': quality,
            'workload_frequency': dict(zip(['Much lighter', 'Somewhat lighter', 'Typical', 'Somewhat heavier', 'Much heavier'], counts)),
            'feedback_frequency': dict(zip(['Disagree strongly', 'Disagree somewhat', 'Neither agree nor disagree', 'Agree somewhat', 'Agree strongly'], counts)),
        }
    add('EN.601.315', 1, 'FA25', 'Databases', 'Jane Smith', [0, 1, 3, 20, 40])
    add('EN.601.415', 1, 'SP24', 'Databases', 'J. Smith', [1, 5, 20, 6, 2])
    add('EN.601.615', 1, 'FA25', 'Databases', 'Jane Smith & Alex Rivera', [0, 1, 3, 20, 40])
    add('EN.553.431', 1, 'SP20', 'Honors Introduction to Statistics', 'Jane Smith', [0, 0, 1, 10, 20])
    add('EN.553.431', 1, 'SP25', 'Honors Mathematical Statistics', 'Jane Smith', [0, 0, 1, 10, 20])
    add('EN.553.631', 1, 'SP25', 'Mathematical Statistics', 'Dana Lee', [4, 10, 20, 4, 2])
    add('EN.601.727', 1, 'FA24', 'Machine Programming', 'Dana Lee', [10, 20, 15, 3, 2])
    add('EN.601.727', 1, 'SP25', 'Machine Programming', 'Alex Rivera', [1, 1, 3, 10, 30])
    add('AS.180.101', 1, 'IN25', 'Introduction to Psychology', 'Alex Rivera', [1, 2, 8, 9, 15])
    add('AS.180.101', 1, 'SU24', 'Introduction to Psychology', 'Alex Rivera', [1, 2, 8, 9, 15])
    add('AS.180.101', 1, 'SP25', 'Introduction to Psychology', 'Dana Lee', [10, 10, 6, 3, 1])
    add('AS.050.203', 1, 'FA23', 'Cognitive Neuroscience: Exploring the Living Brain', 'Dana Lee', [0, 2, 10, 10, 20])
    add('AS.050.203', 1, 'SP25', 'Neuroscience: Cognitive', 'Dana Lee', [0, 2, 10, 10, 20])
    add('AS.100.200', 1, 'SP25', 'Smith Seminar', 'Robin Statistics', [0, 1, 2, 10, 20])
    add('AS.999.001', 1, 'SP20', 'Historical course', 'Old Teacher', [1, 1, 2, 10, 10])
    records['AS.999.002.01.SP25'] = {'course_name': 'Null Statistics Example', 'instructor_name': 'No Ratings'}
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--snapshot', type=Path)
    args = parser.parse_args()
    data = json.loads(args.snapshot.read_text()) if args.snapshot else fixtures()
    records = [(key, match[1], value) for key, value in data.items()
               if (match := re.match(r'^([A-Z]{2}\.\d{3}\.\d{3})', key))]
    codes = {code for _, code, _ in records}
    metadata = {code: {'last_period_gathered': get_current_period(), 'last_period_failed': False,
                       'updated_at': datetime(2026, 9, 1, tzinfo=timezone.utc), 'in_progress': False,
                       'data_updated_at': datetime(2026, 9, 1, tzinfo=timezone.utc),
                       'last_scrape_during_grace_period': None} for code in codes}
    if not args.snapshot:
        metadata['AS.050.203']['last_period_gathered'] = 'IN26'
        metadata['EN.553.431']['last_scrape_during_grace_period'] = date(2026, 8, 20)
        metadata['EN.601.315']['last_scrape_during_grace_period'] = date(2026, 8, 22)
    benchmark = build_benchmark(records)
    active = set()
    mutex = Lock()

    def no_database(*args, **kwargs):
        raise RuntimeError('The fixture server cannot connect to a database.')
    db_utils.get_db_connection = no_database
    db_utils.get_records_for_courses = lambda selected: [r for r in records if r[1] in selected]
    db_utils.get_professor_records = lambda name: [r for r in records if name in recorded_instructor_names(r[2])]
    db_utils.get_refresh_metadata = lambda code: {**metadata.get(code, {'last_period_gathered': get_current_period()}), 'in_progress': code in active}
    db_utils.get_course_metadata = lambda code: metadata.get(code)

    def search_courses(query, limit=20, offset=0):
        matches = [r for r in records if query.lower() in r[2].get('course_name', '').lower()]
        seen, results = set(), []
        for key, code, record in sorted(matches):
            if code in seen:
                continue
            members = result_service.grouping_service.get_grouped_courses(code)
            seen.update(members)
            actual = sorted(set(members) & codes)
            results.append({'course_code': '/'.join(actual), 'primary_course': code, 'course_name': record['course_name'], 'group_courses': members})
        return {'results': results[offset:offset + limit], 'total_count': len(results)}

    def search_professors(query, limit=20, offset=0):
        names = sorted({name for _, _, record in records for name in recorded_instructor_names(record) if query.lower() in name.lower()})
        return {'results': [{'type': 'professor', 'name': name} for name in names[offset:offset + limit]], 'total_count': len(names)}

    def check_course(code, **kwargs):
        with mutex:
            if code in active:
                return {'success': False, 'in_progress': True}
            active.add(code)
        try:
            time.sleep(3)
            changed = not args.snapshot and code == 'AS.050.203' and metadata[code]['last_period_gathered'] != get_current_period()
            if changed:
                previous = next(r[2] for r in records if r[1] == code)
                records.append((f'{code}.01.SU26', code, {**previous, 'course_name': 'Neuroscience: Cognitive', 'overall_quality_frequency': {'Good': 3, 'Excellent': 20}}))
            metadata.setdefault(code, {}).update(last_period_gathered=get_current_period(), last_period_failed=False,
                last_scrape_during_grace_period=None, updated_at=datetime.now(timezone.utc))
            return {'success': True, 'new_data_found': changed}
        finally:
            with mutex:
                active.remove(code)

    result_service.scrape_course_data_core = check_course
    api = importlib.import_module('backend.app')
    api.find_courses_by_name_with_details = search_courses
    api.find_professors_by_name_db = search_professors
    api.get_percentile_benchmark = lambda: benchmark
    api.app.static_folder = str(ROOT / 'frontend' / 'build')
    api.app.add_url_rule('/__fixture__', 'fixture_marker', lambda: {'fixture_server': True, 'synthetic': not bool(args.snapshot)})
    api.app.add_url_rule('/_vercel/insights/script.js', 'local_analytics_stub', lambda: ('', 200, {'Content-Type': 'application/javascript'}))
    print('LOCAL FIXTURES ONLY: database and upstream network calls disabled.', flush=True)
    api.app.run(host='127.0.0.1', port=args.port, threaded=True, use_reloader=False)


if __name__ == '__main__':
    main()
