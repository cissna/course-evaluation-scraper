# Technical Documentation: `backend/workflow_helpers.py`

## Overview

This module orchestrates the complex, multi-step workflow of scraping course evaluation data for a given course. It acts as the high-level controller, managing link discovery, data extraction, database interaction, and metadata updates. Its primary goal is to ensure data integrity and to employ optimized scraping strategies to handle the university's paginated and sometimes inconsistent evaluation portal.

The core logic is encapsulated in `scrape_course_data_core`, which intelligently decides how to gather evaluation report links, scrapes only new data, and meticulously updates a course's metadata to track its state, including handling "grace periods" for newly available evaluations.

---

## `get_all_links_by_section(session, course_code)`

This is a specialized helper function designed as a robust fallback for a critical edge case: when a single course has so many evaluations that they are paginated even within a single year's view. It systematically finds all evaluation report links by brute-forcing through every possible section number.

### Parameters

-   **`session` (`requests.Session`)**: An authenticated `requests` session object required to access the evaluation portal.
-   **`course_code` (`str`)**: The base course code (e.g., `AS.180.101`).

### Returns

-   **`dict`**: A dictionary where keys are unique `instance_key` strings (e.g., `AS.180.101.01_FA23_1`) and values are the corresponding direct URLs to the evaluation reports.

### Implementation Details

1.  **Initialization**: An empty dictionary `all_links` is created to aggregate results.
2.  **Section Iteration**: The function loops through integers from 0 to 99 (`for i in range(100)`).
3.  **Course Code Construction**: In each iteration, it formats a section-specific course code by appending the zero-padded section number (e.g., `AS.180.101.01`, `AS.180.101.02`).
4.  **Link Discovery**: It calls `get_evaluation_report_links` for the constructed `section_course_code`.
    -   **Exception Handling**: The call is wrapped in a `try...except` block. Since many section numbers will not exist, exceptions are expected, logged, and ignored, allowing the loop to continue.
5.  **Pagination Handling (Edge Case)**:
    -   If `get_evaluation_report_links` returns links and its `has_more` flag is `False`, the links are simply added to the `all_links` dictionary.
    -   If `has_more` is `True`, it signifies that this specific section has more than 20 reports, triggering a "Show more results" button. The function then switches to a more granular, year-by-year scan *for that specific section*:
        -   It determines a `start_year` to begin the scan (either from the oldest year in the links just found or defaulting to 2010).
        -   It iterates from the `start_year` to the current academic year + 2 (the buffer adds robustness).
        -   In each year, it calls `get_evaluation_report_links` again, but this time providing both the `section_course_code` and the `year`.
        -   The results from this yearly scan are aggregated into `section_yearly_links`, which are then added to the main `all_links` dictionary.

---

## `scrape_course_data_core(course_code, session=None, skip_grace_period_logic=True)`

This is the main function that executes the entire scraping and data storage workflow for a single course. It is designed to be idempotent and resilient, handling everything from initial setup to final metadata updates.

### Parameters

-   **`course_code` (`str`)**: The course code to be scraped (e.g., `AS.180.101`).
-   **`session` (`requests.Session`, optional)**: An optional pre-authenticated `requests` session. If `None`, the function will acquire one itself. Defaults to `None`.
-   **`skip_grace_period_logic` (`bool`, optional)**: This parameter is defined but not currently used within the function's logic. Defaults to `True`.

### Returns

-   **`dict`**: A dictionary summarizing the operation's result, containing:
    -   `'success'` (`bool`): `True` if the process completed without a hard failure that would lead to partial data.
    -   `'new_data_found'` (`bool`): `True` if at least one new evaluation report was scraped and saved.
    -   `'data'` (`dict`): A dictionary containing the full dataset for all relevant instances of the course, fetched from the database.
    -   `'metadata'` (`dict`): The final, updated metadata for the course.
    -   `'error'` (`str` | `None`): An error message if a batch failure occurred.

### Implementation Details

The function operates in four distinct phases:

#### Phase 0: Setup

1.  **Metadata Retrieval**: It calls `db_utils.get_course_metadata` to fetch the course's existing metadata.
2.  **New Course Initialization**: If no metadata is found, it creates a default metadata structure and immediately saves it via `db_utils.update_course_metadata`. This "touch" operation prevents foreign key constraint violations when course data is later inserted.
3.  **Session Authentication**: It ensures a valid, authenticated `requests.Session` is available by either using the one passed as an argument or calling `scraping_logic.get_authenticated_session`. If authentication fails, it updates the metadata to reflect the failure and returns immediately.

#### Phase 1: Link Collection

This phase determines the optimal strategy for discovering all evaluation report URLs.

1.  **Initial Fetch**: It performs an initial call to `scrape_search.get_evaluation_report_links` for the base `course_code`.
2.  **Strategy Selection**:
    -   **Simple Case**: If the initial fetch returns `has_more_initial = False`, there is no pagination. The `initial_links` are considered complete.
    -   **Paginated Case**: If `has_more_initial = True`, a more complex strategy is engaged to gather all links from subsequent pages.
        1.  **Optimized Yearly Scan**: Instead of clicking "Show more results," the logic initiates a year-by-year scan. It calculates a `smart_start_year` as the maximum of the `last_period_gathered` year and the latest year found in the `initial_links`. This prevents re-scanning years that are already known to be complete.
        2.  It then iterates from this `smart_start_year` up to the current academic year (+2 for safety), calling `get_evaluation_report_links` for each year.
        3.  **Critical Edge Case Handling**: If any of these yearly scans *also* returns `has_more_yearly = True`, it means a single year has >20 reports. The yearly scan is aborted, and the function pivots to the `get_all_links_by_section` helper for a brute-force, section-based scan.
        4.  **Link Aggregation**: All discovered links (from the initial fetch, the yearly scan, and/or the section scan) are consolidated into the `links_to_process` dictionary.

#### Phase 2: Unified Scraping

This phase processes the discovered links, scrapes the data, and saves it to the database.

1.  **Filter Existing Data**: It calls `db_utils.get_course_data_by_keys` with all the discovered link keys to find which reports are already in the database.
2.  **Iterate and Scrape**: It iterates through the `links_to_process`.
    -   If a key already exists in the database (`existing_course_keys`), it is skipped.
    -   For each new key, it calls `scrape_link.scrape_evaluation_data` with the report URL.
3.  **Data Handling and Storage**:
    -   If scraping is successful, the returned data is saved to the database using `db_utils.update_course_data`. The new `instance_key` is appended to the `relevant_periods` list in the local `course_metadata` object, and `new_data_found` is set to `True`.
    -   If `scrape_evaluation_data` returns a dictionary with `scrape_failed: True`, it's a soft failure for a single report. A warning is logged, and the process continues to the next link.
    -   If `scrape_evaluation_data` returns `None`, it's a hard, unexpected failure. To prevent storing incomplete data for the course, the entire batch is halted by setting `batch_failed = True` and breaking the loop.

#### Phase 3: Finalization

This phase updates the course's metadata based on the outcome of the scraping process.

1.  **Update Status**: The `last_period_failed` flag in the metadata is updated based on the `batch_failed` status.
2.  **Update `last_period_gathered`**: If the batch was successful, `last_period_gathered` is set to the `current_period`.
3.  **Grace Period Logic**: This logic determines if the course should be re-checked soon for evaluations from the current semester.
    -   It checks if any of the newly scraped data belongs to the `current_period`.
    -   If yes, the `last_scrape_during_grace_period` flag is cleared (`None`), as the most recent data has been found.
    -   If no, it checks `period_logic.is_grace_period_over()`.
        -   If the grace period is over, the flag is cleared. The course is considered up-to-date.
        -   If the grace period is still active, the `last_scrape_during_grace_period` flag is set to the current date, marking it for a potential re-scrape in the near future.
4.  **Final DB Update**: The fully updated `course_metadata` object is saved to the database with `db_utils.update_course_metadata`.
5.  **Data Retrieval for Return**: Finally, it fetches the complete and current data for all `relevant_periods` from the database using `db_utils.get_course_data_by_keys` and includes it in the return dictionary.