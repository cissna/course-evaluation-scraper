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
