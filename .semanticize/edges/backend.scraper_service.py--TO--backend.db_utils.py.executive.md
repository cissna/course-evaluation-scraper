**Relationship:** Data Source and Persistence Layer Interaction

**Description:**

The `scraper_service.py` component is responsible for the core business logic of gathering external data (scraping) and determining if that data is fresh or needs updating. To perform this function, it relies entirely on `db_utils.py` as its **Persistence Interface**.

*   **Reading/Checking Status (Metadata):** The Scraper Service frequently asks `db_utils.py` (via functions like `get_course_metadata`) to check when data was last gathered or if previous attempts failed. This decision-making process (caching vs. scraping) is dependent on the database records managed by `db_utils.py`.
*   **Saving Results (Persistence):** Once scraping is successful or fails, the Scraper Service instructs `db_utils.py` (via `update_course_metadata`) to record the outcome, ensuring future checks leverage the latest status.
*   **Data Retrieval:** When data is deemed up-to-date, the service pulls the actual course content from storage using functions like `get_course_data_by_keys` provided by the utility layer.
*   **Search Functionality:** The service also uses `db_utils.py` to execute user-initiated searches against the stored course information.

In simple terms, **Scraper Service** is the worker that fetches and validates information, and **DB Utilities** is the secure, standardized gateway to the application's long-term memory (the database).