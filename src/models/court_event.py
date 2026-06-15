from dataclasses import dataclass

from src.models.court import Court
from src.models.court_state import CourtState


@dataclass(frozen=True)
class CourtEvent:
	state: CourtState
	courts: list[Court]

	@property
	def is_available(self) -> bool:
		return self.state == CourtState.AVAILABLE

	@classmethod
	def from_dict(cls, data: dict) -> 'CourtEvent':
		return cls(
			state=CourtState(data['state']),
			courts=[Court.from_dict(court) for court in data['courts']]
		)