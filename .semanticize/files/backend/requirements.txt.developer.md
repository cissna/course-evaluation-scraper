# Backend Dependencies (`requirements.txt`)

This file lists the Python packages required for the backend server. These dependencies provide the core framework for the web server, database connection, web scraping, and utility functions.

### Framework & Server

-   **Flask**: A lightweight web framework used to build the backend REST API. It handles routing, request handling, and responses.
-   **Flask-Cors**: An extension for Flask that handles Cross-Origin Resource Sharing (CORS). This is essential for allowing the React frontend (running on a different domain/port) to communicate with the backend API.
-   **gunicorn**: A production-ready WSGI HTTP server for UNIX. It's used to run the Flask application in a more robust and scalable way than the built-in development server.

### Data Scraping & Parsing

-   **requests**: A simple and elegant HTTP library used to make requests to the JHU course evaluation website to fetch the raw HTML content for scraping.
-   **beautifulsoup4**: A library for pulling data out of HTML and XML files. It's used to parse the HTML content retrieved by `requests` and extract the relevant course evaluation data.

### Database

-   **psycopg2-binary**: The most popular PostgreSQL database adapter for Python. It is used to connect to and interact with the Supabase (PostgreSQL) database, executing queries to store and retrieve course data and metadata.

### Utilities

-   **python-dateutil**: Provides powerful extensions to the standard `datetime` module. It is likely used for parsing, manipulating, and comparing dates, which is crucial for handling academic periods and scrape timestamps.
-   **python-dotenv**: A utility to load environment variables from a `.env` file into the application's environment. This is used in local development to securely manage the `DATABASE_URL` without hardcoding it.