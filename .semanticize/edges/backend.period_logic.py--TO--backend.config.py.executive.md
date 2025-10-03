The `backend/period_logic.py` module relies on configuration constants defined in `backend/config.py` to manage time-sensitive business logic related to academic periods.

Specifically, `period_logic.py` imports and uses:
1.  **`PERIOD_RELEASE_DATES`**: This configuration dictates *when* specific academic periods (like Fall 'FA' or Spring 'SP') are officially released. The `get_current_period` function directly uses these dates to determine the active semester based on today's calendar date.
2.  **`PERIOD_GRACE_MONTHS`**: This configuration defines how long after the release date the system should continue checking for updates related to that specific period. The `is_grace_period_over` function uses this setting to calculate when the evaluation window for a historical period is officially closed.

**Business Connection:**
This relationship ensures that the system's understanding of the "current" academic term, and how long it should actively monitor for new results from past terms, is centrally controlled and easily adjustable via the `config.py` file, separating operational rules from execution logic.