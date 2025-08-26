from data_manager import load_json_file, save_json_file
from period_logic import is_course_up_to_date, find_oldest_year_from_keys
from period_logic import get_year_from_period_string, get_current_period, is_grace_period_over
from config import METADATA_FILE, DATA_FILE
from scraping_logic import get_authenticated_session
from scrape_search import get_evaluation_report_links
from scrape_link import scrape_evaluation_data
import requests
from datetime import date

def initialize_course_metadata(course_code):
    """Initializes metadata for a new course if it doesn't exist."""
    metadata = load_json_file(METADATA_FILE)
    if course_code not in metadata:
        metadata[course_code] = {
            "last_period_gathered": None,
            "last_period_failed": False,
            "relevant_periods": [],
            "last_scrape_during_grace_period": None
        }
        save_json_file(METADATA_FILE, metadata)
    
    # Ensure the new field exists for existing metadata
    if "last_scrape_during_grace_period" not in metadata[course_code]:
        metadata[course_code]["last_scrape_during_grace_period"] = None
        save_json_file(METADATA_FILE, metadata)
    
    return metadata[course_code]

def check_course_status(course_code):
    """Checks if a course is up-to-date and returns its metadata."""
    metadata = load_json_file(METADATA_FILE)
    if course_code in metadata:
        course_metadata = metadata[course_code]
        if is_course_up_to_date(course_metadata.get('last_period_gathered'), course_metadata):
            print(f"Course {course_code} is already up-to-date. Skipping workflow.")
            return None, None # Indicate skipping
    
    course_metadata = initialize_course_metadata(course_code)
    data = load_json_file(DATA_FILE)
    return data, course_metadata

def scrape_course_data_core(course_code: str, session: requests.Session = None, skip_grace_period_logic: bool = True) -> dict:
    """
    Core scraping function that handles the actual data collection logic.
    
    Args:
        course_code: The course code to scrape
        session: Optional authenticated session (will create one if not provided)
        skip_grace_period_logic: If True, always check during grace periods (CLI default).
                               If False, don't auto-check during grace periods (web default).
    
    Returns:
        dict: Results containing:
            - 'success': bool indicating if scraping succeeded
            - 'new_data_found': bool indicating if new data was discovered
            - 'data': dict of scraped course data (instance_key -> course_data)
            - 'metadata': dict of updated metadata for the course
            - 'error': str error message if success=False
    """
    # Load existing data and metadata
    metadata = load_json_file(METADATA_FILE)
    data = load_json_file(DATA_FILE)
    
    # Initialize course metadata if needed
    if course_code not in metadata:
        metadata[course_code] = {
            "last_period_gathered": None,
            "last_period_failed": False,
            "relevant_periods": [],
            "last_scrape_during_grace_period": None
        }
        save_json_file(METADATA_FILE, metadata)
    
    # Ensure the new field exists for existing metadata
    if "last_scrape_during_grace_period" not in metadata[course_code]:
        metadata[course_code]["last_scrape_during_grace_period"] = None
        save_json_file(METADATA_FILE, metadata)
    
    course_metadata = metadata[course_code]
    
    # Get authenticated session if not provided
    if session is None:
        try:
            session = get_authenticated_session()
        except requests.exceptions.RequestException as e:
            course_metadata['last_period_failed'] = True
            save_json_file(METADATA_FILE, metadata)
            return {
                'success': False,
                'error': f"Could not get authenticated session: {e}",
                'metadata': course_metadata,
                'data': {},
                'new_data_found': False
            }
    
    new_data_found = False
    
    # Get initial dictionary of report links
    print(f"Fetching initial report links for {course_code}...")
    try:
        report_links_dict = get_evaluation_report_links(session=session, course_code=course_code)
    except Exception as e:
        course_metadata['last_period_failed'] = True
        save_json_file(METADATA_FILE, metadata)
        return {
            'success': False,
            'error': f"Failed to get report links: {e}",
            'metadata': course_metadata,
            'data': {},
            'new_data_found': False
        }
    
    if not report_links_dict:
        print("No report links found on the main page. Workflow will check for grace period updates at the end.")
    
    # Decide workflow based on number of links (pagination indicator)
    if len(report_links_dict) >= 20:
        print("Pagination detected (20+ links). Switching to year-by-year scraping.")
        
        # Determine start year: from metadata if available, otherwise from oldest key
        last_period = course_metadata.get('last_period_gathered')
        if last_period:
            start_year = get_year_from_period_string(last_period)
            print(f"Resuming from last gathered period's year: {start_year}")
        else:
            start_year = find_oldest_year_from_keys(report_links_dict.keys())
            print(f"First-time scrape. Dynamically determined start year: {start_year}")
        
        # Get current academic year from get_current_period() instead of date.today()
        current_period = get_current_period()
        current_academic_year = get_year_from_period_string(current_period)
        end_year = current_academic_year
        
        # Loop through each year to get a complete set of links
        for year in range(start_year, end_year + 2): # +2 to be safe
            print(f"\n--- Processing year: {year} ---")
            try:
                yearly_links_dict = get_evaluation_report_links(session=session, course_code=course_code, year=year)
            except Exception as e:
                course_metadata['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                return {
                    'success': False,
                    'error': f"Failed to get links for year {year}: {e}",
                    'metadata': course_metadata,
                    'data': {},
                    'new_data_found': new_data_found
                }
            
            if len(yearly_links_dict) >= 20:
                print(f"CRITICAL: Found 20 or more links for year {year}. Halting to prevent incomplete data.")
                metadata[course_code]['last_period_gathered'] = f"IN{str(year)[2:]}"
                metadata[course_code]['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                return {
                    'success': False,
                    'error': f"Too many results for year {year}, incomplete data risk",
                    'metadata': course_metadata,
                    'data': {},
                    'new_data_found': new_data_found
                }
            
            if not yearly_links_dict:
                print(f"No links found for {year}.")
                continue
            
            print(f"Found {len(yearly_links_dict)} links for {year}. Scraping and saving individually...")
            
            year_batch_failed = False
            for instance_key, link_url in yearly_links_dict.items():
                if instance_key in data:
                    continue
                
                print(f"Scraping new report: {instance_key}")
                scraped_data = scrape_evaluation_data(link_url, session)
                
                if scraped_data:
                    data[instance_key] = scraped_data
                    save_json_file(DATA_FILE, data)
                    new_data_found = True
                    
                    if instance_key not in metadata[course_code]['relevant_periods']:
                        metadata[course_code]['relevant_periods'].append(instance_key)
                    
                    metadata[course_code]['last_period_failed'] = False
                    save_json_file(METADATA_FILE, metadata)
                    print(f"Successfully scraped and stored {instance_key}.")
                else:
                    print(f"Failed to scrape {instance_key}. Halting processing for this course.")
                    metadata[course_code]['last_period_failed'] = True
                    save_json_file(METADATA_FILE, metadata)
                    year_batch_failed = True
                    break # Exit the loop for this year
            
            if not year_batch_failed:
                print(f"Successfully completed all new reports for {year}.")
            else:
                print(f"Finished processing {year}, but some reports failed to scrape. Further processing for this course halted.")
                break
            
            # If a batch within a year fails, we should stop processing subsequent years for this course.
            if year_batch_failed:
                break
    
    else: # Simple case: < 20 links, no pagination
        print(f"Found {len(report_links_dict)} links. No pagination detected. Scraping all.")
        
        batch_failed = False
        for instance_key, link_url in report_links_dict.items():
            if instance_key in data:
                continue
            
            print(f"Scraping new report: {instance_key}")
            scraped_data = scrape_evaluation_data(link_url, session)
            
            if scraped_data:
                data[instance_key] = scraped_data
                save_json_file(DATA_FILE, data)
                new_data_found = True
                
                if instance_key not in metadata[course_code]['relevant_periods']:
                    metadata[course_code]['relevant_periods'].append(instance_key)
                
                metadata[course_code]['last_period_failed'] = False
                save_json_file(METADATA_FILE, metadata)
                print(f"Successfully scraped and stored {instance_key}.")
            else:
                print(f"Failed to scrape {instance_key}. Halting processing for this course.")
                metadata[course_code]['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                batch_failed = True
                break # Exit the loop for this batch
        
        if not batch_failed:
            print("Successfully completed all new reports for this batch.")
        else:
            print("Finished processing batch, but some reports failed to scrape.")
    
    # Final period tracking logic
    current_period = get_current_period()
    
    if not metadata[course_code]['last_period_failed']:
        # Set last_period_gathered to current period after successful scraping
        metadata[course_code]['last_period_gathered'] = current_period
        
        if new_data_found:
            # Found data for current period, clear grace period flag
            print(f"Found data for {course_code}. Clearing grace period flag.")
            metadata[course_code]['last_scrape_during_grace_period'] = None
        else:
            # No new data found, check if we're in grace period
            if is_grace_period_over(current_period):
                print(f"No new data found for {course_code}, but grace period is over. Marking as up-to-date.")
                metadata[course_code]['last_scrape_during_grace_period'] = None
            else:
                # Only set grace period flag if we're NOT skipping grace period logic
                if skip_grace_period_logic:
                    print(f"No new data found for {course_code} and still in grace period, but skipping grace period logic.")
                    metadata[course_code]['last_scrape_during_grace_period'] = None
                else:
                    print(f"No new data found for {course_code} and still in grace period. Marking for re-check.")
                    metadata[course_code]['last_scrape_during_grace_period'] = date.today().isoformat()
        
        save_json_file(METADATA_FILE, metadata)
    
    # Return relevant data
    relevant_keys = metadata[course_code].get('relevant_periods', [])
    course_data = {key: data[key] for key in relevant_keys if key in data}
    
    return {
        'success': True,
        'new_data_found': new_data_found,
        'data': course_data,
        'metadata': metadata[course_code],
        'error': None
    }
