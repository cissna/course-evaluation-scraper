import re
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from config import PERIOD_RELEASE_DATES, PERIOD_GRACE_MONTHS

def find_oldest_year_from_keys(keys: list) -> int:
    """
    Finds the oldest year from a list of course instance codes.
    Assumes year is represented by two digits (e.g., 'FA15' for 2015).
    Returns the oldest year found, or a default if no valid years are found.
    """
    oldest_year = date.today().year
    found_year = False
    
    year_re = re.compile(r'\.(?:FA|SP|SU|IN)(\d{2})$')
    
    for key in keys:
        match = year_re.search(key)
        if match:
            year_short = int(match.group(1))
            # Convert 2-digit year to 4-digit year
            year = 2000 + year_short if year_short < 70 else 1900 + year_short
            if year < oldest_year:
                oldest_year = year
                found_year = True
                
    # If no valid year was found in any key, return a default start year
    return oldest_year if found_year else 2010

def get_period_from_instance_key(instance_key: str) -> str:
    """
    Extracts the period string (e.g., 'FA15') from a full course instance key.
    Example: "EN.601.475.01.FA17" -> "FA17"
    """
    # This regex looks for a period separator, followed by a term code (FA, SP, etc.)
    # and a two-digit year at the end of the string.
    match = re.search(r'\.((?:FA|SP|SU|IN)\d{2})$', instance_key)
    if match:
        # group(1) will capture the content inside the outer parentheses, e.g., "FA17"
        return match.group(1)
    return None

def get_year_from_period_string(period_string: str) -> int:
    """
    Extracts the four-digit year from a period string (e.g., 'FA23' -> 2023).
    """
    if not period_string or len(period_string) < 4:
        return None
    
    year_short = int(period_string[-2:])
    return 2000 + year_short


def get_current_period() -> str:
    """
    Determines the current evaluation period based on today's date.

    Returns:
        str: The current period string (e.g., "FA25").
    """
    today = date.today()
    year_short = today.year % 100

    # Check periods in reverse chronological order of their release dates
    if today.month > PERIOD_RELEASE_DATES['FA'][0] or \
       (today.month == PERIOD_RELEASE_DATES['FA'][0] and today.day >= PERIOD_RELEASE_DATES['FA'][1]):
        return f"FA{year_short}"
    elif today.month > PERIOD_RELEASE_DATES['SU'][0] or \
         (today.month == PERIOD_RELEASE_DATES['SU'][0] and today.day >= PERIOD_RELEASE_DATES['SU'][1]):
        return f"SU{year_short}"
    elif today.month > PERIOD_RELEASE_DATES['SP'][0] or \
         (today.month == PERIOD_RELEASE_DATES['SP'][0] and today.day >= PERIOD_RELEASE_DATES['SP'][1]):
        return f"SP{year_short}"
    elif today.month > PERIOD_RELEASE_DATES['IN'][0] or \
         (today.month == PERIOD_RELEASE_DATES['IN'][0] and today.day >= PERIOD_RELEASE_DATES['IN'][1]):
        return f"IN{year_short}"
    else:
        # If before the first period release of the year, it's the last period of the previous year
        return f"FA{year_short - 1}"

def is_course_up_to_date(last_period_gathered: str, course_metadata: dict) -> bool:
    """
    Checks if the course data is up-to-date.

    Args:
        last_period_gathered (str): The last period for which data was gathered.
        course_metadata (dict): The metadata for the course.

    Returns:
        bool: True if the course data is current, False otherwise.
    """
    current_period = get_current_period()
    return last_period_gathered == current_period

def is_grace_period_over(period: str) -> bool:
    """
    Determines if the grace period for a given period has passed.

    Args:
        period (str): The period string (e.g., "FA25").

    Returns:
        bool: True if the grace period has passed, False otherwise.
    """
    today = date.today()
    period_prefix = period[:2]
    year_short = int(period[2:])
    year = 2000 + year_short

    release_month, release_day = PERIOD_RELEASE_DATES[period_prefix]
    release_date = date(year, release_month, release_day)

    grace_months = PERIOD_GRACE_MONTHS[period_prefix]
    grace_period_end = release_date + relativedelta(months=grace_months)

    return today > grace_period_end