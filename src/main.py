import asyncio
import logging
import os

from aiogram import Bot
from dotenv import load_dotenv
from redis.asyncio import Redis

from src.config import CONFIG
from src.court.cache import CourtCache
from src.court.poller import CourtPoller
from src.court.publisher import CourtPublisher
from src.court.subscriber import CourtSubscriber
from src.models.platform import Platform
from src.telegram_bot.bot import TelegramBot
from src.telegram_bot.notifier import TelegramNotifier

load_dotenv()
logging.basicConfig(
	level=CONFIG.logging_level,
	format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
	client = Redis(host=CONFIG.redis.host, port=CONFIG.redis.port, decode_responses=True)
	await client.ping()
	logger.info(f'Connected to Redis (host={CONFIG.redis.host}, port={CONFIG.redis.port})')

	cache = CourtCache(client)
	publisher = CourtPublisher(client)
	poller = CourtPoller(cache, publisher)

	bot = Bot(os.getenv('BOT_TOKEN'))
	telegram_bot = TelegramBot(bot, cache)
	telegram_subscriber = CourtSubscriber(Platform.TELEGRAM, client)
	telegram_notifier = TelegramNotifier(cache, telegram_subscriber, bot)

	poller_task = asyncio.create_task(poller.run())
	telegram_bot_task = asyncio.create_task(telegram_bot.run())
	telegram_notifier_task = asyncio.create_task(telegram_notifier.run())

	tasks = [poller_task, telegram_bot_task, telegram_notifier_task]

	try:
		await asyncio.gather(*tasks)
	except (asyncio.CancelledError, KeyboardInterrupt):
		pass
	finally:
		logger.info('Shutting down')

		for task in tasks:
			task.cancel()
		await asyncio.gather(*tasks, return_exceptions=True)

		await telegram_notifier.stop()
		await bot.session.close()
		await client.aclose()


if __name__ == '__main__':
	asyncio.run(main())