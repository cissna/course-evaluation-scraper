from datetime import date
from config import METADATA_FILE, DATA_FILE
from data_manager import load_json_file, save_json_file
from scraping_logic import get_authenticated_session
from scrape_search import get_evaluation_report_links
from scrape_link import scrape_evaluation_data
from period_logic import find_oldest_year_from_keys, is_course_up_to_date, get_period_from_instance_key
from period_logic import get_year_from_period_string
from period_logic import get_current_period, is_grace_period_over

def run_scraper_workflow(course_code: str):
    """
    Orchestrates the scraping process for a course, with frequent saving
    and robust handling of paginated results.
    """
    print(f"--- Starting workflow for course: {course_code} ---")

    # 1. Load existing data and metadata
    metadata = load_json_file(METADATA_FILE)
    data = load_json_file(DATA_FILE)

    # 2. Check if course is up-to-date, then initialize if new.
    if course_code in metadata:
        course_metadata = metadata[course_code]
        if is_course_up_to_date(course_metadata.get('last_period_gathered'), course_metadata):
            print(f"Course {course_code} is already up-to-date. Skipping workflow.")
            return
    else:
        metadata[course_code] = {
            "last_period_gathered": None,
            "last_period_failed": False, # Start optimistically
            "relevant_periods": []
        }
        # Save initial metadata structure
        save_json_file(METADATA_FILE, metadata)

    course_metadata = metadata[course_code]

    # 3. Get an authenticated session for all scraping
    session = get_authenticated_session()
    if not session:
        print("Could not get authenticated session. Aborting.")
        # Mark failure in metadata
        metadata[course_code]['last_period_failed'] = True
        save_json_file(METADATA_FILE, metadata)
        return

    new_data_found = False

    # 4. Get initial dictionary of report links using the authenticated session
    print(f"Fetching initial report links for {course_code}...")
    report_links_dict = get_evaluation_report_links(session=session, course_code=course_code)

    if not report_links_dict:
        print("No report links found on the main page. Workflow will check for grace period updates at the end.")

    # 5. Decide workflow based on number of links (pagination indicator)
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
        
        end_year = date.today().year

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
                    new_data_found = True
                    
                    if instance_key not in metadata[course_code]['relevant_periods']:
                        metadata[course_code]['relevant_periods'].append(instance_key)
                    
                    period = get_period_from_instance_key(instance_key)
                    if period:
                        metadata[course_code]['last_period_gathered'] = period
                    
                    metadata[course_code]['last_period_failed'] = False
                    save_json_file(METADATA_FILE, metadata)
                    print(f"Successfully scraped and stored {instance_key}.")
                else:
                    print(f"Failed to scrape {instance_key}. Halting processing for this course.")
                    metadata[course_code]['last_period_failed'] = True
                    save_json_file(METADATA_FILE, metadata)
                    year_batch_failed = True # Mark as failed to prevent success message
                    break # Exit the loop for this year

            if not year_batch_failed:
                print(f"Successfully completed all new reports for {year}.")
            else:
                print(f"Finished processing {year}, but some reports failed to scrape. Further processing for this course halted.")
            
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
                
                period = get_period_from_instance_key(instance_key)
                if period:
                    metadata[course_code]['last_period_gathered'] = period
                
                metadata[course_code]['last_period_failed'] = False
                save_json_file(METADATA_FILE, metadata)
                print(f"Successfully scraped and stored {instance_key}.")
            else:
                print(f"Failed to scrape {instance_key}. Halting processing for this course.")
                metadata[course_code]['last_period_failed'] = True
                save_json_file(METADATA_FILE, metadata)
                batch_failed = True # Mark as failed to prevent success message
                break # Exit the loop for this batch

        if not batch_failed:
            print("Successfully completed all new reports for this batch.")
        else:
            print("Finished processing batch, but some reports failed to scrape.")

    # Final check for courses where no new data was found
    if not new_data_found and not metadata[course_code]['last_period_failed']:
        print(f"No new evaluation data was found for {course_code}.")
        current_period = get_current_period()
        if is_grace_period_over(current_period):
            print(f"Grace period for {current_period} is over. Updating last_period_gathered to mark as up-to-date.")
            metadata[course_code]['last_period_gathered'] = current_period
            metadata[course_code]['last_period_failed'] = False
            save_json_file(METADATA_FILE, metadata)
        else:
            print(f"Grace period for {current_period} is not over. Not updating metadata.")

    print(f"--- Workflow for {course_code} complete. ---")