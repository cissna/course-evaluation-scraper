# Reviewing course and professor comparisons

The `codex/overnight-comparisons` branch adds TODO #13–14 on top of `codex/overnight-improvements`. Both branches are left unmerged. [OVERNIGHT_REVIEW.md](../OVERNIGHT_REVIEW.md) records decisions and incomplete validation.

## Result selection and shared settings

Search, Enter, and ordinary history selection open one result. **Add to comparison** and each history **compare** button add a course or professor, up to five in total. An ambiguous add search keeps its intent and the current tables until a choice succeeds. An unsuccessful search keeps the previous results. Exact duplicate result IDs do not consume a slot; separate course codes from one cross-listed group can be shown together.

Results stay side by side in a horizontally scrolling row, with a minimum width of 520px each. Each result retains its own title, former names, grouping controls, and refresh state. Filters, statistics, percentiles, comparison metric/threshold, and separation settings apply to every result. Professor separation applies to course tables; Course separation applies to professor tables. A single-code table omits the redundant code grouping. Removing down to one result restores the single-result layout.

## Comparing rows

Click a row, or focus it and press Enter/Space, to select it. The newest row has an 8px red outline and the older row an orange outline. Selecting a third row replaces the older selection. Clicking a selected row removes it. Filtering/separating away a row or removing its result clears that selection. There are no extra selection cards or clear button.

The compact metric dropdown begins with “Choose a metric to compare” while using Overall Quality. Its column is yellow in every table. Only displayed numeric rating metrics are offered; hiding the current metric chooses the first remaining metric. With none visible, testing and highlighting stop. The threshold is under Advanced Options → Statistics and defaults to 0.05. These settings remain in memory across searches and reset on reload.

Significant pairs receive gold cell backgrounds while retaining the colored outlines. The small message names both groups, adding source course codes or professor names when they come from different tables. Percentile display does not affect the test.

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

Every sample also carries the IDs of source evaluation records that contributed valid responses to that metric after filtering. Shared IDs make the independent-samples test unavailable, including course/professor overlap and shared team-taught evaluations. Matching names/scores alone do not imply overlap. This cannot detect the same respondent appearing in two distinct reports because respondent identities are unavailable.

Either sample with fewer than two valid responses, two zero sample variances, an invalid threshold, missing sample moments, or numerical nonconvergence produces a short unavailable reason and no significance claim. One zero variance is supported when the other is positive. The two-zero-variance rule follows the explicit TODO decision, including samples with different constant means.

## Verification and browser review

The numerical tests compare both argument orders against 105 independently generated [SciPy Welch reference results](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind_from_stats.html). The cases include unequal variances/sample sizes, two-response samples, equal means, one zero variance, random 1–5 histograms, and a pair whose displayed means round identically but are significantly different. `tools/generate_welch_reference.py` regenerates the checked-in reference file with an optional development SciPy installation; SciPy is not a runtime dependency.

React integration tests exercise single-course and single-professor row pairs, course/course, professor/professor and mixed pairs, source overlap, stale selection removal, metric fallback, threshold changes, shared controls, ambiguous searches, history behavior, and the five-result cap.

After building the frontend, run `python3 tools/fixture_server.py --port 8765`, then `node tools/browser_review.cjs` with a local Playwright installation (or `PLAYWRIGHT_MODULE=/absolute/path/to/playwright`). The fixture server uses in-memory records and disables database/upstream access. The browser runner covers 1440×900 and 390×844 viewports, captures screenshots and CSV downloads, and checks styles and interactions. The fixtures must be synthetic: do not use `--snapshot` for this runner. Browser execution was blocked in the implementation environment; the prepared script is not a completed visual review.
