import asyncio
import logging
import random
from datetime import date, datetime, timedelta

import aiohttp

from src.config import CONFIG
from src.models.activity import Activity
from src.models.court import Court
from src.models.venue import Venue

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class CourtPoller:
    API_URL = 'https://better-admin.org.uk/api/activities/venue/{venue}/activity/{activity}/v2/times'
    HEADERS = {
        'accept': 'application/json',
        'origin': 'https://bookings.better.org.uk',
        'referer': 'https://bookings.better.org.uk/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15'
    }

    def __init__(self):
        self._stop_event = asyncio.Event()

    # TODO: Store to Redis cache
    # TODO: Publish to Redis
    async def run(self) -> None:
        logger.info(f'Starting CourtPoller...)')
        logger.debug(CONFIG.polling)
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            while not self._stop_event.is_set():
                courts = await self._fetch_all(session)

                available_courts = 0
                for court in courts:
                    if court.spaces > 0:
                        available_courts += 1
                logger.info(f'Fetched {len(courts)} court objects, {available_courts} available courts')

                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=CONFIG.polling.interval)
                except asyncio.TimeoutError:
                    pass

    def stop(self) -> None:
        self._stop_event.set()

    async def _fetch_all(self, session: aiohttp.ClientSession) -> list[Court]:
        logger.info('Fetching all courts')

        # Check the next 6 days for all courts
        dates = [(datetime.today() + timedelta(days=i)).date() for i in range(6)]
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

    async def _fetch(self, session: aiohttp.ClientSession, venue: Venue, activity: Activity, booking_date: date) -> list[Court]:
        logger.debug(f'Fetching (venue={venue}, activity={activity}, booking_date={booking_date})')

        for attempt in range(0, CONFIG.polling.max_retries + 1):
            try:
                async with session.get(
                    self.API_URL.format(venue=venue, activity=activity),
                    params={'date': booking_date.isoformat()}
                ) as response:
                    # Retry with exponential backoff + jitter
                    if response.status == 429 or response.status >= 500:
                        if attempt < CONFIG.polling.max_retries:
                            delay = self._get_backoff_delay(attempt)
                            logger.warning(f'Retrying in {delay:.1f}s (status={response.status}, attempt={attempt}, venue={venue}, activity={activity}, booking_date={booking_date})')
                            await asyncio.sleep(delay)
                            continue
                        logger.error(f'Max retries exceeded (status={response.status}, venue={venue}, activity={activity}, booking_date={booking_date})')
                        return []

                    response.raise_for_status()
                    data = (await response.json())['data']
                    return [Court.from_api(court) for court in data]
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt < CONFIG.polling.max_retries:
                    delay = self._get_backoff_delay(attempt)
                    logger.warning(f'Retrying in {delay:.1f}s (attempt={attempt}, venue={venue}, activity={activity}, booking_date={booking_date})')
                    await asyncio.sleep(delay)
                    continue
                logger.exception(f'Max retries exceeded (venue={venue}, activity={activity}, booking_date={booking_date})')
                return []

        return []

    @staticmethod
    def _get_backoff_delay(attempt: int) -> float:
        """Get delay with exponential backoff and equal jitter."""
        exponential_delay = CONFIG.polling.base_delay * (2 ** attempt)
        return exponential_delay / 2 + random.uniform(0, exponential_delay / 2)

if __name__ == '__main__':
    poller = CourtPoller()
    asyncio.run(poller.run())
