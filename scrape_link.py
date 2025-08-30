
import requests
from bs4 import BeautifulSoup
import json
import time
from config import MAX_RETRIES, INITIAL_RETRY_DELAY

def scrape_evaluation_data(report_url: str, session: requests.Session) -> dict:
    """
    Scrapes the detailed evaluation data from a single report URL.
    Enhanced to retry if 'overall_quality_frequency' not present, with exponential backoff delay.

    Args:
        report_url (str): The full URL to a specific evaluation report page.
        session (requests.Session): An authenticated requests Session object.

    Returns:
        A dictionary containing the scraped course data, structured
        according to the project's data.json format.
    
    Raises:
        requests.exceptions.RequestException: If the network request fails.
    """
    attempt = 0
    delay = INITIAL_RETRY_DELAY
    last_exception = None

    while attempt < MAX_RETRIES:
        if attempt > 0:
            print(f"Retrying scrape for {report_url} after {delay}s (attempt {attempt+1}/{MAX_RETRIES})...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

        try:
            # print(f"Scraping data from: {report_url}")  # prints for every specific course code, kinda a lot...
            scraped_data = {}

            # 1. Use the provided authenticated session to get the report page.
            response = session.get(report_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 2. Scrape Course Name and Instructor Name
            course_element = soup.find(lambda tag: tag.name == 'h3' and 'Course:' in tag.text)
            if course_element:
                course_name_element = course_element.find_next_sibling('span')
                if course_name_element:
                    full_course_name = course_name_element.text.strip()
                    # Extract only the part after " : " if present
                    if ' : ' in full_course_name:
                        scraped_data['course_name'] = full_course_name.split(' : ', 1)[1]
                    else:
                        scraped_data['course_name'] = full_course_name
            
            instructor_element = soup.find(lambda tag: tag.name == 'h3' and 'Instructor:' in tag.text)
            if instructor_element:
                instructor_name_element = instructor_element.find_next_sibling('span')
                if instructor_name_element:
                    scraped_data['instructor_name'] = instructor_name_element.text.strip()

            # 3. Scrape the frequency data from the hidden JSON data
            report_data_element = soup.find('input', id='hdnReportData')
            if report_data_element:
                report_data = json.loads(report_data_element['value'])
                question_mapping = {
                    "The overall quality of this course is:": "overall_quality_frequency",
                    "The instructor's teaching effectiveness is:": "instructor_effectiveness_frequency",
                    "The intellectual challenge of this course is:": "intellectual_challenge_frequency",
                    "The teaching assistant for this course is:": "ta_frequency",
                    "Feedback on my work for this course is useful:": "feedback_frequency",
                    "Compared to other Hopkins courses at this level, the workload for this course is:": "workload_frequency",
                    "Please enter the name of the TA you evaluated in question 4:": "ta_names"
                }
                for question in report_data:
                    question_text = question.get("QuestionText", "").strip()
                    if question_text in question_mapping:
                        key = question_mapping[question_text]
                        if key == "ta_names":
                            ta_names_raw = question.get("AnswerText", "")
                            if ta_names_raw:
                                # Split by '||' and clean up names
                                ta_names = [name.strip() for name in ta_names_raw.split('||')]
                                # Get unique names
                                scraped_data['ta_names'] = list(set(ta_names))
                            else:
                                scraped_data['ta_names'] = ["N/A"]
                        else:
                            frequency_dict = {}
                            for option in question.get("Options", []):
                                frequency_dict[option["OptionText"]] = option["Frequency"]
                            scraped_data[key] = frequency_dict

            if 'ta_names' not in scraped_data:
                scraped_data['ta_names'] = ["N/A"]

            # Success criteria: overall_quality_frequency present
            if 'overall_quality_frequency' in scraped_data:
                return scraped_data
            else:
                print(f"'overall_quality_frequency' missing in scrape attempt {attempt+1} for {report_url}.")
        except Exception as e:
            print(f"Exception during scrape attempt {attempt+1} for {report_url}: {e}")
            last_exception = e

        attempt += 1

    # If here, all attempts failed to get overall_quality_frequency; mark as failed for metadata handler
    if last_exception:
        print(f"Max retries reached for {report_url}: scrape failed due to network error.")
        return {
            "scrape_failed": True,
            "reason": "network_error",
            "exception": str(last_exception)
        }
    else:
        print(f"Max retries reached for {report_url}: scrape failed due to missing 'overall_quality_frequency' after successful requests.")
        return {
            "scrape_failed": True,
            "reason": "overall_quality_frequency missing after successful requests"
        }

if __name__ == '__main__':
    # This part is for standalone testing and requires a valid, authenticated session.
    # It cannot be run directly without the authentication logic from scrapeSearch.py
    print("This script is intended to be imported and used with an authenticated session.")
    print("To test, you would need to:")
    print("1. Get an authenticated session object from the main application.")
    print("2. Get a valid report URL.")
    print("3. Call scrape_evaluation_data(url, session).")