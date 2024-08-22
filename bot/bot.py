import logging.handlers
import os
import json
import random
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

# Set up logging configuration
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, 'game_promo.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
    ]
)

logger = logging.getLogger(__name__)

API_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = int(API_TOKEN.split(':')[0])
games = [
    'Bike Ride 3D',
    'Chain Cube 2048',
    'My Clone Army',
    'Train Miner',
    'Merge Away',
    'Twerk Race 3D',
    'Polysphere'
]
status_limits = {
    'free': {'daily_limit': 5, 'interval_minutes': 30},
    'friend': {'daily_limit': 10, 'interval_minutes': 20},
    'premium': {'daily_limit': 25, 'interval_minutes': 10}
}
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


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
async def get_translation(conn, user_id, key):
    user_lang = await get_user_language(conn, user_id)
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
async def get_action_buttons(conn, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(conn, user_id, "get_keys"), callback_data="get_keys")],
    ])


# Command handler /start
@dp.message(F.text == "/start")
async def send_welcome(message: types.Message, state: FSMContext):
    conn = await create_database_connection()
    try:
        user = message.from_user
        user_id = user.id if user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id
        first_name = user.first_name
        last_name = user.last_name
        username = user.username
        language_code = user.language_code

        # Log user action
        await log_user_action(conn, user_id, "/start command used")

        # Language selection based on the user's language
        if language_code in translations:
            selected_language = language_code
        elif language_code in ["ru", "uk"]:
            selected_language = "ru"
        else:
            selected_language = "en"

        # Save user in DB
        await add_user(conn, chat_id, user_id, first_name, last_name, username, selected_language)

        # Ban check
        if await is_user_banned(conn, user_id):
            await handle_banned_user(message)
            return

        # Receiving the transfer
        translation = await get_translation(conn, user_id, "welcome_message")

        # Forming the greeting text
        welcome_text = translation.format(first_name=first_name)

        # Check if the directory exists and contains files
        image_dir = os.path.join(os.path.dirname(__file__), "images", "welcome")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id,
                    photo=photo,
                    caption=welcome_text,
                    reply_markup=await get_action_buttons(conn, user_id)
                )
                return

        # If no valid image is found or the directory doesn't exist, send a message without photo
        await bot.send_message(chat_id, text=welcome_text, reply_markup=await get_action_buttons(conn, user_id))
    finally:
        await conn.close()


# Function to send keys menu after generating keys
async def send_keys_menu(message: types.Message, state: FSMContext):
    conn = await create_database_connection()
    try:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        # Use the function to get the buttons
        buttons = await get_action_buttons(conn, user_id)

        # Check if the directory exists and contains files
        image_dir = os.path.join(os.path.dirname(__file__), "images", "key_generated")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)
                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id,
                    photo=photo,
                    caption=await get_translation(conn, user_id, "chose_action"),
                    reply_markup=buttons,
                    parse_mode="HTML",
                )
                return
        await bot.send_message(
            chat_id,
            await get_translation(conn, user_id, "chose_action"),
            parse_mode="HTML",
            reply_markup=buttons
        )
    finally:
        await conn.close()


# Change language command
@dp.message(F.text == "/change_lang")
async def change_language(message: types.Message, state: FSMContext):
    conn = await create_database_connection()
    try:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

        # Ban check
        if await is_user_banned(conn, user_id):
            await handle_banned_user(message)
            return

        # Log user action
        await log_user_action(conn, user_id, "/change_lang command used")

        # Check for a ban before performing any actions
        if await is_user_banned(conn, user_id):
            await handle_banned_user(message)
            return

        language_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="English", callback_data="en"),
             InlineKeyboardButton(text="Русский", callback_data="ru")],
        ])

        # Send the message and store its ID in the state
        lang_message = await message.answer(
            await get_translation(conn, user_id, "choose_language"), reply_markup=language_buttons
        )

        # Save the IDs of the language message and user's command message
        await state.update_data(lang_message_id=lang_message.message_id, user_command_message_id=message.message_id)

        await state.set_state(Form.choosing_language)
    finally:
        await conn.close()


# Language selection processing
@dp.callback_query(F.data.in_({"en", "ru"}))
async def set_language(callback_query: types.CallbackQuery, state: FSMContext):
    conn = await create_database_connection()
    try:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id

        # Ban check
        if await is_user_banned(conn, user_id):
            await handle_banned_user(callback_query.message)
            return

        selected_language = callback_query.data

        # Updating the language in the database
        await update_user_language(conn, user_id, selected_language)

        # Forcibly query the language from the database again
        new_language = await get_user_language(conn, user_id)
        logging.info(f"Language after update for user {user_id}: {new_language}")

        # Log user action
        await log_user_action(conn, user_id, f"Language changed to {selected_language}")

        # Deleting the language selection message and the user's command message
        data = await state.get_data()
        if "lang_message_id" in data:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=data["lang_message_id"])
        if "user_command_message_id" in data:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=data["user_command_message_id"])

        # Sending confirmation and proceeding to game selection
        await bot.send_message(
            callback_query.message.chat.id,
            await get_translation(conn, user_id, "language_selected")
        )

        # Displaying the updated action menu
        await send_keys_menu(callback_query.message, state)

        # Resetting the state
        await state.clear()
    finally:
        await conn.close()


# Shields special characters in text for MarkdownV2.
def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)


# Handling of "get_keys" button pressing
@dp.callback_query(F.data == "get_keys")
async def send_keys(callback_query: types.CallbackQuery, state: FSMContext):
    conn = await create_database_connection()
    try:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id

        # Ban check
        if await is_user_banned(conn, user_id):
            await handle_banned_user(callback_query.message)
            return

        # Check for reaching the limit of keys per day
        if not await check_user_limits(conn, user_id, status_limits):
            await send_limit_reached_message(callback_query, user_id)
            return

        # Checking the time of the last request
        last_request_time, user_status = await get_last_request_time(conn, user_id)
        interval_minutes = status_limits[user_status]['interval_minutes']

        # Calculation of remaining time
        minutes, seconds = get_remaining_time(last_request_time, interval_minutes)
        if minutes > 0 or seconds > 0:
            translation = await get_translation(conn, user_id, "wait_time_message")
            wait_message = translation.format(minutes=minutes, sec=seconds)
            await send_wait_time_message(callback_query, user_id, wait_message)
            return

        # If the limit is not reached, continue processing
        response_text = f"{escape_markdown(await get_translation(conn, user_id, 'keys_generated_ok'))}\n\n"
        total_keys_in_request = 0

        for game in games:
            keys = await get_oldest_keys(conn, game)
            if keys:
                total_keys_in_request += len(keys)
                response_text += f"*{escape_markdown(game)}*:\n"
                keys_to_delete = []
                for key in keys:
                    response_text += f"`{escape_markdown(key['promo_code'])}`\n"
                    keys_to_delete.append(key['promo_code'])
                response_text += "\n"
                await delete_keys(conn, game, keys_to_delete)
            else:
                response_text += (
                    f"{escape_markdown(await get_translation(conn, user_id, 'no_keys_for'))} *{escape_markdown(game)}* "
                    f"{escape_markdown(await get_translation(conn, user_id, 'no_keys_available'))} 😢\n\n")

        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=response_text.strip(),
            parse_mode="MarkdownV2"
        )

        if total_keys_in_request > 0:
            await update_keys_generated(conn, user_id, total_keys_in_request)

        await callback_query.answer()
        await send_keys_menu(callback_query.message, state)
    finally:
        await conn.close()


# Function for sending a message when the daily limit is reached
async def send_limit_reached_message(callback_query: types.CallbackQuery, user_id: int):
    conn = await create_database_connection()
    try:
        image_dir = os.path.join(os.path.dirname(__file__), "images", "wait")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id=callback_query.message.chat.id,
                    photo=photo,
                    caption=await get_translation(conn, user_id, "daily_limit_reached"),
                    reply_markup=await get_action_buttons(conn, user_id)
                )
                return
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=await get_translation(conn, user_id, "daily_limit_reached"),
            reply_markup=await get_action_buttons(conn, user_id)
        )
    finally:
        await conn.close()


# Function for sending a message to tell you to wait
async def send_wait_time_message(callback_query: types.CallbackQuery, user_id: int, wait_message: str):
    conn = await create_database_connection()
    try:
        image_dir = os.path.join(os.path.dirname(__file__), "images", "welcome")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id=callback_query.message.chat.id,
                    photo=photo,
                    caption=wait_message,
                    reply_markup=await get_action_buttons(conn, user_id)
                )
                return
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=wait_message,
            reply_markup=await get_action_buttons(conn, user_id)
        )
    finally:
        await conn.close()


# Handler of other messages (including ban check)
@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    conn = await create_database_connection()
    try:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

        # Ban check
        if await is_user_banned(conn, user_id):
            await handle_banned_user(message)
            return

        # Reset daily keys if needed
        await reset_daily_keys_if_needed(conn, user_id)

        # Ban check
        if await is_user_banned(conn, user_id):
            await handle_banned_user(message)
            return

        # Logging a user's message
        await log_user_action(conn, user_id, f"User message: {message.text}")

        # Response to user post
        await message.answer(await get_translation(conn, user_id, "default_response"))
    finally:
        await conn.close()


# Handling banned users
async def handle_banned_user(message: types.Message):
    conn = await create_database_connection()
    try:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        # User action logging
        await log_user_action(conn, user_id, "Attempted interaction while banned")

        # Sending a ban notification
        image_dir = os.path.join(os.path.dirname(__file__), "images", "welcome")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id,
                    photo=photo,
                    caption=await get_translation(conn, user_id, "ban_message")
                )
                return
        await bot.send_message(chat_id, await get_translation(conn, user_id, "ban_message"))
    finally:
        await conn.close()


async def main():
    conn = await create_database_connection()
    try:
        await create_table_users(conn)
        await create_table_logs(conn)
    finally:
        await conn.close()

    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
