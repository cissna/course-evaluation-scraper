# TODO

## Professor-name search

Search by professor names as well as course names. Keep distinct recorded professor names separate for now; do not automatically merge initials, similar names, or shared surnames. Professor-name grouping is a separate deferred TODO below.

Resolve ambiguity across both result types: if there is exactly one course/group or professor match, open it directly; if there is more than one possible match, show the search results page, including when the choice is between a course and a professor. Clearly distinguish courses from professors using type labels and distinct colors.

The results page has "Course names" and "Professors" tabs. Default to course names if that tab has results; otherwise default to professors. Gray out and disable empty tabs. If neither type has results, show the existing no-results error without opening the results page.

For professor results:

- Show the professor's name as the title. Include only evaluations attributed to that professor, including team-taught evaluations where they are listed; exclude other instructors' evaluations even when the same course or cross-listed group is fetched.
- Show a popup saying "Searching by Professor Name" with a "Click here to separate by course" button linked to the **"Course"** checkbox under Advanced Options → Separate By. Show this professor-mode control only for professor results. In professor-only views, replace the usual professor-separation checkbox and shortcut with course separation; mixed views show both controls as specified in #13.
- Separating by **Course** uses the existing course groupings. Offer a mutually exclusive "Course code" option that ignores course groupings and displays the individual code in the Group column. Keep this distinct from **"Course title (including former names)"**, which separates historical titles. Preserve the other table columns and functionality.
- For stale data, show "At least one of the courses this professor teaches may be out of date, last updated at …", using the oldest last-updated date among the outdated courses. Recheck the professor's courses using the existing per-course refresh behavior.

## [#6](https://github.com/cissna/course-evaluation-scraper/issues/6): download as csv doesn't add the additional columns being displayed

The CSV should include all visible table columns plus the information available in their tooltips, including response counts, standard deviations, and percentiles when available. Export tooltip information as separate, clearly labeled columns.

## [#10](https://github.com/cissna/course-evaluation-scraper/issues/10): EN.661.250 not showing data even though it should

**Planning note:** Skip for now: EN.661.250 is now showing data. The underlying issue may still affect other courses. If it comes up again, investigate this together with me, not as an unattended overnight task.

## [#12](https://github.com/cissna/course-evaluation-scraper/issues/12): some courses show null data instead of no results found

**Planning note:** Keep the broader investigation deferred. Unexplained null tables are useful for identifying bugs and should remain visible. The specific year-range-only UI change below is ready for implementation.

I know that this can happen if "filter by last 3 years" is enabled when you search. Which makes sense. But it also happens for some other courses for no clear reason. Need to dig into that.

## No results in the selected year range

If the year range means there are no results, but without that filtering there would be, replace the table in the UI with a popup that says:

**"No results for range [year range], try including some of these years [comma separated list of all years with data]"**

This is an active TODO, separate from the broader deferred investigation in #12. Apply it to both custom year ranges and Show Last 3 Years. Display the actual selected bounds in [year range], including one-sided ranges when only a minimum or maximum is set. List all available years once each, in ascending order, separated by commas.

Confirm that year filtering is the cause: there must be no matching evaluations with the year bounds applied, and removing only those bounds must restore actual results. Keep all other filters and the selected course/professor scope unchanged for that check and for the available-year list. Do not infer this condition merely from null or N/A table cells.

Show the popup in place of the affected table, keeping the heading and controls usable. In comparisons, check each table independently. Leave the chosen filters unchanged; do not automatically switch to all years. Restore the table when the selected range has results again.

**Do not show this popup if results are null for any other reason. Preserve the null table so I can identify bugs; do not hide or replace it.**

**Code references:** Year filtering is in `filterInstances` in `frontend/src/utils/analysisEngine.js:67`; `processAnalysisRequest` at `:217` passes the filtered evaluations into row grouping and statistics. The table is rendered in `frontend/src/components/DataDisplay.js:100`. Distinguish a year-range empty state from missing or null statistics before choosing which UI to render.

## [#13](https://github.com/cissna/course-evaluation-scraper/issues/13): Add side-by-side comparisons between courses

**Planning note:** You can try an implementation and make reasonable choices where the spec is incomplete. Keep this feature isolated on its own branch so I can evaluate it afterward; document the choices made and leave it unmerged for review.

**Comparison scope:** Allow any mixture of courses and professors, including professor-versus-professor comparisons. The five-item cap counts courses and professors together. Apply the same add/remove behavior and shared settings to both result types.

Keep my current styles. The mockup was fine from a UX perspective, but use the compact comparison UI specified in #14.

Once a course or professor result is displayed, add a button next to the Search button that says **"Add to comparison"**. It searches the current input just like normal Search, but adds the chosen course or professor alongside the displayed results. Carry the add-to-comparison intent through the results page until a result is chosen; direct course codes and unambiguous matches add the result immediately.

If adding opens the search results page, calculate the most concise heading from the types that actually have matches:

- Courses only: **"Choose a course to add to comparison"**.
- Professors only: **"Choose a professor to add to comparison"**.
- Both types: **"Choose a course or professor to add to comparison"**.

Use the available types across the full search result sets, not just the active tab or loaded page. Do not mention a type that has no matches. Keep the current **Search Results for "[query]"** heading for a normal search. The existing rules still apply: one overall match opens directly; no matches show the existing no-results error without opening the results page.

Add to each search-history item a button to the right, but to the left of that item's X, which is fairly small and green and just says **"compare"** in small text. Include professor results in history, and distinguish entries with **Course / Professor** labels and the same type colors used in search results. The compare button adds that course or professor to the displayed results; clicking it must not also trigger the history row's normal navigation. Clicking the rest of the history item still opens it normally, and its X still removes it from history.

Normal Search, Enter, and ordinary history selection replace the displayed results with the new single course or professor result. Keep the existing results while resolving an add-to-comparison search, including through ambiguous results. If a search never finds a result, continue to display the previous results and the existing red no-results error.

Let's cap it at **5 courses or professors in total**. In the comparison view, put a small **X beside each result's heading** to remove it. At five results, disable both the search-box add-to-comparison button and the history compare buttons, with the message **"Remove a course or professor to add another."** Removing results until only one remains restores the normal single-result layout and heading for that course or professor.

Let the UI be janky on computer for more than 3, janky for more than 1 on phone. It's fine right now on phone; don't edit the way it is when we aren't comparing. Keep the results side by side. General controls stay at the top, using the existing local filtering.

**All settings are shared** across the displayed results, including filters, displayed statistics, comparison metric/threshold, and separation settings. Course-only views show **Separate by Professor**; professor-only views show **Separate by Course**; mixed views show **both**. Professor separation splits course tables, while course separation splits professor tables using the existing course groupings. Do not add redundant grouping labels or splits to tables already restricted to one professor or course.

Under Advanced Options → Separate By, use **Professor** for professor separation and **Course** for splitting professor results into courses. Rename the existing historical-name option to **"Course title (including former names)"**. Keep actual-course separation and historical-title separation distinct; they must not reuse the same setting or grouping key.

A Separate by Course Code / Recombine by Course Code button in any course's banner changes the shared setting, and all those buttons stay in sync. So the UI isn't annoying, don't "separate" a result whose table contains only one code: don't add that code to the Group text or create a redundant split. Keep labels such as "All Data" or the professor's name, and apply the other separation settings as usual. Tables with multiple codes still split by code when the shared setting is enabled.

Currently, we have the name on top and subtitle beneath. That would move down and to the side, since it's per result, but that bold title slot would still be there and just say **"Comparison"**. Each table keeps its own course title/code or professor name. The compact metric dropdown from #14 goes immediately below "Comparison". Single-result headings remain unchanged.

Course-specific things like the recheck data button, course grouping control, or FKA subtitle should be made less wide and fit under the course code, so the popups can happen per course. Keep each course's grouping details, refresh status, and recheck action with that course, rather than combining their banners. A professor's table keeps its professor-mode banner and refresh controls beneath its name. The single-result layout shouldn't be affected by this rearrangement; the small comparison controls from #14 and the grouping tooltip below are still added where applicable.

**Screenshot and code references:**

- The bold "Machine Programming" title and gray `EN.601.727` subtitle in image 1 are the inline heading block in `frontend/src/App.js:305`, using `metadata.current_name` and `courseCode`. This is the title slot that becomes "Comparison", not the dark "JHU Course Evaluation Analyzer" app header (`frontend/src/App.js:275`, `.App-header` in `frontend/src/App.css`).
- Image 2 shows "Neuroscience: Cognitive", its gray "formerly known as Cognitive Neuroscience: Exploring the Living Brain" line, and `AS.050.203`. The FKA line is `metadata.former_names` in `frontend/src/App.js:321`. The wide pale-yellow "SU26 period might have data..." banner and right-hand Recheck button are `frontend/src/components/GracePeriodWarning.js:20`, styled by `.grace-period-warning`, `.warning-content`, and `.recheck-button` in `frontend/src/components/GracePeriodWarning.css`. In multiple-course mode these become narrow, per-course content below the corresponding code.
- Image 3 shows "Honors Mathematical Statistics", its gray "formerly known as Honors Introduction to Statistics" line, `EN.553.431`, and the yellow "This course was automatically grouped with: EN.553.631" box. The course grouping control is currently a banner with a green **Separate by Course Code / Recombine by Course Code** button, not a dropdown: `frontend/src/App.js:336`, with the button at `:361` and `handleSeparateByCourseCode` at `:225`. Keep the grouping details and control under their own course code.
- The existing Search button is in `frontend/src/components/CourseSearch.js:119`; `handleSearch` at `:32` resolves codes and course names, and `handleHistoryItemClick` at `:86` handles history navigation. Add the comparison action alongside Search. `frontend/src/components/SearchResults.js:72` contains the current results heading, and `handleCourseClick` at `:56` opens the selected result; both need to retain whether this is a normal search or an add-to-comparison search.
- Each history row is rendered in `frontend/src/components/SearchHistory.js:148`, with normal navigation at `:152` and the item's remove X at `:157`. Insert the small green compare button before that remove button, not beside the separate dropdown-close X at `:146`. The row and remove button use `.search-history-item` and `.search-history-item-remove` in `frontend/src/components/SearchHistory.css`.
- All current successful course-entry paths converge on `handleDataReceived` in `frontend/src/App.js:142`; ambiguous-result selections also go through `handleSearchResultSelect` at `:166`. Pass the normal-search versus add-to-comparison intent through these handlers (currently a `currentView` state change, not a URL route). The error callback in `frontend/src/components/CourseSearch.js:79` passes `null`, which is not a new destination; preserve previous results on that path.
- `frontend/src/App.js:17` currently holds one course's result/raw data/code, with error at `:30` and grace status at `:32`. Keep those per displayed result; recheck currently uses the single `courseCode` in `handleRecheck` at `:51`. The shared filter shortcuts are at `:386`, and `handleApplyAdvancedOptions` at `:239` currently processes just one course. The conditional Course Name separation control is in `frontend/src/components/AdvancedOptions.js:102`; rename it to Course title (including former names) and keep it available when any displayed course has former names.
- `separateInstances` in `frontend/src/utils/analysisEngine.js:85` currently appends the course code to every Group label when code separation is enabled (`:128`); it receives the filtered dataset at `:222`. Omit the redundant course-code label component for single-code tables without turning off the shared setting.

## [#14](https://github.com/cissna/course-evaluation-scraper/issues/14): Check if two datasets are statistically significantly different.

Implement after #13. Support selecting two rows within one table or across any displayed course or professor tables, including mixed comparisons. All of this should also appear if we don't have multiple results selected. I don't want to clutter the UI too much, so make it all small and consistent between one result and multiple results.

Keep the UI very similar to the current UI. No big topbar comparison panel or selected-row cards. Instead of a big Select button, **clicking anywhere on the row** will do it (a single click, not a double-click). Instead of "A" and "B", color the row outlines **red and orange**, kinda thick like half the height of a letter or **8 pixels**. The most recently selected row is red, the older one orange. Selecting a third row replaces orange with the new red selection; the previous red becomes orange.

Clicking an already selected row deselects it. Removing a result or filtering/separating away a selected row clears that selection. If only one selected row remains, its outline is red. Clear any stale significance message and gold fill when there is no longer a selected pair.

The metric dropdown should be below the **"Comparison"** header, where the course code used to be. In the one-course version it should be under the course code; in the one-professor version, under the professor's name. Keep it above the other popups. It shouldn't have a label on top of it and should say **"Choose a metric to compare"** until the user selects a metric, although it defaults to **Overall Quality**. Even though you can't see that default on the dropdown, the columns for Overall Quality should be highlighted in **yellow**, like the mockup's column highlighting. Once you select a metric it no longer needs to say "Choose a metric to compare"; show the selected metric instead and move the yellow column highlight in every table. Offer the displayed numeric rating metrics.

If the selected metric is hidden in Advanced Options, switch to the first remaining visible numeric rating metric and update the dropdown, column highlight, and comparison. If none remain, disable the metric dropdown and significance testing, and clear the significance message and gold fill until a rating metric is available again.

We don't need to write "Compare two rows" anywhere; people will just realize. Put a tooltip on the "Choose a metric to compare" control explaining what to do, including the default metric and that a third selection replaces the orange row. **No Clear selection button.**

The selected rows' insides should light up **gold** if they are significantly different; keep their red/orange outlines. There should be a small popup below the metric dropdown saying **"[Group name 1] and [Group name 2] are significantly different (P<0.05)"**, with the group names in bold. For rows from different tables, prefix each group name with its source: the course code for a course table or the professor's name for a professor table, e.g. **"EN.601.315 — All Data"** and **"Jane Smith — All Data"**. This distinguishes identically named groups across course, professor, and mixed comparisons. Use the actual configured threshold in that message if it differs from 0.05. Remove the significance message and gold fill when the comparison no longer meets the threshold.

Put the significance threshold in **Advanced Options → Statistics**, which currently only contains checkboxes. Default to **0.05** and label it **"Significance threshold for comparisons"**, with a tooltip explaining the specifics of the comparison.

Use a **two-tailed Welch independent two-sample t-test** to compare mean ratings in either direction. Gold means statistically different; the displayed scores show which is higher. Use the currently filtered evaluations and calculate locally from full-precision response counts, means, and sample variances for the selected metric, not rounded display values or percentile ranks. Recalculate when the metric, filters, or threshold changes. The threshold tooltip should explain the two-sided comparison of mean ratings, unequal variances, the `p < threshold` rule, and that the result is approximate and assumes independent responses.

If the two selected groups share underlying evaluations, keep both tables and allow selecting the rows, but show **"Significance unavailable: these groups share evaluations."** near the metric control. Keep the red/orange selection outlines, but do not run the independent-samples test or show a significance claim or gold highlighting for that pair. Check for shared source evaluation records contributing to the selected metric after the current filters, not merely matching names or scores. This covers, for example, a course's All Data row and a professor result that includes some of those same evaluations.

Display unavailable with a short reason when either sample has fewer than two valid responses or both sample variances are zero; do not highlight those comparisons as significant. Keep this feedback compact near the metric control.

**Code references:** The existing rows and Group labels are rendered in `frontend/src/components/DataDisplay.js:109`; rating cells and their `n`/standard-deviation tooltips are at `:31`. Preserve the current blue table headers, sizing, and score tooltips in `frontend/src/components/DataDisplay.css:28`, adding the yellow metric highlight, colored outlines, and gold selected-row fill without hover/striping hiding them. The Statistics checkbox group is in `frontend/src/components/AdvancedOptions.js:125`. `calculateDetailedStatistics` in `frontend/src/utils/analysisEngine.js:142` currently rounds both mean and standard deviation before returning them (`:166`), and `calculateGroupStatistics` at `:173` returns the row summaries; retain full-precision comparison inputs separately from display rounding.

## Automatically grouped courses: undergraduate/graduate tooltip

Add an **(i)** to the "This course was automatically grouped with" popup. On hover, show a tooltip noting that **for some courses, undergraduate reviews are included with the graduate section, so using this separation to understand the undergrad/grad breakdown isn't useful**.

This is the yellow grouping banner and green Separate by Course Code button shown in image 3, rendered in `frontend/src/App.js:336`. Add the information icon beside the grouping message, in both the normal one-course view and each course's banner when comparing. This explains the limitation of separating the stored reviews by course code; it does not change the grouping or separation behavior.

## [#15](https://github.com/cissna/course-evaluation-scraper/issues/15): search button gets taller (no longer matches height of search box) if a course name searched has no results

it's because of the element "No matching courses found in existing database. Use a course code if this is a new course." that pops up next to it weirdly, but I actually like how it pops up currently so i don't want to change that.
Fundamentally, the search button should be tied to the search box and nothing else, so the fact that it is not is just bad UI code. tie them together so that this could never happen, regardless of whatever weird things change for components around the search box/button.

## [#16](https://github.com/cissna/course-evaluation-scraper/issues/16): pre-compute course groupings using SIS API

**Planning note:** Needs a lot more definition before implementation. The ideas below are exploratory, not a ready overnight specification. Discuss together with professor-name groupings; defer both for now.

simple:
look for courses with the same name but different course codes, that were always run at the same time, with the same professor
courses that match this must be the same

more complicated:
if names are very similar and they otherwise match, group them together

more complicated:
check with a quick LLM if the names are likely the same course (e.g. Seminar in XX vs XX, that might not get caught by a simple textual similarity detector)

more complicated:
if they are not always run at the same time, but have been run at the same time some semesters and match otherwise

more complicated:
if they changed names but did so in tandem, probably still the same, as some courses just change names.

## Professor-name groupings (deferred)

Define a one-time script or infrequently run process to identify recorded professor names that refer to the same person and should be grouped. Discuss the matching rules and how groups are applied together with #16. Leave this out of the initial professor-search implementation and keep name variants separate until then.

## [#19](https://github.com/cissna/course-evaluation-scraper/issues/19): Add options to advanced settings to ignore summer and intersession instances

Add separate "Exclude summer" and "Exclude intersession" checkboxes, both unchecked by default. Match the existing general filters' persistence: retain choices across course searches while the app is open, but reset on page reload or a new visit. Do not add persistent browser storage for these options.

## [#20](https://github.com/cissna/course-evaluation-scraper/issues/20): make scraping of new course data load in the background so users can view old data in the meantime.

Show cached data while checking for updates. The progress banner must make clear that new data may not exist: "Checking for evaluations from [period]. There may be no new data available. Previously saved data is shown below."

When checking finishes, replace the loading indicator with either "No new data found for [period]" or a "Show updated data" button. Display updated results without a full-page reload and preserve the selected filters.

Offer an optional "Notify me when finished" button for supported browsers, requesting notification permission only when clicked. Notifications apply only while the tab remains open; do not add closed-tab notifications or persistent client-side scrape tracking.

Keep the existing server-side scraping approach while allowing cached data to remain usable during a scrape. Prevent simultaneous requests from scraping the same course with a per-course lock shared across backend instances, covering both automatic updates and manual rechecks. Release the lock on completion or failure, and show an in-progress state rather than starting a duplicate scrape. Do not add a separate persistent job system for this feature.

Store the lock in a nullable `scrape_lock_expires_at` timestamp column on the existing `course_metadata` row. NULL means unlocked; a future timestamp means active; an expired timestamp can be reclaimed. Create the metadata row when needed and claim the lock atomically. Remember the exact expiry returned by the database; renew it during long scrapes and clear it to NULL on completion or failure only if it still matches this scrape's claim. A scraper that loses ownership must not publish further results. No separate lock table is needed.

## Scrape failure handling (deferred)

**Planning note:** Flesh this out together before changing failure behavior. For now, preserve the existing retries and warning/skip/continue behavior when a report returns `scrape_failed`.

Distinguish transient failures (such as temporary network or server problems) from persistent failures (such as unavailable reports or unsupported report contents). Decide which failures should be retried, when to retry them, and how partial success should affect the course's up-to-date status. Avoid letting a persistently failing report block the remaining reports or force endless rechecks. Define the policy and user-facing failure messages before implementing it.

## [#21](https://github.com/cissna/course-evaluation-scraper/issues/21): Somehow represent scores as percentiles

Add a small **"Show percentiles"** checkbox beside the shared quick controls (Show Last 3 Years / separation shortcuts), outside Advanced Options. Show it once for the whole view, in the same position for a single result or a comparison. Leave it unchecked by default, and match the other general settings: retain its value across searches while the app is open and reset on reload or a new visit.

Unchecked, show the existing absolute scores to two decimal places. Checked, show whole-number ordinal percentiles such as **"87th"**, rather than "87%", so they aren't mistaken for percentage scores. Apply this only to numeric rating metrics; keep text such as Periods Course Has Been Run unchanged. If a percentile is unavailable, show N/A with a brief tooltip reason instead of mixing a raw score into percentile mode.

Update the existing scale caption with the selected mode: **"Ratings are on a 1–5 scale."** for absolute scores, and **"Ratings shown as percentiles of course averages."** for percentiles.

In either mode, score tooltips should include the absolute score (e.g. **4.30 / 5**), percentile (e.g. **87th percentile**), response count, standard deviation of the original 1–5 ratings, and the benchmark's year coverage. Keep percentile information available without switching the table display. Clarify in the Workload tooltip that a higher percentile means heavier reported workload, not a better score.

Calculate percentile rankings against all courses in the database, not just courses in the same department.

Use precomputed dataset-wide percentile distributions, with a fixed comparison population across filter changes. Filtering should only recalculate the displayed course scores and look up their percentiles; do not add dataset-wide processing on each frontend filter change. Separating rows should also use the same fixed benchmark. Label the benchmark's year coverage and retain response counts in tooltips.

Document the benchmark's time window and refresh schedule when implementing.

**Code references:** The shared quick controls are in `frontend/src/App.js:386`; the existing "All numeric results are between 1 and 5" caption is at `:405`. Numeric cells and their response-count/standard-deviation tooltips are rendered in `frontend/src/components/DataDisplay.js:31`. Keep the existing table styles and expand those tooltips rather than adding a separate percentile panel.
