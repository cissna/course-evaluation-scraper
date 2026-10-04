"""Build a fixed, all-department distribution of logical course averages."""
from collections import defaultdict
from datetime import datetime, timezone
import math
import re
from .course_grouping_service import CourseGroupingService

QUALITY = {'Poor': 1, 'Weak': 2, 'Satisfactory': 3, 'Good': 4, 'Excellent': 5}
METRICS = {
    'overall_quality': QUALITY,
    'instructor_effectiveness': QUALITY,
    'intellectual_challenge': QUALITY,
    'workload': {'Much lighter': 1, 'Somewhat lighter': 2, 'Typical': 3, 'Somewhat heavier': 4, 'Much heavier': 5},
    'feedback_frequency': {'Disagree strongly': 1, 'Disagree somewhat': 2, 'Neither agree nor disagree': 3, 'Agree somewhat': 4, 'Agree strongly': 5},
    'ta_frequency': QUALITY,
}
PERIOD = re.compile(r'\.(?:IN|SP|SU|FA)\.?(\d{2})$')


def build_benchmark(records, generated_at=None):
    service = CourseGroupingService()
    codes = {code for _, code, record in records if isinstance(record, dict)}
    groups = {code: tuple(sorted(set(service.get_group_info(code).get('courses') or [code]) & codes)) for code in codes}
    memberships = {}
    for members in groups.values():
        for code in members:
            if code in memberships and memberships[code] != members:
                raise ValueError(f'Overlapping existing course groups for {code}; review before building a benchmark.')
            memberships[code] = members
    totals = {metric: defaultdict(lambda: [0, 0]) for metric in METRICS}
    years = set()
    skipped = 0
    for key, code, record in records:
        period = PERIOD.search(key)
        if not isinstance(record, dict) or not period:
            skipped += 1
            continue
        contributed = False
        for metric, mapping in METRICS.items():
            field = metric if metric.endswith('_frequency') else metric + '_frequency'
            for label, count in (record.get(field) or {}).items():
                if label not in mapping or not isinstance(count, (int, float)) or isinstance(count, bool):
                    continue
                if not math.isfinite(count) or count <= 0 or count != int(count):
                    continue
                totals[metric][groups[code]][0] += mapping[label] * count
                totals[metric][groups[code]][1] += count
                contributed = True
        if contributed:
            years.add(2000 + int(period[1]))
    return {
        'version': 1,
        'generated_at': generated_at or datetime.now(timezone.utc).isoformat(),
        'population': 'All logical course groups in the database, all available years; one response-weighted mean per group.',
        'refresh_schedule': 'After every regular bulk scrape/import, at least monthly.',
        'ranking': 'midrank',
        'years': sorted(years),
        'year_coverage': f'{min(years)}–{max(years)}' if years else 'Unavailable',
        'skipped_records': skipped,
        'metrics': {
            metric: {'scores': sorted(total / n for total, n in by_group.values() if n > 0),
                     'course_count': sum(n > 0 for _, n in by_group.values())}
            for metric, by_group in totals.items()
        },
    }
