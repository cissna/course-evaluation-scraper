from workflow import run_scraper_workflow
from scraping_logic import get_authenticated_session
from exceptions import SessionExpiredException
from requests.exceptions import RequestException
import time
# Department/course code list to process
COURSE_CODES = [
    "AS.001","AS.004","AS.010","AS.020","AS.030","AS.040","AS.050","AS.060","AS.061","AS.070","AS.080",
    "AS.100","AS.110","AS.130","AS.134","AS.136","AS.140","AS.145","AS.150","AS.171","AS.173","AS.180",
    "AS.190","AS.191","AS.192","AS.194","AS.196","AS.197","AS.200","AS.210","AS.217","AS.220","AS.225",
    "AS.230","AS.250","AS.270","AS.271","AS.280","AS.290","AS.300","AS.305","AS.310","AS.360","AS.361",
    "AS.362","AS.363","AS.371","AS.374","AS.376","AS.389","AS.410","AS.420","AS.425","AS.430","AS.440",
    "AS.450","AS.455","AS.460","AS.465","AS.470","AS.472","AS.475","AS.480","AS.485","AS.490","AS.491",
    "AS.492","AS.999",
    "EN.500","EN.501","EN.510","EN.515","EN.520","EN.525","EN.530","EN.535","EN.540","EN.545","EN.553",
    "EN.555","EN.560","EN.565","EN.570","EN.575","EN.580","EN.585","EN.595","EN.601","EN.605","EN.615",
    "EN.620","EN.625","EN.635","EN.645","EN.650","EN.655","EN.660","EN.661","EN.662","EN.663","EN.665",
    "EN.670","EN.675","EN.685","EN.695","EN.700","EN.705"
]

if __name__ == "__main__":
    # Get initial authenticated session
    try:
        session = get_authenticated_session()
    except RequestException as e:
        print(f"Could not get initial authenticated session: {e}. Aborting.")
        exit()

    for target_course in COURSE_CODES:
        print(f"\n{'='*60}")
        print(f"=== Processing course: {target_course} ===")
        print(f"{'='*60}\n")

        start = time.time()

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

        elapsed = time.time() - start
        print(f"\n{'*'*60}")
        print(f"*** Finished: {target_course}    Elapsed Time: {elapsed:.2f} seconds ***")
        print(f"{'*'*60}\n")

        # Big, visually clear pre-sleep message
        print("\n" + "#"*60)
        print(f"# Preparing to SLEEP 5 minutes after {target_course}")
        print("# You may safely keyboard interrupt now if desired.")
        print("#" + " "*50 + "#")
        print("#" * 60 + "\n")

        time.sleep(300) # 5 minutes

        # Big, visually clear post-sleep message
        print("\n" + "#"*60)
        print("# SLEEP COMPLETE. Starting next course.")
        print("#" + " "*50 + "#")
        print("#" * 60 + "\n")

    print("--- All department courses have been processed. ---")