The `workflow_helpers.py` file imports and utilizes the `get_authenticated_session` function from `scraping_logic.py`.

**Interaction:**
1.  **Import:** `workflow_helpers.py` imports `get_authenticated_session` from the local module `.scraping_logic`.
2.  **Usage (Session Creation):** In `scrape_course_data_core`, if no existing `requests.Session` is provided, it calls `get_authenticated_session()` to obtain a pre-authenticated session object necessary for making subsequent authenticated requests to the scraping target (implied by the context of link gathering and data scraping).
3.  **Error Handling:** The call to `get_authenticated_session()` is wrapped in a `try...except` block in `scrape_course_data_core`, anticipating that the target function might raise a `requests.exceptions.RequestException` upon failure, as indicated by the documentation in `scraping_logic.py`.

This establishes a dependency where the core workflow logic relies on `scraping_logic.py` to initialize the necessary HTTP session capable of performing authenticated web requests.