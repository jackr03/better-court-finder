import logging
from datetime import datetime
from typing import Optional

from src.services.court_database import CourtDatabase
from src.services.court_fetcher import CourtFetcher

logger = logging.getLogger(__name__)


class CourtUpdater:
	_instance = None
	_initialised = False

	def __new__(cls):
		if cls._instance is None:
			logger.debug('Creating a new instance of CourtUpdater')
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self):
		if self._initialised:
			return
		self.court_fetcher = CourtFetcher()
		self.court_database = CourtDatabase()
		self.last_updated: Optional[datetime] = None
		self._initialised = True

	def update(self) -> None:
		logger.info('Updating court database')
		courts = self.court_fetcher.fetch_all()
		self.court_database.insert(courts)
		logger.info('Court database updated successfully')

		self._set_last_updated()

	def get_last_updated(self) -> str:
		"""
		Returns the time that courts were last updated as a string in the format HH:MM:SS.
		"""
		if self.last_updated:
			return self.last_updated.strftime('%H:%M:%S')
		return 'never'

	def _set_last_updated(self) -> None:
		self.last_updated = datetime.now()
		logger.debug(f'Last updated time set to {self.get_last_updated()}')
