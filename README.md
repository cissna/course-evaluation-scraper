# JHU Course Evaluation Analyzer

This project is a web application for analyzing course evaluation data from Johns Hopkins University. It consists of a Python/Flask backend that scrapes and caches data, and a React frontend for user interaction.

## Running the Application Locally

To run the application, you will need to start both the backend and frontend servers.

### Backend (Flask API)

1.  **Navigate to the `backend` directory:**
    ```bash
    cd backend
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Flask server:**
    ```bash
    python3 app.py
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

1.  Open your browser to `http://localhost:3000`.
2.  Enter a course code (e.g., `AS.180.101`) or a course name (e.g., `Introduction to Psychology`) into the search bar.
3.  Click the "Search" button to fetch and display the data.
4.  Use the toggle buttons and advanced options to filter and separate the data as needed.
5.  Click the "Download as CSV" button to save the current view of the data.
