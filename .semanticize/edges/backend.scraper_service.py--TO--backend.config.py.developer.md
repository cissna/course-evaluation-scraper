The `backend/scraper_service.py` file imports configuration constants from `backend/config.py` to manage time-based scraping logic.

**Functionality Used:**
The source file imports two specific constants:
1.  `PERIOD_RELEASE_DATES`: Used implicitly for logic that determines if a course is up-to-date (though the direct dependency is via `is_course_up_to_date` which likely uses this, or other logic downstream).
2.  `PERIOD_GRACE_MONTHS`: Used to determine if a course check should be performed within a grace period after the standard release date.

**Interaction Pattern:**
This is a **Dependency Injection/Configuration Read** pattern. `scraper_service.py` (the consumer) relies on `config.py` (the provider) to supply immutable, application-wide settings necessary for its time-sensitive business logic (scheduling and staleness checks).

**Component Relationship:**
`scraper_service.py` depends on `config.py` for operational constants related to scheduling and period definitions. This establishes a one-way dependency where the service logic is configured by the constants defined in the configuration file.