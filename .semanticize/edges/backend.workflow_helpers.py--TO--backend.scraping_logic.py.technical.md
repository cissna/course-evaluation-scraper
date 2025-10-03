**Usage and Data Flow:**

1.  **`scrape_course_data_core` (in `workflow_helpers.py`)** calls `get_authenticated_session` when `session is None` during the setup phase of scraping a course.
    ```python
    # In workflow_helpers.py:
    if session is None:
        try:
            session = get_authenticated_session()
        except requests.exceptions.RequestException as e:
            # ... error handling
    ```

2.  **`get_authenticated_session` (in `scraping_logic.py`)** handles the creation and authentication of an HTTP session using `requests.Session()` and accessing a configuration variable `AUTH_URL` (imported from `.config`).

3.  **Return Value:** `get_authenticated_session` returns a fully configured and authenticated `requests.Session` object, which is then used by `scrape_course_data_core` (and potentially other functions in `workflow_helpers.py`) for subsequent scraping requests (e.g., calling `get_evaluation_report_links`).

4.  **Error Handling:** `workflow_helpers.py` wraps the call in a `try...except requests.exceptions.RequestException`, acknowledging that session acquisition might fail, as detailed in the target function's docstring.