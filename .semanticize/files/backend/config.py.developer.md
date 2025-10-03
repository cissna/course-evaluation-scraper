# Developer Documentation for `backend/config.py`

## Overview

This configuration file serves as a centralized repository for all static constants used across the backend application. It defines critical parameters for web scraping, including target URLs, timing for incremental data collection, and reliability settings for network requests. By externalizing these values, the file allows for easy adjustments to the scraper's behavior without altering the core application logic.

## Component Breakdown

### File Paths

These constants define the names for local data files. They are primarily legacy values from the previous file-based architecture before the migration to a Supabase database.

-   `METADATA_FILE`: Specifies the filename for storing course metadata (`metadata.json`).
-   `DATA_FILE`: Specifies the filename for storing raw course evaluation data (`data.json`).

### Scraping URLs

This group of constants defines the essential endpoints for interacting with the JHU evaluation website.

-   `AUTH_URL`: The URL used to authenticate and establish a session for scraping public reports.
-   `BASE_REPORT_URL`: The base URL for the evaluation system's domain.
-   `INDIVIDUAL_REPORT_BASE_URL`: The base URL for accessing the detailed report page for a specific course.

### Incremental Scraping Logic Constants

These constants govern the intelligent, incremental scraping logic, which is designed to check for new evaluations only when they are expected to be available. This minimizes unnecessary scraping operations.

-   `PERIOD_RELEASE_DATES`: A dictionary that maps academic period prefixes (e.g., 'FA' for Fall, 'SP' for Spring) to their typical result release dates (Month, Day). This allows the `period_logic.py` service to predict when to start looking for new data for a given semester.
-   `PERIOD_GRACE_MONTHS`: Defines a "grace period" in months following the official release date. During this window, the scraper will continue to check for new evaluations to account for potential delays in their posting.

### Scraping Reliability

These constants configure the scraper's resilience to network errors or transient server issues, ensuring a more robust data collection process.

-   `SCRAPING_DELAY_SECONDS`: The delay (in seconds) between consecutive scraping requests. Currently set to zero.
-   `MAX_RETRIES`: The maximum number of times the scraper will attempt to re-fetch a URL if the initial request fails.
-   `INITIAL_RETRY_DELAY`: The initial delay (in seconds) for the first retry attempt. The delay increases exponentially with subsequent retries to avoid overwhelming the server.

## High-Level Interaction Patterns

-   The **Scraping URLs** are consumed by the `scraper_service.py` and `scraping_logic.py` modules to construct and send HTTP requests to the JHU evaluation portal.
-   The **Incremental Scraping Logic Constants** are heavily used by `period_logic.py` to determine if a course's data is stale and requires a new scrape. This logic is central to the `GET /api/course/<course_code>` endpoint's decision-making process.
-   The **Scraping Reliability** constants are used within the scraping functions to implement an exponential backoff retry mechanism, making the data collection process more fault-tolerant.