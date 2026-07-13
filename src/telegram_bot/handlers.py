import asyncio
import logging
from datetime import datetime, timedelta, date
from functools import wraps
from typing import Callable

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.config import CONFIG
from src.court.cache import CourtCache
from src.models.court import Court
from src.models.time_range import TimeRange
from src.models.venue import Venue
from src.notifications.store import NotificationStore
from src.telegram_bot.callbacks import SearchByDate, SearchByTime, SearchByVenue, ToggleNotification
from src.telegram_bot.constants import Commands, Messages, Keyboards
from src.telegram_bot.formatter import format_court_availability
from src.utils import format_date_and_time, format_date

logger = logging.getLogger(__name__)
router = Router()

MAX_MSG_LENGTH = 4096


def log_update(func: Callable):
	@wraps(func)
	async def wrapper(update: Message | CallbackQuery, *args, **kwargs):
		if isinstance(update, Message):
			logger.info(f'Received command: {update.text} from user {update.from_user.id}')
		elif isinstance(update, CallbackQuery):
			logger.info(f'Received callback query: {update.data} from user {update.from_user.id}')
		return await func(update, *args, **kwargs)
	return wrapper


# region Search Command
@router.message(Command(Commands.SEARCH))
@log_update
async def search_command(message: Message, cache: CourtCache):
	text, keyboard = await _create_search_message(cache)
	await message.answer(
		text=text,
		reply_markup=keyboard,
	)


@router.callback_query(F.data == Commands.SEARCH)
@log_update
async def search_callback(callback_query: CallbackQuery, cache: CourtCache):
	text, keyboard = await _create_search_message(cache)
	await callback_query.message.edit_text(
		text=text,
		reply_markup=keyboard,
	)
	await callback_query.answer()


@router.callback_query(F.data == Commands.SEARCH_ALL)
@log_update
async def search_all_callback(
		callback_query: CallbackQuery,
		state: FSMContext,
		cache: CourtCache,
):
	courts = await cache.get_all_available_courts()

	await _handle_court_results(
		callback_query,
		state,
		courts,
		Messages.NO_COURTS,
	)


@router.callback_query(F.data == Commands.SEARCH_BY_DATE)
@log_update
async def search_by_date_callback(callback_query: CallbackQuery, cache: CourtCache):
	dates = [(datetime.today() + timedelta(days=i)).date() for i in range(6)]
	keyboard_buttons = [
		[InlineKeyboardButton(
			text=f'📅 {format_date(d)}',
			callback_data=SearchByDate(date=d.isoformat()).pack()
		)] for d in dates
	]

	await _send_selection_message(
		callback_query,
		cache,
		Messages.SELECT_DATE,
		keyboard_buttons,
		Commands.SEARCH
	)


@router.callback_query(SearchByDate.filter())
@log_update
async def search_by_date_selected_callback(
		callback_query: CallbackQuery,
		callback_data: SearchByDate,
		state: FSMContext,
		cache: CourtCache,
):
	search_date = date.fromisoformat(callback_data.date)
	courts = await cache.get_available_by_date(search_date)

	await _handle_court_results(
		callback_query,
		state,
		courts,
		Messages.NO_COURTS_FOR_DATE.format(date=search_date),
	)


@router.callback_query(F.data == Commands.SEARCH_BY_TIME)
@log_update
async def search_by_time_callback(callback_query: CallbackQuery, cache: CourtCache):
	await _send_selection_message(
		callback_query,
		cache,
		Messages.SELECT_TIME,
		Keyboards.TIME,
		Commands.SEARCH
	)


@router.callback_query(SearchByTime.filter())
@log_update
async def search_by_time_selected_callback(
		callback_query: CallbackQuery,
		callback_data: SearchByTime,
		state: FSMContext,
		cache: CourtCache,
):
	time_range = TimeRange[callback_data.time_range]
	courts = await cache.get_available_by_time_range(time_range)

	await _handle_court_results(
		callback_query,
		state,
		courts,
		Messages.NO_COURTS_FOR_TIME.format(time_range=time_range.label),
	)


@router.callback_query(F.data == Commands.SEARCH_BY_VENUE)
@log_update
async def search_by_venue_callback(callback_query: CallbackQuery, cache: CourtCache):
	await _send_selection_message(
		callback_query,
		cache,
		Messages.SELECT_VENUE,
		Keyboards.VENUE,
		Commands.SEARCH
	)


@router.callback_query(SearchByVenue.filter())
@log_update
async def search_by_venue_selected_callback(
		callback_query: CallbackQuery,
		callback_data: SearchByVenue,
		state: FSMContext,
		cache: CourtCache,
):
	venue = Venue(callback_data.venue)
	courts = await cache.get_available_by_venue(venue)

	await _handle_court_results(
		callback_query,
		state,
		courts,
		Messages.NO_COURTS_FOR_VENUE.format(venue=venue.display_name),
		for_venue=True
	)


async def _create_search_message(cache: CourtCache) -> tuple[str, InlineKeyboardMarkup]:
	last_updated = await _get_last_updated(cache)
	return (
		Messages.SEARCH_PROMPT.format(last_updated=last_updated),
		InlineKeyboardMarkup(inline_keyboard=Keyboards.SEARCH),
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
	)
	await callback_query.answer()


async def _handle_court_results(
		callback_query: CallbackQuery,
		state: FSMContext,
		courts: list[Court],
		empty_message: str,
		for_venue: bool = False
) -> None:
	if courts:
		message = format_court_availability(courts, for_venue)
	else:
		message = empty_message

	chunks = _split_message_into_chunks(message)
	sent_message_ids = []

	for i, chunk in enumerate(chunks):
		# Last message should contain a back button
		is_last = i == len(chunks) - 1
		keyboard = _create_close_button_keyboard() if is_last else None

		sent = await callback_query.message.answer(
			text=chunk,
			reply_markup=keyboard
		)

		# Answer callback_query after processing first chunk
		if i == 0:
			await callback_query.answer()

		sent_message_ids.append(sent.message_id)
		await asyncio.sleep(CONFIG.telegram.multi_message_delay)

	await state.update_data(message_ids=sent_message_ids)


def _split_message_into_chunks(message: str) -> list[str]:
	lines = message.split('\n')
	chunks = []
	current = []
	current_length = 0
	for line in lines:
		# Account for the line feed character
		line_length = len(line) + 1

		if line_length > MAX_MSG_LENGTH:
			error_message = f'Single line exceeds {MAX_MSG_LENGTH} characters: {line}'
			logger.error(error_message)
			raise ValueError(error_message)

		if current_length + line_length > MAX_MSG_LENGTH:
			chunks.append('\n'.join(current))
			current = []
			current_length = 0

		current.append(line)
		current_length += line_length

	# Need to add remaining lines in buffer
	chunks.append('\n'.join(current))

	return chunks


async def _get_last_updated(cache: CourtCache) -> str:
	last_updated = await cache.get_last_updated()
	formatted_last_updated = format_date_and_time(last_updated)
	return f'_Last updated: {formatted_last_updated}_' if last_updated else 'Never'


def _create_back_button(callback_data: str) -> InlineKeyboardButton:
	return InlineKeyboardButton(
		text=Messages.BACK,
		callback_data=callback_data
	)
# endregion

# region Close
@router.callback_query(F.data == Commands.CLOSE)
@log_update
async def close_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
	await _delete_stored_messages(callback_query, state)

	# KNOWN BUG: close button only handles the latest set of results, since context is overwritten
	# Too much effort to fix the issue fully, so as a compromise always delete the message close was pressed on at least
	try:
		await callback_query.message.delete()
	except TelegramBadRequest:
		pass
	await callback_query.answer()


async def _delete_stored_messages(callback_query: CallbackQuery, state: FSMContext) -> None:
	data = await state.get_data()
	message_ids = data.get('message_ids')
	if not message_ids:
		return

	chat_id = callback_query.message.chat.id
	results = await asyncio.gather(
		*(callback_query.bot.delete_message(chat_id, message_id) for message_id in message_ids),
		return_exceptions=True
	)
	for message_id, result in zip(message_ids, results):
		if isinstance(result, Exception):
			logger.warning(f'Failed to delete message {message_id}: {result}')

	await state.update_data(message_ids=[])


def _create_close_button_keyboard() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(
			text=Messages.CLOSE,
			callback_data=Commands.CLOSE
		)]
	])
# endregion

# region Notifications
@router.message(Command(Commands.NOTIFICATIONS))
@log_update
async def notifications_command(message: Message, notification_store: NotificationStore):
	subscribed_venues = await notification_store.find_venues_for_user(message.from_user.id)
	keyboard = await _create_notifications_keyboard(subscribed_venues)

	await message.answer(
		text=Messages.NOTIFICATIONS,
		reply_markup=keyboard,
	)


@router.callback_query(ToggleNotification.filter())
@log_update
async def toggle_notification_callback(
		callback_query: CallbackQuery,
		callback_data: ToggleNotification,
		notification_store: NotificationStore,
):
	await notification_store.toggle_subscription(callback_query.from_user.id, Venue(callback_data.venue))

	subscribed_venues = await notification_store.find_venues_for_user(callback_query.from_user.id)
	keyboard = await _create_notifications_keyboard(subscribed_venues)

	await callback_query.message.edit_text(
		text=Messages.NOTIFICATIONS,
		reply_markup=keyboard,
	)
	await callback_query.answer()


async def _create_notifications_keyboard(subscribed_venues: set[Venue]) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(
			text=f'{'🟢' if venue in subscribed_venues else '⚪'} {venue.display_name}',
			callback_data=ToggleNotification(venue=venue).pack()
		)]
		for venue in Venue
	])
# endregion
