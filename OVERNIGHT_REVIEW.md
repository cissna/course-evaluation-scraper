# Overnight review

Authoritative scope: `TODO.md`, starting at `32e7eec` on `dev`. The specification is unchanged. No deployment or live database migration is authorized or performed.

## Review branches

- Shared prerequisites and improvements: `codex/overnight-improvements`.
- Comparisons (#13–14), based on that branch: `codex/overnight-comparisons` (created after the shared work is complete).
- Both branches remain unmerged.

## Environment and unexpected findings

- **Git permissions:** The supplied workspace makes its `.git` read-only. Creating the requested branch there failed with `cannot lock ref`. Work continues in an independent local clone at `/private/tmp/course-evaluation-overnight-20261004`, where Git writes are allowed. A portable bundle will accompany the final review. Review/import the branches from that checkout or bundle; the original `dev` checkout is preserved.
- **Specification tracking:** Although the request describes `TODO.md` as untracked, it is already committed in `32e7eec`. The local clone contains that exact file, and both review branches inherit it.
- **Existing tests:** The only frontend test is the unmodified Create React App “learn react” test, which does not describe this application. Replace it with tests of the actual requested behavior.
- **Browser blocker:** Local Flask serving fails with `Operation not permitted` when binding a socket. Shell-launched Chromium fails at macOS `bootstrap_check_in` with `Permission denied (1100)`. The supported computer-use tool reports no available Chrome browser; its approval check rejects Arc with **“Computer Use was not approved to use Arc.”** Approval policy is `never`, so browser access cannot be escalated. Browser checks and screenshots must therefore be completed after review in a permitted environment; none are claimed as passed. A database-free local fixture server is included to make that check reproducible.
- **Database validation blocker:** PostgreSQL client tools exist, but no PostgreSQL server or disposable test database is available; local sockets are also blocked. Three real-database integration tests are provided and explicitly skipped without a local `TEST_DATABASE_URL`. Review migrations and run those tests before release. Unit tests exercise lease lifecycle/ownership loss and API scoping without a database; these do not establish real multi-instance SQL correctness.
- **Test environment:** The supplied default Python changes with the checkout directory. Validation uses the existing Python environment with Flask/psycopg2 installed. Jest's Watchman daemon cannot write its LaunchAgent, so tests run successfully with `--watchman=false`; no machine settings are changed.
- **Team teaching:** The local export contains 33,502 evaluation records and no instructor strings using explicit list delimiters. Support explicit instructor arrays and clear list separators (semicolon, newline, pipe, spaced `&`/`and`); preserve comma-form names as a single recorded name because commas can mean “surname, given name.” No fuzzy/initial/surname merging. Review this convention against future team-taught exports.

## Implementation decisions

- **Cached-first refresh (#20):** Return saved evaluations immediately. Keep a separate browser-initiated refresh request open while the existing server-side scraper runs; use only tab-local UI state and polling when another request owns the course lock. This works with request-scoped/serverless execution without adding persistent jobs or relying on a thread after a response ends.
- **Percentile benchmark (#21):** Use one response-weighted mean per existing logical course group, across all departments and all available evaluation years in the snapshot; give each course group equal weight in the distribution. Use midrank ties. Refresh the precomputed snapshot after each regular bulk data import/scrape, at least monthly. Filters and row separations never change the benchmark. Review this time window/population choice before publishing.
- **Deferred scope:** #10, the broader null-table investigation in #12, #16, and professor-name grouping remain untouched. Only the explicit year-range empty state is implemented from the active adjacent specification.
- **Scrape failures:** A report flagged `scrape_failed` previously fell through to a successful completion marker. In the guarded refresh path, that now marks the check failed and stops publishing the remainder, while previously saved data remains available. Review this necessary refresh-status correction; it is not a broader investigation of null tables.
- **Professor attribution:** The same team-taught evaluation may belong to multiple professors; its source evaluation ID is preserved for the later overlap guard. No evaluation is divided into invented per-teacher response samples.
- **Recorded names:** Course-row professor separation now retains exact recorded strings rather than stripping punctuation for display grouping. This keeps the new exact-name search and the table consistent with the explicit instruction to keep recorded names separate; no new professor grouping is introduced.
- **Benchmark evidence:** The offline build from the committed `data.json` covers 2015–2026 and yields 5,878 Overall Quality course-group averages (5,877 instructor effectiveness, 5,877 challenge, 5,830 workload, 5,872 feedback, 4,171 TA). No production benchmark has been written.

## Validation and remaining work

Shared branch implementation is complete for professor search, #6, the explicit year-range state, grouping information tooltip, #15, and #19–21. #13–14 are reserved for the branch based on it.

- Frontend: **19 tests passed**; production build passed with CI warnings treated as errors. Existing toolchain messages about old Browserslist/Baseline data and Node `fs.F_OK` deprecation remain; dependencies were not upgraded as unrelated scope.
- Backend: **11 tests passed**, **3 real PostgreSQL tests skipped** for the concrete environment blocker above. Python compilation passed.
- Offline full-export percentile build passed (coverage and counts above).
- Browser verification: **not run / blocked**, for both desktop and phone. `tools/browser_review.cjs` contains the prepared checks and screenshot capture, and `tools/fixture_server.py` supplies safe fixtures. These scripts are not evidence that a browser pass occurred.
- Live database migrations, production scraping, actual notification delivery, deployment, and merges: **not performed**.
