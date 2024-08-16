import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)


API_TOKEN = os.getenv('BOT_TOKEN')


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

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
    image_path = os.path.join(os.path.dirname(__file__), "images", 'welcome_image.jpg')

    language_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English", callback_data="lang_en"),
            InlineKeyboardButton(text="Русский", callback_data="lang_ru")]
    ])
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await message.answer_photo(photo=photo, caption="Выберите язык / Choose your language:", reply_markup=language_buttons)
    else:
        await message.answer("Выберите язык / Choose your language:", reply_markup=language_buttons)
    await state.set_state(Form.choosing_language)


# Change language button
@dp.message(F.text == "/change_lang")
async def change_language(message: types.Message, state: FSMContext):
    language_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English", callback_data="lang_en"),
            InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
    ])
    await message.answer("Выберите язык / Choose your language:", reply_markup=language_buttons)
    await state.set_state(Form.choosing_language)


# Language selection processing
@dp.callback_query(F.data.in_({"lang_en", "lang_ru"}))
async def set_language(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    image_path = os.path.join(os.path.dirname(__file__), "images", 'start_image.jpg')

    await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)

    if callback_query.data == "lang_en":
        user_language[user_id] = "en"
        await bot.send_message(user_id, "You have selected English.")
    else:
        user_language[user_id] = "ru"
        await bot.send_message(user_id, "Вы выбрали русский язык.")

    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await bot.send_photo(user_id, photo=photo)

    buttons_en = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Riding Extreme 3D", callback_data="riding_extreme_3d"),
            InlineKeyboardButton(text="Chain Cube 2048", callback_data="chain_cube_2048")],
        [InlineKeyboardButton(text="My Clone Army", callback_data="my_clone_army"),
           InlineKeyboardButton(text="Train Miner", callback_data="train_miner")],
        [InlineKeyboardButton(text="Merge Away", callback_data="merge_away"),
            InlineKeyboardButton(text="Twerk Race 3D", callback_data="twerk_race_3d")],
    ])

    buttons_ru = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Riding Extreme 3D", callback_data="riding_extreme_3d"),
            InlineKeyboardButton(text="Chain Cube", callback_data="chain_cube_2048")],
        [InlineKeyboardButton(text="My Clone Army", callback_data="my_clone_army"),
            InlineKeyboardButton(text="Train Miner", callback_data="train_miner")],
        [InlineKeyboardButton(text="Merge Away", callback_data="merge_away"),
            InlineKeyboardButton(text="Twerk Race 3D", callback_data="twerk_race_3d")],
    ])

    buttons = buttons_en if user_language[user_id] == "en" else buttons_ru
    await bot.send_message(user_id, "Choose a game:" if user_language[
                                                                              user_id] == "en" else "Выберите игру:",
                           reply_markup=buttons)

    await state.clear()


async def main():
    await dp.start_polling(bot)
    await set_commands(bot)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
