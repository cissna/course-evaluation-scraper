The `workflow_helpers.py` file is responsible for orchestrating the data collection process for a specific course. To manage the timing, freshness, and completeness of this data, it relies heavily on the utility functions provided by `period_logic.py`.

**Business Connection:**

`period_logic.py` acts as the system's definitive source for **time-based rules and context** regarding evaluation periods.

`workflow_helpers.py` uses these rules to make critical execution decisions:

1.  **Determining Data Freshness:** It uses `get_current_period()` to understand what the current active academic period is, influencing how long it waits to re-scrape.
2.  **Handling Data Gaps/Age:** It uses functions like `is_grace_period_over()` to decide if it should flag a course as having incomplete data when the newest evaluation reports aren't yet available (i.e., during a grace period).
3.  **Historical Context:** It relies on `get_year_from_period_string()` and `find_oldest_year_from_keys()` (which are also defined in `period_logic.py` but are imported and used in `workflow_helpers.py`) to correctly scope its searches across past academic years when handling complex pagination issues.

In essence, `period_logic.py` defines *when* data is considered current, and `workflow_helpers.py` uses that definition to determine *what* data to collect and *when* to stop or flag an issue.