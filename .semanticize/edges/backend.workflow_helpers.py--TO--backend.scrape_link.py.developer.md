The `backend/workflow_helpers.py` file acts as the orchestrator for course data collection, and it **consumes** the specific report scraping functionality provided by `backend/scrape_link.py`.

**High-Level Interaction:**
The interaction is a direct function call where `workflow_helpers.py` initiates the detailed data extraction process for a specific evaluation report link.

**Functionality Used:**
`workflow_helpers.py` calls `scrape_evaluation_data` imported from `scrape_link.py`. This function is responsible for making the final HTTP request to a report URL, parsing the HTML using BeautifulSoup, extracting structured data (like quality frequencies, instructor names, etc.) from hidden JSON fields, and handling transient network errors via retries with exponential backoff.

**General Interaction Patterns:**
1.  **Orchestration/Delegation:** `workflow_helpers.py` iterates through a calculated set of report links (`links_to_process`).
2.  **Data Retrieval:** For each link, it delegates the actual retrieval and parsing job to `scrape_evaluation_data`.
3.  **Error Handling:** `workflow_helpers.py` checks the return value of `scrape_evaluation_data` for a `scrape_failed` flag to decide whether to continue processing the batch or halt.

**Component-Level Relationship:**
*   `backend/scrape_link.py` provides low-level, robust utility for scraping a *single* data point (evaluation report).
*   `backend/workflow_helpers.py` provides high-level workflow logic (finding all links, deciding scraping strategy, applying grace period logic) and uses `scrape_link.py` as a necessary tool in its "Unified Scraping" phase.