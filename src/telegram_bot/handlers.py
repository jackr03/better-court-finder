import logging
from datetime import datetime, timedelta, date
from functools import wraps
from typing import Callable

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.court.cache import CourtCache
from src.models.court import Court
from src.models.time_range import TimeRange
from src.models.venue import Venue
from src.telegram_bot.constants import Commands, CallbackData, Messages, Keyboards
from src.telegram_bot.formatter import format_court_availability
from src.utils import format_date_and_time, format_date

logger = logging.getLogger(__name__)
router = Router()

_PARSE_MODE = 'Markdown'


def log_update(func: Callable):
	@wraps(func)
	async def wrapper(update: Message | CallbackQuery, *args, **kwargs):
		if isinstance(update, Message):
			logger.info(f'Received command: {update.text} from user {update.from_user.id}')
		elif isinstance(update, CallbackQuery):
			logger.info(f'Received callback query: {update.data} from user {update.from_user.id}')
		return await func(update, *args, **kwargs)
	return wrapper


@router.message(Command(Commands.SEARCH))
@log_update
async def search_command(message: Message, cache: CourtCache):
	text, keyboard, parse_mode = await _create_search_message(cache)
	await message.answer(
		text,
		reply_markup=keyboard,
		parse_mode=parse_mode
	)


@router.callback_query(lambda c: c.data == Commands.SEARCH)
@log_update
async def search_callback(callback_query: CallbackQuery, cache: CourtCache):
	text, keyboard, parse_mode = await _create_search_message(cache)
	await callback_query.message.edit_text(
		text,
		reply_markup=keyboard,
		parse_mode=parse_mode
	)


@router.callback_query(lambda c: c.data == Commands.SEARCH_ALL)
@log_update
async def search_all_callback(callback_query: CallbackQuery, cache: CourtCache):
	courts = await cache.get_all_available_courts()

	await _handle_court_results(
		callback_query,
		courts,
		Messages.NO_COURTS,
		Commands.SEARCH
	)


@router.callback_query(lambda c: c.data == Commands.SEARCH_BY_DATE)
@log_update
async def search_by_date_callback(callback_query: CallbackQuery, cache: CourtCache):
	dates = [(datetime.today() + timedelta(days=i)).date() for i in range(6)]
	keyboard_buttons = [
		[InlineKeyboardButton(
			text=f'📅 {format_date(d)}',
			callback_data=f'{CallbackData.DATE_PREFIX}{d.isoformat()}'
		)] for d in dates
	]

	await _send_selection_message(
		callback_query,
		cache,
		Messages.SELECT_DATE,
		keyboard_buttons,
		Commands.SEARCH
	)


@router.callback_query(lambda c: c.data.startswith(CallbackData.DATE_PREFIX))
@log_update
async def search_by_date_selected_callback(callback_query: CallbackQuery, cache: CourtCache):
	search_date = date.fromisoformat(_get_callback_data(callback_query, CallbackData.DATE_PREFIX))
	courts = await cache.get_available_by_date(search_date)

	await _handle_court_results(
		callback_query,
		courts,
		Messages.NO_COURTS_FOR_DATE.format(date=search_date),
		Commands.SEARCH_BY_DATE
	)


@router.callback_query(lambda c: c.data == Commands.SEARCH_BY_TIME)
@log_update
async def search_by_time_callback(callback_query: CallbackQuery, cache: CourtCache):
	await _send_selection_message(
		callback_query,
		cache,
		Messages.SELECT_TIME,
		Keyboards.TIME,
		Commands.SEARCH
	)


@router.callback_query(lambda c: c.data.startswith(CallbackData.TIME_PREFIX))
@log_update
async def search_by_time_selected_callback(callback_query: CallbackQuery, cache: CourtCache):
	time_range = TimeRange[_get_callback_data(callback_query, CallbackData.TIME_PREFIX)]
	courts = await cache.get_available_by_time_range(time_range)

	await _handle_court_results(
		callback_query,
		courts,
		Messages.NO_COURTS_FOR_TIME.format(time_range=time_range.label),
		Commands.SEARCH_BY_TIME
	)


@router.callback_query(lambda c: c.data == Commands.SEARCH_BY_VENUE)
@log_update
async def search_by_venue_callback(callback_query: CallbackQuery, cache: CourtCache):
	await _send_selection_message(
		callback_query,
		cache,
		Messages.SELECT_VENUE,
		Keyboards.VENUE,
		Commands.SEARCH
	)


@router.callback_query(lambda c: c.data.startswith(CallbackData.VENUE_PREFIX))
@log_update
async def search_by_venue_selected_callback(callback_query: CallbackQuery, cache: CourtCache):
	venue = Venue(_get_callback_data(callback_query, CallbackData.VENUE_PREFIX))
	courts = await cache.get_available_by_venue(venue)

	await _handle_court_results(
		callback_query,
		courts,
		Messages.NO_COURTS_FOR_VENUE.format(venue=venue.display_name),
		Commands.SEARCH_BY_VENUE
	)


def _create_back_button_keyboard(callback_data: str) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[_create_back_button(callback_data)]
	])


def _create_back_button(callback_data: str) -> InlineKeyboardButton:
	return InlineKeyboardButton(
		text='⬅️ Back',
		callback_data=callback_data
	)


def _get_callback_data(callback_query: CallbackQuery, prefix: str) -> str:
	return callback_query.data[len(prefix):]


async def _create_search_message(cache: CourtCache) -> tuple[str, InlineKeyboardMarkup, str]:
	last_updated = await _get_last_updated(cache)
	return (
		Messages.SEARCH_PROMPT.format(last_updated=last_updated),
		InlineKeyboardMarkup(inline_keyboard=Keyboards.SEARCH),
		_PARSE_MODE
	)


async def _send_selection_message(
		callback_query: CallbackQuery,
		cache: CourtCache,
		header: str,
		keyboard_buttons: list,
		back_command: str,
) -> None:
	last_updated = await _get_last_updated(cache)
	buttons = list(keyboard_buttons) + [[_create_back_button(back_command)]]

	await callback_query.message.edit_text(
		header.format(last_updated=last_updated),
		reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
		parse_mode=_PARSE_MODE
	)


async def _handle_court_results(
		callback_query: CallbackQuery,
		courts: list[Court],
		empty_message: str,
		back_button: str | None
) -> None:
	if courts:
		message = format_court_availability(courts)
	else:
		message = empty_message
	await callback_query.message.edit_text(
		message,
		reply_markup=_create_back_button_keyboard(back_button) if back_button else None,
		parse_mode=_PARSE_MODE
	)


async def _get_last_updated(cache: CourtCache) -> str:
	last_updated = await cache.get_last_updated()
	formatted_last_updated = format_date_and_time(last_updated)
	return f'_Last updated: {formatted_last_updated}_' if last_updated else 'Never'
