# Utility Functions for Year and Period Calculation (`yearUtils.js`)

This module provides essential utility functions for determining the current academic period based on specific release date logic and calculating time-based year ranges, primarily for historical data retrieval (e.g., "last 3 years"). The logic closely mirrors backend period determination found in `config.py` and `period_logic.py`.

## Constants

### `PERIOD_RELEASE_DATES`

| Key | Description | Release Date (MM/DD) |
| :--- | :--- | :--- |
| `IN` | Intersession | 01/15 |
| `SP` | Spring | 05/15 |
| `SU` | Summer | 08/15 |
| `FA` | Fall | 12/15 |

This constant defines the cutoff dates for determining which academic period is currently active.

## Functions

### `getCurrentPeriod()`

**Summary:**
Determines the active academic term based on the current system date, adhering strictly to predefined period release dates. This function replicates backend logic to ensure frontend reporting aligns with backend data availability windows.

**Big Picture Understanding:**
It answers the question: "Based on today's date, which academic period (e.g., FA25, SP24) is considered the current one?"

**Interaction Patterns:**
1. Fetches the current month and day.
2. Iterates through the defined periods (`FA`, `SU`, `SP`, `IN`) in reverse chronological order of their release dates.
3. If the current date passes a period's release date, that period string (e.g., "FA25") is returned.
4. If the current date is before the first period of the current calendar year (January 15th), it defaults to the Fall period of the *previous* calendar year (e.g., if it's Jan 10, 2025, it returns "FA24").

### `convertToFullYear(yearShort)`

**Summary:**
Converts a two-digit year representation into a four-digit year (e.g., 25 -> 2025, 95 -> 1995).

**Big Picture Understanding:**
This function enforces a specific century convention for legacy or short-form year inputs, typically used in period strings: years 00-69 map to 2000s, and years 70-99 map to 1900s.

**Interaction Patterns:**
Used internally by `calculateLast3YearsRange` to resolve the 2-digit year extracted from the period string into an absolute year value.

### `calculateLast3YearsRange()`

**Summary:**
Calculates a time range representing the "last 3 years" relevant for historical reporting, adjusting the start year based on the current academic period structure.

**Big Picture Understanding:**
This function computes a safe, inclusive range (`min_year`, `max_year`) to query historical academic data. The calculation is sensitive to the current period: if the current period is Intersession (`IN`), the baseline year for subtraction is shifted back one year to ensure the range correctly spans three full academic cycles.

**Interaction Patterns:**
1. Calls `getCurrentPeriod()` to establish the temporal context.
2. Extracts the period type (e.g., 'FA') and short year (e.g., 25).
3. Determines the `baseYear` (4-digit year of the current period). If the period is `IN`, the `baseYear` is decremented by 1.
4. Sets `min_year` to `baseYear - 2`.
5. Sets `max_year` to the current calendar year derived from `new Date()`.
6. Returns an object `{ min_year, max_year }`.