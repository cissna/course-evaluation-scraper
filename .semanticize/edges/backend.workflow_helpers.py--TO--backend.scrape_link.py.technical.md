The file `backend/workflow_helpers.py` **imports and calls** the function `scrape_evaluation_data` from `backend/scrape_link.py`.

**Specific Interaction:**

1.  **Import:** `workflow_helpers.py` imports the target function via:
    ```python
    from .scrape_link import scrape_evaluation_data
    ```

2.  **Call Site:** `scrape_evaluation_data` is called within the `scrape_course_data_core` function inside the link processing loop (Phase 2):
    ```python
    for instance_key, link_url in sorted_links:
        # ... skip existing ...
        scraped_data = scrape_evaluation_data(link_url, session)
        # ... processing logic ...
    ```

3.  **Parameters Passed:**
    *   `link_url`: The URL string retrieved for a specific report (the second item in the `(instance_key, link_url)` tuple from `links_to_process`).
    *   `session`: The authenticated `requests.Session` object established earlier in `scrape_course_data_core` via `get_authenticated_session()`.

4.  **Data Flow/Return Value:**
    *   `scrape_evaluation_data` returns a dictionary (`scraped_data`).
    *   This dictionary is expected to contain the scraped evaluation details.
    *   `workflow_helpers.py` checks the returned dictionary for a failure marker:
        ```python
        if scraped_data and scraped_data.get("scrape_failed", False):
            # ... handle failure ...
            continue
        ```
    *   If successful, the returned data is used to update the database:
        ```python
        if scraped_data:
            update_course_data(instance_key, course_code, scraped_data)
            # ...
        ```

**Technical Summary:**
`workflow_helpers.py` acts as the orchestration layer, managing the collection of report links. When it possesses a valid `link_url` and an active `session`, it delegates the task of fetching the detailed data from that specific URL to `scrape_link.scrape_evaluation_data`. The result dictates whether the data is saved to the database or if the process for that specific report is marked as failed.