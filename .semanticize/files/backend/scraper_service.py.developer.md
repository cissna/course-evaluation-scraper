# Scraper Service (`scraper_service.py`)

## 1. Overview

This module serves as the primary service layer for the backend, orchestrating all operations related to fetching, caching, and scraping course evaluation data. It acts as the main entry point for the Flask API endpoints, abstracting the underlying complexity of database interactions, session management, and the scraping workflow.

The service is responsible for deciding whether to return cached data from the database or to initiate a new scrape based on data freshness, grace periods, and specific user requests.

## 2. Components

### Class: `SessionExpiredException`

- **Purpose**: A custom exception used to signal that the authenticated `requests` session for scraping has likely expired. This allows for specific error handling when interacting with the JHU SIS website.

### Function: `get_course_data_and_update_cache(course_code)`

- **Purpose**: The main function for retrieving all evaluation data for a given course. It implements the core "get-or-scrape" logic.
- **Interaction Pattern**:
    1.  Fetches course metadata from the database via `db_utils.get_course_metadata`.
    2.  Checks a `last_period_failed` flag in the metadata. If true, it immediately returns an error to prevent repeated failed attempts.
    3.  Uses `period_logic.is_course_up_to_date` to check if the existing data is fresh.
    4.  If the data is up-to-date, it retrieves all relevant course instances from the database using `db_utils.get_course_data_by_keys` and returns the cached data.
    5.  If the data is stale or non-existent, it calls the core scraping engine, `workflow_helpers.scrape_course_data_core`, to perform a live scrape.
    6.  It handles authentication and request errors during the scrape, updating the course metadata to mark the attempt as failed if necessary.
    7.  Returns the fresh data upon a successful scrape.

### Function: `force_recheck_course(course_code)`

- **Purpose**: Triggers a mandatory re-scrape of a course, bypassing the standard caching and grace period logic. This is intended for user-initiated actions to get the absolute latest data.
- **Interaction Pattern**:
    - It directly invokes `workflow_helpers.scrape_course_data_core` with the `skip_grace_period_logic` flag set to `True`. This tells the core scraper to ignore any grace period checks and proceed with the scrape.

### Function: `get_course_grace_status(course_code)`

- **Purpose**: Checks if a course is currently in a "grace period"—the time right after a semester ends when new evaluations are expected but may not be published yet.
- **Interaction Pattern**:
    - It reads the course's metadata from the database.
    - It checks the `last_scrape_during_grace_period` timestamp to determine if a recent scrape occurred during this window.
    - It returns a simple status object for the frontend, which allows the UI to display a warning that the data may not yet include the most recent semester.

### Function: `find_courses_by_name(search_query)`

- **Purpose**: Provides a basic search functionality to find course codes that match a given name query.
- **Interaction Pattern**:
    - This function is a simple wrapper that passes the search query directly to `db_utils.find_courses_by_name_db`, which executes the search against the database.

### Function: `find_courses_by_name_with_details(search_query, limit, offset)`

- **Purpose**: Implements a more advanced, paginated search for courses by name, returning detailed results.
- **Interaction Pattern**:
    - It makes two calls to the `db_utils` layer:
        1. `count_courses_by_name_db` to get the total number of results for the query (for pagination).
        2. `find_courses_by_name_with_details_db` to retrieve the actual course data for the current page (using `limit` and `offset`).
    - It then aggregates this information into a structured response containing the results and total count.