The `scraper_service.py` acts as the primary service layer interface for fetching course data, managing caching logic, and coordinating scraping efforts. It achieves this by heavily relying on functions exported by `workflow_helpers.py`.

**High-Level Interaction:**

The core interaction revolves around executing the actual scraping logic. `scraper_service.py` orchestrates when and how scraping occurs based on database metadata (checking if data is up-to-date, checking for previous failures).

1.  **Core Scraping Execution:**
    *   `scraper_service.get_course_data_and_update_cache` calls `workflow_helpers.scrape_course_data_core(..., skip_grace_period_logic=False)`.
    *   `scraper_service.force_recheck_course` calls `workflow_helpers.scrape_course_data_core(..., skip_grace_period_logic=True)`.
    *   This shows that `workflow_helpers.py` contains the **centralized, reusable logic** for the entire scraping and data processing pipeline, while `scraper_service.py` provides the **business logic wrapper** (caching checks, authentication handling, error reporting) around that core function.

2.  **Metadata and Period Logic Usage:**
    *   `scraper_service.py` imports and uses several helper functions from `workflow_helpers.py` for decision-making *before* scraping:
        *   `is_course_up_to_date` (used in `get_course_data_and_update_cache`).
    *   Crucially, `workflow_helpers.py` has been significantly expanded to include the advanced, detailed logic previously implied to be elsewhere (or newly implemented), specifically:
        *   It defines and uses `scrape_course_data_core` (which appears to be the function that was previously imported and used by `scraper_service.py`).
        *   It defines `get_all_links_by_section`, which handles complex pagination/section fallback logic.

**Component-Level Relationship:**

*   **Backend Structure Shift:** The existence of `scrape_course_data_core` in *both* files suggests a refactoring or migration. In the source (`scraper_service.py`), `scrape_course_data_core` is imported, implying it lived elsewhere (perhaps `workflow_helpers.py` previously contained only simple helpers). In the target (`workflow_helpers.py`), `scrape_course_data_core` is now fully defined, implementing complex link collection strategies (`get_all_links_by_section`) and data persistence (`update_course_data`).
*   **Dependency Reversal/Consolidation:** `workflow_helpers.py` has absorbed the primary, complex scraping orchestration logic (`scrape_course_data_core`).
*   **Service Layer Dependency:** `scraper_service.py` remains dependent on `workflow_helpers.py` to execute the actual scraping work, but it now delegates the entire scraping process, rather than just calling a core function that might have relied on external scraping modules.

In summary, `scraper_service.py` is the **Controller/Service Layer** that manages state and caching decisions, while `workflow_helpers.py` has evolved to become the **Scraping Orchestrator**, containing the detailed, multi-phased logic for link gathering and data extraction.