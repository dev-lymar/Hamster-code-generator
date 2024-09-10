from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from utils.helpers import get_translation


async def get_back_to_main_menu_button(user_id):
    builder = InlineKeyboardBuilder()
    backmsg_button = InlineKeyboardButton(
        text=await get_translation(user_id, "back_key"),
        callback_data="main_menu_back"
    )
    builder.row(backmsg_button)

    return builder.as_markup()
