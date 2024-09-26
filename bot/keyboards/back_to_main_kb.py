from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils import get_translation


async def get_back_to_main_menu_button(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text=await get_translation(user_id, "buttons", "back"), callback_data="main_menu_back")
    )

    back_markup = builder.as_markup()
    return back_markup
