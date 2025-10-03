The `backend/scrape_link.py` module **consumes** configuration constants defined in `backend/config.py` to manage its scraping reliability and retry mechanisms.

**Functionality Used:**
1.  **Scraping Reliability Constants:** It imports `MAX_RETRIES` and `INITIAL_RETRY_DELAY` from `config.py`.

**Interaction Pattern:**
*   `scrape_link.py` uses these imported constants within its `scrape_evaluation_data` function to control the exponential backoff strategy (`INITIAL_RETRY_DELAY` is the starting point, and it doubles) and to set the maximum number of attempts (`MAX_RETRIES`) before giving up on scraping a specific URL.

**Component Relationship:**
*   `config.py` acts as a centralized source of application-wide parameters, specifically concerning scraping behavior (how aggressively or cautiously to retry network operations).
*   `scrape_link.py` is a consumer module that relies on these configuration values to implement robust, fault-tolerant network requests.