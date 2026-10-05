"""Plot course workload averages with a matching normal curve.

Run from the repository root:
    python3 one-time-scripts/plot_workload_histogram.py
    python3 one-time-scripts/plot_workload_histogram.py --database --bins 60

Reads data.json by default; --database reads DATABASE_URL from the environment
or the repository's .env. Neither mode changes the database. Requires matplotlib
(python3 -m pip install matplotlib), plus backend dependencies for --database.

Each existing course group counts once, matching the percentile population.
Its average pools all valid workload responses across sections, instructors,
years, and seasons. Means retain full precision; the normal curve uses the
mean and sample standard deviation (n - 1) of these course-group averages.
"""

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import re
from statistics import mean, NormalDist, stdev
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.course_grouping_service import CourseGroupingService
from backend.percentiles import METRICS, PERIOD

COURSE_CODE = re.compile(r"^([A-Z]{2,}\.\d{3}\.\d{3})(?:\.|$)")


def load_records(args):
    if args.database:
        from backend.db_utils import get_db_connection

        with get_db_connection() as connection:
            connection.set_session(readonly=True)
            with connection.cursor() as cursor:
                cursor.execute("SELECT instance_key, course_code, data FROM courses")
                return cursor.fetchall()

    data = json.loads(args.input.read_text())
    return [(key, match[1], record) for key, record in data.items()
            if (match := COURSE_CODE.match(key))]


def workload_averages(records):
    service = CourseGroupingService()
    codes = {code for _, code, record in records if isinstance(record, dict)}
    groups = {
        code: tuple(sorted(set(service.get_group_info(code).get("courses") or [code]) & codes))
        for code in codes
    }
    memberships = {}
    for members in groups.values():
        for code in members:
            if code in memberships and memberships[code] != members:
                raise ValueError(f"Overlapping existing course groups for {code}.")
            memberships[code] = members

    totals = defaultdict(lambda: [0, 0])
    years = set()
    included_reports = 0
    for key, code, record in records:
        period = PERIOD.search(key)
        if not isinstance(record, dict) or not period:
            continue
        score_sum = responses = 0
        for label, count in (record.get("workload_frequency") or {}).items():
            if label not in METRICS["workload"] or not isinstance(count, (int, float)) or isinstance(count, bool):
                continue
            if not math.isfinite(count) or count <= 0 or count != int(count):
                continue
            score_sum += METRICS["workload"][label] * int(count)
            responses += int(count)
        if responses:
            totals[groups[code]][0] += score_sum
            totals[groups[code]][1] += responses
            years.add(2000 + int(period[1]))
            included_reports += 1

    scores = [total / count for total, count in totals.values()]
    return scores, years, included_reports, sum(count for _, count in totals.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, default=ROOT / "data.json", help="Evaluation JSON export (default: repository data.json).")
    source.add_argument("--database", action="store_true", help="Read current evaluations from DATABASE_URL in a read-only transaction.")
    parser.add_argument("--bins", type=int, default=40, help="Equal-width bins across the 1–5 scale (default: 40).")
    parser.add_argument("--output", type=Path, default=Path("workload_histogram.png"), help="Output image path; .png, .pdf, or .svg (default: workload_histogram.png).")
    args = parser.parse_args()
    if args.bins < 1:
        parser.error("--bins must be positive")

    records = load_records(args)
    scores, years, reports, responses = workload_averages(records)
    if len(scores) < 2:
        parser.error("At least two course groups with workload responses are needed.")
    average, sd = mean(scores), stdev(scores)
    if sd == 0:
        parser.error("All course averages are identical; a normal curve needs a nonzero SD.")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(11, 6.5))
    _, edges, _ = ax.hist(scores, bins=args.bins, range=(1, 5), color="#5790AA",
                          edgecolor="white", linewidth=0.6, label="Course averages")
    # A probability density must be scaled by N × bin width to overlay counts.
    normal = NormalDist(average, sd)
    scale = len(scores) * (edges[1] - edges[0])
    x = [1 + 4 * i / 1000 for i in range(1001)]
    ax.plot(x, [scale * normal.pdf(value) for value in x], color="#C9512D",
            linewidth=2.5, label="Normal with matching mean and SD")
    ax.set(xlim=(1, 5), ylim=(0, None), ylabel="Number of course groups",
           xlabel="Average workload (1 = much lighter, 3 = typical, 5 = much heavier)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    coverage = f"{min(years)}–{max(years)}"
    source_label = "Database at run time" if args.database else f"Local export: {args.input.name}"
    fig.suptitle("Workload across all courses", x=0.09, y=0.96, ha="left", fontsize=21, fontweight="bold")
    fig.text(0.09, 0.89, f"{len(scores):,} course groups  ·  {coverage}  ·  Mean {average:.3f}  ·  Sample SD {sd:.3f}", color="#475569")
    fig.text(0.09, 0.065, "Each course group counts equally; its average is weighted by student response counts.\n"
             f"{source_label} · all available years and seasons · normal curve scaled to histogram counts.",
             fontsize=9, color="#475569", linespacing=1.6)
    fig.subplots_adjust(left=0.09, right=0.975, bottom=0.23, top=0.84)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"Source: {source_label}")
    print(f"Course groups: {len(scores):,}; years: {coverage}")
    print(f"Workload responses: {responses:,} in {reports:,} of {len(records):,} reports")
    print(f"Mean: {average:.6f}; sample SD: {sd:.6f}")
    print(f"Saved: {args.output.resolve()}")


if __name__ == "__main__":
    main()
