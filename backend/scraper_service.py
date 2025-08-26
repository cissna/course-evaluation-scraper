import json
import os
import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urljoin
from dateutil.relativedelta import relativedelta

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
PERIOD_RELEASE_DATES = {
    'IN': (1, 15), 'SP': (5, 15), 'SU': (8, 15), 'FA': (12, 15)
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
        scraped_data['course_name'] = course_element.find_next_sibling('span').text.strip()

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

    # If not up-to-date, run the scraper workflow
    print(f"--- Starting scraper for course: {course_code} ---")
    
    if course_code not in metadata:
        metadata[course_code] = {
            "last_period_gathered": None,
            "last_period_failed": False, "relevant_periods": []
        }
        save_json_file(METADATA_FILE, metadata)
    
    course_metadata = metadata[course_code]

    try:
        session = get_authenticated_session()
    except requests.exceptions.RequestException as e:
        print(f"Could not get authenticated session: {e}. Aborting.")
        course_metadata['last_period_failed'] = True
        save_json_file(METADATA_FILE, metadata)
        return {"error": "Failed to authenticate with scraping service."}

    new_data_found = False
    
    # 4. Get initial dictionary of report links to check for pagination
    print(f"Fetching initial report links for {course_code}...")
    initial_links = get_evaluation_report_links(session=session, course_code=course_code)

    # 5. Decide workflow based on number of links
    if len(initial_links) >= 20:
        print("Pagination detected. Switching to year-by-year scraping.")
        last_period = course_metadata.get('last_period_gathered')
        start_year = get_year_from_period_string(last_period) if last_period else find_oldest_year_from_keys(initial_links.keys())
        end_year = date.today().year

        for year in range(start_year, end_year + 2):
            print(f"Processing year: {year}")
            try:
                yearly_links_dict = get_evaluation_report_links(session=session, course_code=course_code, year=str(year))
                
                if len(yearly_links_dict) >= 20:
                    print(f"CRITICAL: Found 20+ links for year {year}. Halting.")
                    course_metadata['last_period_failed'] = True
                    save_json_file(METADATA_FILE, metadata)
                    return {"error": f"Too many results for year {year}, please contact admin."}

                if not yearly_links_dict:
                    continue

                for instance_key, link_url in yearly_links_dict.items():
                    if instance_key in data:
                        continue
                    
                    scraped_data = scrape_evaluation_data(link_url, session)
                    if scraped_data:
                        data[instance_key] = scraped_data
                        new_data_found = True
                        if instance_key not in course_metadata['relevant_periods']:
                            course_metadata['relevant_periods'].append(instance_key)
                        
                        period = get_period_from_instance_key(instance_key)
                        if period:
                            course_metadata['last_period_gathered'] = period
                        
                        course_metadata['last_period_failed'] = False
                    else:
                        course_metadata['last_period_failed'] = True
                        break  # Stop processing this year if a single scrape fails
                
                save_json_file(DATA_FILE, data)
                save_json_file(METADATA_FILE, metadata)
                if course_metadata['last_period_failed']:
                    break # Stop processing subsequent years if this year failed

            except requests.exceptions.RequestException as e:
                print(f"Failed to scrape year {year}: {e}")
                course_metadata['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                break
    else:
        print(f"No pagination detected ({len(initial_links)} links). Scraping all.")
        for instance_key, link_url in initial_links.items():
            if instance_key in data:
                continue
            
            scraped_data = scrape_evaluation_data(link_url, session)
            if scraped_data:
                data[instance_key] = scraped_data
                new_data_found = True
                if instance_key not in course_metadata['relevant_periods']:
                    course_metadata['relevant_periods'].append(instance_key)
                
                period = get_period_from_instance_key(instance_key)
                if period:
                    course_metadata['last_period_gathered'] = period
                
                course_metadata['last_period_failed'] = False
                save_json_file(DATA_FILE, data)
                save_json_file(METADATA_FILE, metadata)
            else:
                course_metadata['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                break # Stop if one fails

    # Final grace period check
    if not new_data_found and not course_metadata['last_period_failed']:
        current_period = get_current_period()
        if is_grace_period_over(current_period):
            print(f"Grace period for {current_period} is over. Marking as up-to-date.")
            course_metadata['last_period_gathered'] = current_period
            save_json_file(METADATA_FILE, metadata)

    print(f"--- Workflow for {course_code} complete. ---")
    relevant_keys = metadata[course_code].get('relevant_periods', [])
    return {key: data[key] for key in relevant_keys if key in data}

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