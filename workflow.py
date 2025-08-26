from workflow_helpers import scrape_course_data_core, check_course_status
from scraping_logic import get_authenticated_session

def run_scraper_workflow(course_code: str):
    """
    Orchestrates the scraping process for a course, with frequent saving
    and robust handling of paginated results.
    """
    print(f"--- Starting workflow for course: {course_code} ---")

    # Check if course is up-to-date first
    data, course_metadata = check_course_status(course_code)
    if data is None and course_metadata is None:
        # Course is up-to-date, skip workflow
        return

    # Get an authenticated session for all scraping
    try:
        session = get_authenticated_session()
    except Exception as e:
        print(f"Could not get initial authenticated session: {e}. Aborting.")
        return

    # Use the shared core scraping function
    result = scrape_course_data_core(course_code, session)
    
    if not result['success']:
        print(f"--- CRITICAL ERROR in workflow for {course_code}: {result['error']} ---")
    else:
        print(f"--- Workflow for {course_code} complete. ---")