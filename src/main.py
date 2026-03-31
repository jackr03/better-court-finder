import asyncio
import logging

from src.tasks import telegram_bot_task, court_updater_task

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s [%(levelname)s] %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)


async def main():
	await asyncio.gather(
		court_updater_task(),
		telegram_bot_task(),
	)


if __name__ == '__main__':
	asyncio.run(main())