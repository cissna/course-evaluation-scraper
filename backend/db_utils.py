import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Establishes a connection to the database."""
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        raise Exception("DATABASE_URL environment variable not set.")
    return psycopg2.connect(conn_string)

def get_course_metadata(course_code):
    """Fetches metadata for a specific course."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM course_metadata WHERE course_code = %s", (course_code,))
            row = cur.fetchone()
            if row:
                # Convert row to dict
                colnames = [desc[0] for desc in cur.description]
                return dict(zip(colnames, row))
    return None

def update_course_metadata(course_code, metadata):
    """Inserts or updates course metadata."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO course_metadata (course_code, last_period_gathered, last_period_failed, relevant_periods, last_scrape_during_grace_period)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (course_code) DO UPDATE SET
                    last_period_gathered = EXCLUDED.last_period_gathered,
                    last_period_failed = EXCLUDED.last_period_failed,
                    relevant_periods = EXCLUDED.relevant_periods,
                    last_scrape_during_grace_period = EXCLUDED.last_scrape_during_grace_period,
                    updated_at = NOW();
                """,
                (
                    course_code,
                    metadata.get('last_period_gathered'),
                    metadata.get('last_period_failed', False),
                    json.dumps(metadata.get('relevant_periods')),
                    metadata.get('last_scrape_during_grace_period')
                )
            )

def get_course_data_by_keys(keys):
    """Fetches course data for a list of instance keys."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT instance_key, data FROM courses WHERE instance_key = ANY(%s)", (keys,))
            rows = cur.fetchall()
            return {row[0]: row[1] for row in rows}

def update_course_data(instance_key, course_code, data):
    """Inserts or updates course data."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO courses (instance_key, course_code, data)
                VALUES (%s, %s, %s)
                ON CONFLICT (instance_key) DO UPDATE SET
                    data = EXCLUDED.data,
                    updated_at = NOW();
                """,
                (instance_key, course_code, json.dumps(data))
            )

def find_courses_by_name_db(search_query):
    """Finds course codes by searching for a query in the course names within the JSONB data."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # The query is case-insensitive and searches within the 'course_name' field of the JSONB data.
            # The `->>` operator extracts the JSON field as text.
            query = """
                SELECT DISTINCT course_code
                FROM courses
                WHERE data->>'course_name' ILIKE %s;
            """
            cur.execute(query, ('%' + search_query + '%',))
            rows = cur.fetchall()
            return sorted([row[0] for row in rows])

def get_last_name(full_name: str) -> str:
    """
    Extracts the last name from a full name string.
    """
    if not full_name:
        return ""
    return full_name.strip().split()[-1].lower()

def find_instructor_variants_db(instructor_name):
    """
    Finds variations of an instructor's name from the database based on last name.
    """
    target_last_name = get_last_name(instructor_name)
    if not target_last_name:
        return [instructor_name]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # This query finds all unique instructor names where the last part of the name matches.
            # It's a simplified way to match by last name.
            query = """
                SELECT DISTINCT data->>'instructor_name'
                FROM courses
                WHERE lower(split_part(data->>'instructor_name', ' ', -1)) = %s;
            """
            cur.execute(query, (target_last_name,))
            rows = cur.fetchall()
            variants = {row[0] for row in rows}
            variants.add(instructor_name) # Ensure the original name is included
            return sorted(list(variants))
