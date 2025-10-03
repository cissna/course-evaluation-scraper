### Parameters

-   **`session` (requests.Session)**: An authenticated `requests.Session` object. The caller is responsible for handling the initial authentication with the evaluation website.
-   **`course_code` (str)**: The primary and required identifier for the course (e.g., 'EN.601.473').
-   **`instructor` (str, optional)**: The name of an instructor to filter by.
-   **`term_id` (str, optional)**: A specific term ID to filter by (e.g., a code for "Fall 2023").
-   **`year` (str, optional)**: A specific academic year to filter by.
-   **`area_id` (str, optional)**: A specific academic area/department ID to filter by.
-   **`question_key` (str, optional)**: A key for a specific evaluation question to filter by.
-   **`search` (str, optional)**: A general search query string (noted as unimportant in the code).

### Returns

-   **`tuple[dict, bool]`**: A tuple containing two elements:
    1.  A `dict` mapping unique course instance codes (e.g., `AS.030.101.01.FA15`) to their corresponding full report URL.
    2.  A `bool` that is `True` if a "Show more results" button is detected on the page, indicating pagination, and `False` otherwise.

### Implementation Details

1.  **URL Construction**:
    -   The function starts with a base URL for the public results page: `https://asen-jhu.evaluationkit.com/`.
    -   It initializes a `query_params` dictionary with the mandatory `Course` parameter (`course_code`).
    -   It conditionally adds any provided optional filters (`Instructor`, `TermId`, `Year`, etc.) to the `query_params` dictionary.
    -   The `urllib.parse.urlencode` function converts the `query_params` dictionary into a URL-encoded query string.
    -   This query string is appended to the report path (`Report/Public/Results?{...}`).
    -   Finally, `urllib.parse.urljoin` combines the base URL and the path to create the final, absolute URL for the search query.

2.  **HTTP Request and Parsing**:
    -   It uses the provided `session` object to send an HTTP GET request to the constructed `course_url` with a 10-second timeout.
    -   `course_page_response.raise_for_status()` is called to raise an `HTTPError` if the request was unsuccessful (i.e., status code 4xx or 5xx).
    -   The raw HTML text from the response is parsed into a `BeautifulSoup` object (`soup`) using the standard `html.parser`.

3.  **Data Extraction**:
    -   `soup.find_all('a', class_='sr-view-report')` is used to locate all hyperlink (`<a>`) elements that have the CSS class `sr-view-report`. These are the links to the individual evaluation reports.
    -   `soup.find('a', id='publicMore')` is used to check for the existence of the "Show more results" button. The presence of this element indicates that not all results are displayed on the current page. The result is stored in `has_more_results`.
    -   If no links are found (`if not links_found`), the function asserts that the `has_more_results` flag must also be false and returns an empty dictionary and `False`.

4.  **Link and Course Code Processing**:
    -   The function iterates through each `link` found by BeautifulSoup.
    -   For each link, it extracts four essential pieces of data from `data-id` attributes: `data-id0`, `data-id1`, `data-id2`, and `data-id3`.
    -   It validates that all four `data-id` attributes were successfully found.
    -   If valid, it constructs the final report URL. The four `data-id` values are concatenated with commas into an `id_string`, which is then used as a query parameter for the student report base URL (`https://asen-jhu.evaluationkit.com/Reports/StudentReport.aspx?id={id_string}`).
    -   To find the associated course instance code, the code traverses up the DOM from the link element using `link.find_parent('div', class_='row')` to find the container for that search result.
    -   Within this parent `div`, it searches for a paragraph (`<p>`) tag with the class `sr-dataitem-info-code`. The text content of this tag, once stripped of whitespace, is the unique course instance code (e.g., `AS.030.101.01.FA15`).
    -   If the course instance code is found, a new key-value pair is added to the `report_links` dictionary: `{course_instance_code: final_url}`.
    -   If any part of the data extraction fails (e.g., missing `data-id` attributes or the course code element isn't found), a message is printed to standard output, and that specific link is skipped.

5.  **Return Value**:
    -   The function returns the populated `report_links` dictionary and the `has_more_results` boolean.

## 3. Example Usage (`if __name__ == '__main__'`)

This block demonstrates how to use the `get_evaluation_report_links` function as a standalone script.

### Implementation Details

1.  **Authentication**:
    -   Since the script requires an authenticated session, this block first creates a new `requests.Session`.
    -   It defines a hardcoded `auth_url`. A GET request to this URL appears to set the necessary session cookies to grant access to the public reports. This simulates the initial step a user would take to view reports.
    -   It includes a `try...except` block to handle potential `requests.exceptions.RequestException` during authentication or scraping.

2.  **Simple Search Example**:
    -   It defines a `target_course` ('AS.030.101').
    -   It calls `get_evaluation_report_links` with the authenticated session and the course code.
    -   It then prints the number of links found, the links themselves (code and URL), and whether the "Show more results" button was present.

3.  **Advanced Search Example**:
    -   It defines a more specific search with a `target_course_adv` ('EN.601.220'), `target_instructor` ('Jason Eisner'), and `target_year` ('2023').
    -   It calls `get_evaluation_report_links` with these additional filter parameters.
    -   The results are printed in the same format as the simple search.

This block serves as both a practical usage example and a basic integration test for the scraping logic.