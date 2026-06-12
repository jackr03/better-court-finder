from datetime import time
from enum import Enum

from src.utils import format_time


class TimeRange(Enum):
    MORNING = (time(7), time(12), '🌅')
    AFTERNOON = (time(12), time(17), '☀️')
    EVENING = (time(17), time(22), '🌙')

    def __init__(self, start: time, end: time, emoji: str):
        self.start = start
        self.end = end
        self.emoji = emoji

    @property
    def label(self) -> str:
        return f'{self.name} ({format_time(self.start)} - {format_time(self.end)}'

    @property
    def display_name(self) -> str:
        return f'{self.emoji} {self.name.capitalize()} ({format_time(self.start)} - {format_time(self.end)})'

    def contains(self, t: time) -> bool:
        return self.start <= t <= self.end
