The file `backend/workflow_helpers.py` heavily relies on functions imported from `backend/period_logic.py` to manage temporal logic related to course scraping and data freshness.

**Imports from `backend/period_logic.py` into `backend/workflow_helpers.py`:**

1.  **`get_current_period`**: Called within `scrape_course_data_core` in the SETUP phase (to initialize metadata if missing, though not strictly used there) and critically in the FINALIZATION phase to compare against `last_period_gathered` and update metadata based on the current academic period.
    *   *Usage Example (Finalization Phase)*: `current_academic_year = get_year_from_period_string(get_current_period())` (inside `get_all_links_by_section`) and `current_period = get_current_period()` (inside `scrape_course_data_core`).

2.  **`is_grace_period_over`**: Used in the FINALIZATION phase of `scrape_course_data_core` to determine if a course update is considered timely even if data for the absolute current period isn't present, based on whether the grace period has elapsed.
    *   *Usage Example*: `elif is_grace_period_over(current_period):`

3.  **`get_period_from_instance_key`**: Used in the FINALIZATION phase to determine the period associated with newly scraped instance keys, which informs the update to `course_metadata['relevant_periods']`.
    *   *Usage Example*: `newly_scraped_periods = {get_period_from_instance_key(key) for key in links_to_process.keys() if key not in existing_course_keys}`

4.  **`get_year_from_period_string`**: Used in both `get_all_links_by_section` (to set the upper bound for year-based scraping) and in `scrape_course_data_core` (to determine the year associated with the last gathered period and the current academic year).
    *   *Usage Example (in `scrape_course_data_core`)*: `last_period_year = get_year_from_period_string(last_period)`

5.  **`find_latest_year_from_keys`**: Called in `scrape_course_data_core` when pagination is detected to find the latest year present in the initial set of links, helping to set the starting point (`smart_start_year`) for subsequent year-by-year scraping.
    *   *Usage Example*: `latest_initial_year = find_latest_year_from_keys(initial_links.keys())`

6.  **`find_oldest_year_from_keys`**: Called within `get_all_links_by_section` when section-level pagination is detected, used to find the minimum year present in the collected section links to establish a robust starting year for section-specific year iteration.
    *   *Usage Example*: `start_year = find_oldest_year_from_keys(keys)`

**Data Flow:**
`workflow_helpers.py` acts as the orchestrator, calling functions from `period_logic.py` to interpret dates, determine current academic context, and evaluate data freshness boundaries. It provides keys or period strings to `period_logic.py`, which returns integers (years), boolean flags (grace period status), or period strings necessary for controlling the scraping loops and finalizing metadata updates.