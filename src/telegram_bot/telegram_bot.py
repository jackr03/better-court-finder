import asyncio
import logging
from collections import defaultdict

from aiogram import Bot, Dispatcher
from src.services.court_database import CourtDatabase

from src.court_formatter import format_court_availability
from src.models import Court
from src.telegram_bot.bot_config import BotConfig
from src.telegram_bot.handlers import router

logger = logging.getLogger(__name__)


class TelegramBot:
	def __init__(self, bot_token: str):
		self.bot = Bot(bot_token)
		self.dp = Dispatcher()
		self.dp.include_router(router)
		self.config = BotConfig()
		self.court_database = CourtDatabase()

		logger.info('Building initial court availability cache')
		self.cache = set(self.court_database.get_all_available())

	async def run(self):
		await self.bot.delete_webhook(drop_pending_updates=True)
		logger.info("Bot initialised")

		self._monitor_task = asyncio.create_task(self._availability_monitor_task())

		try:
			await self.dp.start_polling(self.bot)
		except asyncio.CancelledError:
			await self._shutdown()
			raise

	async def _shutdown(self):
		if hasattr(self, '_monitor_task'):
			self._monitor_task.cancel()
			try:
				await self._monitor_task
			except asyncio.CancelledError:
				pass

	async def _availability_monitor_task(self):
		while True:
			await asyncio.sleep(self.config.get('polling_interval'))
			logger.info('Running check for any changes in court availability')

			new_set = set(self.court_database.get_all_available())

			now_available = new_set - self.cache
			now_unavailable = self.cache - new_set

			self.cache = new_set

			if not now_available and not now_unavailable:
				logger.info('No changes in court availability, no notification will be sent')
				continue
			elif now_available:
				logger.debug(f'Change in courts now available: {now_available}')
			elif now_unavailable:
				logger.debug(f'Change in courts now unavailable: {now_unavailable}')

			logger.info('Notifying users of court availability changes')
			await self._notify_users(list(now_available), list(now_unavailable))

			logger.info(f'Done, next check for court availability in {self.config.get("polling_interval")} seconds')

	async def _notify_users(self, now_available: list[Court], now_unavailable: list[Court]):
		notify_list = self.config.get_notify_list()
		if not notify_list:
			logger.info('No users to notify')
			return

		for user_id in notify_list:
			logger.debug('Notifying user %s', user_id)
			if now_available:
				await self.bot.send_message(
					user_id,
					format_court_availability(now_available, header=f'✅ Now available:', include_spaces=False)
				)

			if now_unavailable:
				await self.bot.send_message(
					user_id,
					format_court_availability(now_unavailable, header=f'❌ Now unavailable:', include_spaces=False)
				)

	def _format_court_availability(self, header: str, courts: list[Court]) -> str:
		courts_by_date = defaultdict(list)
		for court in courts:
			courts_by_date[court.date].append(court)

		sections = [header]

		for day, courts in sorted(courts_by_date.items()):
			if not courts:
				continue

			lines = [f'📅 {day.strftime("%A (%d/%m)")}:']
			for court in courts:
				lines.append(
					f'🏸 {court.starts_at.strftime("%H:%M")} - {court.ends_at.strftime("%H:%M")} ({court.duration})'
				)
			sections.append('\n'.join(lines))

		return '\n\n'.join(sections)
