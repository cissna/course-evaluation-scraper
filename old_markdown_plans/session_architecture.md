# Session Management and Retry Architecture

This document outlines a new architecture for session management and retrying failed courses. The primary goal is to use a single session for as long as possible, and when it expires, create a new one and retry the last failed course.

## 1. Custom Exception

A new custom exception will be defined to signal that a session has likely expired. This will allow for specific handling of this error case.

**`exceptions.py`** (new file)
```python
class SessionExpiredException(Exception):
    """Raised when the session is believed to have expired."""
    pass
```

## 2. `main.py` Logic

The `main.py` file will be updated to manage a single, shared `requests.Session` object and to handle the `SessionExpiredException`.

**Changes:**

*   **Shared Session:** A single `session` object will be created at the beginning of the script and passed to the workflow.
*   **Retry Loop:** A `while` loop will be used to retry the scraping workflow for a course if a `SessionExpiredException` is caught. A retry counter will prevent infinite loops.

**`main.py`**
```python
from workflow import run_scraper_workflow
from scraping_logic import get_authenticated_session
from exceptions import SessionExpiredException

if __name__ == "__main__":
    department_code = 'EN.601'
    session = get_authenticated_session()

    if not session:
        print("Could not get initial authenticated session. Aborting.")
        exit()

    for course_number in range(0, 1000):
        formatted_course_number = f"{course_number:03d}"
        target_course = f"{department_code}.{formatted_course_number}"
        
        print(f"--- Processing course: {target_course} ---")
        
        retries = 1 # Allow one retry
        while retries >= 0:
            try:
                run_scraper_workflow(target_course, session)
                print(f"--- Finished processing: {target_course} ---\n")
                break # Success, exit retry loop
            except SessionExpiredException:
                print(f"Session expired while processing {target_course}. Retrying...")
                session = get_authenticated_session()
                if not session:
                    print("Could not get new authenticated session. Aborting retries for this course.")
                    break
                retries -= 1
            except Exception as e:
                print(f"--- CRITICAL ERROR in workflow for {target_course}: {e} ---")
                print("--- Moving to next course. ---\n")
                break # Exit retry loop on other errors

    print("--- All department courses have been processed. ---")
```

## 3. `workflow.py` Logic

The `run_scraper_workflow` function will be modified to accept the shared session and to raise the `SessionExpiredException` when appropriate.

**Changes:**

*   **Accept Session:** The function will accept the `session` object as an argument instead of creating its own.
*   **Exception Handling:** It will catch `requests.exceptions.RequestException` from the scraping functions. If the exception suggests a session failure (e.g., a redirect to a login page or a 401/403 error), it will raise the new `SessionExpiredException`.

**`workflow.py`**
```python
from datetime import date
from config import METADATA_FILE, DATA_FILE
from data_manager import load_json_file, save_json_file
from scraping_logic import get_authenticated_session
from scrape_search import get_evaluation_report_links
from scrape_link import scrape_evaluation_data
from period_logic import find_oldest_year_from_keys, is_course_up_to_date, get_period_from_instance_key
from period_logic import get_year_from_period_string
from period_logic import get_current_period, is_grace_period_over
from exceptions import SessionExpiredException
import requests

def run_scraper_workflow(course_code: str, session: requests.Session):
    """
    Orchestrates the scraping process for a course, with frequent saving
    and robust handling of paginated results.
    """
    # ... (initialization logic remains the same)

    try:
        # ... (rest of the workflow logic)
        # All calls to get_evaluation_report_links and scrape_evaluation_data
        # will now be wrapped in this try...except block.
    except requests.exceptions.RequestException as e:
        # Here we can add more sophisticated checks if needed, e.g.,
        # checking the status code or response URL to confirm it's a login redirect.
        print(f"RequestException caught in workflow: {e}. Assuming session expired.")
        raise SessionExpiredException from e

    # ... (final check logic remains the same)
```

## 4. Scraping Functions (`scrape_link.py`, `scrape_search.py`) Logic

The scraping functions will be simplified to no longer catch `requests.exceptions.RequestException`. They will let these exceptions propagate up to `workflow.py`.

**Changes:**

*   **Remove `try...except`:** The `try...except requests.exceptions.RequestException` blocks will be removed from `scrape_evaluation_data` in `scrape_link.py` and `get_evaluation_report_links` in `scrape_search.py`.

**`scrape_link.py`**
```python
def scrape_evaluation_data(report_url: str, session: requests.Session) -> dict:
    """
    ...
    """
    # The try...except requests.exceptions.RequestException block is removed.
    # The function will now let RequestException propagate.
    response = session.get(report_url, timeout=10)
    response.raise_for_status()
    # ... (rest of the function)
```

**`scrape_search.py`**
```python
def get_evaluation_report_links(...) -> dict:
    """
    ...
    """
    # The try...except requests.exceptions.RequestException block is removed.
    # The function will now let RequestException propagate.
    course_page_response = session.get(course_url, timeout=10)
    course_page_response.raise_for_status()
    # ... (rest of the function)
```

## 5. Function Signature Changes

The following function signatures will need to be changed:

*   **`workflow.py`**:
    *   `run_scraper_workflow(course_code: str)` -> `run_scraper_workflow(course_code: str, session: requests.Session)`

This change propagates from `main.py`, which will now be responsible for creating and managing the session.