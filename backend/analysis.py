import re
import json
from backend.course_grouping_service import CourseGroupingService

# --- Mappings for Statistical Calculations ---

# Maps frequency keys to a tuple: (name for UI, numerical value mapping)
STAT_MAPPINGS = {
    "overall_quality_frequency": (
        "Overall Quality",
        {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
    ),
    "instructor_effectiveness_frequency": (
        "Instructor Effectiveness",
        {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
    ),
    "intellectual_challenge_frequency": (
        "Intellectual Challenge",
        {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
    ),
    "workload_frequency": (
        "Workload",
        {"Much lighter": 1, "Somewhat lighter": 2, "Typical": 3, "Somewhat heavier": 4, "Much heavier": 5}
    ),
    "feedback_frequency": (
        "Helpful Feedback",
        {"Disagree strongly": 1, "Disagree somewhat": 2, "Neither agree nor disagree": 3, "Agree somewhat": 4, "Agree strongly": 5}
    ),
    "ta_frequency": (
        "TA Quality",
        {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
    ),
    "periods_course_has_been_run": (
        "Periods Course Has Been Run",
        {}  # Special case - computed field, no frequency mapping needed
    )
}

# --- Core Calculation Functions ---

grouping_service = CourseGroupingService()

def calculate_weighted_average(frequency_dict: dict, value_mapping: dict) -> float:
    """
    Calculates the weighted average for a set of frequency data.
    
    Args:
        frequency_dict (dict): A dictionary of response counts (e.g., {"Good": 10, "Excellent": 20}).
        value_mapping (dict): A dictionary mapping response text to numerical values (e.g., {"Good": 4, "Excellent": 5}).

    Returns:
        float: The calculated weighted average, or 0.0 if there are no responses.
    """
    total_responses = 0
    weighted_sum = 0
    
    for response_text, count in frequency_dict.items():
        if response_text in value_mapping:
            total_responses += count
            weighted_sum += count * value_mapping[response_text]
            
    if total_responses == 0:
        return 0.0
        
    return round(weighted_sum / total_responses, 2)


def extract_course_metadata(course_names: dict, course_code: str, metadata_from_file: dict, primary_course_code: str = None) -> dict:
    """
    Extract course name metadata from course instances and merge with existing metadata.

    Args:
        course_names (dict): Dictionary mapping instance keys to course names.
        course_code (str): The course code (e.g., "AS.171.105").
        metadata_from_file (dict): The metadata loaded from metadata.json.
        primary_course_code (str, optional): The primary course code to filter for grouping.

    Returns:
        dict: Contains 'current_name', 'former_names', and merged fields from metadata_from_file.
    """
    # Initialize with current_name and former_names
    result_metadata = {'current_name': None, 'former_names': []}

    filtered_course_names = course_names
    if primary_course_code:
        # Only include instances matching the base code, e.g., "AS.050.375" from "AS.050.375.01.FA23"
        def matches_primary(instance_key):
            match = re.match(r'([A-Z]+\.\d+\.\d+)', instance_key)
            return match and match.group(1) == primary_course_code

        filtered_course_names = {k: v for k, v in course_names.items() if matches_primary(k)}

    if not filtered_course_names:
        # If no course names, but metadata from file exists, use it
        if course_code in metadata_from_file:
            result_metadata.update(metadata_from_file[course_code])
        return result_metadata

    def parse_semester_year(instance_key):
        """Parse semester and year from instance key for chronological sorting."""
        # Extract semester/year pattern (e.g., 'FA24', 'SP23', 'SU22')
        match = re.search(r'([A-Z]{2})(\d{2})', instance_key)
        if match:
            semester, year = match.groups()
            year_num = int('20' + year)  # Convert '24' to 2024

            # Convert semesters to numbers for sorting (SP=1, SU=2, FA=3)
            semester_order = {'SP': 1, 'SU': 2, 'FA': 3}
            semester_num = semester_order.get(semester, 0)

            return (year_num, semester_num)
        return (0, 0)  # Default for unparseable keys

    # Sort by chronological order (year, then semester within year)
    sorted_instances = sorted(filtered_course_names.keys(), key=parse_semester_year)

    # Get the most recent name
    most_recent_key = sorted_instances[-1]
    current_name = filtered_course_names[most_recent_key]

    # Collect all unique names that are different from the current name
    all_names = set(filtered_course_names.values())
    former_names = list(all_names - {current_name})

    result_metadata['current_name'] = current_name
    result_metadata['former_names'] = former_names

    # Merge with metadata from file, if available
    if course_code in metadata_from_file:
        # Overwrite current_name and former_names if they exist in metadata_from_file
        # but the prompt says "Don't change the json structure besides adding new fields"
        # so we should keep the current_name and former_names from the course_names
        # and add the other fields from metadata_from_file
        file_metadata = metadata_from_file[course_code].copy()
        file_metadata.pop('current_name', None) # Remove if exists to avoid overwriting
        file_metadata.pop('former_names', None) # Remove if exists to avoid overwriting
        result_metadata.update(file_metadata)

    return result_metadata


def calculate_group_statistics(course_instances: list, stats_to_calculate: list, metadata: dict = None, instance_keys: list = None) -> dict:
    """
    Calculates aggregated statistics for a group of course instances.

    Args:
        course_instances (list): A list of course data dictionaries.
        stats_to_calculate (list): A list of frequency keys to be calculated (e.g., ["overall_quality_frequency"]).
        metadata (dict, optional): Metadata for special-case stats like 'periods_course_has_been_run'.
        instance_keys (list, optional): List of instance keys corresponding to course_instances for period calculation.

    Returns:
        dict: A dictionary containing the calculated average for each requested statistic.
    """
    # Aggregate frequencies from all instances in the group
    aggregated_frequencies = {}
    for key in stats_to_calculate:
        aggregated_frequencies[key] = {}

    for instance in course_instances:
        for key in stats_to_calculate:
            if key in instance:
                for response_text, count in instance[key].items():
                    agg_dict = aggregated_frequencies[key]
                    agg_dict[response_text] = agg_dict.get(response_text, 0) + count

    # Calculate the final averages from the aggregated frequencies
    results = {}
    for key in stats_to_calculate:
        ui_name, value_mapping = STAT_MAPPINGS[key]
        if key == "periods_course_has_been_run":
            # Compute periods_course_has_been_run using actual instance keys from the filtered group
            value = compute_periods_from_instance_keys(instance_keys)
            # Use the original key, not the converted UI name
            results[key] = value
        else:
            avg = calculate_weighted_average(aggregated_frequencies[key], value_mapping)
            # Use the original key (e.g., "feedback_frequency"), not the converted UI name
            results[key] = avg
    return results

# --- Filtering and Separation Logic ---

def get_instance_year(instance_key: str) -> int:
    """Extracts the four-digit year from a course instance key."""
    match = re.search(r'\.(?:FA|SP|SU|IN)(\d{2})$', instance_key)
    if match:
        year_short = int(match.group(1))
        return 2000 + year_short
    return 0

def get_instance_season(instance_key: str) -> str:
    """Extracts the season (e.g., 'Fall') from a course instance key."""
    match = re.search(r'\.((?:FA|SP|SU|IN))\d{2}$', instance_key)
    seasons = {"FA": "Fall", "SP": "Spring", "SU": "Summer", "IN": "Intersession"}
    return seasons.get(match.group(1)) if match else "Unknown"
    
def compute_periods_course_has_been_run(course_instances):
    """Compute Periods Course Has Been Run from actual course instances in the group."""
    if not course_instances:
        return "N/A"
    
    # Extract periods from the instance keys themselves
    periods = set()
    for instance in course_instances:
        # Instance is a dict, we need to get the key from somewhere
        # We'll need to modify the calling code to pass the keys
        pass
    
    if not periods:
        return "N/A"
    
    # Sort periods chronologically and return as comma-separated string
    sorted_periods = sorted(periods)
    return ', '.join(sorted_periods)

def compute_periods_from_instance_keys(instance_keys):
    """Extract periods from instance keys and return as sorted, comma-separated string."""
    if not instance_keys:
        return "N/A"
    
    periods = set()
    for key in instance_keys:
        # Extract period from instance key (e.g., "AS.100.101.01.FA24" -> "FA24")
        match = re.search(r'\.([A-Z]{2}\d{2})$', key)
        if match:
            periods.add(match.group(1))
    
    if not periods:
        return "N/A"
    
    # Sort periods chronologically
    sorted_periods = sorted(periods)
    return ', '.join(sorted_periods)

def filter_instances(all_instances: dict, filters: dict) -> dict:
    """Filters course instances based on a set of criteria."""
    filtered = {}
    
    min_year_str = filters.get('min_year')
    max_year_str = filters.get('max_year')

    min_year = int(min_year_str) if min_year_str else None
    max_year = int(max_year_str) if max_year_str else None
    seasons = filters.get('seasons') # Expects a list of seasons, e.g., ["Fall", "Spring"]
    instructors = filters.get('instructors') # Expects a list of instructor names

    for key, instance in all_instances.items():
        year = get_instance_year(key)
        
        if min_year and year < min_year:
            continue
        if max_year and year > max_year:
            continue
        if seasons and get_instance_season(key) not in seasons:
            continue
        if instructors and instance.get('instructor_name') not in instructors:
            continue
            
        filtered[key] = instance
        
    return filtered

def separate_instances(instances: dict, separation_keys=None) -> dict:
    """
    Separates instances into groups based on one or more separation keys.

    Args:
        instances (dict): Data instances to group.
        separation_keys (Union[str, list, None]): Key(s) to group by.
            Can be a single key (str), multiple keys (list of str), or None.

    Returns:
        dict: Groups of instances, keyed by composite group name.
    """
    if not separation_keys:
        return {"All Data": list(instances.values())}

    # Backward compatibility: single string handled as single-key list
    if isinstance(separation_keys, str):
        separation_keys = [separation_keys]
    elif not isinstance(separation_keys, list):
        separation_keys = []

    if not separation_keys:
        return {"All Data": list(instances.values())}

    groups = {}
    for key, instance in instances.items():
        group_parts = []
        for sep_key in separation_keys:
            value = "Unknown"
            if sep_key == "instructor":
                value = instance.get("instructor_name", "Unknown")
            elif sep_key == "year":
                value = str(get_instance_year(key))
            elif sep_key == "season":
                value = get_instance_season(key)
            elif sep_key == "course_name":
                value = instance.get("course_name", "Unknown")
            elif sep_key == "exact_period":
                # Extract period from instance key (e.g., "AS.100.101.01.FA24" -> "FA24")
                match = re.search(r'\.([A-Z]{2}\d{2})$', key)
                value = match.group(1) if match else "Unknown"
            else:
                value = str(instance.get(sep_key, "Unknown"))
            group_parts.append(value)
        group_name = ", ".join(group_parts)
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(instance)

    return groups

def process_analysis_request(all_course_data: dict, params: dict) -> dict:
def process_analysis_request(all_course_data: dict, params: dict, primary_course_code: str = None) -> dict:
    """
    Main function to process an analysis request.

    Args:
        all_course_data (dict): The complete, raw data for a course from data.json.
        params (dict): A dictionary of analysis parameters from the API request.
                       - 'filters': {'min_year', 'max_year', 'seasons', 'instructors'}
                       - 'separation_keys': list of keys, e.g. ['instructor', 'year']
                         (backward compatible with 'separation_key': str)
                       - 'stats_to_calculate': list of frequency keys
        primary_course_code (str, optional): The base code for grouping analysis.

    Returns:
        A dictionary containing the results of the analysis, structured by group,
        plus course metadata including current and former course names,
        and course grouping metadata.
    """
    filters = params.get('filters', {})
    separation_keys = params.get('separation_keys')
    # Backward compatibility: accept 'separation_key' as string
    if separation_keys is None:
        separation_keys = params.get('separation_key')
    
    # Handle both old format (stats_to_calculate) and new format (stats object)
    stats_to_calculate = params.get('stats_to_calculate')
    if stats_to_calculate is None:
        # New format: Always calculate ALL statistics regardless of selection
        # The frontend will handle which ones to display
        stats_dict = params.get('stats', {})
        if stats_dict:
            # Create mapping from frontend keys to backend keys
            frontend_to_backend = {
                'overall_quality': 'overall_quality_frequency',
                'instructor_effectiveness': 'instructor_effectiveness_frequency',
                'intellectual_challenge': 'intellectual_challenge_frequency',
                'workload': 'workload_frequency',
                'feedback_frequency': 'feedback_frequency',
                'ta_frequency': 'ta_frequency',
                'periods_course_has_been_run': 'periods_course_has_been_run'
            }
            # Always calculate all available stats using frontend keys
            stats_to_calculate = list(frontend_to_backend.keys())
        else:
            # Fallback: use all available frontend keys
            stats_to_calculate = [
                'overall_quality', 'instructor_effectiveness', 'intellectual_challenge',
                'workload', 'feedback_frequency', 'ta_frequency',
                'periods_course_has_been_run'
            ]

    # 1. Filter the data
    filtered_data = filter_instances(all_course_data, filters)

    # 2. Extract course name information and merge with metadata.json
    course_names = {}
    course_code = None # Assuming all instances in all_course_data belong to the same course code
    for instance_key, instance_data in all_course_data.items():
        if 'course_name' in instance_data:
            course_names[instance_key] = instance_data['course_name']
        # Extract course code from the first instance key
        if course_code is None:
            match = re.match(r'([A-Z]+\.\d+\.\d+)', instance_key)
            if match:
                course_code = match.group(1)

    # Load metadata from metadata.json
    metadata_from_file = {}
    try:
        with open('metadata.json', 'r') as f:
            metadata_from_file = json.load(f)
    except FileNotFoundError:
        print("metadata.json not found. Proceeding without it.")
    except json.JSONDecodeError:
        print("Error decoding metadata.json. Proceeding without it.")

    # 2.5. Get grouping info if grouping
    grouping_metadata = {
        "grouped_courses": [],
        "group_description": "",
        "is_grouped": False
    }
    if primary_course_code:
        group_info = grouping_service.get_group_info(primary_course_code)
        if group_info:
            grouping_metadata = {
                "grouped_courses": group_info.get("courses", []),
                "group_description": group_info.get("description", ""),
                "is_grouped": True
            }

    # Find the most recent course name and collect former names, merging with metadata from file
    course_metadata = extract_course_metadata(
        course_names, course_code, metadata_from_file, primary_course_code=primary_course_code
    )

    # 3. Separate the filtered data into groups
    separated_groups = separate_instances(filtered_data, separation_keys)

    # 4. Calculate statistics for each group
    # Map stats_to_calculate to data keys (statKey → statKey + "_frequency", except special keys)
    stats_backend_keys = []
    statkey_reverse_map = {}  # For mapping backend key to frontend/UI key
    for s in stats_to_calculate:
        if s == "periods_course_has_been_run":
            stats_backend_keys.append(s)
            statkey_reverse_map[s] = s
        else:
            backend_key = s + "_frequency"
            stats_backend_keys.append(backend_key)
            statkey_reverse_map[backend_key] = s

    analysis_results = {}
    for group_name, instances in separated_groups.items():
        # Patch: Special stats (feedback_frequency, ta_frequency) use the raw key from the UI/config, not "_frequency"
        backend_keys_fixed = []
        statkey_reverse_map_fixed = {}
        for frontend_key in stats_to_calculate:
            if frontend_key in ["feedback_frequency", "ta_frequency", "periods_course_has_been_run"]:
                backend_key = frontend_key
            elif frontend_key.endswith("_frequency"):
                backend_key = frontend_key
            else:
                backend_key = frontend_key + "_frequency"
            backend_keys_fixed.append(backend_key)
            statkey_reverse_map_fixed[backend_key] = frontend_key

        # Extract instance keys from the filtered data for this group
        group_instance_keys = []
        for instance_key, instance_data in filtered_data.items():
            if instance_data in instances:
                group_instance_keys.append(instance_key)

        backend_result = calculate_group_statistics(
            instances, backend_keys_fixed, course_metadata, group_instance_keys
        )
        # Convert backend keys back to frontend keys
        analysis_results[group_name] = {
            statkey_reverse_map_fixed[k]: v
            for k, v in backend_result.items()
            if k in statkey_reverse_map_fixed
        }

    # 5. Add course metadata to results
    analysis_results.update(course_metadata)

    # 6. Add grouping metadata to results
    analysis_results["grouping_metadata"] = grouping_metadata

    return analysis_results


if __name__ == '__main__':
    # Example usage
    dummy_instances = {
        "AS.100.101.01.FA22": {
            "instructor_name": "Alice",
            "overall_quality_frequency": {"Good": 10, "Excellent": 20},
            "workload_frequency": {"Typical": 15, "Somewhat heavier": 5}
        },
        "AS.100.101.01.SP23": {
            "instructor_name": "Alice",
            "overall_quality_frequency": {"Satisfactory": 5, "Good": 15},
            "workload_frequency": {"Somewhat lighter": 10, "Typical": 10}
        },
        "AS.100.101.01.FA23": {
            "instructor_name": "Bob",
            "overall_quality_frequency": {"Excellent": 25},
            "workload_frequency": {"Typical": 20}
        }
    }
    
    print("--- Test Case 1: No filtering, separate by instructor ---")
    params1 = {
        "filters": {},
        "separation_key": "instructor",
        "stats_to_calculate": ["overall_quality_frequency"]
    }
    results1 = process_analysis_request(dummy_instances, params1)
    print(results1)
    # Expected: {'Alice': {'overall_quality': 4.3}, 'Bob': {'overall_quality': 5.0}}

    print("\n--- Test Case 2: Filter by year (2023), no separation ---")
    params2 = {
        "filters": {"min_year": 2023, "max_year": 2023},
        "separation_key": None,
        "stats_to_calculate": ["overall_quality_frequency", "workload_frequency"]
    }
    results2 = process_analysis_request(dummy_instances, params2)
    print(results2)
    # Expected: {'All Data': {'overall_quality': 4.38, 'workload': 2.5}}
    