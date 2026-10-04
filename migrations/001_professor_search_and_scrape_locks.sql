BEGIN;

ALTER TABLE course_metadata
    ADD COLUMN IF NOT EXISTS scrape_lock_expires_at TIMESTAMPTZ;

-- Lock heartbeats must not pretend that evaluation data was refreshed.
CREATE OR REPLACE FUNCTION set_course_metadata_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'scrape_lock_expires_at' - 'updated_at') IS DISTINCT FROM
       (to_jsonb(OLD) - 'scrape_lock_expires_at' - 'updated_at') THEN
        NEW.updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_timestamp_course_metadata ON course_metadata;
CREATE TRIGGER set_timestamp_course_metadata
BEFORE UPDATE ON course_metadata
FOR EACH ROW EXECUTE FUNCTION set_course_metadata_timestamp();

-- Remove the superseded list parser if an earlier review version was applied.
DROP INDEX IF EXISTS courses_instructor_names_idx;
DROP FUNCTION IF EXISTS evaluation_instructor_names(JSONB);

-- A professor is one literal recorded string. Do not interpret lists or delimiters.
CREATE OR REPLACE FUNCTION evaluation_instructor_name(record JSONB)
RETURNS TEXT LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT CASE WHEN jsonb_typeof(record->'instructor_name') = 'string'
        THEN NULLIF(btrim(record->>'instructor_name'), '') END;
$$;

CREATE INDEX IF NOT EXISTS courses_instructor_name_idx
    ON courses (evaluation_instructor_name(data));
CREATE INDEX IF NOT EXISTS courses_course_code_idx ON courses(course_code);

COMMIT;
