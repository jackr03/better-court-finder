import logging

from aiogram import Bot, Dispatcher

from src.court.cache import CourtCache
from src.telegram_bot.handlers import router

logger = logging.getLogger(__name__)


class TelegramBot:
	def __init__(self, bot: Bot, cache: CourtCache):
		self._bot = bot
		self._dp = Dispatcher()
		self._dp['cache'] = cache
		self._dp.include_router(router)

	async def run(self) -> None:
		await self._bot.delete_webhook(drop_pending_updates=True)
		logger.info("Starting Telegram bot")
		await self._dp.start_polling(self._bot, handle_signals=False)
