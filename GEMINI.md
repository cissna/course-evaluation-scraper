# GEMINI.md: JHU Course Evaluation Analyzer

## Project Overview

This project is a full-stack web application designed to scrape, analyze, and display course evaluation data from Johns Hopkins University.

- **Backend**: A Python server using the **Flask** web framework. It exposes a REST API for the frontend to consume. Its primary responsibilities include:
    - Scraping course evaluation data from the JHU EvaluationKIT website using **Requests** and **BeautifulSoup**.
    - Caching scraped data and metadata in local JSON files (`data.json`, `metadata.json`).
    - Performing on-demand data analysis, filtering, and aggregation.
    - Providing endpoints for searching courses and instructors.

- **Frontend**: A modern single-page application (SPA) built with **React**. It provides the user interface for:
    - Searching for courses by code or name.
    - Displaying evaluation data in a structured table.
    - Applying advanced filters (by year, season) and data separation (by instructor, course code).
    - Downloading the analyzed data as a CSV file.

- **Architecture**: The application follows a classic client-server model. The React frontend is the user-facing client, and the Flask backend serves as the data provider and processing engine. The core scraping logic is centralized in `workflow_helpers.py`, which orchestrates the process of fetching, parsing, and storing data.

## Building and Running

The project can be run using a convenience script or by starting the frontend and backend servers separately.

### Using the Run Script (Recommended)

A shell script is provided to install dependencies and start both servers concurrently.

```bash
# Make the script executable (if needed)
chmod +x run_all.sh

# Run the script from the project root
./run_all.sh
```

### Manual Startup

#### Backend (Flask)

1.  **Install dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```
2.  **Start the server from the project root directory:**
    ```bash
    python3 backend/app.py
    ```
    The backend will be available at `http://127.0.0.1:5000`.

#### Frontend (React)

1.  **Navigate to the directory:**
    ```bash
    cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Start the development server:**
    ```bash
    npm start
    ```
    The frontend will open automatically at `http://localhost:3000`.

### Testing

The frontend includes a test script, although the project currently lacks a comprehensive test suite.

```bash
# From the frontend/ directory
npm test
```

## Development Conventions

- **Modular Structure**: The Python code is organized into modules with specific responsibilities:
    - `backend/app.py`: Flask API routing.
    - `backend/scraper_service.py`: High-level service logic that connects the API to the core scraping workflow.
    - `workflow_helpers.py`: The central orchestrator for the entire scraping and data storage process.
    - `scrape_search.py` / `scrape_link.py`: Low-level modules responsible for specific scraping tasks (finding links and scraping data from them).
    - `period_logic.py`: Handles time-based logic for evaluation periods.
    - `data_manager.py`: Manages reading from and writing to JSON files.
    - `config.py`: Stores shared constants like URLs and file paths.

- **Data Storage**: The application uses a simple file-based storage system:
    - `data.json`: A large JSON file containing all raw scraped evaluation data, keyed by a unique course instance identifier.
    - `metadata.json`: Stores metadata for each course, including when it was last scraped and which periods are relevant.
    - `failed.json`: Logs any scraping attempts that failed.
    - **Note**: This file-based approach is a major performance bottleneck. Migrating to a database is a key area for improvement.

- **Frontend State Management**: The main `frontend/src/App.js` component manages the application's global state, including advanced options, API results, and loading status. Data is passed down to child components via props.

- **API Communication**: The frontend communicates with the backend via REST API calls to endpoints defined in `backend/app.py`. All API endpoints are prefixed with `/api/`.
