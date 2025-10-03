The file `backend/period_logic.py` has a direct technical dependency on `backend/config.py` through relative imports.

**Specific Imports and Usage:**

1.  **Import Statement:**
    In `backend/period_logic.py`, the following line imports specific variables from `backend/config.py`:
    ```python
    from .config import PERIOD_RELEASE_DATES, PERIOD_GRACE_MONTHS
    ```
    This establishes a dependency where `period_logic.py` requires the existence and structure of these two variables from `config.py` to function correctly.

2.  **Usage of `PERIOD_RELEASE_DATES`:**
    The variable `PERIOD_RELEASE_DATES` (a dictionary mapping period prefixes like 'FA', 'SP' to release month/day tuples) is used within:
    *   `get_current_period()`: To determine the current period based on today's date relative to the defined release dates.
    *   `is_grace_period_over()`: To fetch the release month and day for a specific period string.

3.  **Usage of `PERIOD_GRACE_MONTHS`:**
    The variable `PERIOD_GRACE_MONTHS` (a dictionary mapping period prefixes to an integer number of grace months) is used within:
    *   `is_grace_period_over()`: To calculate the end date of the grace period by adding the specified number of months to the release date.

**Data Flow and Interaction:**

The interaction is one-way: `backend/config.py` defines configuration constants, and `backend/period_logic.py` imports and consumes these constants to execute time-sensitive logic (determining the current period, checking grace periods). No data flows back from `period_logic.py` to modify definitions in `config.py`.