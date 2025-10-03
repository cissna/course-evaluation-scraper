The `backend/analysis.py` module acts as a **consumer** of data provided by `backend/scraper_service.py`.

**High-Level Interaction:**
The primary interaction point is the function call `get_course_data_and_update_cache()` from `analysis.py` within `process_analysis_request`. This function is crucial because statistical analysis relies on having the raw, up-to-date course instance data, which the scraper service is responsible for fetching, caching, and ensuring accuracy (via date checks and forced rechecks).

**Functionality Used:**
1.  **Data Retrieval:** `analysis.py` calls `get_course_data_and_update_cache(course_code)` to obtain the raw course instance data (`all_course_data`) required for filtering, grouping, and statistical calculation.
2.  **Grouping Dependency:** If grouping is active (`primary_course_code` is present and `skip_grouping` is False), `analysis.py` iterates through grouped course codes and calls `get_course_data_and_update_cache(course_code)` for each related course to aggregate the total dataset.

**General Interaction Patterns:**
*   **Request/Response:** `analysis.py` initiates a request for data associated with a specific `course_code`, and `scraper_service.py` returns a dictionary containing the instance data (or an error object).
*   **Dependency Flow:** The flow is unidirectional: Analysis depends on Scraper to provide the underlying data entities.

**Component-Level Relationship:**
*   **Consumer (`analysis.py`):** This component performs high-level aggregation, filtering, grouping (`separate_instances`), and complex statistical computation (`calculate_group_statistics`). It consumes the raw data structure provided by the scraper.
*   **Producer/Data Provider (`scraper_service.py`):** This component is responsible for external interaction (HTTP requests via `requests.Session`), database checks (`get_course_metadata`), cache validation (`is_course_up_to_date`), and coordinating the actual scraping logic (`scrape_course_data_core`).