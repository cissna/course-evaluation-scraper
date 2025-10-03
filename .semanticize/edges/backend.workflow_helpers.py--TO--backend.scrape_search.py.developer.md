The source file, `backend/workflow_helpers.py`, acts as a **consumer** of the functionality provided by the target file, `backend/scrape_search.py`.

**High-Level Interaction:**

1.  **Functionality Used:** `workflow_helpers.py` imports and uses the function `get_evaluation_report_links` from `scrape_search.py`. This function is responsible for interfacing with the external evaluation website to discover URLs for course evaluation reports.

2.  **General Interaction Patterns:**
    *   **Link Discovery:** `workflow_helpers.py` calls `get_evaluation_report_links` multiple times within its complex scraping logic (both for the main course code and within the section-by-section fallback, `get_all_links_by_section`).
    *   **Session Passing:** An authenticated `requests.Session` object, created in `workflow_helpers.py` (via `get_authenticated_session`), is passed to `get_evaluation_report_links` to maintain state during the scraping process.
    *   **Contextual Filtering:** In the pagination handling logic within `scrape_course_data_core`, `get_evaluation_report_links` is called repeatedly, passing the `year` parameter to fetch links specific to that academic year. In the section fallback, it's called with a modified `section_course_code` as the primary identifier.
    *   **Output Consumption:** `workflow_helpers.py` consumes the tuple returned by the function: the dictionary of `links` (mapping instance codes to URLs) and a boolean indicating if pagination (`has_more`) was detected. This pagination status is crucial for deciding whether to proceed with advanced scraping strategies (like year-by-year scanning or section-by-section scanning).

**Component-Level Relationship:**

*   **`backend/scrape_search.py` (Target):** Acts as the **Scraping Interface Layer**. It handles the HTTP requests, URL construction specific to the evaluation website structure, parsing HTML using BeautifulSoup, and extracting raw report links based on various optional filters (course code, year, instructor, etc.). It abstracts the complexity of direct HTTP interaction and HTML parsing.
*   **`backend/workflow_helpers.py` (Source):** Acts as the **Orchestrator/Workflow Manager**. It uses the output of `get_evaluation_report_links` to drive its high-level data gathering workflow. It decides *when* and *how* to call the link discovery function based on metadata stored locally (e.g., `last_period_gathered`) and the pagination status returned by the target function.