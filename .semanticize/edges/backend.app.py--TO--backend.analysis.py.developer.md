The `backend/app.py` file, which serves as the main Flask application entry point, interacts with `backend/analysis.py` exclusively through the `analyze_course_data` route handler.

**High-Level Interaction:**

1.  **Initiation:** The client sends a POST request to `/api/analyze/<course_code>` containing JSON analysis parameters (`analysis_params`).
2.  **Data Retrieval:** `app.py` first ensures the course code is valid and then calls `get_course_data_and_update_cache(course_code)` (from `scraper_service`) to fetch the raw evaluation data for the primary course.
3.  **Grouping Context:** `app.py` fetches related course data for grouped courses via `get_course_data_and_update_cache` again and uses the `CourseGroupingService` to assemble a comprehensive `all_instances` dictionary, mimicking the structure expected by the analysis module.
4.  **Analysis Execution:** The core logic is delegated by calling:
    ```python
    # backend/app.py line 313
    course_metadata = extract_course_metadata(
        course_names, 
        course_code, 
        metadata_from_file,
        primary_course_code=course_code,
        primary_course_has_no_data=not all_course_data
    )
    # ...
    return jsonify({
        "raw_data": {
            "instances": all_instances,
            "metadata": {
                "current_name": course_metadata.get("current_name"),
                # ... other metadata fields
            },
            "grouping_metadata": {
                # ... grouping info
            }
        }
    })
    ```
    **Correction based on Target File:** The interaction pattern observed in `app.py` suggests it was *intending* to call a function for metadata extraction, but the actual call shown is to `extract_course_metadata`. However, the target file (`analysis.py`) contains the comprehensive function `process_analysis_request(all_course_data, params, ...)`.

    *In the provided `app.py` code, the call to `extract_course_metadata` seems incomplete for generating the full analysis result structure.* If we assume `app.py` is referencing the functionality that *should* exist in `analysis.py` to produce the final result structure (similar to how `process_analysis_request` is structured in the target file), the interaction is:
    *   `app.py` gathers raw data (`all_instances`) and metadata structure elements.
    *   It calls a function in `analysis.py` (likely `process_analysis_request`, although `app.py` only explicitly imports and calls `extract_course_metadata` in the final return structure shown) to perform filtering, grouping, statistical calculation, and metadata merging.

**Component-Level Relationship:**

*   **`backend/app.py` (Consumer/Orchestrator):** Acts as the API gateway. It handles HTTP requests, input validation, data fetching orchestration (using `scraper_service` and `grouping_service`), and structures the input payload (`all_instances`, `analysis_params`) for the analysis module. It consumes the final structured output from `analysis.py`.
*   **`backend/analysis.py` (Core Logic Provider):** Contains the complex business logic for statistical computation, data filtering, and grouping separation. It relies on utilities like `CourseGroupingService` internally to enrich the data set before calculation. It exposes `process_analysis_request` (the main entry point for complex analysis) and several helper functions (`calculate_detailed_statistics`, `filter_instances`, `separate_instances`, `extract_course_metadata`).

**Specific Import/Usage:**

*   `app.py` imports: `from .analysis import process_analysis_request, extract_course_metadata`.
*   In the `/api/analyze` route, `app.py` calls `extract_course_metadata` (which is also defined in `analysis.py`). *Note: The implementation in `app.py` shows it calculating some grouping structure and then calling `extract_course_metadata` to finalize name data before returning the raw structure, which deviates from using the fully featured `process_analysis_request` defined in the target file.*

**Edge Description based on Target File Content:**

The primary dependency is the consumption of statistical processing and data manipulation functions from `analysis.py`. Specifically, `app.py` relies on `analysis.py` for:

1.  **`extract_course_metadata`**: Used within the `/api/analyze` route to determine the canonical and former names of the course based on the gathered instances.
2.  **`process_analysis_request`**: This function (defined in `analysis.py`) is the intended central processor for the `/api/analyze` endpoint, as it encapsulates filtering, grouping, statistical calculation (`calculate_group_statistics`), and metadata assembly. Although `app.py`'s implementation of `/api/analyze` seems to manually perform some steps that `process_analysis_request` handles (like calling `get_course_data_and_update_cache` repeatedly and manually handling grouping structure), the existence of `process_analysis_request` in the target confirms that the API endpoint relies on this function for the heavy lifting of statistical analysis upon receiving POST data.