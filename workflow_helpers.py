from data_manager import load_json_file, save_json_file
from period_logic import find_oldest_year_from_keys, find_latest_year_from_keys
from period_logic import get_year_from_period_string, get_current_period, is_grace_period_over, get_period_from_instance_key
from config import METADATA_FILE, DATA_FILE
from scraping_logic import get_authenticated_session
from scrape_search import get_evaluation_report_links
from scrape_link import scrape_evaluation_data
import requests
from datetime import date

# Helper function to sort links chronologically before scraping
def get_sort_key(item):
    """Creates a sort key based on year and semester from an instance_key."""
    instance_key = item[0]
    # Example instance_key: AS.020.101.01.FA23
    period = instance_key.split('.')[-1]
    year = int(period[2:])
    semester = period[:2]
    # Maps semester codes to a chronological order
    semester_map = {'SP': 0, 'SU': 1, 'FA': 2, 'IN': 3}
    return (year, semester_map.get(semester, 99))

def get_all_links_by_section(session, course_code):
    """
    Iterates through sections 00-99 for a course to find all possible report links.
    If any section returns 20 or more links, break up the section gathering by year for future-proof robustness.
    """
    print(f"--- Switching to section-based link gathering for {course_code} ---")
    all_links = {}

    for i in range(100):
        # e.g., creates AS.020.101.01, AS.020.101.02, etc.
        section_course_code = f"{course_code}.{i:02d}"
        try:
            links = get_evaluation_report_links(session, section_course_code)
            if links:
                print(f"Found {len(links)} links for section {i:02d}.")
                if len(links) < 20:
                    all_links.update(links)
                else:
                    # Too many links for this section, break up by year
                    print(f"Section {section_course_code} has {len(links)} links (≥20). Breaking up by year.")
                    keys = list(links.keys())
                    if keys:
                        # Use available keys to determine start year for the section
                        start_year = find_oldest_year_from_keys(keys)
                    else:
                        # Fallback if links dict is empty for some reason
                        start_year = 2010
                    current_academic_year = get_year_from_period_string(get_current_period())
                    section_yearly_links = {}
                    for year in range(start_year, current_academic_year + 2):  # +2 for robustness
                        print(f"  Scanning section {section_course_code}, year {year}...")
                        try:
                            yearly_links = get_evaluation_report_links(session, section_course_code, year=year)
                            if yearly_links:
                                print(f"    Found {len(yearly_links)} links for section {section_course_code}, year {year}.")
                                section_yearly_links.update(yearly_links)
                        except Exception as e_year:
                            print(f"    --- Could not get links for section {section_course_code}, year {year}: {e_year} ---")
                    if section_yearly_links:
                        all_links.update(section_yearly_links)
        except Exception as e:
            # It's okay if some sections don't exist; we log and continue.
            print(f"--- Could not get links for section {section_course_code}: {e} ---")
    return all_links

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
        initial_links = get_evaluation_report_links(session=session, course_code=course_code)
    except Exception as e:
        course_metadata['last_period_failed'] = True
        save_json_file(METADATA_FILE, metadata)
        return {'success': False, 'error': f"Failed to get initial report links: {e}", 'metadata': course_metadata, 'data': {}, 'new_data_found': False}

    if not initial_links:
        print("No report links found on the main page.")

    # Main logic branch: Decide scraping strategy
    if len(initial_links) < 20:
        # ✅ Simple Case: No pagination. Scrape what we found.
        print("No pagination detected. Processing initial links.")
        links_to_process = initial_links
    else:
        # ⚠️ Paginated Case: Use optimized scraping strategy.
        print("Pagination detected (20+ links). Using optimized scraping strategy.")
        
        # Always start with initial_links - this is the key optimization
        links_to_process = initial_links.copy()
        
        # Calculate smart start year for additional year-by-year scraping
        last_period = course_metadata.get('last_period_gathered')
        last_period_year = get_year_from_period_string(last_period) if last_period else 0
        latest_initial_year = find_latest_year_from_keys(initial_links.keys()) if initial_links else 0
        
        # Start year-by-year scraping from the year AFTER the latest we already have
        smart_start_year = max(last_period_year, latest_initial_year)
        current_academic_year = get_year_from_period_string(get_current_period())
        
        print(f"Initial links cover up to year {latest_initial_year}.")
        print(f"Starting additional year-by-year scraping from {smart_start_year} to {current_academic_year + 1}.")
        
        switchToSectionScraping = False
        all_yearly_links = {}

        for year in range(smart_start_year, current_academic_year + 2): # +2 to be safe
            print(f"\n--- Checking year: {year} ---")
            try:
                yearly_links = get_evaluation_report_links(session=session, course_code=course_code, year=year)
            except Exception as e:
                course_metadata['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                return {'success': False, 'error': f"Failed during year-by-year scan at year {year}: {e}", 'metadata': course_metadata, 'data': {}, 'new_data_found': False}

            if len(yearly_links) >= 20:
                # 🚨 Edge Case: A single year has 20+ courses.
                # Per the optimization, we now switch to scraping the entire course by section number.
                print(f"CRITICAL EDGE CASE: Found {len(yearly_links)} links for year {year}. Aborting year-by-year scan.")
                switchToSectionScraping = True
                break # Exit the year-by-year loop
            
            if yearly_links:
                print(f"Found {len(yearly_links)} links for {year}.")
                all_yearly_links.update(yearly_links)
        
        if switchToSectionScraping:
            # Execute the optimized fallback strategy - still include initial_links
            section_links = get_all_links_by_section(session, course_code)
            links_to_process.update(section_links)
        else:
            # The year-by-year scan completed successfully - combine with initial_links
            print("Year-by-year scan complete.")
            links_to_process.update(all_yearly_links)

    # --- PHASE 2: UNIFIED SCRAPING ---
    print(f"\nFound a total of {len(links_to_process)} unique reports to potentially process.")
    batch_failed = False
    new_data_found = False
    new_data_in_batch = {}
    new_relevant_periods = []
    
    # Sort links chronologically to process older data first
    sorted_links = sorted(links_to_process.items(), key=get_sort_key)

    for instance_key, link_url in sorted_links:
        if instance_key in data:
            continue # Skip data we already have

        # print(f"Scraping new report: {instance_key}")  # prints every specific course code, kinda a lot...
        scraped_data = scrape_evaluation_data(link_url, session)
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
