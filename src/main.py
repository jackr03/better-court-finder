import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from redis.asyncio import Redis

from src.config import CONFIG
from src.court.cache import CourtCache
from src.court.poller import CourtPoller
from src.court.publisher import CourtPublisher
from src.court.subscriber import CourtSubscriber
from src.discord.notifier import DiscordNotifier
from src.models.venue import Venue
from src.notifications.store import NotificationStore
from src.telegram.bot import TelegramBot
from src.telegram.notifier import TelegramNotifier

logging.basicConfig(
	level=CONFIG.logging_level,
	format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
	redis = Redis(host=CONFIG.redis.host,
				  port=CONFIG.redis.port,
				  decode_responses=True)
	await redis.ping()
	logger.info(f'Connected to Redis (host={CONFIG.redis.host}, port={CONFIG.redis.port})')

	notification_store = NotificationStore(user=CONFIG.postgres.user,
										   password=CONFIG.postgres.password,
										   database=CONFIG.postgres.database,
										   host=CONFIG.postgres.host,
										   port=CONFIG.postgres.port)
	await notification_store.connect()

	cache = CourtCache(redis)
	publisher = CourtPublisher(redis)
	poller = CourtPoller(cache, publisher)

	# Discord
	# Log any venues that are disabled for Discord
	disabled = [v.name for v in Venue if v not in CONFIG.discord.webhooks.keys()]
	if disabled:
		logger.warning(f'Discord notifications disabled for %s', ', '.join(disabled))

	discord_subscriber = CourtSubscriber(redis)
	discord_notifier = DiscordNotifier(discord_subscriber, CONFIG.discord.webhooks)

	# Telegram
	aiogram_bot = Bot(token=CONFIG.telegram.token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
	telegram_bot = TelegramBot(aiogram_bot, notification_store, cache)
	telegram_subscriber = CourtSubscriber(redis)
	telegram_notifier = TelegramNotifier(telegram_subscriber, notification_store, aiogram_bot)

	# Tasks
	poller_task = asyncio.create_task(poller.run())
	discord_notifier_task = asyncio.create_task(discord_notifier.run())
	telegram_bot_task = asyncio.create_task(telegram_bot.run())
	telegram_notifier_task = asyncio.create_task(telegram_notifier.run())

	notifiers = [discord_notifier, telegram_notifier]
	tasks = [poller_task, discord_notifier_task, telegram_bot_task, telegram_notifier_task]

	try:
		await asyncio.gather(*tasks)
	except asyncio.CancelledError:
		pass
	finally:
		logger.info('Shutting down')

		for task in tasks:
			task.cancel()
		await asyncio.gather(*tasks, return_exceptions=True)

		for notifier in notifiers:
			await notifier.stop()

		await aiogram_bot.session.close()
		await notification_store.close()
		await redis.aclose()


if __name__ == '__main__':
	asyncio.run(main())