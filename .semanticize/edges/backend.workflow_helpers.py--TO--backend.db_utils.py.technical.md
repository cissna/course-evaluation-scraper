The file `backend/workflow_helpers.py` depends heavily on functions imported from `backend/db_utils.py` to interact with the underlying database for persistence and retrieval of course data and metadata.

**Specific Function Calls and Data Flow:**

1.  **`get_course_metadata(course_code)`**: Called at the start of `scrape_course_data_core` to retrieve existing metadata for a given `course_code`.
    *   **Data Flow**: `course_code` (string) is passed in. It returns a dictionary (metadata) or `None`.

2.  **`update_course_metadata(course_code, metadata)`**: Called multiple times in `scrape_course_data_core`:
    *   Immediately after retrieving metadata if it was missing (to initialize it).
    *   When an authentication session fails.
    *   When year-by-year scraping fails.
    *   In the finalization phase to persist updated state (`last_period_gathered`, grace period flags, etc.).
    *   **Data Flow**: `course_code` (string) and `metadata` (dictionary) are passed in for persistence.

3.  **`get_course_data_by_keys(keys)`**: Called within `scrape_course_data_core` before Phase 2 (Unified Scraping) to efficiently check which reports (identified by `instance_key`) already exist in the database.
    *   **Data Flow**: A list of `instance_key` strings is passed in. It returns a dictionary mapping existing keys to their stored data.

4.  **`update_course_data(instance_key, course_code, scraped_data)`**: Called inside the loop during Phase 2 whenever new evaluation data is successfully scraped. This function handles the insertion or update of the actual evaluation report content.
    *   **Data Flow**: `instance_key` (string), `course_code` (string), and `scraped_data` (dictionary) are passed in for database persistence.

**Technical Interaction Details:**

*   **Import:** `workflow_helpers.py` explicitly imports the required database utilities using a relative import: `from .db_utils import get_course_metadata, update_course_metadata, update_course_data, get_course_data_by_keys`.
*   **Purpose:** `workflow_helpers.py` manages the complex scraping logic (handling pagination, year iteration, section fallback via `get_all_links_by_section`), while `db_utils.py` is responsible solely for the CRUD operations against the PostgreSQL database (using `psycopg2`) to store the results of that scraping.
*   **Data Serialization:** Notice that when interacting with data structures, `workflow_helpers.py` handles Python dictionaries, which are serialized into JSON strings by the functions in `db_utils.py` (e.g., in `update_course_metadata` and `update_course_data`) before being written to the database columns (which are assumed to be JSON/JSONB).