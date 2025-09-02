from workflow_helpers import scrape_course_data_core, check_course_status
from scraping_logic import get_authenticated_session
from data_manager import load_json_file, save_json_file
from config import METADATA_FILE
import requests

def run_scraper_workflow(course_code: str, session: requests.Session = None):
    """
    Orchestrates the scraping process for a course, with frequent saving
    and robust handling of paginated results.
    This function behaves like the web application's normal scraping (no recheck).
    """
    print(f"--- Starting workflow for course: {course_code} ---")

    # Check if course is up-to-date first
    data, course_metadata = check_course_status(course_code)
    if data is None and course_metadata is None:
        # Course is up-to-date, skip workflow
        return False

    # Use provided session or get a new one
    if session is None:
        try:
            session = get_authenticated_session()
        except requests.exceptions.RequestException as e:
            print(f"Could not get authenticated session: {e}. Aborting.")
            # Update metadata to mark failure
            metadata = load_json_file(METADATA_FILE)
            if course_code not in metadata:
                metadata[course_code] = {"last_period_gathered": None, "last_period_failed": False, "relevant_periods": [], "last_scrape_during_grace_period": None}
            metadata[course_code]['last_period_failed'] = True
            save_json_file(METADATA_FILE, metadata)
            return False

    # Use the shared core scraping function with grace period logic (skip_grace_period_logic=False)
    # This means it will behave like normal web app scraping, not like force recheck
    result = scrape_course_data_core(course_code, session, skip_grace_period_logic=False)
    
    if not result['success']:
        print(f"--- CRITICAL ERROR in workflow for {course_code}: {result['error']} ---")
    else:
        print(f"--- Workflow for {course_code} complete. ---")
        return True