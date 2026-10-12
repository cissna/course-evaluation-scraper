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
2.  Enter a full or partial course code, course title, or a recorded professor name into the search bar. Course code matching ignores periods and capitalization: `AS100`, `AS.100`, and `AS.100.` all find saved courses in `AS.100`; `601.465` and `601465` find matching codes under any school prefix. A single match opens automatically; ambiguous matches appear in Courses and Professors tabs. A full code such as `AS.180.101` or `AS180101` opens directly, including when the course has no saved evaluations yet. Recent-search filtering also accepts partial codes without periods.
3.  Your recent searches will appear in a dropdown for easy access.
4.  Click the "Search" button to fetch and display the data.
5.  Use the toggle buttons and advanced options to filter and separate the data as needed.
6.  Click the download icon to save every displayed statistic and its tooltip information as CSV.

Overall Quality and Workload are the default statistics, listed first in that order. Instructor Effectiveness, Intellectual Challenge, Helpful Feedback, and TA Quality can be enabled in Advanced Options. **Show percentiles** remembers your choice across visits in the same browser, using local storage like search history; it starts off if you have no saved preference.

Every choice under **Advanced Options → Statistics** is also remembered between visits: displayed statistics (including Periods Course Has Been Run), percentile weighting, and the comparison significance threshold. An unfinished or invalid threshold edit leaves the last valid saved value in place. Date, season, and separation choices retain their current session-only behavior.

**Advanced Options → Statistics → Weight percentiles by average class size** weights course averages by valid responses for the metric divided by distinct observed terms, including summer and intersession. In professor views, the label becomes **Weight percentiles by average students per semester**: each professor is weighted by valid responses across all their courses divided by distinct observed teaching terms. Concurrent courses and sections share a term in that denominator; observed terms without answers to the metric still count. These weights estimate student volume from evaluation responses, not enrollment. Mixed side-by-side views show **Weight percentiles by average class size / students per semester** and apply the appropriate distribution to each result. The setting starts unchecked and remembers your choice independently of **Show percentiles**. Percentile cells, tooltips, captions, and CSV exports update immediately; absolute ratings and statistical comparisons keep using the original scores. CSV metadata identifies the comparison population and selected weighting.

Use **Add side-by-side** or a history item's **side-by-side** button to display up to five courses/professors together. **Side-by-Side View** aligns table tops beneath the tallest title/grouping block, while each table keeps its own height. Statistical comparison starts off: choose **Enter comparison mode** to select two rows and compare their averages. At least two rows must be displayed before entering; otherwise a dismissible alert explains how to add or separate entries. If an active comparison drops below two displayed rows, selections clear and row selection is disabled until two rows are available again. Red/orange outlines identify the selections, and the feedback names the metric and reports whether its difference is significant; significant pairs also receive gold fill. This mode works with a single result separated into multiple rows too. [Comparison review notes](docs/COMPARISONS.md) explain the controls, Welch calculation, and overlap guard.

## Database preparation and percentile maintenance

The new cached-first and professor-search APIs require the reviewed SQL files in [migrations](migrations/README.md). Do not run migrations against a live database as part of frontend development. `db_schema.sql` also includes the new schema for a fresh database.

Percentiles are precomputed across all departments and available years, separately for existing logical course groups and recorded professors. Each entity contributes one response-weighted average per metric; professor identities follow the same literal trimmed names as professor search. Course views use course averages and professor views use professor averages, including when results are shown side by side. Separating or filtering a result keeps its original comparison population. Each population stores two lookups per metric with 401 values for scores 1.00–5.00: equal entity weights and average student volume. Both use scores rounded to the nearest hundredth. Ties use midpoint ranks: the share below the score plus half of the tied share. Filters only recompute displayed averages and look them up in the selected fixed benchmark. A database counter tracks newly inserted evaluation reports; after 1,000, all course and professor mappings rebuild together at the end of a scrape or on the next benchmark request. One report aggregates student responses for a course section and term. Metadata-only checks do not increment the counter. An absent or outdated mapping is built on first use; no monthly job is required. Format version 4 adds professor lookups to the existing JSONB payload, with no additional SQL migration; older snapshots rebuild automatically on the first benchmark request after the update. [Migration and maintenance instructions](migrations/README.md) cover imports and explicit rebuilds. Percentile cells use small superscript ordinal suffixes; CSV exports use plain-text ordinals. Start with whole numbers and add decimal places only while rounding produces 0/100, an all-nines upper rank (99, 99.9, …), or the smallest positive decimal (0.1, 0.01, …). Stop at the first unambiguous result, preserving its trailing zeros: 99.57 becomes 99.6, 99.90 stays 99.90, and 0.1 becomes 0.10. Exact 0/100 values remain whole. Each score tooltip shows the other display mode, response count, and σ. Unavailable percentiles show N/A with a reason. The benchmark's year coverage and selected weighting remain available in CSV exports.

## Cached data and professor results

`POST /api/analyze/<code>` and `GET /api/professor?name=...` return saved data immediately, plus per-course freshness metadata. They do not scrape. The tab calls `POST /api/refresh/<code>` for automatic updates or `POST /api/recheck/<code>` for a manual check while keeping cached tables usable. Duplicate work returns 202 and is polled via `GET /api/refresh-status/<code>`. A renewable database lease covers automatic, manual, and batch scrapes. Closing a tab does not create a persistent client job or closed-tab notification.

When new saved evaluations are available, **Show updated data** replaces the table data in place, preserving search, filters, and comparison settings. When there are no new evaluations, the same banner says **No new data found for [period]**, removes Recheck immediately, and disappears after 10 seconds. Applied-update confirmations also disappear after 10 seconds; pending updates and failures remain actionable.

Side-by-side results share one refresh banner above their headings. It lists courses that may be missing recent evaluations and offers **Recheck all**. A shared course is checked once per manual batch, and every displayed result containing it reloads saved data; **Show updated data** applies all available updates together. Grouping notices remain course-specific. Notifications are optional and remember the first enabled choice for later checks and visits; an existing granted browser permission is honored too. Neither outcome requires notification permission or a page reload.

`GET /api/search?q=...` returns paginated course/group and professor matches with independent total counts. Courses match title substrings or code substrings with periods removed; code matching is case-insensitive and does not assume a school prefix. Existing cross-listed course grouping applies to results and counts. Professor membership uses one literal recorded `instructor_name` string. Multiple-professor lists are not parsed, and name variants are kept separate. `GET /api/percentiles` serves the precomputed snapshot once per page visit.

## Review

Run `npm run build` in `frontend` to create a production build. The added test suites and test-only scripts have been removed at the owner's request. See [OVERNIGHT_REVIEW.md](OVERNIGHT_REVIEW.md) for implementation decisions and remaining manual review, and [migration instructions](migrations/README.md) for applying or rolling back the prepared SQL.

## Deployment

This application is deployed on Vercel. The `vercel.json` file in the root directory configures the deployment, including the builds for the frontend and backend, and the routing rules.
