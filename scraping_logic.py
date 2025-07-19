import requests
from config import AUTH_URL

def get_authenticated_session():
    """
    Creates and returns an authenticated requests.Session object.
    This is a simplified version based on the logic in scrapeSearch.py.
    A robust implementation might share the session more directly.
    """
    session = requests.Session()
    try:
        auth_response = session.get(AUTH_URL, timeout=10)
        auth_response.raise_for_status()
        print("Authentication session created successfully.")
        return session
    except requests.exceptions.RequestException as e:
        print(f"Failed to create authenticated session: {e}")
        return None