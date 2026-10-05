# Production release

This is the release procedure for the overnight work and subsequent UI/percentile changes. On October 4, 2026, the owner approved the release and specified **push everything to `dev` first, then `main`**. [Release PR #27](https://github.com/cissna/course-evaluation-scraper/pull/27) promotes the full release from `dev` to `main`; its deployment status and release verification are recorded there.

## Access and current state

- Supabase: the repository's `DATABASE_URL` connects as `postgres`, owns the application tables, and can create/alter schema and write records. No new database credential or Supabase management-API login is needed for this release.
- GitHub: authenticated access includes repository administration and push permissions. `main` requires a pull request and up-to-date **Vercel** and **Vercel Preview Comments** checks; use that process rather than pushing directly to `main`.
- Vercel: login is restored. Production and the `dev` preview use the same `DATABASE_URL`, confirmed against the local connection without printing credentials. The production branch is `main`; the project has Fluid Compute enabled and a 300-second default function timeout. No application environment or timeout setting was changed.
- The preceding production deployment, available as a rollback reference, is commit `91a074b` at `https://course-evaluation-scraper-8u418zezv-cissnas-projects.vercel.app`. The full feature history from `codex/overnight-comparisons` (including `codex/overnight-improvements`) is now on `dev` and contains that production history.
- Migrations 001 and 002 were applied at 02:01 UTC on October 5 (the evening of October 4 locally), preserving all 34,574 evaluation reports and 19,175 metadata rows. A private custom-format backup of `public` was saved outside the repository and its archive contents verified. Both version-3 percentile mappings were built from live data in 1.64 seconds, with the pending counter reset to zero. The older local export must not be uploaded over production data.
- The `dev` Vercel build and both required PR checks passed. Authenticated preview requests returned the current frontend bundle, course data, exact-professor data, combined search, and all 12 percentile lookups. A real recheck of `EN.553.430` completed in 6.89 seconds with no new reports, no counter increase, and its lease released. [Review notes](../OVERNIGHT_REVIEW.md) record the remaining manual checks.

## Release order

1. Confirm Vercel login, the linked `course-evaluation-scraper` project's production branch, and its existing `DATABASE_URL`. No new application environment variable, Supabase Auth configuration, storage bucket, scheduled job, or additional database is required.
2. Incorporate the full comparison branch into `dev` and push `dev` first. Open a release PR from `dev` to `main`, retaining both feature branches as review references. Keep the PR unmerged until the database is ready and the `dev` checks pass. Vercel can build the branch before migration; database-dependent preview features require the new schema because this preview uses the same database.
3. At the start of the release window, take a fresh custom-format dump of the live `public` schema and its data. Save it outside the repository with private filesystem permissions. Use the existing `DATABASE_URL` in the release shell without printing it. For example: `pg_dump --format=custom --schema=public --file=<private-backup-path> "$DATABASE_URL"`. Confirm `pg_restore --list <private-backup-path>` can read it. Use a `pg_dump` version compatible with the server.
4. From the full release checkout, apply these in order, stopping on any error:

   ```sh
   psql "$DATABASE_URL" -X -v ON_ERROR_STOP=1 -f migrations/001_professor_search_and_scrape_locks.sql
   psql "$DATABASE_URL" -X -v ON_ERROR_STOP=1 -f migrations/002_percentile_benchmarks.sql
   python3 -m backend.build_percentiles --database --write-store
   ```

   The first migration adds the refresh lease column, timestamp handling, professor-name helper, and indexes. The second adds the percentile snapshot and insert counter, enables RLS, and removes client access to that table. The Python command builds both equal-course and class-size-weighted mappings from the actual live data. No evaluation rows are replaced. Index creation may briefly block writes; the previous application can use the additive schema while the deployment completes.
5. Confirm the cache has format version 3, both 401-value lookups for each metric, and a generated timestamp. Confirm RLS is enabled and `anon`/`authenticated` cannot access the cache directly. Its public app endpoint still serves the calculated percentiles through the backend. Then merge the approved PR once its required checks pass and watch the Git-triggered production deployment complete.
6. Check the production APIs and let the owner review the desktop UI: a single course, a single professor, mixed side-by-side results, entering/exiting comparison mode, both percentile weighting choices, saved preferences after reload, and an actual CSV download. Run one real course recheck to verify the external scrape/lease path and that **Show updated data** preserves the current view or the banner reports **No new data found**. Phone review and automated browser use remain excluded at the owner's request.

The frontend builds, local migration rehearsal, live migration, and a real Vercel scrape/recheck passed. The migrations themselves took about 0.21 and 0.06 seconds. The last UI adjustments, saved browser preferences, and CSV file delivery still need the owner's final inspection. The release's live recheck found no new reports, so publication of newly discovered reports, heartbeat renewal during a long scrape, concurrent-worker recovery, and OS notification delivery remain unverified on Vercel. No test suites or browser automation were added.

## Rollback

If the new application has a problem, restore the preceding Vercel deployment or revert the release PR and redeploy the prior code. Prefer leaving the additive schema in place during application rollback; the previous code does not depend on the new cache or lease.

If the schema also needs reverting, stop the new application's refresh requests and let active scrapes finish before applying [the SQL rollback](../migrations/rollback/001_002.sql). It restores the old metadata trigger and removes only the newly introduced column, functions, indexes, counter, and cache. Existing evaluations remain; the generated mapping and temporary lease/counter values are discarded. It does not undo subsequent scrapes or rewind timestamps. [Migration notes](../migrations/README.md) describe the assumptions and exact command.
