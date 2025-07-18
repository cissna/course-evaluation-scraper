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

    # 4. Get initial list of report links using the authenticated session
    print(f"Fetching initial report links for {course_code}...")
    report_links = get_evaluation_report_links(session=session, course_code=course_code)

    if not report_links:
        print("No report links found on the main page. Workflow ending.")
        # We can record that we checked and found nothing.
        metadata[course_code]['last_period_gathered'] = metadata[course_code].get('last_period_gathered', 'checked_no_new_links')
        metadata[course_code]['last_period_failed'] = False
        save_json_file(METADATA_FILE, metadata)
        return

    # 5. Decide workflow based on number of links (pagination indicator)
    # If there are 20 or more links, the results are paginated by year.
    # We must scrape year by year to ensure we get all results and can save progress.
    if len(report_links) >= 20:
        print("Pagination detected (20+ links). Switching to year-by-year scraping.")
        start_year = 2010  # Define a reasonable start year for the data
        end_year = datetime.date.today().year

        # Loop through each year to get a complete set of links
        for year in range(start_year, end_year + 2): # +2 to be safe for how years are categorized
            print(f"\n--- Processing year: {year} ---")
            # Pass the session to the yearly link fetch as well
            yearly_links = get_evaluation_report_links(session=session, course_code=course_code, year=year)

            # If a single year returns 20+ links, it's an unhandled edge case.
            # Per the protocol, we must stop and record the failure point to avoid incomplete data.
            if len(yearly_links) >= 20:
                print(f"CRITICAL: Found 20 or more links for year {year}. This implies results for this year are incomplete.")
                print("Halting process to prevent saving partial data for the year.")
                # We record the failure point as the start of the problematic year (Intersession).
                # This allows the scraper to know where to resume or what period is problematic.
                metadata[course_code]['last_period_gathered'] = f"IN{str(year)[2:]}"
                metadata[course_code]['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                break  # Exit the year loop

            if not yearly_links:
                print(f"No links found for {year}.")
                continue

            print(f"Found {len(yearly_links)} links for {year}. Scraping and saving individually...")
            
            # Scrape all links for the current year, saving after each one
            year_batch_failed = False
            for link in yearly_links:
                instance_key = get_course_instance_key_from_url(link)
                if not instance_key:
                    print(f"Could not generate key for URL: {link}. Skipping.")
                    continue
                
                if instance_key in data:
                    # print(f"Report {instance_key} already exists. Skipping.")
                    continue

                print(f"Scraping new report: {instance_key}")
                scraped_data = scrape_evaluation_data(link, session)

                if scraped_data:
                    # Save data for this one report
                    data[instance_key] = scraped_data
                    save_json_file(DATA_FILE, data)
                    
                    # Update metadata and save it immediately to record progress
                    if instance_key not in metadata[course_code]['relevant_periods']:
                        metadata[course_code]['relevant_periods'].append(instance_key)
                    
                    metadata[course_code]['last_period_gathered'] = instance_key
                    if not metadata[course_code].get('first_period_gathered'):
                        metadata[course_code]['first_period_gathered'] = instance_key
                    
                    # Mark as not failed for now, will be updated if any in this batch fail
                    metadata[course_code]['last_period_failed'] = False
                    save_json_file(METADATA_FILE, metadata)
                    print(f"Successfully scraped and stored {instance_key}.")
                else:
                    print(f"Failed to scrape {instance_key}. Marking this batch as failed.")
                    year_batch_failed = True
                    # Record the failure immediately in the metadata
                    metadata[course_code]['last_period_failed'] = True
                    save_json_file(METADATA_FILE, metadata)

            if not year_batch_failed:
                print(f"Successfully completed all new reports for {year}.")
            else:
                print(f"Finished processing {year}, but some reports failed to scrape.")

    else: # Simple case: < 20 links, no pagination
        print(f"Found {len(report_links)} links. No pagination detected. Scraping all.")
        
        batch_failed = False
        for link in report_links:
            instance_key = get_course_instance_key_from_url(link)
            if not instance_key:
                print(f"Could not generate key for URL: {link}. Skipping.")
                continue
            
            if instance_key in data:
                # print(f"Report {instance_key} already exists. Skipping.")
                continue

            print(f"Scraping new report: {instance_key}")
            scraped_data = scrape_evaluation_data(link, session)

            if scraped_data:
                # Save data for this one report
                data[instance_key] = scraped_data
                save_json_file(DATA_FILE, data)
                
                # Update metadata and save it immediately
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