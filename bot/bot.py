import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from database import (create_database_connection, create_table_users, create_table_logs, add_user, update_user_language,
                      log_user_action, reset_daily_keys_if_needed)

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Connect to the database and create the tables if they do not exist
conn = create_database_connection()
create_table_users(conn)
create_table_logs(conn)

# Storing the selected language
user_language = {}


# Bot states
class Form(StatesGroup):
    choosing_language = State()


# Setting bot commands
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/change_lang", description="Change language / Сменить язык")
    ]
    await bot.set_my_commands(commands)


@dp.message(F.text == "/start")
async def send_welcome(message: types.Message, state: FSMContext):
    user = message.from_user
    user_id = user.id
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
    if language_code in ["ru", "uk"]:
        selected_language = "ru"
    else:
        selected_language = "en"

    # Save user in DB
    add_user(conn, chat_id, user_id, first_name, last_name, username, selected_language)

    # Set the selected language
    user_language[user_id] = selected_language

    await show_game_selection(message, selected_language)


# Game selection processing
async def show_game_selection(message: types.Message, selected_language: str):
    chat_id = message.chat.id
    image_path = os.path.join(os.path.dirname(__file__), "images", 'start_image.jpg')
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(chat_id, photo=photo)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Riding Extreme 3D", callback_data="riding_extreme_3d"),
         InlineKeyboardButton(text="Chain Cube 2048", callback_data="chain_cube_2048")],
        [InlineKeyboardButton(text="My Clone Army", callback_data="my_clone_army"),
         InlineKeyboardButton(text="Train Miner", callback_data="train_miner")],
        [InlineKeyboardButton(text="Merge Away", callback_data="merge_away"),
         InlineKeyboardButton(text="Twerk Race 3D", callback_data="twerk_race_3d")],
    ])

    await bot.send_message(
        chat_id,
        "Choose a game:" if selected_language == "en" else "Выберите игру:",
        reply_markup=buttons
    )


# Change language command
@dp.message(F.text == "/change_lang")
async def change_language(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Log user action
    log_user_action(conn, user_id, "/change_lang command used")

    language_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English", callback_data="en"),
         InlineKeyboardButton(text="Русский", callback_data="ru")],
    ])
    await message.answer("Выберите язык / Choose your language:", reply_markup=language_buttons)
    await state.set_state(Form.choosing_language)


# Language selection processing
@dp.callback_query(F.data.in_({"en", "ru"}))
async def set_language(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    selected_language = callback_query.data

    # Updating the language in the database
    update_user_language(conn, user_id, selected_language)

    # Updating the language in memory
    user_language[user_id] = selected_language

    # Deleting a language selection message
    await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)

    # Sending confirmation and proceeding to game selection
    await bot.send_message(
        chat_id,
        "You have selected English." if selected_language == "en" else "Вы выбрали русский язык."
    )

    # Log user action
    log_user_action(conn, user_id, f"Language changed to {selected_language}")

    # Switching to game selection
    await show_game_selection(callback_query.message, selected_language)


async def main():
    await dp.start_polling(bot)
    await set_commands(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
