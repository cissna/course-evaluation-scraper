from flask import Flask, jsonify
from flask_cors import CORS
from flask import request
from scraper_service import get_course_data_and_update_cache, find_courses_by_name, force_recheck_course, get_course_grace_status
from similarity import find_instructor_variants
from analysis import process_analysis_request
from backend.course_grouping_service import CourseGroupingService

app = Flask(__name__, static_folder='../static', static_url_path='/')
CORS(app)  # Enable Cross-Origin Resource Sharing

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
    print(f"Received search request for: {search_query}")
    try:
        course_codes = find_courses_by_name(search_query)
        return jsonify(course_codes)
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({"error": "An internal server error occurred during search."}), 500

@app.route('/api/search/instructor/<string:instructor_name>')
def search_by_instructor_name(instructor_name):
    """
    API endpoint to find variations of an instructor's name.
    """
    print(f"Received instructor search for: {instructor_name}")
    try:
        variants = find_instructor_variants(instructor_name)
        return jsonify(variants)
    except Exception as e:
        print(f"An error occurred during instructor search: {e}")
        return jsonify({"error": "An internal server error occurred during instructor search."}), 500

@app.route('/api/grace-status/<string:course_code>')
def get_grace_status(course_code):
    """
    API endpoint to check if a course needs grace period warning.
    """
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
    """
    # Normalize course code to uppercase to match stored format
    course_code = course_code.upper()
    print(f"Received analysis request for course: {course_code}")
    try:
        # Get the analysis parameters from the request body
        analysis_params = request.get_json()
        if not analysis_params:
            return jsonify({"error": "Missing analysis parameters in request body."}), 400



        # First, get all the data for the course (from cache or by scraping)
        all_course_data = get_course_data_and_update_cache(course_code)

        # If no data, check for groupings before returning an error
        if not all_course_data:
            group_info = grouping_service.get_group_info(course_code)
            if not group_info or not group_info.get("courses"):
                return jsonify({"error": "No data found for this course."}), 404
            # If grouped, proceed with an empty dict; analysis module will fetch grouped data
            all_course_data = {}

        # Check if the response contains an error (e.g., from scraping)
        if isinstance(all_course_data, dict) and "error" in all_course_data:
            return jsonify(all_course_data), 500

        # Process the data using the analysis module
        results = process_analysis_request(all_course_data, analysis_params, primary_course_code=course_code)
        return jsonify(results)

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return jsonify({"error": "An internal server error occurred during analysis."}), 500

if __name__ == '__main__':
    app.run(debug=True)