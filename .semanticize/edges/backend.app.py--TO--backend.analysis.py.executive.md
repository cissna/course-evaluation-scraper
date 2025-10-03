The `backend/app.py` file (the main API server) directly imports and utilizes functions from `backend/analysis.py` when handling the `/api/analyze/<course_code>` endpoint.

**Relationship:** **Execution Dependency/Service Provider**

The relationship is that `app.py` acts as the **interface/controller** that receives user requests for course analysis, and `analysis.py` acts as the **specialized processing engine** that performs the complex calculations, filtering, grouping, and statistical derivation required for that analysis.

1.  **Initiation:** `app.py` receives a POST request to `/api/analyze/<course_code>`.
2.  **Data Gathering:** Before calling `analysis.py`, `app.py` gathers the raw course data (by calling `get_course_data_and_update_cache`) and any grouping information.
3.  **Delegation:** `app.py` passes this raw data, along with user-specified parameters (filters, separation keys), to the core function `process_analysis_request` located in `analysis.py`.
4.  **Processing:** `analysis.py` executes the heavy lifting: filtering instances, merging data from grouped courses (if applicable), calculating weighted averages, standard deviations, and determining course metadata.
5.  **Return:** `analysis.py` returns the final structured analysis results back to `app.py`, which then formats this output as a JSON response for the client.

In essence, `app.py` handles HTTP communication and routing, while `analysis.py` handles the core business logic of statistical analysis on the raw course evaluation data.