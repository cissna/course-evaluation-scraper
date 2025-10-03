The relationship is a direct dependency where `backend/scraping_logic.py` imports a constant value, `AUTH_URL`, from `backend/config.py`.

**Technical Details:**

1.  **Import:** `backend/scraping_logic.py` contains the line:
    ```python
    from .config import AUTH_URL
    ```
    This uses a relative import, indicating that `config.py` is in the same package/directory (`backend/`).

2.  **Usage in Source (`scraping_logic.py`):** The imported constant `AUTH_URL` is used as the target URL in an HTTP GET request within the `get_authenticated_session` function:
    ```python
    auth_response = session.get(AUTH_URL, timeout=10)
    ```

3.  **Definition in Target (`config.py`):** `backend/config.py` defines `AUTH_URL` as a string constant:
    ```python
    AUTH_URL = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
    ```

**Data Flow:**
The value of `AUTH_URL` is read from `config.py` during module loading in `scraping_logic.py` and is passed as an argument to the `session.get()` method when `get_authenticated_session` is executed.