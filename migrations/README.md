# Database changes for the overnight branches

These SQL files are prepared for manual review. They have **not** been applied to any database. No database test run is required by this handoff.

1. `001_professor_search_and_scrape_locks.sql`: nullable lease on `course_metadata`, a timestamp trigger that excludes lock-only updates, a literal instructor-name helper, and query indexes. Multiple-professor parsing has been removed at the owner's request.
2. `002_percentile_benchmarks.sql`: single current precomputed benchmark snapshot.

Run each SQL file with `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f <file>` when authorized. The migrations are transactional and can be reapplied. Existing evaluation records and course groupings are preserved. Index creation takes a normal table lock during migration; schedule this with the release for a large database. Reapplying 001 removes the superseded list-parser function/index if an earlier review version was applied.

## Rollback

[rollback/001_002.sql](rollback/001_002.sql) reverses both migrations against the original repository schema. It restores the metadata timestamp trigger to `trigger_set_timestamp()` and removes the new lock column, helper functions, indexes, and percentile table. It does not delete or rewrite existing `courses` or `course_metadata` records.

Stop new refresh requests, let active scrapes finish, and stop the new application before running the rollback; resume the previous application afterward. The new application requires the added schema. Rollback discards the temporary lock values and the generated percentile snapshot, which can be rebuilt. It does not undo evaluations added by later scrapes or restore historical timestamps. Thus the schema changes are reversible, but rollback is not a rewind of all subsequent database activity.

Review the rollback against the actual schema before running it. It assumes the named functions/indexes/table were introduced by these migrations and the original timestamp function is unchanged. If any already existed or were customized, preserve their previous definitions rather than dropping them. The rollback intentionally avoids `CASCADE`, so unexpected dependencies cause the transaction to fail instead of being removed.

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/rollback/001_002.sql
```

## Percentile maintenance

After migration, build the benchmark explicitly with `python3 -m backend.build_percentiles --database --write-store`. This reads all database courses and writes only the benchmark snapshot. For offline review use `python3 -m backend.build_percentiles --input data.json --output /tmp/course-benchmark.json`, which makes no database connection.

The benchmark includes all available evaluation years, all departments, and all seasons in the snapshot. Each existing logical course group contributes one mean per metric, weighted by its valid 1–5 response counts; groups have equal weight in the percentile distribution. N/A and invalid response counts are excluded. Ties use midranks. The snapshot records its actual year coverage, generation time, and counts. Rebuild after every regular bulk scrape/import, **at least monthly**; this is an explicit maintenance step, not a scheduled job or work done by HTTP requests. New per-course scrapes do not change a tab's benchmark until the next snapshot is built and the page reloaded.

The scraper lease expires after 120 seconds and renews every 30 seconds while its HTTP request is active. All entry points use the same lease. Writes take an ownership-checked row lock; renewal and release compare the exact expiry returned by PostgreSQL. If the process dies, another request can reclaim the expired lease. A lost owner cannot publish. No separate lock table or job queue is used.
