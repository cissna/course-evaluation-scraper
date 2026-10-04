# JHU Course Evaluation Analyzer

This project is a full-stack web application for scraping, analyzing, and displaying course evaluation data from Johns Hopkins University. It uses a Python/Flask backend, a React frontend, and a Supabase PostgreSQL database, all deployed on Vercel. It can be accessed by the public at https://course-evaluation-scraper.vercel.app

## Features

- **Course Evaluation Scraping:** On-demand scraping of course evaluation data from the JHU website.
- **Data Analysis:** Filter and separate data by year, season, and instructor.
- **Search History:** Your recent searches are saved in your browser for easy access.
- **Cross-listed Course Grouping:** Data from cross-listed courses is automatically grouped together.

## Architecture

The application is a monorepo with a `backend` (Python/Flask) and a `frontend` (React) directory. The backend exposes a REST API that the frontend consumes. Data is stored in a PostgreSQL database hosted on Supabase.

## Local Development

To run the application locally, you will need to start both the backend and frontend servers.
Crucially, you will need a Supabase database since use of .json's has been discontinued.
However, using db_setup.py and migrate_data.py is a simple solution to set up your db for you.
Then, the export_data.py script will convert the supabase database back into easily sharable .json files.

### Backend (Flask API)

1.  **Create a `.env` file** in the project root and add your Supabase connection string:
    ```
    DATABASE_URL="your_supabase_connection_string"
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Run the Flask server from the project root directory:**
    ```bash
    python3 -m backend.app
    ```

    The backend server will start on `http://127.0.0.1:5000`.

### Frontend (React UI)

1.  **Navigate to the `frontend` directory:**
    ```bash
    cd frontend
    ```

2.  **Install the required Node.js packages:**
    ```bash
    npm install
    ```

3.  **Run the React development server:**
    ```bash
    npm start
    ```

    The frontend application will open in your browser at `http://localhost:3000`.

## How to Use

1.  Open your browser to `http://localhost:3000` (or the Vercel deployment URL).
2.  Enter a course code (e.g., `AS.180.101`), course title, or a recorded professor name into the search bar. Ambiguous matches appear in Course names and Professors tabs.
3.  Your recent searches will appear in a dropdown for easy access.
4.  Click the "Search" button to fetch and display the data.
5.  Use the toggle buttons and advanced options to filter and separate the data as needed.
6.  Click the download icon to save every displayed statistic and its tooltip information as CSV.

## Database preparation and percentile maintenance

The new cached-first and professor-search APIs require the reviewed SQL files in [migrations](migrations/README.md). Do not run migrations against a live database as part of frontend development. `db_schema.sql` also includes the new schema for a fresh database.

Percentiles are precomputed across all departments, all available years, and existing logical course groups. Each metric stores 401 percentile values for scores 1.00–5.00, rounded to the nearest hundredth. Filters only recompute displayed averages and look them up in that fixed benchmark. A database counter tracks newly inserted evaluation reports; after 1,000, the mapping is rebuilt at the end of a scrape or on the next benchmark request. One report aggregates student responses for a course section and term. Metadata-only checks do not increment the counter. An absent or outdated mapping is built on first use; no monthly job is required. [Migration and maintenance instructions](migrations/README.md) cover imports and explicit rebuilds. The tooltip shows the benchmark's year coverage; unavailable percentiles show N/A with a reason.

## Cached data and professor results

`POST /api/analyze/<code>` and `GET /api/professor?name=...` return saved data immediately, plus per-course freshness metadata. They do not scrape. The tab calls `POST /api/refresh/<code>` for automatic updates or `POST /api/recheck/<code>` for a manual check while keeping cached tables usable. Duplicate work returns 202 and is polled via `GET /api/refresh-status/<code>`. A renewable database lease covers automatic, manual, and batch scrapes. Closing a tab does not create a persistent client job or closed-tab notification.

When new saved evaluations are available, **Show updated data** replaces the table data in place, preserving search, filters, and comparison settings. When there are no new evaluations, the same banner says **No new data found for [period]**. Notifications are optional; neither outcome requires notification permission or a page reload.

`GET /api/search?q=...` returns paginated course/group and professor matches with independent total counts. Professor membership uses one literal recorded `instructor_name` string. Multiple-professor lists are not parsed, and name variants are kept separate. `GET /api/percentiles` serves the precomputed snapshot once per page visit.

## Review

Run `npm run build` in `frontend` to create a production build. The added test suites and test-only scripts have been removed at the owner's request. See [OVERNIGHT_REVIEW.md](OVERNIGHT_REVIEW.md) for implementation decisions and remaining manual review, and [migration instructions](migrations/README.md) for applying or rolling back the prepared SQL.

## Deployment

This application is deployed on Vercel. The `vercel.json` file in the root directory configures the deployment, including the builds for the frontend and backend, and the routing rules.
