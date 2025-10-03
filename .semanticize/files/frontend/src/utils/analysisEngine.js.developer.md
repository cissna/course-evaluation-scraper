# Analysis Engine Utility (`frontend/src/utils/analysisEngine.js`)

This module provides the core JavaScript implementation for processing raw course/instance data, applying user-defined filters, grouping the results, and calculating aggregated statistical metrics based on predefined mappings. It serves as the frontend port of the backend analysis logic (originally in Python).

## Core Constants

### `STAT_MAPPINGS`
A static object defining the structure and numerical conversion for various quantitative statistics extracted from course instances.

- **Purpose:** Maps descriptive text responses (e.g., "Poor", "Good") found in the raw instance data frequencies to numerical values (1 through 5) used for calculating means and standard deviations.
- **Structure:** Keys correspond to internal metric names (e.g., `overall_quality`). Each entry contains `displayName` and a `mapping` object translating text responses to integers.
- **Special Case:** `periods_course_has_been_run` has an empty mapping as it is treated specially (counting unique periods rather than calculating a mean).

## Helper Functions

### `simplifyName(name)`
Cleans and normalizes a string, typically an instructor name, for use in stable key generation or comparison.

- **Interaction:** Takes a string, removes all non-alphabetic characters, and converts the result to lowercase.

### `parseSemesterYear(instanceKey)`
Extracts structured semester and year information from a standardized instance key format (e.g., `course.inst.FA23`).

- **Interaction:** Uses regex to find the season code (IN, SP, SU, FA) and two-digit year. It converts this into a structured object containing the full year (e.g., 2023), a numerical semester order (0-3), and the season code.

### `getInstanceYear(instanceKey)`
Extracts the four-digit year from the instance key.

### `getInstanceSeason(instanceKey)`
Extracts the full season name (e.g., "Fall") from the instance key, mapping the two-letter code to its descriptive name.

## Core Processing Functions

### `filterInstances(allInstances, filters)`
Applies user-defined filtering criteria to a map of all available course instances.

- **Components:** Filters based on minimum/maximum year, specified list of seasons, and a list of required instructors.
- **Interaction Pattern:** Iterates over `allInstances`, checks each instance against all provided filter parameters, and returns a new object containing only the matching instances.

### `separateInstances(instances, separationKeys)`
Groups instances based on one or more specified categorization criteria.

- **Components:** Determines grouping keys such as `instructor`, `year`, `season`, `exact_period`, `course_code`, or any other top-level instance property.
- **Interaction Pattern:**
    1. If no keys are provided, all instances are returned under the group "All Data".
    2. It first establishes a canonical display name for instructors if instructor separation is requested (by finding the latest instance associated with that instructor identifier).
    3. It then iterates through instances, constructs a composite group key by joining the values corresponding to each `separationKey`, and buckets the instance into the appropriate group object.

### `calculateDetailedStatistics(frequencyDict, valueMapping)`
Calculates the mean, standard deviation (sample standard deviation), and count ($N$) for a single metric based on its frequency distribution.

- **Interaction Pattern:**
    1. Converts the frequency dictionary (text response $\rightarrow$ count) into an array of numerical data points using the provided `valueMapping`.
    2. Calculates the arithmetic mean.
    3. Calculates the sample standard deviation, avoiding division by zero if $N \le 1$.
    4. Rounds the results to two decimal places.

### `calculateGroupStatistics(groupInstances, statsToCalculate, instanceKeys)`
Aggregates frequency data across all instances within a single group and calculates the final statistics for requested metrics.

- **Interaction Pattern:**
    1. Initializes an aggregation structure for all requested statistics (`statsToCalculate`).
    2. Iterates through `groupInstances`, accumulating the raw frequency counts for each metric specified.
    3. For each metric, it calls `calculateDetailedStatistics` using the aggregated frequencies and the corresponding `STAT_MAPPINGS`.
    4. **Special Handling:** For `"periods_course_has_been_run"`, it uses the provided `instanceKeys` to count the number of unique period codes found in the keys.
    5. Returns two objects: `values` (the calculated means/results) and `details` (the $N$ and $SD$ for each result).

### `processAnalysisRequest(rawData, params)`
The main entry point orchestrating the entire data pipeline from raw input to structured analysis output.

- **Interaction Pattern (Pipeline):**
    1. **Filtering:** Calls `filterInstances` using `rawData.instances` and `params.filters`.
    2. **Grouping:** Calls `separateInstances` on the filtered results using `params.separation_keys`.
    3. **Calculation:** Iterates through each generated group and calls `calculateGroupStatistics` for all metrics enabled in `params.stats`.
    4. **Output Assembly:** Structures the final output into `data` (the group statistics) and `statistics_metadata` (the counts and standard deviations), merging necessary metadata from the input.