The `scraper_service.py` file acts as the main orchestrator for course data retrieval, coordinating database checks, period logic, and actual scraping operations.

The relationship with `scraping_logic.py` is one of **dependency for core utility functions**.

Specifically, `scraper_service.py` imports and utilizes the following function from `scraping_logic.py`:

1.  **`get_authenticated_session`**: This function is crucial for establishing the necessary authenticated HTTP session required before any external scraping can occur. It is called at the beginning of data-gathering workflows (`get_course_data_and_update_cache`, `force_recheck_course`) and is wrapped in error handling in case the authentication fails (which raises `requests.exceptions.RequestException`).

In summary, `scraper_service.py` *consumes* authentication utilities provided by `scraping_logic.py` to enable its primary scraping duties.