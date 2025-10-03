The `scraper_service.py` file imports several functions and names directly from `backend.period_logic`:

1.  **Imports:**
    ```python
    from .period_logic import (
        get_year_from_period_string,
        get_current_period,
        is_course_up_to_date,
        is_grace_period_over
    )
    ```

2.  **Function Calls and Data Flow:**

    *   **`get_current_period()`:** Called within `get_course_grace_status` to determine the current evaluation period, which is used in the returned dictionary.
        ```python
        # In scraper_service.py: get_course_grace_status
        current_period = get_current_period()
        ```

    *   **`is_course_up_to_date(last_period_gathered, metadata)`:** Called in `get_course_data_and_update_cache` to check if cached course data is sufficiently recent before attempting a scrape.
        ```python
        # In scraper_service.py: get_course_data_and_update_cache
        if metadata and is_course_up_to_date(metadata.get('last_period_gathered'), metadata):
        ```
        *Note: The signature of `is_course_up_to_date` in `period_logic.py` accepts an optional third argument (`skip_grace_period_logic`), but in `scraper_service.py`, it is called with only two arguments.*

    *   **`get_year_from_period_string(period_string)`:** This function is imported but **not explicitly called** in the provided source code for `scraper_service.py`.

    *   **`is_grace_period_over(period)`:** This function is imported but **not explicitly called** in the provided source code for `scraper_service.py`.

3.  **Data Relationship:**
    `period_logic.py` provides utility functions related to determining time validity, current academic periods, and grace periods, which `scraper_service.py` consumes to decide whether to execute expensive scraping operations or interpret status checks for courses based on time constraints. The interaction is one-way: `scraper_service.py` calls functions in `period_logic.py` to retrieve status information.