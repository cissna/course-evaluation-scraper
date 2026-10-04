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
- **Team teaching:** The local export contains 33,502 evaluation records and no instructor strings using explicit list delimiters. Support explicit instructor arrays and clear list separators (semicolon, newline, pipe, spaced `&`/`and`); preserve comma-form names as a single recorded name because commas can mean “surname, given name.” No fuzzy/initial/surname merging. Review this convention against future team-taught exports.

## Implementation decisions

- **Cached-first refresh (#20):** Return saved evaluations immediately. Keep a separate browser-initiated refresh request open while the existing server-side scraper runs; use only tab-local UI state and polling when another request owns the course lock. This works with request-scoped/serverless execution without adding persistent jobs or relying on a thread after a response ends.
- **Percentile benchmark (#21):** Use one response-weighted mean per existing logical course group, across all departments and all available evaluation years in the snapshot; give each course group equal weight in the distribution. Use midrank ties. Refresh the precomputed snapshot after each regular bulk data import/scrape, at least monthly. Filters and row separations never change the benchmark. Review this time window/population choice before publishing.
- **Deferred scope:** #10, the broader null-table investigation in #12, #16, and professor-name grouping remain untouched. Only the explicit year-range empty state is implemented from the active adjacent specification.

## Validation and remaining work

Implementation and validation are in progress. The final entries here will identify automated checks, browser coverage, database migration checks, and concrete limitations; no unchecked item should be interpreted as completed.
