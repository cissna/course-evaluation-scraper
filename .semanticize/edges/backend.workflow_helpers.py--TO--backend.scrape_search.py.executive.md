The `workflow_helpers.py` file acts as the orchestrator for collecting course evaluation data. It relies heavily on the function `get_evaluation_report_links` imported from `scrape_search.py` to find the initial web links pointing to individual evaluation reports for a given course.

**Business Connection:**

`workflow_helpers.py` drives the core data acquisition process. To ensure it gathers *all* available historical data for a course, it uses the function from `scrape_search.py` for initial link discovery. If the initial search reveals that the data is paginated (meaning there are "Show more results" buttons), `workflow_helpers.py` calls the link-finding function again, this time passing specific year filters, or it resorts to iterating through every possible section number to guarantee comprehensive coverage.

In essence, **`scrape_search.py` provides the necessary tool (the link finder) for the workflow engine (`workflow_helpers.py`) to locate the specific web addresses it needs to visit and scrape.**