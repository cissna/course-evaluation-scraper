# Technical Documentation for `backend/app.py`

## 1. Overview

This file is the main entry point for the Flask web server, which serves as the backend API for the JHU Course Evaluation Analyzer. It defines all the REST API endpoints that the frontend application consumes. Its responsibilities include handling incoming HTTP requests, validating inputs, delegating business logic to various service modules (`scraper_service`, `analysis`, `db_utils`), and formatting the responses in JSON.

## 2. Initialization and Configuration

### Flask Application Setup
- A Flask application instance is created: `app = Flask(__name__, static_folder='../static', static_url_path='/')`.
- The `static_folder` is configured to point to a `static` directory at the parent level, which is intended to serve the frontend's `index.html`.

### Cross-Origin Resource Sharing (CORS)
- The application is configured to handle CORS to allow requests from specific origins. This is crucial for a decoupled frontend-backend architecture.
- `CORS(app, origins=allowed_origins)` enables CORS for the entire app.
- The `allowed_origins` list includes:
    - `http://localhost:3000`: For local React development server.
    - `http://127.0.0.1:5000`: For local Flask development server.
    - `https://course-evaluation-scraper.vercel.app`: The production frontend URL.
    - `re.compile(r"^https://course-evaluation-scraper-[a-z0-9]+-[a-z0-9-]+\.vercel\.app$")`: A regular expression to dynamically allow requests from Vercel's preview deployment URLs, which have unique, generated subdomains.

### Service Instantiation
- `grouping_service = CourseGroupingService()`: An instance of the `CourseGroupingService` is created at startup. This service is responsible for identifying which courses are cross-listed or otherwise grouped together.

## 3. Helper Functions

### `validate_course_code(course_code)`
- **Signature**: `validate_course_code(course_code: str) -> bool`
- **Purpose**: Validates that a given `course_code` string conforms to the standard JHU format.
- **Algorithm**:
    1.  Checks if the `course_code` is `None` or has a length greater than 50 characters to prevent abuse. Returns `False` if so.
    2.  Uses a regular expression `r'^[A-Za-z]{2}\.\d{3}\.\d{3}$'` to match the pattern: two letters, a dot, three digits, a dot, and three digits. The match is case-insensitive for the letters.
    3.  Returns `True` if the pattern matches, `False` otherwise.

## 4. API Endpoints

All API endpoints are prefixed with `/api/`.

### `GET /`
- **Function**: `home()`
- **Purpose**: Serves the main entry point of the frontend application.
- **Implementation**: Returns the `index.html` file from the configured `static_folder`.

### `GET /api/course/<string:course_code>`
- **Function**: `get_course_data(course_code)`
- **Purpose**: Retrieves all evaluation data for a single course. It triggers a web scrape if the cached data is considered stale.
- **Implementation**:
    1.  Validates the `course_code` using `validate_course_code`. Returns a 400 error if invalid.
    2.  Normalizes the `course_code` to uppercase (`course_code.upper()`) for consistency with the database.
    3.  Calls `get_course_data_and_update_cache(course_code)` from `scraper_service.py` to handle the core logic of fetching/scraping.
    4.  If the service returns no data, a 404 error is returned.
    5.  If the service returns a dictionary containing an "error" key, it's passed through with a 500 status code.
    6.  On success, the data is serialized to JSON and returned with a 200 status code.
    7.  A generic 500 error is returned if any other exception occurs.

### `GET /api/search/course_name/<string:search_query>`
- **Function**: `search_by_course_name(search_query)`
- **Purpose**: Searches for courses by their name.
- **Implementation**:
    1.  Decodes the `search_query` using `urllib.parse.unquote` to handle special characters in the URL.
    2.  Validates the query length (max 1000 characters) to prevent performance issues, returning a 400 error if exceeded.
    3.  Calls `find_courses_by_name(search_query)` from `scraper_service.py`.
    4.  Returns the resulting list of course codes as a JSON array.

### `GET /api/search/course_name_detailed/<string:search_query>`
- **Function**: `search_by_course_name_detailed(search_query)`
- **Purpose**: Performs a detailed search for courses by name, returning course codes and names. Supports pagination.
- **Implementation**:
    1.  Decodes and validates the `search_query` length, same as the simple search.
    2.  Retrieves `limit` and `offset` query parameters from the request arguments for pagination. Defaults are `None` and `0` respectively.
    3.  Validates pagination parameters: `limit` must be between 1 and 100, and `offset` must be non-negative. Returns a 400 error if invalid.
    4.  Calls `find_courses_by_name_with_details(search_query, limit, offset)` from `scraper_service.py`.
    5.  Returns the detailed results as a JSON object.

### `GET /api/search/instructor/<string:instructor_name>`
- **Function**: `search_by_instructor_name(instructor_name)`
- **Purpose**: Finds all known name variations for a given instructor's last name.
- **Implementation**:
    1.  Decodes and validates the `instructor_name` length (max 1000 characters).
    2.  Calls `find_instructor_variants_db(instructor_name)` from `db_utils.py`.
    3.  Returns the list of name variants as a JSON array.

### `GET /api/grace-status/<string:course_code>`
- **Function**: `get_grace_status(course_code)`
- **Purpose**: Checks if a course is in a "grace period," meaning new evaluation data might be available soon, but a scrape hasn't been attempted recently.
- **Implementation**:
    1.  Validates and normalizes the `course_code`.
    2.  Calls `get_course_grace_status(course_code)` from `scraper_service.py`.
    3.  Returns the status object as JSON.

### `POST /api/recheck/<string:course_code>`
- **Function**: `recheck_course_data(course_code)`
- **Purpose**: Forces a re-scrape of a course's evaluation data, bypassing the normal grace period logic.
- **Implementation**:
    1.  Validates and normalizes the `course_code`.
    2.  Calls `force_recheck_course(course_code)` from `scraper_service.py`.
    3.  Returns the newly fetched data, or an error if none is found, similar to the `get_course_data` endpoint.

### `POST /api/analyze/<string:course_code>`
- **Function**: `analyze_course_data(course_code)`
- **Purpose**: This is the primary data aggregation endpoint. It collects all raw evaluation data for a given course and any courses it's grouped with. It does **not** perform statistical analysis; it returns the complete raw dataset for the frontend to process.
- **Algorithm**:
    1.  Validates and normalizes the `course_code`.
    2.  Retrieves the JSON body of the request via `request.get_json()`. While the parameters are fetched, they are not used in the subsequent logic, as all analysis is now client-side.
    3.  Fetches the data for the primary `course_code` using `get_course_data_and_update_cache`.
    4.  If no data is found for the primary course, it checks if the course is part of a group using `grouping_service.get_group_info`. If not, it returns a 404 error.
    5.  Initializes an empty dictionary `all_instances` to aggregate data from all grouped courses.
    6.  If the course is part of a group, it iterates through each `grouped_code` in the group.
    7.  For each `grouped_code`, it calls `get_course_data_and_update_cache` to fetch its data.
    8.  It merges the fetched data into `all_instances`. To avoid key collisions and preserve origin information, instance keys are prefixed with the course code (e.g., `AS.100.101_FA23_...`), and the `course_code` is added as a field inside each instance's data dictionary. This is critical for the frontend to separate data by its original course.
    9.  If the course is not part of a group, `all_instances` simply contains the data for the primary course.
    10. It calls `extract_course_metadata` from `analysis.py` to determine the current and former names of the course based on the aggregated data.
    11. It determines the final set of `actual_grouped_courses` by parsing the course codes from the keys in the `all_instances` dictionary. This ensures the list only contains courses that actually contributed data.
    12. It constructs and returns a final JSON object with a single top-level key, `raw_data`. This object contains:
        - `instances`: The `all_instances` dictionary.
        - `metadata`: Course name history.
        - `grouping_metadata`: A list of courses that contributed data, a description of the group, and a boolean `is_grouped`.

## 5. Main Execution Block
- The `if __name__ == '__main__':` block ensures that the Flask development server (`app.run(debug=True)`) is started only when the script is executed directly.
- `debug=True` enables Flask's debug mode, which provides automatic reloading on code changes and detailed error pages during development.