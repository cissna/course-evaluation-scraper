The `scraper_service.py` acts as a high-level orchestrator for fetching and validating course data. It **consumes (imports and uses)** several utility functions from `period_logic.py` to determine the freshness and validity of cached course data before initiating potentially expensive scraping operations.

**Key Interactions:**

1.  **State Checking (`is_course_up_to_date`):** `scraper_service.py` calls `is_course_up_to_date` within `get_course_data_and_update_cache`. This function relies on `period_logic.py` to compare the `last_period_gathered` metadata against the `get_current_period()` to decide if cached data is sufficient.
2.  **Current Context (`get_current_period`):** This function is called directly within `is_course_up_to_date` (and indirectly via `get_course_grace_status`) to establish the authoritative current academic period.
3.  **Grace Period Status (`is_course_grace_status`):** `scraper_service.py` calls `get_current_period` and uses the resulting period information to check against metadata related to grace period scraping.
4.  **Grace Period Calculation (Implicit):** While `is_grace_period_over` is imported, it is **not explicitly called** in the provided source code of `scraper_service.py`. However, its import indicates that the logic for determining when a grace period ends is made available to the scraper service if needed elsewhere, or perhaps was intended for use in an earlier iteration of the logic now handled by `is_course_up_to_date`.

**Component Relationship:**

*   **`scraper_service.py` (Consumer/Orchestrator):** Manages the primary workflow (check cache -> scrape if necessary). It depends on `period_logic.py` for time-based validity checks.
*   **`period_logic.py` (Provider/Utility Layer):** Provides the deterministic logic for interpreting dates, calculating the current academic period, and defining what constitutes "up-to-date" data based on configuration constants (`PERIOD_RELEASE_DATES`, `PERIOD_GRACE_MONTHS`).

This dependency structure suggests a clear separation of concerns: `scraper_service` handles I/O and workflow control, while `period_logic` handles temporal business rules.