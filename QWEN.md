QWEN.md/GEMINI.md

# JHU Course Evaluation Analyzer

## 1. Project Overview

This project is a full-stack web application designed to scrape, analyze, and display course evaluation data from Johns Hopkins University. It has been migrated from a local, file-based system to a robust, cloud-based architecture using Supabase for data storage and Vercel for deployment.

- **Backend**: A Python/Flask server that exposes a REST API. Its responsibilities have been streamlined to focus on:
    - On-demand scraping of course evaluation data from the JHU website.
    - Storing and retrieving course data and metadata from a Supabase (PostgreSQL) database.
    - Aggregating raw data for a course and all courses in its logical group (e.g., cross-listed courses).

- **Frontend**: A single-page application (SPA) built with React. It provides the user interface and is now responsible for all data processing. Its duties include:
    - Searching, displaying, and interacting with the evaluation data.
    - Performing all client-side data analysis, including filtering (by year, instructor, etc.), separation (grouping for display), and all statistical calculations, using its internal `analysisEngine.js`.
    - A search history feature that stores recent searches in the browser's local storage.

- **Database**: A PostgreSQL database hosted on Supabase, which stores all course and metadata information.

## 2. Architecture

The application is a monorepo composed of three main parts:

```
.
├── backend/          # Python/Flask backend API
├── frontend/         # React frontend SPA
└── vercel.json       # Vercel deployment configuration
```

### 2.1. Data Model (Supabase)

The application uses a PostgreSQL database hosted by Supabase. The schema is defined in `db_schema.sql` and consists of two main tables with automatic timestamping for updates.

- **`course_metadata`**: Stores metadata for each course.
    - `course_code` (Primary Key): The unique code for the course (e.g., `AS.180.101`).
    - `last_period_gathered`: The most recent academic period successfully scraped.
    - `last_period_failed`: A boolean indicating if the last scrape attempt for a new period failed.
    - `relevant_periods`: A JSONB field listing all academic periods for which this course has evaluations.
    - `last_scrape_during_grace_period`: A date tracking the last scrape attempt within a grace period.
    - `created_at`: Timestamp of when the record was created.
    - `updated_at`: Timestamp of the last update to the record.

- **`courses`**: Stores the raw evaluation data for each specific course instance (i.e., a course from a specific semester and instructor).
    - `instance_key` (Primary Key): A unique identifier for a course instance (e.g., `AS.180.101_FA23`).
    - `course_code`: A foreign key referencing `course_metadata`.
    - `data`: A JSONB field containing the full scraped evaluation data for that instance.
    - `created_at`: Timestamp of when the record was created.
    - `updated_at`: Timestamp of the last update to the record.

A database trigger (`trigger_set_timestamp`) automatically updates the `updated_at` field on any row modification for both tables.

### 2.2. Backend (Flask)

The backend is a Python/Flask server. Its primary role is to serve as a data gateway, handling scraping and raw data aggregation. The `CourseGroupingService` uses a default, embedded configuration for course groupings.

### 2.3. Frontend (React)

The frontend is a React SPA that contains all the application's business logic. It fetches raw data from the backend and uses `src/utils/analysisEngine.js` to perform all filtering, separation, and statistical calculations on the client side. It also includes a `SearchHistory` component that displays a dropdown of recent searches, and a `storageUtils` utility to manage the search history in the browser's local storage.

### 2.4. Deployment (Vercel)

The application is deployed as a monorepo on Vercel. The deployment is configured using `vercel.json`.

- **Builds**:
    1.  A Python build (`@vercel/python`) for the backend API (`backend/app.py`).
    2.  A static-build (`@vercel/static-build`) for the React frontend, triggered by `frontend/package.json`, which outputs to a `build` directory.

- **Routing**:
    - Requests to `/api/(.*)` are routed to the Python backend.
    - Static assets (`/static/*`, `/favicon.ico`, etc.) are served directly from the frontend build output.
    - All other requests are routed to the frontend's `index.html` to enable client-side routing.

- **CORS**: The Flask backend is configured to handle Cross-Origin Resource Sharing (CORS) from the main production URL, `localhost` for development, and a regular expression to dynamically allow Vercel preview deployment URLs.

### 2.5. Environment Variables

The application connects to the Supabase database via a connection string. This is managed by a single environment variable that must be configured in the Vercel project settings:

- **`DATABASE_URL`**: The PostgreSQL connection string provided by Supabase.

## 3. Local Development

To run the project locally, you will need to start the frontend and backend servers separately.

### Backend (Flask)

1.  **Create a `.env` file** in the project root and add your Supabase connection string:
    ```
    DATABASE_URL="your_supabase_connection_string"
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```
3.  **Start the server from the project root:**
    ```bash
    python3 backend/app.py
    ```
    The backend will be available at `http://127.0.0.1:5000`.

### Frontend (React)

1.  **Navigate to the directory:**
    ```bash
    cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Start the development server:**
    ```bash
    npm start
    ```
    The frontend will open automatically at `http://localhost:3000`.

## 4. API Endpoints

The backend provides the following REST API endpoints, all prefixed with `/api/`. The API validates `course_code` parameters to ensure they match the `XX.###.###` format.

- `GET /api/course/<course_code>`: Retrieves all evaluation data for a given course, triggering a scrape if the data is stale.
- `GET /api/search/course_name/<query>`: Searches for courses by name.
- `GET /api/search/instructor/<name>`: Finds variations of an instructor's name based on last name.
- `GET /api/grace-status/<course_code>`: Checks if a course is in a "grace period" where new evaluations may be available.
- `POST /api/recheck/<course_code>`: Forces a re-scrape of a course, even if it's within a grace period.
- `POST /api/analyze/<course_code>`: Aggregates and returns the complete, raw evaluation data for a given course and all other courses in its group. It returns a `raw_data` object containing all course instances. All filtering, analysis, and statistical calculations are performed by the client (frontend).
