import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.court.cache import CourtCache
from src.notifications.store import NotificationStore
from src.telegram_bot.handlers import router

logger = logging.getLogger(__name__)


class TelegramBot:
	def __init__(self, bot: Bot, notification_store: NotificationStore, cache: CourtCache):
		self._bot = bot
		self._dp = Dispatcher(storage=MemoryStorage())
		self._dp['cache'] = cache
		self._dp['notification_store'] = notification_store
		self._dp.include_router(router)

	async def run(self) -> None:
		await self._bot.delete_webhook(drop_pending_updates=True)
		logger.info("Starting Telegram bot")
		await self._dp.start_polling(self._bot, handle_signals=False)
