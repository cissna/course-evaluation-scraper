import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_INPUT_PATH = SCRIPT_DIR / "course_prefixes.txt"

load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(REPO_ROOT))

from backend.course_grouping_service import CourseGroupingService


STAT_MAPPINGS = {
    "overall_quality_frequency": {
        "Poor": 1,
        "Weak": 2,
        "Satisfactory": 3,
        "Good": 4,
        "Excellent": 5,
    },
    "workload_frequency": {
        "Much lighter": 1,
        "Somewhat lighter": 2,
        "Typical": 3,
        "Somewhat heavier": 4,
        "Much heavier": 5,
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Find courses matching line-separated course-code prefixes and rank "
            "them by lowest workload, while requiring a minimum overall-quality N."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"Path to the line-separated prefix file. Default: {DEFAULT_INPUT_PATH}",
    )
    parser.add_argument(
        "--min-n",
        type=int,
        default=40,
        help="Minimum overall-quality N required for a course group to appear.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of results to print.",
    )
    return parser.parse_args()


def load_prefixes(input_path: Path):
    if not input_path.exists():
        raise FileNotFoundError(f"Prefix file not found: {input_path}")

    prefixes = []
    seen = set()

    for raw_line in input_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        normalized = line.rstrip(".").upper()
        if not re.fullmatch(r"[A-Z]{2,}\.\d{3}", normalized):
            raise ValueError(
                f"Invalid prefix '{line}'. Expected values like 'AS.200' or 'EN.553'."
            )

        if normalized not in seen:
            prefixes.append(normalized)
            seen.add(normalized)

    if not prefixes:
        raise ValueError(
            f"No prefixes found in {input_path}. Add one prefix per line, like AS.200"
        )

    return prefixes


def calculate_detailed_statistics(frequency_dict, value_mapping):
    if not frequency_dict:
        return {"mean": None, "std": None, "n": 0}

    total_responses = 0
    weighted_sum = 0
    data_points = []

    for response_text, count in frequency_dict.items():
        if response_text not in value_mapping or count <= 0:
            continue

        value = value_mapping[response_text]
        total_responses += count
        weighted_sum += count * value
        data_points.extend([value] * count)

    if total_responses == 0:
        return {"mean": None, "std": None, "n": 0}

    mean = weighted_sum / total_responses

    if total_responses == 1:
        std = 0.0
    else:
        variance = sum((point - mean) ** 2 for point in data_points) / (total_responses - 1)
        std = variance ** 0.5

    return {"mean": round(mean, 2), "std": round(std, 2), "n": total_responses}


def parse_semester_year(instance_key):
    match = re.search(r"\.((?:IN|SP|SU|FA))(\d{2})$", instance_key)
    if not match:
        return (0, 0)

    semester, year = match.groups()
    semester_order = {"IN": 0, "SP": 1, "SU": 2, "FA": 3}
    return (2000 + int(year), semester_order.get(semester, 0))


def coerce_course_data(data):
    if isinstance(data, dict):
        return data
    return json.loads(data)


def fetch_matching_course_codes(cur, prefixes):
    patterns = [f"{prefix}.%" for prefix in prefixes]
    cur.execute(
        """
        SELECT DISTINCT course_code
        FROM courses
        WHERE course_code LIKE ANY(%s)
        ORDER BY course_code
        """,
        (patterns,),
    )
    return [row[0] for row in cur.fetchall()]


def fetch_rows_for_course_codes(cur, course_codes):
    cur.execute(
        """
        SELECT instance_key, course_code, data
        FROM courses
        WHERE course_code = ANY(%s)
        ORDER BY course_code, instance_key
        """,
        (course_codes,),
    )
    return cur.fetchall()


def get_db_connection_or_raise():
    try:
        from backend.db_utils import get_db_connection
    except ModuleNotFoundError as exc:
        if exc.name == "psycopg2":
            raise ModuleNotFoundError(
                "psycopg2 is required to query the database. Install the project "
                "Python requirements before running this script."
            ) from exc
        raise

    return get_db_connection


def build_group_results(prefixes, min_n):
    grouping_service = CourseGroupingService()
    get_db_connection = get_db_connection_or_raise()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            matching_course_codes = fetch_matching_course_codes(cur, prefixes)
            if not matching_course_codes:
                return {
                    "matching_course_codes": [],
                    "results": [],
                }

            unique_group_codes = set()
            seen_groups = set()

            for course_code in matching_course_codes:
                grouped_courses = tuple(grouping_service.get_grouped_courses(course_code))
                if grouped_courses in seen_groups:
                    continue

                seen_groups.add(grouped_courses)
                unique_group_codes.update(grouped_courses)

            rows = fetch_rows_for_course_codes(cur, sorted(unique_group_codes))

    matching_course_code_set = set(matching_course_codes)
    rows_by_course_code = defaultdict(list)
    for instance_key, course_code, data in rows:
        rows_by_course_code[course_code].append((instance_key, coerce_course_data(data)))

    results = []
    processed_groups = set()

    for course_code in matching_course_codes:
        grouped_courses = tuple(grouping_service.get_grouped_courses(course_code))
        if grouped_courses in processed_groups:
            continue

        processed_groups.add(grouped_courses)

        group_rows = []
        matched_course_codes = []
        for grouped_course_code in grouped_courses:
            if grouped_course_code in matching_course_code_set:
                matched_course_codes.append(grouped_course_code)
            for instance_key, data in rows_by_course_code.get(grouped_course_code, []):
                group_rows.append((instance_key, grouped_course_code, data))

        if not group_rows:
            continue

        aggregated_frequencies = {
            "overall_quality_frequency": defaultdict(int),
            "workload_frequency": defaultdict(int),
        }

        for _, _, data in group_rows:
            for stat_key in aggregated_frequencies:
                for label, count in data.get(stat_key, {}).items():
                    aggregated_frequencies[stat_key][label] += count

        overall_quality_stats = calculate_detailed_statistics(
            aggregated_frequencies["overall_quality_frequency"],
            STAT_MAPPINGS["overall_quality_frequency"],
        )
        workload_stats = calculate_detailed_statistics(
            aggregated_frequencies["workload_frequency"],
            STAT_MAPPINGS["workload_frequency"],
        )

        if overall_quality_stats["n"] <= min_n or workload_stats["mean"] is None:
            continue

        latest_instance_key, _, latest_data = max(group_rows, key=lambda row: parse_semester_year(row[0]))
        course_name = latest_data.get("course_name") or "(no course name found)"

        results.append(
            {
                "grouped_course_codes": list(grouped_courses),
                "matched_course_codes": matched_course_codes,
                "latest_instance_key": latest_instance_key,
                "course_name": course_name,
                "overall_quality_mean": overall_quality_stats["mean"],
                "overall_quality_n": overall_quality_stats["n"],
                "workload_mean": workload_stats["mean"],
                "workload_n": workload_stats["n"],
            }
        )

    results.sort(
        key=lambda item: (
            item["workload_mean"],
            -(item["overall_quality_mean"] or 0),
            -item["overall_quality_n"],
            "/".join(item["grouped_course_codes"]),
        )
    )

    return {
        "matching_course_codes": matching_course_codes,
        "results": results,
    }


def format_group_label(grouped_course_codes):
    return grouped_course_codes[0] if len(grouped_course_codes) == 1 else "/".join(grouped_course_codes)


def main():
    args = parse_args()
    try:
        prefixes = load_prefixes(args.input)
        output = build_group_results(prefixes, args.min_n)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    matching_course_codes = output["matching_course_codes"]
    results = output["results"]
    total_result_count = len(results)

    if args.limit is not None:
        results = results[: args.limit]

    print(f"Loaded {len(prefixes)} prefixes from {args.input}")
    print(f"Matching prefixes: {', '.join(prefixes)}")
    print(f"Found {len(matching_course_codes)} matching course codes in the database.")
    if args.limit is None or len(results) == total_result_count:
        print(
            f"Found {total_result_count} course groups with overall-quality N > {args.min_n}, "
            "sorted by lowest workload."
        )
    else:
        print(
            f"Found {total_result_count} course groups with overall-quality N > {args.min_n}, "
            f"printing the first {len(results)} sorted by lowest workload."
        )

    if not results:
        return

    print("")
    for index, result in enumerate(results, start=1):
        group_label = format_group_label(result["grouped_course_codes"])
        matched_label = ", ".join(result["matched_course_codes"])
        print(
            f"{index}. {group_label} | {result['course_name']}\n"
            f"   workload={result['workload_mean']} (n={result['workload_n']}), "
            f"overall_quality={result['overall_quality_mean']} (n={result['overall_quality_n']}), "
            f"latest_instance={result['latest_instance_key']}, matched={matched_label}"
        )


if __name__ == "__main__":
    main()
