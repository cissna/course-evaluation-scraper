# Developer Documentation: JHU Course Evaluation Analyzer

This document provides a high-level technical overview of the JHU Course Evaluation Analyzer, focusing on the architecture and interaction patterns for developers.

## 1. System Architecture

The application follows a client-server model with a distinct separation of concerns: a thin, data-focused backend and a thick, logic-heavy frontend.

- **Backend (Python/Flask)**: Functions as a stateless data gateway. Its sole purpose is to scrape data on demand, interact with the database, and serve raw, unprocessed data to the frontend. It does not perform any data analysis or business logic.
- **Frontend (React SPA)**: Contains the entirety of the application's business logic. It fetches raw data from the backend and performs all analysis, filtering, and statistical calculations client-side.
- **Database (Supabase/PostgreSQL)**: A cloud-hosted relational database that persists all scraped course evaluation data and metadata.

This architecture makes the backend a simple, maintainable data provider, while the frontend is a powerful, self-contained analysis tool.

## 2. Component Breakdown

### 2.1. Backend (Flask API)

The backend's role is to abstract away the data sources (JHU website, database) from the client.

- **Primary Function**: To respond to API requests from the frontend. It fetches data from the database or, if necessary, triggers a live scrape of the JHU course evaluation website.
- **Key Modules**:
    - `app.py`: The main Flask application file defining the API endpoints.
    - `scraper_service.py`: Orchestrates the scraping process, deciding when to fetch new data based on metadata and grace periods.
    - `db_utils.py`: A data access layer that handles all communication with the Supabase database.
    - `course_grouping_service.py`: Identifies and groups cross-listed courses to provide a complete dataset for analysis.
- **Interaction Pattern**: The frontend initiates all interactions by calling an API endpoint. The backend retrieves the requested data (from the DB or by scraping), aggregates it if necessary (for cross-listed courses), and returns a single JSON object containing the raw data.

### 2.2. Frontend (React SPA)

The frontend is responsible for the user interface and all data processing.

- **Primary Function**: To provide a user interface for searching and viewing course evaluations. It transforms the raw data from the backend into meaningful statistics and visualizations.
- **Key Modules**:
    - **`analysisEngine.js`**: The core of the frontend's logic. This module ingests the raw JSON data from the backend and executes all filtering (e.g., by year, instructor), data separation (grouping for display), and statistical computations. Any changes to the analysis logic will be made here.
    - **`components/`**: Contains the React components that make up the UI.
        - `CourseSearch.js`: Handles user input for searching courses.
        - `DataDisplay.js`: Renders the results of the analysis performed by `analysisEngine.js`.
        - `SearchHistory.js`: A UI component that uses `storageUtils.js` to display recent searches.
    - **`utils/storageUtils.js`**: A utility for managing the search history in the browser's local storage.
- **Interaction Pattern**: On user search, the frontend calls the backend's `/api/analyze/<course_code>` endpoint. Upon receiving the raw data, it passes the data to `analysisEngine.js`. The resulting processed data is then rendered by the `DataDisplay` component.

### 2.3. Database (Supabase/PostgreSQL)

The database acts as a cache and a persistent store for all scraped data.

- **`course_metadata` table**: This table is an index of all known courses. It tracks the most recent scrape attempts and the academic periods for which data is available. The backend uses this table to determine if a new scrape is needed.
- **`courses` table**: This table stores the raw JSON output from the scraper for each individual course instance (i.e., a specific course taught in a specific semester by a specific instructor).
- **Interaction Pattern**: The database is only ever accessed by the backend via the `db_utils.py` module. The frontend has no direct knowledge of or access to the database.

## 3. Deployment & Environment (Vercel)

- **`vercel.json`**: This configuration file is central to the deployment process. It defines the build process for the monorepo and the routing rules.
- **Routing**: The routing is set up to serve a modern SPA.
    - API calls (`/api/*`) are rewritten and proxied to the Python backend function.
    - All other user-facing paths are routed to the frontend's `index.html`, allowing the React router to handle client-side navigation.
- **Environment Variables**: The system is configured with a single `DATABASE_URL` variable, which contains the connection string for the Supabase instance. This is the only secret required for the application to run.