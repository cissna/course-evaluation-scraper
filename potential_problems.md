# Potential Problems in Course Evaluation Scraper

## 1. Duplicate Functions
There are several functions that appear to be duplicated across different files:

- [x] **`find_oldest_year_from_keys`** - Defined in both `period_logic.py` and `backend/scraper_service.py`
- [x] **`get_period_from_instance_key`** - Defined in both `period_logic.py` and `backend/scraper_service.py`
- [x] **`load_json_file`** - Defined in both `data_manager.py` and `backend/scraper_service.py`
- [x] **`save_json_file`** - Defined in both `data_manager.py` and `backend/scraper_service.py`
- [ ] **`get_authenticated_session`** - Defined in both `scraping_logic.py` and `backend/scraper_service.py`
- [x] **`scrape_evaluation_data`** - Defined in both `scrape_link.py` and `backend/scraper_service.py`
- [x] **`get_evaluation_report_links`** - Defined in both `scrape_search.py` and `backend/scraper_service.py`

This duplication can lead to maintenance issues where changes need to be made in multiple places.

## 2. Inconsistent Function Usage
Some functions appear to have better implementations in other files but are not being used:
- As noted in `potential_improvements.md`, the `scrape_evaluation_data()` function in `scrape_link.py` includes a retry mechanism with exponential backoff, making it more resilient to network errors, but the web app currently uses a simpler version.

## 3. Potential Dead Code
The `data.json` file contains a very large amount of data (1.1M+ lines) and includes a line that says `"def didnt have one"`, which suggests there might be corrupted or improperly formatted data in the file.

## 4. Unreferenced Files
There are Python files in the repository that don't seem to be imported or used anywhere:
- `config.py` - Doesn't appear to be imported anywhere
- `period_logic.py` - Contains functions that are duplicated in `backend/scraper_service.py`

## 5. Unused Directory
The `random_unused` directory has been removed as it contained several Python scripts and markdown files that were development tools or experiments that were not part of the main application.

## Recommendations

1. Consolidate duplicate functions into a single location and remove duplicates
2. Use the more robust version of `scrape_evaluation_data` from `scrape_link.py` in the main application
3. Clean up `data.json` to remove any corrupted entries
4. Remove truly unused files like `config.py` if they're not needed