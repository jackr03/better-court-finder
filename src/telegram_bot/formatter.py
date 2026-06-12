from collections import defaultdict
from datetime import datetime

from src.models.court import Court
from src.models.venue import Venue
from src.utils import format_date, format_time


def format_court_availability(courts: list[Court]) -> str:
    grouped = _sort_and_group_courts(courts)

    date_blocks = []
    for d, venues in grouped.items():
        venue_blocks = []
        for venue, venue_courts in venues.items():
            venue_block = [f'📍 _{venue.display_name}_']
            for court in venue_courts:
                venue_block.append(f'⏱️ {court.starts_at.strftime("%H:%M")} - {court.ends_at.strftime("%H:%M")}: {court.spaces} spaces')
            venue_blocks.append('\n'.join(venue_block))
        date_block = f'📅 *{format_date(d)}*\n' + '\n\n'.join(venue_blocks)
        date_blocks.append(date_block)
    return '\n\n'.join(date_blocks)


def _format_slots(courts: list[Court]) -> list[str]:
    return [
        f'⏱️ {format_time(c.starts_at)} - {format_time(c.ends_at)}: '
        f'{c.spaces} space{'s' if c.spaces != 1 else ''}'
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
