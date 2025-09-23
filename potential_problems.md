# Potential Problems in Course Evaluation Scraper

This document has been updated to reflect the current state of the codebase.

## 1. Code Duplication and Consistency

- **Duplicate Functions**:
  - **Status**: LARGELY FIXED.
  - **Details**: Most of the duplicate functions previously found in `backend/scraper_service.py` have been resolved. The backend now correctly calls the centralized `scrape_course_data_core` function in `workflow_helpers.py`, which in turn imports functions from `period_logic.py`, `data_manager.py`, and `scraping_logic.py`. This is a significant improvement.

## 2. Architectural and Performance Issues

- **Inefficient Data Handling**:
  - **Status**: UNCHANGED.
  - **Details**: The `data.json` file is very large (over 1.1 million lines). The backend loads this entire file into memory for every request that requires a data lookup (`load_json_file(DATA_FILE)`). This is highly inefficient and will lead to high memory consumption and slow response times, especially under concurrent load.
  - **Recommendation**: This is the most critical issue. The application should be migrated from using a single JSON file to a proper database (like SQLite, PostgreSQL, or MongoDB) for storing and querying course evaluation data.

## 3. Data Integrity and Quality

- **Corrupted Data in `data.json`**:
  - **Status**: UNCHANGED.
  - **Details**: The `data.json` file contains entries like `"def didnt have one"`, which indicates that some data may have been scraped or processed incorrectly.
  - **Recommendation**: A data cleanup script should be created to parse `data.json`, identify and fix or remove malformed entries.

- **Inconsistent Function Usage**:
  - **Status**: FIXED.
  - **Details**: The web application now correctly uses the more robust `scrape_evaluation_data` function (with retry logic) from `scrape_link.py` via the `workflow_helpers.py` module.

## 4. Unused/Unreferenced Code

- **Unreferenced Files**:
  - **Status**: FIXED.
  - **Details**: `period_logic.py` is now correctly referenced and used. The issues with duplicate constants in `backend/scraper_service.py` and brittle `sys.path` manipulation have been resolved.
  - **Recommendation**: Continue to ensure all modules import from the central `config.py` where applicable.

- **Unused Directory**:
  - **Status**: FIXED.
  - **Details**: The `random_unused` directory was removed.

## 5. Lack of Testing

- **No Automated Tests**:
  - **Status**: NEW PROBLEM.
  - **Details**: There are no unit tests or integration tests in the project. This makes it difficult to refactor code or add new features without risking regressions. The complexity of the scraping and data processing logic makes testing especially important.
  - **Recommendation**: Introduce a testing framework like `pytest`. Start by writing tests for the critical business logic in `period_logic.py`, `workflow_helpers.py`, and the backend services.
