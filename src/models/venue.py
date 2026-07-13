from enum import StrEnum

from src.models.activity import Activity


class Venue(StrEnum):
    ARDWICK_SPORTS_HALL = 'ardwick-sports-hall'
    BELLE_VUE_SPORTS_VILLAGE = 'belle-vue-sports-village'
    MOSS_SIDE_LEISURE_CENTRE = 'moss-side-leisure-centre'
    SUGDEN_SPORTS_CENTRE = 'sugden-sports-centre'

    @property
    def display_name(self) -> str:
        return self.name.replace('_', ' ').title()

    @property
    def activities(self) -> list[Activity]:
        match self:
            case Venue.BELLE_VUE_SPORTS_VILLAGE | Venue.MOSS_SIDE_LEISURE_CENTRE | Venue.SUGDEN_SPORTS_CENTRE:
                return [Activity.BADMINTON_60MIN, Activity.BADMINTON_40MIN]
            case Venue.ARDWICK_SPORTS_HALL:
                return [Activity.BADMINTON_40MIN]
