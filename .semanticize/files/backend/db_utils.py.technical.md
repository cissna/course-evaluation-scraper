# Technical Documentation: `backend/db_utils.py`

## 1. Overview

This module provides a suite of utility functions for interacting with the PostgreSQL database. It encapsulates all direct database operations, including connection management, and CRUD (Create, Read, Update) actions for course metadata and raw course evaluation data. It also contains functions for performing complex searches for courses and instructors, including logic for handling cross-listed course groupings.

## 2. Dependencies

- **`os`**: Used to access environment variables, specifically `DATABASE_URL`.
- **`psycopg2`**: The PostgreSQL database adapter for Python used to execute all database queries.
- **`json`**: Used to serialize Python dictionaries into JSON strings for storage in `JSONB` database columns.
- **`dotenv`**: Used to load environment variables from a `.env` file for local development.
- **`backend.course_grouping_service.CourseGroupingService`**: A service used to resolve which courses are cross-listed or grouped together. This is used in search functions to return comprehensive results.

## 3. Core Functions

### 3.1. Connection Management

---

#### `get_db_connection()`

Establishes and returns a new connection to the PostgreSQL database.

-   **Signature**: `get_db_connection()`
-   **Parameters**: None.
-   **Returns**: A `psycopg2` connection object.
-   **Raises**: `Exception` if the `DATABASE_URL` environment variable is not set.
-   **Implementation Details**:
    1.  The `load_dotenv()` function is called at the module level to ensure environment variables are loaded from a `.env` file if present.
    2.  `os.getenv("DATABASE_URL")` retrieves the database connection string.
    3.  `psycopg2.connect(conn_string)` uses the string to establish the connection.

### 3.2. Metadata Operations

---

#### `get_course_metadata(course_code)`

Fetches the metadata record for a single course.

-   **Signature**: `get_course_metadata(course_code: str) -> dict | None`
-   **Parameters**:
    -   `course_code` (str): The unique identifier for the course (e.g., `AS.180.101`).
-   **Returns**: A dictionary containing the course metadata if found, otherwise `None`.
-   **Implementation Details**:
    1.  Opens a database connection using `get_db_connection()`.
    2.  Executes a `SELECT * FROM course_metadata WHERE course_code = %s` query.
    3.  If `cur.fetchone()` returns a result, it dynamically constructs a dictionary by zipping the column names (retrieved from `cur.description`) with the row values.

---

#### `update_course_metadata(course_code, metadata)`

Inserts a new course metadata record or updates an existing one if it already exists (an "upsert" operation).

-   **Signature**: `update_course_metadata(course_code: str, metadata: dict) -> None`
-   **Parameters**:
    -   `course_code` (str): The course's unique code.
    -   `metadata` (dict): A dictionary containing the metadata fields to insert or update.
-   **Returns**: None.
-   **Implementation Details**:
    1.  It executes an `INSERT ... ON CONFLICT DO UPDATE` SQL statement, which is an atomic and efficient way to handle upserts.
    2.  **`ON CONFLICT (course_code)`**: Specifies that a conflict occurs if a row with the same `course_code` already exists.
    3.  **`DO UPDATE SET ...`**: If a conflict occurs, it updates the fields of the existing row. The `EXCLUDED` pseudo-table contains the values that would have been inserted, which are used in the `SET` clause.
    4.  The `updated_at` field is explicitly set to `NOW()` to ensure the timestamp is always updated on a modification.
    5.  The `relevant_periods` field, which is expected to be a list or dict, is serialized to a JSON string using `json.dumps()`.

### 3.3. Course Data Operations

---

#### `get_course_data_by_keys(keys)`

Fetches raw course evaluation data for multiple course instances based on a list of instance keys.

-   **Signature**: `get_course_data_by_keys(keys: list[str]) -> dict`
-   **Parameters**:
    -   `keys` (list[str]): A list of unique instance keys (e.g., `['AS.180.101_FA23', 'EN.601.220_SP24']`).
-   **Returns**: A dictionary mapping each `instance_key` to its corresponding `data` (JSONB content).
-   **Implementation Details**:
    1.  Uses the `WHERE instance_key = ANY(%s)` clause, which is an efficient PostgreSQL-specific way to find all rows where `instance_key` matches any value in the provided array.
    2.  The resulting list of `(instance_key, data)` tuples is converted into a dictionary for O(1) lookup time by the caller.

---

#### `update_course_data(instance_key, course_code, data)`

Inserts or updates the raw evaluation data for a specific course instance.

-   **Signature**: `update_course_data(instance_key: str, course_code: str, data: dict) -> None`
-   **Parameters**:
    -   `instance_key` (str): The unique identifier for the course instance (e.g., `AS.180.101_FA23`).
    -   `course_code` (str): The base code for the course.
    -   `data` (dict): The raw evaluation data to be stored.
-   **Returns**: None.
-   **Implementation Details**:
    1.  Similar to `update_course_metadata`, this function uses an `INSERT ... ON CONFLICT (instance_key) DO UPDATE` statement.
    2.  The `data` dictionary is serialized into a JSON string via `json.dumps()` before being passed to the query.
    3.  If the `instance_key` exists, the `data` field is overwritten with the new data, and `updated_at` is set to `NOW()`.

## 4. Search Functions

---

#### `find_courses_by_name_db(search_query)`

Performs a simple search for courses by name, returning a list of unique course codes.

-   **Signature**: `find_courses_by_name_db(search_query: str) -> list[str]`
-   **Parameters**:
    -   `search_query` (str): The text to search for within course names.
-   **Returns**: A sorted list of unique `course_code` strings that match the query.
-   **Implementation Details**:
    1.  The query uses `ILIKE` for a case-insensitive substring search.
    2.  The `data->>'course_name'` operator extracts the `course_name` field as text from the `data` JSONB column for comparison.
    3.  `SELECT DISTINCT course_code` ensures each matching course code is returned only once.

---

#### `find_courses_by_name_with_details_db(search_query, limit=None, offset=None)`

A comprehensive search function that finds courses by name, groups them with their cross-listed equivalents, and returns detailed, paginated results.

-   **Signature**: `find_courses_by_name_with_details_db(search_query: str, limit: int | None = None, offset: int | None = None) -> list[dict]`
-   **Parameters**:
    -   `search_query` (str): The search term.
    -   `limit` (int, optional): The maximum number of results for pagination.
    -   `offset` (int, optional): The starting offset for pagination.
-   **Returns**: A sorted and paginated list of dictionaries, where each dictionary represents a unique course group.
-   **Algorithm**:
    1.  **Initial Fetch**: An initial query retrieves the most recent instance of each course matching the search query.
        -   `SELECT DISTINCT ON (course_code)` is used to get one result per course.
        -   The `ORDER BY` clause is critical: it sorts by `course_code`, then by year (descending, extracted from `instance_key`), and finally by semester (FA=3, SU=2, SP=1) to ensure `DISTINCT ON` picks the most recent version of the course.
    2.  **Grouping**: It iterates through the fetched courses. A `processed_groups` set is used to avoid processing the same group multiple times.
    3.  **Group Resolution**: For each course, `CourseGroupingService.get_grouped_courses()` is called to get all cross-listed courses.
    4.  **Find Most Recent Name**: The function then finds the most recent course name *within the entire group*. This may involve additional database queries for other courses in the group to compare their `updated_at` timestamps.
    5.  **Result Aggregation**: A result object is created for the group, including:
        -   `course_code`: A display-friendly, "/" separated string of all course codes in the group (e.g., `AS.100.101/PH.100.101`).
        -   `course_name`: The most recent name found among all courses in the group.
        -   `group_courses`: The full list of course codes in the group.
    6.  **Relevance Sorting**: The aggregated results are sorted to prioritize user experience: exact name matches appear first, followed by "starts with" matches, and finally "contains" matches.
    7.  **Pagination**: The final sorted list is sliced using the `limit` and `offset` parameters.

---

#### `count_courses_by_name_db(search_query)`

Counts the total number of unique course *groups* that match a search query. This is intended to be used by the frontend for calculating total pages for pagination.

-   **Signature**: `count_courses_by_name_db(search_query: str) -> int`
-   **Parameters**:
    -   `search_query` (str): The search term.
-   **Returns**: The total count of unique course groups.
-   **Algorithm**:
    1.  Fetches all `DISTINCT course_code`s that match the search query.
    2.  Initializes a `CourseGroupingService`.
    3.  Iterates through the list of course codes, using a `processed_groups` set to keep track of visited groups.
    4.  For each code not yet processed, it resolves the group, increments a counter, and adds all courses from that group to the `processed_groups` set.
    5.  Returns the final counter value.

---

#### `find_instructor_variants_db(instructor_name)`

Finds all known variations of an instructor's name in the database, based on a last name match.

-   **Signature**: `find_instructor_variants_db(instructor_name: str) -> list[str]`
-   **Parameters**:
    -   `instructor_name` (str): An instructor's name (e.g., "John Smith").
-   **Returns**: A sorted list of unique full name strings found in the database that share the same last name.
-   **Implementation Details**:
    1.  The helper function `get_last_name()` is used to extract the last name from the input string.
    2.  A PostgreSQL query is executed to find all distinct instructor names where the last name matches.
    3.  The SQL function `split_part(data->>'instructor_name', ' ', -1)` is used to extract the last part of the stored instructor name string. This is converted to lowercase for a case-insensitive comparison.
    4.  The results are collected into a `set` to ensure uniqueness, the original search name is added, and a sorted list is returned.

---

#### `get_last_name(full_name)`

A simple utility to extract the last name from a full name string.

-   **Signature**: `get_last_name(full_name: str) -> str`
-   **Parameters**:
    -   `full_name` (str): The full name.
-   **Returns**: The last name, converted to lowercase. Returns an empty string if the input is empty.
-   **Implementation**: `full_name.strip().split()[-1].lower()`