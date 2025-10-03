# Course Grouping Service (`CourseGroupingService`)

## Class: `CourseGroupingService`

### Overview

The `CourseGroupingService` is responsible for identifying and grouping related university courses. Its primary function is to determine which courses should be considered equivalent for the purpose of data aggregation and analysis. For example, it can group a 400-level undergraduate course with its 600-level graduate counterpart.

The service operates based on a configuration that defines two types of grouping rules:
1.  **Department Patterns**: Groups courses within the same department based on their level (e.g., `EN.601.4xx` is grouped with `EN.601.6xx`).
2.  **Explicit Groupings**: Groups a specific, hardcoded list of courses, which may span different departments.

A key architectural feature is its flexible configuration loading. It attempts to load rules from an external JSON file. If the file is not found, it falls back to a `DEFAULT_CONFIG` embedded directly within the class, ensuring the service remains functional in serverless or isolated environments.

### High-Level Interaction

A client instantiates the service and then uses its public methods to query course relationships. The typical flow is:
1.  Provide a `course_code` to `get_grouped_courses`.
2.  The service consults its configuration (both explicit and pattern-based rules) to find all related courses.
3.  It returns a list of all course codes belonging to that logical group.

---

## Public Methods

### `get_grouped_courses(course_code: str) -> List[str]`

-   **What it does**: This is the primary method of the service. It takes a single course code and returns a comprehensive list of all courses that are grouped with it, including the original course.
-   **How it works**: It first checks for any `explicit_groupings` that contain the course. It then applies any relevant `department_patterns` to find level-based equivalents. The results from both rule sets are combined into a single, unique, and sorted list.
-   **Usage**: Call this method to get a complete picture of a course's logical group before fetching or aggregating data for all of them. If no group is found, it returns a list containing only the input `course_code`.

### `is_course_grouped(course_code: str) -> bool`

-   **What it does**: A simple boolean check to determine if a given course is part of any defined group (either explicit or pattern-based).
-   **Usage**: Useful for quickly checking if a course has equivalents without needing the full list of them.

### `get_group_info(course_code: str) -> Dict`

-   **What it does**: Retrieves metadata about the group a course belongs to.
-   **How it works**: It finds the group for the given `course_code` and returns a dictionary containing the list of `courses` in the group and a `description` if one is available (descriptions are typically only defined for `explicit_groupings`).
-   **Usage**: Use this to get context or a human-readable description for a course group, which can be displayed in a UI. Returns an empty dictionary if no group is found.

---

## Private Helper Methods & Configuration

-   `_load_config()`: Manages the loading of grouping rules, prioritizing an external JSON file over the embedded `DEFAULT_CONFIG`.
-   `_parse_course_code()`: A utility that uses regex to split a course code (e.g., "EN.601.485") into its department (`EN.601`) and number (`485`) components.
-   `_get_department_equivalents()`: Implements the logic for finding courses that match a department-level pattern.
-   `_find_explicit_group()`: Implements the logic for finding if a course is listed in one of the hardcoded explicit groups.