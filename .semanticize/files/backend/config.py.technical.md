# Technical Documentation for `config.py`

## 1. Overview

This configuration file, `config.py`, centralizes all static constants required for the course evaluation scraper application. It defines file paths for a legacy data storage model, critical URLs for the scraping process, and parameters that govern the timing and reliability of scraping operations. Centralizing these values makes the application easier to manage and modify without altering core logic.

## 2. Code Description

### 2.1. File Path Constants

These constants define the filenames for a legacy local file-based storage system. While the application has migrated to Supabase, these might be used by utility scripts or older, unmigrated parts of the system.

- **`METADATA_FILE = 'metadata.json'`**: Specifies the name of the JSON file used to store metadata about each course, such as the last time it was scraped.
- **`DATA_FILE = 'data.json'`**: Specifies the name of the JSON file used to store the raw scraped evaluation data for all courses.

### 2.2. Scraping URL Constants

These URLs are fundamental to the web scraping process, providing the entry points and base paths for accessing the JHU course evaluation system.

- **`AUTH_URL`**: A hardcoded URL used to authenticate with the EvaluationKit system. The long query string likely contains a pre-generated, non-expiring token or identifier that grants public access to the reporting system.
- **`BASE_REPORT_URL`**: The base URL for the EvaluationKit portal. This is used as a prefix to construct other, more specific report URLs.
- **`INDIVIDUAL_REPORT_BASE_URL`**: The base URL for accessing individual student evaluation reports. This URL is combined with specific report identifiers to navigate to the page for a particular course instance.

### 2.3. Incremental Scraping Logic Constants

These constants define the rules and timing for the incremental scraping logic, which is designed to efficiently check for new course evaluations only when they are expected to be available.

- **`PERIOD_RELEASE_DATES`**: A dictionary that maps an academic period's prefix to its official evaluation release date.
    - **Data Structure**: Dictionary (hash map).
    - **Keys**: Two-letter string prefixes representing the academic period (`'IN'` for Intersession, `'SP'` for Spring, `'SU'` for Summer, `'FA'` for Fall).
    - **Values**: A tuple `(Month, Day)` representing the date when evaluation results for that period are typically published.
    - **Algorithm**: This dictionary is used by the `period_logic.py` module to determine the earliest date a scraper should attempt to find new evaluations for a given academic term. For example, evaluations for a "FA23" (Fall 2023) course will not be scraped for before December 20th, 2023.

- **`PERIOD_GRACE_MONTHS`**: A dictionary that defines a "grace period" in months following the official release date. During this window, the system will continue to check for newly posted evaluations that may have been delayed.
    - **Data Structure**: Dictionary (hash map).
    - **Keys**: The same two-letter academic period prefixes as `PERIOD_RELEASE_DATES`.
    - **Values**: An integer representing the number of months in the grace period.
    - **Implementation Detail**: The comment `this is unnecesarily robust because they used to have different values` indicates that while all periods are currently set to a 1-month grace period, the data structure was designed to support different durations for each period, suggesting a more variable release schedule in the past.
    - **Algorithm**: This value is used to calculate an end date for the scraping window. For a Spring course released on May 15th, a 1-month grace period means the system will continue to check for new data until June 15th of that year.

### 2.4. Scraping Reliability Constants

These constants configure the reliability and network behavior of the scraper, including retry logic and delays, to handle transient network failures or slow-loading pages.

- **`SCRAPING_DELAY_SECONDS = 0`**: An integer specifying a delay in seconds between consecutive scraping requests. It is currently set to `0`, meaning no delay is enforced between scrapes. This could be increased to avoid rate-limiting or to reduce load on the target server.
- **`MAX_RETRIES = 8`**: The maximum number of times the scraper will attempt to re-fetch a URL if the initial attempt fails. This is a crucial component of the error-handling mechanism.
- **`INITIAL_RETRY_DELAY = 0.5`**: The initial delay in seconds before the first retry attempt. This delay is typically used in an exponential backoff algorithm, where the delay increases after each subsequent failure (e.g., `INITIAL_RETRY_DELAY * (2 ** attempt_number)`). This prevents overwhelming a struggling server with rapid-fire retries.