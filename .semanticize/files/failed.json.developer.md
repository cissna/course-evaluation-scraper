## Interaction Patterns

- **Generation**: The `scraper_service.py` in the backend is responsible for populating this file. When a scrape attempt for a course instance fails, the service catches the exception, constructs a failure record, and appends it to this JSON file.

- **Consumption**:
    - **Debugging**: Developers can inspect this file to diagnose issues with the scraping process, identify patterns in failures (e.g., a specific semester is failing, or the target site structure has changed), and understand why certain courses may be missing from the database.
    - **Manual Intervention**: The list of failed courses can be used as input for manual re-scraping attempts or for one-time scripts designed to address specific types of failures.