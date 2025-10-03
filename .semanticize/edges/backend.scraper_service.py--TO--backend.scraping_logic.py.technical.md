The `scraper_service.py` file **imports** the function `get_authenticated_session` from `scraping_logic.py` using a relative import: `from .scraping_logic import get_authenticated_session`.

This function is **called** within `scraper_service.py` in three main methods:

1.  **`get_course_data_and_update_cache(course_code: str)`**:
    *   It is called inside a `try...except` block: `session = get_authenticated_session()`.
    *   The successful return value (a `requests.Session` object) is stored in the `session` variable and subsequently passed as an argument to `scrape_course_data_core`.
    *   It handles potential `requests.exceptions.RequestException` raised by `get_authenticated_session` (or subsequent requests made using the session) by marking the course metadata as failed and returning an error dictionary.

2.  **`force_recheck_course(course_code: str)`**:
    *   It is called inside a `try...except` block: `session = get_authenticated_session()`.
    *   The returned session is used in the subsequent call to `scrape_course_data_core`.
    *   It handles potential `requests.exceptions.RequestException` by returning an error dictionary.

The `scraping_logic.py` file **defines** the function `get_authenticated_session() -> requests.Session`. This function uses `requests.Session()` and interacts with an external authentication URL (`AUTH_URL`, imported from `.config`) to establish an authenticated session, which it then returns.

**Data Flow:**
`scraper_service.py` initiates the request for an authenticated session by calling `get_authenticated_session()`. `scraping_logic.py` performs the HTTP request using `requests` and returns a configured `requests.Session` object back to `scraper_service.py`. This session object is then used by `scraper_service.py` to execute the core scraping operation via `scrape_course_data_core`.