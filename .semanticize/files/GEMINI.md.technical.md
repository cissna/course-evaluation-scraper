# Technical Documentation for GEMINI.md

This document provides a detailed technical breakdown of the system architecture described in `GEMINI.md` for the JHU Course Evaluation Analyzer.

## 1. Project Overview

This section outlines the high-level architecture of a full-stack web application. The system's primary function is to scrape, store, analyze, and display course evaluation data from Johns Hopkins University. A key architectural evolution is its migration from a local, file-based proof-of-concept to a scalable, cloud-native application.

### 1.1. Core Components

-   **Backend (Python/Flask)**: This component acts as a service layer or data gateway. Its responsibilities are narrowly defined and do not include business logic for data analysis.
    -   **Scraping**: It performs on-demand data extraction from the JHU course evaluation website. This implies a web scraping module that can navigate the target site and parse HTML or other data formats.
    -   **Data Persistence**: It interfaces with a Supabase PostgreSQL database to perform CRUD (Create, Read, Update, Delete) operations on course and metadata records.
    -   **Data Aggregation**: It provides an endpoint to gather all raw data for a course and its cross-listed equivalents based on a predefined grouping logic.

-   **Frontend (React)**: A Single-Page Application (SPA) that serves as the primary user interface and contains the bulk of the application's business logic.
    -   **Data Interaction**: Provides UI elements for searching, filtering, and viewing evaluation data.
    -   **Client-Side Analysis**: It is explicitly responsible for all data processing. It receives raw JSON data from the backend and uses a dedicated JavaScript module (`analysisEngine.js`) to perform statistical calculations, filtering by various criteria (e.g., year, instructor), and data separation for display purposes. This offloads computational work from the server to the client's browser.
    -   **Local Storage**: Implements a `SearchHistory` feature by persisting recent user searches in the browser's `localStorage`.

-   **Database (PostgreSQL on Supabase)**: A cloud-hosted relational database that serves as the single source of truth for all scraped data.

## 2. Architecture

The project is structured as a monorepo, which simplifies development and deployment by keeping all related code in a single repository.

-   `backend/`: Contains the Python/Flask source code for the API.
-   `frontend/`: Contains the React source code for the SPA.
-   `vercel.json`: A configuration file that defines the deployment and routing rules for the Vercel platform.

### 2.1. Data Model (Supabase/PostgreSQL)

The database schema, defined in `db_schema.sql`, consists of two primary tables. The use of `created_at` and `updated_at` timestamps is a standard practice for tracking data lifecycle.

-   **`course_metadata` Table**: This table stores high-level, persistent information about each unique course, abstracting away from specific instances (i.e., semester/instructor).
    -   `course_code` (TEXT, Primary Key): The unique identifier for a course (e.g., `AS.180.101`).
    -   `last_period_gathered` (TEXT): The most recent academic term (e.g., "FA23") for which data was successfully scraped. Used to determine if a new scrape is needed.
    -   `last_period_failed` (BOOLEAN): A flag to indicate if the last attempt to scrape a *new* period failed. This can be used for retry logic or to alert administrators.
    -   `relevant_periods` (JSONB): A JSON array storing all academic periods for which this course has evaluation data. JSONB is an efficient binary format for storing and querying JSON.
    -   `last_scrape_during_grace_period` (DATE): Tracks the last time a scrape was attempted during a "grace period" (a window when new evaluations might be released but are not yet available). This prevents excessive scraping.
    -   `created_at` / `updated_at` (TIMESTAMPTZ): Automatically managed timestamps for record creation and modification.

-   **`courses` Table**: This table stores the raw scraped data for each specific offering of a course.
    -   `instance_key` (TEXT, Primary Key): A composite-like unique key for a specific course instance, likely combining `course_code` and the academic period (e.g., `AS.180.101_FA23`).
    -   `course_code` (TEXT, Foreign Key): Links the instance back to the `course_metadata` table.
    -   `data` (JSONB): The complete, raw evaluation data for that instance, stored in a flexible JSON structure. This allows the data format to evolve without requiring schema migrations.
    -   `created_at` / `updated_at` (TIMESTAMPTZ): Timestamps for record management.

-   **`trigger_set_timestamp` Trigger**: A PostgreSQL database trigger that executes a function (`set_timestamp()`) before any `UPDATE` operation on a row. This function automatically sets the `updated_at` column to the current time, ensuring data freshness is always tracked at the database level.

### 2.2. Backend (Flask)

The backend is a lightweight Flask application. The `CourseGroupingService` mentioned uses an "embedded configuration," which implies a hardcoded or file-based mapping (e.g., a Python dictionary or a JSON file) to identify cross-listed courses, rather than a dynamic database-driven approach.

### 2.3. Frontend (React)

The frontend architecture places all analytical logic on the client.
-   `src/utils/analysisEngine.js`: This is the core of the client-side logic. It likely contains functions that take the raw JSON from the `/api/analyze` endpoint and perform operations like:
    -   Filtering the data based on user-selected criteria.
    -   Grouping data by instructor or semester.
    -   Calculating statistical metrics (mean, median, standard deviation) for ratings.
-   `storageUtils.js`: A utility module that abstracts interactions with the browser's `localStorage` API, providing a clean interface for the `SearchHistory` component to read and write search terms.

### 2.4. Deployment (Vercel)

The `vercel.json` file orchestrates the deployment of the monorepo.
-   **Builds**: Vercel is configured to run two separate build processes:
    1.  `@vercel/python`: This builder takes the Flask application defined in `backend/app.py` and deploys it as a serverless function.
    2.  `@vercel/static-build`: This builder executes the `npm run build` command defined in `frontend/package.json`. The output, a set of static HTML, CSS, and JS files in the `frontend/build` directory, is then served by Vercel's CDN.
-   **Routing**: The routing configuration is critical for a monorepo setup.
    -   `"source": "/api/(.*)", "destination": "/backend/app.py"`: This rule acts as a reverse proxy. All incoming requests to the `/api/` path are forwarded to the backend Python serverless function.
    -   Static file routes (`/static/*`, `/favicon.ico`, etc.): These rules ensure that requests for static assets are served directly from the `frontend/build` directory.
    -   Fallback route: All other requests are rewritten to `/frontend/index.html`. This is the standard pattern for a SPA, allowing React Router (or a similar library) to handle client-side navigation.
-   **CORS (Cross-Origin Resource Sharing)**: The Flask backend is configured to accept requests from specific origins. The use of a regular expression for Vercel preview URLs is a robust method to automatically allow CORS for dynamically generated deployment previews (e.g., `my-app-git-my-branch-username.vercel.app`).

### 2.5. Environment Variables

-   `DATABASE_URL`: A single, critical environment variable containing the full connection string for the Supabase PostgreSQL database. This string includes the username, password, host, port, and database name, and must be kept secret.

## 3. Local Development

This section provides standard setup instructions for a bifurcated full-stack project.
-   **Backend**: Requires Python, `pip` for dependency management (`requirements.txt`), and a `.env` file to load the `DATABASE_URL` locally using a library like `python-dotenv`.
-   **Frontend**: Requires Node.js and `npm` for dependency management (`package.json`). The `npm start` command runs a local development server with features like hot-reloading.

## 4. API Endpoints

The backend exposes a RESTful API with a `/api/` prefix. All endpoints that accept a `course_code` perform validation against a `XX.###.###` format.

-   **`GET /api/course/<course_code>`**
    -   **Parameter**: `course_code` (string) - The course to retrieve.
    -   **Functionality**: Fetches all evaluation data for a specific course. It includes logic to check if the data is "stale" (e.g., based on `last_period_gathered`) and triggers a new scrape if necessary.

-   **`GET /api/search/course_name/<query>`**
    -   **Parameter**: `query` (string) - The search term for a course name.
    -   **Functionality**: Performs a search against the database (likely the `course_metadata` table) for courses matching the query.

-   **`GET /api/search/instructor/<name>`**
    -   **Parameter**: `name` (string) - The last name of an instructor.
    -   **Functionality**: Searches for all known variations of an instructor's name. This suggests that the backend may have logic to handle different name formats found during scraping.

-   **`GET /api/grace-status/<course_code>`**
    -   **Parameter**: `course_code` (string) - The course to check.
    -   **Functionality**: Checks the `last_scrape_during_grace_period` field to determine if a recent scrape attempt was made during a period where evaluations might not have been fully released.

-   **`POST /api/recheck/<course_code>`**
    -   **Parameter**: `course_code` (string) - The course to re-scrape.
    -   **Functionality**: Forces a new scrape for the course, bypassing the "grace period" logic. This is useful for manual data refreshes.

-   **`POST /api/analyze/<course_code>`**
    -   **Parameter**: `course_code` (string) - The primary course for analysis.
    -   **Functionality**: This is the main data-gathering endpoint for the frontend. It identifies all courses in the requested course's group (including cross-listings), fetches all their raw evaluation data from the `courses` table, and returns a single, large `raw_data` object.
    -   **Return Value**: A JSON object of the form `{ "raw_data": [...] }`, where the array contains the complete data for all relevant course instances. The client is responsible for all subsequent processing.