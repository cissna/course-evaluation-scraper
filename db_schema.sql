-- Schema for the JHU Course Evaluation Analyzer database

-- Table to store metadata about each course
CREATE TABLE course_metadata (
    course_code VARCHAR(255) PRIMARY KEY,
    last_period_gathered VARCHAR(10),
    last_period_failed BOOLEAN DEFAULT FALSE,
    relevant_periods JSONB,
    last_scrape_during_grace_period DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table to store the detailed course evaluation data for each course instance
CREATE TABLE courses (
    instance_key VARCHAR(255) PRIMARY KEY,
    course_code VARCHAR(255) REFERENCES course_metadata(course_code),
    data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to call the function before any update on the tables
CREATE TRIGGER set_timestamp_course_metadata
BEFORE UPDATE ON course_metadata
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TRIGGER set_timestamp_courses
BEFORE UPDATE ON courses
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- 001_professor_search_and_scrape_locks.sql

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

-- 002_percentile_benchmarks.sql

-- A precomputed snapshot; never rebuilt during a search or frontend filter change.
CREATE TABLE IF NOT EXISTS percentile_benchmarks (
    benchmark_id TEXT PRIMARY KEY CHECK (benchmark_id = 'current'),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);
