# Technical Documentation for `backend/analysis.py`

## 1. Overview

This module serves as the core data analysis engine for the course evaluation application. It is responsible for taking raw, aggregated course evaluation data, applying user-defined filters and groupings, and calculating a variety of statistical metrics. The main entry point is `process_analysis_request`, which orchestrates the entire analysis workflow from filtering to final statistical aggregation.

The module depends on `course_grouping_service.py` to identify cross-listed or related courses and `scraper_service.py` to fetch data for those courses.

## 2. Data Structures

### `STAT_MAPPINGS`
A constant dictionary that provides the configuration for statistical calculations.

- **Structure**: `dict[str, tuple[str, dict[str, int]]]`
- **Key**: The internal key for a frequency distribution (e.g., `"overall_quality_frequency"`).
- **Value**: A tuple containing:
    1.  `str`: The user-facing name for the statistic (e.g., `"Overall Quality"`).
    2.  `dict`: A mapping from the textual response (e.g., `"Excellent"`) to its corresponding numerical value (e.g., `5`) used in calculations.

This structure centralizes the mapping between raw data keys, UI labels, and the numerical values required for statistical analysis.

## 3. Helper Functions

### `_simplify_name(name: str) -> str`
- **Purpose**: Normalizes a name string for comparison purposes.
- **Parameters**:
    - `name` (str): The input name.
- **Returns**: A simplified, lowercase string containing only alphabetic characters.
- **Implementation**:
    - It first checks if the input `name` is a string; if not, it returns an empty string.
    - It uses `filter(str.isalpha, name)` to iterate through the input string and keep only the characters that are letters.
    - `"".join(...)` concatenates these letters back into a string.
    - `.lower()` converts the result to lowercase.
    - This is primarily used to group instructors who may have slight variations in their names (e.g., "John Smith" vs. "Smith, John A.").

### `parse_semester_year(instance_key: str) -> tuple[int, int]`
- **Purpose**: Extracts a sortable representation of the academic period from a course instance key.
- **Parameters**:
    - `instance_key` (str): The unique key for a course instance (e.g., `"AS.180.101_FA23"`).
- **Returns**: A tuple `(year, semester_num)` for chronological sorting. Returns `(0, 0)` if parsing fails.
- **Implementation**:
    - A regular expression `r'\.((?:IN|SP|SU|FA))(\d{2})$'` is used to find the semester code (IN, SP, SU, FA) and the two-digit year at the end of the key.
    - The two-digit year (e.g., `23`) is converted to a four-digit year (e.g., `2023`).
    - A dictionary `semester_order` maps the semester codes to integers (`IN`: 0, `SP`: 1, `SU`: 2, `FA`: 3) to ensure correct chronological sorting (Intersession < Spring < Summer < Fall).
    - The function returns a tuple of the numeric year and semester, which allows Python's default tuple sorting to work correctly.

## 4. Core Calculation Functions

### `calculate_weighted_average(frequency_dict: dict, value_mapping: dict) -> float`
- **Purpose**: Calculates the weighted average for a single statistic from its frequency distribution.
- **Parameters**:
    - `frequency_dict` (dict): A dictionary of response counts (e.g., `{"Good": 10, "Excellent": 20}`).
    - `value_mapping` (dict): A dictionary mapping response text to numerical values (e.g., `{"Good": 4, "Excellent": 5}`).
- **Returns**: The calculated weighted average, rounded to two decimal places, or `0.0` if there are no responses.
- **Algorithm**:
    1. Initializes `total_responses` and `weighted_sum` to zero.
    2. Iterates through the `frequency_dict`. For each response (e.g., "Good"), it looks up its numerical value in `value_mapping`.
    3. It calculates the `weighted_sum` by summing `count * numerical_value` for all responses.
    4. It calculates `total_responses` by summing all `count` values.
    5. The final average is `weighted_sum / total_responses`.

### `calculate_detailed_statistics(frequency_dict: dict, value_mapping: dict) -> dict`
- **Purpose**: Calculates a comprehensive set of statistics: mean, standard deviation, and total count (n).
- **Parameters**:
    - `frequency_dict` (dict): A dictionary of response counts.
    - `value_mapping` (dict): A dictionary mapping response text to numerical values.
- **Returns**: A dictionary `{"mean": float, "std": float, "n": int}`. Values are `None` if no data is available.
- **Algorithm**:
    1. **Data Expansion**: It first creates a flat list `data_points` containing all individual numerical responses. For example, `{"Good": 2, "Excellent": 1}` becomes `[4, 4, 5]`.
    2. **Mean**: Calculates the simple arithmetic mean: `sum(data_points) / total_responses`.
    3. **Standard Deviation**: Calculates the *sample* standard deviation.
        - It computes the variance using the formula `sum((x - mean) ** 2) / (n - 1)`.
        - The standard deviation is the square root of the variance.
        - An edge case handles `n=1`, where the standard deviation is `0.0`.
    4. **Count (n)**: The total number of responses.
    5. The results are rounded and returned in a dictionary.

### `calculate_group_statistics(...)`
- **Purpose**: Aggregates statistics for a list of course instances.
- **Parameters**:
    - `course_instances` (list): A list of course data dictionaries for a specific group.
    - `stats_to_calculate` (list): A list of frequency keys to be calculated (e.g., `["overall_quality_frequency"]`).
    - `metadata` (dict, optional): Not actively used but available for future extensions.
    - `instance_keys` (list, optional): List of instance keys used to compute `periods_course_has_been_run`.
- **Returns**: A dictionary containing aggregated `values` (means) and `details` (n, std).
- **Implementation**:
    1. **Aggregate Frequencies**: It first iterates through all `course_instances` in the group and combines their frequency data into a single `aggregated_frequencies` dictionary for each statistic.
    2. **Calculate Stats**: It then iterates through the `stats_to_calculate`.
        - For standard statistics, it calls `calculate_detailed_statistics` on the aggregated frequencies.
        - For the special case `"periods_course_has_been_run"`, it calls `compute_periods_from_instance_keys` to derive the value directly from the instance keys.
    3. **Structure Output**: It formats the results into a dictionary with two keys: `"values"` (containing the mean for each statistic) and `"details"` (containing a sub-dictionary with `n` and `std` for each statistic).

## 5. Filtering and Separation Logic

### `get_instance_year(instance_key: str) -> int`
- **Purpose**: Extracts the four-digit year from a course instance key.
- **Implementation**: Uses a regex `r'\.(?:FA|SP|SU|IN)(\d{2})$'` to find the two-digit year and adds `2000` to it.

### `get_instance_season(instance_key: str) -> str`
- **Purpose**: Extracts the human-readable season name from a course instance key.
- **Implementation**: Uses a regex `r'\.((?:FA|SP|SU|IN))\d{2}$'` to find the season code and maps it to a full name (e.g., "FA" -> "Fall").

### `compute_periods_from_instance_keys(instance_keys: list) -> str`
- **Purpose**: Derives a summary of academic periods a course was run based on its instance keys.
- **Implementation**:
    - Iterates through the provided `instance_keys`.
    - For each key, a regex `r'\.([A-Z]{2}\d{2})$'` extracts the period string (e.g., "FA24").
    - It collects all unique period strings into a `set`.
    - The set is sorted chronologically (default string sort works here) and joined into a comma-separated string.

### `filter_instances(all_instances: dict, filters: dict) -> dict`
- **Purpose**: Filters a dictionary of course instances based on user-provided criteria.
- **Parameters**:
    - `all_instances` (dict): The dictionary of all course instances to be filtered.
    - `filters` (dict): A dictionary of filter criteria: `min_year`, `max_year`, `seasons` (list), `instructors` (list).
- **Returns**: A new dictionary containing only the instances that match all filter criteria.
- **Implementation**: It iterates through each instance, checking it against each active filter. An instance is excluded if it fails any of the year, season, or instructor checks.

### `separate_instances(instances: dict, separation_keys: list) -> dict`
- **Purpose**: Groups filtered instances based on one or more keys (e.g., by instructor, by year).
- **Parameters**:
    - `instances` (dict): The filtered data instances to group.
    - `separation_keys` (list): A list of keys to group by (e.g., `['instructor', 'year']`).
- **Returns**: A dictionary where keys are the composite group names (e.g., `"Alice, 2022"`) and values are lists of course instances belonging to that group.
- **Implementation**:
    1. **Instructor Name Canonicalization**: If separating by `'instructor'`, it first builds a `simplified_to_display_name` map. It iterates through all instances, simplifies each instructor's name, and finds the most recent chronological occurrence of that name to use as the canonical display name for that group. This ensures "Smith, J" and "John Smith" are grouped together under the most recent name.
    2. **Grouping**: It iterates through each instance and builds a `group_name` string.
    3. For each `sep_key` in `separation_keys`, it extracts the corresponding value from the instance (e.g., instructor name, year, season). There is specific logic for each supported key:
        - `instructor`: Uses the canonical name from the map created in step 1.
        - `year`/`season`: Calls `get_instance_year`/`get_instance_season`.
        - `course_code`/`exact_period`: Extracts the value from the instance key using regex.
        - Other keys are retrieved directly from the instance data.
    4. The extracted values are joined with ", " to form the `group_name`.
    5. The instance is appended to the list associated with that `group_name` in the `groups` dictionary.

## 6. Main Orchestration Function

### `process_analysis_request(...)`
- **Purpose**: The main entry point that orchestrates the entire analysis workflow.
- **Parameters**:
    - `all_course_data` (dict): The raw data for the primary course being analyzed.
    - `params` (dict): API request parameters containing `filters`, `separation_keys`, and `stats_to_calculate`.
    - `primary_course_code` (str, optional): The course code used to look up grouping information.
    - `skip_grouping` (bool): If `True`, analysis is confined to `all_course_data` only.
- **Returns**: A dictionary with three top-level keys: `data`, `metadata`, and `statistics_metadata`, or `None` if no data is available.
- **Workflow**:
    1.  **Parameter Parsing**: Extracts `filters`, `separation_keys`, and `stats_to_calculate` from the `params` dict. It includes backward-compatibility for older parameter names.
    2.  **Metadata and Grouping**:
        - Loads `metadata.json` if it exists.
        - If a `primary_course_code` is provided, it calls `grouping_service.get_group_info` to find related courses.
    3.  **Data Aggregation**:
        - Initializes a master dictionary `all_instances` with the `all_course_data`.
        - If grouping is enabled and related courses were found, it iterates through them, fetches their data using `get_course_data_and_update_cache`, and adds it to `all_instances`. To prevent key collisions, instance keys from grouped courses are prefixed with their own course code.
    4.  **Filtering**: Calls `filter_instances` to apply the user's filters to the aggregated `all_instances` dataset.
    5.  **Course Name Extraction**: Calls `extract_course_metadata` to determine the `current_name` and `former_names` by chronologically sorting all available instances. This result is merged with metadata from `metadata.json`.
    6.  **Separation**: Calls `separate_instances` to group the filtered data based on the `separation_keys`.
    7.  **Statistical Calculation**:
        - It iterates through each `group` returned by the separation step.
        - For each group, it calls `calculate_group_statistics` to compute the mean, standard deviation, and count for all requested statistics.
        - It maps the internal backend statistic keys (e.g., `overall_quality_frequency`) back to the frontend-facing keys (e.g., `overall_quality`).
    8.  **Response Formatting**: It assembles the final dictionary containing:
        - `data`: The calculated mean values for each statistic, organized by group.
        - `metadata`: The combined course and grouping metadata.
        - `statistics_metadata`: The detailed `n` and `std` values for each statistic, organized by group.

## 7. Example Usage (`if __name__ == '__main__'`)

The script includes a main execution block that demonstrates how to use `process_analysis_request` with dummy data. It provides two test cases:
1.  Separating data by instructor with no filters.
2.  Filtering data by year with no separation.

This serves as a basic integration test and an example of how to structure the `params` dictionary.