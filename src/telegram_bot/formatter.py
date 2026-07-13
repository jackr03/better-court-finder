from collections import defaultdict
from datetime import datetime

from src.models.court import Court
from src.models.venue import Venue
from src.telegram_bot.constants import Messages
from src.utils import format_date, format_time


def format_court_availability(courts: list[Court], for_venue: bool) -> str:
    """
    Format court availability, grouped by date.

    If for_venue, all courts must share one venue.
    Venue name is rendered once as a header rather than per section.
    """
    grouped = _sort_and_group_courts(courts)

    date_blocks = []
    for d, venues in grouped.items():
        venue_blocks = []
        for venue, venue_courts in venues.items():
            venue_block = [] if for_venue else [f'📍 _{venue.display_name}_']
            venue_block.extend(_format_slots(venue_courts))
            venue_blocks.append('\n'.join(venue_block))
        date_block = f'📅 *{format_date(d)}*\n' + '\n\n'.join(venue_blocks)
        date_blocks.append(date_block)

    body = '\n\n'.join(date_blocks)

    if for_venue:
        header = f'📍 *{courts[0].venue.display_name}*'
        return f'{header}\n\n{body}'
    return body


def format_court_notification(available: bool, venue: Venue, courts: list[Court])-> str:
    status = Messages.COURTS_AVAILABLE if available else Messages.COURTS_UNAVAILABLE
    header = f'*{status} at {venue.display_name}*'

    grouped = _sort_and_group_courts(courts)
    date_blocks = []
    for d, venues in grouped.items():
        venue_courts = venues[venue]
        slots = _format_slots(venue_courts, include_spaces=False)
        date_blocks.append(f'📅 _{format_date(d)}_\n' + '\n'.join(slots))

    return header + '\n' + '\n\n'.join(date_blocks)


def _format_slots(courts: list[Court], include_spaces: bool = True) -> list[str]:
    return [
        f'⏱️ {format_time(c.starts_at)} - {format_time(c.ends_at)}'
        + (f': {c.spaces} space{'s' if c.spaces != 1 else ''}' if include_spaces else '')
        for c in courts
    ]


def _sort_and_group_courts(courts: list[Court]) -> dict[datetime, dict[Venue, list[Court]]]:
    sorted_courts = sorted(
        courts,
        key=lambda c: (c.date, c.venue, c.starts_at, c.duration)
    )
    grouped = defaultdict(lambda: defaultdict(list))
    for court in sorted_courts:
        grouped[court.date][court.venue].append(court)
    return grouped
