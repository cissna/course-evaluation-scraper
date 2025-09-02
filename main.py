from workflow import run_scraper_workflow
from scraping_logic import get_authenticated_session
from exceptions import SessionExpiredException
from requests.exceptions import RequestException
import time
# Removed department/course code imports; now using all codes from 'jhu_as_en_courses.txt'


if __name__ == "__main__":
    # Read all course codes from 'jhu_as_en_courses.txt'
    with open("jhu_as_en_courses.txt") as f:
        course_codes = []
        start_adding = False
        for line in f:
            stripped_line = line.strip()
            if stripped_line == 'AS.191.371':
                start_adding = True
            if start_adding and stripped_line:
                course_codes.append(stripped_line)

    try:
        session = get_authenticated_session()
    except RequestException as e:
        print(f"Could not get initial authenticated session: {e}. Aborting.")
        exit()

    start = time.time()
    batch_start = start
    scraped_count = 0
    attempted_count = 0
    for target_course in course_codes:
        attempted_count += 1
        retries = 1  # Allow one retry
        scraped = False
        while retries >= 0:
            try:
                result = run_scraper_workflow(target_course, session)
                if result:
                    scraped = True
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
        if scraped:
            scraped_count += 1

        # Log progress every 10% of the 250 scrapes
        if scraped_count > 0 and scraped_count % 25 == 0:
            current_elapsed = time.time() - batch_start
            percentage = (scraped_count % 250) / 250 * 100
            if percentage == 0 and scraped_count > 0: # For the 250th scrape, it should be 100%
                percentage = 100
            
            if percentage == 50:
                print(f"\n--- Halfway through the current batch ({scraped_count} scrapes). Elapsed: {current_elapsed:.2f} seconds ---")
            elif percentage == 100:
                # This will be handled by the 250-scrape pause logic below
                pass
            else:
                print(f"\n--- {percentage:.0f}% through current batch ({scraped_count % 250} scrapes). Elapsed: {current_elapsed:.2f} seconds ---")


        if scraped_count > 0 and scraped_count % 250 == 0:
            batch_elapsed = time.time() - batch_start
            print("\n" + "*"*60)
            print(f"*** Processed {scraped_count} scrapes + an additional {attempted_count - scraped_count} attempted scrapes. Elapsed Time (this batch): {batch_elapsed:.2f} seconds ***")
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
