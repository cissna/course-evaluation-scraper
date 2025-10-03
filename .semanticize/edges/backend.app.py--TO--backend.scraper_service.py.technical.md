The `backend/app.py` (Flask API server) acts as a client to the `backend/scraper_service.py` module, which contains the core business logic for data retrieval, scraping orchestration, and caching management.

### 1. Imports and Dependencies

`backend/app.py` imports several functions directly from `.scraper_service`:

*   `get_course_data_and_update_cache`
*   `find_courses_by_name`
*   `find_courses_by_name_with_details`
*   `force_recheck_course`
*   `get_course_grace_status`

### 2. Function Calls and Data Flow

The API endpoints in `app.py` rely entirely on these imported functions to fulfill requests:

| API Endpoint (app.py) | Function Called (scraper_service.py) | Input Data | Return Data Flow |
| :--- | :--- | :--- | :--- |
| `/api/course/<course_code>` | `get_course_data_and_update_cache(course_code)` | `course_code` (validated/uppercased) | Returns raw course JSON data or an error dictionary (which `app.py` converts to a 404/500 HTTP response). |
| `/api/search/course_name/<query>` | `find_courses_by_name(search_query)` | `search_query` (URL-decoded) | Returns a list of course codes. |
| `/api/search/course_name_detailed/<query>` | `find_courses_by_name_with_details(search_query, limit, offset)` | `search_query`, `limit`, `offset` (from request args) | Returns a dictionary containing `results`, `total_count`, and `search_query`. |
| `/api/grace-status/<course_code>` | `get_course_grace_status(course_code)` | `course_code` (validated/uppercased) | Returns a status dictionary (e.g., `{"needs_warning": True, ...}`). |
| `/api/recheck/<course_code>` (POST) | `force_recheck_course(course_code)` | `course_code` (validated/uppercased) | Returns raw course JSON data or an error dictionary (triggers a scrape bypassing standard cache checks). |

### 3. Data Processing in `/api/analyze/<course_code>`

The `/api/analyze` endpoint in `app.py` has a complex interaction:

1.  It calls `get_course_data_and_update_cache(course_code)` to fetch the primary course data, ensuring the cache is updated if necessary.
2.  It interacts with `grouping_service` (imported from `.course_grouping_service`), which is also instantiated in `scraper_service.py`.
3.  Crucially, for grouped courses, it *re-calls* `get_course_data_and_update_cache(grouped_code)` for each related course code found via the grouping service. This demonstrates that the scraping/caching logic in `scraper_service.py` is the single source of truth for retrieving raw evaluation data, even when assembling complex responses in the API layer.

### Summary

`backend/scraper_service.py` encapsulates all external interaction logic (HTTP requests via `requests`, DB access via `.db_utils`, and core scraping via `workflow_helpers` and `scraping_logic`). `backend/app.py` serves purely as the HTTP request handler, validator, and formatter, delegating all data retrieval and manipulation tasks to the imported functions in `scraper_service.py`.