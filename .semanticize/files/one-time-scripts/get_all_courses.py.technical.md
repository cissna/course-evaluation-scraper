# Technical Documentation: `one-time-scripts/get_all_courses.py`

This Python script is designed to systematically retrieve and aggregate all unique course offerings ("OfferingName") from the Johns Hopkins University Student Information System (JHU SIS) API across a defined range of academic terms and specific schools.

The primary goal is to build a comprehensive, deduplicated list of course codes for the Krieger School of Arts and Sciences and the Whiting School of Engineering spanning from Spring 2009 up to Fall 2026.

## Dependencies

The script relies on the following standard and third-party libraries:

- `requests`: For making HTTP requests to the external API.
- `json`: For parsing JSON responses from the API.
- `time`: For introducing delays (`time.sleep`) between API calls to respect rate limits.
- `urllib.parse.quote`: For URL-encoding parameters like school and term names.
- `dotenv`: To load sensitive credentials (API key) from environment variables (`.env` file).
- `os`: To interact with the operating system environment variables.

## Core Functionality Breakdown

The script executes three main phases: configuration/setup, API fetching, and data aggregation/output.

### 1. API Key Retrieval (`get_api_key`)

This function handles securing the necessary authentication credential.

**Function Signature:**
`def get_api_key() -> str | None`

**How it Works:**
1.  `load_dotenv()`: Attempts to load environment variables from a local `.env` file.
2.  `os.environ.get("SIS_API_KEY")`: Checks if the required environment variable `SIS_API_KEY` is set.
3.  If the key is missing, it prompts the user interactively via `input()` to provide the key manually.
4.  A `KeyboardInterrupt` (Ctrl+C) during input is caught, printing a cancellation message and returning `None`.
5.  Returns the retrieved (or input) API key string, or `None` if retrieval failed or was cancelled.

### 2. API Data Fetching (`fetch_courses_for_school_and_term`)

This function executes a single request to the JHU SIS API endpoint for a specific school and term combination.

**Function Signature:**
`def fetch_courses_for_school_and_term(school: str, term: str, api_key: str, session: requests.Session) -> list | None`

**Parameters:**
- `school` (str): The full name of the school (e.g., "Krieger School of Arts and Sciences").
- `term` (str): The academic term string (e.g., "Fall 2025").
- `api_key` (str): The valid SIS API key.
- `session` (requests.Session): An active `requests.Session` object to reuse HTTP connections.

**How it Works:**
1.  **URL Encoding:** The `school` and `term` strings are URL-encoded using `quote()` to ensure proper handling of spaces and special characters in the URL path.
    ```python
    encoded_school = quote(school)
    encoded_term = quote(term)
    ```
2.  **URL Construction:** The final endpoint URL is constructed using an f-string, incorporating the encoded path components and the API key as a query parameter.
    ```python
    url = f"https://sis.jhu.edu/api/classes/{encoded_school}/{encoded_term}?key={api_key}"
    ```
3.  **Request Execution:** A GET request is made using the provided `session`. A `timeout` of 30 seconds is enforced.
4.  **Error Handling:**
    - `response.raise_for_status()`: Immediately checks the HTTP status code. If it's 4xx or 5xx, a `requests.exceptions.HTTPError` is raised and caught below.
5.  **Response Processing:**
    - The response body is parsed into a Python object using `response.json()`.
    - **Special Case Check:** The script explicitly checks if the API returned a 200 OK status but contained a specific error dictionary: `{'Message': 'No records found'}`. If this is true, it returns an empty list (`[]`) instead of raising an error.
6.  **Exception Handling:** Catches `HTTPError`, general `RequestException`, and `JSONDecodeError`, printing diagnostic messages for each failure type.
7.  **Return Value:** Returns the list of course dictionaries if successful, an empty list if no courses were found, or `None` if a connection/HTTP error occurred.

### 3. Main Orchestration (`main`)

This function coordinates the entire fetching and output process.

**Function Signature:**
`def main() -> None`

**Data Structures & Configuration:**
- **`terms` (list):** A hardcoded list containing 70 specific academic term strings, ranging from "Spring 2009" to "Fall 2026".
- **`schools` (list):** A list containing the two target schools: `"Krieger School of Arts and Sciences"` and `"Whiting School of Engineering"`.
- **`all_course_codes` (set):** A Python `set` is used to store the extracted `OfferingName` values. This guarantees automatic deduplication of course codes across different terms and schools.

**Execution Flow:**
1.  Calls `get_api_key()`. If the key is absent, execution stops.
2.  Initializes `all_course_codes` as an empty set.
3.  **Session Management:** Enters a `with requests.Session() as session:` block. This initializes a persistent session object, which is crucial for connection pooling, improving the efficiency of the subsequent loop of requests.
4.  **Iterative Fetching:** It performs nested loops:
    - Outer loop iterates through `schools`.
    - Inner loop iterates through `terms`.
5.  Inside the inner loop:
    - `fetch_courses_for_school_and_term` is called.
    - If the result (`courses`) is not `None` (i.e., the request succeeded or returned an empty set):
        - It iterates through the returned course dictionaries.
        - If `'OfferingName'` exists in a course dictionary, that value is added to the `all_course_codes` set.
    - **Rate Limiting:** `time.sleep(0.2)` is executed after every successful term fetch to prevent overwhelming the SIS API server.
6.  **Output Generation:**
    - After all API calls complete, the set is converted to a sorted list (`sorted_courses`).
    - The script attempts to write this list, one course code per line, to the file `jhu_as_en_courses.txt`.
    - Success or failure messages regarding file writing are printed to the console.

## Algorithm Summary

The script employs a **Brute-Force Iterative Query Algorithm** combined with **Set-based Deduplication**:

1.  **Initialization:** Define the universe of data to query (specific schools and a fixed list of terms).
2.  **Authentication:** Secure the necessary API key.
3.  **Iteration:** Systematically iterate through every combination of (School, Term).
4.  **API Call:** For each combination, execute an HTTP GET request to the JHU SIS endpoint, ensuring proper URL encoding and error checking.
5.  **Data Extraction:** Upon successful receipt of data, extract the specific field of interest (`OfferingName`).
6.  **Aggregation:** Add the extracted item to a `set`. The use of a set ensures that if "CS 101" appears in Fall 2024 and Spring 2025, it is only stored once.
7.  **Persistence:** Finally, output the unique, sorted collection to a local file.