import argparse
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


async def get_redis() -> Redis:
	redis = Redis(host=CONFIG.redis.host,
				  port=CONFIG.redis.port,
				  decode_responses=True)
	await redis.ping()
	logger.info('Connected to Redis (host=%s, port=%s)', CONFIG.redis.host, CONFIG.redis.port)

	return redis


async def get_notification_store() -> NotificationStore:
	notification_store = NotificationStore(user=CONFIG.postgres.user,
										   password=CONFIG.postgres.password,
										   database=CONFIG.postgres.database,
										   host=CONFIG.postgres.host,
										   port=CONFIG.postgres.port)
	await notification_store.connect()
	return notification_store


async def run_poller() -> None:
	redis = await get_redis()
	cache = CourtCache(redis)
	publisher = CourtPublisher(redis)
	poller = CourtPoller(cache, publisher)

	try:
		await poller.run()
	finally:
		await redis.aclose()


async def run_telegram() -> None:
	redis = await get_redis()
	notification_store = await get_notification_store()
	cache = CourtCache(redis)

	aiogram_bot = Bot(
		token=CONFIG.telegram.token,
		default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
	)
	telegram_bot = TelegramBot(aiogram_bot, notification_store, cache)
	telegram_subscriber = CourtSubscriber(redis)
	telegram_notifier = TelegramNotifier(telegram_subscriber, notification_store, aiogram_bot)

	try:
		async with asyncio.TaskGroup() as taskgroup:
			taskgroup.create_task(telegram_bot.run())
			taskgroup.create_task(telegram_notifier.run())
	finally:
		await telegram_notifier.stop()
		await aiogram_bot.close()
		await notification_store.close()
		await redis.aclose()


async def run_discord() -> None:
	redis = await get_redis()

	# Log any venues that are disabled for Discord
	disabled = [v.name for v in Venue if v not in CONFIG.discord.webhooks.keys()]
	if disabled:
		logger.warning('Discord notifications disabled for %s', ', '.join(disabled))

	discord_subscriber = CourtSubscriber(redis)
	discord_notifier = DiscordNotifier(discord_subscriber, CONFIG.discord.webhooks)

	try:
		await discord_notifier.run()
	finally:
		await discord_notifier.stop()
		await redis.aclose()


SERVICES = {
	'poller': run_poller,
	'telegram': run_telegram,
	'discord': run_discord,
}


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument('service', choices=SERVICES)
	args = parser.parse_args()

	try:
		asyncio.run(SERVICES[args.service]())
	except KeyboardInterrupt:
		logger.info('Shutting down...')


if __name__ == '__main__':
	main()
