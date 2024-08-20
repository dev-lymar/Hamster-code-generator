import logging
import os
import json
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from database import (create_database_connection, create_table_users, create_table_logs, add_user, update_user_language,
                      log_user_action, reset_daily_keys_if_needed, is_user_banned, get_user_language, get_oldest_keys,
                      update_keys_generated, delete_keys, check_user_limits, get_last_request_time, get_remaining_time)

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
status_limits = {
    'free': {'daily_limit': 2, 'interval_minutes': 60},
    'friend': {'daily_limit': 5, 'interval_minutes': 0},
    'premium': {'daily_limit': 25, 'interval_minutes': 30}
}
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


# Function that returns the button bar
def get_action_buttons(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_translation(user_id, "get_keys"), callback_data="get_keys")],
    ])


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

    # Log user action
    log_user_action(conn, user_id, "/start command used")

    # Language selection based on the user's language
    selected_language = "ru" if language_code in ["ru", "uk"] else "en"

    # Save user in DB
    add_user(conn, chat_id, user_id, first_name, last_name, username, selected_language)

    # Sending welcome message
    welcome_text = get_translation(user_id, "welcome_message").format(first_name=first_name)
    image_path = os.path.join(os.path.dirname(__file__), "images", 'welcome_image.jpg')
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(chat_id, photo=photo, caption=welcome_text, reply_markup=get_action_buttons(user_id))
    else:
        await bot.send_message(chat_id, text=welcome_text, reply_markup=get_action_buttons(user_id))


# Function to send keys menu after generating keys
async def send_keys_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    chat_id = message.chat.id

    # Use the function to get the buttons
    buttons = get_action_buttons(user_id)

    # Send the key generated image and message
    image_path = os.path.join(os.path.dirname(__file__), "images", 'key_generated_image.jpg')
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(chat_id, photo=photo, caption=get_translation(user_id, "chose_action"), reply_markup=buttons)
    else:
        await bot.send_message(chat_id, get_translation(user_id, "chose_action"), reply_markup=buttons)


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
    await send_keys_menu(callback_query.message, state)

    # Resetting the state
    await state.clear()


# Shields special characters in text for MarkdownV2.
def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)


# Handling of "get_keys" button pressing
@dp.callback_query(F.data == "get_keys")
async def send_keys(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id

    # Check for reaching the limit of keys per day
    if not check_user_limits(conn, user_id, status_limits):
        await send_limit_reached_message(callback_query, user_id)
        return

    # Checking the time of the last request
    last_request_time, user_status = get_last_request_time(conn, user_id)
    interval_minutes = status_limits[user_status]['interval_minutes']

    # Calculation of remaining time
    minutes, seconds = get_remaining_time(last_request_time, interval_minutes)
    if minutes > 0 or seconds > 0:
        wait_message = get_translation(user_id, "wait_time_message").format(minutes=minutes, sec=seconds)
        await send_wait_time_message(callback_query, user_id, wait_message)
        return

    # If the limit is not reached, continue processing
    response_text = f"{escape_markdown(get_translation(user_id, 'keys_generated_ok'))}\n\n"
    total_keys_in_request = 0

    for game in games:
        keys = get_oldest_keys(conn, game)
        if keys:
            total_keys_in_request += len(keys)
            response_text += f"*{escape_markdown(game)}*:\n"
            keys_to_delete = []
            for key in keys:
                response_text += f"`{escape_markdown(key[0])}`\n"
                keys_to_delete.append(key[0])
            response_text += "\n"
            delete_keys(conn, game, keys_to_delete)
        else:
            response_text += (f"{escape_markdown(get_translation(user_id, 'no_keys_for'))} *{escape_markdown(game)}* "
                              f"{escape_markdown(get_translation(user_id, 'no_keys_available'))} 😢\n\n")

    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=response_text.strip(),
        parse_mode="MarkdownV2"
    )

    if total_keys_in_request > 0:
        update_keys_generated(conn, user_id, total_keys_in_request)

    await callback_query.answer()
    await send_keys_menu(callback_query.message, state)


# Function for sending a message when the daily limit is reached
async def send_limit_reached_message(callback_query: types.CallbackQuery, user_id: int):
    image_path = os.path.join(os.path.dirname(__file__), "images", 'wait_image.jpg')
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=photo,
            caption=get_translation(user_id, "daily_limit_reached"),
            reply_markup=get_action_buttons(user_id)
        )
    else:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=get_translation(user_id, "daily_limit_reached"),
            reply_markup=get_action_buttons(user_id)
        )


# Function for sending a message to tell you to wait
async def send_wait_time_message(callback_query: types.CallbackQuery, user_id: int, wait_message: str):
    image_path = os.path.join(os.path.dirname(__file__), "images", 'wait_image.jpg')
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=photo,
            caption=wait_message,
            reply_markup=get_action_buttons(user_id)
        )
    else:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=wait_message,
            reply_markup=get_action_buttons(user_id)
        )


# Handler of other messages (including ban check)
@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

    # Reset daily keys if needed
    reset_daily_keys_if_needed(conn, user_id)

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
