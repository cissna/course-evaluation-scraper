# `backend/analysis.py` Developer Documentation

## File Summary

This module serves as the core analysis engine for the backend. Its primary responsibility is to take raw course evaluation data, process it according to user-defined parameters, and return structured statistical results. It handles data filtering, grouping (separation), and the calculation of various statistics like mean and standard deviation for different evaluation metrics.

The main entry point is `process_analysis_request`, which orchestrates the entire analysis workflow, from fetching data for grouped courses to structuring the final response for the API.

## Dependencies

- **`CourseGroupingService`**: Used to identify cross-listed or related courses that should be analyzed together as a single logical group.
- **`scraper_service`**: Used to fetch the raw evaluation data for any related courses identified by the `CourseGroupingService`.

---

## Core Components

### `process_analysis_request(all_course_data, params, ...)`

- **What it does**: This is the main orchestrator function. It takes the raw data for a primary course and a dictionary of analysis parameters from an API request. It performs a full analysis pipeline: fetching data for grouped courses, filtering, separating data into groups, calculating statistics for each group, and assembling the final data structure for the API response.
- **Interaction**: This function is the primary interface for this module. It receives the request parameters and returns a dictionary containing three top-level keys: `data` (the calculated statistics for each group), `metadata` (course names, grouping info), and `statistics_metadata` (detailed stats like count and standard deviation).

### `filter_instances(all_instances, filters)`

- **What it does**: Filters a dictionary of course instances based on criteria provided in the `filters` dictionary, such as a minimum/maximum year, specific seasons (e.g., "Fall"), or a list of instructor names.
- **Interaction**: It takes the complete set of instances to be analyzed and returns a new, smaller dictionary containing only the instances that match the filter criteria.

### `separate_instances(instances, separation_keys)`

- **What it does**: Separates a dictionary of filtered course instances into distinct groups based on one or more `separation_keys` (e.g., `instructor`, `year`, `course_code`). This is used to create the different data series that will be displayed on the frontend.
- **Interaction**: It returns a dictionary where keys are the generated group names (e.g., "Alice", "Bob") and values are lists of course instances belonging to that group. It intelligently handles instructor name variations by simplifying them for grouping.

### `calculate_group_statistics(course_instances, stats_to_calculate, ...)`

- **What it does**: Calculates aggregated statistics for a single group of course instances. It first aggregates the frequency data (e.g., counts of "Good", "Excellent") from all instances in the group and then computes the final statistical values.
- **Interaction**: It is called by `process_analysis_request` for each group created by `separate_instances`. It returns a dictionary containing the calculated mean values (`values`) and detailed information like count and standard deviation (`details`) for each requested statistic.

### `calculate_detailed_statistics(frequency_dict, value_mapping)`

- **What it does**: A core utility function that performs the actual statistical calculations (mean, standard deviation, and total response count) for a single metric from an aggregated frequency dictionary.
- **Interaction**: It takes a dictionary of response counts (e.g., `{"Good": 10, "Excellent": 20}`) and a mapping of those responses to numerical values, returning a dictionary with the results (`mean`, `std`, `n`).

### `extract_course_metadata(...)`

- **What it does**: Determines a course's "current name" and a list of its "former names" by chronologically sorting all its instances. It also merges this information with any existing metadata loaded from `metadata.json`.
- **Interaction**: It is called once per analysis request to provide descriptive metadata for the course or course group being analyzed.

---

## Helper Functions & Constants

- **`STAT_MAPPINGS`**: A constant dictionary that defines the UI display names and numerical value mappings for each statistical metric (e.g., mapping "Excellent" to `5`). This is the central configuration for how raw frequency data is converted into quantitative values for calculation.

- **`_simplify_name(name)`**: A helper to normalize instructor names by removing non-alphabetic characters and converting to lowercase. This allows instances taught by "A. Professor" and "Professor, A" to be grouped together.

- **`parse_semester_year(instance_key)`**: A helper that parses a chronological sorting key (a `(year, semester_number)` tuple) from a course instance key string (e.g., `AS.180.101_FA23`).

- **`get_instance_year(instance_key)` / `get_instance_season(instance_key)`**: Simple helpers that extract the year and season from a course instance key, respectively. Used for filtering and separation.

- **`compute_periods_from_instance_keys(instance_keys)`**: A utility to generate a sorted, comma-separated string of academic periods (e.g., "FA22, SP23") from a list of instance keys.