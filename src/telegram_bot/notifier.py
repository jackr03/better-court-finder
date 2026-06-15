import logging

from aiogram import Bot

from src.court.cache import CourtCache
from src.court.subscriber import CourtSubscriber
from src.models.court_event import CourtEvent
from src.models.venue import Venue
from src.notifications.notifier import Notifier
from src.telegram_bot.formatter import format_court_notification

logger = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
	def __init__(self, cache: CourtCache, subscriber: CourtSubscriber, bot: Bot):
		super().__init__(cache, subscriber)
		self._bot = bot

	# TODO: Handle TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
	async def _send(self, message: str, user_ids: list[str]) -> None:
		for user_id in user_ids:
			try:
				await self._bot.send_message(
					chat_id=user_id,
					text=message,
					parse_mode='Markdown')
				logger.info(f'Notified user {user_id}')
			except:
				pass

	def _format(self, venue: Venue, event: CourtEvent) -> str:
		return format_court_notification(event.is_available, venue, event.courts)
