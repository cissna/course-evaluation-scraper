"""Compare current percentiles with weights of responses / distinct terms offered.

    python3 one-time-scripts/analyze_size_weighted_percentiles.py
    python3 one-time-scripts/analyze_size_weighted_percentiles.py --database

Defaults to the repository's data.json and writes a report, charts, and CSV/JSON
results under overnight-review/size-weighted-percentiles. --database uses a
read-only transaction. Requires numpy and matplotlib (plus backend dependencies
for database input). This script never changes the app or its saved benchmark.

The primary weight is metric-specific n / all observed terms for the existing
course group, including summer and intersession. Sections/cross-listings in the
same term share a denominator entry. n counts valid evaluation answers, not
enrollment. Scores and course membership stay fixed; only percentile mass changes.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.course_grouping_service import CourseGroupingService
from backend.percentiles import build_benchmark, METRICS
from plot_workload_histogram import load_records

PERIOD = re.compile(r"\.(IN|SP|SU|FA)\.?(\d{2})$")
SEASONS = {"IN": 0, "SP": 1, "SU": 2, "FA": 3}
LABELS = {
    "overall_quality": "Overall Quality",
    "workload": "Workload",
    "instructor_effectiveness": "Instructor Effectiveness",
    "intellectual_challenge": "Intellectual Challenge",
    "feedback_frequency": "Helpful Feedback",
    "ta_frequency": "TA Quality",
}


def aggregate(records):
    service = CourseGroupingService()
    codes = {code for _, code, record in records if isinstance(record, dict)}
    memberships = {
        code: tuple(sorted(set(service.get_group_info(code).get("courses") or [code]) & codes))
        for code in codes
    }
    groups = {members: {"periods": set(), "reports": 0, "latest": (-1, -1, ""),
                        "name": "", "metrics": {}} for members in memberships.values()}
    # The production builder separately validates that these groups do not overlap.
    skipped = normalized = 0
    for key, code, record in records:
        period = PERIOD.search(key)
        if not isinstance(record, dict) or not period:
            skipped += 1
            continue
        season, short_year = period.groups()
        year = 2000 + int(short_year)
        term = season + short_year
        normalized += bool(re.search(r"\.(IN|SP|SU|FA)\.\d{2}$", key))
        group = groups[memberships[code]]
        group["periods"].add(term)
        group["reports"] += 1
        order = (year, SEASONS[season], key)
        if record.get("course_name") and order > group["latest"]:
            group["name"], group["latest"] = record["course_name"], order
        for metric, mapping in METRICS.items():
            field = metric if metric.endswith("_frequency") else metric + "_frequency"
            total = n = 0
            for label, count in (record.get(field) or {}).items():
                if label not in mapping or not isinstance(count, (int, float)) or isinstance(count, bool):
                    continue
                if not math.isfinite(count) or count <= 0 or count != int(count):
                    continue
                n += int(count)
                total += mapping[label] * int(count)
            if n:
                tally = group["metrics"].setdefault(metric, {"total": 0, "n": 0, "periods": set(), "reports": 0})
                tally["total"] += total
                tally["n"] += n
                tally["periods"].add(term)
                tally["reports"] += 1
    return groups, {"skipped_records": skipped, "normalized_period_keys": normalized}


def midrank_mapping(indices, weights):
    mass = np.bincount(indices, weights=weights, minlength=401)
    return np.clip(100 * (np.cumsum(mass) - mass / 2) / mass.sum(), 0, 100)


def percentage(mask):
    return float(100 * np.mean(mask)) if len(mask) else None


def compare(groups, reference):
    summaries, courses, mappings, sensitivity = [], [], [], []
    plot_data = {}
    for metric, label in LABELS.items():
        eligible = [(codes, group, group["metrics"][metric]) for codes, group in sorted(groups.items())
                    if metric in group["metrics"]]
        if not eligible:
            continue
        n = np.array([tally["n"] for _, _, tally in eligible])
        means = np.array([tally["total"] / tally["n"] for _, _, tally in eligible])
        periods = np.array([len(group["periods"]) for _, group, _ in eligible])
        covered_periods = np.array([len(tally["periods"]) for _, _, tally in eligible])
        indices = np.floor(means * 100 + 0.5).astype(int) - 100
        weights = n / periods
        equal_map = midrank_mapping(indices, np.ones(len(eligible)))
        weighted_map = midrank_mapping(indices, weights)
        # Check the full current lookup, not just percentiles at observed scores.
        current = reference["metrics"][metric]
        if current["course_count"] != len(eligible) or not np.allclose(equal_map, current["percentiles"], atol=1e-10, rtol=0):
            raise ValueError(f"Equal-course baseline does not match the app for {metric}.")
        if np.any(np.diff(weighted_map) < -1e-10):
            raise ValueError(f"Weighted mapping is not monotone for {metric}.")
        equal, weighted = equal_map[indices], weighted_map[indices]
        shifts = weighted - equal
        absolute = np.abs(shifts)
        upper = equal >= 95
        reliable = n >= 20
        summary = {
            "metric": metric, "label": label, "course_groups": len(eligible),
            "responses": int(n.sum()), "median_responses_per_term": float(np.median(weights)),
            "equal_course_mean": float(np.mean(means)),
            "size_weighted_mean": float(np.average(means, weights=weights)),
            "median_absolute_shift_pp": float(np.median(absolute)),
            "p95_absolute_shift_pp": float(np.quantile(absolute, 0.95)),
            "maximum_absolute_shift_pp": float(absolute.max()),
            "mean_signed_shift_pp": float(np.mean(shifts)),
            "percent_moving_at_least_1_pp": percentage(absolute >= 1),
            "percent_moving_at_least_5_pp": percentage(absolute >= 5),
            "percent_moving_at_least_10_pp": percentage(absolute >= 10),
            "percent_increasing_at_least_1_pp": percentage(shifts >= 1),
            "percent_decreasing_at_least_1_pp": percentage(shifts <= -1),
            "median_absolute_shift_n_at_least_20": float(np.median(absolute[reliable])) if reliable.any() else None,
            "median_signed_shift_original_top_5_percent": float(np.median(shifts[upper])) if upper.any() else None,
        }
        # Practical display thresholds, not statistical-significance tests.
        summary["noticeable_change_for_at_least_20_percent_of_courses"] = summary["percent_moving_at_least_5_pp"] >= 20
        summaries.append(summary)
        for cutoff in (90, 95, 99):
            before, after = equal >= cutoff, weighted >= cutoff
            summary[f"original_top_{100 - cutoff}_percent_count"] = int(before.sum())
            summary[f"weighted_top_{100 - cutoff}_percent_count"] = int(after.sum())
            summary[f"leaving_top_{100 - cutoff}_percent"] = int((before & ~after).sum())
            summary[f"entering_top_{100 - cutoff}_percent"] = int((~before & after).sum())
            summary[f"percent_of_original_top_{100 - cutoff}_leaving"] = percentage(~after[before])

        # Missing-answer sensitivity: primary policy counts every observed term,
        # even if that term has no valid answers to this particular question.
        covered_map = midrank_mapping(indices, n / covered_periods)
        missing_shift = np.abs(covered_map[indices] - weighted)
        sensitivity.append({
            "metric": metric, "groups_with_missing_metric_terms": int((periods != covered_periods).sum()),
            "median_change_using_only_answered_terms_pp": float(np.median(missing_shift)),
            "p95_change_using_only_answered_terms_pp": float(np.quantile(missing_shift, 0.95)),
            "maximum_change_using_only_answered_terms_pp": float(missing_shift.max()),
        })
        for i, (codes, group, tally) in enumerate(eligible):
            courses.append({
                "metric": metric, "course_codes": "/".join(codes), "course_name": group["name"],
                "mean_score": float(means[i]), "responses": int(n[i]),
                "distinct_terms": int(periods[i]), "terms_with_metric_answers": int(covered_periods[i]),
                "evaluation_reports": group["reports"], "average_responses_per_term": float(weights[i]),
                "equal_percentile": float(equal[i]), "size_weighted_percentile": float(weighted[i]),
                "change_pp": float(shifts[i]),
            })
        for i in range(401):
            mappings.append({"metric": metric, "score": (i + 100) / 100,
                             "equal_percentile": float(equal_map[i]),
                             "size_weighted_percentile": float(weighted_map[i]),
                             "change_pp": float(weighted_map[i] - equal_map[i])})
        occupied = np.unique(indices)
        plot_data[metric] = {"equal": equal_map[occupied], "change": (weighted_map - equal_map)[occupied],
                             "means": means, "weights": weights, "equal_map": equal_map, "weighted_map": weighted_map}
    return summaries, courses, mappings, sensitivity, plot_data


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def table(headers, rows):
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    return "\n".join(["| " + " | ".join(escape(value) for value in headers) + " |",
                       "| " + " | ".join(["---"] * len(headers)) + " |"] +
                      ["| " + " | ".join(escape(value) for value in row) + " |" for row in rows])


def write_report(out, provenance, summaries, courses, mappings, sensitivity):
    summary_rows = [[row["label"], f'{row["course_groups"]:,}', f'{row["median_absolute_shift_pp"]:.2f}',
                     f'{row["p95_absolute_shift_pp"]:.2f}', f'{row["percent_moving_at_least_5_pp"]:.1f}%',
                     f'{row["percent_moving_at_least_10_pp"]:.1f}%', f'{row["mean_signed_shift_pp"]:+.2f}']
                    for row in summaries]
    workload_lookup = {row["score"]: row for row in mappings if row["metric"] == "workload"}
    fixed_rows = []
    for score in (2.5, 3.0, 3.5, 4.0, 4.5, 4.68, 4.83, 4.90, 5.0):
        if score not in workload_lookup:
            continue
        row = workload_lookup[score]
        equal_tail, weighted_tail = 100 - row["equal_percentile"], 100 - row["size_weighted_percentile"]
        ratio = f"{weighted_tail / equal_tail:.2f}×" if equal_tail > 0 else "N/A"
        fixed_rows.append([f"{score:.2f}", f'{row["equal_percentile"]:.3f}',
                           f'{row["size_weighted_percentile"]:.3f}', f'{row["change_pp"]:+.3f}', ratio])
    tail_rows = [[row["label"], row["original_top_5_percent_count"], row["weighted_top_5_percent_count"],
                 row["leaving_top_5_percent"], row["entering_top_5_percent"],
                 f'{row["median_signed_shift_original_top_5_percent"]:+.2f}' if row["median_signed_shift_original_top_5_percent"] is not None else "N/A"]
                for row in summaries]
    # Pick one representative per lookup bucket so tied scores do not repeat
    # the same example. Among ties, show the course with the most responses.
    examples_by_bucket = {}
    for row in sorted((row for row in courses if row["metric"] == "workload"), key=lambda row: -row["responses"]):
        examples_by_bucket.setdefault(math.floor(row["mean_score"] * 100 + 0.5), row)
    largest = sorted(examples_by_bucket.values(), key=lambda row: -abs(row["change_pp"]))[:5]
    examples = [[row["course_codes"], row["course_name"], f'{row["mean_score"]:.3f}',
                 f'{row["average_responses_per_term"]:.1f}', f'{row["equal_percentile"]:.2f}',
                 f'{row["size_weighted_percentile"]:.2f}', f'{row["change_pp"]:+.2f}'] for row in largest]
    sensitivity_rows = [[LABELS[row["metric"]], row["groups_with_missing_metric_terms"],
                         f'{row["median_change_using_only_answered_terms_pp"]:.3f}',
                         f'{row["maximum_change_using_only_answered_terms_pp"]:.3f}'] for row in sensitivity]
    useful = [row["label"] for row in summaries if row["noticeable_change_for_at_least_20_percent_of_courses"]]
    ta_endpoint = next((row for row in mappings if row["metric"] == "ta_frequency" and row["score"] == 5), None)
    ta_note = ""
    if ta_endpoint:
        ta_note = (f"TA Quality has many tied 5.00 averages: its highest current percentile is {ta_endpoint['equal_percentile']:.2f}, "
                   f"compared with {ta_endpoint['size_weighted_percentile']:.2f} after weighting. "
                   "Midranks place every course in that top bucket at the same percentile; this explains the unusual boundary counts.")
    writing = next((row for row in courses if row["metric"] == "workload" and row["course_codes"] == "AS.004.101"), None)
    section_note = ""
    if writing:
        section_note = (f"For a concrete example, {writing['course_name']} has {writing['responses']:,} workload answers across "
                        f"{writing['evaluation_reports']} section/term reports in {writing['distinct_terms']} distinct terms. "
                        f"Your formula gives it weight {writing['average_responses_per_term']:.1f}; dividing by reports instead would give "
                        f"{writing['responses'] / writing['evaluation_reports']:.1f}. The primary analysis keeps your term-based formula. "
                        "This is why a future control should clarify that it weights courses by average total responses per term, across sections.")
    sections = [
        "# Average-class-size weighting: one-time analysis",
        f"Source: {provenance['source']}. {provenance['source_records']:,} reports; {provenance['year_coverage']}. Generated {provenance['generated_at']}.",
        "## What changes",
        "Course means and ordering stay fixed. Only the reference distribution changes. The current lookup gives each existing course group one vote; the proposed lookup gives it `valid metric responses / distinct observed terms`. All years, summer, and intersession are included. Sections and grouped codes offered in the same term share one denominator entry.",
        "The stored data contains evaluation answers, not enrollment. This estimates average responses per term across a course's sections, not literal average section enrollment. Different response rates can affect the weights, and each metric has its own valid-answer count. The calculation uses the owner's formula as requested; it does not establish which population is inherently correct.",
        section_note,
        "Both versions use the app's 1.00–5.00 hundredth-score buckets and midranks: percentile = 100 × (weight below + half the tied weight) / total weight. The equal-course lookup was checked against all 401 production benchmark values for each metric. No score, grouping rule, application code, or saved benchmark was changed.",
        "## How much is enough?",
        "For this review, 5 percentile points is a noticeable display change and 10 is large. I would consider an optional mode worth discussing if at least 20% of courses move by 5 points. These are explicit product judgments, not significance tests or universal cutoffs. A change below one point is usually small at the current display precision. In an extreme tail, also compare the remaining upper-tail mass: 99.9 to 99.5 is only 0.4 points but five times the tail mass.",
        "Metrics meeting the 20%-of-courses / 5-point criterion: " + (", ".join(useful) if useful else "none") + ".",
        "## Changes across all course groups",
        "Each row below describes the courses equally, so a large class does not also get extra weight when reporting how many courses change. Changes are weighted minus current, in percentile points (pp). Positive means a higher displayed percentile.",
        table(["Metric", "Groups", "Median |change|", "95th pct |change|", "Move ≥5 pp", "Move ≥10 pp", "Mean signed change"], summary_rows),
        "![Percentile shifts](percentile_changes.png)",
        "## Workload, including the upper tail",
        "The tail ratio is `(100 − weighted percentile) / (100 − current percentile)`. It includes half the tied mass, matching the app's midrank convention; it is not strictly the fraction of courses above the score.",
        table(["Workload score", "Current percentile", "Weighted percentile", "Change (pp)", "Upper-tail mass ratio"], fixed_rows),
        "![Workload distributions and upper-tail percentiles](workload_weighting.png)",
        "## Crossing the 95th-percentile boundary",
        "The weighted top 5% means 5% of average-response mass, so it need not contain 5% of distinct courses. Crossing a cutoff is a useful display consequence, not an independent reordering of courses.",
        table(["Metric", "Current count", "Weighted count", "Leave ≥95", "Enter ≥95", "Median change among original ≥95"], tail_rows),
        ta_note,
        "## Largest workload changes",
        "One representative per hundredth-score bucket, choosing the course with the most responses among ties.",
        table(["Course codes", "Latest recorded title", "Score", "Responses / term", "Current", "Weighted", "Change (pp)"], examples),
        "## Missing-answer sensitivity",
        "The requested primary denominator counts all observed terms, including those without valid answers to a metric. As a sensitivity check only, dividing by terms that do contain metric answers produces the following differences from the primary weighted result. Courses and scores are unchanged.",
        table(["Metric", "Groups with missing-answer terms", "Median difference (pp)", "Maximum difference (pp)"], sensitivity_rows),
        "## Files and limits",
        "`summary.csv` / `summary.json` include shift quantiles, direction, ≥1/5/10-point rates, the ≥20-response cohort, and 90/95/99-boundary changes. `course_percentiles.csv` contains every course's score, counts, weight, old/new percentile, and difference. `score_mappings.csv` contains both complete lookup tables. `missing_answer_sensitivity.csv` contains the denominator sensitivity.",
        "This is descriptive analysis of the selected stored data. It does not measure enrollment, fill in unrecorded terms, or correct response-selection effects. Scores are the existing all-history course means; past or filtered section scores can use the exported lookup tables but were not individually reanalyzed. Existing course groups and metric eligibility are preserved.",
        f"Skipped records: {provenance['skipped_records']}. Normalized optional dots in {provenance['normalized_period_keys']} period keys for this analysis, as the percentile builder already does. Source files remain unchanged.",
    ]
    (out / "REPORT.md").write_text("\n\n".join(sections) + "\n")


def plot(out, summaries, plot_data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(3, 2, figsize=(11.5, 10), sharex=True, sharey=True)
    lower = min(0, min(float(values["change"].min()) for values in plot_data.values())) - 1
    upper = max(0, max(float(values["change"].max()) for values in plot_data.values())) + 5
    for ax, summary in zip(axes.flat, summaries):
        metric = summary["metric"]
        values = plot_data[metric]
        color = "#C9512D" if metric == "workload" else "#287A99"
        ax.axhline(0, color="#64748B", linewidth=0.9, linestyle="--")
        ax.plot(values["equal"], values["change"], color=color, linewidth=2)
        ax.fill_between(values["equal"], 0, values["change"], color=color, alpha=0.10)
        ax.set_title(summary["label"], loc="left", fontweight="bold")
        ax.text(0.02, 0.95, f'Median |shift| {summary["median_absolute_shift_pp"]:.1f} pp; '
                f'{summary["percent_moving_at_least_5_pp"]:.0f}% shift ≥5 pp',
                transform=ax.transAxes, va="top", fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_ylim(lower, upper)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.grid(axis="y", alpha=0.15)
    for ax in axes[-1]:
        ax.set_xlabel("Current percentile (equal course weights)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Weighted − current percentile (points)")
    fig.suptitle("How average-class-size weighting changes percentiles", x=0.09, ha="left", fontsize=17, fontweight="bold", y=0.98)
    fig.text(0.09, 0.937, "Weight = valid answers ÷ distinct terms offered; all years, summer, and intersession included.", fontsize=10, color="#475569")
    fig.text(0.09, 0.025, "Positive values increase the displayed percentile. Scores and course ordering are unchanged.\nClass size is estimated from evaluation responses, not enrollment.", fontsize=9, color="#475569")
    fig.subplots_adjust(left=0.09, right=0.98, top=0.875, bottom=0.11, hspace=0.38, wspace=0.20)
    fig.savefig(out / "percentile_changes.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    if "workload" not in plot_data:
        return
    values = plot_data["workload"]
    fig, (hist, tail) = plt.subplots(1, 2, figsize=(12, 5.5))
    bins = np.linspace(1, 5, 41)
    hist.hist(values["means"], bins=bins, weights=np.ones(len(values["means"])) / len(values["means"]) * 100,
              color="#287A99", alpha=0.30, label="Equal course weights")
    hist.hist(values["means"], bins=bins, weights=values["weights"] / values["weights"].sum() * 100,
              histtype="step", color="#C9512D", linewidth=2, label="Average responses / term")
    hist.set(xlabel="Average workload (1–5)", ylabel="Percent of reference mass per bin", xlim=(1, 5))
    hist.set_title("Reference distributions", loc="left", fontweight="bold")
    hist.legend(frameon=False, fontsize=9)
    scores = np.arange(401) / 100 + 1
    tail.plot(scores, values["equal_map"], color="#287A99", label="Equal course weights", linewidth=2)
    tail.plot(scores, values["weighted_map"], color="#C9512D", label="Average responses / term", linewidth=2)
    starts = [scores[np.flatnonzero(values[key] >= 90)[0]] for key in ("equal_map", "weighted_map")
              if np.any(values[key] >= 90)]
    tail.set(xlim=(max(1, min(starts, default=4) - 0.05), 5), ylim=(89, 100.2),
             xlabel="Average workload (1–5)", ylabel="Percentile")
    tail.set_title("Upper-tail workload percentiles", loc="left", fontweight="bold")
    for ax in (hist, tail):
        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=0.15)
    fig.suptitle("Workload: equal-course vs average-class-size weights", x=0.08, ha="left", fontsize=17, fontweight="bold", y=0.98)
    fig.text(0.08, 0.045, "Both curves use the same course scores. Weights use evaluation answers per term, not enrollment.\nThe right panel uses the same hundredth-score buckets and tie handling as the app.", fontsize=9, color="#475569")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.83, bottom=0.24, wspace=0.25)
    fig.savefig(out / "workload_weighting.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, default=ROOT / "data.json")
    source.add_argument("--database", action="store_true", help="Read DATABASE_URL without modifying the database.")
    parser.add_argument("--output", type=Path, default=ROOT / "overnight-review" / "size-weighted-percentiles", help="Output directory.")
    args = parser.parse_args()
    records = load_records(args)
    reference = build_benchmark(records)
    groups, coverage = aggregate(records)
    summaries, courses, mappings, sensitivity, plot_data = compare(groups, reference)
    if not summaries:
        parser.error("No valid metric responses found.")
    args.output.mkdir(parents=True, exist_ok=True)
    provenance = {
        "source": "Database queried in a read-only transaction" if args.database else str(args.input.resolve()),
        "source_sha256": None if args.database else hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "source_records": len(records), "year_coverage": reference["year_coverage"],
        "generated_at": datetime.now(timezone.utc).isoformat(), **coverage,
    }
    write_csv(args.output / "summary.csv", summaries)
    write_csv(args.output / "course_percentiles.csv", courses)
    write_csv(args.output / "score_mappings.csv", mappings)
    write_csv(args.output / "missing_answer_sensitivity.csv", sensitivity)
    (args.output / "summary.json").write_text(json.dumps({"provenance": provenance, "metrics": summaries,
                                                          "missing_answer_sensitivity": sensitivity}, indent=2) + "\n")
    plot(args.output, summaries, plot_data)
    write_report(args.output, provenance, summaries, courses, mappings, sensitivity)
    for row in summaries:
        print(f'{row["label"]}: median absolute shift {row["median_absolute_shift_pp"]:.2f} pp; '
              f'{row["percent_moving_at_least_5_pp"]:.1f}% move ≥5 pp; '
              f'mean signed shift {row["mean_signed_shift_pp"]:+.2f} pp')
    print(f"Report: {(args.output / 'REPORT.md').resolve()}")


if __name__ == "__main__":
    main()
