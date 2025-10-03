# Technical Documentation for `backend/requirements.txt`

This file lists the Python packages required for the backend application to run. These dependencies provide the core framework for the web server, database connectivity, web scraping, and utility functions.

### Dependency Breakdown

A line-by-line explanation of each dependency:

1.  **`Flask`**
    -   **Purpose**: A lightweight WSGI (Web Server Gateway Interface) web application framework. It is the foundation of the backend API.
    -   **Usage**: Flask is used to create the web server, define API routes (e.g., `/api/course/<course_code>`), handle incoming HTTP requests from the frontend, and formulate responses. It provides the routing mechanism that maps URLs to specific Python functions.

2.  **`Flask-Cors`**
    -   **Purpose**: A Flask extension for handling Cross-Origin Resource Sharing (CORS).
    -   **Usage**: Since the React frontend and the Python backend are served on different origins (e.g., `localhost:3000` and `localhost:5000` during development), the browser's same-origin policy would block API requests. `Flask-Cors` adds the necessary CORS headers (like `Access-Control-Allow-Origin`) to the backend's HTTP responses, allowing the frontend to make requests to the API without being blocked.

3.  **`requests`**
    -   **Purpose**: A simple and elegant HTTP library for Python.
    -   **Usage**: This library is used by the scraping service (`scraper_service.py`) to send HTTP GET requests to the Johns Hopkins University course evaluation website. It fetches the raw HTML content of the evaluation pages, which is then passed to BeautifulSoup for parsing.

4.  **`beautifulsoup4`**
    -   **Purpose**: A library for pulling data out of HTML and XML files.
    -   **Usage**: After the `requests` library fetches the HTML of a course evaluation page, `beautifulsoup4` is used to parse the HTML string into a navigable object tree. The scraping logic (`scraping_logic.py`) then uses BeautifulSoup's methods (e.g., `find()`, `find_all()`) to locate and extract specific data points from the HTML, such as instructor names, course titles, and evaluation scores.

5.  **`python-dateutil`**
    -   **Purpose**: Provides powerful extensions to the standard `datetime` module.
    -   **Usage**: This library is likely used for parsing, manipulating, and comparing dates and times throughout the backend. A key use case is in the `period_logic.py` module for handling academic semester codes (e.g., "FA23") and in the `scraper_service.py` for managing the "grace period" logic, which involves checking if a certain amount of time has passed since the last scrape attempt.

6.  **`gunicorn`**
    -   **Purpose**: A Python WSGI HTTP Server for UNIX.
    -   **Usage**: While Flask includes a built-in development server, it is not suitable for production. Gunicorn is a production-grade web server that runs the Flask application. It manages multiple worker processes to handle concurrent requests, providing better performance and stability. Vercel's deployment environment uses Gunicorn to serve the Python backend.

7.  **`psycopg2-binary`**
    -   **Purpose**: A PostgreSQL database adapter for Python.
    -   **Usage**: This is the driver that allows the Python application to connect to and interact with the PostgreSQL database hosted on Supabase. The `db_utils.py` module uses `psycopg2` to establish a connection using the `DATABASE_URL` environment variable and to execute SQL queries for fetching, inserting, and updating course data and metadata in the `courses` and `course_metadata` tables. The `-binary` version includes pre-compiled components, simplifying installation.

8.  **`python-dotenv`**
    -   **Purpose**: Reads key-value pairs from a `.env` file and sets them as environment variables.
    -   **Usage**: For local development, this library is used to load the `DATABASE_URL` from a `.env` file in the project root into the application's environment. This avoids hardcoding sensitive credentials in the source code, as described in the project's `README.md`. The application code can then access the database connection string as if it were a standard environment variable.