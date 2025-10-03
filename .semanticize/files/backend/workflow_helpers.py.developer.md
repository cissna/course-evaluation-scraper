# `workflow_helpers.py` Developer Documentation

This module acts as the central orchestrator for the course data scraping workflow. It integrates functionalities from various other modules—such as database interactions (`db_utils`), session management and scraping logic (`scraping_logic`, `scrape_link`, `scrape_search`), and academic period calculations (`period_logic`)—to perform the complex task of gathering, processing, and storing course evaluation data.

The primary function, `scrape_course_data_core`, encapsulates the entire end-to-end process for a single course, from discovering evaluation links to storing the scraped data in the database and updating the course's metadata.

---

## Functions

### `get_all_links_by_section(session, course_code)`

-   **What it does:** Serves as a robust, fallback link-gathering mechanism when the primary strategies in `scrape_course_data_core` are insufficient. It systematically iterates through all possible section numbers (e.g., `.01`, `.02`, ... `.99`) for a given `course_code` to find every available evaluation report link.
-   **Interaction Patterns:**
    -   This function is called exclusively by `scrape_course_data_core` as a last resort, specifically when a "Show more results" button is unexpectedly found during a year-by-year scan—a critical edge case indicating a very high number of evaluations.
    -   It calls `scrape_search.get_evaluation_report_links` for each potential section.
    -   If it encounters a section that *also* has a "Show more results" button, it further breaks down the search for that section by academic year to ensure completeness, using helpers from `period_logic`.

### `scrape_course_data_core(course_code, session=None, skip_grace_period_logic=True)`

-   **What it does:** Orchestrates the complete, end-to-end process of scraping all evaluation data for a given `course_code`. It handles fetching or creating metadata, collecting report links using an optimized strategy, scraping new data, and updating the database.
-   **High-Level Workflow:**
    1.  **Setup Phase:**
        -   Retrieves the course's metadata from the database using `db_utils.get_course_metadata`. If no record exists, it creates a new one.
        -   Ensures an authenticated `requests.Session` is available, calling `scraping_logic.get_authenticated_session` if needed.
    2.  **Link Collection Phase:**
        -   First, it attempts to get all links from the main evaluation search page for the course (`scrape_search.get_evaluation_report_links`).
        -   It then employs a smart strategy based on whether a "Show more results" button is present (indicating pagination):
            -   **No Pagination:** The simplest case; it proceeds to scrape the links found.
            -   **Pagination Detected:** It uses an optimized strategy. It takes the initial set of links and then performs a targeted, year-by-year search starting from the most recently known year. This avoids re-checking years for which data is likely already stored.
            -   If the pagination is too complex (e.g., more than 20 results within a single year), it escalates to the `get_all_links_by_section` function.
    3.  **Unified Scraping Phase:**
        -   Compares the collected links against existing data in the database (`db_utils.get_course_data_by_keys`) to identify only new reports.
        -   Iterates through the new links, calling `scrape_link.scrape_evaluation_data` for each one.
        -   If any individual scrape fails, it halts the entire batch for the course to prevent storing incomplete data.
    4.  **Finalization Phase:**
        -   Updates the course's metadata (`db_utils.update_course_metadata`) with the outcome of the scrape (`last_period_gathered`, `last_period_failed`).
        -   Manages the `last_scrape_during_grace_period` flag based on whether data for the current academic term was found, using helpers from `period_logic`.
        -   Returns a dictionary containing the final status, all relevant course data from the database, and the updated metadata.