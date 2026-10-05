# Reviewing course and professor comparisons

The `codex/overnight-comparisons` branch adds TODO #13–14 on top of `codex/overnight-improvements`. Both branches are left unmerged. [OVERNIGHT_REVIEW.md](../OVERNIGHT_REVIEW.md) records implementation decisions and remaining manual review.

## Result selection and shared settings

Search, Enter, and ordinary history selection open one result. **Add side-by-side** and each history **side-by-side** button add a course or professor, up to five in total. An ambiguous add search keeps its intent and the current tables until a choice succeeds. An unsuccessful search keeps the previous results. Exact duplicate result IDs do not consume a slot; separate course codes from one cross-listed group can be shown together.

Results stay side by side in a horizontally scrolling row, starting at 520px each and expanding to fit their table's minimum content width. Each result retains its own title, former names, grouping controls, and refresh state. Filters, statistics, percentiles, comparison metric/threshold, and separation settings apply to every result. Professor separation applies to course tables; Course separation applies to professor tables, displaying course names with code tooltips. A single-code table omits the redundant code grouping. Removing down to one result restores the single-result layout. Multiple results use the heading **Side-by-side View**, changing to **Comparison View** while statistical comparison is enabled.

## Comparing rows

Comparison mode starts off. **Enter comparison mode** requires at least two displayed rows, either separated within one result or across multiple results. Otherwise a browser alert explains how to add or separate entries and must be dismissed; the mode stays off. A single professor result uses the same rule with a course-separation example. The entry button and circled information icon are centered together while the mode is off. Once enabled, the mode reveals the metric menu, row selection, metric-header highlighting, and the advanced significance threshold. The icon moves to the center, with the exit button on its left and the metric menu on its right. The icon explains how to use the mode, followed by a separate statistics paragraph in a font 2px smaller. **Exit comparison mode** removes the comparison controls, feedback, and row highlights and clears the selected pair, while preserving results and filters. The chosen mode, metric, and threshold remain in memory across searches and reset on reload. The entry restriction does not automatically exit an already active mode when rows are combined or filtered away.

In comparison mode, click a row, or focus it and press Enter/Space, to select it. The newest row has a 4.8px red outline and the older row an orange outline, 40% thinner than the original 8px. Selecting a third row replaces the older selection. Clicking a selected row removes it. Filtering/separating away a row or removing its result clears that selection. There are no extra selection cards or clear button.

The compact metric dropdown starts at Overall Quality. Only its header is yellow in each table; numeric cells keep their usual backgrounds. Only displayed numeric rating metrics are offered; hiding the current metric chooses the first remaining metric. With none visible, testing and metric highlighting stop and a selected pair receives an unavailable explanation. The threshold is under Advanced Options → Statistics while comparison mode is on and defaults to 0.05.

Every selected pair receives feedback: significant, not significant, or unavailable with a reason. The popup has square corners and an orange background. Group names are bold and use the matching orange/red hues; **significantly** or **not** is emphasized as appropriate. Names from different tables include their source course code or professor name. An All Data row uses only its source name, without an extra separator. Significant pairs receive gold cell backgrounds while retaining the colored outlines. Percentile display does not affect the test.

## Statistical calculation

Each metric retains valid response counts, the unrounded mean, and unbiased sample variance from the filtered frequency distributions. N/A responses are excluded. The comparison uses the two-sided Welch independent two-sample t-test:

```text
a = s₁² / n₁, b = s₂² / n₂
t = (mean₁ − mean₂) / sqrt(a + b)
df = (a + b)² / (a² / (n₁ − 1) + b² / (n₂ − 1))
p = 2 × Student-t upper-tail probability(|t|, df)
significant when p < threshold
```

The JavaScript implementation evaluates the Student-t tail through the regularized incomplete beta function. It uses the full sample moments, never rounded table scores or percentile ranks. The formulas follow the [NIST two-sample t-test reference](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm). The test is approximate and assumes independent responses; it does not adjust for multiple comparisons or treat ordinal ratings as a different statistical model.

Every sample also carries the IDs of source evaluation records that contributed valid responses to that metric after filtering. Shared IDs make the independent-samples test unavailable, including course/professor overlap and different course codes that fetch the same existing group. Matching names/scores alone do not imply overlap. This cannot detect the same respondent appearing in two distinct reports because respondent identities are unavailable.

Either sample with fewer than two valid responses, two zero sample variances, an invalid threshold, missing sample moments, or numerical nonconvergence produces a short unavailable reason and no significance claim. One zero variance is supported when the other is positive. The two-zero-variance rule follows the explicit TODO decision, including samples with different constant means.
