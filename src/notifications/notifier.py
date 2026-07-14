import logging
from abc import ABC, abstractmethod

from src.court.subscriber import CourtSubscriber
from src.models.court_event import CourtEvent
from src.models.venue import Venue

logger = logging.getLogger(__name__)


class Notifier(ABC):
	NAME: str

	def __init__(self, subscriber: CourtSubscriber):
		self._subscriber = subscriber

	async def run(self) -> None:
		logger.info('Starting %s notifier', self.NAME)
		await self._subscriber.run(self._on_event)

	async def stop(self) -> None:
		await self._subscriber.stop()

	@abstractmethod
	async def _on_event(self, venue: Venue, event: CourtEvent) -> None:
		pass
