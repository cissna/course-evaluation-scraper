### Parameters
- `report_url` (str): The full, direct URL to a specific course evaluation report page.
- `session` (`requests.Session`): A pre-authenticated `requests.Session` object. The target website requires authentication to view evaluation pages, so a plain request will fail. This session must contain the necessary cookies.

### Return Value
- **On Success**: A `dict` containing the scraped course data. The keys of the dictionary are standardized (e.g., `course_name`, `instructor_name`, `overall_quality_frequency`). A successful scrape is explicitly defined by the presence of the `overall_quality_frequency` key in the returned dictionary.
- **On Failure**: If the function fails to scrape the data after all retry attempts, it returns a `dict` with a `scrape_failed: True` key and additional keys explaining the failure:
    - `reason`: A string indicating the cause, either `"network_error"` or `"overall_quality_frequency missing after successful requests"`.
    - `exception`: (Only for network errors) A string representation of the last exception caught.

### Implementation Details & Algorithm

#### 2.1. Retry and Exponential Backoff Mechanism

The function is designed to be resilient to temporary failures.

- **Looping**: The entire scraping process is wrapped in a `while` loop that runs up to `MAX_RETRIES` times.
- **Exponential Backoff**: If a scrape attempt fails, the function waits before retrying. The delay starts at `INITIAL_RETRY_DELAY` seconds and doubles after each failed attempt (`delay *= 2`). This prevents overwhelming the server and adapts to longer-lasting transient issues.
- **Failure Conditions**: An attempt is considered a failure if:
    1. A network-related exception (`requests.exceptions.RequestException` or any other `Exception`) occurs during the HTTP request or parsing.
    2. The HTTP request succeeds, but the critical data field (`overall_quality_frequency`) is not found in the parsed HTML. This handles cases where the page loads incompletely.
- **Final Failure**: If all `MAX_RETRIES` attempts are exhausted, the function gives up and returns a structured error dictionary, capturing the last known exception if one occurred.

#### 2.2. Data Scraping Process (Line-by-Line Equivalent)

Inside the `try` block of each attempt, the function performs the following steps:

1.  **HTTP Request**: It uses the provided `session` to execute an HTTP GET request to the `report_url` with a 10-second timeout. `response.raise_for_status()` is called to raise an exception for HTTP error codes (4xx or 5xx).
2.  **HTML Parsing**: The raw HTML text from the response is parsed into a `BeautifulSoup` object for easy traversal.
    ```python
    response = session.get(report_url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    ```
3.  **Scrape Course and Instructor Name**:
    - It locates the `<h3>` tag containing the text "Course:".
    - It then finds the immediate next sibling, which is a `<span>` tag containing the full course name string (e.g., "EN.601.226 : Data Structures").
    - The code splits the string at " : " and takes the second part to get the clean course name.
    - The same logic is applied to find the instructor's name, using "Instructor:" as the search key.
    ```python
    course_element = soup.find(lambda tag: tag.name == 'h3' and 'Course:' in tag.text)
    # ... find next sibling span and extract text ...
    ```
4.  **Scrape Quantitative Evaluation Data**:
    - The core evaluation data (question responses) is not rendered in standard HTML tags but is embedded as a JSON string within the `value` attribute of a hidden `<input>` tag with `id="hdnReportData"`.
    - The function finds this element and uses `json.loads()` to parse its `value` into a Python list of dictionaries.
    ```python
    report_data_element = soup.find('input', id='hdnReportData')
    report_data = json.loads(report_data_element['value'])
    ```
5.  **Data Mapping and Structuring**:
    - A `question_mapping` dictionary is used to translate the official question text from the website into the standardized keys used in this project's data model.
    - The code iterates through each question dictionary from the parsed `report_data`.
    - If a question's text matches a key in `question_mapping`, it processes the answers.
    - **For standard frequency questions**: It creates a dictionary where keys are the answer options (e.g., "Excellent", "Very Good") and values are the frequency (count) of that response. This is assigned to the corresponding mapped key (e.g., `overall_quality_frequency`).
    - **For TA names**: A special case exists for the question about TA names. The answers are in a single string, delimited by `||`. The code splits this string, strips whitespace from each name, and uses `list(set(...))` to store only the unique TA names. If no TAs are listed, it defaults to `["N/A"]`.
    ```python
    question_mapping = { ... }
    for question in report_data:
        # ... check question_text in question_mapping ...
        if key == "ta_names":
            # ... split '||' delimited string ...
        else:
            # ... create frequency_dict from Options ...
    ```
6.  **Success Validation**: After parsing, the function checks if the `overall_quality_frequency` key exists in the `scraped_data` dictionary. If it does, the scrape is considered successful, and the data is returned immediately, exiting the retry loop. If not, the attempt is marked as failed, and the loop continues to the next retry.

## 3. Standalone Execution (`if __name__ == '__main__'`)

The script is not designed to be run directly from the command line. The `if __name__ == '__main__'` block simply prints an informational message explaining that the module is intended for import and requires a pre-authenticated session and a valid report URL to be tested.