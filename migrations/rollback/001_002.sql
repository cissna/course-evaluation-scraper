-- Reverse migrations 001 and 002 against the original repository schema.
-- Stop the new application and active scrapes before running this file.
-- This drops only the new cache/schema objects; existing evaluations remain.
-- Review pre-existing/custom objects first, as described in ../README.md.
BEGIN;

DROP TRIGGER IF EXISTS set_timestamp_course_metadata ON course_metadata;
CREATE TRIGGER set_timestamp_course_metadata
BEFORE UPDATE ON course_metadata
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

DROP INDEX IF EXISTS courses_instructor_names_idx;
DROP INDEX IF EXISTS courses_course_code_idx;
DROP FUNCTION IF EXISTS evaluation_instructor_names(JSONB);
DROP FUNCTION IF EXISTS set_course_metadata_timestamp();

ALTER TABLE course_metadata DROP COLUMN IF EXISTS scrape_lock_expires_at;
DROP TABLE IF EXISTS percentile_benchmarks;

COMMIT;
