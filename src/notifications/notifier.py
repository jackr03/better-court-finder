from abc import ABC, abstractmethod

from src.court.cache import CourtCache
from src.court.subscriber import CourtSubscriber
from src.models.court_event import CourtEvent
from src.models.venue import Venue
from src.notifications.store import NotificationStore


class Notifier(ABC):
	def __init__(self, notification_store: NotificationStore, cache: CourtCache, subscriber: CourtSubscriber):
		self._notification_store = notification_store
		self._cache = cache
		self._subscriber = subscriber

	async def run(self) -> None:
		await self._subscriber.run(self._on_event)

	async def stop(self) -> None:
		await self._subscriber.stop()

	async def _on_event(self, venue: Venue, event: CourtEvent) -> None:
		user_ids = await self._notification_store.find_users_for_venue(venue)
		message = self._format(venue, event)
		await self._send(message, user_ids)

	@abstractmethod
	async def _send(self, message: str, user_ids: set[str]) -> None:
		pass

	@abstractmethod
	def _format(self, venue: Venue, event: CourtEvent) -> str:
		pass
