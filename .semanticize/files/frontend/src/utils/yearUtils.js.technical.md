# Technical Documentation: `yearUtils.js`

This file contains utility functions for determining academic periods, converting short year representations, and calculating rolling year ranges based on specific institutional period logic, replicating functionality found in a backend configuration (likely `config.py` and `period_logic.py`).

## Constants

### `PERIOD_RELEASE_DATES`

This constant maps academic period codes to their fixed release dates (Month, Day). These dates determine when a given academic period officially begins or becomes the "current" period for evaluation purposes.

| Key (Period Code) | Value (Array: [Month, Day]) | Description |
| :--- | :--- | :--- |
| `'IN'` | `[1, 15]` | Intersession (January 15th) |
| `'SP'` | `[5, 15]` | Spring (May 15th) |
| `'SU'` | `[8, 15]` | Summer (August 15th) |
| `'FA'` | `[12, 15]` | Fall (December 15th) |

---

## Functions

### 1. `getCurrentPeriod()`

Determines the current academic period string (e.g., "FA25") based on the current system date and the static `PERIOD_RELEASE_DATES`. This function strictly replicates the logic of a backend function `get_current_period()`.

**Algorithm:**
The function compares the current month and day against the predefined release dates, checking the periods in reverse chronological order of their release dates (FA, SU, SP, IN).

1.  **Date Initialization:** Captures the current date using `new Date()`.
2.  **Month/Day Extraction:** Calculates `currentMonth` (1-indexed) and `currentDay`.
3.  **Year Short Extraction:** Calculates the 2-digit year (`yearShort = YYYY % 100`).
4.  **Period Check (Descending Order):**
    *   For each period $P$ (FA, SU, SP, IN), it checks if the current date is *after* the release date of $P$.
    *   The condition for being in period $P$ is:
        $$ (CurrentMonth > P_{Month}) \text{ OR } (CurrentMonth = P_{Month} \text{ AND } CurrentDay \ge P_{Day}) $$
    *   If the condition is met, the function immediately returns the period string formatted as $P + yearShort$ (e.g., "FA24").
5.  **Catch-all (Previous Year):** If the current date falls before the release date of the earliest period (`IN` on Jan 15th), it signifies that the current evaluation context is still associated with the last period of the previous academic year (Fall of the preceding year). It returns `FA{yearShort - 1}`.

**Parameters:**
None.

**Returns:**
`{string}`: The current period identifier (e.g., "FA25").

**Line-by-Line Detail:**

| Line | Code | Description |
| :--- | :--- | :--- |
| 13 | `function getCurrentPeriod() {` | Function definition starts. |
| 14 | `const today = new Date();` | Creates a `Date` object for the current system time. |
| 15 | `const currentMonth = today.getMonth() + 1;` | Gets the month (0-indexed) and converts it to 1-indexed (1=Jan, 12=Dec). |
| 16 | `const currentDay = today.getDate();` | Gets the day of the month (1-31). |
| 17 | `const yearShort = today.getFullYear() % 100;` | Extracts the last two digits of the current year (e.g., 2024 -> 24). |
| 19 | `if (currentMonth > PERIOD_RELEASE_DATES['FA'][0] || ...)` | Checks if the date is past the Fall release date (Dec 15). |
| 20 | `(currentMonth === PERIOD_RELEASE_DATES['FA'][0] && currentDay >= PERIOD_RELEASE_DATES['FA'][1]))` | Checks if it is December AND on or after the 15th. |
| 21 | `return \`FA\${yearShort}\`;` | If true, returns Fall period for the current year. |
| 22 | `} else if (currentMonth > PERIOD_RELEASE_DATES['SU'][0] || ...)` | Checks if the date is past the Summer release date (Aug 15). |
| 25 | `return \`SU\${yearShort}\`;` | If true, returns Summer period. |
| 26 | `} else if (currentMonth > PERIOD_RELEASE_DATES['SP'][0] || ...)` | Checks if the date is past the Spring release date (May 15). |
| 29 | `return \`SP\${yearShort}\`;` | If true, returns Spring period. |
| 30 | `} else if (currentMonth > PERIOD_RELEASE_DATES['IN'][0] || ...)` | Checks if the date is past the Intersession release date (Jan 15). |
| 33 | `return \`IN\${yearShort}\`;` | If true, returns Intersession period. |
| 34 | `} else {` | Executes if the date is before Jan 15th. |
| 36 | `return \`FA\${yearShort - 1}\`;` | Returns Fall period of the *previous* year. |
| 37 | `}` | End of function. |

---

### 2. `convertToFullYear(yearShort)`

Converts a 2-digit year representation into a standard 4-digit year based on a specific century cutoff rule frequently used in legacy systems.

**Algorithm:**
This implements a common historical date interpretation rule:
*   If the 2-digit year is $< 70$, the century is 2000 (e.g., `25` -> `2025`).
*   If the 2-digit year is $\ge 70$, the century is 1900 (e.g., `98` -> `1998`).

**Parameters:**
*   `yearShort` (`number`): The 2-digit year (e.g., 25).

**Returns:**
`{number}`: The corresponding 4-digit year (e.g., 2025).

**Line-by-Line Detail:**

| Line | Code | Description |
| :--- | :--- | :--- |
| 41 | `function convertToFullYear(yearShort) {` | Function definition starts. |
| 42 | `if (yearShort < 70) {` | Checks if the short year falls in the 21st century range. |
| 43 | `return 2000 + yearShort;` | Returns the year adjusted to 2000s. |
| 44 | `} else {` | Otherwise, assumes 20th century. |
| 46 | `return 1900 + yearShort;` | Returns the year adjusted to 1900s. |
| 47 | `}` | End of function. |

---

### 3. `calculateLast3YearsRange()` (Exported)

Calculates a recommended range of years for evaluation, defined as the "last 3 years" based on the current academic period context.

**Algorithm:**
This function relies heavily on `getCurrentPeriod()` and `convertToFullYear()` to establish a contextually correct starting point (`baseYear`) before calculating the range boundaries.

1.  **Determine Current Context:** Calls `getCurrentPeriod()` to get the current period string (e.g., "SP24").
2.  **Parse Period:** Extracts the 2-letter period type (`periodType`) and the 2-digit year (`yearShort`).
3.  **Convert to Full Year:** Converts `yearShort` to the 4-digit `periodYear`.
4.  **Establish Base Year:**
    *   If the `periodType` is `'IN'` (Intersession), the academic year calculation is anchored to the *previous* calendar year's end. Therefore, `baseYear = periodYear - 1`.
    *   Otherwise (FA, SP, SU), `baseYear = periodYear`.
5.  **Calculate Range:**
    *   `minYear`: Set to `baseYear - 2`. This establishes the three-year span ending at `baseYear`.
    *   `maxYear`: Set to the current calendar year retrieved from `new Date().getFullYear()`.
6.  **Return:** Returns an object containing the calculated boundaries.

**Parameters:**
None.

**Returns:**
`{Object}`: An object with keys `min_year` and `max_year`.

**Line-by-Line Detail:**

| Line | Code | Description |
| :--- | :--- | :--- |
| 51 | `export function calculateLast3YearsRange() {` | Function definition starts, exported for use elsewhere. |
| 53 | `const currentPeriod = getCurrentPeriod();` | Gets the current period string. |
| 56 | `const periodType = currentPeriod.substring(0, 2);` | Extracts the first two characters (e.g., "FA"). |
| 57 | `const yearShort = parseInt(currentPeriod.substring(2), 10);` | Extracts the numeric part and converts it to an integer (e.g., 25). |
| 59 | `const periodYear = convertToFullYear(yearShort);` | Converts the short year to a 4-digit year. |
| 62 | `const baseYear = periodType === 'IN' ? periodYear - 1 : periodYear;` | Sets the base year: decremented if the current period is Intersession. |
| 65 | `const minYear = baseYear - 2;` | Calculates the minimum year for the range (3 years back from the base). |
| 68 | `const maxYear = new Date().getFullYear();` | Calculates the maximum year as the current calendar year. |
| 71 | `return {` | Returns the result object. |
| 72 | `min_year: minYear,` | |
| 73 | `max_year: maxYear` | |
| 74 | `};` | |