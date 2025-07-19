import re
from datetime import date

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
    )
}

# --- Core Calculation Functions ---

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

def calculate_group_statistics(course_instances: list, stats_to_calculate: list) -> dict:
    """
    Calculates aggregated statistics for a group of course instances.
    
    Args:
        course_instances (list): A list of course data dictionaries.
        stats_to_calculate (list): A list of frequency keys to be calculated (e.g., ["overall_quality_frequency"]).

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
        avg = calculate_weighted_average(aggregated_frequencies[key], value_mapping)
        results[ui_name.replace(" ", "_").lower()] = avg # e.g., "overall_quality"
        
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

def filter_instances(all_instances: dict, filters: dict) -> dict:
    """Filters course instances based on a set of criteria."""
    filtered = {}
    
    min_year = filters.get('min_year')
    max_year = filters.get('max_year')
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

def separate_instances(instances: dict, separation_key: str) -> dict:
    """Separates instances into groups based on a given key."""
    if not separation_key:
        return {"All Data": list(instances.values())}

    groups = {}
    for key, instance in instances.items():
        group_name = "Unknown"
        if separation_key == 'instructor':
            group_name = instance.get('instructor_name', 'Unknown')
        elif separation_key == 'year':
            group_name = str(get_instance_year(key))
        elif separation_key == 'season':
            group_name = get_instance_season(key)
        
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(instance)
        
    return groups

def process_analysis_request(all_course_data: dict, params: dict) -> dict:
    """
    Main function to process an analysis request.
    
    Args:
        all_course_data (dict): The complete, raw data for a course from data.json.
        params (dict): A dictionary of analysis parameters from the API request.
                       - 'filters': {'min_year', 'max_year', 'seasons', 'instructors'}
                       - 'separation_key': 'instructor', 'year', or 'season'
                       - 'stats_to_calculate': list of frequency keys
    
    Returns:
        A dictionary containing the results of the analysis, structured by group.
    """
    filters = params.get('filters', {})
    separation_key = params.get('separation_key')
    stats_to_calculate = params.get('stats_to_calculate', list(STAT_MAPPINGS.keys()))

    # 1. Filter the data
    filtered_data = filter_instances(all_course_data, filters)
    
    # 2. Separate the filtered data into groups
    separated_groups = separate_instances(filtered_data, separation_key)
    
    # 3. Calculate statistics for each group
    analysis_results = {}
    for group_name, instances in separated_groups.items():
        analysis_results[group_name] = calculate_group_statistics(instances, stats_to_calculate)
        
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