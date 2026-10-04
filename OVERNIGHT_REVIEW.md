# Overnight review

`TODO.md` is unchanged; subsequent owner decisions recorded below override it where stated. Both review branches are normal local branches in the original repository and remain unmerged:

- `codex/overnight-improvements`: professor search, #6, the explicit year-range empty state, grouping tooltip, #15, and #19–21.
- `codex/overnight-comparisons`: based on the shared branch, adding #13–14.

## Follow-up decisions

- **Tests:** At the owner's request, the added tests and test-only fixtures, browser scripts, and reference data are removed. The old Create React App example test had been replaced by the new app tests; that replacement is removed too. Existing test dependencies/configuration are unchanged.
- **Browser review:** Browser access was intended to check the requested desktop/phone layout and interactions. Those visual checks were not completed overnight because execution was denied. This is a remaining manual visual review, not a missing application dependency.
- **Database review:** The migrations were prepared but not run against a database. The owner will review them manually before applying them. [Migration instructions](migrations/README.md) now include a prepared rollback and its limits; no database-test prerequisite is imposed.
- **Deferred scope:** #10, the broader #12 investigation, #16, and professor-name grouping remain untouched. Existing course-grouping rules/configuration and date cutoffs are unchanged. The earlier date and grouping-precedence observations were irrelevant and have been removed.

## Implementation decisions to review

- **Multiple listed professors — removed:** The owner deferred this requirement after the overnight review. Professor search/filtering now treats `instructor_name` as one literal string. Array support and guessed delimiters have been removed from SQL, Python, and JavaScript. The earlier “Jane Smith & Alex Rivera” example was invented to explain the parser, not supplied by the owner or found in the local data. Review an actual example before adding support later.
- **Cached refresh (#20):** Saved evaluations remain visible while a separate browser request runs the existing scraper. A renewable per-course database lock prevents duplicate scrapes. The work runs during the request; no persistent job system or closed-tab notification was added.
- **Refresh failures:** A report marked `scrape_failed` now marks the check failed instead of incorrectly reporting completion. Previously saved evaluations remain available. This corrects refresh status without investigating the deferred null-table issue.
- **Recorded names:** Professor separation retains exact recorded names rather than stripping punctuation, keeping it consistent with exact-name search. No professor-name grouping is introduced.
- **Percentile population (#21):** The benchmark covers all departments and all available years, with one response-weighted mean per existing logical course group and equal weight between groups. Ties use midranks. Review this population/time-window choice. Rebuild after bulk imports/scrapes, at least monthly; frontend filters do not rebuild it.

## Status

Production builds passed during implementation, and the offline percentile build from `data.json` covered 2015–2026. No migrations have been applied, no production scrape or deployment was performed, and neither review branch has been merged. Desktop/phone appearance and actual notification delivery remain unverified. `TODO.md` accompanies both branches unchanged.
