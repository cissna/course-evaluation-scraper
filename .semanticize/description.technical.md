# Technical Project Summary: JHU Course Evaluation Analyzer

## 1. Project Overview

The JHU Course Evaluation Analyzer is a full-stack application designed to ingest, process, analyze, and serve aggregated statistical data derived from Johns Hopkins University's public course evaluation platform. The architecture is decoupled, consisting of a Python/Flask RESTful backend, a PostgreSQL database for persistence, and a React frontend for dynamic data visualization.

The core technical challenge addressed by the system is efficiently retrieving complex, paginated, and often time-gated evaluation data via web scraping, normalizing it, and providing client-side statistical analysis tools.

## 2. Architecture and Design Patterns

The project adheres to a **Client-Server (Decoupled) Architecture** with significant emphasis on **Data Caching and Incremental Updates** on the backend.

### Key Design Patterns:

*   **Service Layer Pattern:** Business logic is cleanly separated into service modules (`scraper_service.py`, `analysis.py`, `course_grouping_service.py`). The Flask API (`app.py`) acts purely as the controller, delegating tasks to these services.
*   **Read-Through Caching (Backend):** The `scraper_service.py` implements a sophisticated data freshness check using course metadata timestamps and academic period logic (`period_logic.py`). Data is only scraped if it is stale or if a forced recheck is requested, significantly reducing load on the external evaluation site.
*   **Repository/Data Access Pattern:** Database interaction is isolated to `db_utils.py`, which uses raw SQL via `psycopg2` and leverages PostgreSQL's `JSONB` type for storing complex, evolving evaluation data structures.
*   **Single Page Application (SPA):** The frontend is a React application that manages its own complex state (filters, selected stats, raw data cache) to perform rapid client-side calculations, minimizing unnecessary network requests.
*   **External Configuration & Deployment:** Configuration (`config.py`) centralizes scraping URLs and time-sensitive logic (grace periods). The backend is deployed using Gunicorn, and environmental variables (`.env`) are used for sensitive credentials like the database URL and API keys.

## 3. Key Packages and Libraries Used

### Backend (Python)
*   **Framework/Web:** `Flask`, `Flask-Cors` (for cross-origin communication).
*   **Database:** `psycopg2-binary` (PostgreSQL adapter).
*   **Web Scraping:** `requests` (for HTTP), `beautifulsoup4` (for HTML parsing).
*   **Utilities:** `python-dateutil` (for robust date arithmetic/period logic), `python-dotenv` (for local credential loading).
*   **Deployment:** `gunicorn` (WSGI server).

### Frontend (React)
*   **Framework:** React (uses Hooks for state management).
*   **Styling:** Component-scoped CSS modules (e.g., `App.css`, `DataDisplay.css`).
*   **API Communication:** Standard `fetch` API (or implied library for service calls).
*   **Testing:** Jest, `@testing-library/react`, and `@testing-library/jest-dom`.

## 4. Component Integration and Technical Flow

### Data Ingestion Workflow (Backend)

1.  **Scraping Session:** `scraping_logic.py` establishes an authenticated `requests.Session` using a hardcoded `AUTH_URL`.
2.  **Link Discovery:** `scrape_search.py` queries the external site for a given course code. It handles pagination and ambiguity by checking for a "Show more" button or by performing brute-force checks across known section numbers (`workflow_helpers.py`).
3.  **Data Extraction:** `scrape_link.py` uses the discovered report URL, parses the HTML, and extracts evaluation frequencies and metadata (instructor names, course names). It employs an exponential backoff retry mechanism for resilience.
4.  **Persistence:** `scraper_service.py` coordinates the process. New data is saved to the `courses` table (using `instance_key` as the primary key) via `db_utils.py`. Metadata is updated in `course_metadata`.

### Data Retrieval and Analysis Workflow (Frontend/Backend Interaction)

1.  **API Request:** The frontend POSTs to `/api/analyze/:code` with desired filters and statistics.
2.  **Backend Aggregation (`scraper_service.py`):** If the data is stale, the backend fetches all related course instances (including cross-listed groups resolved by `course_grouping_service.py`) from the DB. It then calls `backend/analysis.py`'s `process_analysis_request`.
3.  **Client-Side Analysis:** The backend returns the fully aggregated, raw data. The frontend's `analysisEngine.js` then performs the statistical heavy lifting:
    *   **Filtering:** Filters instances by year/season/instructor.
    *   **Grouping:** Partitions data based on user-selected keys (e.g., separating results by individual instructor names, ensuring name canonicalization across different time periods).
    *   **Calculation:** Computes means, sample standard deviations, and counts ($N$) using the numerical mappings defined in `STAT_MAPPINGS`.
4.  **Display:** The `DataDisplay` component renders the results in a table, dynamically creating columns based on the selected statistics and rows based on the selected grouping key. Tooltips provide additional metadata ($N$, $\sigma$).

## 5. Technical Decisions and Implementation Approach

| Area | Decision/Approach | Rationale |
| :--- | :--- | :--- |
| **Data Storage** | PostgreSQL with `JSONB` for raw data (`courses` table) and relational metadata (`course_metadata`). | `JSONB` allows flexible schema evolution for scraped data while maintaining relational integrity for course codes and timestamps. |
| **Scraping Resilience** | Exponential Backoff, Session Persistence, Grace Period Logic. | Essential due to external site reliance. Grace periods prevent false negatives when data is posted late. |
| **Course Grouping** | Hybrid approach: Explicit hardcoded groups + Pattern-based department equivalents. | Handles known cross-listings (explicit) and systematic structural equivalencies (pattern-based) for comprehensive analysis. |
| **Frontend Performance** | Client-Side Analysis Caching. | Caching the raw, aggregated data (`rawCourseData` in `App.js`) prevents re-scraping/re-fetching from the backend when users only change display options (filters, statistics, grouping). |
| **Schema Management** | Database Triggers (`db_schema.sql`). | Automatically manages `updated_at` timestamps on `UPDATE` operations for both primary tables, ensuring data freshness tracking is always reliable, regardless of the application layer logic. |
| **Code Export Utility** | `one-time-scripts/export_code.py` | Used to programmatically generate documentation lists, ensuring the documentation reflects the current codebase structure without manual maintenance. |