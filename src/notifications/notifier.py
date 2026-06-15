from abc import ABC, abstractmethod

from src.court.cache import CourtCache
from src.court.subscriber import CourtSubscriber
from src.models.court_event import CourtEvent
from src.models.venue import Venue


# TODO: Needs to instantiated with a NotificationStore which we can grab user_ids from
class Notifier(ABC):
	def __init__(self, cache: CourtCache, subscriber: CourtSubscriber):
		self._cache = cache
		self._subscriber = subscriber

	async def run(self) -> None:
		await self._subscriber.run(self._on_event)

	async def stop(self) -> None:
		await self._subscriber.stop()

	async def _on_event(self, venue: Venue, event: CourtEvent) -> None:
		# TODO: Hardcoded right now
		user_ids = []
		message = self._format(venue, event)
		await self._send(message, user_ids)

	@abstractmethod
	async def _send(self, message: str, user_ids: list[str]) -> None:
		pass

	@abstractmethod
	def _format(self, venue: Venue, event: CourtEvent) -> str:
		pass
