# Refactoring Plan

This document outlines a plan to refactor the course evaluation scraper to improve modularity, reduce complexity, and increase maintainability.

## 1. Configuration Management

### Problem
The `department_code` and the `course_number` range are currently hardcoded in `main.py`. This makes it difficult to change the target courses without modifying the source code.

### Proposed Solution
Move the `department_code` and `course_number` range to `config.py`. This will centralize configuration and make it easier to modify.

**`config.py` additions:**
```python
# Target Courses
TARGET_DEPARTMENT = 'EN.601'
COURSE_NUMBER_START = 0
COURSE_NUMBER_END = 999
```

**`main.py` changes:**
```python
from config import TARGET_DEPARTMENT, COURSE_NUMBER_START, COURSE_NUMBER_END

# ...

if __name__ == "__main__":
    for course_number in range(COURSE_NUMBER_START, COURSE_NUMBER_END + 1):
        # ...
```

### Benefits
-   **Centralized Configuration:** All configuration variables are in one place.
-   **Ease of Modification:** No need to change `main.py` to scrape different courses.

## 2. `workflow.py` Complexity

### Problem
The `workflow.py` file is too large and handles multiple responsibilities, including:
-   Loading data and metadata.
-   Checking if a course is up-to-date.
-   Handling paginated vs. non-paginated results.
-   The main scraping loop.

### Proposed Solution
Break down `workflow.py` into smaller, more focused functions and potentially new modules.

#### New `workflow_helpers.py` module
Create a new file `workflow_helpers.py` to house some of the logic currently in `workflow.py`.

**`workflow_helpers.py` contents:**
```python
from data_manager import load_json_file, save_json_file
from period_logic import is_course_up_to_date
from config import METADATA_FILE, DATA_FILE

def initialize_course_metadata(course_code):
    """Initializes metadata for a new course if it doesn't exist."""
    metadata = load_json_file(METADATA_FILE)
    if course_code not in metadata:
        metadata[course_code] = {
            "first_period_gathered": None,
            "last_period_gathered": None,
            "last_period_failed": False,
            "relevant_periods": []
        }
        save_json_file(METADATA_FILE, metadata)
    return metadata[course_code]

def check_course_status(course_code):
    """Checks if a course is up-to-date and returns its metadata."""
    metadata = load_json_file(METADATA_FILE)
    if course_code in metadata:
        course_metadata = metadata[course_code]
        if is_course_up_to_date(course_metadata.get('last_period_gathered'), course_metadata):
            print(f"Course {course_code} is already up-to-date. Skipping workflow.")
            return None, None # Indicate skipping
    
    course_metadata = initialize_course_metadata(course_code)
    data = load_json_file(DATA_FILE)
    return data, course_metadata

# ... other helper functions can be moved here ...
```

#### Refactored `workflow.py`
The main `workflow.py` will be simplified to orchestrate the calls to the new helper functions.

### Benefits
-   **Improved Readability:** Smaller functions are easier to understand.
-   **Better Maintainability:** Changes to one part of the logic are isolated to a smaller area of the code.
-   **Follows Single Responsibility Principle:** Each function will have a single, clear purpose.

## 3. Single Responsibility Principle

### Problem
Several functions are doing more than one thing. For example, the main loop in `workflow.py` handles both the pagination logic and the scraping logic.

### Proposed Solution
Create more specialized functions. For example, create separate functions for handling the paginated and non-paginated scraping loops.

**New functions in `workflow.py`:**
```python
def _scrape_paginated_results(session, course_code, course_metadata, data):
    # ... logic for year-by-year scraping ...

def _scrape_non_paginated_results(session, report_links_dict, course_metadata, data):
    # ... logic for simple scraping ...

def run_scraper_workflow(course_code: str, session):
    data, course_metadata = check_course_status(course_code)
    if data is None:
        return

    report_links_dict = get_evaluation_report_links(session=session, course_code=course_code)

    if len(report_links_dict) >= 20:
        _scrape_paginated_results(session, course_code, course_metadata, data)
    else:
        _scrape_non_paginated_results(session, report_links_dict, course_metadata, data)
    
    # ... final metadata update logic ...
```

### Benefits
-   **Clearer Code:** The purpose of each function is more obvious.
-   **Easier to Test:** Smaller, focused functions are easier to unit test.

## 4. Code Duplication

### Problem
The scraping loop for paginated and non-paginated results in `workflow.py` is very similar. This violates the DRY (Don't Repeat Yourself) principle.

### Proposed Solution
Create a single, reusable function that encapsulates the common scraping logic.

**New function in `workflow.py`:**
```python
def _scrape_and_save_report(instance_key, link_url, session, data, course_metadata):
    """Scrapes a single report, saves the data, and updates metadata."""
    if instance_key in data:
        return True # Already scraped

    print(f"Scraping new report: {instance_key}")
    scraped_data = scrape_evaluation_data(link_url, session)

    if scraped_data:
        data[instance_key] = scraped_data
        save_json_file(DATA_FILE, data)
        
        # Update metadata
        if instance_key not in course_metadata['relevant_periods']:
            course_metadata['relevant_periods'].append(instance_key)
        
        period = get_period_from_instance_key(instance_key)
        if period:
            course_metadata['last_period_gathered'] = period
            if not course_metadata.get('first_period_gathered'):
                course_metadata['first_period_gathered'] = period
        
        course_metadata['last_period_failed'] = False
        save_json_file(METADATA_FILE, {"course_code": course_metadata}) # Simplified for example
        print(f"Successfully scraped and stored {instance_key}.")
        return True
    else:
        print(f"Failed to scrape {instance_key}.")
        course_metadata['last_period_failed'] = True
        save_json_file(METADATA_FILE, {"course_code": course_metadata})
        return False
```

This function can then be called from both `_scrape_paginated_results` and `_scrape_non_paginated_results`.

### Benefits
-   **Reduced Code:** Less code to maintain.
-   **Single Point of Change:** If the scraping logic needs to be updated, it only needs to be changed in one place.

## Summary of Proposed Changes

1.  **`config.py`**: Add `TARGET_DEPARTMENT`, `COURSE_NUMBER_START`, and `COURSE_NUMBER_END`.
2.  **`main.py`**: Import configuration from `config.py` and use it to drive the main loop.
3.  **`workflow_helpers.py` (New File)**: Create this file to hold helper functions for `workflow.py`.
4.  **`workflow.py`**: Refactor to use the new helper functions and the new `_scrape_and_save_report` function. Break down the main function into smaller, more focused functions.
