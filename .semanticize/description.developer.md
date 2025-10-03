description.developer.md:
# Project Summary: JHU Course Evaluation Analyzer

## 1. Project Goal and Architecture

The JHU Course Evaluation Analyzer is a full-stack web application designed to fetch, process, and visualize detailed statistical data from JHU course evaluation reports. It utilizes a Python/Flask backend for data scraping, persistence, and heavy computation, and a React frontend for dynamic user interaction and data visualization.

The architecture follows a clear separation of concerns:
1.  **Frontend (React/Node.js):** Handles UI rendering, user input, client-side filtering/analysis, and API consumption.
2.  **Backend (Python/Flask):** Manages REST APIs, orchestrates complex data scraping workflows targeting an external JHU site, handles database interaction (PostgreSQL/Supabase), and performs the core statistical analysis.
3.  **Persistence (PostgreSQL):** Stores course metadata (for scrape tracking) and raw evaluation data instances.

## 2. Main Components and Purposes

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Flask API (`app.py`)** | Python/Flask | Serves REST endpoints (`/api/*`), handles CORS, validates input, and routes requests to the appropriate service layer. |
| **Scraper Service (`scraper_service.py`)** | Python | The primary orchestration layer for data fetching. Decides whether to use cached data or initiate a live scrape based on time-based freshness logic (`period_logic.py`). |
| **Analysis Engine (`analysis.py`, `analysisEngine.js`)** | Python (Backend), JavaScript (Frontend) | Core computation modules. The backend performs initial aggregation; the frontend utility processes raw data based on user filters (year, instructor, statistics selection) client-side. |
| **Course Grouping Service (`course_grouping_service.py`)** | Python | Business logic for identifying related courses (e.g., cross-listed 400/600 level classes) to ensure comprehensive group analysis. |
| **Data Access Layer (`db_utils.py`)** | Python | Abstracts all direct PostgreSQL interactions (connection, UPSERTs, complex search queries). |
| **Scraping Modules (`scrape_search.py`, `scrape_link.py`)** | Python | Handles the low-level interaction with the external JHU evaluation site, including session authentication, link discovery, and HTML parsing. |
| **Frontend (`App.js`, Components)** | React/JavaScript | Manages global state, controls UI views (Search, Results List, Analysis View), and renders dynamic charts/tables based on analysis output. |
| **Database Schema (`db_schema.sql`)** | SQL (PostgreSQL) | Defines two key tables: `course_metadata` (for tracking scrape status) and `courses` (for storing JSONB evaluation documents). |

## 3. High-Level Integration Flow

1.  **User Request (Frontend):** A user selects a course or initiates a search query in the React UI.
2.  **API Call:** The frontend calls a Flask endpoint (e.g., `POST /api/analyze/<course_code>`).
3.  **Data Freshness Check (Backend):** `scraper_service.py` checks `course_metadata` against `period_logic.py` to see if the data is fresh based on academic release schedules.
4.  **Data Retrieval/Scraping:**
    *   If fresh, data is retrieved from the `courses` table via `db_utils.py`.
    *   If stale, the `workflow_helpers.py` orchestrator initiates the scrape: it authenticates (`scraping_logic.py`), finds report links (`scrape_search.py`), scrapes the content (`scrape_link.py`), and persists new data/metadata to the DB.
5.  **Grouping & Analysis:** The raw data is passed to `CourseGroupingService` to identify related courses. The data is then processed by `analysis.py` to generate statistical summaries based on user-defined parameters (filters, separation keys).
6.  **Response:** The structured analysis result is returned to the frontend.
7.  **Client-Side Processing:** The React `App` component receives the raw data and applies any immediate changes (e.g., switching statistics being displayed) using the client-side `analysisEngine.js` utility for fast, reactive updates without hitting the backend again.

## 4. Development-Relevant Information

### Dependencies & Environment
*   **Python Backend:** Requires `Flask`, `requests`, `beautifulsoup4`, `psycopg2-binary`, and `python-dotenv`. Dependencies are managed via `backend/requirements.txt`.
*   **Frontend:** Standard Create React App setup, managed via `package.json` (dependencies include React, standard build tools, and potentially a dependency for logging/analytics).
*   **Configuration:** Sensitive configuration (like `DATABASE_URL` and scraping API keys) is managed via environment variables, loaded locally using `.env` files (ignored by Git).

### Artifacts and Ignoring
*   **Git Ignore (`.gitignore`):** Explicitly excludes Python virtual environments (`.venv/`), Node dependencies (`node_modules/`), build artifacts (`.vercel/`), and sensitive configuration (`.env*`).
*   **Deployment Ignore (`.vercelignore`):** Excludes local data files (`data.json`, `metadata.json`) and development artifacts, assuming deployment relies solely on the database for persistence.

### Data Migration & Setup
*   **Migration Scripts:** A suite of Python scripts exists in `one-time-scripts/` for bootstrapping the environment:
    *   `db_setup.py`: Creates the required PostgreSQL schema from `db_schema.sql`.
    *   `migrate_data.py`: Ingests static JSON data (`data.json`, `metadata.json`) into the new database tables.
    *   `export_code.py`: A utility to snapshot the source code for documentation purposes.
*   **Development Launch:** The `one-time-scripts/run_all.sh` script is provided to launch both the backend (`python3 -m backend.app`) and frontend (`npm start`) servers concurrently, using process trapping for clean shutdown.