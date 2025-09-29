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

def find_courses_by_name_with_details_db(search_query, limit=None, offset=None):
    """Finds course codes and names by searching for a query in the course names within the JSONB data.
    Deduplicates by course code, applies course groupings, and returns the most recent course name for each group."""
    from .course_grouping_service import CourseGroupingService

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all matching courses with their names and timestamps, ordering by updated_at DESC to get most recent first
            query = """
                SELECT DISTINCT ON (course_code)
                       course_code,
                       data->>'course_name' as course_name,
                       updated_at
                FROM courses
                WHERE data->>'course_name' ILIKE %s
                ORDER BY
                    course_code,
                    SUBSTRING(instance_key FROM '..(\\d{2})$') DESC,
                    CASE SUBSTRING(instance_key FROM '..(FA|SP|SU|IN)..$')
                        WHEN 'FA' THEN 3
                        WHEN 'SU' THEN 2
                        WHEN 'SP' THEN 1
                        ELSE 0
                    END DESC;
            """
            cur.execute(query, ('%' + search_query + '%',))
            rows = cur.fetchall()

            # Create course grouping service
            grouping_service = CourseGroupingService()

            # Group courses and find the most recent name for each group
            processed_groups = set()
            grouped_results = []

            for course_code, course_name, updated_at in rows:
                # Skip if this course is already part of a processed group
                if course_code in processed_groups:
                    continue

                # Get all courses in this group
                group_courses = grouping_service.get_grouped_courses(course_code)

                # Mark all courses in this group as processed
                processed_groups.update(group_courses)

                # Find the most recent course name among all courses in the group
                most_recent_name = course_name
                most_recent_timestamp = updated_at
                courses_with_data = {course_code}

                # Check if any other courses in the group have more recent names
                for other_course in group_courses:
                    if other_course != course_code:
                        # Get the most recent name for this other course
                        other_query = """
                            SELECT data->>'course_name' as course_name, updated_at
                            FROM courses
                            WHERE course_code = %s
                            ORDER BY updated_at DESC
                            LIMIT 1;
                        """
                        cur.execute(other_query, (other_course,))
                        other_result = cur.fetchone()
                        if other_result:
                            courses_with_data.add(other_course)
                            if other_result[1] > most_recent_timestamp:
                                most_recent_name = other_result[0]
                                most_recent_timestamp = other_result[1]

                # Create display name - if multiple courses, join with "/"
                if len(courses_with_data) > 1:
                    display_code = "/".join(sorted(list(courses_with_data)))
                else:
                    display_code = course_code

                grouped_results.append({
                    "course_code": display_code,
                    "course_name": most_recent_name,
                    "group_courses": sorted(group_courses),  # For selection purposes
                    "primary_course": course_code  # The course that matched the search
                })

            # Sort results to prioritize exact matches
            def sort_key(result):
                course_name_lower = result["course_name"].lower().strip() if result["course_name"] else ""
                search_lower = search_query.lower().strip()

                if course_name_lower == search_lower:
                    return (1, result["course_code"])  # Exact match
                elif course_name_lower.startswith(search_lower):
                    return (2, result["course_code"])  # Starts with
                else:
                    return (3, result["course_code"])  # Contains

            sorted_results = sorted(grouped_results, key=sort_key)

            # Apply pagination if specified
            if offset is not None:
                sorted_results = sorted_results[offset:]
            if limit is not None:
                sorted_results = sorted_results[:limit]

            return sorted_results

def count_courses_by_name_db(search_query):
    """Counts the total number of unique course groups matching a search query."""
    from .course_grouping_service import CourseGroupingService

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all matching course codes
            query = """
                SELECT DISTINCT course_code
                FROM courses
                WHERE data->>'course_name' ILIKE %s;
            """
            cur.execute(query, ('%' + search_query + '%',))
            rows = cur.fetchall()
            course_codes = [row[0] for row in rows]

            # Group courses and count unique groups
            grouping_service = CourseGroupingService()
            processed_groups = set()
            group_count = 0

            for course_code in course_codes:
                if course_code in processed_groups:
                    continue

                group_courses = grouping_service.get_grouped_courses(course_code)
                processed_groups.update(group_courses)
                group_count += 1

            return group_count

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
