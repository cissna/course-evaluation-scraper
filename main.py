import json
import os
import datetime
import re
import requests
from urllib.parse import urlparse, parse_qs

# Import the scraper functions from other files
from scrape_search import get_evaluation_report_links
from scrape_link import scrape_evaluation_data

METADATA_FILE = 'metadata.json'
DATA_FILE = 'data.json'

def load_json_file(filepath: str) -> dict:
    """Safely loads a JSON file, creating it if it doesn't exist."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty dict if file is empty or corrupt

def save_json_file(filepath: str, data: dict):
    """Saves a dictionary to a JSON file with pretty printing."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def get_authenticated_session():
    """
    Creates and returns an authenticated requests.Session object.
    This is a simplified version based on the logic in scrapeSearch.py.
    A robust implementation might share the session more directly.
    """
    auth_url = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
    session = requests.Session()
    try:
        auth_response = session.get(auth_url, timeout=10)
        auth_response.raise_for_status()
        print("Authentication session created successfully.")
        return session
    except requests.exceptions.RequestException as e:
        print(f"Failed to create authenticated session: {e}")
        return None


def find_oldest_year_from_keys(keys: list) -> int:
    """
    Finds the oldest year from a list of course instance codes.
    Assumes year is represented by two digits (e.g., 'FA15' for 2015).
    Returns the oldest year found, or a default if no valid years are found.
    """
    oldest_year = datetime.date.today().year
    found_year = False
    
    year_re = re.compile(r'\.(?:FA|SP|SU|IN)(\d{2})$')
    
    for key in keys:
        match = year_re.search(key)
        if match:
            year_short = int(match.group(1))
            # Convert 2-digit year to 4-digit year
            year = 2000 + year_short if year_short < 70 else 1900 + year_short
            if year < oldest_year:
                oldest_year = year
                found_year = True
                
    # If no valid year was found in any key, return a default start year
    return oldest_year if found_year else 2010

def run_scraper_workflow(course_code: str):
    """
    Orchestrates the scraping process for a course, with frequent saving
    and robust handling of paginated results.
    """
    print(f"--- Starting workflow for course: {course_code} ---")

    # 1. Load existing data and metadata
    metadata = load_json_file(METADATA_FILE)
    data = load_json_file(DATA_FILE)

    # 2. Initialize metadata for the course if it's not present
    if course_code not in metadata:
        metadata[course_code] = {
            "first_period_gathered": None,
            "last_period_gathered": None,
            "last_period_failed": False, # Start optimistically
            "relevant_periods": []
        }
        # Save initial metadata structure
        save_json_file(METADATA_FILE, metadata)

    # 3. Get an authenticated session for all scraping
    session = get_authenticated_session()
    if not session:
        print("Could not get authenticated session. Aborting.")
        # Mark failure in metadata
        metadata[course_code]['last_period_failed'] = True
        save_json_file(METADATA_FILE, metadata)
        return

    # 4. Get initial dictionary of report links using the authenticated session
    print(f"Fetching initial report links for {course_code}...")
    report_links_dict = get_evaluation_report_links(session=session, course_code=course_code)

    if not report_links_dict:
        print("No report links found on the main page. Workflow ending.")
        metadata[course_code]['last_period_gathered'] = metadata[course_code].get('last_period_gathered', 'checked_no_new_links')
        metadata[course_code]['last_period_failed'] = False
        save_json_file(METADATA_FILE, metadata)
        return

    # 5. Decide workflow based on number of links (pagination indicator)
    if len(report_links_dict) >= 20:
        print("Pagination detected (20+ links). Switching to year-by-year scraping.")
        
        # Dynamically determine the start year from the oldest course instance code
        start_year = find_oldest_year_from_keys(report_links_dict.keys())
        end_year = datetime.date.today().year
        print(f"Dynamically determined start year: {start_year}")

        # Loop through each year to get a complete set of links
        for year in range(start_year, end_year + 2): # +2 to be safe
            print(f"\n--- Processing year: {year} ---")
            yearly_links_dict = get_evaluation_report_links(session=session, course_code=course_code, year=year)

            if len(yearly_links_dict) >= 20:
                print(f"CRITICAL: Found 20 or more links for year {year}. Halting to prevent incomplete data.")
                metadata[course_code]['last_period_gathered'] = f"IN{str(year)[2:]}"
                metadata[course_code]['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                break

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
                    
                    if instance_key not in metadata[course_code]['relevant_periods']:
                        metadata[course_code]['relevant_periods'].append(instance_key)
                    
                    metadata[course_code]['last_period_gathered'] = instance_key
                    if not metadata[course_code].get('first_period_gathered'):
                        metadata[course_code]['first_period_gathered'] = instance_key
                    
                    metadata[course_code]['last_period_failed'] = False
                    save_json_file(METADATA_FILE, metadata)
                    print(f"Successfully scraped and stored {instance_key}.")
                else:
                    print(f"Failed to scrape {instance_key}. Marking this batch as failed.")
                    year_batch_failed = True
                    metadata[course_code]['last_period_failed'] = True
                    save_json_file(METADATA_FILE, metadata)

            if not year_batch_failed:
                print(f"Successfully completed all new reports for {year}.")
            else:
                print(f"Finished processing {year}, but some reports failed to scrape.")

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
                
                if instance_key not in metadata[course_code]['relevant_periods']:
                    metadata[course_code]['relevant_periods'].append(instance_key)
                
                metadata[course_code]['last_period_gathered'] = instance_key
                if not metadata[course_code].get('first_period_gathered'):
                    metadata[course_code]['first_period_gathered'] = instance_key
                
                metadata[course_code]['last_period_failed'] = False
                save_json_file(METADATA_FILE, metadata)
                print(f"Successfully scraped and stored {instance_key}.")
            else:
                print(f"Failed to scrape {instance_key}. Marking this batch as failed.")
                batch_failed = True
                metadata[course_code]['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)

        if not batch_failed:
            print("Successfully completed all new reports for this batch.")
        else:
            print("Finished processing batch, but some reports failed to scrape.")

    print(f"--- Workflow for {course_code} complete. ---")


if __name__ == "__main__":
    # Example: Run the workflow for a specific course
    # This course code is from the project brief.
    target_course = 'AS.030.101'
    run_scraper_workflow(target_course)