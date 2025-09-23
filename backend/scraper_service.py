import os
import re
import requests
from datetime import date
from course_grouping_service import CourseGroupingService
from dateutil.relativedelta import relativedelta
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from workflow_helpers import scrape_course_data_core
from data_manager import load_json_file, save_json_file

# --- Constants (Adapted from config.py) ---

# File Paths (anchored to the project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
METADATA_FILE = os.path.join(PROJECT_ROOT, 'metadata.json')
DATA_FILE = os.path.join(PROJECT_ROOT, 'data.json')

# Scraping URLs
AUTH_URL = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
BASE_REPORT_URL = 'https://asen-jhu.evaluationkit.com/'
INDIVIDUAL_REPORT_BASE_URL = 'https://asen-jhu.evaluationkit.com/Reports/StudentReport.aspx'

# Period Logic Constants

# --- Course Grouping Service Instance ---
grouping_service = CourseGroupingService()
PERIOD_RELEASE_DATES = {
    'IN': (1, 16), 'SP': (5, 15), 'SU': (8, 15), 'FA': (12, 15)
}
PERIOD_GRACE_MONTHS = {
    'IN': 1, 'SP': 1, 'SU': 2, 'FA': 1
}

# --- Custom Exceptions (from exceptions.py) ---

class SessionExpiredException(Exception):
    """Raised when the session is believed to have expired."""
    pass


def get_year_from_period_string(period_string: str) -> int:
    if not period_string or len(period_string) < 4:
        return None
    year_short = int(period_string[-2:])
    return 2000 + year_short

def get_current_period() -> str:
    today = date.today()
    year_short = today.year % 100
    if today.month > PERIOD_RELEASE_DATES['FA'][0] or \
       (today.month == PERIOD_RELEASE_DATES['FA'][0] and today.day >= PERIOD_RELEASE_DATES['FA'][1]):
        return f"FA{year_short}"
    elif today.month > PERIOD_RELEASE_DATES['SU'][0] or \
         (today.month == PERIOD_RELEASE_DATES['SU'][0] and today.day >= PERIOD_RELEASE_DATES['SU'][1]):
        return f"SU{year_short}"
    elif today.month > PERIOD_RELEASE_DATES['SP'][0] or \
         (today.month == PERIOD_RELEASE_DATES['SP'][0] and today.day >= PERIOD_RELEASE_DATES['SP'][1]):
        return f"SP{year_short}"
    elif today.month > PERIOD_RELEASE_DATES['IN'][0] or \
         (today.month == PERIOD_RELEASE_DATES['IN'][0] and today.day >= PERIOD_RELEASE_DATES['IN'][1]):
        return f"IN{year_short}"
    else:
        return f"FA{year_short - 1}"

def is_course_up_to_date(last_period_gathered: str) -> bool:
    current_period = get_current_period()
    return last_period_gathered == current_period

def is_grace_period_over(period: str) -> bool:
    today = date.today()
    period_prefix = period[:2]
    year_short = int(period[2:])
    year = 2000 + year_short
    release_month, release_day = PERIOD_RELEASE_DATES[period_prefix]
    release_date = date(year, release_month, release_day)
    grace_months = PERIOD_GRACE_MONTHS[period_prefix]
    grace_period_end = release_date + relativedelta(months=grace_months)
    return today > grace_period_end

# --- Scraping Logic (from scraping_logic.py, scrape_search.py, scrape_link.py) ---

def get_authenticated_session() -> requests.Session:
    session = requests.Session()
    auth_response = session.get(AUTH_URL, timeout=10)
    auth_response.raise_for_status()
    print("Authentication session created successfully.")
    return session

# --- Main Workflow (Adapted from workflow.py) ---

def get_course_data_and_update_cache(course_code: str) -> dict:
    """
    Main service function to get course data.
    Checks cache, scrapes if necessary, and returns all relevant data.
    """
    metadata = load_json_file(METADATA_FILE)
    data = load_json_file(DATA_FILE)

    # Check if the last scraping attempt failed for this course
    if course_code in metadata and metadata[course_code].get('last_period_failed', False):
        print(f"Course {course_code} has last_period_failed set to true. Returning error.")
        return {"error": f"The last attempt to gather data for course {course_code} failed. Please try again later or contact support if this persists."}

    # Check if course is up-to-date
    if course_code in metadata and is_course_up_to_date(metadata[course_code].get('last_period_gathered')):
        print(f"Course {course_code} is up-to-date. Returning cached data.")
        relevant_keys = metadata[course_code].get('relevant_periods', [])
        return {key: data[key] for key in relevant_keys if key in data}

    # If not up-to-date, use the shared core scraping function
    print(f"--- Starting scraper for course: {course_code} ---")
    
    try:
        session = get_authenticated_session()
    except requests.exceptions.RequestException as e:
        print(f"Could not get authenticated session: {e}. Aborting.")
        # Update metadata to mark failure
        if course_code not in metadata:
            metadata[course_code] = {"last_period_gathered": None, "last_period_failed": False, "relevant_periods": [], "last_scrape_during_grace_period": None}
        metadata[course_code]['last_period_failed'] = True
        save_json_file(METADATA_FILE, metadata)
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
    metadata = load_json_file(METADATA_FILE)
    
    if course_code not in metadata:
        return {"needs_warning": False}
    
    course_metadata = metadata[course_code]
    last_scrape_during_grace = course_metadata.get('last_scrape_during_grace_period')
    
    if last_scrape_during_grace is None:
        return {"needs_warning": False}
    
    # Course has grace period flag, get current period info
    current_period = get_current_period()
    
    return {
        "needs_warning": True,
        "current_period": current_period,
        "last_scrape_date": last_scrape_during_grace
    }

def find_courses_by_name(search_query: str) -> list:
    """
    Finds course codes by searching for a query in the course names.
    """
    data = load_json_file(DATA_FILE)
    if not data:
        return []

    matching_codes = set()
    search_query_lower = search_query.lower()

    for instance_key, course_data in data.items():
        course_name = course_data.get('course_name', '')
        if search_query_lower in course_name.lower():
            # Extract the base course code (e.g., "AS.123.456") from the instance key
            match = re.match(r'([A-Z]{2}\.\d{3}\.\d{3})', instance_key)
            if match:
                matching_codes.add(match.group(1))
    
    return sorted(list(matching_codes))