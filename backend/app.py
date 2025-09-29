from flask import Flask, jsonify, request
from flask_cors import CORS
import re
import json
from urllib.parse import unquote
from .scraper_service import get_course_data_and_update_cache, find_courses_by_name, find_courses_by_name_with_details, force_recheck_course, get_course_grace_status
from .db_utils import find_instructor_variants_db
from .analysis import process_analysis_request, extract_course_metadata
from .course_grouping_service import CourseGroupingService

app = Flask(__name__, static_folder='../static', static_url_path='/')

def validate_course_code(course_code):
    """
    Validate that a course code matches the expected format: XX.###.###
    Returns True if valid, False otherwise.
    """
    if not course_code or len(course_code) > 50:  # Prevent extremely long strings
        return False
    # Pattern: 2 letters, dot, 3 digits, dot, 3 digits (case insensitive)
    pattern = r'^[A-Za-z]{2}\.\d{3}\.\d{3}$'
    return bool(re.match(pattern, course_code))

# Define allowed origins for CORS, including a regex for Vercel preview deployments.
# This is compatible with Flask-Cors >= 4.0.
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:5000",
    "https://course-evaluation-scraper.vercel.app",
    re.compile(r"^https://course-evaluation-scraper-[a-z0-9]+-[a-z0-9-]+\.vercel\.app$")
]
CORS(app, origins=allowed_origins)  # Enable Cross-Origin Resource Sharing

grouping_service = CourseGroupingService()

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/api/course/<string:course_code>')
def get_course_data(course_code):
    """
    API endpoint to get course evaluation data.
    It triggers the scraper if the data is not up-to-date in the cache.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    print(f"Received request for course code: {course_code}")
    try:
        # Call the centralized scraping and caching logic
        data = get_course_data_and_update_cache(course_code)
        if not data:
            return jsonify({"error": "No data found for this course."}), 404
        # Check if the response contains an error
        if isinstance(data, dict) and "error" in data:
            return jsonify(data), 500
        return jsonify(data)
    except Exception as e:
        # Log the exception for debugging
        print(f"An error occurred: {e}")
        # Return a generic error message to the client
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/search/course_name/<string:search_query>')
def search_by_course_name(search_query):
    """
    API endpoint to search for courses by name.
    """
    # URL-decode the search query in case it's not automatically decoded
    search_query = unquote(search_query)

    # Prevent extremely long search queries that could cause performance issues
    if len(search_query) > 1000:
        return jsonify({"error": "Search query too long. Maximum 1000 characters allowed."}), 400

    print(f"Received search request for: {search_query}")
    try:
        course_codes = find_courses_by_name(search_query)
        return jsonify(course_codes)
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({"error": "An internal server error occurred during search."}), 500

@app.route('/api/search/course_name_detailed/<string:search_query>')
def search_by_course_name_detailed(search_query):
    """
    API endpoint to search for courses by name with detailed results including course names.
    Supports pagination via query parameters: limit and offset.
    """
    # URL-decode the search query in case it's not automatically decoded
    search_query = unquote(search_query)

    # Prevent extremely long search queries that could cause performance issues
    if len(search_query) > 1000:
        return jsonify({"error": "Search query too long. Maximum 1000 characters allowed."}), 400

    # Get pagination parameters
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)

    # Validate pagination parameters
    if limit is not None and (limit <= 0 or limit > 100):
        return jsonify({"error": "Limit must be between 1 and 100."}), 400
    if offset < 0:
        return jsonify({"error": "Offset must be non-negative."}), 400

    print(f"Received detailed search request for: {search_query} (limit={limit}, offset={offset})")
    try:
        results = find_courses_by_name_with_details(search_query, limit, offset)
        return jsonify(results)
    except Exception as e:
        print(f"An error occurred during detailed search: {e}")
        return jsonify({"error": "An internal server error occurred during search."}), 500

@app.route('/api/search/instructor/<string:instructor_name>')
def search_by_instructor_name(instructor_name):
    """
    API endpoint to find variations of an instructor's name.
    """
    # URL-decode the instructor name in case it's not automatically decoded
    instructor_name = unquote(instructor_name)

    # Prevent extremely long instructor names that could cause performance issues
    if len(instructor_name) > 1000:
        return jsonify({"error": "Instructor name too long. Maximum 1000 characters allowed."}), 400

    print(f"Received instructor search for: {instructor_name}")
    try:
        variants = find_instructor_variants_db(instructor_name)
        return jsonify(variants)
    except Exception as e:
        print(f"An error occurred during instructor search: {e}")
        return jsonify({"error": "An internal server error occurred during instructor search."}), 500

@app.route('/api/grace-status/<string:course_code>')
def get_grace_status(course_code):
    """
    API endpoint to check if a course needs grace period warning.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    try:
        status = get_course_grace_status(course_code)
        return jsonify(status)
    except Exception as e:
        print(f"An error occurred checking grace status: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/recheck/<string:course_code>', methods=['POST'])
def recheck_course_data(course_code):
    """
    API endpoint to force recheck course data during grace periods.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    print(f"Received force recheck request for course: {course_code}")
    try:
        data = force_recheck_course(course_code)
        if not data:
            return jsonify({"error": "No data found for this course."}), 404
        # Check if the response contains an error
        if isinstance(data, dict) and "error" in data:
            return jsonify(data), 500
        return jsonify(data)
    except Exception as e:
        print(f"An error occurred during recheck: {e}")
        return jsonify({"error": "An internal server error occurred during recheck."}), 500

@app.route('/api/analyze/<string:course_code>', methods=['POST'])
def analyze_course_data(course_code):
    """
    API endpoint to perform filtering and separation analysis on course data.
    Modified to support raw data mode for frontend processing.
    """
    # Validate course code format
    if not validate_course_code(course_code):
        return jsonify({"error": "Invalid course code format. Expected format: XX.###.###"}), 400

    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    print(f"Received analysis request for course: {course_code}")
    try:
        # Get the analysis parameters from the request body
        analysis_params = request.get_json()
        if not analysis_params:
            return jsonify({"error": "Missing analysis parameters in request body."}), 400

        # This is now the only data path.
        # Get all the data for the course
        all_course_data = get_course_data_and_update_cache(course_code)

        # If no data, check for groupings before returning an error
        if not all_course_data:
            group_info = grouping_service.get_group_info(course_code)
            if not group_info or not group_info.get("courses"):
                return jsonify({"error": "No data found for this course."}), 404
        
        # Get metadata
        metadata_from_file = {}
        try:
            with open('metadata.json', 'r') as f:
                metadata_from_file = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Get grouping info
        group_info = grouping_service.get_group_info(course_code)
        grouped_courses = []
        all_instances = {}
        
        if group_info and group_info.get("courses"):
            grouped_courses = group_info["courses"]
            
            # Add main course data
            if all_course_data:
                all_instances.update(all_course_data)
            
            # Fetch data for all grouped courses
            for grouped_code in grouped_courses:
                if grouped_code != course_code:
                    try:
                        grouped_data = get_course_data_and_update_cache(grouped_code)
                        if grouped_data and isinstance(grouped_data, dict):
                            # Add course_code field to each instance for separation
                            for instance_key, instance_data in grouped_data.items():
                                if isinstance(instance_data, dict):
                                    instance_data_with_code = instance_data.copy()
                                    instance_data_with_code['course_code'] = grouped_code
                                    all_instances[f"{grouped_code}_{instance_key}"] = instance_data_with_code
                    except Exception as e:
                        print(f"Warning: Could not load grouped course {grouped_code}: {e}")
        else:
            # No grouping, just use the main course data
            if all_course_data:
                all_instances.update(all_course_data)
        
        # Extract course names for metadata
        course_names = {}
        for instance_key, instance_data in all_instances.items():
            if 'course_name' in instance_data:
                course_names[instance_key] = instance_data['course_name']
        
        # Get course metadata
        course_metadata = extract_course_metadata(
            course_names, 
            course_code, 
            metadata_from_file,
            primary_course_code=course_code,
            primary_course_has_no_data=not all_course_data
        )
        
        # Return raw data structure
        return jsonify({
            "raw_data": {
                "instances": all_instances,
                "metadata": {
                    "current_name": course_metadata.get("current_name"),
                    "former_names": course_metadata.get("former_names", []),
                    **{k: v for k, v in course_metadata.items() 
                       if k not in ["current_name", "former_names"]}
                },
                "grouping_metadata": {
                    "grouped_courses": grouped_courses,
                    "group_description": group_info.get("description", "") if group_info else "",
                    "is_grouped": bool(grouped_courses and len(grouped_courses) > 1)
                }
            }
        })

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return jsonify({"error": "An internal server error occurred during analysis."}), 500

if __name__ == '__main__':
    app.run(debug=True)
