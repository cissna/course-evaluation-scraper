The `workflow_helpers.py` file contains the core logic for scraping course evaluation data. Since scraping involves long-running, external operations, it needs a persistent place to store its findings and track its progress.

The relationship is that **`workflow_helpers.py` acts as the primary operational engine that reads from and writes results to the database managed by `db_utils.py`**.

Specifically:
1.  **Reading Configuration/State:** `workflow_helpers.py` calls functions in `db_utils.py` (e.g., `get_course_metadata`, `get_course_data_by_keys`) to check if data for a course already exists, what the last successful scrape time was, and what links to skip. This ensures the scraping process is efficient and avoids reprocessing old data.
2.  **Writing Results:** After successfully scraping new data (evaluation reports or course details), `workflow_helpers.py` uses functions in `db_utils.py` (e.g., `update_course_data`, `update_course_metadata`) to persist the newly collected information and update the state tracking tables.

In simple business terms, `workflow_helpers.py` is the **Data Collector/Processor**, and `db_utils.py` is the **Centralized Data Repository and State Manager**. The Processor relies entirely on the Repository to know what to do next and where to save its findings.