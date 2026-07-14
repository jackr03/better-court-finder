import logging

import asyncpg

from src.models.venue import Venue

logger = logging.getLogger(__name__)

class NotificationStore:
	def __init__(self, user: str, password: str, database: str, host: str, port: int):
		self._conn_params = {
			'user': user,
			'password': password,
			'database': database,
			'host': host,
			'port': port
		}

		self._pool: asyncpg.Pool | None = None

	async def connect(self) -> None:
		self._pool = await asyncpg.create_pool(**self._conn_params)
		logger.info(f'Connected to Postgres (host={self._conn_params['host']}, port={self._conn_params['port']}, database={self._conn_params['database']})')

	async def close(self) -> None:
		if self._pool:
			await self._pool.close()

	async def toggle_subscription(self, user_id, venue: Venue) -> None:
		subscribed = await self._pool.fetchval(
			'''
			SELECT EXISTS(SELECT 1
                          FROM subscriptions
                          WHERE user_id = $1
                            AND venue = $2);
			''',
			user_id, venue
		)

		if subscribed:
			await self.unsubscribe(user_id, venue)
		else:
			await self.subscribe(user_id, venue)

	async def subscribe(self, user_id: str, venue: Venue) -> None:
		await self._pool.execute(
			'''
			INSERT INTO subscriptions (user_id, venue)
			VALUES ($1, $2) ON CONFLICT DO NOTHING
			''',
			user_id, venue
		)

	async def unsubscribe(self, user_id, venue: Venue) -> None:
		await self._pool.execute(
			'''
			DELETE FROM subscriptions
			WHERE user_id = $1 AND venue = $2
			''',
			user_id, venue
		)

	async def unsubscribe_all(self, user_id) -> None:
		await self._pool.execute(
			'''
			DELETE FROM subscriptions
			WHERE user_id = $1
			''',
			user_id
		)

	async def find_venues_for_user(self, user_id) -> set[Venue]:
		rows = await self._pool.fetch(
			'''
			SELECT venue FROM subscriptions
			WHERE user_id = $1
			''',
			user_id
		)

		return {Venue(row['venue']) for row in rows}

	async def find_users_for_venue(self, venue: Venue) -> set[str]:
		rows = await self._pool.fetch(
			'''
			SELECT user_id FROM subscriptions
			WHERE venue = $1
			''',
			venue
		)

		return {row['user_id'] for row in rows}
