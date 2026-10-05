"""One literal recorded name. Keep in sync with evaluation_instructor_name in SQL."""


def recorded_instructor_name(record):
    value = record.get('instructor_name')
    if not isinstance(value, str):
        return None
    return value.strip() or None
