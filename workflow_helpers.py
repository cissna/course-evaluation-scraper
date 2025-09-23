from backend.db_utils import get_course_metadata, update_course_metadata, update_course_data, get_course_data_by_keys
from period_logic import (
    get_current_period,
    is_grace_period_over,
    get_period_from_instance_key,
    get_year_from_period_string,
    find_latest_year_from_keys,
    find_oldest_year_from_keys,
)
from scraping_logic import get_authenticated_session
from scrape_search import get_evaluation_report_links
from scrape_link import scrape_evaluation_data
import requests
from datetime import date

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
            links, has_more = get_evaluation_report_links(session, section_course_code)
            if links:
                print(f"Found {len(links)} links for section {i:02d}.")
                if not has_more:
                    all_links.update(links)
                else:
                    # "Show more results" button present, break up by year
                    print(f"Section {section_course_code} has 'Show more results' button. Breaking up by year.")
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
                            yearly_links, _ = get_evaluation_report_links(session, section_course_code, year=year)
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

# Helper function to sort links chronologically before scraping
def scrape_course_data_core(course_code: str, session: requests.Session = None, skip_grace_period_logic: bool = True) -> dict:
    """
    Core scraping function that handles the actual data collection logic.
    """
    # --- SETUP PHASE ---
    course_metadata = get_course_metadata(course_code)
    if not course_metadata:
        course_metadata = {
            "last_period_gathered": None, "last_period_failed": False,
            "relevant_periods": [], "last_scrape_during_grace_period": None
        }

    if session is None:
        try:
            session = get_authenticated_session()
        except requests.exceptions.RequestException as e:
            course_metadata['last_period_failed'] = True
            update_course_metadata(course_code, course_metadata)
            return {'success': False, 'error': f"Could not get authenticated session: {e}", 'metadata': course_metadata, 'data': {}, 'new_data_found': False}

    # --- PHASE 1: LINK COLLECTION ---
    links_to_process = {}
    
    try:
        print(f"Fetching initial report links for {course_code}...")
        initial_links, has_more_initial = get_evaluation_report_links(session=session, course_code=course_code)
    except Exception as e:
        course_metadata['last_period_failed'] = True
        update_course_metadata(course_code, course_metadata)
        return {'success': False, 'error': f"Failed to get initial report links: {e}", 'metadata': course_metadata, 'data': {}, 'new_data_found': False}

    if not initial_links:
        print("No report links found on the main page.")

    # Main logic branch: Decide scraping strategy based on "Show more results" button
    if not has_more_initial:
        # ✅ Simple Case: No "Show more results" button. Scrape what we found.
        print("No pagination detected (no 'Show more results' button). Processing initial links.")
        links_to_process = initial_links
    else:
        # ⚠️ Paginated Case: "Show more results" button present. Use optimized scraping strategy.
        print("Pagination detected ('Show more results' button present). Using optimized scraping strategy.")
        
        links_to_process = initial_links.copy()
        
        last_period = course_metadata.get('last_period_gathered')
        last_period_year = get_year_from_period_string(last_period) if last_period else 0
        latest_initial_year = find_latest_year_from_keys(initial_links.keys()) if initial_links else 0
        
        smart_start_year = max(last_period_year, latest_initial_year)
        current_academic_year = get_year_from_period_string(get_current_period())
        
        print(f"Initial links cover up to year {latest_initial_year}.")
        print(f"Starting additional year-by-year scraping from {smart_start_year} to {current_academic_year + 1}.")
        
        switchToSectionScraping = False
        all_yearly_links = {}

        for year in range(smart_start_year, current_academic_year + 2): # +2 to be safe
            print(f"\n--- Checking year: {year} ---")
            try:
                yearly_links, has_more_yearly = get_evaluation_report_links(session=session, course_code=course_code, year=year)
            except Exception as e:
                course_metadata['last_period_failed'] = True
                update_course_metadata(course_code, course_metadata)
                return {'success': False, 'error': f"Failed during year-by-year scan at year {year}: {e}", 'metadata': course_metadata, 'data': {}, 'new_data_found': False}

            if has_more_yearly:
                print(f"CRITICAL EDGE CASE: Year {year} has 'Show more results' button. Aborting year-by-year scan.")
                switchToSectionScraping = True
                break
            
            if yearly_links:
                print(f"Found {len(yearly_links)} links for {year}.")
                all_yearly_links.update(yearly_links)
        
        if switchToSectionScraping:
            section_links = get_all_links_by_section(session, course_code)
            links_to_process.update(section_links)
        else:
            print("Year-by-year scan complete.")
            links_to_process.update(all_yearly_links)

    # --- PHASE 2: UNIFIED SCRAPING ---
    print(f"\nFound a total of {len(links_to_process)} unique reports to potentially process.")
    batch_failed = False
    new_data_found = False

    existing_course_keys = get_course_data_by_keys(list(links_to_process.keys())).keys()

    sorted_links = links_to_process.items()

    for instance_key, link_url in sorted_links:
        if instance_key in existing_course_keys:
            continue

        scraped_data = scrape_evaluation_data(link_url, session)

        if scraped_data and scraped_data.get("scrape_failed", False):
            # In a DB-driven world, we might log these failures to a separate table.
            # For now, we'll just print a warning and skip.
            print(f"Warning: Scraping failed for {instance_key}. See server logs for details.")
            continue

        if scraped_data:
            update_course_data(instance_key, course_code, scraped_data)
            if instance_key not in course_metadata['relevant_periods']:
                course_metadata['relevant_periods'].append(instance_key)
            new_data_found = True
        else:
            print(f"Failed to scrape {instance_key}. Halting all scraping for {course_code} to prevent incomplete data.")
            course_metadata['last_period_failed'] = True
            batch_failed = True
            break

    # --- PHASE 3: FINALIZATION ---
    if not batch_failed and not new_data_found:
        print("No new reports found to scrape.")
        course_metadata['last_period_failed'] = False

    current_period = get_current_period()
    if not course_metadata['last_period_failed']:
        course_metadata['last_period_gathered'] = current_period

        newly_scraped_periods = {get_period_from_instance_key(key) for key in links_to_process.keys() if key not in existing_course_keys}
        current_period_data_found = current_period in newly_scraped_periods

        if current_period_data_found:
            print(f"Found data for current period {current_period}. Clearing grace period flag.")
            course_metadata['last_scrape_during_grace_period'] = None
        elif is_grace_period_over(current_period):
            print("No current period data found, but grace period is over. Marking as up-to-date.")
            course_metadata['last_scrape_during_grace_period'] = None
        else:
            print("No current period data found and still in grace period. Marking for re-check.")
            course_metadata['last_scrape_during_grace_period'] = date.today().isoformat()
    
    update_course_metadata(course_code, course_metadata)

    relevant_keys = course_metadata.get('relevant_periods', [])
    course_data = get_course_data_by_keys(relevant_keys)
    
    return {
        'success': not batch_failed,
        'new_data_found': new_data_found,
        'data': course_data,
        'metadata': course_metadata,
        'error': f"Scraping halted for {course_code} due to a failed report." if batch_failed else None
    }

