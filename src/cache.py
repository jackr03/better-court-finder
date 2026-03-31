import json
import logging
from datetime import date

from redis.asyncio import Redis

from src.config import CONFIG
from src.models.court import Court
from src.models.venue import Venue

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self):
        self.client = Redis(host=CONFIG.redis.host, port=CONFIG.redis.port, decode_responses=True)

    async def connect(self) -> None:
        await self.client.ping()
        logger.debug(f'Connected to Redis (key={CONFIG.redis.key}, port={CONFIG.redis.port})')

    async def get(self, venue: Venue, booking_date: date) -> list[Court]:
        key = self._format_key(venue, booking_date)
        value = await self.client.get(key)
        if value is None:
            logger.debug(f'Cache miss (key={key})')
            return []
        logger.debug(f'Cache get (key={key}, value={value=})')
        return [Court.from_dict(court) for court in json.loads(value)]

    async def set(self, venue: Venue, booking_date: date, courts: list[Court]) -> None:
        key = self._format_key(venue, booking_date)
        value = json.dumps([court.to_dict() for court in courts])
        await self.client.set(key, value, ex=CONFIG.redis.ttl)
        logger.debug(f'Cache set (key={key}, courts={len(courts)})')

    @staticmethod
    def _format_key(venue: Venue, booking_date: date) -> str:
        return f'{venue.value}-{booking_date.isoformat()}'
