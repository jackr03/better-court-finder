from redis.asyncio import Redis

from src.config import CONFIG
from src.models.platform import Platform
from src.models.venue import Venue


# TODO: Implement this with a two way mapping of userId -> [venues] and venue -> [userIds]
class NotificationStore:
	def __init__(self, client: Redis, platform: Platform, ):
		self._client = client
		self._platform = platform
		self._prefix = f'{CONFIG.redis.namespace}:{platform}'

	async def add_user_to_venue(self, venue: Venue, user: str) -> None:
		await self._client.sadd(f'{self._prefix}:venue:{venue}', user)

	async def remove_user_from_venue(self, venue: Venue, user: str) -> None:
		await self._client.srem(f'{self._prefix}:venue:{venue}', user)

	async def get_users_for_venue(self, venue: Venue) -> list[str]:
		pass