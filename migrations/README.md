# Database changes for the overnight branches

Apply these only after review, to a disposable/local database first, then as a separately authorized release step. They have **not** been applied to a live database.

1. `001_professor_search_and_scrape_locks.sql`: nullable lease on `course_metadata`, a timestamp trigger that excludes lock-only updates, exact instructor membership helper, and query indexes.
2. `002_percentile_benchmarks.sql`: single current precomputed benchmark snapshot.

Run each SQL file with `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f <file>` when authorized. The migrations are transactional and can be reapplied. Existing evaluation records and course groupings are preserved. The GIN index build takes a normal table lock during migration; schedule this with the release for a large database.

After migration, build the benchmark explicitly with `python3 -m backend.build_percentiles --database --write-store`. This reads all database courses and writes only the benchmark snapshot. For offline review use `python3 -m backend.build_percentiles --input data.json --output /tmp/course-benchmark.json`, which makes no database connection.

The benchmark includes all available evaluation years, all departments, and all seasons in the snapshot. Each existing logical course group contributes one mean per metric, weighted by its valid 1–5 response counts; groups have equal weight in the percentile distribution. N/A and invalid response counts are excluded. Ties use midranks. The snapshot records its actual year coverage, generation time, and counts. Rebuild after every regular bulk scrape/import, **at least monthly**; this is an explicit maintenance step, not a scheduled job or work done by HTTP requests. New per-course scrapes do not change a tab's benchmark until the next snapshot is built and the page reloaded.

The scraper lease expires after 120 seconds and renews every 30 seconds while its HTTP request is active. All entry points use the same lease. Writes take an ownership-checked row lock; renewal and release compare the exact expiry returned by PostgreSQL. If the process dies, another request can reclaim the expired lease. A lost owner cannot publish. No separate lock table or job queue is used.
