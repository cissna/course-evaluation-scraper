# Developer Documentation: `get_all_courses.py`

This script is a one-time utility designed to systematically query the JHU Student Information System (SIS) API to retrieve and aggregate all unique course offerings across specified schools and a defined historical/future range of academic terms.

The primary output is a text file (`jhu_as_en_courses.txt`) containing a sorted list of unique course codes (e.g., 'EN.500.401').

## Dependencies

*   `requests`: For making HTTP requests to the external SIS API.
*   `json`: For parsing API responses.
*   `time`: For introducing delays between API calls to respect rate limits.
*   `urllib.parse.quote`: For correctly encoding URL parameters.
*   `python-dotenv` (`dotenv`): For securely loading the API key from environment variables.
*   `os`: For environment variable interaction.

## Functions

### `get_api_key()`

**Summary:**
This function is responsible for securely retrieving the necessary JHU SIS API key. It prioritizes fetching the key from the `SIS_API_KEY` environment variable. If the environment variable is missing, it prompts the user interactively via the console to input the key.

**Big Picture:**
Authentication setup for the external API interaction. It ensures the script can proceed only if valid credentials are provided, either automatically or manually.

**Interaction Patterns:**
1.  Loads environment variables (`.env` file checked first).
2.  Checks `os.environ["SIS_API_KEY"]`.
3.  If missing, falls back to `input()`.
4.  Handles `KeyboardInterrupt` during manual input gracefully.

### `fetch_courses_for_school_and_term(school, term, api_key, session)`

**Summary:**
This function executes a single, targeted GET request to the JHU SIS API endpoint to retrieve all course data associated with a specific academic `school` and `term`. It handles URL encoding, standard HTTP error checking, and specific API response structures indicating no data found.

**Big Picture:**
The core data retrieval mechanism. It abstracts the complexities of querying the REST API for a single combination of parameters and ensures robust error handling for network issues or invalid responses.

**Interaction Patterns:**
1.  Constructs the full API URL, ensuring `school` and `term` are URL-encoded using `quote`.
2.  Uses the provided `requests.Session` object for the request.
3.  Applies a 30-second timeout.
4.  Uses `response.raise_for_status()` to catch 4xx/5xx errors.
5.  Specifically checks for a 200 OK response containing a JSON body with `{"Message": "No records found"}` and returns an empty list in that case.
6.  Returns the list of course objects on success, or `None` upon failure (network error, HTTP error, or JSON decoding issue).
7.  Includes necessary `time.sleep(0.2)` in the calling context (`main`) to manage API rate limits.

### `main()`

**Summary:**
The orchestrator of the entire data collection process. It initializes the API key, defines the target schools and the extensive list of academic terms, iterates through every School/Term combination, aggregates the unique course codes found, and finally writes the consolidated results to a file.

**Big Picture:**
Drives the comprehensive data crawl. It manages the session lifecycle, controls the nested loops over the defined search space (Terms $\times$ Schools), performs data deduplication using a Python `set`, and manages the final output persistence.

**Interaction Patterns:**
1.  Calls `get_api_key()` for authentication. Exits if the key is unavailable.
2.  Defines static lists for target `schools` and `terms` (covering Spring 2009 through Fall 2026).
3.  Initializes an empty `set` (`all_course_codes`) for efficient deduplication.
4.  Utilizes a `requests.Session` context manager for connection pooling across all requests.
5.  Iterates: `for school -> for term`.
6.  Calls `fetch_courses_for_school_and_term`.
7.  If data is returned, extracts the `'OfferingName'` field from each course object and adds it to the set.
8.  Introduces a 0.2-second delay after each term fetch.
9.  Upon completion, converts the set to a sorted list and writes each code to `jhu_as_en_courses.txt`.