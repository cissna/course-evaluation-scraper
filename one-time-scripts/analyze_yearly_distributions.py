"""Describe historical score distributions from a local evaluation JSON export.

Read-only with respect to the application and database. Requires numpy, pandas,
and matplotlib. Each benchmark observation is a course-group mean, calculated
from response totals (not an average of section or annual means).
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.course_grouping_service import CourseGroupingService


QUALITY = {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
WORKLOAD = {
    "Much lighter": 1, "Somewhat lighter": 2, "Typical": 3,
    "Somewhat heavier": 4, "Much heavier": 5,
}
FEEDBACK = {
    "Disagree strongly": 1, "Disagree somewhat": 2,
    "Neither agree nor disagree": 3, "Agree somewhat": 4, "Agree strongly": 5,
}
METRICS = {
    "overall_quality": ("Overall quality", QUALITY),
    "instructor_effectiveness": ("Instructor effectiveness", QUALITY),
    "intellectual_challenge": ("Intellectual challenge", QUALITY),
    "workload": ("Workload", WORKLOAD),
    "feedback_frequency": ("Helpful feedback", FEEDBACK),
    "ta_frequency": ("TA quality", QUALITY),
}
PERIOD = re.compile(r"\.(IN|SP|SU|FA)\.?(\d{2})$")
CODE = re.compile(r"^([A-Z]+\.\d+\.\d+)")
COMPLETE_YEARS = list(range(2016, 2026))
WINDOWS = {
    "all_snapshot": (2015, 2026),
    "full_main_term_years": (2016, 2025),
    "early_2016_2019": (2016, 2019),
    "middle_2020_2021": (2020, 2021),
    "recent_2022_2025": (2022, 2025),
    "recent_2023_2025": (2023, 2025),
}


def aggregate(frame, dimensions):
    result = frame.groupby(dimensions, as_index=False).agg(
        score_sum=("score_sum", "sum"), n=("n", "sum"),
        records=("records", "sum"),
    )
    result["score"] = result.score_sum / result.n
    return result


def describe(frame):
    if frame.empty:
        return {"groups": 0}
    scores = frame.score.to_numpy()
    quantiles = np.quantile(scores, [.05, .25, .5, .75, .9, .95])
    return {
        "groups": len(frame), "responses": int(frame.n.sum()),
        "mean": float(scores.mean()),
        "response_weighted_mean": float(frame.score_sum.sum() / frame.n.sum()),
        **dict(zip(["p05", "p25", "median", "p75", "p90", "p95"], quantiles)),
        "sd_between_groups": float(scores.std(ddof=1)) if len(scores) > 1 else 0,
        "median_responses_per_group": float(frame.n.median()),
        "pct_fewer_than_10_responses": float(100 * (frame.n < 10).mean()),
        "pct_fewer_than_20_responses": float(100 * (frame.n < 20).mean()),
        "pct_perfect_5": float(100 * np.isclose(scores, 5, atol=1e-12, rtol=0).mean()),
    }


def percentile(values, score):
    # Midrank convention: percent below, plus half of the tied observations.
    tied = np.isclose(values, score, atol=1e-12, rtol=0)
    below = (values < score) & ~tied
    return float(100 * (below.sum() + .5 * tied.sum()) / len(values))


def markdown_table(frame, columns):
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.iterrows():
        values = [f"{row[c]:.3f}" if isinstance(row[c], (float, np.floating)) else str(row[c]) for c in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = args.input.read_bytes()
    data = json.loads(source)
    service = CourseGroupingService()
    parsed, malformed, skipped = [], [], []
    for key, record in data.items():
        code, period = CODE.match(key), PERIOD.search(key)
        if not code or not period or not isinstance(record, dict):
            skipped.append(key)
            continue
        season, short_year = period.groups()
        year = 2000 + int(short_year)
        if re.search(r"\.(IN|SP|SU|FA)\.\d{2}$", key):
            malformed.append(key)
        parsed.append((key, code[1], year, season, record))

    codes = {p[1] for p in parsed}
    groups = {c: tuple(sorted(set(service.get_group_info(c).get("courses", [c])) & codes)) for c in codes}
    memberships = {}
    for group in set(groups.values()):
        for member in group:
            if member in memberships and memberships[member] != group:
                raise ValueError(f"Overlapping data-bearing groups for {member}")
            memberships[member] = group

    facts, coverage, missing, unknown_labels = [], [], [], []
    for key, code, year, season, record in parsed:
        group = ";".join(groups[code])
        coverage.append({"group": group, "code": code, "year": year, "season": season, "record": key})
        for metric, (_, mapping) in METRICS.items():
            field = metric if metric.endswith("_frequency") else metric + "_frequency"
            frequency = record.get(field) or {}
            score_sum, n = 0, 0
            for label, count in frequency.items():
                if not isinstance(count, (int, float)) or not np.isfinite(count) or count < 0 or count != int(count):
                    raise ValueError(f"Invalid frequency count in {key}: {field}")
                if label in mapping:
                    score_sum += mapping[label] * count
                    n += count
                elif label != "N/A" and count:
                    unknown_labels.append([key, field, label])
            if n:
                facts.append({"group": group, "year": year, "season": season,
                              "metric": metric, "score_sum": score_sum, "n": n, "records": 1})
            else:
                missing.append({"metric": metric, "year": year, "season": season, "records": 1})
    if unknown_labels:
        raise ValueError(f"Unmapped response labels: {unknown_labels[:5]}")

    frame = pd.DataFrame(facts)
    coverage_df = pd.DataFrame(coverage)
    yearly = aggregate(frame, ["group", "year", "metric"])
    summary = []
    for (year, metric), subset in yearly.groupby(["year", "metric"]):
        for threshold in [1, 10, 20, 30]:
            summary.append({"year": year, "metric": metric, "min_responses": threshold,
                            **describe(subset[subset.n >= threshold])})
    yearly_summary = pd.DataFrame(summary)
    yearly_summary.to_csv(out / "yearly_distributions.csv", index=False)
    yearly.to_csv(out / "course_group_year_scores.csv", index=False)

    term_coverage = coverage_df.groupby(["year", "season"], as_index=False).agg(
        records=("record", "size"), course_codes=("code", "nunique"), course_groups=("group", "nunique"))
    term_coverage.to_csv(out / "coverage_by_term.csv", index=False)
    if missing:
        pd.DataFrame(missing).groupby(["metric", "year", "season"], as_index=False).sum().to_csv(out / "missing_metrics.csv", index=False)

    windows, window_summary, fixed_scores = {}, [], []
    for label, (start, end) in WINDOWS.items():
        windows[label] = aggregate(frame[frame.year.between(start, end)], ["group", "metric"])
        for metric, subset in windows[label].groupby("metric"):
            for threshold in [1, 20]:
                eligible = subset[subset.n >= threshold]
                window_summary.append({"window": label, "metric": metric, "min_responses": threshold, **describe(eligible)})
                if not eligible.empty:
                    for score in [2.5, 3., 3.5, 4., 4.5, 4.75]:
                        fixed_scores.append({"window": label, "metric": metric, "min_responses": threshold,
                                             "score": score, "percentile": percentile(eligible.score.to_numpy(), score)})
    window_summary = pd.DataFrame(window_summary)
    window_summary.to_csv(out / "window_distributions.csv", index=False)
    fixed_scores = pd.DataFrame(fixed_scores)
    fixed_scores.to_csv(out / "fixed_score_percentiles.csv", index=False)

    matched = []
    early, late = windows["early_2016_2019"], windows["recent_2022_2025"]
    for metric in METRICS:
        for threshold in [1, 20]:
            a = early[(early.metric == metric) & (early.n >= threshold)]
            b = late[(late.metric == metric) & (late.n >= threshold)]
            both = a.merge(b, on="group", suffixes=("_early", "_late"))
            difference = both.score_late - both.score_early
            matched.append({"metric": metric, "min_responses_each_window": threshold, "matched_groups": len(both),
                            "early_mean": both.score_early.mean(), "late_mean": both.score_late.mean(),
                            "mean_change": difference.mean(), "median_change": difference.median(),
                            "pct_increased": float(100 * (difference > 0).mean())})
    matched = pd.DataFrame(matched)
    matched.to_csv(out / "matched_course_changes.csv", index=False)

    # Same course cohort in every full-main-term year: no entry/exit effects.
    panel_rows = []
    for metric in METRICS:
        eligible = yearly[(yearly.metric == metric) & yearly.year.isin(COMPLETE_YEARS) & (yearly.n >= 10)]
        n_years = eligible.groupby("group").year.nunique()
        common = n_years[n_years == len(COMPLETE_YEARS)].index
        for year, subset in eligible[eligible.group.isin(common)].groupby("year"):
            panel_rows.append({"metric": metric, "year": year, **describe(subset)})
    panel = pd.DataFrame(panel_rows)
    panel.to_csv(out / "fixed_course_cohort.csv", index=False)

    seasonal_summary, seasonal_pairs = [], []
    complete = frame[frame.year.isin(COMPLETE_YEARS)]
    for season in ["SP", "FA", "SU", "IN"]:
        seasonal = aggregate(complete[complete.season == season], ["group", "metric"])
        for metric, subset in seasonal.groupby("metric"):
            for threshold in [1, 20]:
                seasonal_summary.append({"season": season, "metric": metric, "min_responses": threshold,
                                         **describe(subset[subset.n >= threshold])})
    seasonal_summary = pd.DataFrame(seasonal_summary)
    seasonal_summary.to_csv(out / "season_distributions.csv", index=False)
    for target, reference in [("SU", ["SP", "FA"]), ("IN", ["SP", "FA"]), ("SP", ["FA"])]:
        a = aggregate(complete[complete.season == target], ["group", "year", "metric"])
        b = aggregate(complete[complete.season.isin(reference)], ["group", "year", "metric"])
        both = a[a.n >= 10].merge(b[b.n >= 10], on=["group", "year", "metric"], suffixes=("_target", "_reference"))
        for metric, subset in both.groupby("metric"):
            delta = subset.score_target - subset.score_reference
            seasonal_pairs.append({"target": target, "reference": "+".join(reference), "metric": metric,
                                   "matched_course_years": len(subset), "distinct_course_groups": subset.group.nunique(),
                                   "mean_change": delta.mean(), "median_change": delta.median()})
    seasonal_pairs = pd.DataFrame(seasonal_pairs)
    seasonal_pairs.to_csv(out / "matched_season_changes.csv", index=False)

    benchmark_changes = []
    for metric in METRICS:
        for threshold in [1, 20]:
            reference = windows["all_snapshot"]
            recent = windows["recent_2023_2025"]
            a = reference[(reference.metric == metric) & (reference.n >= threshold)].score.to_numpy()
            b = recent[(recent.metric == metric) & (recent.n >= threshold)].score.to_numpy()
            differences = np.array([percentile(b, value) - percentile(a, value) for value in b])
            benchmark_changes.append({"metric": metric, "min_responses": threshold,
                                      "all_history_groups": len(a), "recent_groups": len(b),
                                      "median_absolute_percentile_point_change": np.median(abs(differences)),
                                      "p95_absolute_percentile_point_change": np.quantile(abs(differences), .95),
                                      "max_absolute_percentile_point_change": abs(differences).max(),
                                      "mean_signed_percentile_point_change": differences.mean()})
    benchmark_changes = pd.DataFrame(benchmark_changes)
    benchmark_changes.to_csv(out / "benchmark_window_impact.csv", index=False)

    provenance = {
        "source": str(args.input.resolve()), "sha256": hashlib.sha256(source).hexdigest(),
        "source_records": len(data), "parsed_records": len(parsed), "course_codes": len(codes),
        "course_groups": len(set(groups.values())), "normalized_period_keys": malformed,
        "skipped_records": skipped, "metric_response_totals": frame.groupby("metric").n.sum().to_dict(),
        "full_main_term_years_used": COMPLETE_YEARS,
    }
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

    os.environ.setdefault("MPLCONFIGDIR", str(out / ".matplotlib-cache"))
    os.environ.setdefault("XDG_CACHE_HOME", str(out / ".cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold"})
    fig, axes = plt.subplots(3, 2, figsize=(13, 11), sharex=True)
    for ax, (metric, (label, _)) in zip(axes.flat, METRICS.items()):
        annual = yearly_summary[(yearly_summary.metric == metric) & yearly_summary.year.isin(COMPLETE_YEARS)]
        a = annual[annual.min_responses == 1].sort_values("year")
        b = annual[annual.min_responses == 20].sort_values("year")
        ax.plot(a.year, a["mean"], color="#176B87", marker="o", label="Average course score")
        ax.plot(a.year, a.p95, color="#C05B24", marker="o", label="95th percentile")
        ax.plot(b.year, b.p95, color="#C05B24", linestyle="--", label="95th percentile, ≥20 responses")
        ax.set_title(label, loc="left")
        ax.set_ylabel("Score (1–5)")
        ax.grid(axis="y", alpha=.18)
        ax.set_xticks([2016, 2018, 2020, 2022, 2024, 2025])
        if metric == "workload":
            ax.set_ylim(2.9, 4.35)
        else:
            ax.set_ylim(3.6, 5.05)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .925), ncol=3, frameon=False)
    fig.suptitle("How course-score distributions changed by year", fontsize=20, x=.07, ha="left", y=.984)
    fig.text(.07, .947, "Each course group counts once per year; scores within groups are weighted by response counts.", fontsize=11, color="#475569")
    fig.text(.07, .025, "Local snapshot • Spring/Fall present in 2016–2025; other coverage may vary.\n2015 and 2026 excluded here because coverage is partial. Percentiles describe course averages, not individual answers.", fontsize=10, color="#475569")
    fig.subplots_adjust(top=.87, bottom=.10, left=.07, right=.98, hspace=.30, wspace=.19)
    fig.savefig(out / "yearly_distributions.png", dpi=170)
    plt.close(fig)

    endpoints = []
    for metric, (label, _) in METRICS.items():
        annual = yearly_summary[(yearly_summary.metric == metric) & (yearly_summary.min_responses == 1)].set_index("year")
        endpoints.append({"Metric": label, "2016 mean": annual.loc[2016, "mean"],
                          "2025 mean": annual.loc[2025, "mean"], "2016 p95": annual.loc[2016, "p95"],
                          "2025 p95": annual.loc[2025, "p95"]})
    endpoints = pd.DataFrame(endpoints)
    endpoints.to_csv(out / "annual_endpoint_comparison.csv", index=False)
    quality_2025 = yearly_summary[(yearly_summary.year == 2025) & (yearly_summary.metric == "overall_quality")].set_index("min_responses")
    matched_lookup = matched[matched.min_responses_each_window == 20].set_index("metric")
    workload_seasons = seasonal_summary[(seasonal_summary.metric == "workload") & (seasonal_summary.min_responses == 1)].set_index("season")
    headline = yearly_summary[(yearly_summary.min_responses == 1) & yearly_summary.year.isin([2016, 2019, 2020, 2021, 2023, 2025])]
    sections = [
        "# Historical course-score distributions",
        "This is a descriptive analysis of the local `data.json` snapshot, not a query of the live database or a complete university census.",
        "## Findings",
        markdown_table(endpoints, list(endpoints.columns)),
        "Most ratings rise modestly over the decade; workload is comparatively stable. The 95th percentile alone misses much of the change because several metrics are already at the 5.0 ceiling. See the medians and lower percentiles in the accompanying tables.",
        f"The upward shift also occurs within repeated courses: overall quality rises {matched_lookup.loc['overall_quality', 'mean_change']:.3f} points across {int(matched_lookup.loc['overall_quality', 'matched_groups'])} matched groups, and helpful feedback rises {matched_lookup.loc['feedback_frequency', 'mean_change']:.3f}; workload changes only {matched_lookup.loc['workload', 'mean_change']:+.3f}. These compare 2016–2019 with 2022–2025, requiring 20 responses in each window.",
        f"Sample size and course composition matter: the 2025 overall-quality p95 is {quality_2025.loc[1, 'p95']:.3f} across {int(quality_2025.loc[1, 'groups'])} groups, versus {quality_2025.loc[20, 'p95']:.3f} among the {int(quality_2025.loc[20, 'groups'])} with at least 20 responses. This restriction changes which courses are included; it does not prove low-count scores are wrong or justify automatically excluding them.",
        "A fixed benchmark is a reasonable first implementation based on this snapshot. Switching from all stored history to a 2023–2025 benchmark changes recent courses' percentile ranks by a median of roughly 1–2 points for most metrics, below 1 point for workload/TA quality, and about 5.3 points for helpful feedback. The exact effects and sensitivity to a response-count cutoff are exported. A fixed baseline should be labeled with its time window and refresh date.",
        f"Season comparisons are not universally too small: across 2016–2025 there are {int(workload_seasons.loc['SU', 'groups'])} summer and {int(workload_seasons.loc['IN', 'groups'])} intersession groups with workload scores. Their course mix differs substantially. Intersession's mean workload is {workload_seasons.loc['IN', 'mean']:.3f}, versus {workload_seasons.loc['SP', 'mean']:.3f} in spring and {workload_seasons.loc['FA', 'mean']:.3f} in fall. The matched same-course/year intersession workload comparison has only four distinct courses, so the broad seasonal difference should not be interpreted as an effect of the season itself.",
        "![Annual distribution chart](yearly_distributions.png)",
        "## Method and coverage",
        f"- {len(data):,} evaluation records; {len(codes):,} course codes; {len(set(groups.values())):,} non-overlapping data-bearing analysis groups.",
        "- Sum response score totals and valid counts across sections/cross-listed codes within each group and period. Exclude N/A and metric cells with no valid responses. Never average annual percentiles or rounded scores.",
        "- Distributions give each course group equal weight. Response-weighted overall means are also exported for comparison. Counts across metrics are not counts of unique students.",
        "- Quantiles use NumPy's default linear interpolation. Score-to-percentile lookups use the fraction below plus half the tied fraction. Small-sample exclusions are sensitivity checks, not an adopted product policy.",
        "- 2015 has only Summer/Fall records; 2026 only Intersession. Main comparisons use 2016–2025, which each have Spring and Fall records; this does not establish complete course coverage. Intersession 2024 is absent, and all 125 Intersession 2021 records lack workload responses.",
        f"- Normalized an extra dot in {len(malformed)} source period keys for this analysis only. Source files are unchanged.",
        "- Matched-course comparisons reduce changes in course mix, but do not control for instructor, student composition, response rates, or other changes; descriptive differences are not causal estimates.",
        "## Selected annual distributions",
        markdown_table(headline, ["year", "metric", "groups", "mean", "median", "p95", "median_responses_per_group"]),
        "## Same courses: 2016–2019 versus 2022–2025",
        "At least 20 valid responses for the metric in each window; course averages are response-weighted within each window, and paired changes are equally weighted across courses.",
        markdown_table(matched[matched.min_responses_each_window == 20], ["metric", "matched_groups", "early_mean", "late_mean", "mean_change", "median_change"]),
        "## Effect of a recent versus all-history benchmark",
        "Hold each recent (2023–2025) course score fixed; change only the reference distribution from all stored years to 2023–2025. Differences are percentile points, not score points. Course coverage also differs across benchmarks.",
        markdown_table(benchmark_changes[benchmark_changes.min_responses == 1], ["metric", "all_history_groups", "recent_groups", "median_absolute_percentile_point_change", "p95_absolute_percentile_point_change"]),
        "## Seasons: matched course and year",
        "At least 10 responses for the metric on each side. Each matched course/year counts once. The same course can appear in multiple years.",
        markdown_table(seasonal_pairs, ["target", "reference", "metric", "matched_course_years", "distinct_course_groups", "mean_change"]),
        "## Files",
        "`yearly_distributions.csv` includes thresholds of 1, 10, 20, and 30 responses. `fixed_course_cohort.csv` holds the course cohort constant across all 10 full-main-term years (≥10 responses every year). `season_distributions.csv` describes course averages within each season over 2016–2025. `window_distributions.csv`, `fixed_score_percentiles.csv`, and `benchmark_window_impact.csv` compare alternative fixed benchmarks. `coverage_by_term.csv` and `missing_metrics.csv` show coverage limitations. `provenance.json` identifies the exact input snapshot.",
    ]
    (out / "report.md").write_text("\n\n".join(sections) + "\n")
    print(json.dumps(provenance, indent=2))
    print("MATCHED CHANGES (at least 20 responses each window)")
    print(matched[matched.min_responses_each_window == 20].round(4).to_string(index=False))
    print("BENCHMARK WINDOW IMPACT (all nonempty course means)")
    print(benchmark_changes[benchmark_changes.min_responses == 1].round(3).to_string(index=False))
    print("Results:", out)


if __name__ == "__main__":
    main()
