from flask import Flask, jsonify, request
from flask_cors import CORS
import re
from urllib.parse import unquote
from .scraper_service import get_course_data_and_update_cache, find_courses_by_name, find_courses_by_name_with_details, force_recheck_course, get_course_grace_status
from .db_utils import find_instructor_variants_db, find_professors_by_name_db, get_percentile_benchmark
from .result_service import cached_course_result, cached_professor_result, refresh_course, course_refresh_status
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

@app.route('/api/search')
def search_all():
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    course_offset = request.args.get('course_offset', 0, type=int)
    professor_offset = request.args.get('professor_offset', 0, type=int)
    if not query or len(query) > 1000:
        return jsonify({'error': 'Enter a search of 1 to 1000 characters.'}), 400
    if limit is None or not 1 <= limit <= 100 or min(course_offset, professor_offset) < 0:
        return jsonify({'error': 'Invalid pagination parameters.'}), 400
    try:
        return jsonify({
            'courses': find_courses_by_name_with_details(query, limit, course_offset),
            'professors': find_professors_by_name_db(query, limit, professor_offset),
        })
    except Exception:
        app.logger.exception('Combined search failed')
        return jsonify({'error': 'An internal server error occurred during search.'}), 500


@app.route('/api/professor')
def professor_result():
    name = request.args.get('name', '')
    if not name or len(name) > 1000:
        return jsonify({'error': 'Invalid professor name.'}), 400
    try:
        result = cached_professor_result(name)
        if not result['raw_data']['instances']:
            return jsonify({'error': 'No evaluations found for this professor.'}), 404
        return jsonify(result)
    except Exception:
        app.logger.exception('Professor lookup failed')
        return jsonify({'error': 'An internal server error occurred during professor lookup.'}), 500


@app.route('/api/analyze/<string:course_code>', methods=['POST'])
def analyze_course_data(course_code):
    # Cached reads never start a scraper. The tab explicitly requests a refresh.
    if not validate_course_code(course_code):
        return jsonify({'error': 'Invalid course code format. Expected format: XX.###.###'}), 400
    try:
        result = cached_course_result(course_code.upper())
        if not result['raw_data']['instances'] and not any(
            c['needs_refresh'] or c['in_progress'] for c in result['refresh']['courses']
        ):
            return jsonify({'error': 'No data found for this course.'}), 404
        return jsonify(result)
    except Exception:
        app.logger.exception('Cached course lookup failed')
        return jsonify({'error': 'An internal server error occurred during analysis.'}), 500


@app.route('/api/recheck/<string:course_code>', methods=['POST'])
@app.route('/api/refresh/<string:course_code>', methods=['POST'])
def refresh_course_data(course_code):
    if not validate_course_code(course_code):
        return jsonify({'error': 'Invalid course code format. Expected format: XX.###.###'}), 400
    try:
        payload, status = refresh_course(course_code.upper(), force=request.path.startswith('/api/recheck/'))
        return jsonify(payload), status
    except Exception:
        app.logger.exception('Refresh failed')
        return jsonify({'error': 'Unable to check for new evaluations. Please try again.'}), 500


@app.route('/api/refresh-status/<string:course_code>')
def refresh_status(course_code):
    if not validate_course_code(course_code):
        return jsonify({'error': 'Invalid course code format. Expected format: XX.###.###'}), 400
    try:
        return jsonify(course_refresh_status(course_code.upper()))
    except Exception:
        app.logger.exception('Refresh status failed')
        return jsonify({'error': 'Unable to check refresh status.'}), 500


@app.route('/api/percentiles')
def percentile_benchmark():
    try:
        return jsonify({'benchmark': get_percentile_benchmark()})
    except Exception:
        app.logger.exception('Benchmark lookup failed')
        return jsonify({'benchmark': None, 'reason': 'The percentile benchmark is not available.'}), 503


if __name__ == '__main__':
    app.run(debug=True)
