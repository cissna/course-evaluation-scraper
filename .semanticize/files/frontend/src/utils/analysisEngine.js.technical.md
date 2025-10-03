# Technical Documentation: `frontend/src/utils/analysisEngine.js`

This file serves as the JavaScript port of a Python analysis engine, responsible for filtering, grouping, and calculating aggregate statistics (like mean and standard deviation) from raw course evaluation data instances.

It primarily deals with mapping categorical survey responses to numerical values for statistical computation.

---

## Constants

### `STAT_MAPPINGS`

This constant object defines the configuration for various statistical metrics derived from survey responses. Each entry specifies a human-readable display name and a numerical mapping for categorical string responses to numerical scores (typically 1 to 5).

| Key (Internal Metric Name) | `displayName` | `mapping` Structure | Notes |
| :--- | :--- | :--- | :--- |
| `overall_quality` | "Overall Quality" | `{"Poor": 1, ..., "Excellent": 5}` | Standard 5-point scale. |
| `instructor_effectiveness` | "Instructor Effectiveness" | `{"Poor": 1, ..., "Excellent": 5}` | Standard 5-point scale. |
| `intellectual_challenge` | "Intellectual Challenge" | `{"Poor": 1, ..., "Excellent": 5}` | Standard 5-point scale. |
| `workload` | "Workload" | `{"Much lighter": 1, ..., "Much heavier": 5}` | 5-point scale for perceived workload. |
| `feedback_frequency` | "Helpful Feedback" | `{"Disagree strongly": 1, ..., "Agree strongly": 5}` | 5-point scale for agreement/feedback helpfulness. |
| `ta_frequency` | "TA Quality" | `{"Poor": 1, ..., "Excellent": 5}` | Standard 5-point scale for TA quality. |
| `periods_course_has_been_run` | "Periods Course Has Been Run" | `{}` (Empty) | Special case handled separately; does not use numerical mapping. |

---

## Helper Functions

### `simplifyName(name)`

**Purpose:** Sanitizes a string (typically an instructor's name) by removing all non-alphabetic characters and converting it to lowercase. This is used to create consistent, simplified keys for grouping or comparison.

**Parameters:**
* `name` (string): The input name string.

**Returns:**
* (string): The simplified, lowercased, alphabetic-only string, or an empty string if the input is not a string.

**Implementation Details:**
Uses `String.prototype.replace` with the regex `/[^a-zA-Z]/g` to match and remove anything that is not an uppercase or lowercase letter globally, followed by `toLowerCase()`.

### `parseSemesterYear(instanceKey)`

**Purpose:** Extracts structured semester and year information from a course instance key, which is assumed to follow a pattern like `...[SEMESTER][YY]`.

**Parameters:**
* `instanceKey` (string): The unique identifier for the course instance (e.g., `CS.101.01.FA23`).

**Returns:**
* (Object): An object containing:
    * `year` (number): The full four-digit year (e.g., 2023).
    * `semesterNum` (number): An ordered index for the semester (0=IN, 1=SP, 2=SU, 3=FA).
    * `semester` (string | null): The two-letter abbreviation (e.g., "FA").
    * Returns `{ year: 0, semesterNum: 0, semester: null }` if the pattern does not match.

**Implementation Details:**
Uses regex `/\.((?:IN|SP|SU|FA))(\d{2})$/` to capture the season code and the last two digits of the year at the end of the string, preceded by a dot. It assumes years starting with `20XX`.

### `getInstanceYear(instanceKey)`

**Purpose:** Extracts and returns the full four-digit year from an instance key.

**Parameters:**
* `instanceKey` (string): The course instance key.

**Returns:**
* (number): The calculated year (e.g., 2023), defaulting to 2000 if parsing fails.

### `getInstanceSeason(instanceKey)`

**Purpose:** Extracts the full name of the semester season from an instance key.

**Parameters:**
* `instanceKey` (string): The course instance key.

**Returns:**
* (string): The full season name (e.g., "Fall", "Spring"), defaulting to "Unknown".

**Implementation Details:**
Uses a map `seasons = {"FA": "Fall", "SP": "Spring", "SU": "Summer", "IN": "Intersession"}` to translate the two-letter code captured by regex `/\.((?:IN|SP|SU|FA))\d{2}$/`.

---

## Core Logic Functions

### `filterInstances(allInstances, filters)`

**Purpose:** Filters a collection of course instances based on provided criteria (year range, seasons, instructors).

**Parameters:**
* `allInstances` (Object): A map where keys are instance keys and values are instance data objects.
* `filters` (Object): Criteria object containing:
    * `min_year` (string | null)
    * `max_year` (string | null)
    * `seasons` (Array<string>): List of season names (e.g., ["Fall", "Spring"]).
    * `instructors` (Array<string>): List of instructor names.

**Returns:**
* (Object): A new map containing only the instances that satisfy all filter conditions.

**How it works:**
Iterates over `allInstances`. For each instance, it checks:
1. Year constraint: Compares `getInstanceYear(key)` against `minYear` and `maxYear`.
2. Season constraint: Checks if `getInstanceSeason(key)` is present in the `seasons` array (if `seasons` is non-empty).
3. Instructor constraint: Checks if `instance.instructor_name` is present in the `instructors` array (if `instructors` is non-empty).
If all checks pass, the instance is included in the result.

### `separateInstances(instances, separationKeys)`

**Purpose:** Groups instances based on one or more specified keys (e.g., 'instructor', 'year', 'season').

**Parameters:**
* `instances` (Object): The map of instances to group.
* `separationKeys` (Array<string>): An array specifying the fields to group by. Supported keys include: "instructor", "year", "season", "exact_period", "course_code", or any property name expected on the instance object.

**Returns:**
* (Object): A map where keys are concatenated group names (e.g., "John Doe, 2023, Fall") and values are arrays of instance objects belonging to that group. Returns `{"All Data": [all instances]}` if `separationKeys` is empty.

**Instructor Handling Detail (Pre-computation):**
If `"instructor"` is in `separationKeys`, the function first iterates through all instances to determine the **most recent display name** associated with each simplified instructor name.
1. It uses `simplifyName` on `instructor_name`.
2. It tracks the latest instance encountered for that simplified name using `parseSemesterYear` for accurate temporal sorting (`tempMap`).
3. `simplifiedToDisplayName` maps the simplified key back to the latest full instructor name found.

**Grouping Logic:**
For each instance, it iterates through every `sepKey` in `separationKeys`:
1. It determines a `value` based on the key (e.g., using `getInstanceYear`, `getInstanceSeason`, or looking up the instructor name in `simplifiedToDisplayName`).
2. These values are joined by `, ` to form the final `groupName`.
3. The instance is pushed into `groups[groupName]`.

### `calculateDetailedStatistics(frequencyDict, valueMapping)`

**Purpose:** Computes the mean, standard deviation, and count ($N$) for a set of numerical data points derived from frequency counts.

**Parameters:**
* `frequencyDict` (Object): A map where keys are categorical responses (strings) and values are their counts (numbers).
* `valueMapping` (Object): A map translating the string responses to numerical scores (e.g., `{"Good": 4, "Poor": 1}`).

**Returns:**
* (Object): `{ mean: number | null, std: number | null, n: number }`.

**Algorithm:**
1. **Data Expansion:** Creates an array `dataPoints` by repeating the numerical score (`valueMapping[response]`) according to its count in `frequencyDict`.
2. **Total Count ($N$):** Sums all counts (`totalResponses`).
3. **Mean Calculation:** Standard arithmetic mean: $\mu = \frac{1}{N} \sum x_i$.
4. **Standard Deviation Calculation:** Uses the **sample standard deviation** formula:
   $$s = \sqrt{\frac{1}{n-1} \sum_{i=1}^n (x_i - \mu)^2}$$
   If $N \le 1$, standard deviation is 0.
5. **Rounding:** Mean and standard deviation are rounded to two decimal places.

### `calculateGroupStatistics(groupInstances, statsToCalculate, instanceKeys)`

**Purpose:** Aggregates response frequencies across all instances within a group and calculates the final statistics for specified metrics.

**Parameters:**
* `groupInstances` (Array<Object>): Array of instance objects belonging to the group.
* `statsToCalculate` (Array<string>): List of metric keys (e.g., "overall\_quality") for which statistics should be computed.
* `instanceKeys` (Array<string>): The original keys corresponding to `groupInstances`, needed for calculating `periods_course_has_been_run`.

**Returns:**
* (Object): `{ values: Object, details: Object }` containing the calculated mean/result and metadata (N, StdDev).

**How it works:**
1. **Aggregation:** Initializes `aggregatedFrequencies` structured by stat key. It then iterates through all instances in the group, summing up the counts from the raw frequency dictionaries (`instance[freqKey]`) found within each instance object.
2. **Calculation Loop:** Iterates through `statsToCalculate`:
    * **Special Case (`periods_course_has_been_run`):** If the key matches, it gathers all unique two-letter period codes from `instanceKeys` and returns the sorted, comma-separated list size as the result. Metadata $N$ and $Std$ are set to `null`.
    * **Standard Case:** Calls `calculateDetailedStatistics` using the aggregated frequencies and the corresponding `STAT_MAPPINGS[key].mapping`.
3. Results are stored in `results` (means) and `details` (N, std).

---

## Exported Main Function

### `processAnalysisRequest(rawData, params)`

**Purpose:** Orchestrates the entire analysis pipeline: filtering, grouping, and statistical calculation.

**Parameters:**
* `rawData` (Object): Contains the initial data structure:
    * `instances` (Object): All raw course instances.
    * `metadata` (Object)
    * `grouping_metadata` (Object)
* `params` (Object): Request parameters:
    * `filters` (Object): Passed directly to `filterInstances`.
    * `separation_keys` or `separationKeys` (Array<string>): Keys for grouping.
    * `stats` (Object): Map where keys are metric names and values are booleans indicating whether to calculate that statistic (e.g., `{ overall_quality: true }`).

**Returns:**
* (Object): The final structured analysis output:
    ```json
    {
      data: {
        "GroupName1": { metric1: mean1, metric2: mean2, ... },
        // ...
      },
      metadata: { ... }, // Original metadata preserved
      statistics_metadata: {
        "GroupName1": { metric1: { n: count1, std: std1 }, ... },
        // ...
      }
    }
    ```

**Workflow:**
1. **Filtering:** Calls `filterInstances` using `rawData.instances` and `params.filters`.
2. **Separation:** Calls `separateInstances` using the filtered data and separation keys.
3. **Statistical Calculation:** Iterates through each resulting group:
    a. Identifies `statsToSend` (metrics requested by the user).
    b. Retrieves the original keys corresponding to the instances in the current group.
    c. Calls `calculateGroupStatistics` to derive means and metadata for the group.
    d. Stores means in `analysisResults` and metadata in `statisticsMetadata`.
4. **Return:** Combines results into the final output structure.