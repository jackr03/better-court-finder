import asyncio
import logging

from src.court_cache import CourtCache
from src.court_poller import CourtPoller

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s [%(levelname)s] %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)


async def main():
	cache = CourtCache()
	await cache.connect()

	poller = CourtPoller(cache)

	await asyncio.gather(
		poller.run()
	)


if __name__ == '__main__':
	asyncio.run(main())