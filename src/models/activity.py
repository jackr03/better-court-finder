from enum import StrEnum


class Activity(StrEnum):
    BADMINTON_40MIN = 'badminton-40min'
    BADMINTON_60MIN = 'badminton-60min'

    @property
    def display_name(self) -> str:
        return self.name.replace('_', ' ').title()