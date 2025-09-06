from data_manager import load_json_file, save_json_file
from period_logic import find_oldest_year_from_keys, find_latest_year_from_keys
from period_logic import get_year_from_period_string, get_current_period, is_grace_period_over, get_period_from_instance_key, is_course_up_to_date
from config import METADATA_FILE, DATA_FILE
from scraping_logic import get_authenticated_session
from scrape_search import get_evaluation_report_links
from scrape_link import scrape_evaluation_data
import requests
from datetime import date

# Helper function to sort links chronologically before scraping

def scrape_course_data_core(course_code: str, session: requests.Session = None, skip_grace_period_logic: bool = True) -> dict:
    """
    Core scraping function that handles the actual data collection logic.
    """
    # --- SETUP PHASE ---
    metadata = load_json_file(METADATA_FILE)
    data = load_json_file(DATA_FILE)

    if course_code not in metadata:
        metadata[course_code] = {
            "last_period_gathered": None, "last_period_failed": False,
            "relevant_periods": [], "last_scrape_during_grace_period": None
        }
    course_metadata = metadata[course_code]

    if session is None:
        try:
            session = get_authenticated_session()
        except requests.exceptions.RequestException as e:
            course_metadata['last_period_failed'] = True
            save_json_file(METADATA_FILE, metadata)
            return {'success': False, 'error': f"Could not get authenticated session: {e}", 'metadata': course_metadata, 'data': {}, 'new_data_found': False}

    # --- PHASE 1: LINK COLLECTION ---
    links_to_process = {}
    
    try:
        print(f"Fetching initial report links for {course_code}...")
        initial_links, has_more_initial = get_evaluation_report_links(session=session, course_code=course_code)
    except Exception as e:
        course_metadata['last_period_failed'] = True
        save_json_file(METADATA_FILE, metadata)
        return {'success': False, 'error': f"Failed to get initial report links: {e}", 'metadata': course_metadata, 'data': {}, 'new_data_found': False}

    if not initial_links:
        print("No report links found on the main page.")

    # Main logic branch: Decide scraping strategy based on "Show more results" button
    if not has_more_initial:
        # ✅ Simple Case: No "Show more results" button. Scrape what we found.
        print("No pagination detected (no 'Show more results' button). Processing initial links.")
        links_to_process = initial_links

    # --- PHASE 2: UNIFIED SCRAPING ---
    print(f"\nFound a total of {len(links_to_process)} unique reports to potentially process.")
    batch_failed = False
    new_data_found = False
    new_data_in_batch = {}
    new_relevant_periods = []
    failed_scrapes = {}

    # Sort links chronologically to process older data first
    sorted_links = links_to_process.items()

    for instance_key, link_url in sorted_links:
        if instance_key in data:
            continue # Skip data we already have

        # print(f"Scraping new report: {instance_key}")  # prints every specific course code, kinda a lot...
        scraped_data = scrape_evaluation_data(link_url, session)

        # Check for explicit scrape failure (e.g., missing overall_quality_frequency)
        if scraped_data and scraped_data.get("scrape_failed", False):
            # Collect all failed scrapes separately for failed.json
            failed_scrapes[instance_key] = scraped_data
            continue  # Skip normal handling; don't include in metadata or data.json

        if scraped_data:
            new_data_in_batch[instance_key] = scraped_data
            if instance_key not in course_metadata['relevant_periods']:
                new_relevant_periods.append(instance_key)
        else:
            print(f"Failed to scrape {instance_key}. Halting all scraping for {course_code} to prevent incomplete data.")
            course_metadata['last_period_failed'] = True
            batch_failed = True
            break # Exit the scraping loop immediately

    # --- PHASE 3: SAVING & FINALIZATION ---

    # Handle saving failed scrapes to failed.json if any detected
    if failed_scrapes:
        failed_data = load_json_file("failed.json")
        failed_data.update(failed_scrapes)
        save_json_file("failed.json", failed_data)

    if not batch_failed and new_data_in_batch:
        print("Batch successful. Saving all new data...")
        data.update(new_data_in_batch)
        course_metadata['relevant_periods'].extend(new_relevant_periods)
        course_metadata['last_period_failed'] = False
        save_json_file(DATA_FILE, data)
        new_data_found = True
    elif not new_data_in_batch and not batch_failed:
        print("No new reports found to scrape.")
        course_metadata['last_period_failed'] = False


    # Final period tracking logic (unchanged from your robust 'after' version)
    current_period = get_current_period()
    if not course_metadata['last_period_failed']:
        course_metadata['last_period_gathered'] = current_period
        current_period_data_found = any(get_period_from_instance_key(key) == current_period for key in new_data_in_batch.keys())

        if current_period_data_found:
            print(f"Found data for current period {current_period}. Clearing grace period flag.")
            course_metadata['last_scrape_during_grace_period'] = None
        elif is_grace_period_over(current_period):
            print("No current period data found, but grace period is over. Marking as up-to-date.")
            course_metadata['last_scrape_during_grace_period'] = None
        else:
            print("No current period data found and still in grace period. Marking for re-check.")
            course_metadata['last_scrape_during_grace_period'] = date.today().isoformat()
    
    save_json_file(METADATA_FILE, metadata)

    relevant_keys = course_metadata.get('relevant_periods', [])
    course_data = {key: data[key] for key in relevant_keys if key in data}
    
    return {
        'success': not batch_failed,
        'new_data_found': new_data_found,
        'data': course_data,
        'metadata': course_metadata,
        'error': f"Scraping halted for {course_code} due to a failed report." if batch_failed else None
    }

