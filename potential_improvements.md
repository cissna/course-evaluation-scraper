# Potential Improvements Identified During Refactoring

This document lists potential improvements that were identified while refactoring the repository to be web-app exclusive. These changes were out of scope for the refactoring task but are recommended for future consideration.

1.  **Unify `is_course_up_to_date()` Logic**: The version of this function in `period_logic.py` is more robust than the simplified version that was previously used in `scraper_service.py`. The web app could benefit from this more nuanced logic, which handles grace periods correctly.

2.  **Adopt Robust `scrape_evaluation_data()`**: The version of this function in `scrape_link.py` includes a retry mechanism with exponential backoff, making it more resilient to network errors. The web app currently uses a simpler version; adopting the more robust version would improve reliability.

3.  **Centralize File Path Logic**: The `config.py` file uses relative paths, while the web app backend requires absolute paths. This logic should be centralized to avoid potential file-not-found errors.