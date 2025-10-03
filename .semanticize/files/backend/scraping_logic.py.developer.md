# Developer Documentation for `backend/scraping_logic.py`

## File Overview

This file contains the logic for authenticating with the JHU course evaluation system. Its primary responsibility is to create and provide an authenticated `requests.Session` that can be used by other parts of the application to perform scraping operations. This centralizes the authentication process, ensuring that any module needing to make authenticated requests can do so consistently.

## High-Level Interaction Patterns

Any service or function that needs to scrape data from the JHU website will first call `get_authenticated_session()` from this file. The returned session object is then used to make all subsequent HTTP requests to the target endpoints. The calling code is responsible for handling potential exceptions during the authentication process.

---

## Functions

### `get_authenticated_session() -> requests.Session`

-   **What it does:** This function creates a new `requests.Session` and authenticates it against the authentication URL specified in `config.py`. It essentially "logs in" to the system to prepare for data scraping.
-   **Returns:** A `requests.Session` object containing the necessary authentication cookies to be used for subsequent scraping requests.
-   **Error Handling:** It will raise a `requests.exceptions.RequestException` if the initial authentication request fails due to network issues or an unsuccessful HTTP status code (e.g., 4xx, 5xx). This allows callers to implement retry logic or fail gracefully.