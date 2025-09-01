import json
import os
import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from course_grouping_service import CourseGroupingService
from urllib.parse import urlencode, urljoin
from dateutil.relativedelta import relativedelta
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from workflow_helpers import scrape_course_data_core

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

# --- Data Management (from data_manager.py) ---

def load_json_file(filepath: str) -> dict:
    """Safely loads a JSON file, creating it if it doesn't exist."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json_file(filepath: str, data: dict):
    """Saves a dictionary to a JSON file with pretty printing."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# --- Period Logic (from period_logic.py) ---

def find_oldest_year_from_keys(keys: list) -> int:
    oldest_year = date.today().year
    found_year = False
    year_re = re.compile(r'\.(?:FA|SP|SU|IN)(\d{2})$')
    for key in keys:
        match = year_re.search(key)
        if match:
            year_short = int(match.group(1))
            year = 2000 + year_short if year_short < 70 else 1900 + year_short
            if year < oldest_year:
                oldest_year = year
                found_year = True
    return oldest_year if found_year else 2010

def get_period_from_instance_key(instance_key: str) -> str:
    match = re.search(r'\.((?:FA|SP|SU|IN)\d{2})$', instance_key)
    return match.group(1) if match else None

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

def get_evaluation_report_links(session: requests.Session, course_code: str, year: str = None) -> dict:
    query_params = {'Course': course_code}
    if year:
        query_params['Year'] = year
    course_path = f"Report/Public/Results?{urlencode(query_params)}"
    course_url = urljoin(BASE_REPORT_URL, course_path)
    
    report_links = {}
    course_page_response = session.get(course_url, timeout=10)
    course_page_response.raise_for_status()
    soup = BeautifulSoup(course_page_response.text, 'html.parser')
    links_found = soup.find_all('a', class_='sr-view-report')

    for link in links_found:
        data_id0, data_id1, data_id2, data_id3 = link.get('data-id0'), link.get('data-id1'), link.get('data-id2'), link.get('data-id3')
        if all([data_id0, data_id1, data_id2, data_id3]):
            id_string = f"{data_id0},{data_id1},{data_id2},{data_id3}"
            final_url = f"{INDIVIDUAL_REPORT_BASE_URL}?id={id_string}"
            parent_row = link.find_parent('div', class_='row')
            if parent_row:
                course_code_p = parent_row.find('p', class_='sr-dataitem-info-code')
                if course_code_p and course_code_p.text:
                    report_links[course_code_p.text.strip()] = final_url
    return report_links

def scrape_evaluation_data(report_url: str, session: requests.Session) -> dict:
    scraped_data = {}
    response = session.get(report_url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    course_element = soup.find(lambda tag: tag.name == 'h3' and 'Course:' in tag.text)
    if course_element and course_element.find_next_sibling('span'):
        full_course_name = course_element.find_next_sibling('span').text.strip()
        # Extract only the part after " : " if present
        if ' : ' in full_course_name:
            scraped_data['course_name'] = full_course_name.split(' : ', 1)[1]
        else:
            scraped_data['course_name'] = full_course_name

    instructor_element = soup.find(lambda tag: tag.name == 'h3' and 'Instructor:' in tag.text)
    if instructor_element and instructor_element.find_next_sibling('span'):
        scraped_data['instructor_name'] = instructor_element.find_next_sibling('span').text.strip()

    report_data_element = soup.find('input', id='hdnReportData')
    if report_data_element:
        report_data = json.loads(report_data_element['value'])
        question_mapping = {
            "The overall quality of this course is:": "overall_quality_frequency",
            "The instructor's teaching effectiveness is:": "instructor_effectiveness_frequency",
            "The intellectual challenge of this course is:": "intellectual_challenge_frequency",
            "The teaching assistant for this course is:": "ta_frequency",
            "Feedback on my work for this course is useful:": "feedback_frequency",
            "Compared to other Hopkins courses at this level, the workload for this course is:": "workload_frequency",
            "Please enter the name of the TA you evaluated in question 4:": "ta_names"
        }
        for question in report_data:
            question_text = question.get("QuestionText", "").strip()
            if question_text in question_mapping:
                key = question_mapping[question_text]
                if key == "ta_names":
                    ta_names_raw = question.get("AnswerText", "")
                    scraped_data['ta_names'] = list(set([name.strip() for name in ta_names_raw.split('||')])) if ta_names_raw else ["N/A"]
                else:
                    scraped_data[key] = {opt["OptionText"]: opt["Frequency"] for opt in question.get("Options", [])}
    
    if 'ta_names' not in scraped_data:
        scraped_data['ta_names'] = ["N/A"]
    return scraped_data

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
        "last_scrape_date": last_scrape_during_grace,
        "future_course_periods": course_metadata.get('future_course_periods')
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