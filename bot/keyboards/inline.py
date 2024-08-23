from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_translation


# Function that returns the button bar
async def get_action_buttons(conn, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(conn, user_id, "get_keys"), callback_data="get_keys")],
    ])
