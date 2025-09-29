import json
import re
import os
import sys

# Add the backend directory to the Python path to allow imports
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from course_grouping_service import CourseGroupingService

# Copied from analysis.py to avoid import issues
STAT_MAPPINGS = {
    "overall_quality_frequency": (
        "Overall Quality",
        {"Poor": 1, "Weak": 2, "Satisfactory": 3, "Good": 4, "Excellent": 5}
    ),
}

def calculate_detailed_statistics(frequency_dict: dict, value_mapping: dict) -> dict:
    """
    Calculates detailed statistics including mean, standard deviation, and count.
    """
    if not frequency_dict or not value_mapping:
        return {"mean": None, "std": None, "n": 0}

    # Collect all individual data points
    data_points = []
    total_responses = 0

    for response_text, count in frequency_dict.items():
        if response_text in value_mapping and count > 0:
            value = value_mapping[response_text]
            data_points.extend([value] * count)
            total_responses += count

    if total_responses == 0:
        return {"mean": None, "std": None, "n": 0}

    # Calculate mean
    mean = sum(data_points) / total_responses

    # Calculate standard deviation
    if total_responses == 1:
        std = 0.0
    else:
        variance = sum((x - mean) ** 2 for x in data_points) / (total_responses - 1)
        std = variance ** 0.5

    return {
        "mean": round(mean, 2),
        "std": round(std, 2),
        "n": total_responses
    }

def extract_base_course_code(instance_key):
    """Extract base course code from instance key, e.g., 'EN.553.421.01.FA22' -> 'EN.553.421'"""
    match = re.match(r'([A-Z]{2,}\.\d{3}\.\d{3})', instance_key)
    return match.group(1) if match else None

def main():
    # Load data.json
    with open('../data.json', 'r') as f:
        data = json.load(f)

    # Initialize grouping service
    grouping_service = CourseGroupingService()

    # Get all unique base course codes from data
    base_codes = set()
    for instance_key in data.keys():
        base_code = extract_base_course_code(instance_key)
        if base_code:
            base_codes.add(base_code)

    print(f"Found {len(base_codes)} unique base course codes in data.json")

    # For each base code, compute N for its group
    course_n = {}

    for base_code in base_codes:
        # Get grouped courses
        grouped_courses = grouping_service.get_grouped_courses(base_code)

        # Find all instances for these courses
        group_instances = []
        for instance_key, instance_data in data.items():
            instance_base = extract_base_course_code(instance_key)
            if instance_base in grouped_courses:
                group_instances.append(instance_data)

        if not group_instances:
            continue

        # Aggregate overall_quality_frequency
        aggregated_freq = {}
        for instance in group_instances:
            freq = instance.get('overall_quality_frequency', {})
            for key, count in freq.items():
                aggregated_freq[key] = aggregated_freq.get(key, 0) + count

        # Compute N
        ui_name, value_mapping = STAT_MAPPINGS['overall_quality_frequency']
        detailed_stats = calculate_detailed_statistics(aggregated_freq, value_mapping)
        n = detailed_stats['n']

        # Use the base_code as key, but if grouped, maybe use a group identifier
        if len(grouped_courses) > 1:
            group_key = f"{base_code} (group: {', '.join(sorted(grouped_courses))})"
        else:
            group_key = base_code

        course_n[group_key] = n

    # Find the top 10 courses with highest N
    if course_n:
        sorted_courses = sorted(course_n.items(), key=lambda x: x[1], reverse=True)
        print("\nTop 10 courses with highest N:")
        for i, (course, n) in enumerate(sorted_courses[:10], 1):
            print(f"{i}. {course}: N={n}")
    else:
        print("No data found")

if __name__ == '__main__':
    main()