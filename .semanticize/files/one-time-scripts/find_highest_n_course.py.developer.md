# Developer Documentation: `find_highest_n_course.py`

This script is a one-time utility designed to analyze the `data.json` file, group courses based on a defined service, calculate the total number of responses (`N`) for each course group using the 'Overall Quality' statistic, and report the top 10 groups with the highest response counts.

## Big Picture Understanding

The script bridges raw course instance data (from `data.json`) with a predefined course grouping logic (via `CourseGroupingService`). Its primary goal is to determine which logical course groups have the largest sample size (`N`) based on aggregated survey responses, specifically focusing on the 'Overall Quality' metric to calculate `N`. This is useful for identifying the most robustly evaluated courses or course groups.

## Dependencies and Setup

1.  **Path Setup:** The script dynamically modifies `sys.path` to include the parent directory's `backend` folder. This is crucial for importing `CourseGroupingService`.
2.  **Data Source:** Relies on a local file named `../data.json` containing course instance data keyed by instance identifiers.
3.  **Grouping Logic:** Depends on the externally defined `CourseGroupingService` class.

---

## Function Summaries

### `calculate_detailed_statistics(frequency_dict: dict, value_mapping: dict) -> dict`

**Component Role:** Statistical calculation utility.

**Summary:** This function takes a frequency map (e.g., counts per response text like {"Good": 10, "Poor": 2}) and a numerical mapping (e.g., {"Good": 4, "Poor": 1}) and converts the categorical data into quantitative statistics. It calculates the total count (`n`), the weighted mean, and the sample standard deviation ($\sigma$) based on the assigned numerical values.

**High-Level Interaction:** It is used internally by `main()` to convert the aggregated frequency counts for 'Overall Quality' into a total response count (`n`) needed for ranking.

### `extract_base_course_code(instance_key)`

**Component Role:** Data parsing utility.

**Summary:** This function isolates the canonical base identifier for a course from its full, time/section-specific instance key (e.g., extracting `EN.553.421` from `EN.553.421.01.FA22`). It uses regular expressions to enforce a specific format for the base code.

**High-Level Interaction:** Called repeatedly in `main()` when iterating over keys in `data.json` to normalize instance keys before grouping.

---

## Main Execution (`main` function)

**Component Role:** Orchestration and Reporting.

**Summary:** The `main` function executes the core logic:
1.  Loads course instance data from `data.json`.
2.  Initializes `CourseGroupingService`.
3.  Identifies all unique *base course codes* present in the data.
4.  Iterates through each base code:
    a.  Uses `grouping_service.get_grouped_courses(base_code)` to find all related courses that should be analyzed together.
    b.  Aggregates the `overall_quality_frequency` data across all instances belonging to that course group.
    c.  Calculates the total response count (`N`) for the aggregated group using `calculate_detailed_statistics`.
    d.  Assigns a descriptive key (base code or group identifier) to the calculated `N`.
5.  Sorts all computed groups by $N$ in descending order and prints the top 10 results to the console.

**High-Level Interaction:** This function drives the entire analysis pipeline, relying heavily on external services (`CourseGroupingService`) and statistical helpers to produce the final ranked output.