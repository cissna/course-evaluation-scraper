# `period_logic.py` Developer Documentation

## 1. High-Level Summary

This module serves as the central hub for all business logic related to academic periods, semesters, and timing. It is responsible for parsing period information from various data structures, determining the current academic period based on the system date, and evaluating whether a course's scraped data is up-to-date.

The logic in this file is critical for the scraper's efficiency, as it dictates when the system should attempt to fetch new data for a course. It directly interacts with configuration defined in `backend/config.py` to control its behavior.

## 2. Component Breakdown

### **Dependencies**

- **`backend.config`**: This module is highly dependent on `PERIOD_RELEASE_DATES` and `PERIOD_GRACE_MONTHS` from the config file. These external configurations define the core schedule for when new course evaluation data is expected and how long the system should wait for potentially delayed data to appear.

### **Function Summaries**

---

#### `find_oldest_year_from_keys(keys: list) -> int`

- **What it does**: Scans a list of course instance keys (e.g., `AS.180.101.FA15`) and identifies the earliest academic year present.
- **Purpose**: Used to establish the historical starting point for a course's available data. It defaults to a safe start year (2010) if no valid years are found.

---

#### `find_latest_year_from_keys(keys: list) -> int`

- **What it does**: Complements the above function by finding the most recent academic year from a list of course instance keys.
- **Purpose**: Helps determine the most recent data available for a course.

---

#### `get_period_from_instance_key(instance_key: str) -> str`

- **What it does**: A simple utility function that parses a full course instance key to extract the academic period identifier (e.g., "FA23").
- **Purpose**: Provides a standardized way to get the period string from a unique course instance identifier.

---

#### `get_year_from_period_string(period_string: str) -> int`

- **What it does**: Extracts the full four-digit year from a period string (e.g., "FA23" -> 2023).
- **Purpose**: A helper for converting the two-digit year format used in period strings into a standard integer year.

---

#### `get_current_period() -> str`

- **What it does**: Calculates the current academic period based on the system's current date and the release schedules defined in `config.py`.
- **Purpose**: This is a primary driver of the application's state. It establishes the "target" period that all courses should ideally be updated to. If today's date is before the first evaluation release of the year, it correctly identifies the final period of the previous year.

---

#### `is_course_up_to_date(last_period_gathered: str, course_metadata: dict, ...) -> bool`

- **What it does**: Encapsulates the core logic for determining if a course needs to be re-scraped.
- **Purpose**: This function acts as the main gatekeeper for scraping operations. It checks if the last gathered period for a course matches the application's current period (`get_current_period()`) and also accounts for whether the course is in a "grace period" where data might still be pending release. The `skip_grace_period_logic` flag allows forcing a re-check.

---

#### `is_grace_period_over(period: str) -> bool`

- **What it does**: Checks whether the configured grace period (defined in `PERIOD_GRACE_MONTHS` from `config.py`) for a specific academic term has passed.
- **Purpose**: This function helps the system decide when to stop attempting to re-scrape for a period that has just been released. Once the grace period is over, the system can assume that no new data will be posted for that term and can stop checking.