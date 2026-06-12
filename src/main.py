import asyncio
import logging
import os

from dotenv import load_dotenv

from src.config import CONFIG
from src.court.cache import CourtCache
from src.court.poller import CourtPoller
from src.telegram_bot.telegram_bot import TelegramBot

load_dotenv()
logging.basicConfig(
	level=CONFIG.logging_level,
	format='%(asctime)s [%(levelname)s] %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)


async def main():
	cache = CourtCache()
	await cache.connect()

	poller = CourtPoller(cache)
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
		logging.info('Shutting down')

		poller_task.cancel()
		telegram_bot_task.cancel()

		await asyncio.gather(
			poller_task,
			telegram_bot_task,
			return_exceptions=True
		)

		await telegram_bot.stop()
		poller.stop()
		await cache.close()


if __name__ == '__main__':
	asyncio.run(main())