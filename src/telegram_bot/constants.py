from aiogram.types import InlineKeyboardButton

from src.models.time_range import TimeRange
from src.models.venue import Venue
from src.telegram_bot.callbacks import SearchByTime, SearchByVenue


class Commands:
    SEARCH = 'search'
    SEARCH_ALL = 'search_all'
    SEARCH_BY_DATE = 'search_by_date'
    SEARCH_BY_TIME = 'search_by_time'
    SEARCH_BY_VENUE = 'search_by_venue'
    CLOSE = 'close'
    NOTIFICATIONS = 'notifications'


class Messages:
    BACK = '⬅️ Back'
    CLOSE = '❌ Close'
    NO_COURTS = '❌ No courts available.'
    NO_COURTS_FOR_DATE = '❌ No courts available for {date}.'
    NO_COURTS_FOR_TIME = '❌ No courts available in the {time_range}.'
    NO_COURTS_FOR_VENUE = '❌ No courts available at {venue}.'
    SEARCH_PROMPT = '🔍 Choose your search criteria:\n{last_updated}'
    SELECT_DATE = '🔍 Select a date:\n{last_updated}'
    SELECT_TIME = '🔍 Select a time:\n{last_updated}'
    SELECT_VENUE = '🔍 Select a venue:\n{last_updated}'
    COURTS_AVAILABLE = '✅ Courts available'
    COURTS_UNAVAILABLE = '❌ Courts unavailable'
    NOTIFICATIONS = '🔔 Choose venues to receive notifications for:'


class Keyboards:
    """A helper class containing only the static keyboards."""
    SEARCH = [
        [InlineKeyboardButton(text=text, callback_data=command)]
        for text, command in [
            ('🗓️ All', Commands.SEARCH_ALL),
            ('📅 Date', Commands.SEARCH_BY_DATE),
            ('⏰ Time', Commands.SEARCH_BY_TIME),
            ('📍 Venue', Commands.SEARCH_BY_VENUE),
        ]
    ]

    TIME = [
        [InlineKeyboardButton(
            text=time_range.display_name,
            callback_data=SearchByTime(time_range=time_range.name).pack()
        )]
        for time_range in TimeRange
    ]

    VENUE = [
        [InlineKeyboardButton(
            text=f'📍 {venue.display_name}',
            callback_data=SearchByVenue(venue=venue.value).pack()
        )]
        for venue in Venue
    ]
