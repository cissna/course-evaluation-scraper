The `scraper_service.py` file imports several functions and classes from `db_utils.py` to interact with the database layer, primarily for retrieving and updating course metadata and fetching actual course data.

**Specific Function Calls and Imports:**

1.  **Import:**
    ```python
    from .db_utils import (
        get_course_metadata,
        get_course_data_by_keys,
        update_course_metadata,
        find_courses_by_name_db,
        find_courses_by_name_with_details_db,
        count_courses_by_name_db
    )
    ```

2.  **`get_course_data_and_update_cache` function:**
    *   Calls `get_course_metadata(course_code)`: Used to fetch existing metadata for a course.
        *   *Data Flow:* Receives a dictionary representing metadata or `None`.
    *   Calls `is_course_up_to_date(...)` (imported from `.period_logic`, not `db_utils`).
    *   Calls `get_course_data_by_keys(relevant_keys)`: Used to retrieve cached course data when the course is determined to be up-to-date.
        *   *Data Flow:* `relevant_keys` is a list obtained from metadata. Returns a dictionary of course data keyed by instance key.
    *   Calls `update_course_metadata(course_code, metadata)`: Used when authentication fails during scraping to mark the metadata record as failed (`last_period_failed=True`).
        *   *Data Flow:* Receives the `course_code` and the potentially updated `metadata` dictionary, which is then persisted to the DB.

3.  **`get_course_grace_status` function:**
    *   Calls `get_course_metadata(course_code)`: Used to retrieve grace period tracking information.

4.  **`find_courses_by_name` function:**
    *   Calls `find_courses_by_name_db(search_query)`: Delegates the database search for course codes based on name.
        *   *Data Flow:* Returns a list of course codes matching the query.

5.  **`find_courses_by_name_with_details` function:**
    *   Calls `count_courses_by_name_db(search_query)`: Fetches the total count of matching groups.
    *   Calls `find_courses_by_name_with_details_db(search_query, limit, offset)`: Fetches the paginated, grouped, and deduplicated search results.
        *   *Data Flow:* Both functions return aggregated counts or structured lists required for the API response.

**Technical Interaction Summary:**

The relationship is a standard service-to-utility dependency. `scraper_service.py` acts as the orchestration layer, deciding *when* to interact with the database (e.g., check freshness, update failure status, fetch cached data) by calling specific, narrow functions provided by `db_utils.py`. The data passed to `db_utils` functions is typically strings (course codes, search queries) or dictionaries (metadata), and the returned data is structured data retrieved from the PostgreSQL database via `psycopg2` connections managed within `db_utils.py`.