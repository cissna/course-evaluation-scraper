# config.py

"""
This file contains all the constants for the course evaluation scraper application.
"""

# File Paths
METADATA_FILE = 'metadata.json'
DATA_FILE = 'data.json'

# Scraping URLs
AUTH_URL = 'https://asen-jhu.evaluationkit.com/Login/ReportPublic?id=THo7RYxiDOgppCUb8vkY%2bPMVFDNyK2ADK0u537x%2fnZsNvzOBJJZTTNEcJihG8hqZ'
BASE_REPORT_URL = 'https://asen-jhu.evaluationkit.com/'
INDIVIDUAL_REPORT_BASE_URL = 'https://asen-jhu.evaluationkit.com/Reports/StudentReport.aspx'

# Incremental Scraping Logic Constants

# A dictionary mapping period prefixes to their release month and day.
# (Month, Day) for when evaluation results are typically released.
PERIOD_RELEASE_DATES = {
    'IN': (1, 15),   # Intersession
    'SP': (5, 15),   # Spring
    'SU': (8, 15),   # Summer
    'FA': (12, 15)  # Fall
}

# A dictionary mapping period prefixes to their grace period in months.
# This is the number of months after the release date during which we should still check for new evaluations.
PERIOD_GRACE_MONTHS = {
    'IN': 1,
    'SP': 1,
    'SU': 2,
    'FA': 1
}

# Scraping Reliability
SCRAPING_DELAY_SECONDS = 0    # No delay between scrapes
MAX_RETRIES = 8               # Maximum number of retries for a failed scrape
INITIAL_RETRY_DELAY = 0.5     # Initial delay in seconds for content loading (will be exponential)
