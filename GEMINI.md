# GEMINI.md: JHU Course Evaluation Analyzer

## 1. Project Overview

This project is a full-stack web application designed to scrape, analyze, and display course evaluation data from Johns Hopkins University.

- **Backend**: A Python server using the **Flask** web framework. It exposes a REST API for the frontend to consume. Its primary responsibilities include:
    - Scraping course evaluation data from the JHU EvaluationKIT website using **Requests** and **BeautifulSoup**.
    - Caching scraped data and metadata in local JSON files (`data.json`, `metadata.json`).
    - Performing on-demand data analysis, filtering, and aggregation.

- **Frontend**: A modern single-page application (SPA) built with **React**. It provides the user interface for searching, displaying, and interacting with the evaluation data.

- **Architecture**: The application follows a classic client-server model. The React frontend is the user-facing client, and the Flask backend serves as the data provider and processing engine. The core scraping logic is centralized in `workflow_helpers.py`.

## 2. Project Structure

```
.
├── backend/                 # Python/Flask backend
│   ├── app.py              # Main Flask application with API endpoints
│   ├── requirements.txt    # Python dependencies
│   └── ...
├── frontend/               # React frontend
│   ├── src/                # Source code
│   │   └── App.js          # Main application component
│   ├── package.json        # Node.js dependencies and scripts
│   └── ...
├── config.py               # Application configuration constants
├── data_manager.py         # JSON file loading/saving utilities
├── period_logic.py         # Academic period handling logic
├── workflow_helpers.py     # Core scraping workflow logic
├── data.json               # Main data storage (scraped evaluations)
├── metadata.json           # Course metadata (scraping status tracking)
└── run_all.sh              # Script to run the entire application
```

## 3. Technologies Used

#### Backend
- Python 3.x
- Flask
- BeautifulSoup4
- Requests
- Gunicorn

#### Frontend
- React 19
- JavaScript (JSX)
- CSS

## 4. Key Features

- **Course Search**: Search by course code or name.
- **Data Scraping**: Automated, on-demand scraping of JHU course evaluation reports.
- **Data Analysis**: Filter and separate evaluation data by various criteria (year, season, instructor).
- **Course Grouping**: Automatically groups evaluations for equivalent courses (e.g., 400/600 level).
- **Grace Period Handling**: Smartly handles evaluation release schedules to avoid unnecessary scraping while ensuring data is fresh.

## 5. Building and Running

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

1.  **Install dependencies from the project root:**
    ```bash
    pip install -r backend/requirements.txt
    ```
2.  **Start the server from the project root:**
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

## 6. Architecture & Development Conventions

- **Modular Structure**: The Python code is organized into modules with specific responsibilities:
    - `backend/app.py`: Flask API routing.
    - `backend/scraper_service.py`: High-level service logic that connects the API to the core scraping workflow.
    - `workflow_helpers.py`: The central orchestrator for the entire scraping and data storage process.
    - `scrape_search.py` / `scrape_link.py`: Low-level modules for specific scraping tasks.
    - `period_logic.py`: Handles time-based logic for evaluation periods.
    - `config.py`: Stores shared constants like URLs and file paths.

- **Data Storage**: The application uses a simple file-based storage system:
    - `data.json`: A large JSON file containing all raw scraped evaluation data.
    - `metadata.json`: Stores metadata for each course, including when it was last scraped.
    - `failed.json`: Logs any scraping attempts that failed.
    - **Note**: This file-based approach is a major performance bottleneck. Migrating to a database is a key area for improvement.

- **API Communication**: The frontend communicates with the backend via REST API calls to endpoints defined in `backend/app.py`. All API endpoints are prefixed with `/api/`.

## 7. API Endpoints

- `GET /api/course/<course_code>`: Get all evaluation data for a course.
- `GET /api/search/course_name/<query>`: Search for courses by name.
- `GET /api/search/instructor/<name>`: Find variations of an instructor's name.
- `GET /api/grace-status/<course_code>`: Check if a course is in a grace period for new evaluations.
- `POST /api/recheck/<course_code>`: Force a re-scrape of a course during its grace period.
- `POST /api/analyze/<course_code>`: Perform filtering and separation analysis on course data.
