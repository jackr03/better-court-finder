import json
import logging
from collections import defaultdict

from redis.asyncio import Redis

from src.config import CONFIG
from src.models.court import Court
from src.models.court_state import CourtState
from src.models.venue import Venue

logger = logging.getLogger(__name__)


class CourtPublisher:
	CHANNEL_PREFIX = f'{CONFIG.redis.namespace}:venues'

	def __init__(self, client: Redis):
		self._client = client

	async def publish_changes(self, newly_available: frozenset[Court], newly_unavailable: frozenset[Court]) -> None:
		await self._publish_courts(newly_available, CourtState.AVAILABLE)
		await self._publish_courts(newly_unavailable, CourtState.UNAVAILABLE)

	async def _publish_courts(self, courts: frozenset[Court], state: CourtState) -> None:
		grouped: dict[Venue, list[Court]] = defaultdict(list)
		for court in courts:
			grouped[court.venue].append(court)

		for venue, venue_courts in grouped.items():
			channel = f'{self.CHANNEL_PREFIX}:{venue.value}'
			payload = json.dumps({
				'state': state, # TODO: Will this throw an error?
				'venue': venue.value,
				'courts': [court.to_dict() for court in venue_courts]
			})
			receivers = await self._client.publish(channel, payload)

			if receivers == 0:
				logger.warning(f'Published {state} to {channel} but no subscribers were listening')
			else:
				logger.debug(f'Published {state} to {channel} ({len(courts)} courts) to {receivers} receivers')
