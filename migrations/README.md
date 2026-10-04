# Database changes for the overnight branches

These SQL files are prepared for manual review. They have **not** been applied to any database. No database test run is required by this handoff.

1. `001_professor_search_and_scrape_locks.sql`: nullable lease on `course_metadata`, a timestamp trigger that excludes lock-only updates, a literal instructor-name helper, and query indexes. Multiple-professor parsing has been removed at the owner's request.
2. `002_percentile_benchmarks.sql`: one current percentile mapping, a pending-evaluation counter, and an `AFTER INSERT` trigger on `courses` to increment it.

Run each SQL file with `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f <file>` when authorized. The migrations are transactional and can be reapplied. Existing evaluation records and course groupings are preserved. Index creation takes a normal table lock during migration; schedule this with the release for a large database. Reapplying 001 removes the superseded list-parser function/index if an earlier review version was applied.

## Rollback

[rollback/001_002.sql](rollback/001_002.sql) reverses both migrations against the original repository schema. It restores the metadata timestamp trigger to `trigger_set_timestamp()` and removes the new lock column, helper functions, indexes, counter trigger, and percentile table. It does not delete or rewrite existing `courses` or `course_metadata` records.

Stop new refresh requests, let active scrapes finish, and stop the new application before running the rollback; resume the previous application afterward. The new application requires the added schema. Rollback discards the temporary lock values, generated percentile mapping, and pending counter; the mapping can be rebuilt from the preserved evaluations. It does not undo evaluations added by later scrapes or restore historical timestamps. Thus the schema changes are reversible, but rollback is not a rewind of all subsequent database activity.

Review the rollback against the actual schema before running it. It assumes the named functions/indexes/table were introduced by these migrations and the original timestamp function is unchanged. If any already existed or were customized, preserve their previous definitions rather than dropping them. The rollback intentionally avoids `CASCADE`, so unexpected dependencies cause the transaction to fail instead of being removed.

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/rollback/001_002.sql
```

## Percentile maintenance

After migration, the first benchmark request builds the mapping if missing or from the earlier format. To build it ahead of time or force a rebuild after correcting/deleting existing evaluations, run `python3 -m backend.build_percentiles --database --write-store`. This reads all database courses and writes only the mapping and its counter in one transaction. For offline review use `python3 -m backend.build_percentiles --input data.json --output /tmp/course-benchmark.json`, which makes no database connection.

The benchmark includes all available evaluation years, all departments, and all seasons. Each existing logical course group contributes one mean per metric, weighted by its valid 1–5 response counts; groups have equal weight. N/A and invalid response counts are excluded. Course means and lookup scores are rounded to the nearest hundredth, with halfway values rounded up, and ties use midranks. Each metric stores an array of 401 percentile values: index 0 is 1.00 and index 400 is 5.00. The snapshot includes its actual year coverage, generation time, and course counts. Full-precision means and variances remain available for statistical comparisons.

The database counter increments once per newly inserted `courses` evaluation row, across all scrapers and imports. An update to an existing evaluation, a metadata-only update, or a check with no new reports adds zero. A scrape that adds 20 reports adds 20, regardless of how many courses are involved. At 100 pending reports, rebuild at the end of a scrape that published data, or on the next `GET /api/percentiles` request. Long scrapes can cross the threshold by more than 100 before their final rebuild. Bulk imports are counted automatically; their next benchmark request triggers a due rebuild, or the command above can run immediately afterward. There is no monthly schedule.

Rebuilds lock the current benchmark row, recheck the counter, read the evaluations, write the mapping, and reset the counter in one transaction. Concurrent inserts wait on that row and count toward the next rebuild after it commits. A failed rebuild leaves the previous mapping and counter intact for retry; it does not turn a successful scrape into a failure. Normal benchmark requests below the threshold read only the cached mapping. Each open page keeps one shared snapshot across its filters and comparisons; a later page visit fetches the latest snapshot.

The scraper lease expires after 120 seconds and renews every 30 seconds while its HTTP request is active. All entry points use the same lease. Writes take an ownership-checked row lock; renewal and release compare the exact expiry returned by PostgreSQL. If the process dies, another request can reclaim the expired lease. A lost owner cannot publish. No separate lock table or job queue is used.
