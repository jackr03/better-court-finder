import logging
from datetime import timedelta, datetime, date

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from src.services.court_database import CourtDatabase
from src.services.court_updater import CourtUpdater

from src.court_formatter import format_court_availability
from src.telegram_bot.bot_config import BotConfig

logger = logging.getLogger(__name__)
router = Router()


# TODO: Add an introduction message to /start
@router.message(CommandStart())
async def start_command(message: Message):
	_log_command(message)
	await message.answer('Test')


@router.message(Command('search'))
async def search_command(message: Message):
	_log_command(message)
	text, keyboard, parse_mode = _create_search_message()
	await message.answer(text, reply_markup=keyboard, parse_mode=parse_mode)


@router.callback_query(lambda c: c.data == 'search')
async def search_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)
	text, keyboard, parse_mode = _create_search_message()
	await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=parse_mode)


@router.callback_query(lambda c: c.data == 'search_all')
async def search_all_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)
	courts = CourtDatabase().get_all_available()

	await callback_query.message.edit_text(
		format_court_availability(
			courts,
			'❌ No courts available.'),
		reply_markup=_create_back_button_keyboard('search')
	)


@router.callback_query(lambda c: c.data == 'search_by_date')
async def search_by_date_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)

	dates = [(datetime.today() + timedelta(days=i)).date() for i in range(6)]

	keyboard_buttons = [
		[InlineKeyboardButton(
			text=f'📅 {d.strftime("%A (%d/%m)")}',
			callback_data=f'search_by_date_{d.isoformat()}'
		)] for d in dates
	]

	keyboard_buttons.append([_create_back_button('search')])

	await callback_query.message.edit_text(
		f'🔍 Select a date:\n{_get_last_updated()}',
		reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
		parse_mode='Markdown'
	)


@router.callback_query(lambda c: c.data.startswith('search_by_date_'))
async def search_by_date_selected_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)
	prefix = 'search_by_date_'
	search_date = date.fromisoformat(callback_query.data[len(prefix):])
	courts = CourtDatabase().get_available_by_date(search_date)

	await callback_query.message.edit_text(
		format_court_availability(
			courts,
			f'❌ No courts available on {search_date.strftime("%A (%d/%m)")}.'),
		reply_markup=_create_back_button_keyboard('search_by_date')
	)


@router.callback_query(lambda c: c.data == 'search_by_time')
async def search_by_time_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)

	keyboard_buttons = [
		[InlineKeyboardButton(
			text='🌅 Morning (07:00 - 12:00)',
			callback_data='search_by_time_morning'
		)],
		[InlineKeyboardButton(
			text='☀️ Afternoon (12:00 - 17:00)',
			callback_data='search_by_time_afternoon'
		)],
		[InlineKeyboardButton(
			text='🌙 Evening (17:00 - 22:00)',
			callback_data='search_by_time_evening'
		)],
		[_create_back_button('search')]
	]

	await callback_query.message.edit_text(
		f'🔍 Select a time:\n{_get_last_updated()}',
		reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
		parse_mode='Markdown'
	)


@router.callback_query(lambda c: c.data.startswith('search_by_time_'))
async def search_by_time_selected_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)
	prefix = 'search_by_time_'
	time_range = {
		'morning': ('07:00', '12:00'),
		'afternoon': ('12:00', '17:00'),
		'evening': ('17:00', '22:00')
	}[callback_query.data[len(prefix):]]

	courts = CourtDatabase().get_available_by_time_range(time_range)

	await callback_query.message.edit_text(
		format_court_availability(
			courts,
			f'❌ No courts available for the time range {time_range[0]} - {time_range[1]}.'
		),
		reply_markup=_create_back_button_keyboard('search_by_time')
	)


@router.message(Command('notify'))
async def notify_command(message: Message):
	_log_command(message)
	user_id = message.from_user.id

	if user_id in BotConfig().get_notify_list():
		BotConfig().remove_from_notify_list(user_id)
		await message.answer(
			'''
			🔕 You are no longer on the notification list.
🏸 You won't receive updates about court availability.
			'''
		)
	else:
		BotConfig().add_to_notify_list(user_id)
		await message.answer(
			'''
			🔔 You are now on the notification list.
🏸 You will be pinged automatically when courts become available.
			'''
		)


@router.message(Command('refresh'))
async def refresh_command(message: Message):
	_log_command(message)

	msg = await message.answer(
		'🔄 Manually updating courts, please wait...'
	)

	CourtUpdater().update()

	await msg.edit_text(
		f'✅ Courts updated successfully!\n{_get_last_updated()}',
		parse_mode='Markdown'
	)


# HELPER METHODS
def _create_search_message() -> tuple[str, InlineKeyboardMarkup, str]:
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(
			text='🗓️ All',
			callback_data='search_all'
		)],
		[InlineKeyboardButton(
			text='📅 Date',
			callback_data='search_by_date'
		)],
		[InlineKeyboardButton(
			text='⏰ Time',
			callback_data='search_by_time'
		)]
	])

	return (
		f'🔍 Choose your search criteria:\n{_get_last_updated()}',
		keyboard,
		'Markdown'
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


def _get_last_updated() -> str:
	"""Return last updated time as a markdown string with italics."""
	last_updated = CourtUpdater().get_last_updated()
	return f'_Last updated: {last_updated}_'


def _log_command(message: Message) -> None:
	logger.debug(f'Received command: {message.text} from user {message.from_user.id}')


def _log_callback_query(callback_query: CallbackQuery) -> None:
	logger.debug(f'Received callback query: {callback_query.data} from user {callback_query.from_user.id}')
