# `backend/scrape_search.py` Developer Documentation

## File Summary

This module provides the core web scraping functionality for finding and extracting links to individual course evaluation reports from the JHU evaluation website. It is responsible for constructing search URLs based on various criteria, fetching the HTML content, and parsing it to retrieve the specific report links and associated course instance identifiers.

---

## Functions

### `get_evaluation_report_links(session, course_code, ...)`

#### High-Level Summary

This function scrapes a search results page on the JHU evaluation website to find all available evaluation reports for a given course. It constructs a URL with the specified search filters, fetches the page using a pre-authenticated session, and parses the HTML to extract the direct links to each report.

#### What it Does

-   **Builds & Queries:** It dynamically constructs a URL for the evaluation system's public results page based on a `course_code` and other optional filters (like `instructor`, `year`, etc.).
-   **Parses & Extracts:** It uses `BeautifulSoup` to parse the HTML of the results page. It specifically looks for `<a>` tags with the class `sr-view-report`, which correspond to individual evaluation reports.
-   **Constructs URLs:** For each link found, it reads custom `data-id` attributes to assemble the final, direct URL to the student report page (`StudentReport.aspx`).
-   **Identifies Instances:** It extracts the unique course instance code (e.g., `AS.030.101.01.FA15`) associated with each link, which serves as a unique key for that specific report.
-   **Checks for Pagination:** It detects the presence of a "Show more results" button to inform the caller whether additional pages of results exist.

#### Interaction Patterns

-   **External Dependency:** This function is tightly coupled to the HTML structure of the `asen-jhu.evaluationkit.com` website. Changes to CSS classes (e.g., `sr-view-report`), element IDs, or `data-id` attributes on the target site will break the scraper.
-   **Authentication:** It operates on the assumption that the `requests.Session` object passed to it has already been authenticated. It does not handle the login process itself.
-   **Return Value:** It returns a tuple containing a dictionary of `{course_instance_code: report_url}` and a boolean indicating if more results are available. This allows the calling service to decide if further scraping actions (like clicking "Show more") are needed.