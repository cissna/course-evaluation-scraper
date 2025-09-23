import re
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from data_manager import load_json_file
from config import DATA_FILE

def get_last_name(full_name: str) -> str:
    """
    Extracts the last name from a full name string.
    Handles simple cases and names with middle initials.
    """
    if not full_name:
        return ""
    # Remove common titles
    name = re.sub(r'^(Dr|Mr|Mrs|Ms)\.\s+', '', full_name.strip())
    parts = name.split()
    return parts[-1].lower() if parts else ""

def find_instructor_variants(instructor_name: str) -> list:
    """
    Finds all variations of an instructor's name in the dataset based on last name.
    
    Args:
        instructor_name (str): The name of the instructor to search for.

    Returns:
        list: A list of unique instructor names that share the same last name.
    """
    data = load_json_file(DATA_FILE)
    if not data:
        return [instructor_name] # Return the original name if no data

    all_instructors = set(
        course_data.get('instructor_name', '').strip()
        for course_data in data.values()
        if course_data.get('instructor_name')
    )

    target_last_name = get_last_name(instructor_name)
    if not target_last_name:
        return [instructor_name]

    similar_names = {
        name for name in all_instructors if get_last_name(name) == target_last_name
    }
    
    # Always include the original name in the set
    similar_names.add(instructor_name)

    return sorted(list(similar_names))

if __name__ == '__main__':
    # Example usage (requires data.json to be populated)
    test_name_1 = "Michael Bonner"
    print(f"Finding variants for '{test_name_1}':")
    variants_1 = find_instructor_variants(test_name_1)
    print(variants_1)

    test_name_2 = "Ali Darvish"
    print(f"\nFinding variants for '{test_name_2}':")
    variants_2 = find_instructor_variants(test_name_2)
    print(variants_2)