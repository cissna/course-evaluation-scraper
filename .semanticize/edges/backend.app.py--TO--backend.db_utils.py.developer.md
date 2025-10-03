The `backend/app.py` file, which serves as the main Flask application entry point, interacts heavily with `backend/db_utils.py` to persist and retrieve data handled by the API endpoints.

**High-Level Interaction:**
`app.py` acts as the API gateway, handling HTTP requests, validating input, and orchestrating business logic. It calls functions from `db_utils.py` primarily for persistence (saving data fetched by scrapers) and structured querying (searching for courses or instructors).

**Functionality Used:**
1.  **Data Persistence/Retrieval:** `app.py` calls `update_course_data` (implicitly via `get_course_data_and_update_cache` which likely uses it) to save scraped data, and `get_course_data_by_keys` when reconstructing grouped analysis data in the `/api/analyze` endpoint.
2.  **Search/Querying:**
    *   The `/api/search/instructor/<string:instructor_name>` endpoint calls `find_instructor_variants_db` to retrieve variations of an instructor's name from the database based on last name matching.
3.  **Metadata Handling:** While `app.py` reads `metadata.json` locally for the analysis endpoint, it relies on `db_utils.py` for database-backed metadata operations, although the specific functions (`get_course_metadata`, `update_course_metadata`) are not directly called in the provided `app.py` snippet (they are likely used by other services imported into `app.py`, such as `get_course_data_and_update_cache`).

**General Interaction Patterns:**
The interaction is standard service-to-data-access-layer:
*   **Request Handling:** `app.py` receives a request (e.g., instructor search).
*   **Data Access Call:** It delegates the complex database interaction (like SQL execution and JSONB querying) to the specific function in `db_utils.py` (e.g., `find_instructor_variants_db`).
*   **Response Formatting:** `db_utils.py` returns structured data (lists or dictionaries), which `app.py` then wraps in a Flask `jsonify` response.

**Component-Level Relationship:**
This represents a classic separation of concerns:
*   **`app.py` (API/Controller):** Manages HTTP routing, input validation, and orchestrates data flow between external services (like scraping, grouping) and the persistence layer.
*   **`db_utils.py` (Data Access Layer - DAL):** Encapsulates all logic related to connecting to PostgreSQL using `psycopg2` and executing specific SQL queries (including advanced JSONB operations) required by the application logic.