import json
import logging
from datetime import date, datetime

from redis.asyncio import Redis

from src.config import CONFIG
from src.models.court import Court
from src.models.time_range import TimeRange
from src.models.venue import Venue

logger = logging.getLogger(__name__)


class CourtCache:
    COURTS_PREFIX = f'{CONFIG.redis.namespace}:courts'
    LAST_UPDATED_KEY = f'{CONFIG.redis.namespace}:last-updated'

    def __init__(self, client: Redis):
        self._client = client

    async def get(self, venue: Venue, booking_date: date) -> list[Court]:
        key = self._format_key(venue, booking_date)
        value = await self._client.get(key)
        if value is None:
            logger.debug(f'Cache miss (key={key})')
            return []
        logger.debug(f'Cache get (key={key}, value={value=})')
        return [Court.from_dict(court) for court in json.loads(value)]

    async def set(self, venue: Venue, booking_date: date, courts: list[Court]) -> None:
        key = self._format_key(venue, booking_date)
        value = json.dumps([court.to_dict() for court in courts])
        await self._client.set(key, value, ex=CONFIG.redis.ttl)
        logger.debug(f'Cache set (key={key}, courts={len(courts)})')

    async def get_last_updated(self) -> datetime:
        last_updated = await self._client.get(self.LAST_UPDATED_KEY)
        return datetime.fromisoformat(last_updated)

    async def set_last_updated(self) -> None:
        await self._client.set(self.LAST_UPDATED_KEY, datetime.isoformat(datetime.now()))

    async def get_all_available_courts(self) -> list[Court]:
        courts = await self._get_courts(f'{self.COURTS_PREFIX}:*')
        return [court for court in courts if court.spaces > 0]

    async def get_available_by_date(self, d: date) -> list[Court]:
        courts = await self._get_courts(f'{self.COURTS_PREFIX}:*:{d}')
        return [court for court in courts if court.spaces > 0]

    async def get_available_by_time_range(self, time_range: TimeRange) -> list[Court]:
        courts = await self._get_courts(f'{self.COURTS_PREFIX}:*')
        return [court for court in courts if court.spaces > 0 and time_range.contains(court.starts_at)]

    async def get_available_by_venue(self, venue: Venue) -> list[Court]:
        courts = await self._get_courts(f'{self.COURTS_PREFIX}:{venue.value}:*')
        return [court for court in courts if court.spaces > 0]

    async def _get_courts(self, prefix: str) -> list[Court]:
        keys = [key async for key in self._client.scan_iter(match=prefix)]
        values = await self._client.mget(keys)
        return [Court.from_dict(court) for value in values for court in json.loads(value)]

    def _format_key(self, venue: Venue, booking_date: date) -> str:
        return f'{self.COURTS_PREFIX}:{venue.value}:{booking_date.isoformat()}'
