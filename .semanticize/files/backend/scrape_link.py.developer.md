# `backend/scrape_link.py` Developer Documentation

## Overview

This module is responsible for the final, detailed scraping of a single course evaluation report. It takes a specific URL to a report page and extracts all available evaluation data, including course/instructor names and the statistical frequency data for various evaluation questions.

Its primary design consideration is robustness. It uses an authenticated session provided by its caller and implements a retry mechanism with exponential backoff to handle transient network issues or incompletely loaded pages from the source server.

## Functions

### `scrape_evaluation_data(report_url: str, session: requests.Session) -> dict`

#### Summary

This function scrapes the evaluation data from a single, specific course evaluation report URL. It is the workhorse for extracting the raw numbers and text from a page that has already been discovered by another service.

The function is designed to be resilient. If it successfully fetches the page but finds that the key evaluation data (`overall_quality_frequency`) is missing, it will retry several times, assuming the page may not have fully loaded. It also handles network exceptions with the same retry logic.

#### Interaction Patterns

- **Caller**: This function is not called directly by the API layer. It is intended to be used by other backend services (like `scraper_service.py`) that manage the process of finding which URLs to scrape.
- **Dependencies**:
    - It requires an authenticated `requests.Session` object to be passed in, as the evaluation pages are not public.
    - It imports `MAX_RETRIES` and `INITIAL_RETRY_DELAY` from `backend.config` to control its retry behavior.
- **Output**:
    - On success, it returns a dictionary containing the structured evaluation data (e.g., `course_name`, `instructor_name`, `overall_quality_frequency`).
    - On failure after all retries, it returns a dictionary with a `scrape_failed: True` flag and a `reason` for the failure, which allows the calling service to handle the error gracefully (e.g., by updating the course metadata).