import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError

from src.court.subscriber import CourtSubscriber
from src.models.court_event import CourtEvent
from src.models.venue import Venue
from src.notifications.notifier import Notifier
from src.notifications.store import NotificationStore
from src.telegram.formatter import format_court_notification_telegram

logger = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
	NAME = 'Telegram'

	def __init__(self, subscriber: CourtSubscriber, notification_store: NotificationStore, bot: Bot):
		super().__init__(subscriber)
		self._bot = bot
		self._notification_store = notification_store

	async def _on_event(self, venue: Venue, event: CourtEvent) -> None:
		user_ids = await self._notification_store.find_users_for_venue(venue)
		message = format_court_notification_telegram(event.is_available, venue, event.courts)

		sent = 0
		for user_id in user_ids:
			try:
				await self._bot.send_message(chat_id=user_id, text=message)
				sent += 1
			except TelegramForbiddenError:
				# User blocked the bot or deleted their account, remove from subscriber list
				logger.warning('User %s blocked the bot / deleted their account, pruning from database', user_id)
				await self._notification_store.unsubscribe_all(user_id)
			except TelegramRetryAfter as e:
				# Rate limited
				logger.warning('Rate limited, retrying user %s after %ss', user_id, e.retry_after)
				await asyncio.sleep(e.retry_after)
				try:
					await self._bot.send_message(chat_id=user_id,text=message)
				except TelegramAPIError:
					logger.exception('Retry failed for user %s', user_id)
			except TelegramAPIError:
				logger.exception('Failed to notify user: %s', user_id)

		logger.info('Notified %d/%d user(s) for %s', sent, len(user_ids), venue)
