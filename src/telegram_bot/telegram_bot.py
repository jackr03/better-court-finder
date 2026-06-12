import logging

from aiogram import Bot, Dispatcher

from src.court.cache import CourtCache
from src.telegram_bot.handlers import router

logger = logging.getLogger(__name__)


class TelegramBot:
	def __init__(self, bot_token: str, cache: CourtCache):
		self.bot = Bot(bot_token)
		self.dp = Dispatcher()
		self.dp['cache'] = cache
		self.dp.include_router(router)

	async def run(self) -> None:
		await self.bot.delete_webhook(drop_pending_updates=True)
		logger.info("Starting Telegram bot")
		await self.dp.start_polling(self.bot, handle_signals=False)

	async def stop(self) -> None:
		await self.bot.session.close()
