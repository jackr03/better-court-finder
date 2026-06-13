import asyncio
import logging
import os

from dotenv import load_dotenv
from redis.asyncio import Redis

from src.config import CONFIG
from src.court.cache import CourtCache
from src.court.poller import CourtPoller
from src.court.publisher import CourtPublisher
from src.telegram_bot.telegram_bot import TelegramBot

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
	telegram_bot = TelegramBot(os.getenv('BOT_TOKEN'), cache)

	poller_task = asyncio.create_task(poller.run())
	telegram_bot_task = asyncio.create_task(telegram_bot.run())

	try:
		await asyncio.gather(
			poller_task,
			telegram_bot_task
		)
	except (asyncio.CancelledError, KeyboardInterrupt):
		pass
	finally:
		logger.info('Shutting down')

		poller_task.cancel()
		telegram_bot_task.cancel()

		await asyncio.gather(
			poller_task,
			telegram_bot_task,
			return_exceptions=True
		)

		await telegram_bot.stop()
		poller.stop()
		await client.close()


if __name__ == '__main__':
	asyncio.run(main())