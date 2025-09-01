from dotenv import load_dotenv
import requests
import argparse
from typing import List


load_dotenv()
# check_course.py

# Base URL for the JHU SIS API
BASE_URL = "https://sis.jhu.edu/api"

def _convert_term_format(short_term: str) -> str:
    """[Internal] Converts a short term format to the full API format."""
    prefix_map = {
        'SP': 'Spring', 'SU': 'Summer', 'FA': 'Fall', 'IN': 'Intersession'
    }
    try:
        prefix = short_term[:2].upper()
        year = short_term[2:]
        return f"{prefix_map[prefix]} 20{year}"
    except (KeyError, IndexError):
        raise ValueError(f"Invalid term format '{short_term}'. Use SP, SU, FA, or IN followed by a two-digit year.")

def _get_target_terms(api_key: str, start_term_full: str, limit: int) -> List[str]:
    """[Internal] Fetches and returns a chronological list of terms to check."""
    url = f"{BASE_URL}/classes/codes/terms?key={api_key}"
    response = requests.get(url)
    response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    
    terms_data = response.json()
    if not isinstance(terms_data, list) or not terms_data:
        raise ConnectionError(f"API returned an invalid response for terms. Check API key. Response: {response.text}")

    all_terms = [term['Name'] for term in terms_data]

    try:
        start_index = all_terms.index(start_term_full)
    except ValueError:
        raise ValueError(f"Start term '{start_term_full}' not found in available terms.")

    slice_start = max(0, start_index - limit + 1)
    target_terms_rev_chrono = all_terms[slice_start : start_index + 1]
    
    return target_terms_rev_chrono[::-1] # Return in chronological order

def _fetch_course_data(api_key: str, course_number: str, terms_to_check: List[str]) -> List[dict]:
    """[Internal] Fetches raw course offering data from the API."""
    if not terms_to_check:
        return []
    
    api_course_number = course_number.replace('.', '')
    url = f"{BASE_URL}/classes"
    params = {
        'key': api_key,
        'CourseNumber': api_course_number,
        'Term': terms_to_check
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# --- Public Function ---
def find_course_offerings(api_key: str, course_number: str, start_term: str, limit: int = 4):
    """
    Checks the JHU SIS API to see which future terms a course is offered in.

    Returns:
        dict: {
            "status": "success"|"api_failed"|"invalid_term",
            "offerings": List[str] (may be empty),
            "error": Optional error message
        }
    """
    try:
        start_term_full = _convert_term_format(start_term)
        target_terms = _get_target_terms(api_key, start_term_full, limit)
        offerings = _fetch_course_data(api_key, course_number, target_terms)

        if not offerings:
            return {"status": "success", "offerings": [], "error": None}

        found_terms_set = {offering['Term'] for offering in offerings}
        chronological_found_terms = [term for term in target_terms if term in found_terms_set]

        return {"status": "success", "offerings": chronological_found_terms, "error": None}
    except ValueError as ve:
        return {"status": "invalid_term", "offerings": [], "error": str(ve)}
    except requests.exceptions.RequestException as re:
        return {"status": "api_failed", "offerings": [], "error": str(re)}

# --- Example usage when run as a standalone script ---
def main():
    """Parses command-line arguments and prints a human-readable summary."""
    parser = argparse.ArgumentParser(
        description="Check JHU course offerings and print a summary.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("api_key", help="Your JHU SIS API key.")
    parser.add_argument("course_number", help="Course number (e.g., 'EN.601.479').")
    parser.add_argument("start_term", help="Starting term (e.g., 'SU25', 'FA26').")
    parser.add_argument(
        "-l", "--limit", type=int, default=4,
        help="Number of terms to check (default: 4)."
    )
    args = parser.parse_args()
    
    print(f"🔍 Checking for {args.course_number} starting {args.start_term}...")
    try:
        found_terms = find_course_offerings(
            api_key=args.api_key,
            course_number=args.course_number,
            start_term=args.start_term,
            limit=args.limit
        )
        
        if found_terms:
            print(f"✅ Course will be run in: {', '.join(found_terms)}")
        else:
            print(f"❌ Course not found in the {args.limit} terms checked.")
            
    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()