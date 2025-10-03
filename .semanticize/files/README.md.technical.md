# Technical Documentation for README.md

This document provides a detailed technical breakdown of the `README.md` file for the JHU Course Evaluation Analyzer project. It is intended for engineers who need to understand the project's setup, architecture, and operation.

## 1. Project Overview

The `README.md` introduces a full-stack web application.

-   **Tech Stack**:
    -   **Backend**: A Python server using the Flask framework. It serves a RESTful API.
    -   **Frontend**: A JavaScript-based single-page application (SPA) built with the React library.
    -   **Database**: A PostgreSQL database hosted on the Supabase platform. This replaces a legacy file-based (`.json`) storage system.
    -   **Deployment**: The entire monorepo is deployed and hosted on Vercel.
-   **Public Access**: The application is live and can be accessed at `https://course-evaluation-scraper.vercel.app`.

## 2. Features

This section outlines the core functionalities of the application.

-   **Course Evaluation Scraping**: This is an on-demand server-side process. When the frontend requests data for a course that is either not in the database or is considered stale, the Flask backend triggers a scraping module. This module makes HTTP requests to the JHU course evaluation website, parses the HTML response, and extracts the relevant data.
-   **Data Analysis**: This functionality allows users to filter and segment the displayed data. The filtering logic (e.g., by academic year, semester, or instructor) is implemented entirely on the client-side within the React application. The backend provides raw, unfiltered data for a given course and its cross-listed counterparts.
-   **Search History**: This is a client-side feature. The React application captures user search queries and stores them in the browser's `localStorage`. This allows for a persistent search history on the user's machine.
-   **Cross-listed Course Grouping**: This is a backend feature. The Flask server contains a service that understands the relationships between different course codes that are cross-listed (e.g., the same course offered by different departments). When data for one course is requested, the backend aggregates data from all courses in its group before returning the payload to the frontend.

## 3. Architecture

This section describes the high-level structure of the project.

-   **Monorepo**: The project is contained within a single repository, with two primary subdirectories:
    -   `backend/`: Contains the Python/Flask source code.
    -   `frontend/`: Contains the React source code.
-   **Client-Server Model**: The system follows a standard client-server architecture. The React frontend acts as the client, making API calls to the Flask backend to fetch data. The backend communicates with the Supabase database to store and retrieve information.
-   **Database**: The database schema is defined in `db_schema.sql` and consists of two main tables: `course_metadata` and `courses`. The backend connects to this database using a standard PostgreSQL connection string.

## 4. Local Development

This section provides instructions for setting up a local development environment.

-   **Database Prerequisite**: A running Supabase PostgreSQL instance is a hard requirement. The legacy system of using local `.json` files for data storage is deprecated.
-   **Database Seeding**: The `one-time-scripts/` directory contains helper scripts for database management:
    -   `db_setup.py`: Likely initializes the database schema based on `db_schema.sql`.
    -   `migrate_data.py`: Migrates data from the old `.json` files into the new Supabase database structure.
    -   `export_data.py`: Exports data from the Supabase database back into `.json` files, useful for backups or sharing.

### 4.1. Backend Setup (Flask)

1.  **Environment Configuration**: A `.env` file must be created in the project's root directory. This file stores environment variables.
    -   `DATABASE_URL`: This variable must contain the full connection string for the Supabase PostgreSQL database. The Flask application reads this variable to establish a database connection.
2.  **Dependency Installation**: The command `pip install -r backend/requirements.txt` uses Python's package manager, `pip`, to install all server-side dependencies listed in the `requirements.txt` file located in the `backend` directory.
3.  **Server Execution**: The command `python3 backend/app.py` starts the Flask development server. By default, it listens for HTTP requests on `http://127.0.0.1:5000`.

### 4.2. Frontend Setup (React)

1.  **Directory Navigation**: The `cd frontend` command changes the current working directory to `frontend/`.
2.  **Dependency Installation**: The command `npm install` uses the Node Package Manager to download and install all frontend dependencies defined in `frontend/package.json` and `frontend/package-lock.json` into a `node_modules` directory.
3.  **Server Execution**: The command `npm start` runs the React development server (often using a tool like `react-scripts`). This compiles the React code, starts a server (typically on `http://localhost:3000`), and opens the application in the default web browser. It also enables hot-reloading for development.

## 5. How to Use

This section describes the application's user flow from a functional perspective.

1.  **Access**: The user navigates to the application's URL.
2.  **Search**: The user inputs a query into the search bar. The React frontend captures this input.
3.  **Search History**: A dropdown displays previous searches retrieved from `localStorage`.
4.  **Data Fetching**: Upon clicking "Search," the React app sends a `POST` request to the `/api/analyze/<course_code>` endpoint on the Flask backend. The backend then scrapes or retrieves data from the database and returns it as a JSON payload.
5.  **Client-Side Analysis**: The frontend processes the raw data. Users can manipulate the view using UI controls, which triggers client-side filtering and re-rendering of the data components.
6.  **Data Export**: A "Download as CSV" button triggers a function in the React app that converts the currently displayed (and filtered) data into a CSV format and initiates a browser download.

## 6. Deployment

This section explains the production deployment strategy.

-   **Platform**: The application is deployed on Vercel, a cloud platform specializing in hosting frontend frameworks and serverless functions.
-   **Configuration**: The `vercel.json` file at the project root is the Vercel deployment configuration file. It defines:
    -   **Builds**: It specifies how to build the different parts of the monorepo. This includes a Python build for the Flask API (`backend/app.py`) and a static-site build for the React application (`npm run build` in the `frontend` directory).
    -   **Routing**: It contains rules that direct incoming requests.
        -   API requests (e.g., `/api/*`) are rewritten and proxied to the serverless function running the Flask app.
        -   Other requests are typically routed to serve the static assets (HTML, CSS, JS) from the React build output, enabling the single-page application to handle its own routing on the client side.