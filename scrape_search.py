import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urljoin

def get_evaluation_report_links(
    session: requests.Session,
    course_code: str,
    instructor: str = None,
    term_id: str = None,
    year: str = None,
    area_id: str = None,
    question_key: str = None,
    search: str = None
) -> list:
    """
    Scrapes report links for a given course using a pre-authenticated session.

    Args:
        session (requests.Session): An authenticated requests session object.
        course_code (str): The course code to look up (e.g., 'EN.601.473'). This is required.
        instructor (str, optional): Filter by instructor name. Defaults to None.
        term_id (str, optional): Filter by a specific term ID. Defaults to None.
        year (str, optional): Filter by a specific year. Defaults to None.
        area_id (str, optional): Filter by a specific area ID. Defaults to None.
        question_key (str, optional): Filter by a specific question key. Defaults to None.
        search (str, optional): An unimportant search query. Defaults to None.

    Returns:
        A list of fully constructed report URLs found on the page.
        Returns an empty list if the page can't be accessed or no links are found.
        Returns None on unexpected behavior.
    """
    # The base URL for the course reports page.
    base_report_url = 'https://asen-jhu.evaluationkit.com/'
    
    # --- Build the dynamic course URL ---
    # Start with the required parameter
    query_params = {'Course': course_code}
    
    # Add optional parameters to the dictionary if they are provided
    if instructor:
        query_params['Instructor'] = instructor
    if term_id:
        query_params['TermId'] = term_id
    if year:
        query_params['Year'] = year
    if area_id:
        query_params['AreaId'] = area_id
    if question_key:
        query_params['QuestionKey'] = question_key
    if search:
        query_params['Search'] = search
        
    # URL-encode the parameters and join with the base path
    course_path = f"Report/Public/Results?{urlencode(query_params)}"
    course_url = urljoin(base_report_url, course_path)
    # --- End URL construction ---

    # The base URL for constructing the final, individual report links.
    individual_report_base_url = 'https://asen-jhu.evaluationkit.com/Reports/StudentReport.aspx'

    report_links = []

    try:
        # The session is assumed to be authenticated by the caller.
        # 1. Navigate: Go to the specific course page.
        # print(f"Fetching course page: {course_url}")
        course_page_response = session.get(course_url, timeout=10)
        course_page_response.raise_for_status()
        # print("Successfully accessed course page.")

        # 2. Parse and Find Links: Use BeautifulSoup to parse the HTML.
        soup = BeautifulSoup(course_page_response.text, 'html.parser')

        # Find all <a> tags with the class 'sr-view-report'. This class seems
        # to be the specific selector for the "View Report" buttons.
        links_found = soup.find_all('a', class_='sr-view-report')

        if not links_found:
            # print("No 'View Report' links found on the page.")
            return []

        # print(f"Found {len(links_found)} report link(s). Processing...")

        # 3. Construct URLs: For each link, extract data attributes and build the full URL.
        for link in links_found:
            # The href is '#', so the actual link is generated dynamically.
            # We can reconstruct it from the 'data-id' attributes.
            data_id0 = link.get('data-id0')
            data_id1 = link.get('data-id1')
            data_id2 = link.get('data-id2')
            data_id3 = link.get('data-id3')

            # Get the aria-label for context, which usually contains the report title.
            label = link.get('aria-label', 'No label found').strip()

            if all([data_id0, data_id1, data_id2, data_id3]):
                # The correct URL format is a single 'id' parameter with comma-separated values.
                # The order is id0, id1, id2, id3.

                id_string = f"{data_id0},{data_id1},{data_id2},{data_id3}"
                
                # Manually construct the final URL to match the required format.
                final_url = f"{individual_report_base_url}?id={id_string}"
                
                # print(f"\n---\nFound Report: {label}")
                # print(f"Constructed URL: {final_url}")
                report_links.append(final_url)
            else:
                print(f"\n---\nSkipping a link because it was missing required data-id attributes: {label}")
                return None  # may change this later, but for now I don't want to miss any potential data.


    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    return report_links

if __name__ == '__main__':
    # --- Example Usage ---
    
    # For standalone execution, we need to create and authenticate a session.
    auth_url = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
    with requests.Session() as example_session:
        try:
            auth_response = example_session.get(auth_url, timeout=10)
            auth_response.raise_for_status()
            print("Authentication successful for example run.")

            # 1. Simple lookup with just the required course code.
            target_course = 'AS.030.101'
            print(f"--- Starting scraper for course: {target_course} ---")
            links = get_evaluation_report_links(session=example_session, course_code=target_course)
            
            print("\n--- Scraping Complete ---")
            if links:
                print(f"Found and constructed {len(links)} report URL(s):")
                for url in links:
                    print(url)
            else:
                print("No links were successfully extracted or an error occurred.")

            print("\n" + "="*50 + "\n")

            # 2. Example of a more complex lookup with an instructor and year.
            # (Note: These are example values and may not return results)
            target_course_adv = 'EN.601.220'
            target_instructor = 'Jason Eisner'
            target_year = '2023'
            print(f"--- Starting advanced search for course: {target_course_adv}, Instructor: {target_instructor}, Year: {target_year} ---")
            
            adv_links = get_evaluation_report_links(
                session=example_session,
                course_code=target_course_adv,
                instructor=target_instructor,
                year=target_year
            )

            print("\n--- Scraping Complete ---")
            if adv_links:
                print(f"Found and constructed {len(adv_links)} report URL(s):")
                for url in adv_links:
                    print(url)
            else:
                print("No links were successfully extracted or an error occurred.")

        except requests.exceptions.RequestException as e:
            print(f"Failed to authenticate for example run: {e}")
