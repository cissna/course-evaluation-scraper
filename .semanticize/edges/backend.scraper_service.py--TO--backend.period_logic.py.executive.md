The **Scraper Service** (`scraper_service.py`) is responsible for fetching the most current course information. To determine if it needs to fetch new data or if cached data is still valid, it relies heavily on **Period Logic** (`period_logic.py`).

The relationship is one of **Dependency and Enforcement**:

1.  **Data Freshness Check:** The Scraper Service calls functions like `is_course_up_to_date` from Period Logic to check if the existing data is still relevant based on the current academic period, saving time and resources if it is.
2.  **Period Definition:** The Scraper Service uses `get_current_period` to establish what the "current" academic term is, which dictates whether scraping is necessary.
3.  **Grace Period Management:** The Scraper Service uses Period Logic functions (like those related to grace periods, although the direct import usage is slightly abstract in the provided scrape workflow) to manage when users are allowed to override standard freshness checks.

In simple terms, **Period Logic defines the rules and timing of the academic calendar**, and the **Scraper Service uses those rules to decide when to go out and get new information.**