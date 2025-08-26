# Project Brief: JHU Course Evaluation Scraper

## 1. Project Overview

This project is a web scraper designed to automatically collect, parse, and store course evaluation data from the Johns Hopkins University (JHU) public reporting system. It provides a reliable and efficient way to maintain an up-to-date local database of course evaluations, which can be used for analysis and review. The scraper is built to be resilient, handling network issues and session expirations gracefully, and smart enough to avoid re-scraping data it already has.

## 2. Core Features

*   **Efficient "Up-to-Date" Checking:** The scraper intelligently checks existing metadata to determine the last successfully scraped academic period. This allows it to only fetch new data, avoiding redundant scraping and minimizing network load.
*   **Robust Pagination Handling:** The system is designed to handle the year-by-year pagination of the evaluation website. It systematically scrapes data for each academic year, ensuring complete data collection across all available time periods.
*   **Resilient Session Management:** The scraper uses a persistent `requests.Session` object. It can detect session expirations and automatically retry failed requests, ensuring a stable and reliable scraping process even during long-running jobs.
*   **Incremental Saving:** Data is saved to disk immediately after being scraped. This progressive persistence prevents data loss in case of an interruption or error, ensuring that already-collected data is safe.

## 3. Data Storage

The scraper uses two JSON files to store data and metadata.

### `data.json`

This file is the primary database for all scraped course evaluation data. It is a JSON object where each key is a unique identifier for a specific course instance (e.g., `"AS.200.312.01.FA21"`). The value for each key is an object containing detailed evaluation metrics for that course.

**Example Entry in `data.json`:**
```json
{
    "AS.200.312.01.FA21": {
        "course_name": "Substance Use and Mental Health",
        "instructor_name": "Chelsea Howe",
        "overall_quality_frequency": {
            "Poor": 0, "Weak": 0, "Satisfactory": 3, "Good": 6, "Excellent": 20
        },
        "instructor_effectiveness_frequency": {
            "Poor": 0, "Weak": 0, "Satisfactory": 0, "Good": 6, "Excellent": 22
        },
        "intellectual_challenge_frequency": {
            "Poor": 0, "Weak": 0, "Satisfactory": 1, "Good": 6, "Excellent": 21
        },
        "ta_names": ["NA", "N/A"],
        "workload_frequency": {
            "Much lighter": 2, "Somewhat lighter": 5, "Typical": 17, "Somewhat heavier": 3, "Much heavier": 0
        }
    }
}
```

### `metadata.json`

This file tracks the state of the scraping process for each high-level course code (e.g., `"AS.123.456"`). It stores metadata that enables efficient and incremental updates.

*   `last_period_gathered`: The most recent academic period (e.g., "FA23") for which data has been successfully scraped. This is the key to the "up-to-date" check.
*   `last_period_failed`: A boolean flag indicating if the last attempt to scrape a new period failed. This helps in retrying failed attempts.
*   `relevant_periods`: A list of all specific course instance keys (from `data.json`) that correspond to this course code.

## 4. Workflow and Data Flow

1.  **Initiation:** The process starts in [`main.py`](main.py:1), which takes a course code as input from the command line.
2.  **Workflow Orchestration:** [`main.py`](main.py:1) invokes the main control function in [`workflow.py`](workflow.py:1).
3.  **Period Calculation:** [`workflow.py`](workflow.py:1) uses logic from [`period_logic.py`](period_logic.py:1) to determine the range of academic years that need to be scraped. It does this by comparing the `last_period_gathered` from [`metadata.json`](metadata.json:1) with the current date.
4.  **Search and Link Discovery:** For each year that needs scraping, the workflow calls [`scrape_search.py`](scrape_search.py:1). This module queries the JHU evaluation search page for the given course and year, then parses the resulting HTML to find links to individual evaluation reports.
5.  **Individual Report Scraping:** For each report link found, the workflow calls [`scrape_link.py`](scrape_link.py:1). This module navigates to the report URL, parses the detailed evaluation data (like response frequencies), and structures it into a Python dictionary.
6.  **Data Persistence:** As the data for each course instance is scraped, it is immediately saved to [`data.json`](data.json:1) via the [`data_manager.py`](data_manager.py:1) module. The corresponding entry in [`metadata.json`](metadata.json:1) is also updated to reflect the new `last_period_gathered`.
7.  **Completion:** Once all specified years have been processed, the workflow completes. The `data.json` and `metadata.json` files are now fully up-to-date for the requested course.

## 5. Code Architecture (File Breakdown)

*   **`main.py`**: The entry point of the application. It handles command-line arguments and initiates the scraping workflow.
*   **`workflow.py`**: The central orchestrator. It manages the high-level logic of the scraping process, coordinating calls to other modules.
*   **`scrape_search.py`**: Responsible for interacting with the course evaluation search page. It finds and returns all relevant report links for a given course and year.
*   **`scrape_link.py`**: Responsible for scraping a single evaluation report page. It extracts all relevant data points and returns them in a structured format.
*   **`period_logic.py`**: Contains the business logic for handling academic periods and years. It determines which years need to be scraped.
*   **`data_manager.py`**: A utility module for reading from and writing to the `data.json` and `metadata.json` files, abstracting the file I/O operations.
*   **`config.py`**: Stores global configuration variables and constants, such as base URLs, request headers, and timeouts.
*   **`exceptions.py`**: Defines custom exception classes (e.g., `SessionExpiredError`) used throughout the project for more specific and robust error handling.
