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

Overall Quality and Workload are the default statistics, listed first in that order. Instructor Effectiveness, Intellectual Challenge, Helpful Feedback, and TA Quality can be enabled in Advanced Options. **Show percentiles** remembers your choice across visits in the same browser, using local storage like search history; it starts off if you have no saved preference.

**Advanced Options → Statistics → Weight percentiles by average class size** gives each course group weight equal to its valid response count for that metric divided by the number of distinct terms it has run, including summer and intersession. Sections within a term are combined. It starts unchecked and remembers your choice independently of **Show percentiles**. The setting updates percentile cells, score tooltips, and CSV exports immediately across course and professor results; absolute ratings and statistical comparisons keep using the original scores. CSV metadata identifies the selected weighting.

On the comparison branch, use **Add side-by-side** or a history item's **side-by-side** button to display up to five courses/professors together. Statistical comparison starts off: choose **Enter comparison mode** to select two rows and compare their averages. At least two rows must be displayed before entering; otherwise a dismissible alert explains how to add or separate entries. Red/orange outlines identify the selections, and the feedback reports whether their difference is significant; significant pairs also receive gold fill. This mode works with a single result separated into multiple rows too. [Comparison review notes](docs/COMPARISONS.md) explain the controls, Welch calculation, and overlap guard.

## Database preparation and percentile maintenance

The new cached-first and professor-search APIs require the reviewed SQL files in [migrations](migrations/README.md). Do not run migrations against a live database as part of frontend development. `db_schema.sql` also includes the new schema for a fresh database.

Percentiles are precomputed across all departments, all available years, and existing logical course groups. Each metric stores two lookups of 401 values for scores 1.00–5.00: equal course weights and average class size. Both use scores rounded to the nearest hundredth. Ties use midpoint ranks: the share below the score plus half of the tied share. Filters only recompute displayed averages and look them up in the selected fixed benchmark. A database counter tracks newly inserted evaluation reports; after 1,000, both mappings rebuild together at the end of a scrape or on the next benchmark request. One report aggregates student responses for a course section and term. Metadata-only checks do not increment the counter. An absent or outdated mapping is built on first use; no monthly job is required. Format version 3 adds the weighted lookup to the existing JSONB payload, with no additional SQL migration. [Migration and maintenance instructions](migrations/README.md) cover imports and explicit rebuilds. Percentile cells use small superscript ordinal suffixes; CSV exports use plain-text ordinals. Start with whole numbers and add decimal places only while rounding produces 0/100, an all-nines upper rank (99, 99.9, …), or the smallest positive decimal (0.1, 0.01, …). Stop at the first unambiguous result, preserving its trailing zeros: 99.57 becomes 99.6, 99.90 stays 99.90, and 0.1 becomes 0.10. Exact 0/100 values remain whole. Each score tooltip shows the other display mode, response count, and σ. Unavailable percentiles show N/A with a reason. The benchmark's year coverage and selected weighting remain available in CSV exports.

## Cached data and professor results

`POST /api/analyze/<code>` and `GET /api/professor?name=...` return saved data immediately, plus per-course freshness metadata. They do not scrape. The tab calls `POST /api/refresh/<code>` for automatic updates or `POST /api/recheck/<code>` for a manual check while keeping cached tables usable. Duplicate work returns 202 and is polled via `GET /api/refresh-status/<code>`. A renewable database lease covers automatic, manual, and batch scrapes. Closing a tab does not create a persistent client job or closed-tab notification.

When new saved evaluations are available, **Show updated data** replaces the table data in place, preserving search, filters, and comparison settings. When there are no new evaluations, the same banner says **No new data found for [period]**. Notifications are optional; neither outcome requires notification permission or a page reload.

`GET /api/search?q=...` returns paginated course/group and professor matches with independent total counts. Professor membership uses one literal recorded `instructor_name` string. Multiple-professor lists are not parsed, and name variants are kept separate. `GET /api/percentiles` serves the precomputed snapshot once per page visit.

## Review

Run `npm run build` in `frontend` to create a production build. The added test suites and test-only scripts have been removed at the owner's request. See [OVERNIGHT_REVIEW.md](OVERNIGHT_REVIEW.md) for implementation decisions and remaining manual review, and [migration instructions](migrations/README.md) for applying or rolling back the prepared SQL.

## Deployment

This application is deployed on Vercel. The `vercel.json` file in the root directory configures the deployment, including the builds for the frontend and backend, and the routing rules.
