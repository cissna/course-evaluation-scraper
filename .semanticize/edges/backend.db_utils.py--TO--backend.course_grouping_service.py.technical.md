The `backend/db_utils.py` file directly imports and instantiates the `CourseGroupingService` class from `backend/course_grouping_service.py` within two of its database query functions: `find_courses_by_name_with_details_db` and `count_courses_by_name_db`.

**Specific Interactions:**

1.  **Import:**
    *   `backend/db_utils.py` contains the line: `from .course_grouping_service import CourseGroupingService` inside the scope of the functions that use it.

2.  **Instantiation and Usage in `find_courses_by_name_with_details_db`:**
    *   An instance of the service is created: `grouping_service = CourseGroupingService()`. This implies that `course_grouping_service.py` must be runnable and its `__init__` method must execute successfully (loading default or file-based configuration).
    *   The service method `get_grouped_courses(course_code)` is called repeatedly to determine course groupings: `group_courses = grouping_service.get_grouped_courses(course_code)`.
    *   The returned list of grouped course codes is used to update a set of processed codes: `processed_groups.update(group_courses)`.
    *   The service is used again inside a loop to fetch details for other courses in the group: `group_courses = grouping_service.get_grouped_courses(course_code)`.

3.  **Instantiation and Usage in `count_courses_by_name_db`:**
    *   Similar to the previous function, an instance is created: `grouping_service = CourseGroupingService()`.
    *   The grouping method is called to identify unique groups for counting: `group_courses = grouping_service.get_grouped_courses(course_code)`.

**Data Flow:**

*   `db_utils.py` reads raw `course_code`s from the PostgreSQL database.
*   These raw codes are passed as string arguments to `course_grouping_service.CourseGroupingService.get_grouped_courses()`.
*   `course_grouping_service.py` processes these codes internally (using regex, configuration lookups, and explicit grouping lists) and returns a `List[str]` containing all codes belonging to the same logical group.
*   `db_utils.py` uses this returned list primarily for deduplication and aggregation logic before returning final results to its caller.

**Technical Dependency:**
This relationship establishes a dependency where `db_utils.py` relies on the availability, structure, and methods of the `CourseGroupingService` class defined in `course_grouping_service.py` to correctly process and aggregate search results derived from SQL queries.