# QWEN.md: JHU Course Evaluation Analyzer

## 1. Project Overview

This project is a full-stack web application designed to scrape, analyze, and display course evaluation data from Johns Hopkins University. It has been migrated from a local, file-based system to a robust, cloud-based architecture using Supabase for data storage and Vercel for deployment.

- **Backend**: A Python/Flask server that exposes a REST API. Its responsibilities include:
    - On-demand scraping of course evaluation data from the JHU website.
    - Storing and retrieving course data and metadata from a Supabase (PostgreSQL) database.
    - Performing data analysis, filtering, and aggregation.

- **Frontend**: A single-page application (SPA) built with React. It provides the user interface for searching, displaying, and interacting with the evaluation data.

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

The application uses a PostgreSQL database hosted by Supabase. The schema is defined in `db_schema.sql` and consists of two main tables:

- **`course_metadata`**: Stores metadata for each course.
    - `course_code` (Primary Key): The unique code for the course (e.g., `AS.180.101`).
    - `last_period_gathered`: The most recent academic period successfully scraped.
    - `relevant_periods`: A JSON field listing all academic periods for which this course has evaluations.
    - Other fields for tracking scraping status and grace periods.

- **`courses`**: Stores the raw evaluation data for each specific course instance (i.e., a course from a specific semester and instructor).
    - `instance_key` (Primary Key): A unique identifier for a course instance (e.g., `AS.180.101_FA23`).
    - `course_code`: A foreign key referencing the `course_metadata` table.
    - `data`: A JSON field containing the full scraped evaluation data for that instance.

### 2.2. Deployment (Vercel)

The application is deployed as a monorepo on Vercel. The deployment is configured using the `vercel.json` file, which defines the build and routing rules.

- **Builds**:
    1.  A Python build (`@vercel/python`) for the backend API located at `backend/app.py`.
    2.  A static build (`@vercel/static-build`) for the React frontend located in the `frontend/` directory.

- **Routing**:
    - Requests starting with `/api/` are routed to the Python backend.
    - All other requests are routed to the React frontend, with specific rules to handle static assets (CSS, JS) and the `index.html` file for client-side routing.

### 2.3. Environment Variables

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

The backend provides the following REST API endpoints, all prefixed with `/api/`:

- `GET /api/course/<course_code>`: Retrieves all evaluation data for a given course, triggering a scrape if the data is stale.
- `GET /api/search/course_name/<query>`: Searches for courses by name.
- `GET /api/search/instructor/<name>`: Finds variations of an instructor's name based on last name.
- `GET /api/grace-status/<course_code>`: Checks if a course is in a "grace period" where new evaluations may be available.
- `POST /api/recheck/<course_code>`: Forces a re-scrape of a course, even if it's within a grace period.
- `POST /api/analyze/<course_code>`: Performs filtering and separation analysis on a course's data based on parameters provided in the request body.