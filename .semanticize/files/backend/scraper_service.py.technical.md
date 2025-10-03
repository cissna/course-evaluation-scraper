# Technical Documentation: `backend/scraper_service.py`

## 1. Module Overview

This module serves as the primary service layer for handling all course data operations. It acts as an intermediary between the Flask API endpoints (`app.py`) and the underlying business logic, including database interactions (`db_utils.py`), scraping orchestration (`workflow_helpers.py`), and session management (`scraping_logic.py`).

Its core responsibilities are:
- Providing a unified interface to fetch course evaluation data.
- Implementing a caching strategy by checking the database for fresh data before initiating a new scrape.
- Orchestrating the scraping workflow when data is stale or missing.
- Handling forced re-scrapes initiated by a user.
- Providing status information about a course's grace period.
- Exposing database search functionalities for finding courses by name.

## 2. Dependencies

- `requests`: For handling HTTP exceptions during session authentication.
- `datetime`, `dateutil`: For date-based calculations related to grace periods.
- `.course_grouping_service`: Used to group cross-listed courses (instance created but not directly used in the functions shown).
- `.workflow_helpers`: Contains the core scraping orchestration logic (`scrape_course_data_core`).
- `.db_utils`: Provides all functions for interacting with the PostgreSQL database (getting/setting metadata and course data).
- `.scraping_logic`: Handles the logic for obtaining an authenticated session for the scraping website.
- `.config`: Provides application-level constants like `PERIOD_RELEASE_DATES` and `PERIOD_GRACE_MONTHS`.
- `.period_logic`: Contains helper functions for determining the current academic period and checking if course data is up-to-date or within a grace period.

## 3. Custom Exceptions

### `SessionExpiredException`
- **Description**: A custom exception class intended to be raised when an authenticated session is determined to have expired.
- **Usage**: Defined in this module but intended to be used within the scraping logic to signal a need for re-authentication.

## 4. Functions

### `get_course_data_and_update_cache`
- **Signature**: `def get_course_data_and_update_cache(course_code: str) -> dict:`
- **Description**: This is the main entry point for fetching all evaluation data for a given course. It implements a read-through caching mechanism. It first checks the database for fresh data and only triggers a new scrape if the data is considered stale or non-existent.
- **Parameters**:
    - `course_code` (str): The unique identifier for the course (e.g., "AS.180.101").
- **Returns**:
    - `dict`: A dictionary containing either the aggregated course data for all relevant periods or an "error" key with a descriptive message.

- **Implementation Details**:
    1.  Calls `get_course_metadata(course_code)` to retrieve the course's status record from the database.
    2.  **Circuit Breaker**: It checks if the metadata contains `last_period_failed: true`. If so, it immediately returns an error to prevent repeated attempts on a known-failing course.
    3.  **Cache Check**: It calls `is_course_up_to_date()` from `period_logic`, which compares the `last_period_gathered` from the metadata with the current academic period.
    4.  **Cache Hit**: If the data is up-to-date, it retrieves the list of relevant instance keys from `metadata['relevant_periods']` and fetches all corresponding data from the `courses` table using `get_course_data_by_keys()`.
    5.  **Cache Miss**: If the data is stale or missing, it proceeds to scrape.
    6.  It calls `get_authenticated_session()` to get a `requests.Session` object with the necessary authentication cookies.
    7.  **Authentication Failure**: If session acquisition fails, it updates the course metadata to set `last_period_failed: true` and returns an authentication error. This prevents the system from trying again until the failure flag is cleared.
    8.  It calls the core scraping orchestrator, `scrape_course_data_core(course_code, session, skip_grace_period_logic=False)`. The `skip_grace_period_logic=False` flag ensures that the scraper respects the configured grace periods and avoids scraping for evaluations that may not have been released yet.
    9.  If the scrape fails, it propagates the error message from the result.
    10. On success, it returns the `data` field from the result of the scrape.

---

### `force_recheck_course`
- **Signature**: `def force_recheck_course(course_code: str) -> dict:`
- **Description**: Triggers a mandatory re-scrape of a course, bypassing the caching and grace period checks. This is designed for user-initiated updates.
- **Parameters**:
    - `course_code` (str): The unique identifier for the course.
- **Returns**:
    - `dict`: A dictionary containing the newly scraped course data or an "error" key.

- **Implementation Details**:
    1.  Acquires an authenticated session via `get_authenticated_session()`, handling failures similarly to the function above.
    2.  Calls `scrape_course_data_core(course_code, session, skip_grace_period_logic=True)`. The key difference is the `skip_grace_period_logic=True` argument, which instructs the core scraper to ignore any grace period checks and proceed with the scrape immediately.
    3.  Handles the success or failure of the scraping process and returns the data or an error message accordingly.

---

### `get_course_grace_status`
- **Signature**: `def get_course_grace_status(course_code: str) -> dict:`
- **Description**: Checks if a course was recently scraped during a "grace period" (i.e., a time when new evaluations were expected but not found). This is used by the frontend to display a warning to the user.
- **Parameters**:
    - `course_code` (str): The unique identifier for the course.
- **Returns**:
    - `dict`: A dictionary with the following structure:
        - `needs_warning` (bool): `True` if a warning should be shown.
        - `current_period` (str, optional): The current academic period.
        - `last_scrape_date` (str, optional): The ISO format date of the last scrape attempt during a grace period.

- **Implementation Details**:
    1.  Retrieves the course metadata using `get_course_metadata()`.
    2.  If no metadata exists, returns `{"needs_warning": False}`.
    3.  Checks for the existence of the `last_scrape_during_grace_period` timestamp in the metadata.
    4.  If the timestamp is present, it means a scrape was attempted when new data was expected but not found. It returns `needs_warning: True` along with the current period and the timestamp.

---

### `find_courses_by_name`
- **Signature**: `def find_courses_by_name(search_query: str) -> list:`
- **Description**: A simple passthrough function that searches for courses by name in the database.
- **Parameters**:
    - `search_query` (str): The search term to find within course names.
- **Returns**:
    - `list`: A list of course codes that match the search query.
- **Implementation Details**:
    1.  Directly calls and returns the result of `find_courses_by_name_db(search_query)`.

---

### `find_courses_by_name_with_details`
- **Signature**: `def find_courses_by_name_with_details(search_query: str, limit: int = None, offset: int = None) -> dict:`
- **Description**: Performs a paginated search for courses by name, returning detailed results along with the total count for the query.
- **Parameters**:
    - `search_query` (str): The search term.
    - `limit` (int, optional): The maximum number of results to return.
    - `offset` (int, optional): The starting position for the results (for pagination).
- **Returns**:
    - `dict`: A dictionary containing the search results, total count, and the original query.
        - `results` (list): A list of course objects (dictionaries) with details.
        - `total_count` (int): The total number of courses matching the query.
        - `search_query` (str): The original search query.

- **Implementation Details**:
    1.  Calls `count_courses_by_name_db(search_query)` to get the total number of matching records, which is used for frontend pagination controls.
    2.  Calls `find_courses_by_name_with_details_db(search_query, limit, offset)` to fetch the paginated list of detailed course information.
    3.  Packages the results, total count, and search query into a single dictionary for the response.