The `backend/app.py` (Flask API server) acts as the **Client** or **Consumer** of the core data retrieval and utility logic encapsulated in `backend/scraper_service.py` (the Service Layer).

### High-Level Interaction

The relationship is a **Service Dependency** where the API endpoints in `app.py` rely heavily on functions exposed by `scraper_service.py` to fulfill client requests related to course data fetching, searching, and status checking.

1.  **Data Retrieval & Caching (`/api/course/<course_code>`):**
    *   `app.py` calls `get_course_data_and_update_cache(course_code)`. This function in `scraper_service.py` handles the primary workflow: checking cache staleness based on metadata, initiating necessary scraping via `scrape_course_data_core` if needed (after authenticating), and returning the processed data or an error.

2.  **Forced Update (`/api/recheck/<course_code>`):**
    *   `app.py` calls `force_recheck_course(course_code)`. This bypasses standard cache checks and forces a fresh scrape, relying on the service layer to handle authentication and core scraping execution (`scrape_course_data_core`).

3.  **Status Check (`/api/grace-status/<course_code>`):**
    *   `app.py` calls `get_course_grace_status(course_code)`. This function in the service layer reads metadata (likely from the DB, via imported `get_course_metadata`) to determine if the course data is still valid under grace period rules.

4.  **Searching:**
    *   `app.py` calls `find_courses_by_name(search_query)` and `find_courses_by_name_with_details(search_query, limit, offset)`. These functions in `scraper_service.py` abstract the database interaction needed for searching, utilizing DB utility functions imported within `scraper_service.py`.

### Component-Level Relationship

*   **`/app.py` (API Layer):** Handles HTTP requests, input validation (e.g., `validate_course_code`), URL decoding, CORS, JSON serialization/deserialization, and routing. It delegates all business logic concerning data freshness, scraping initiation, and persistent storage interaction to the service layer.
*   **`/scraper_service.py` (Service Layer):** Contains the coordination logic. It imports necessary components like `requests`, database utilities (`db_utils`), configuration (`config`), and the core scraping implementation (`workflow_helpers.scrape_course_data_core`). It orchestrates the primary user-facing functions that the API calls.

In summary, `app.py` is the presentation/API interface, and `scraper_service.py` is the backend engine responsible for data acquisition and state management.