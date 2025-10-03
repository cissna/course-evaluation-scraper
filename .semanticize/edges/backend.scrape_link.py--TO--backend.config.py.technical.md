The file `backend/scrape_link.py` imports two specific variables from the module `backend/config.py` (implicitly, as it uses a relative import `.config`):

1.  **`MAX_RETRIES`**: Imported and used in `scrape_evaluation_data` to control the maximum number of times the scraping loop will attempt to fetch data, especially upon failure or missing critical content.
    *   **Usage in `scrape_link.py`**: The `while attempt < MAX_RETRIES:` loop condition.
    *   **Definition in `config.py`**: `MAX_RETRIES = 8`.

2.  **`INITIAL_RETRY_DELAY`**: Imported and used to set the starting delay for exponential backoff during retries.
    *   **Usage in `scrape_link.py`**: Initialized as `delay = INITIAL_RETRY_DELAY` before the retry loop starts.
    *   **Definition in `config.py`**: `INITIAL_RETRY_DELAY = 0.5`.

This relationship is strictly one-way: `scrape_link.py` **consumes** configuration constants defined in `config.py` to manage its retry and reliability logic.