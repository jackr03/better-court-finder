import asyncio
import logging
from datetime import date, datetime, timedelta

import aiohttp

from src.config import CONFIG
from src.court.cache import CourtCache
from src.court.publisher import CourtPublisher
from src.models.activity import Activity
from src.models.court import Court
from src.models.venue import Venue
from src.utils import get_backoff_delay

logger = logging.getLogger(__name__)


class CourtPoller:
    API_URL = 'https://better-admin.org.uk/api/activities/venue/{venue}/activity/{activity}/v2/times'
    HEADERS = {
        'origin': 'https://bookings.better.org.uk',
    }
    # We could look ahead 6 days, but this would require an auth token
    MAX_LOOKAHEAD_DAYS = 5

    def __init__(self, cache: CourtCache, publisher: CourtPublisher) -> None:
        self._cache = cache
        self._publisher = publisher

        self._last_available: dict[str, Court] = {}
        self._cold_start = True

    async def run(self) -> None:
        logger.info('Starting court poller')
        logger.debug(CONFIG.polling)
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            while True:
                courts = await self._fetch_all(session)

                # 1. Group by (venue, date) to store in Redis
                # 2. Store in-memory to compute court changes later
                grouped: dict[tuple[Venue, date], list[Court]] = {}
                available: dict[str, Court] = {}
                for court in courts:
                    key = (court.venue, court.date)
                    grouped.setdefault(key, []).append(court)
                    if court.spaces > 0:
                        available[court.composite_key] = court

                newly_available, newly_unavailable = self._compute_diff(available)
                self._last_available = available

                if self._cold_start:
                    self._cold_start = False
                else:
                    if newly_available or newly_unavailable:
                        logger.info(
                            'Court changes: +%d available, -%d unavailable',
                            len(newly_available), len(newly_unavailable))
                    logger.debug('Courts now available: %s', newly_available)
                    logger.debug('Courts now unavailable: %s', newly_unavailable)

                    await self._publisher.publish_changes(newly_available, newly_unavailable)

                for (venue, booking_date), courts in grouped.items():
                    await self._cache.set(venue, booking_date, courts)
                await self._cache.set_last_updated()

                logger.info('Cached %d venue-date groups', len(grouped))
                logger.debug('Poll cycle complete, next in %ss', CONFIG.polling.interval)
                try:
                    await asyncio.sleep(CONFIG.polling.interval)
                except asyncio.TimeoutError:
                    pass

    def _compute_diff(self, available: dict[str, Court]) -> tuple[frozenset[Court], frozenset[Court]]:
        newly_available_keys = available.keys() - self._last_available.keys()
        newly_unavailable_keys = self._last_available.keys() - available.keys()

        newly_available = frozenset({available[key] for key in newly_available_keys})
        newly_unavailable = frozenset({self._last_available[key] for key in newly_unavailable_keys})

        return newly_available, newly_unavailable

    async def _fetch_all(self, session: aiohttp.ClientSession) -> list[Court]:
        # Check the next 6 days for all courts
        dates = [(datetime.today() + timedelta(days=i)).date() for i in range(self.MAX_LOOKAHEAD_DAYS + 1)]
        args = [
            (venue, activity, booking_date)
            for venue in Venue for activity in venue.activities for booking_date in dates
        ]

        sem = asyncio.Semaphore(CONFIG.polling.max_concurrent)

        async def fetch_one(venue, activity: Activity, booking_date: date):
            async with sem:
                return await self._fetch(session, venue, activity, booking_date)

        results = await asyncio.gather(*[fetch_one(venue, activity, booking_date) for venue, activity, booking_date in args])
        return [court for batch in results for court in batch]

    async def _fetch(
            self,
            session: aiohttp.ClientSession,
            venue: Venue,
            activity: Activity,
            booking_date: date,
    ) -> list[Court]:
        logger.debug('Fetching (venue=%s, activity=%s, booking_date=%s)', venue, activity, booking_date)

        for attempt in range(0, CONFIG.polling.max_retries + 1):
            try:
                async with session.get(
                        self.API_URL.format(venue=venue, activity=activity),
                        params={'date': booking_date.isoformat()}
                ) as resp:
                    # Retry with exponential backoff + jitter if rate limited / server error
                    if resp.status == 429 or resp.status >= 500:
                        if attempt < CONFIG.polling.max_retries:
                            delay = get_backoff_delay(CONFIG.polling.base_delay, attempt)
                            logger.warning(
                                'Retrying in %.1fs (status=%s, attempt=%s, venue=%s, activity=%s, booking_date=%s)',
                                delay, resp.status, attempt, venue, activity, booking_date
                            )
                            await asyncio.sleep(delay)
                            continue
                        logger.error(
                            'Max retries exceeded (status=%s, venue=%s, activity=%s, booking_date=%s)',
                            resp.status, venue, activity, booking_date
                        )
                        return []

                    # Otherwise log error and stop immediately
                    if resp.status >= 400:
                        err_message = (await resp.json()).get('message', resp.reason)
                        logger.error(
                            'Request failed (status=%s, venue=%s, activity=%s, booking_date=%s): %s',
                            resp.status, venue, activity, booking_date, err_message
                        )
                        return []

                    data = (await resp.json())['data']
                    return [Court.from_api(court) for court in data]
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt < CONFIG.polling.max_retries:
                    delay = get_backoff_delay(CONFIG.polling.base_delay, attempt)
                    logger.warning(
                        'Retrying in %.1fs (attempt=%s, venue=%s, activity=%s, booking_date=%s)',
                        delay, attempt, venue, activity, booking_date
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.exception(
                    'Max retries exceeded (venue=%s, activity=%s, booking_date=%s)',
                    venue, activity, booking_date
                )
                return []

        return []
