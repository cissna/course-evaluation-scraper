from data_manager import load_json_file, save_json_file
from period_logic import is_course_up_to_date
from config import METADATA_FILE, DATA_FILE

def initialize_course_metadata(course_code):
    """Initializes metadata for a new course if it doesn't exist."""
    metadata = load_json_file(METADATA_FILE)
    if course_code not in metadata:
        metadata[course_code] = {
            "last_period_gathered": None,
            "last_period_failed": False,
            "relevant_periods": []
        }
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