from enum import StrEnum

from src.models.activity import Activity


class Venue(StrEnum):
    SUGDEN_SPORTS_CENTRE = 'sugden-sports-centre'
    ARDWICK_SPORTS_HALL = 'ardwick-sports-hall'

    @property
    def display_name(self) -> str:
        return self.name.replace('_', ' ').title()

    @property
    def activities(self) -> list[Activity]:
        match self:
            case Venue.SUGDEN_SPORTS_CENTRE:
                return [Activity.BADMINTON_60MIN, Activity.BADMINTON_40MIN]
            case Venue.ARDWICK_SPORTS_HALL:
                return [Activity.BADMINTON_40MIN]