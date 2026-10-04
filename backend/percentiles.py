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
BENCHMARK_VERSION = 2
REBUILD_AFTER_EVALUATIONS = 100


def percentile_mapping(by_group):
    # Index 0 represents 1.00, index 400 represents 5.00. Only percentile
    # lookup uses rounded means; response statistics keep their full precision.
    counts = [0] * 401
    for total, n in by_group.values():
        if n > 0:
            counts[math.floor((total / n) * 100 + 0.5) - 100] += 1
    course_count = sum(counts)
    below = 0
    percentiles = []
    for tied in counts:
        percentiles.append(100 * (below + tied / 2) / course_count if course_count else None)
        below += tied
    return {'percentiles': percentiles, 'course_count': course_count}


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
        'version': BENCHMARK_VERSION,
        'generated_at': generated_at or datetime.now(timezone.utc).isoformat(),
        'population': 'All logical course groups in the database, all available years; one response-weighted mean per group.',
        'refresh_schedule': 'After 100 newly inserted evaluation reports, at the end of a scrape or the next benchmark request.',
        'ranking': 'midrank of course averages rounded to the nearest hundredth',
        'score_min': 1,
        'score_max': 5,
        'score_step': 0.01,
        'years': sorted(years),
        'year_coverage': f'{min(years)}–{max(years)}' if years else 'Unavailable',
        'skipped_records': skipped,
        'metrics': {
            metric: percentile_mapping(by_group)
            for metric, by_group in totals.items()
        },
    }
