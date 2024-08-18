import logging
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from database import (create_database_connection, create_table_users, create_table_logs, add_user, update_user_language,
                      log_user_action, reset_daily_keys_if_needed, is_user_banned, get_user_language, get_oldest_keys)

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = int(API_TOKEN.split(':')[0])
games = [
    'Riding Extreme 3D',
    'Chain Cube 2048',
    'My Clone Army',
    'Train Miner',
    'Merge Away',
    'Twerk Race 3D'
]
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Connect to the databases and create the tables if it does not exist
conn = create_database_connection()
create_table_users(conn)
create_table_logs(conn)


# Load translations from json
def load_translations():
    translations_path = os.path.join(os.path.dirname(__file__), 'translations.json')
    if os.path.exists(translations_path):
        try:
            with open(translations_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading translations: {e}")
    else:
        logging.warning("Translations file not found. Using default empty translations.")
    return {}


translations = load_translations()


# Get translations
def get_translation(user_id, key):
    user_lang = get_user_language(conn, user_id)
    return translations.get(user_lang, {}).get(key, key)


# Bot states
class Form(StatesGroup):
    choosing_language = State()


# Setting bot commands
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/change_lang", description="Change language / Сменить язык")
    ]
    await bot.set_my_commands(commands)


# Command handler /start
@dp.message(F.text == "/start")
async def send_welcome(message: types.Message, state: FSMContext):
    user = message.from_user
    user_id = user.id if user.id != BOT_ID else message.chat.id
    chat_id = message.chat.id
    first_name = user.first_name
    last_name = user.last_name
    username = user.username
    language_code = user.language_code

    # Reset daily keys if needed
    reset_daily_keys_if_needed(conn, user_id)

    # Log user action
    log_user_action(conn, user_id, "/start command used")

    # Language selection based on the user's language
    selected_language = "ru" if language_code in ["ru", "uk"] else "en"

    # Save user in DB
    add_user(conn, chat_id, user_id, first_name, last_name, username, selected_language)

    await display_action_menu(message, state)


# Displaying the action menu
async def display_action_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    chat_id = message.chat.id

    # Obtaining an updated user language
    user_lang = get_user_language(conn, user_id)

    image_path = os.path.join(os.path.dirname(__file__), "images", 'start_image.jpg')
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        sent_message = await bot.send_photo(chat_id, photo=photo)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_translation(user_id, "get_keys"), callback_data="get_keys"),
         InlineKeyboardButton(text=get_translation(user_id, "change_status"), callback_data="change_status")],
    ])

    sent_message = await bot.send_message(
        chat_id,
        get_translation(user_id, "chose_action"),
        reply_markup=buttons
    )

    # Save the ID of the last menu message to delete it later
    await state.update_data(last_menu_message_id=sent_message.message_id)


# Change language command
@dp.message(F.text == "/change_lang")
async def change_language(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

    # Log user action
    log_user_action(conn, user_id, "/change_lang command used")

    # Check for a ban before performing any actions
    if is_user_banned(conn, user_id):
        await handle_banned_user(message)
        return

    language_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English", callback_data="en"),
         InlineKeyboardButton(text="Русский", callback_data="ru")],
    ])

    # Send the message and store its ID in the state
    lang_message = await message.answer(get_translation(user_id, "choose_language"), reply_markup=language_buttons)

    # Save the IDs of the language message and user's command message
    await state.update_data(lang_message_id=lang_message.message_id, user_command_message_id=message.message_id)

    await state.set_state(Form.choosing_language)


# Language selection processing
@dp.callback_query(F.data.in_({"en", "ru"}))
async def set_language(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
    selected_language = callback_query.data

    # Updating the language in the database
    update_user_language(conn, user_id, selected_language)

    # Forcibly query the language from the database again
    new_language = get_user_language(conn, user_id)
    logging.info(f"Language after update for user {user_id}: {new_language}")

    # Log user action
    log_user_action(conn, user_id, f"Language changed to {selected_language}")

    # Deleting the language selection message and the user's command message
    data = await state.get_data()
    if "lang_message_id" in data:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=data["lang_message_id"])
    if "user_command_message_id" in data:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=data["user_command_message_id"])

    # Sending confirmation and proceeding to game selection
    await bot.send_message(
        callback_query.message.chat.id,
        get_translation(user_id, "language_selected")
    )

    # Displaying the updated action menu
    await display_action_menu(callback_query.message, state)

    # Resetting the state
    await state.clear()


# Handling of "get_keys" button pressing
@dp.callback_query(F.data == "get_keys")
async def send_keys(callback_query: types.CallbackQuery, state: FSMContext):
    for game in games:
        keys = get_oldest_keys(conn, game)
        if keys:
            response_text = f"Промокоды для *{game}*:\n"
            for key in keys:
                response_text += f"`{key[0]}`\n"
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=response_text,
                parse_mode="MarkdownV2"
            )
        else:
            response_text = f"Для игры *{game}* нет доступных промокодов 😢"
            await bot.send_message(chat_id=callback_query.message.chat.id, text=response_text, parse_mode="MarkdownV2")

    await callback_query.answer()
    await display_action_menu(callback_query.message, state)


# Handler of other messages (including ban check)
@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

    # Ban check
    if is_user_banned(conn, user_id):
        await handle_banned_user(message)
        return

    # Logging a user's message
    log_user_action(conn, user_id, f"User message: {message.text}")

    # Response to user post
    await message.answer(get_translation(user_id, "default_response"))


# Handling banned users
async def handle_banned_user(message: types.Message):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    chat_id = message.chat.id

    # User action logging
    log_user_action(conn, user_id, "Attempted interaction while banned")

    # Sending a ban notification
    image_path = os.path.join(os.path.dirname(__file__), "images", 'banned_image.jpg')
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(chat_id, photo=photo, caption=get_translation(user_id, "ban_message"))
    else:
        await bot.send_message(chat_id, get_translation(user_id, "ban_message"))


async def main():
    await dp.start_polling(bot)
    await set_commands(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
