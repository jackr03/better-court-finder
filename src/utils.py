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
