The `backend/app.py` file acts as the **API Gateway and Orchestrator** for the application, handling incoming user requests (e.g., fetching course details, searching).

The `backend/db_utils.py` file acts as the **Data Persistence Layer** or the direct interface to the central data store (the database).

**Relationship:**

The Application layer (`app.py`) relies on the Data Layer (`db_utils.py`) to perform specific, persistent data operations required to fulfill user requests.

1.  **Data Retrieval:** When a user requests course data (`/api/course/<course_code>`), `app.py` might call helper functions that ultimately use `db_utils.update_course_data` or `db_utils.get_course_data_by_keys` (though `app.py` uses a scraper service first, the underlying data storage mechanism is managed by `db_utils.py`).
2.  **Searching:** When searching by instructor name (`/api/search/instructor/<instructor_name>`), `app.py` directly calls `db_utils.find_instructor_variants_db` to query the database for name variations.
3.  **Complex Searches:** For detailed course searches, `app.py` calls `db_utils.find_courses_by_name_with_details_db` (via its own internal service logic) to handle complex lookups involving course grouping logic that requires direct database access.

In essence, **`app.py` is the front-facing service that delegates long-term data reading and writing tasks to `db_utils.py` to ensure data integrity and persistence.**