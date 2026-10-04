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

-- Split only explicit lists, never surnames, initials, or comma-form names.
CREATE OR REPLACE FUNCTION evaluation_instructor_names(record JSONB)
RETURNS TEXT[] LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT COALESCE(array_agg(DISTINCT btrim(name)) FILTER (WHERE btrim(name) <> ''), ARRAY[]::TEXT[])
    FROM jsonb_array_elements_text(
        CASE
            WHEN jsonb_typeof(record->'instructor_names') = 'array' THEN record->'instructor_names'
            WHEN jsonb_typeof(record->'instructor_name') = 'array' THEN record->'instructor_name'
            WHEN jsonb_typeof(record->'instructor_name') = 'string' THEN
                to_jsonb(regexp_split_to_array(record->>'instructor_name', E'[;|\\n\\r]+|[[:space:]]+(&|and)[[:space:]]+'))
            ELSE '[]'::JSONB
        END
    ) AS names(name);
$$;

CREATE INDEX IF NOT EXISTS courses_instructor_names_idx
    ON courses USING GIN (evaluation_instructor_names(data));
CREATE INDEX IF NOT EXISTS courses_course_code_idx ON courses(course_code);

COMMIT;
