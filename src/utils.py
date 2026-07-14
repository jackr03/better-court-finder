import random
from datetime import datetime, date, time


TIME_FORMAT = '%H:%M'
DATE_FORMAT = '%a %d %b'
DATE_AND_TIME_FORMAT = '%a %-d %b, %H:%M'


def format_time(t: time) -> str:
    return t.strftime(TIME_FORMAT)


def format_date(d: date) -> str:
    return d.strftime(DATE_FORMAT)


def format_date_and_time(d: datetime) -> str:
    return d.strftime(DATE_AND_TIME_FORMAT)


def get_backoff_delay(base_delay: float, attempt: int) -> float:
    """Get delay with exponential backoff and equal jitter."""
    exponential_delay = base_delay * (2 ** attempt)
    return exponential_delay / 2 + random.uniform(0, exponential_delay / 2)