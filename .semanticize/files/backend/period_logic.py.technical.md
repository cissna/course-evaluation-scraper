# Technical Documentation for `backend/period_logic.py`

## 1. Module Overview

This module provides a suite of utility functions for handling time-sensitive and period-related logic for course evaluations. It is responsible for parsing academic periods and years from various data formats, determining the current academic period based on the system date, and managing the logic for data freshness, including "grace periods" after evaluation data is released. This module is critical for deciding when to trigger new data scraping attempts.

This module depends on configuration constants defined in `backend/config.py`, specifically `PERIOD_RELEASE_DATES` and `PERIOD_GRACE_MONTHS`.

## 2. Functions

---

### `find_oldest_year_from_keys(keys: list) -> int`

**Description:**
Parses a list of course instance keys (e.g., `AS.180.101.FA15`) to find the earliest academic year present.

**Parameters:**
- `keys` (list): A list of strings, where each string is a course instance key.

**Returns:**
- `int`: The oldest four-digit year found among the keys. If no valid year can be parsed from any key, it returns a default value of `2010`.

**Implementation Details:**
- **Initialization**: It initializes `oldest_year` to the current system year and a boolean flag `found_year` to `False`.
- **Regex Matching**: It uses the regular expression `r'\.(?:FA|SP|SU|IN)(\d{2})$'` to find a period identifier at the end of each key.
  - `\.`: Matches the period character preceding the term code.
  - `(?:FA|SP|SU|IN)`: A non-capturing group that matches one of the academic term codes (Fall, Spring, Summer, Intersession).
  - `(\d{2})`: A capturing group for the two-digit year.
  - `$`: Asserts the position at the end of the string.
- **Year Conversion**: For each match, the two-digit year is extracted. It's converted to a four-digit year using the following logic to handle the century ambiguity:
  - If `year_short < 70`, it's assumed to be in the 2000s (e.g., `15` -> `2015`).
  - If `year_short >= 70`, it's assumed to be in the 1900s (e.g., `99` -> `1999`).
- **Logic**: The function iterates through all keys, updating `oldest_year` whenever a smaller year is found. If at least one year is successfully parsed, it returns the final `oldest_year`; otherwise, it returns the hardcoded default of `2010`.

---

### `find_latest_year_from_keys(keys: list) -> int`

**Description:**
Parses a list of course instance keys to find the most recent academic year present.

**Parameters:**
- `keys` (list): A list of strings, where each string is a course instance key.

**Returns:**
- `int`: The latest (most recent) four-digit year found. If no valid year can be parsed, it returns `0`.

**Implementation Details:**
- This function's logic is the inverse of `find_oldest_year_from_keys`.
- **Initialization**: It initializes `latest_year` to `0`.
- **Regex and Year Conversion**: It uses the same regex and year conversion logic as `find_oldest_year_from_keys`.
- **Logic**: It iterates through all keys, updating `latest_year` whenever a larger year is found. If no year is found, the initial value of `0` is returned.

---

### `get_period_from_instance_key(instance_key: str) -> str`

**Description:**
Extracts the academic period code (e.g., "FA17") from a full course instance key.

**Parameters:**
- `instance_key` (str): The full course instance key (e.g., "EN.601.475.01.FA17").

**Returns:**
- `str`: The extracted period string (e.g., "FA17"). Returns `None` if the key does not contain a valid period code at the end.

**Implementation Details:**
- It uses the regex `r'\.((?:FA|SP|SU|IN)\d{2})$'` to find and capture the period code.
- The key difference from the regex in the year-finding functions is the outer capturing group `(...)` around the term and year. This allows `match.group(1)` to return the entire period string (e.g., "FA17") directly.

---

### `get_year_from_period_string(period_string: str) -> int`

**Description:**
Extracts the four-digit year from a period string.

**Parameters:**
- `period_string` (str): The period string (e.g., 'FA23').

**Returns:**
- `int`: The corresponding four-digit year (e.g., `2023`). Returns `None` if the input string is invalid (null or too short).

**Implementation Details:**
- It performs a basic check to ensure the string is not null and has a length of at least 4.
- It extracts the last two characters, converts them to an integer, and adds `2000`. This logic assumes all academic years are in the 21st century.

---

### `get_current_period() -> str`

**Description:**
Determines the current academic evaluation period based on the system's current date and the release schedule defined in the configuration.

**Parameters:**
- None.

**Returns:**
- `str`: A string representing the current academic period (e.g., "FA25").

**Implementation Details:**
- **Dependencies**: Relies on `PERIOD_RELEASE_DATES` from `config.py`, which is a dictionary mapping period prefixes to their `(month, day)` release dates.
- **Logic**:
  1. It retrieves the current date using `datetime.date.today()`.
  2. It checks the date against the release dates for each period in a specific, reverse-chronological order: `FA`, `SU`, `SP`, `IN`.
  3. For a period to be considered "current," today's date must be on or after its release date.
  4. The first period that satisfies this condition is returned as the current one for the present year.
  5. If the current date is before the first release date of the year (`IN`), the function concludes that the active period is the last one from the *previous* year, which is always `FA`. In this case, it returns `FA` combined with the previous year's two-digit code.

---

### `is_course_up_to_date(last_period_gathered: str, course_metadata: dict, skip_grace_period_logic=False) -> bool`

**Description:**
Checks if the stored data for a course is considered up-to-date.

**Parameters:**
- `last_period_gathered` (str): The identifier of the last period for which data was successfully scraped (e.g., "SP24").
- `course_metadata` (dict): The metadata object for the course, which may contain the `last_scrape_during_grace_period` flag.
- `skip_grace_period_logic` (bool, optional): If `True`, the check for a pending grace period re-scrape is ignored. Defaults to `False`.

**Returns:**
- `bool`: `True` if the course data is current, `False` otherwise.

**Implementation Details:**
- A course is considered up-to-date if and only if both of the following conditions are met:
  1. Its `last_period_gathered` value is identical to the value returned by `get_current_period()`.
  2. The `last_scrape_during_grace_period` field in its metadata is `None`. This field acts as a flag indicating that the course was scraped during a grace period and may need to be re-scraped for late-arriving data.
- If `skip_grace_period_logic` is set to `True`, the second condition is ignored, and the up-to-date status depends solely on whether the last gathered period matches the current period.

---

### `is_grace_period_over(period: str) -> bool`

**Description:**
Determines if the "grace period" for a specific academic period has passed. The grace period is a configured number of months after evaluations are released, during which additional evaluation data may become available.

**Parameters:**
- `period` (str): The period string to check (e.g., "FA25").

**Returns:**
- `bool`: `True` if the current system date is after the end of the grace period, `False` otherwise.

**Implementation Details:**
- **Dependencies**: Relies on `PERIOD_RELEASE_DATES` and `PERIOD_GRACE_MONTHS` from `config.py`.
- **Logic**:
  1. It parses the `period` string to get the prefix (e.g., "FA") and the four-digit year.
  2. It constructs the official `release_date` for that period using the `PERIOD_RELEASE_DATES` configuration.
  3. It retrieves the duration of the grace period in months from the `PERIOD_GRACE_MONTHS` configuration.
  4. It calculates the `grace_period_end` date by adding the grace months to the `release_date` using `dateutil.relativedelta.relativedelta(months=...)`.
  5. It returns `True` if `date.today()` is later than this calculated end date.