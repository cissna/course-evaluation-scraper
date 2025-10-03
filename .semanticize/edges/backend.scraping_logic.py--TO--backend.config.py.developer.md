The relationship is a **dependency** where `backend/scraping_logic.py` imports and utilizes configuration constants defined in `backend/config.py`.

**High-level Interaction:**
The `scraping_logic.py` module depends on `config.py` to obtain necessary configuration values required for its core functionality—setting up an authenticated HTTP session for scraping.

**Functionality Being Used:**
The specific constant being used is `AUTH_URL`. This URL is required by the `get_authenticated_session()` function to initiate the authentication process via an HTTP GET request using the `requests` library.

**General Interaction Patterns:**
This is a classic configuration import pattern. The logic module (consumer) pulls static configuration data (provider) from the dedicated configuration file. The import statement `from .config import AUTH_URL` establishes this direct dependency.

**Component-level Relationship:**
*   **`backend/config.py`** acts as the **Configuration Provider**, centralizing external parameters (like API endpoints, file names, and scraping parameters).
*   **`backend/scraping_logic.py`** acts as the **Consumer/Client**, specifically using `AUTH_URL` from the configuration file to execute the session establishment logic.