**Workflow Orchestration to Detailed Data Extraction**

The relationship between `workflow_helpers.py` (the orchestrator) and `scrape_link.py` (the worker) is one of **command and execution**.

1.  **Command:** `workflow_helpers.py` is responsible for finding *which* evaluation reports need to be processed for a given course. It aggregates all necessary report URLs (links) through complex logic involving section and year iteration.
2.  **Execution:** Once `workflow_helpers.py` has a complete list of URLs, it calls the function `scrape_evaluation_data` inside `scrape_link.py` for *each* URL.
3.  **Business Connection:** `workflow_helpers.py` manages the overall course data gathering strategy (when to look, where to look), while `scrape_link.py` handles the detailed, low-level task of visiting a specific link and extracting the clean evaluation metrics (instructor rating, workload, etc.) from that single page. If `scrape_link.py` fails to get the data, it signals this back to the orchestrator in `workflow_helpers.py` so that the main process can decide whether to stop or continue.