import json
import os
import datetime
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

def get_course_instance_key_from_url(url: str) -> str:
    """
    Parses a report URL to generate a unique key for data.json.
    This is a placeholder implementation and may need adjustment based on
    the final URL structure and desired key format.
    Example URL: https://asen-jhu.evaluationkit.com/Reports/StudentReport.aspx?id=val1,val2,val3,val4
    We can use the 'id' as a unique key.
    """
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        id_param = query_params.get('id', [None])[0]
        if id_param:
            # A more robust key might involve parsing course codes/terms from the page
            return f"report_{id_param.replace(',', '_')}"
        return None
    except:
        return None


def run_scraper_workflow(course_code: str):
    """
    Orchestrates the full scraping process for a given course code.
    """
    print(f"--- Starting workflow for course: {course_code} ---")
    
    # 1. Load existing data and metadata
    metadata = load_json_file(METADATA_FILE)
    data = load_json_file(DATA_FILE)
    
    # Initialize metadata for the course if it's not present
    if course_code not in metadata:
        metadata[course_code] = {
            "first_period_gathered": None,
            "last_period_gathered": None,
            "last_period_failed": True,
            "relevant_periods": []
        }

    # 2. Get evaluation report links
    # This function also authenticates implicitly, but we need a session for the next step.
    print(f"Fetching report links for {course_code}...")
    report_links = get_evaluation_report_links(course_code=course_code)

    # Handle paginated results if necessary
    if len(report_links) >= 20:
        print("Pagination detected. Fetching links year by year...")
        all_links_by_year = []
        start_year = 2010
        end_year = datetime.date.today().year

        for year in range(start_year, end_year + 2):  # year somtimes weirdly represents the year before it, so we do an extra to be safe
            print(f"Fetching links for {course_code} for year: {year}")
            yearly_links = get_evaluation_report_links(course_code=course_code, year=year)

            if len(yearly_links) >= 20:
                print(f"WARNING: Found 20 or more links for {year}. This indicates a potential failure to retrieve all results for this year and subsequent years. Skipping.")
                metadata[course_code]['last_period_gathered'] = "IN" + str(year)[2:]  # intersession is the first period of the year
                metadata[course_code]['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                break  # Stop processing further years

            all_links_by_year.extend(yearly_links)
        
        report_links = all_links_by_year

    if not report_links:
        print("No new report links found. Workflow ending.")
        # Update metadata to show we checked
        # A more robust solution would use actual dates/terms
        metadata[course_code]['last_period_gathered'] = "checked_no_new_links"
        save_json_file(METADATA_FILE, metadata)
        return

    print(f"Found {len(report_links)} report links.")

    # 3. Get an authenticated session for scraping individual links
    session = get_authenticated_session()
    if not session:
        print("Could not get authenticated session. Aborting.")
        return

    # 4. Scrape each link and update data
    new_data_found = False
    for link in report_links:
        instance_key = get_course_instance_key_from_url(link)
        
        if not instance_key:
            print(f"Could not generate a key for URL: {link}. Skipping.")
            continue

        # Check if this specific report has already been scraped
        if instance_key in data:
            print(f"Report {instance_key} already exists in data.json. Skipping.")
            continue

        print(f"Scraping new report: {instance_key}")
        scraped_data = scrape_evaluation_data(link, session)

        if scraped_data:
            data[instance_key] = scraped_data
            # Update metadata with the newly found period/instance
            if instance_key not in metadata[course_code]['relevant_periods']:
                 metadata[course_code]['relevant_periods'].append(instance_key)
            new_data_found = True
            print(f"Successfully scraped and stored data for {instance_key}.")
        else:
            print(f"Failed to scrape data for {instance_key}.")
            metadata[course_code]['last_period_failed'] = True

    # 5. Save updated data and metadata
    if new_data_found:
        print("Saving updated data.json...")
        save_json_file(DATA_FILE, data)
        
        # Update metadata timestamps/periods
        # This is simplified; a real implementation would parse terms/dates
        last_gathered = metadata[course_code]['relevant_periods'][-1] if metadata[course_code]['relevant_periods'] else "unknown"
        metadata[course_code]['last_period_gathered'] = last_gathered
        if not metadata[course_code]['first_period_gathered']:
            metadata[course_code]['first_period_gathered'] = last_gathered
        
        # If we successfully scraped something, we can be optimistic.
        # A more robust check would confirm all links were scraped.
        metadata[course_code]['last_period_failed'] = False

    print("Saving updated metadata.json...")
    save_json_file(METADATA_FILE, metadata)
    
    print(f"--- Workflow for {course_code} complete. ---")


if __name__ == "__main__":
    # Example: Run the workflow for a specific course
    # This course code is from the project brief.
    target_course = 'AS.030.101'
    run_scraper_workflow(target_course)