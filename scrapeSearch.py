import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_evaluation_report_links(course_code: str) -> list:
    """
    Authenticates with EvaluationKit and scrapes report links for a given course.

    Args:
        course_code: The path to the specific course page to look up (e.g., 'Report/Public/Results?Course=EN.601.473').
                     It can also have the following &... attributes:
                        - Instructor
                        - TermId
                        - Year
                        - AreaId
                        - QuestionKey
                        - Search

    Returns:
        A list of fully constructed report URLs found on the page.
        Returns an empty list if the page can't be accessed or no links are found.
    """
    # The initial URL that establishes an authenticated session via cookies.
    auth_url = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
    
    # The base URL for the course reports page.
    base_report_url = 'https://asen-jhu.evaluationkit.com/'
    course_url = urljoin(base_report_url, f'Report/Public/Results?Course={course_code}')

    # The base URL for constructing the final, individual report links.
    individual_report_base_url = 'https://asen-jhu.evaluationkit.com/Reports/StudentReport.aspx'

    report_links = []

    # Use a Session object to persist cookies across requests.
    with requests.Session() as session:
        try:
            # 1. Authenticate: Make a request to the auth URL to get session cookies.
            # print(f"Authenticating by accessing: {auth_url}")
            auth_response = session.get(auth_url, timeout=10)
            auth_response.raise_for_status()
            # print("Authentication successful.")

            # 2. Navigate: Go to the specific course page. The session will send the cookies.
            # print(f"Fetching course page: {course_url}")
            course_page_response = session.get(course_url, timeout=10)
            course_page_response.raise_for_status()
            # print("Successfully accessed course page.")

            # 3. Parse and Find Links: Use BeautifulSoup to parse the HTML.
            soup = BeautifulSoup(course_page_response.text, 'html.parser')

            # Find all <a> tags with the class 'sr-view-report'. This class seems
            # to be the specific selector for the "View Report" buttons.
            links_found = soup.find_all('a', class_='sr-view-report')

            if not links_found:
                # print("No 'View Report' links found on the page.")
                return []

            # print(f"Found {len(links_found)} report link(s). Processing...")

            # 4. Construct URLs: For each link, extract data attributes and build the full URL.
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
                    # The data-id values from BeautifulSoup are already URL-encoded, so we just join them.
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
    # Replace with the course code you want to scrape.
    target_course = 'AS.030.101' 
    
    # print(f"--- Starting scraper for course: {target_course} ---")
    links = get_evaluation_report_links(f'Report/Public/Results?Course={target_course}')
    
    # print("\n--- Scraping Complete ---")
    if links:
        # print(f"Found and constructed {len(links)} report URL(s):")
        for url in links:
            print(url)
    else:
        pass  # print("No links were successfully extracted.")

