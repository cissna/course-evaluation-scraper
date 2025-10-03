The source file `backend/workflow_helpers.py` imports the function `get_evaluation_report_links` from the target file `backend/scrape_search.py`.

**Specific Function Calls and Imports:**

1.  **Import:**
    In `backend/workflow_helpers.py`:
    ```python
    from .scrape_search import get_evaluation_report_links
    ```

2.  **Usage in `get_all_links_by_section`:**
    The imported function `get_evaluation_report_links` is called multiple times within the helper function `get_all_links_by_section` to retrieve report links for specific course sections, optionally filtered by year:
    ```python
    # Initial call for a section code (no year specified)
    links, has_more = get_evaluation_report_links(session, section_course_code)
    
    # Subsequent calls when pagination is detected, filtered by year
    yearly_links, _ = get_evaluation_report_links(session, section_course_code, year=year)
    ```
    *   It is called with `session` (a `requests.Session` object) and `section_course_code` (a string like 'AS.020.101.01').
    *   When breaking down by year, the keyword argument `year=year` is passed.

3.  **Usage in `scrape_course_data_core`:**
    The function is also called in the main logic flow of `scrape_course_data_core`:
    ```python
    # Initial call for the main course code
    initial_links, has_more_initial = get_evaluation_report_links(session=session, course_code=course_code)
    
    # Subsequent calls during the year-by-year scan
    yearly_links, has_more_yearly = get_evaluation_report_links(session=session, course_code=course_code, year=year)
    ```
    *   These calls use keyword arguments (`session=session`, `course_code=course_code`).

**Data Flow and Return Values:**

The function `get_evaluation_report_links` (from the target file) returns a tuple: `(dict, bool)`.

1.  **`dict` (Report Links):** A dictionary mapping course instance codes (e.g., 'AS.030.101.01.FA15') to their corresponding report URLs.
2.  **`bool` (Pagination Indicator):** A boolean indicating if the source HTML contained a "Show more results" button (`True` if present, `False` otherwise).

In `workflow_helpers.py`, these return values are used to:
*   Populate the `all_links` dictionary (in `get_all_links_by_section`).
*   Determine the scraping strategy: if `has_more_initial` is `True`, the logic proceeds to the complex year-by-year or section-by-section scraping routines.
*   Update the `links_to_process` dictionary in `scrape_course_data_core`.

**Technical Interaction Summary:**

`workflow_helpers.py` relies entirely on `scrape_search.get_evaluation_report_links` to fetch the initial list of report URLs from the external evaluation website. This function handles the HTTP request, URL construction (including query parameters for filtering by year), HTML parsing (using BeautifulSoup), and identification of pagination indicators. This separation of concerns means the workflow logic handles *when* and *how* to iterate (sections, years) while the search utility handles the *actual retrieval* of links for a given set of parameters.