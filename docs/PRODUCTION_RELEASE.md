# Production release

This is the release procedure for the overnight work and subsequent UI/percentile changes. No live migration, branch push, merge into `main`, or deployment has been performed. The owner's original instruction was to prepare these for review before releasing.

## Access and current state

- Supabase: the repository's `DATABASE_URL` connects as `postgres`, owns the application tables, and can create/alter schema and write records. No new database credential or Supabase management-API login is needed for this release.
- GitHub: authenticated access includes repository administration and push permissions. `main` requires a pull request and up-to-date **Vercel** and **Vercel Preview Comments** checks; use that process rather than pushing directly to `main`.
- Vercel: the local project link exists, but the CLI token has expired. Run [`vercel login`](https://vercel.com/docs/cli/login) to restore access to production settings and direct deployment/rollback controls. GitHub's Vercel integration is separate from that local login.
- The latest successful production deployment recorded by GitHub is commit `91a074b` on `main`. The review branches now incorporate that production history. The full release is `codex/overnight-comparisons`, which also contains `codex/overnight-improvements`.
- The live inspection found 34,574 evaluation reports and 19,175 metadata rows. Neither migration is installed. The local preview/export is older, so it must not be uploaded over production data.

## Release order

1. Restore the Vercel login, then confirm the linked `course-evaluation-scraper` project's production branch and existing `DATABASE_URL`. No new environment variable, Supabase Auth configuration, storage bucket, scheduled job, or additional database is required. Production environment values and function-duration settings could not be inspected while the CLI login was invalid.
2. Push the two review branches and open a release PR from `codex/overnight-comparisons` to `main`. Its changes include both branches, so one PR merge can release everything together. Keep the PR unmerged while reviewing the SQL and checking the build. Vercel can build the branch before migration; database-dependent preview features require the new schema if that preview uses the same database.
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

The prior frontend builds and local migration rehearsal passed. The last UI adjustments and CSV file delivery still need the owner's final inspection. Actual Vercel scraping, concurrent-worker recovery, production migration timing, and OS notification delivery have not been verified. These are deployment/manual checks, not a request to add test suites.

## Rollback

If the new application has a problem, restore the preceding Vercel deployment or revert the release PR and redeploy the prior code. Prefer leaving the additive schema in place during application rollback; the previous code does not depend on the new cache or lease.

If the schema also needs reverting, stop the new application's refresh requests and let active scrapes finish before applying [the SQL rollback](../migrations/rollback/001_002.sql). It restores the old metadata trigger and removes only the newly introduced column, functions, indexes, counter, and cache. Existing evaluations remain; the generated mapping and temporary lease/counter values are discarded. It does not undo subsequent scrapes or rewind timestamps. [Migration notes](../migrations/README.md) describe the assumptions and exact command.
