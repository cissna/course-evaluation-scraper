The `workflow_helpers.py` file acts as a **Service Consumer** that relies heavily on the data persistence and retrieval capabilities provided by `db_utils.py`.

**High-Level Interaction:**
The interaction is primarily **Data Access Layer (DAL) consumption**. `workflow_helpers.py` orchestrates complex scraping workflows (in `scrape_course_data_core` and `get_all_links_by_section`) and uses `db_utils.py` functions to manage state and persist results.

**Functionality Used:**
1.  **Metadata Management:** `workflow_helpers.py` calls `get_course_metadata` to retrieve the last successful scrape state and `update_course_metadata` to save updated state information (like `last_period_gathered`, failure flags, and relevant periods).
2.  **Data Persistence:** It calls `update_course_data` to save the actual scraped evaluation data for a specific course instance key.
3.  **Data Retrieval for Deduplication:** It calls `get_course_data_by_keys` to check which instance keys already exist in the database before attempting to scrape and write new data, which prevents redundant database writes during the main processing loop.

**General Interaction Patterns:**
*   **State Synchronization:** Before starting a scrape, metadata is read; after successfully processing data, metadata is updated.
*   **Batch Write/Check:** Before iterating over links to scrape, existing keys are fetched in bulk using `get_course_data_by_keys`. New data is then written individually using `update_course_data`.

**Component-Level Relationship:**
`workflow_helpers.py` is the **Orchestrator/Business Logic Layer**, handling scraping strategy, pagination, and grace period logic. `db_utils.py` serves as the **Data Access Layer**, abstracting all PostgreSQL interactions required by the orchestrator.