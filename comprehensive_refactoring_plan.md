# Comprehensive Plan: Refactor Repository for Web App Exclusivity

**Objective:** To methodically remove all files, functions, and code related to the batch scraping workflow, ensuring that the repository exclusively serves the web application.

**Guiding Principle:** This is a surgical removal of code. No existing web application functionality will be altered, optimized, or fixed. All potential improvements or discovered bugs will be documented in a separate `potential_improvements.md` file.

---

## Phase 1: Deletion of Batch-Exclusive Files

This phase removes files that are unequivocally part of the batch processing workflow and have no dependencies within the web application.

### Todo:

1.  **Delete `main.py`**:
    *   **Justification**: This is the main entry point for the batch scraping process. It imports `run_scraper_workflow` and is not used by the web app.
    *   **Action**: Delete the file `main.py`.

2.  **Delete `workflow.py`**:
    *   **Justification**: This file defines `run_scraper_workflow`, the high-level orchestrator for the batch process. It is only used by `main.py`.
    *   **Action**: Delete the file `workflow.py`.

3.  **Delete `old_markdown_plans/` directory**:
    *   **Justification**: This directory contains old markdown files that are not part of the web application's functionality.
    *   **Action**: Delete the directory `old_markdown_plans/`.

---

## Phase 2: Surgical Pruning of Shared Modules

This phase involves a meticulous, function-by-function analysis and removal of code from modules that were shared between the batch workflow and the web app.

### Step 2.1: Prune `workflow_helpers.py`

**Analysis**: The `scrape_course_data_core` function in this file is the heart of the scraping logic, used by both the web app (via `scraper_service.py`) and the now-deleted `workflow.py`. However, several helper functions within this file were only ever used to support the more complex, paginated scraping logic required by the batch workflow.

**Todo:**

1.  **Identify and Remove `check_course_status`**:
    *   **Justification**: The function `check_course_status` (lines 244-278) is only imported and used by the now-deleted `workflow.py`. It is not used anywhere in the web application's codebase.
    *   **Action**: Delete the function definition for `check_course_status` from `workflow_helpers.py`.

2.  **Identify and Remove `get_sort_key`**:
    *   **Justification**: The function `get_sort_key` (lines 12-21) is only used on line 170 within `scrape_course_data_core` to sort links chronologically. This sorting is a requirement for the batch process to ensure sequential processing, but it is not necessary for the web app's on-demand scraping.
    *   **Action**: Delete the function definition for `get_sort_key` from `workflow_helpers.py`.

3.  **Identify and Remove `get_all_links_by_section`**:
    *   **Justification**: The function `get_all_links_by_section` (lines 23-67) is a complex fallback mechanism for when the scraper encounters pagination. This was a requirement for the batch scraper to be robust, but the web app's simpler scraping logic does not use this function. It is only called on line 154 of `scrape_course_data_core`.
    *   **Action**: Delete the function definition for `get_all_links_by_section` from `workflow_helpers.py`.

4.  **Simplify `scrape_course_data_core`**:
    *   **Justification**: With the removal of the batch-specific helper functions, the `scrape_course_data_core` function can be significantly simplified. The complex logic for handling pagination (the `else` block from lines 110-160) is now dead code.
    *   **Action**:
        *   In `workflow_helpers.py`, remove the line `sorted_links = sorted(links_to_process.items(), key=get_sort_key)` (line 170). Replace it with `sorted_links = links_to_process.items()`.
        *   Remove the entire pagination handling block from `scrape_course_data_core`. This is the `else` block that starts on line 110 and ends on line 160. The simplified logic should now only contain the "Simple Case" logic (lines 106-109).

### Step 2.2: Prune `period_logic.py`

**Analysis**: This module contains several date and time-related helper functions. Most are used by the web app, but some were exclusively for the batch workflow's more complex logic.

**Todo:**

1.  **Identify and Remove `find_latest_year_from_keys`**:
    *   **Justification**: The function `find_latest_year_from_keys` (lines 30-52) is only used in `workflow_helpers.py` on line 120, inside the pagination logic that is being removed. It is not used by the web app.
    *   **Action**: Delete the function definition for `find_latest_year_from_keys` from `period_logic.py`.

### Step 2.3: Prune `config.py`

**Analysis**: This file contains constants. Some are specific to the batch workflow's reliability features.

**Todo:**

1.  **Identify and Remove Batch-Specific Constants**:
    *   **Justification**: The constants `SCRAPING_DELAY_SECONDS`, `MAX_RETRIES`, and `INITIAL_RETRY_DELAY` (lines 37-39) are used by the robust `scrape_evaluation_data` function in `scrape_link.py`, which was part of the batch workflow. The web app uses a simpler, non-retrying version of this logic.
    *   **Action**: Delete lines 36-39 from `config.py`.

---

## Phase 3: Finalization and Documentation

This phase ensures the project is left in a clean, consistent state.

### Todo:

1.  **Create `potential_improvements.md`**:
    *   **Justification**: To adhere to the principle of not changing functionality, all identified potential improvements must be documented separately.
    *   **Action**: Create a new file named `potential_improvements.md` and add the following content:
        ```markdown
        # Potential Improvements Identified During Refactoring

        This document lists potential improvements that were identified while refactoring the repository to be web-app exclusive. These changes were out of scope for the refactoring task but are recommended for future consideration.

        1.  **Unify `is_course_up_to_date()` Logic**: The version of this function in `period_logic.py` is more robust than the simplified version that was previously used in `scraper_service.py`. The web app could benefit from this more nuanced logic, which handles grace periods correctly.

        2.  **Adopt Robust `scrape_evaluation_data()`**: The version of this function in `scrape_link.py` includes a retry mechanism with exponential backoff, making it more resilient to network errors. The web app currently uses a simpler version; adopting the more robust version would improve reliability.

        3.  **Centralize File Path Logic**: The `config.py` file uses relative paths, while the web app backend requires absolute paths. This logic should be centralized to avoid potential file-not-found errors.
        ```

2.  **Final Verification**:
    *   **Justification**: A final check is necessary to ensure that the refactoring has not inadvertently affected the web application.
    *   **Action**: Briefly review the imports in `backend/app.py` and `backend/scraper_service.py` to confirm that no deleted files or functions are still being referenced.
