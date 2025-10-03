The `workflow_helpers.py` file orchestrates the overall data acquisition process for a course. It relies on the `scraping_logic.py` file to provide a critical utility function: `get_authenticated_session`.

**Business Relationship:**

The workflow helper needs a verified, active connection to the external system (the "session") before it can attempt to find or download any course evaluation data. The `scraping_logic` module is responsible for handling the low-level technical details of establishing this secure, authenticated connection.

In simple terms: **The Workflow needs a valid ID/Key to enter the system; the Scraping Logic module provides that valid ID/Key.**