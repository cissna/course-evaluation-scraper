# `db_utils.py` Developer Documentation

This module serves as the dedicated data access layer (DAL) for the application, abstracting all direct interactions with the PostgreSQL database. It provides a clear and centralized API for performing CRUD (Create, Read, Update, Delete) operations on the `courses` and `course_metadata` tables, handling connection management, and executing complex queries required for search and data aggregation.

## High-Level Interaction Patterns

- **Connection Management**: All functions that interact with the database use the `get_db_connection()` utility to acquire a connection, ensuring consistent configuration from the `DATABASE_URL` environment variable. Connections are managed within a `with` statement to guarantee they are properly closed.
- **Data Upsert**: The `update_course_metadata` and `update_course_data` functions use `INSERT ... ON CONFLICT DO UPDATE` (an "upsert") to simplify the logic for creating or updating records, making database writes idempotent.
- **Search and Grouping**: For user-facing search functionality, this module collaborates with the `CourseGroupingService`. It first fetches a broad set of matching courses from the database and then uses the service to group, deduplicate, and refine the results before returning them. This pattern separates the raw data retrieval from the business logic of how courses are related.

---

## Functions

### `get_db_connection()`

-   **What it does**: Establishes and returns a new connection to the PostgreSQL database. It sources the connection string from the `DATABASE_URL` environment variable.
-   **Why it's important**: Centralizes database connection logic, ensuring all parts of the application connect in a uniform way.

### `get_course_metadata(course_code)`

-   **What it does**: Fetches the entire metadata record for a single course from the `course_metadata` table, identified by its unique `course_code`.
-   **Returns**: A dictionary representing the course's metadata or `None` if no record is found.

### `update_course_metadata(course_code, metadata)`

-   **What it does**: Inserts a new course metadata record or updates an existing one if it already exists (based on `course_code`).
-   **Why it's important**: Provides a single, atomic operation for saving metadata, preventing race conditions and simplifying application logic.

### `get_course_data_by_keys(keys)`

-   **What it does**: Efficiently retrieves multiple course evaluation documents from the `courses` table by taking a list of `instance_key`s.
-   **Returns**: A dictionary mapping each `instance_key` to its corresponding JSON data object.

### `update_course_data(instance_key, course_code, data)`

-   **What it does**: Inserts or updates a specific course instance (e.g., a course from a particular semester and instructor) in the `courses` table.
-   **Why it's important**: The primary mechanism for persisting newly scraped course evaluation data.

### `find_courses_by_name_db(search_query)`

-   **What it does**: Performs a basic, case-insensitive search against the `course_name` field within the `courses` table's JSON data.
-   **Returns**: A simple, sorted list of unique `course_code`s that have at least one instance matching the query.

### `find_courses_by_name_with_details_db(...)`

-   **What it does**: A sophisticated search function that powers the main course search feature. It finds courses by name and then processes the results to make them user-friendly.
-   **Key Features**:
    -   **Grouping**: Leverages `CourseGroupingService` to bundle cross-listed courses into a single search result.
    -   **Name Resolution**: Intelligently selects the most recent course name for a group to display the most relevant title.
    -   **Relevance Sorting**: Ranks results to prioritize exact matches over partial ones.
    -   **Pagination**: Supports `limit` and `offset` to allow for paginated API responses.
-   **Returns**: A list of structured dictionaries, where each dictionary represents a unique course or course group, ready for display in the UI.

### `count_courses_by_name_db(search_query)`

-   **What it does**: Counts the total number of unique course *groups* that match a search query.
-   **Why it's important**: Provides an accurate total count for pagination, as it respects course groupings (e.g., two cross-listed courses are counted as one item).

### `get_last_name(full_name)`

-   **What it does**: A simple string utility to extract the last name from a full name string.
-   **Purpose**: Supports the `find_instructor_variants_db` function by providing a consistent way to identify an instructor's last name.

### `find_instructor_variants_db(instructor_name)`

-   **What it does**: Searches the database for all known variations of an instructor's name by matching on the last name.
-   **Why it's important**: Allows the application to find all courses taught by an instructor, even if their name is recorded differently across different semesters (e.g., "J. Smith" vs. "John Smith").