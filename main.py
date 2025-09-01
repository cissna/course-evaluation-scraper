from workflow import run_scraper_workflow
from scraping_logic import get_authenticated_session
from exceptions import SessionExpiredException
from requests.exceptions import RequestException
import time
# Removed department/course code imports; now using all codes from 'jhu_as_en_courses.txt'


if __name__ == "__main__":
    # Read all course codes from 'jhu_as_en_courses.txt'
    with open("jhu_as_en_courses.txt") as f:
        course_codes = [line.strip() for line in f if line.strip()]

    try:
        session = get_authenticated_session()
    except RequestException as e:
        print(f"Could not get initial authenticated session: {e}. Aborting.")
        exit()

    start = time.time()
    batch_start = start
    for idx, target_course in enumerate(course_codes, start=1):
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
        if idx % 250 == 0:
            batch_elapsed = time.time() - batch_start
            print("\n" + "*"*60)
            print(f"*** Processed {idx} courses. Elapsed Time (this batch): {batch_elapsed:.2f} seconds ***")
            print(f"{'*'*60}\n")
            print("\n" + "#"*60)
            print("# Pausing for 1 minute. You may safely keyboard interrupt now if desired.")
            print("#" + " "*58 + "#")
            print("#" * 60 + "\n")
            time.sleep(60)
            print("\n" + "#"*60)
            print("# SLEEP COMPLETE. Continuing processing.")
            print("#" + " "*58 + "#")
            print("#" * 60 + "\n")
            batch_start = time.time()
    total_elapsed = time.time() - start
    print("--- All course codes from jhu_as_en_courses.txt have been processed. ---")
    print(f"Total elapsed time: {total_elapsed:.2f} seconds")
