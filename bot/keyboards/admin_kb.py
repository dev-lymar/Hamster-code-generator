from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils import get_translation

from .back_to_main_kb import get_back_to_main_menu_button


# Function that returns admin panel
async def get_admin_panel_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    main_menu_back = await get_back_to_main_menu_button(user_id)

    builder.row(InlineKeyboardButton(
        text=await get_translation(user_id, "admin", "manage_keys"), callback_data="keys_admin_panel"),
        InlineKeyboardButton(
            text=await get_translation(user_id, "admin", "manage_users"), callback_data="users_admin_panel")
    )
    builder.row(InlineKeyboardButton(
        text=await get_translation(user_id, "admin", "manage_notifications"), callback_data="notifications_admin_panel")
    )
    builder.row(InlineKeyboardButton(
        text=await get_translation(user_id, "admin", "message_user"), callback_data="send_message_to_user")
    )

    builder.row(*main_menu_back.inline_keyboard[0])

    admin_markup = builder.as_markup()
    return admin_markup


# Button that returns main from info
async def get_main_admin(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=await get_translation(user_id, "buttons", "back"), callback_data="back_to_admin_main")
    )

    admin_main_markup = builder.as_markup()
    return admin_main_markup


# Notification menu
async def notification_menu() -> InlineKeyboardMarkup:
    notifications = {
        "notification": "Great news!",
        "newgame": "New game!",
        "tapswap": "TapSwap",
        "catizen": "Catizen",
        "cityholder": "City Holder",
        "cexiopower": "CEX.IO Power Tap",
        "cats": "Cats",
        "dotcoin": "DotCoin",
        "muskempire": "Musk Empire",
        "hrum": "HRUM",
        "frogtrader": "Frog Trader",
        "notpixel": "Not Pixel",
        "major": "Major",
        "blum": "Blum",
        "binancemoon": "Binance Moonbix",
        "tonstation": "Ton Station",
        "bybitcoin": "Bybit Coin",
    }

    builder = InlineKeyboardBuilder()

    # Generate buttons for each notification
    for key, name in notifications.items():
        builder.row(
            InlineKeyboardButton(text=f"📩 {name} myself", callback_data=f"send_self_{key}"),
            InlineKeyboardButton(text=f"📤 {name} all", callback_data=f"send_all_{key}")
        )

    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_to_admin_main"))

    notifications_markup = builder.as_markup()
    return notifications_markup


# Confirmation button
async def confirmation_button_notification(notif_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="Yes confirm!", callback_data=f"confirm_send_all_{notif_key}"),
        InlineKeyboardButton(text="No, not sending...", callback_data="back_to_admin_main")
    )
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="notifications_admin_panel"))

    confirmation_markup = builder.as_markup()
    return confirmation_markup


# Button that returns main from info
async def get_detail_info_in_admin(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text=await get_translation(user_id, "admin", "view_details"), callback_data="detail_info_in_admin"))

    detail_markup = builder.as_markup()
    return detail_markup
