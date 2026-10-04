"""Exact recorded names. Keep in sync with evaluation_instructor_names in SQL."""
import re


def recorded_instructor_names(record):
    value = record.get('instructor_names', record.get('instructor_name'))
    if isinstance(value, str):
        value = re.split(r'[;|\n\r]+|\s+(?:&|and)\s+', value)
    if not isinstance(value, list):
        return []
    return sorted({name.strip() for name in value if isinstance(name, str) and name.strip()})
