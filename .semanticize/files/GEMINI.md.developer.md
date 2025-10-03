# Developer Documentation: JHU Course Evaluation Analyzer

This document provides a high-level technical overview of the JHU Course Evaluation Analyzer application for developers. It focuses on the architecture, data flow, and core responsibilities of each component.

## 1. Core Architecture

The application is a monorepo with a decoupled frontend and backend, deployed on Vercel. The core design principle is to offload all data processing and analysis to the client-side, keeping the backend lean and focused on data retrieval and scraping.

-   **`backend/` (Python/Flask)**: A stateless API gateway. Its sole purpose is to fetch, scrape, and aggregate raw course evaluation data. It does **not** perform any analysis, filtering, or statistical calculations.
-   **`frontend/` (React SPA)**: The main application logic resides here. It consumes raw data from the backend and performs all data transformations, analysis, filtering, and rendering in the browser.
-   **`vercel.json`**: The deployment configuration file. It defines how Vercel builds the frontend and backend and routes traffic between them.

## 2. Component Deep Dive

### 2.1. Backend (Flask API)

The backend acts as a data provider and scraper.

-   **Primary Function**: To respond to API requests from the frontend. It retrieves requested course data from the Supabase database. If the data is considered stale or is missing, it triggers a scraping process to fetch the latest evaluations from the JHU website.
-   **Data Aggregation**: The `/api/analyze/<course_code>` endpoint is a key function. It identifies all courses belonging to the same group (e.g., cross-listed courses) and returns a single, large `raw_data` object containing all evaluation data for every instance of those courses.
-   **Interaction Pattern**:
    1.  Receives a request (e.g., `GET /api/analyze/AS.180.101`).
    2.  Queries the `course_metadata` table in Supabase to check the data's freshness and identify grouped courses.
    3.  (If necessary) Triggers the scraper to fetch new data from the JHU site and updates the `courses` and `course_metadata` tables.
    4.  Fetches all raw evaluation data for the course and its group from the `courses` table.
    5.  Returns a single JSON object to the client.

### 2.2. Frontend (React SPA)

The frontend is where all the "thinking" happens. It is responsible for the entire user experience, from data interaction to presentation.

-   **`src/utils/analysisEngine.js`**: This is the brain of the frontend. It contains all the business logic for processing the raw data fetched from the backend. Its responsibilities include:
    -   **Filtering**: Slicing the data by academic year, instructor, or other criteria based on user input.
    -   **Separation**: Grouping evaluation data for display (e.g., by semester, by instructor).
    -   **Statistical Calculation**: Computing all statistics (averages, response rates, etc.) on the fly.
-   **`src/components/`**: Contains the UI components for rendering the application, including search bars, results displays, and data visualizations.
-   **`src/utils/storageUtils.js`**: Manages the user's search history by interacting with the browser's local storage.
-   **Interaction Pattern**:
    1.  User enters a course code and initiates a search.
    2.  The app calls the backend's `/api/analyze/` endpoint.
    3.  Upon receiving the `raw_data` object, it passes it to `analysisEngine.js`.
    4.  The user interacts with UI controls (e.g., a dropdown to select a year).
    5.  These interactions trigger functions within `analysisEngine.js` to re-process the original `raw_data` object according to the new criteria.
    6.  The UI re-renders to display the newly calculated results. The backend is not contacted again.

### 2.3. Database (Supabase/PostgreSQL)

The database acts as a persistent cache for scraped data, preventing the need to re-scrape the JHU website on every request.

-   **`course_metadata` table**: A registry of all known courses. It tracks when a course was last scraped, whether scrapes have failed, and which academic periods have available data. This table is used to determine if the cached data in the `courses` table is fresh enough or if a re-scrape is needed.
-   **`courses` table**: Stores the raw, unprocessed JSON data for a specific course instance (e.g., "Intro to Psych" from Fall 2023 taught by Professor X). The `data` field is a JSONB blob containing the exact data scraped from the source.
-   **`trigger_set_timestamp`**: An automatic database trigger that updates the `updated_at` timestamp on any row change, providing a simple mechanism for cache invalidation logic in the backend.

## 3. Deployment & Routing (`vercel.json`)

Vercel orchestrates the building and routing for the monorepo.

-   **Builds**: Two separate build processes are defined: one for the Python backend (`@vercel/python`) and one for the React frontend (`@vercel/static-build`).
-   **Routing**:
    -   Any request path starting with `/api/` is rewritten and proxied to the Flask backend.
    -   All other paths are routed to the frontend's `index.html`, allowing the React Router to handle client-side navigation.