import json
import logging
from typing import Callable, Awaitable

from redis.asyncio import Redis

from src.config import CONFIG
from src.models.court_event import CourtEvent
from src.models.venue import Venue

logger = logging.getLogger(__name__)


class CourtSubscriber:
	PATTERN = f'{CONFIG.redis.namespace}:venues:*'

	def __init__(self, client: Redis) -> None:
		self._client = client
		self._pubsub = None

	async def run(self, handler: Callable[[Venue, CourtEvent], Awaitable[None]]) -> None:
		self._pubsub = self._client.pubsub(ignore_subscribe_messages=True)
		await self._pubsub.psubscribe(self.PATTERN)
		logger.info(f'Subscriber live, listening to {self.PATTERN}')

		async for message in self._pubsub.listen():
			try:
				venue = self._venue_from_channel(message['channel'])
				event = CourtEvent.from_dict(json.loads(message['data']))
				await handler(venue, event)
			except Exception:
				logger.exception(f'Failed to handle event: {message}')

	async def stop(self) -> None:
		if self._pubsub is not None:
			await self._pubsub.aclose()
			logger.info(f'Subscriber stopped')

	@staticmethod
	def _venue_from_channel(channel: str) -> Venue:
		venue_name = channel.split(':')[-1]
		return Venue(venue_name)
