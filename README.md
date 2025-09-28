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
    python3 backend/app.py
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
2.  Enter a course code (e.g., `AS.180.101`) or a course name (e.g., `Introduction to Psychology`) into the search bar.
3.  Your recent searches will appear in a dropdown for easy access.
4.  Click the "Search" button to fetch and display the data.
5.  Use the toggle buttons and advanced options to filter and separate the data as needed.
6.  Click the "Download as CSV" button to save the current view of the data.

## Deployment

This application is deployed on Vercel. The `vercel.json` file in the root directory configures the deployment, including the builds for the frontend and backend, and the routing rules.