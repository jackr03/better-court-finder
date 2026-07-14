from aiogram.filters.callback_data import CallbackData


class SearchByDate(CallbackData, prefix='search_by_date'):
    date: str


class SearchByTime(CallbackData, prefix='search_by_time'):
    time_range: str


class SearchByVenue(CallbackData, prefix='search_by_venue'):
    venue: str


class ToggleNotification(CallbackData, prefix='toggle_notification'):
    venue: str
