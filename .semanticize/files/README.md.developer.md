### 2.2. Backend (Flask)

The backend is a stateless Python/Flask API that functions as a data gateway.

- **Responsibilities**:
    - Exposes REST endpoints for the frontend to consume.
    - Fetches course evaluation data from the JHU website upon request.
    - Caches scraped data in a Supabase (PostgreSQL) database to minimize redundant scraping.
    - Aggregates raw data for a course and its cross-listed counterparts using `CourseGroupingService`.
- **Interaction Pattern**: The backend is purely reactive. It only scrapes or fetches data when an API endpoint is hit. It does not maintain application state.

### 2.3. Frontend (React)

The frontend is a comprehensive React SPA that drives the user experience and handles all data manipulation.

- **Responsibilities**:
    - Provides the complete UI for searching, displaying, and interacting with course data.
    - Fetches raw, unprocessed data from the backend API.
    - **Client-Side Analysis**: Uses `src/utils/analysisEngine.js` to perform all data processing, including:
        - Filtering data by academic year, semester, or instructor.
        - Separating data for comparative views.
        - Calculating all statistical metrics.
    - Manages recent search history using the browser's `localStorage` via `storageUtils.js`.

### 2.4. Database (Supabase/PostgreSQL)

A PostgreSQL database hosted on Supabase serves as the persistence layer, acting primarily as a cache for scraped data.

- **Schema**: Defined in `db_schema.sql`, it consists of two primary tables:
    - `course_metadata`: Stores metadata for each course, including scrape status and relevant academic periods.
    - `courses`: Stores the raw JSONB payload of evaluation data for each specific course instance (e.g., a course from a specific semester).
- **Interaction Pattern**: The backend is the only component that communicates with the database. The frontend is completely decoupled from the database.

## 3. Data Flow

The end-to-end data flow is designed to offload processing to the client:

1.  **User Action**: A user initiates a search from the React frontend.
2.  **API Request**: The frontend calls the `/api/analyze/<course_code>` endpoint on the backend.
3.  **Data Aggregation**: The backend checks for fresh data in Supabase. If data is stale or missing, it triggers a scrape of the JHU website, updates the database, and then collects all raw data for the requested course and its cross-listed group.
4.  **API Response**: The backend returns a single JSON object containing the `raw_data` for all relevant course instances.
5.  **Client-Side Processing**: The React frontend receives the raw data. The `analysisEngine.js` utility then filters, separates, and computes statistics based on the user's selections in the UI.
6.  **Rendering**: React components render the final, analyzed data to the user.

## 4. Local Development

To run the project locally, both the backend and frontend servers must be running. A Supabase database is a hard requirement.

- **Database Setup**: The scripts in `one-time-scripts/` are critical for bootstrapping a development environment.
    - `db_setup.py`: Initializes the database schema.
    - `migrate_data.py`: Populates the database using the legacy `.json` files (`data.json`, `metadata.json`).
- **Environment**: A `.env` file containing the `DATABASE_URL` for your Supabase instance is required in the project root.

## 5. Deployment (Vercel)

The application is deployed as a monorepo on Vercel, orchestrated by `vercel.json`.

- **Builds**: The configuration defines two separate builds:
    1.  `@vercel/python`: Builds the Flask API from `backend/app.py`.
    2.  `@vercel/static-build`: Builds the React application from the `frontend/` directory.
- **Routing**: `vercel.json` contains rewrite rules that are essential for the application to function:
    - API traffic to `/api/(.*)` is routed to the Python backend serverless function.
    - All other requests are routed to the `index.html` of the built React application, enabling client-side routing.