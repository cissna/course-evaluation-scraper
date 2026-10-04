"""Explicit offline/maintenance command. Never invoked by an HTTP request."""
import argparse
import json
from pathlib import Path
import re
from .percentiles import build_benchmark


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path, help='Local JSON evaluation export (no DB connection).')
    source.add_argument('--database', action='store_true', help='Read all evaluations from DATABASE_URL.')
    parser.add_argument('--output', type=Path, help='Write the benchmark JSON to this path.')
    parser.add_argument('--write-store', action='store_true', help='Explicitly replace the DB benchmark. Requires --database.')
    args = parser.parse_args()
    if args.write_store and not args.database:
        parser.error('--write-store requires --database; local exports cannot silently overwrite the live benchmark.')
    if not args.output and not args.write_store:
        parser.error('Specify --output or --write-store.')
    if args.input:
        data = json.loads(args.input.read_text())
        records = [(key, match[1], record) for key, record in data.items()
                   if (match := re.match(r'^([A-Z]{2}\.\d{3}\.\d{3})', key))]
    else:
        from .db_utils import get_all_evaluation_records
        records = get_all_evaluation_records()
    benchmark = build_benchmark(records)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(benchmark, indent=2) + '\n')
    if args.write_store:
        from .db_utils import save_percentile_benchmark
        save_percentile_benchmark(benchmark)
    print(json.dumps({'years': benchmark['years'], 'courses_by_metric': {
        key: metric['course_count'] for key, metric in benchmark['metrics'].items()
    }, 'skipped_records': benchmark['skipped_records']}))


if __name__ == '__main__':
    main()
