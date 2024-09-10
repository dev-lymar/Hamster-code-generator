from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import REFERRAL_LINKS
from .back_to_main_kb import get_back_to_main_menu_button


async def referral_links_keyboard(user_id):
    main_menu_back = await get_back_to_main_menu_button(user_id)
    buttons = []
    for game_name, game_url in REFERRAL_LINKS.items():
        buttons.append(
            InlineKeyboardButton(text=game_name, url=game_url))
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    )
    keyboard_markup.inline_keyboard.append(main_menu_back.inline_keyboard[0])
    return keyboard_markup
