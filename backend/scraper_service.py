import requests
from datetime import date
from .course_grouping_service import CourseGroupingService
from dateutil.relativedelta import relativedelta
from .workflow_helpers import scrape_course_data_core
from .db_utils import (
    get_course_metadata,
    get_course_data_by_keys,
    update_course_metadata,
    find_courses_by_name_db
)
from .scraping_logic import get_authenticated_session
from .config import PERIOD_RELEASE_DATES, PERIOD_GRACE_MONTHS
from .period_logic import (
    get_year_from_period_string,
    get_current_period,
    is_course_up_to_date,
    is_grace_period_over
)

# --- Course Grouping Service Instance ---
grouping_service = CourseGroupingService()

# --- Custom Exceptions (from exceptions.py) ---

class SessionExpiredException(Exception):
    """Raised when the session is believed to have expired."""
    pass




# --- Scraping Logic (from scraping_logic.py, scrape_search.py, scrape_link.py) ---

# get_authenticated_session imported from scraping_logic.py

# --- Main Workflow (Adapted from workflow.py) ---

def get_course_data_and_update_cache(course_code: str) -> dict:
    """
    Main service function to get course data.
    Checks database, scrapes if necessary, and returns all relevant data.
    """
    metadata = get_course_metadata(course_code)

    # Check if the last scraping attempt failed for this course
    if metadata and metadata.get('last_period_failed', False):
        print(f"Course {course_code} has last_period_failed set to true. Returning error.")
        return {"error": f"The last attempt to gather data for course {course_code} failed. Please try again later or contact support if this persists."}

    # Check if course is up-to-date
    if metadata and is_course_up_to_date(metadata.get('last_period_gathered'), metadata):
        print(f"Course {course_code} is up-to-date. Returning cached data.")
        relevant_keys = metadata.get('relevant_periods', [])
        return get_course_data_by_keys(relevant_keys)

    # If not up-to-date, use the shared core scraping function
    print(f"--- Starting scraper for course: {course_code} ---")
    
    try:
        session = get_authenticated_session()
    except requests.exceptions.RequestException as e:
        print(f"Could not get authenticated session: {e}. Aborting.")
        # Update metadata to mark failure
        if not metadata:
            metadata = {"last_period_gathered": None, "last_period_failed": False, "relevant_periods": [], "last_scrape_during_grace_period": None}
        metadata['last_period_failed'] = True
        update_course_metadata(course_code, metadata)
        return {"error": "Failed to authenticate with scraping service."}

    # Use the shared core scraping function (skip grace period logic for web interface)
    result = scrape_course_data_core(course_code, session, skip_grace_period_logic=False)
    
    if not result['success']:
        print(f"--- Scraping failed for {course_code}: {result['error']} ---")
        return {"error": result['error']}
    
    print(f"--- Workflow for {course_code} complete. ---")
    return result['data']

def force_recheck_course(course_code: str) -> dict:
    """
    Force recheck a course by ignoring grace period logic.
    This is used when the user explicitly requests an update.
    """
    print(f"--- Force rechecking course: {course_code} ---")
    
    try:
        session = get_authenticated_session()
    except requests.exceptions.RequestException as e:
        print(f"Could not get authenticated session: {e}. Aborting.")
        return {"error": "Failed to authenticate with scraping service."}

    # Use the shared core scraping function with grace period logic enabled
    result = scrape_course_data_core(course_code, session, skip_grace_period_logic=True)
    
    if not result['success']:
        print(f"--- Force recheck failed for {course_code}: {result['error']} ---")
        return {"error": result['error']}
    
    print(f"--- Force recheck for {course_code} complete. ---")
    return result['data']

def get_course_grace_status(course_code: str) -> dict:
    """
    Check if a course needs a grace period warning.
    Returns info about grace period status for frontend.
    """
    metadata = get_course_metadata(course_code)
    
    if not metadata:
        return {"needs_warning": False}
    
    last_scrape_during_grace = metadata.get('last_scrape_during_grace_period')
    
    if last_scrape_during_grace is None:
        return {"needs_warning": False}
    
    current_period = get_current_period()
    
    return {
        "needs_warning": True,
        "current_period": current_period,
        "last_scrape_date": last_scrape_during_grace.isoformat() if last_scrape_during_grace else None
    }

def find_courses_by_name(search_query: str) -> list:
    """
    Finds course codes by searching for a query in the course names in the database.
    """
    return find_courses_by_name_db(search_query)