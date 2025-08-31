from workflow import run_scraper_workflow
from scraping_logic import get_authenticated_session
from exceptions import SessionExpiredException
from requests.exceptions import RequestException
import time
from data_sources import DEPARTMENT_CODES, COURSE_CODES


SCRAPE_BY_DEPARTMENT = False

if __name__ == "__main__":
    # Get initial authenticated session
    try:
        session = get_authenticated_session()
    except RequestException as e:
        print(f"Could not get initial authenticated session: {e}. Aborting.")
        exit()

    if SCRAPE_BY_DEPARTMENT:
        for dept_prefix in DEPARTMENT_CODES:
            if DEPARTMENT_CODES.index(dept_prefix) <= DEPARTMENT_CODES.index('AS.173'):
                continue
            start = time.time()  # start timer for entire department prefix

            for course_number in range(100, 500):
                course_number_str = f"{course_number:03d}"
                target_course = f"{dept_prefix}.{course_number_str}"


                retries = 1 # Allow one retry
                while retries >= 0:
                    try:
                        run_scraper_workflow(target_course, session)
                        print(f"--- Finished processing: {target_course} ---\n")
                        break
                    except SessionExpiredException:
                        print(f"Session expired while processing {target_course}. Retrying...")
                        try:
                            session = get_authenticated_session()
                        except RequestException as e:
                            print(f"Could not get new authenticated session: {e}. Aborting retries for this course.")
                            break
                        retries -= 1
                    except Exception as e:
                        print(f"--- CRITICAL ERROR in workflow for {target_course}: {e} ---")
                        print("--- Moving to next course. ---\n")
                        break

            elapsed = time.time() - start  # elapsed for full dept batch
            print(f"\n{'*'*60}")
            print(f"*** Finished all courses for {dept_prefix}    Elapsed Time: {elapsed:.2f} seconds ***")
            print(f"{'*'*60}\n")

            print("\n" + "#"*60)
            print(f"# Preparing to SLEEP 5 minutes after finishing dept: {dept_prefix}")
            print("# You may safely keyboard interrupt now if desired.")
            print("#" + " "*58 + "#")
            print("#" * 60 + "\n")

            time.sleep(300) # 5 minutes

            print("\n" + "#"*60)
            print("# SLEEP COMPLETE. Starting next department prefix.")
            print("#" + " "*58 + "#")
            print("#" * 60 + "\n")

        print("--- All department courses have been processed. ---")
    else:
        for target_course in COURSE_CODES:

            retries = 1  # Allow one retry
            while retries >= 0:
                try:
                    run_scraper_workflow(target_course, session)
                    print(f"--- Finished processing: {target_course} ---\n")
                    break
                except SessionExpiredException:
                    print(f"Session expired while processing {target_course}. Retrying...")
                    try:
                        session = get_authenticated_session()
                    except RequestException as e:
                        print(f"Could not get new authenticated session: {e}. Aborting retries for this course.")
                        break
                    retries -= 1
                except Exception as e:
                    print(f"--- CRITICAL ERROR in workflow for {target_course}: {e} ---")
                    print("--- Moving to next course. ---\n")
                    break
        print("--- All explicit course codes have been processed. ---")