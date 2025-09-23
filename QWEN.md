# JHU Course Evaluation Scraper and Analyzer

## Project Overview

This is a full-stack web application for analyzing course evaluation data from Johns Hopkins University. The project consists of:

1. **Backend (Python/Flask)**: Handles scraping, caching, and serving course evaluation data
2. **Frontend (React)**: Provides a user interface for searching, filtering, and analyzing course evaluations
3. **Data Management**: Stores scraped data in JSON files with metadata tracking

The application scrapes course evaluation data from JHU's evaluation system, processes it, and provides analytical tools for students to make informed course selection decisions.

## Project Structure

```
.
├── backend/                 # Python/Flask backend
│   ├── app.py              # Main Flask application with API endpoints
│   ├── requirements.txt    # Python dependencies
│   ├── scraper_service.py  # Core scraping logic
│   ├── analysis.py         # Data analysis and filtering
│   ├── similarity.py       # Instructor name similarity detection
│   └── course_grouping_service.py  # Course grouping logic
├── frontend/               # React frontend
│   ├── src/                # Source code
│   │   ├── components/     # React components
│   │   ├── utils/          # Utility functions
│   │   └── App.js          # Main application component
│   ├── package.json        # Node.js dependencies and scripts
│   └── public/             # Static assets
├── config.py               # Application configuration constants
├── data_manager.py         # JSON file loading/saving utilities
├── period_logic.py         # Academic period handling logic
├── workflow_helpers.py     # Core scraping workflow logic
├── scraping_logic.py       # Authentication and session management
├── scrape_search.py        # Search result scraping
├── scrape_link.py          # Individual evaluation report scraping
├── data.json               # Main data storage (scraped evaluations)
├── metadata.json           # Course metadata (scraping status tracking)
├── course_groupings.json   # Course grouping definitions
└── README.md               # Project documentation
```

## Technologies Used

### Backend
- Python 3.x
- Flask (web framework)
- BeautifulSoup4 (HTML parsing)
- Requests (HTTP library)
- Gunicorn (WSGI server for production)

### Frontend
- React 19
- JavaScript/JSX
- CSS

## Key Features

1. **Course Search**: Search by course code or name
2. **Data Scraping**: Automated scraping of JHU course evaluation reports
3. **Data Analysis**: Filtering and separation of evaluation data by various criteria
4. **Course Grouping**: Automatic grouping of equivalent courses (e.g., 400/600 level)
5. **Grace Period Handling**: Smart handling of evaluation release schedules
6. **Instructor Grouping**: Grouping of evaluations by instructor variants

## API Endpoints

- `GET /api/course/<course_code>` - Get course evaluation data
- `GET /api/search/course_name/<query>` - Search courses by name
- `GET /api/search/instructor/<name>` - Find instructor name variants
- `GET /api/grace-status/<course_code>` - Check grace period status
- `POST /api/recheck/<course_code>` - Force recheck during grace period
- `POST /api/analyze/<course_code>` - Perform data analysis with filters

## Data Structure

The application stores data in three main JSON files:

1. **data.json**: Contains the actual scraped course evaluation data
2. **metadata.json**: Tracks scraping status, relevant periods, and grace period information for each course
3. **course_groupings.json**: Defines course grouping rules for equivalent courses

## Building and Running

### Backend (Flask API)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask server:
   ```bash
   python3 app.py
   ```
   The backend server will start on `http://127.0.0.1:5000`.

### Frontend (React UI)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Run the React development server:
   ```bash
   npm start
   ```
   The frontend application will open in your browser at `http://localhost:3000`.

## Development Conventions

### Backend
- Follows standard Flask application structure
- Uses modular service pattern (scraper_service, analysis, etc.)
- JSON-based data storage with clear separation of concerns
- Comprehensive error handling and logging

### Frontend
- Component-based React architecture
- State management using React hooks (useState)
- REST API communication with fetch
- Responsive design with CSS

### Data Management
- Metadata tracking for each course's scraping status
- Grace period logic for handling evaluation release schedules
- Period-based data organization (FA23, SP24, etc.)
- Course grouping for equivalent courses across departments/levels

## How to Use

1. Start both the backend and frontend servers
2. Open your browser to `http://localhost:3000`
3. Enter a course code (e.g., `AS.180.101`) or course name into the search bar
4. Click "Search" to fetch and display the data
5. Use the toggle buttons and advanced options to filter and separate the data
6. Click "Download as CSV" to save the current view of the data

## Key Configuration Files

- `config.py`: Contains authentication URLs, academic period definitions, and scraping parameters
- `course_groupings.json`: Defines course grouping rules for equivalent courses
- `metadata.json`: Tracks scraping status for each course
- `data.json`: Stores all scraped course evaluation data