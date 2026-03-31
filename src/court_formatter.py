from collections import defaultdict
from datetime import date

from src.models import Court


# TODO: Redo
# TODO: Group by venue in the future
def format_court_availability(
		courts: list[Court],
		none_available_message: str = 'None available.',
		header: str = None,
		include_spaces: bool = True
) -> str:
	courts_by_date = _group_courts_by_date(courts)

	if not any(courts_by_date.values()):
		return none_available_message

	sections = [header] if header else []

	for days, courts in sorted(courts_by_date.items()):
		day = _ordinal(days.day)
		lines = [f'📅 {days.strftime("%A")} {day} {days.strftime("%B")}:']
		for court in sorted(courts, key=lambda c: (c.starts_at, c.ends_at)):
			lines.append(court.format_with_spaces() if include_spaces else court.format_without_spaces())
		sections.append('\n'.join(lines))

	return '\n\n'.join(sections)


def _group_courts_by_date(courts: list[Court]) -> dict[date, list[Court]]:
	grouped = defaultdict(list)
	for court in courts:
		grouped[court.date].append(court)
	return dict(grouped)


def _ordinal(n: int) -> str:
	if 10 <= n % 100 <= 20:
		return f'{n}th'
	return f'{n}{ {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'
