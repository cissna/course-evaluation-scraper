The `workflow_helpers.py` file heavily **consumes** utility functions from `period_logic.py` to manage temporal aspects of course data scraping and metadata updates.

### Functionality Used:
1.  **Period Calculation & Comparison:**
    *   `get_current_period`: Used in `scrape_course_data_core` (Phase 3) to determine the current academic period for metadata updates and to calculate the target range for year-based scraping.
    *   `get_year_from_period_string`: Used both in `get_all_links_by_section` (to determine the starting year for section scanning) and in `scrape_course_data_core` (Phase 1) to compare the last gathered period year against the latest year found in initial links.
    *   `is_grace_period_over`: Used in `scrape_course_data_core` (Phase 3) to decide how to update `last_scrape_during_grace_period` metadata based on whether the current period's evaluation window has closed.
2.  **Key/Link Parsing:**
    *   `get_period_from_instance_key`: Used in `scrape_course_data_core` (Phase 3) to derive the period string from a scraped instance key, which is then used to update relevance tracking in course metadata.
    *   `find_latest_year_from_keys` and `find_oldest_year_from_keys`: These are critical for optimizing scraping in the paginated case within `scrape_course_data_core` and for setting bounds in `get_all_links_by_section`. They parse date codes embedded within the instance keys to determine historical context.

### Interaction Patterns:
The interaction is unidirectional: `workflow_helpers.py` acts as the **consumer/orchestrator**, calling various functions in `period_logic.py` to interpret dates, determine current status, and parse time-sensitive identifiers found in scraping results (instance keys).

The dependency is significant, as the core logic for deciding *when* to scrape more data (Phase 1 optimization) and *how* to update status flags after scraping (Phase 3 finalization) relies entirely on the time-aware functions provided by `period_logic.py`.

### Component-level Relationship:
`period_logic.py` provides the **Temporal Abstraction Layer** for the scraping workflow managed in `workflow_helpers.py`. It encapsulates the business rules regarding academic calendars, grace periods, and the conversion between raw instance keys and structured date information.