**Parameters:**
- None

**Returns:**
- `requests.Session`: A `requests.Session` object containing the necessary authentication cookies and headers obtained from a successful response from `AUTH_URL`.

**Raises:**
- `requests.exceptions.RequestException`: This function will raise an exception (or a subclass like `HTTPError` or `Timeout`) if the authentication request fails. This can happen due to network errors, the server returning an error status code (4xx or 5xx), or the request timing out.

**Implementation Details (Line-by-Line):**

1.  **`session = requests.Session()`**
    - An instance of `requests.Session` is created. A Session object is used to persist parameters, and most importantly, cookies across multiple requests made from that instance. This is critical for maintaining an authenticated state.

2.  **`auth_response = session.get(AUTH_URL, timeout=10)`**
    - A `GET` request is sent to the `AUTH_URL`. This is the key step where the server is expected to respond with session cookies (`Set-Cookie` header) that authenticate the client.
    - `timeout=10`: A timeout of 10 seconds is specified for the request to prevent the application from hanging indefinitely if the authentication endpoint is unresponsive.

3.  **`auth_response.raise_for_status()`**
    - This is a critical error-handling step. It checks if the HTTP response status code indicates success (i.e., is in the 2xx range). If the status code is a client error (4xx) or server error (5xx), it will raise an `requests.exceptions.HTTPError`. This ensures that the function fails immediately and explicitly if authentication is not successful.

4.  **`print("Authentication session created successfully.")`**
    - Upon a successful (2xx) response, a confirmation message is printed to standard output. This serves as a useful log for debugging and monitoring.

5.  **`return session`**
    - The function returns the `session` object. This object now holds the authentication cookies from the server and can be used by other parts of the application to make authenticated requests to the scraping targets.