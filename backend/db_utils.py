import os
import psycopg2
import json
import logging
from contextlib import contextmanager
from dotenv import load_dotenv
from .percentiles import BENCHMARK_VERSION, REBUILD_AFTER_EVALUATIONS, build_benchmark

load_dotenv()

@contextmanager
def get_db_connection():
    """Establishes a connection to the database."""
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        raise Exception("DATABASE_URL environment variable not set.")
    conn = psycopg2.connect(conn_string, connect_timeout=10)
    try:
        with conn:
            yield conn
    finally:
        conn.close()

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

def _course_search_filter(search_query):
    """Match literal title text or a course-code fragment with optional periods."""
    def contains_pattern(value):
        escaped = value.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        return "%" + escaped + "%"

    code_query = search_query.replace(".", "").strip()
    # NULL keeps a query consisting only of periods from matching every code.
    code_pattern = contains_pattern(code_query) if code_query else None
    return """(
        data->>'course_name' ILIKE %s ESCAPE '!'
        OR REPLACE(course_code, '.', '') ILIKE %s ESCAPE '!'
    )""", (contains_pattern(search_query), code_pattern)


def find_courses_by_name_db(search_query):
    """Finds course codes by a case-insensitive title or course-code fragment."""
    search_filter, params = _course_search_filter(search_query)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = f"""
                SELECT DISTINCT course_code
                FROM courses
                WHERE {search_filter};
            """
            cur.execute(query, params)
            rows = cur.fetchall()
            return sorted([row[0] for row in rows])

def find_courses_by_name_with_details_db(search_query, limit=None, offset=None):
    """Finds course codes and names by a title or course-code fragment.
    Deduplicates by course code, applies course groupings, and returns the most recent course name for each group."""
    from .course_grouping_service import CourseGroupingService

    search_filter, params = _course_search_filter(search_query)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all matching courses with their names and timestamps, ordering by updated_at DESC to get most recent first
            query = f"""
                SELECT DISTINCT ON (course_code)
                       course_code,
                       data->>'course_name' as course_name,
                       updated_at
                FROM courses
                WHERE {search_filter}
                ORDER BY
                    course_code,
                    SUBSTRING(instance_key FROM '..(\\d{{2}})$') DESC,
                    CASE SUBSTRING(instance_key FROM '..(FA|SP|SU|IN)..$')
                        WHEN 'FA' THEN 3
                        WHEN 'SU' THEN 2
                        WHEN 'SP' THEN 1
                        ELSE 0
                    END DESC;
            """
            cur.execute(query, params)
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

            # Preserve title relevance while also prioritizing code matches.
            search_lower = search_query.lower().strip()
            code_query = search_lower.replace(".", "")

            def sort_key(result):
                course_name_lower = result["course_name"].lower().strip() if result["course_name"] else ""
                title_rank = 1 if course_name_lower == search_lower else 2 if course_name_lower.startswith(search_lower) else 3
                code_rank = 3
                if code_query:
                    codes = [code.replace(".", "").lower() for code in result["course_code"].split("/")]
                    if code_query in codes:
                        code_rank = 1
                    elif any(code.startswith(code_query) for code in codes):
                        code_rank = 2
                return (min(title_rank, code_rank), result["course_code"])

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

    search_filter, params = _course_search_filter(search_query)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get all matching course codes
            query = f"""
                SELECT DISTINCT course_code
                FROM courses
                WHERE {search_filter};
            """
            cur.execute(query, params)
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


def find_professors_by_name_db(query, limit=20, offset=0):
    """Search recorded names without resolving them to surname/initial variants."""
    pattern = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    names_sql = """
        SELECT DISTINCT evaluation_instructor_name(data) AS name
        FROM courses
        WHERE evaluation_instructor_name(data) ILIKE %s
    """
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute('SELECT count(*) FROM (' + names_sql + ') AS matches', (pattern,))
        total = cur.fetchone()[0]
        cur.execute(names_sql + ' ORDER BY name LIMIT %s OFFSET %s', (pattern, limit, offset))
        results = [{'type': 'professor', 'name': row[0]} for row in cur.fetchall()]
    return {'results': results, 'total_count': total}


def get_professor_records(name):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT instance_key, course_code, data FROM courses
            WHERE evaluation_instructor_name(data) = %s
        """, (name,))
        return cur.fetchall()


def get_records_for_courses(codes):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute('SELECT instance_key, course_code, data FROM courses WHERE course_code = ANY(%s)', (list(codes),))
        return cur.fetchall()


def get_all_evaluation_records():
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute('SELECT instance_key, course_code, data FROM courses')
        return cur.fetchall()


def get_refresh_metadata(course_code):
    """Use the DB clock for active leases and the evaluations for data revisions."""
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT m.*, COALESCE(m.scrape_lock_expires_at > clock_timestamp(), FALSE) AS in_progress,
                   (SELECT max(updated_at) FROM courses WHERE course_code = m.course_code) AS data_updated_at
            FROM course_metadata m WHERE m.course_code = %s
        """, (course_code,))
        row = cur.fetchone()
        return dict(zip([d[0] for d in cur.description], row)) if row else None


def claim_scrape_lock(course_code, ttl_seconds):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO course_metadata(course_code, relevant_periods) VALUES (%s, '[]'::JSONB)
            ON CONFLICT(course_code) DO NOTHING
        """, (course_code,))
        cur.execute("""
            UPDATE course_metadata
            SET scrape_lock_expires_at = clock_timestamp() + %s * interval '1 second'
            WHERE course_code = %s AND
                  (scrape_lock_expires_at IS NULL OR scrape_lock_expires_at <= clock_timestamp())
            RETURNING scrape_lock_expires_at
        """, (ttl_seconds, course_code))
        row = cur.fetchone()
        return row[0] if row else None


def renew_scrape_lock(course_code, claimed_expiry, ttl_seconds):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            UPDATE course_metadata
            SET scrape_lock_expires_at = clock_timestamp() + %s * interval '1 second'
            WHERE course_code = %s AND scrape_lock_expires_at = %s
                  AND scrape_lock_expires_at > clock_timestamp()
            RETURNING scrape_lock_expires_at
        """, (ttl_seconds, course_code, claimed_expiry))
        row = cur.fetchone()
        return row[0] if row else None


def release_scrape_lock(course_code, claimed_expiry):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            UPDATE course_metadata SET scrape_lock_expires_at = NULL
            WHERE course_code = %s AND scrape_lock_expires_at = %s
        """, (course_code, claimed_expiry))
        return cur.rowcount == 1


def update_course_metadata_owned(course_code, metadata, claimed_expiry):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            UPDATE course_metadata SET last_period_gathered = %s, last_period_failed = %s,
                relevant_periods = %s, last_scrape_during_grace_period = %s, updated_at = NOW()
            WHERE course_code = %s AND scrape_lock_expires_at = %s
                  AND scrape_lock_expires_at > clock_timestamp()
        """, (metadata.get('last_period_gathered'), metadata.get('last_period_failed', False),
              json.dumps(metadata.get('relevant_periods') or []), metadata.get('last_scrape_during_grace_period'),
              course_code, claimed_expiry))
        return cur.rowcount == 1


def update_course_data_owned(instance_key, course_code, data, claimed_expiry):
    with get_db_connection() as conn, conn.cursor() as cur:
        # Hold the metadata row lock until the evaluation write commits. A new
        # owner cannot claim the lease between the ownership check and publish.
        cur.execute("""
            SELECT course_code FROM course_metadata
            WHERE course_code = %s AND scrape_lock_expires_at = %s
                  AND scrape_lock_expires_at > clock_timestamp()
            FOR UPDATE
        """, (course_code, claimed_expiry))
        if cur.fetchone() is None:
            return False
        cur.execute("""
            INSERT INTO courses(instance_key, course_code, data) VALUES (%s, %s, %s)
            ON CONFLICT(instance_key) DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()
        """, (instance_key, course_code, json.dumps(data)))
        return True


def get_percentile_benchmark():
    """Serve the saved mapping, rebuilding only when missing or due."""
    try:
        return refresh_percentile_benchmark()
    except Exception:
        # A failed rebuild must not hide an otherwise usable saved snapshot.
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT payload FROM percentile_benchmarks WHERE benchmark_id = 'current'")
            row = cur.fetchone()
        if row and row[0].get('version') == BENCHMARK_VERSION:
            logging.getLogger(__name__).exception('Percentile rebuild failed; serving the previous snapshot.')
            return row[0]
        raise


def _percentile_rebuild_due(row):
    return not row or row[0].get('version') != BENCHMARK_VERSION or row[1] >= REBUILD_AFTER_EVALUATIONS


def refresh_percentile_benchmark(force=False):
    """Atomically rebuild and reset the insertion counter across backend instances."""
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT payload, pending_evaluations FROM percentile_benchmarks WHERE benchmark_id = 'current'")
        row = cur.fetchone()
        if not force and not _percentile_rebuild_due(row):
            return row[0]
        if row is None:
            cur.execute("""
                INSERT INTO percentile_benchmarks(benchmark_id, payload) VALUES ('current', '{}'::JSONB)
                ON CONFLICT(benchmark_id) DO NOTHING
            """)
        # The insertion trigger takes this same row lock. New inserts wait until
        # the snapshot commits, then count toward the next rebuild. No increments
        # can be lost between reading all evaluations and resetting the counter.
        cur.execute("""
            SELECT payload, pending_evaluations FROM percentile_benchmarks
            WHERE benchmark_id = 'current' FOR UPDATE
        """)
        row = cur.fetchone()
        if not force and not _percentile_rebuild_due(row):
            return row[0]
        cur.execute('SELECT instance_key, course_code, data FROM courses')
        payload = build_benchmark(cur.fetchall())
        cur.execute("""
            UPDATE percentile_benchmarks
            SET payload = %s, generated_at = %s, pending_evaluations = 0
            WHERE benchmark_id = 'current'
        """, (json.dumps(payload), payload['generated_at']))
        return payload
