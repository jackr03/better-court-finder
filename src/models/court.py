from dataclasses import dataclass
from datetime import time, date

from src.models.activity import Activity
from src.models.venue import Venue


@dataclass(frozen=True)
class Court:
	starts_at: time
	ends_at: time
	duration: str
	composite_key: str
	activity: Activity
	date: date
	venue: Venue
	spaces: int

	@classmethod
	def from_api(cls, data: dict) -> 'Court':
		return cls(
			starts_at=time.fromisoformat(data['starts_at']['format_24_hour']),
			ends_at=time.fromisoformat(data['ends_at']['format_24_hour']),
			duration=data['duration'],
			composite_key=data['composite_key'],
			activity=Activity(data['category_slug']),
			date=date.fromisoformat(data['date']),
			venue=Venue(data['venue_slug']),
			spaces=data['spaces']
		)
