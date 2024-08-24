from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_translation


# Function that returns the button bar
async def get_action_buttons(conn, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(conn, user_id, "get_keys_key"), callback_data="get_keys")],
        [InlineKeyboardButton(text=await get_translation(conn, user_id, "settings_key"), callback_data="settings")],
    ])


# Function that returns settings menu
async def get_settings_menu(conn, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(
            conn, user_id, "choose_language_key"), callback_data="choose_language")],
        [InlineKeyboardButton(text=await get_translation(conn, user_id, "back_key"), callback_data="back_to_main")],
    ])


# Creating a keyboard with language keys
def create_language_keyboard(translations, conn, user_id):
    language_buttons = []
    for lang_code, translation_data in translations.items():
        language_buttons.append(
            InlineKeyboardButton(text=translation_data["language_name"], callback_data=lang_code)
        )
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[language_buttons[i:i + 2] for i in range(0, len(language_buttons), 2)]
    )
    return keyboard_markup
