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

Percentile distributions are precomputed across all departments, all available years, and existing logical course groups. Filters only recompute the displayed averages and look them up in that fixed benchmark. The tooltip shows the actual benchmark coverage. Rebuild the benchmark after regular bulk scraping/import, at least monthly; [migration and maintenance instructions](migrations/README.md) describe the explicit commands. A missing benchmark displays N/A in percentile mode, with a reason.

## Cached data and professor results

`POST /api/analyze/<code>` and `GET /api/professor?name=...` return saved data immediately, plus per-course freshness metadata. They do not scrape. The tab calls `POST /api/refresh/<code>` for automatic updates or `POST /api/recheck/<code>` for a manual check while keeping cached tables usable. Duplicate work returns 202 and is polled via `GET /api/refresh-status/<code>`. A renewable database lease covers automatic, manual, and batch scrapes. Closing a tab does not create a persistent client job or closed-tab notification.

`GET /api/search?q=...` returns paginated course/group and professor matches with independent total counts. Professor membership uses exact recorded names, including explicitly listed team teachers. Name variants are kept separate. `GET /api/percentiles` serves the precomputed snapshot once per page visit.

## Validation without live data

Run `python3 -m unittest discover -s backend/tests -v` and, in `frontend`, `CI=true npm test -- --watchAll=false --watchman=false --runInBand` followed by `CI=true npm run build`.

The optional PostgreSQL integration tests require `TEST_DATABASE_URL` pointing to a **local** database named `course_eval_test_*`. They create an isolated schema, check concurrent lock claims/stale writers and migrations, then remove only that schema. They never use `DATABASE_URL`.

For browser review, build the frontend, then run `python3 tools/fixture_server.py --port 8765`. Open `http://127.0.0.1:8765`. This serves the real Flask/React application with disposable data; all database and upstream scraping access is disabled. Use `--snapshot data.json` to smoke-test a local export. Synthetic examples include `EN.553.431` (grouping and former titles), `Jane Smith` (professor scope), `Smith` (cross-type ambiguity), `AS.050.203` (delayed background update), `AS.999.001` (old years), and `AS.999.002` (intentional null statistics).

With that synthetic server running (without `--snapshot`) and Playwright installed locally, run `node tools/browser_review.cjs`. Set `PLAYWRIGHT_MODULE` to the absolute module path if it is outside this checkout. The runner checks desktop (1440×900) and phone (390×844) sizes, saves screenshots/CSV/results under ignored `browser-artifacts/`, and refuses nonlocal URLs. It is a prepared review script; see [OVERNIGHT_REVIEW.md](OVERNIGHT_REVIEW.md) for which checks were actually executed in the implementation environment.

## Deployment

This application is deployed on Vercel. The `vercel.json` file in the root directory configures the deployment, including the builds for the frontend and backend, and the routing rules.
