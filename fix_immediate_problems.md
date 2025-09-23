# Plan to Fix Immediate Problems

This document outlines a plan to fix the high-priority issues of duplicate constants and brittle import paths. The goal is to improve code consistency and maintainability with minimal structural changes, preserving the ability to run scripts from the project root.

The core of this plan is to establish a single, consistent convention: **all Python processes, including the web server, should be launched from the project's root directory.** This allows Python's module resolution to work naturally without `sys.path` manipulation.

## The Plan

### Step 1: Refactor `backend/scraper_service.py`

This step will centralize configuration and remove path manipulation.

1.  **Remove `sys.path` Manipulation**: Delete the following line:
    ```python
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
    ```
2.  **Remove Duplicated Constants**: Delete the entire `--- Constants (Adapted from config.py) ---` section. This includes the definitions for `PROJECT_ROOT`, `METADATA_FILE`, `DATA_FILE`, `AUTH_URL`, etc.

3.  **Import from `config.py`**: Add an import statement at the top of the file to bring in the constants from the root `config.py`.
    ```python
    from config import METADATA_FILE, DATA_FILE, AUTH_URL, BASE_REPORT_URL, INDIVIDUAL_REPORT_BASE_URL, PERIOD_RELEASE_DATES, PERIOD_GRACE_MONTHS
    ```
4.  **Preserve Absolute Paths**: The original code correctly used absolute paths for file I/O. We will recreate this by defining a project root variable and joining it with the relative paths from `config.py`. Add the following code at the top of `backend/scraper_service.py`:
    ```python
    import os
    # Determine project root relative to this file (backend/scraper_service.py)
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    # Create absolute paths for use in this service
    METADATA_FILE_ABS = os.path.join(PROJECT_ROOT, METADATA_FILE)
    DATA_FILE_ABS = os.path.join(PROJECT_ROOT, DATA_FILE)
    ```
5.  **Update File Usage**: Replace all instances of `METADATA_FILE` and `DATA_FILE` within `scraper_service.py` with `METADATA_FILE_ABS` and `DATA_FILE_ABS` respectively.

### Step 2: Correct an Inconsistent Import in `backend/app.py`

This fixes a problematic import that breaks standard package conventions.

1.  **Locate the line**:
    ```python
    from backend.course_grouping_service import CourseGroupingService
    ```
2.  **Change it to a direct import**, which will work correctly when the app is run from the root directory:
    ```python
    from course_grouping_service import CourseGroupingService
    ```

### Step 3: Update Documentation to Reflect New Convention

To ensure consistency, we must update the project documentation to reflect the new way of running the backend server.

1.  **Modify `README.md` and `GEMINI.md`**:
    - In the "Backend (Flask API)" or "Manual Startup" sections of both files, the instructions will be changed.
    - **Current instruction**: `cd backend` followed by `python3 app.py`.
    - **New instruction**: "From the project root directory, run: `python3 backend/app.py`".

This plan resolves the specified problems by enforcing a cleaner, more standard project structure without significant refactoring. The `run_all.sh` script already aligns with this approach, so it will not require any changes.
