from enum import StrEnum


class Platform(StrEnum):
	TELEGRAM = 'telegram'

	@property
	def display_name(self) -> str:
		return self.value.capitalize()