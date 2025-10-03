# Flask API Server (`app.py`)

This file defines the main Flask application, which serves as the backend REST API for the course evaluation system. It handles incoming HTTP requests, validates inputs, and orchestrates calls to various service modules to fetch, search, and aggregate course data before sending it to the frontend.

## Core Components

### Flask `app`
The central `Flask` application instance. It's configured to serve the static frontend files and defines all the API routes.

### CORS Configuration
Cross-Origin Resource Sharing (CORS) is enabled to allow requests from the frontend, which is served on a different origin. The configuration explicitly allows the production URL, localhost for development, and a regular expression to dynamically match Vercel preview deployment URLs.

### `grouping_service`
An instance of `CourseGroupingService` that is initialized once when the application starts. It is used by the `/api/analyze` endpoint to find cross-listed or related courses.

## Helper Functions

### `validate_course_code(course_code)`
A utility function that validates if a given `course_code` string conforms to the standard JHU format (`XX.###.###`). It uses a regular expression and length check to prevent invalid or malicious inputs from being processed by the API endpoints.

## API Endpoints

All endpoints are prefixed with `/api`.

### `GET /`
- **Purpose**: Serves the main `index.html` of the React frontend application.
- **Interaction**: Acts as the entry point for the single-page application.

### `GET /api/course/<course_code>`
- **Purpose**: Retrieves all raw evaluation data for a specific course.
- **Interaction**:
    1. Validates the `course_code`.
    2. Calls `scraper_service.get_course_data_and_update_cache` to fetch data, which handles the logic for either returning cached data from the database or triggering a new scrape if the data is stale.

### `GET /api/search/course_name/<search_query>`
- **Purpose**: Performs a basic search for courses by name.
- **Interaction**: Calls `scraper_service.find_courses_by_name` to query the database for course codes matching the search term. Returns a list of course codes.

### `GET /api/search/course_name_detailed/<search_query>`
- **Purpose**: Performs a more detailed search for courses by name, returning course codes and their corresponding names. Supports pagination.
- **Interaction**: Calls `scraper_service.find_courses_by_name_with_details` with the search query and pagination parameters (`limit`, `offset`).

### `GET /api/search/instructor/<instructor_name>`
- **Purpose**: Finds all known name variations for a given instructor's last name.
- **Interaction**: Calls `db_utils.find_instructor_variants_db` to query the database for matching instructor names.

### `GET /api/grace-status/<course_code>`
- **Purpose**: Checks if a course is in a "grace period," meaning new evaluation data might be available soon, but a scrape hasn't been attempted recently.
- **Interaction**: Calls `scraper_service.get_course_grace_status` to determine the status based on the course's metadata in the database.

### `POST /api/recheck/<course_code>`
- **Purpose**: Forces a re-scrape of a course's evaluation data, bypassing the normal grace period logic.
- **Interaction**: Calls `scraper_service.force_recheck_course` to immediately trigger the scraping workflow for the given course.

### `POST /api/analyze/<course_code>`
- **Purpose**: Aggregates and returns the complete, raw evaluation data for a given course and all other courses in its logical group (e.g., cross-listed courses). This endpoint is the primary data source for the frontend's analysis engine.
- **Interaction**:
    1. Fetches the data for the primary `course_code` using `scraper_service.get_course_data_and_update_cache`.
    2. Uses `course_grouping_service.get_group_info` to identify all related courses.
    3. Iteratively calls `get_course_data_and_update_cache` for each related course to gather all associated data.
    4. Merges all fetched data into a single collection of course instances.
    5. Calls `analysis.extract_course_metadata` to determine the current and former names of the course.
    6. Constructs and returns a JSON object containing the aggregated raw data (`raw_data.instances`), course metadata, and grouping metadata for the client to process.