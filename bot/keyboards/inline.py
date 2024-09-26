from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils import get_translation
from bot.utils.referals import REFERRAL_LINKS

from .back_to_main_kb import get_back_to_main_menu_button


# Buttons that returns the button bar
async def get_action_buttons(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "referral_links"), callback_data="referral_links")
    )

    builder.row(
        InlineKeyboardButton(text="Binance Moonbix 🟠", url=REFERRAL_LINKS.get('Binance Moonbix 🟠')),
        InlineKeyboardButton(text="🥠 Hrum", url=REFERRAL_LINKS.get('🥠 Hrum')),
        InlineKeyboardButton(text="🪙 Bybit CoinSweeper", url=REFERRAL_LINKS.get('🪙 Bybit CoinSweeper')),
        InlineKeyboardButton(text="🏠 CITY Holder", url=REFERRAL_LINKS.get('🏠 CITY Holder')),
        width=2
    )
    builder.row(InlineKeyboardButton(text="Cats 🐈‍⬛", url=REFERRAL_LINKS.get('Cats 🐈‍⬛')))
    builder.row(InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "get_regular_keys"), callback_data="keys_regular")
    )
    builder.row(InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "settings"), callback_data="settings_menu"
        ),
        InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "user_stats"), callback_data="user_stats")
    )

    builder.row(
        InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "info"), callback_data="user_info"
        )
    )
    menu_markup = builder.as_markup()
    return menu_markup


# Buttons that returns settings menu
async def get_settings_menu(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    main_menu_back = await get_back_to_main_menu_button(user_id)

    builder.row(InlineKeyboardButton(
            text=await get_translation(user_id, "common", "choose_language"), callback_data="settings_choose_language"),
    )
    builder.row(*main_menu_back.inline_keyboard[0])

    settings_markup = builder.as_markup()
    return settings_markup


# Creating a keyboard with language keys
def create_language_keyboard(available_languages: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for lang_code, language_name in available_languages.items():
        builder.button(
            text=language_name,
            callback_data=lang_code
        )
    builder.adjust(2)

    return builder.as_markup()
