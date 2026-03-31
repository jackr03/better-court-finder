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

	def to_dict(self) -> dict:
		return {
			'starts_at': self.starts_at.isoformat(),
			'ends_at': self.ends_at.isoformat(),
			'duration': self.duration,
			'composite_key': self.composite_key,
			'activity': self.activity.value,
			'date': self.date.isoformat(),
			'venue': self.venue.value,
			'spaces': self.spaces
		}

	@classmethod
	def from_dict(cls, data: dict) -> 'Court':
		return cls(
			starts_at=time.fromisoformat(data['starts_at']),
			ends_at=time.fromisoformat(data['ends_at']),
			duration=data['duration'],
			composite_key=data['composite_key'],
			activity=Activity(data['activity']),
			date=date.fromisoformat(data['date']),
			venue=Venue(data['venue']),
			spaces=data['spaces'],
		)

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
