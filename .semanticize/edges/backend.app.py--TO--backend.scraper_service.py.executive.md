The `backend/app.py` file acts as the **Public Interface** (API Gateway) for external users and frontend applications. It handles incoming web requests, validates input, and manages routing.

The `backend/scraper_service.py` file acts as the **Core Data Engine**. Its primary business function is to ensure the system has the most current course evaluation data by managing caching, database interactions, and orchestrating the actual data retrieval (scraping) when necessary.

**Relationship:**

The Public Interface (`app.py`) relies entirely on the Core Data Engine (`scraper_service.py`) to fulfill its primary data requests.

1.  **Data Retrieval:** When a user requests specific course data (e.g., via `/api/course/<course_code>`), `app.py` calls `scraper_service.get_course_data_and_update_cache`. This means the API cannot function without the service updating or providing the cached data.
2.  **Forced Updates:** When a user forces a data refresh, `app.py` calls `scraper_service.force_recheck_course`.
3.  **Status Checks:** For administrative or UI feedback, `app.py` calls `scraper_service.get_course_grace_status`.
4.  **Search Functionality:** `app.py` delegates all database searches for course names (`find_courses_by_name`, `find_courses_by_name_with_details`) to the corresponding database access functions exposed by `scraper_service.py`.

In summary, `scraper_service.py` handles the heavy lifting of data acquisition, validation, and caching, while `app.py` simply exposes these capabilities via a standardized web API.