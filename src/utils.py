from datetime import datetime, date, time


_TIME_FORMAT = '%H:%M'
_DATE_FORMAT = '%a %d %b'
_DATE_AND_TIME_FORMAT = '%a %-d %b, %H:%M'


def format_time(t: time) -> str:
    return t.strftime(_TIME_FORMAT)


def format_date(d: date) -> str:
    return d.strftime(_DATE_FORMAT)


def format_date_and_time(d: datetime) -> str:
    return d.strftime(_DATE_AND_TIME_FORMAT)
