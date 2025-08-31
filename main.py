from workflow import run_scraper_workflow
from scraping_logic import get_authenticated_session
from exceptions import SessionExpiredException
import requests
from config import TARGET_DEPARTMENT, COURSE_NUMBER_START, COURSE_NUMBER_END

if __name__ == "__main__":
    # Get initial authenticated session
    try:
        session = get_authenticated_session()
    except requests.exceptions.RequestException as e:
        print(f"Could not get initial authenticated session: {e}. Aborting.")
        exit()

    for course_number in range(COURSE_NUMBER_START, COURSE_NUMBER_END + 1):
        # Remove the debug filter - process all courses in the range
        formatted_course_number = f"{course_number:03d}"
        target_course = f"{TARGET_DEPARTMENT}.{formatted_course_number}"
        
        print(f"--- Processing course: {target_course} ---")
        
        retries = 1 # Allow one retry
        while retries >= 0:
            try:
                # Pass the session to the workflow function
                run_scraper_workflow(target_course, session)
                print(f"--- Finished processing: {target_course} ---\n")
                break # Success, exit retry loop
            except SessionExpiredException:
                print(f"Session expired while processing {target_course}. Retrying...")
                try:
                    session = get_authenticated_session()
                except requests.exceptions.RequestException as e:
                    print(f"Could not get new authenticated session: {e}. Aborting retries for this course.")
                    break
                retries -= 1
            except Exception as e:
                print(f"--- CRITICAL ERROR in workflow for {target_course}: {e} ---")
                print("--- Moving to next course. ---\n")
                break # Exit retry loop on other errors

    print("--- All department courses have been processed. ---")