The `backend/period_logic.py` module **consumes** configuration constants defined in `backend/config.py`.

**Functionality Used:**
1.  **`PERIOD_RELEASE_DATES`**: Used in `get_current_period()` to determine the current evaluation period based on today's date relative to predefined release dates for 'FA', 'SP', 'SU', and 'IN' terms. It is also used in `is_grace_period_over()` to calculate the exact release date for a given period string.
2.  **`PERIOD_GRACE_MONTHS`**: Used in `is_grace_period_over()` to calculate the end date of the grace period for a specific term by adding a defined number of months to the release date.

**Interaction Pattern:**
This is a classic **consumer/configuration dependency**. `period_logic.py` relies entirely on the constants exported by `config.py` to implement time-sensitive scheduling and date calculations related to course evaluation cycles. The import statement `from .config import PERIOD_RELEASE_DATES, PERIOD_GRACE_MONTHS` establishes this dependency.

**Component Relationship:**
`config.py` acts as the central source of truth for temporal rules governing when data becomes available or when updates should be considered current. `period_logic.py` implements the business logic that interprets these rules.