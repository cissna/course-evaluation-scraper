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
) -> dict:
    """
    Scrapes report links for a given course and returns them in a dictionary
    mapping the course instance code to the report URL.

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
        A dictionary where keys are course instance codes (e.g., 'AS.030.101.01.FA15')
        and values are the corresponding report URLs.
        Returns an empty dictionary if no links are found.

    Raises:
        requests.exceptions.RequestException: If the network request fails.
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

    report_links = {}

    # The session is assumed to be authenticated by the caller.
    # 1. Navigate: Go to the specific course page.
    course_page_response = session.get(course_url, timeout=10)
    course_page_response.raise_for_status()

    # 2. Parse and Find Links: Use BeautifulSoup to parse the HTML.
    soup = BeautifulSoup(course_page_response.text, 'html.parser')

    # Find all <a> tags with the class 'sr-view-report'.
    links_found = soup.find_all('a', class_='sr-view-report')

    if not links_found:
        return {}

    # 3. Construct URLs and find course codes
    for link in links_found:
        data_id0 = link.get('data-id0')
        data_id1 = link.get('data-id1')
        data_id2 = link.get('data-id2')
        data_id3 = link.get('data-id3')

        if all([data_id0, data_id1, data_id2, data_id3]):
            # Construct the URL for the report
            id_string = f"{data_id0},{data_id1},{data_id2},{data_id3}"
            final_url = f"{individual_report_base_url}?id={id_string}"

            # Find the parent row for the link, which contains all the info for one report
            parent_row = link.find_parent('div', class_='row')
            
            course_instance_code = None
            if parent_row:
                course_code_p = parent_row.find('p', class_='sr-dataitem-info-code')
                if course_code_p and course_code_p.text:
                    course_instance_code = course_code_p.text.strip()

            if course_instance_code:
                report_links[course_instance_code] = final_url
            else:
                label = link.get('aria-label', 'No label found').strip()
                print(f"Could not find course instance code for report: {label}")
        else:
            label = link.get('aria-label', 'No label found').strip()
            print(f"Skipping a link because it was missing required data-id attributes: {label}")

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
                print(f"Found {len(links)} report(s):")
                for code, url in links.items():
                    print(f"  - {code}: {url}")
            else:
                print("No reports were successfully extracted or an error occurred.")

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
                print(f"Found {len(adv_links)} report(s):")
                for code, url in adv_links.items():
                    print(f"  - {code}: {url}")
            else:
                print("No reports were successfully extracted or an error occurred.")

        except requests.exceptions.RequestException as e:
            print(f"Failed to authenticate for example run: {e}")
