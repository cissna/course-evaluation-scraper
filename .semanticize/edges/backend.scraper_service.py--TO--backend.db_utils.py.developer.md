The `scraper_service.py` acts as a high-level service layer responsible for deciding when to scrape data versus retrieving cached data. It heavily relies on `db_utils.py` for all persistent data operations related to courses and metadata.

### High-Level Interaction

1.  **Data Retrieval and Caching Logic:** `scraper_service.py` uses functions from `db_utils.py` to implement caching strategies:
    *   It calls `db_utils.get_course_metadata(course_code)` to check the last scrape time.
    *   If the course is deemed up-to-date (using logic from other modules), it retrieves the actual course data using `db_utils.get_course_data_by_keys(relevant_keys)`.

2.  **Data Persistence (Post-Scraping):** When scraping is necessary (or forced), the results obtained from core scraping logic (not shown here, but implied by `result['data']`) are eventually intended to be persisted. While `scraper_service.py` doesn't directly call `update_course_data` (which is in `db_utils.py`), it *does* call `update_course_metadata` to record scrape status failures or successful updates. This function writes directly to the `course_metadata` table in the database via `db_utils.py`.

3.  **Search and Discovery:** The service layer exposes search functionality by delegating directly to the database utility functions:
    *   `scraper_service.find_courses_by_name` calls `db_utils.find_courses_by_name_db`.
    *   `scraper_service.find_courses_by_name_with_details` calls `db_utils.find_courses_by_name_with_details_db` and `db_utils.count_courses_by_name_db`.

### Component-Level Relationship

*   **Dependency:** `scraper_service.py` has a **hard dependency** on `db_utils.py`, importing 7 specific functions (`get_course_metadata`, `get_course_data_by_keys`, `update_course_metadata`, `find_courses_by_name_db`, `find_courses_by_name_with_details_db`, `count_courses_by_name_db`).
*   **Role Mapping:**
    *   **`scraper_service.py` (Service/Controller):** Orchestrates the workflow, applies business logic (caching checks, grace period checks), and decides *when* to read/write data.
    *   **`db_utils.py` (Data Access Layer - DAL):** Provides the raw interface for CRUD operations against the PostgreSQL database, handling connection management, SQL execution, and data serialization/deserialization (e.g., handling JSON fields).

In essence, `scraper_service.py` dictates *what* data is needed and *why*, and `db_utils.py` handles the technical mechanism of *how* to fetch or store that data.