import asyncio
import logging

import aiohttp

from src.config import CONFIG
from src.court.subscriber import CourtSubscriber
from src.models.court_event import CourtEvent
from src.models.venue import Venue
from src.notifications.notifier import Notifier
from src.telegram.formatter import format_court_notification_discord
from src.utils import get_backoff_delay

logger = logging.getLogger(__name__)


class DiscordNotifier(Notifier):
	NAME = 'Discord'

	def __init__(self, subscriber: CourtSubscriber, webhooks: dict[Venue, str]):
		super().__init__(subscriber)
		self._webhooks = webhooks
		self._session: aiohttp.ClientSession | None = None

	async def run(self) -> None:
		self._session = aiohttp.ClientSession()
		await super().run()

	async def stop(self) -> None:
		await super().stop()
		if self._session:
			await self._session.close()

	async def _on_event(self, venue: Venue, event: CourtEvent) -> None:
		webhook_url = self._webhooks.get(venue)
		content = format_court_notification_discord(event.is_available, venue, event.courts)

		if not webhook_url:
			return # Fail silently here as we already catch missing venues in main.py

		await self._post(webhook_url, content, venue)

	async def _post(self, webhook_url: str, content: str, venue: Venue) -> None:
		for attempt in range(CONFIG.discord.max_retries):
			try:
				async with self._session.post(webhook_url, json={'content': content}) as resp:
					if resp.status == 204:
						logger.info('Posted to #%s', venue)
						return
					elif resp.status == 429:
						retry_after = (await resp.json()).get('retry_after', 1.0)
						logger.warning('Rate limited by Discord, retrying after %.2fs', retry_after)
						await asyncio.sleep(retry_after)
					elif resp.status in (401, 404):
						logger.error('Webhook rejected: %s, giving up', resp.status)
						return
					elif resp.status >= 500:
						logger.error('Discord server error: %s, attempt %d', resp.status, attempt)
						backoff_delay = get_backoff_delay(CONFIG.discord.backoff_delay, attempt)
						await asyncio.sleep(backoff_delay)
						continue
					else:
						logger.error('Unexpected Discord response: %s', resp.status)
						return
			except aiohttp.ClientError:
				logger.warning('Network error while posting to Discord, attempt %d', attempt + 1)
				backoff_delay = get_backoff_delay(CONFIG.discord.backoff_delay, attempt)
				await asyncio.sleep(backoff_delay)

		logger.error('Failed to post to Discord after %d attempts', CONFIG.discord.max_retries)
