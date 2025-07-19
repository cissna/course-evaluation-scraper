import requests
from config import AUTH_URL

def get_authenticated_session() -> requests.Session:
    """
    Creates and returns an authenticated requests.Session object.

    This function will raise a requests.exceptions.RequestException
    if it fails to get a session.
    """
    session = requests.Session()
    auth_response = session.get(AUTH_URL, timeout=10)
    auth_response.raise_for_status()
    print("Authentication session created successfully.")
    return session