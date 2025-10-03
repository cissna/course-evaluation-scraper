The `backend/scraper_service.py` file **imports and calls** the function `scrape_course_data_core` from `backend/workflow_helpers.py` (imported as `from .workflow_helpers import scrape_course_data_core`).

1.  **`get_course_data_and_update_cache` (Source) calls `scrape_course_data_core` (Target):**
    *   It calls `scrape_course_data_core(course_code, session, skip_grace_period_logic=False)`.
    *   It passes the `course_code` (string), the authenticated `session` object (of type `requests.Session`), and sets `skip_grace_period_logic` to `False`.
    *   The return value (`result`) is expected to be a dictionary containing `'success'` (boolean) and either `'error'` or `'data'`.

2.  **`force_recheck_course` (Source) calls `scrape_course_data_core` (Target):**
    *   It calls `scrape_course_data_core(course_code, session, skip_grace_period_logic=True)`.
    *   It passes the `course_code` (string), the authenticated `session` object, and sets `skip_grace_period_logic` to `True`.
    *   The return value (`result`) is expected to be a dictionary containing `'success'` (boolean) and either `'error'` or `'data'`.

**Data Flow/Interaction:**
`scraper_service.py` acts as the orchestrator layer, using cached data checks (`is_course_up_to_date`, `get_course_metadata`, etc.) before delegating the actual heavy lifting of fetching links and scraping data to `workflow_helpers.py` via `scrape_course_data_core`.

**Note on Reversal (Target importing Source dependencies):**
While the primary relationship is the call from Source to Target, it is notable that `workflow_helpers.py` imports several utilities that are also imported by `scraper_service.py`, such as `get_course_metadata`, `get_course_data_by_keys`, `get_authenticated_session`, `get_current_period`, and `get_year_from_period_string`. This indicates a shared dependency structure on database utilities (`db_utils`) and period/authentication logic. However, the direct functional dependency is strictly unidirectional: `scraper_service.py` depends on the execution of `scrape_course_data_core` defined in `workflow_helpers.py`.