from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils import get_translation

from .back_to_main_kb import get_back_to_main_menu_button


# Buttons that returns the button bar
async def get_action_buttons(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "referral_links"), callback_data="referral_links")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "get_regular_keys"), callback_data="keys_regular")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "settings"), callback_data="settings_menu"),
         InlineKeyboardButton(
             text=await get_translation(user_id, "buttons", "user_stats"), callback_data="user_stats")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "info"), callback_data="user_info")],
    ])


# Buttons that returns settings menu
async def get_settings_menu(session, user_id):
    main_menu_back = await get_back_to_main_menu_button(user_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(
                user_id, "common", "choose_language"), callback_data="settings_choose_language")],
        main_menu_back.inline_keyboard[0],
    ])


# Function that returns admin panel
async def get_admin_panel_keyboard(session, user_id):
    main_menu_back = await get_back_to_main_menu_button(user_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, "admin", "manage_keys"), callback_data="keys_admin_panel"),
         InlineKeyboardButton(
             text=await get_translation(user_id, "admin", "manage_users"), callback_data="users_admin_panel")],
        [InlineKeyboardButton(
            text=await get_translation(
                user_id, "admin", "manage_notifications"), callback_data="notifications_admin_panel")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "admin", "message_user"), callback_data="send_message_to_user")],
        main_menu_back.inline_keyboard[0]
    ])


# Button that returns main from info
async def get_main_in_admin(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, "buttons", "back"), callback_data="back_to_admin_main")],
    ])


# Notification menu
async def notification_menu(session, user_id):
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
    }

    inline_keyboard = []

    # Generate buttons for each notification
    for key, name in notifications.items():
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📩 {name} себе",
                callback_data=f"send_self_{key}"
            ),
            InlineKeyboardButton(
                text=f"📤 {name} всем",
                callback_data=f"send_all_{key}"
            )
        ])

    inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# Confirmation button
async def confirmation_button_notification(session, user_id, notif_key):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤡 YES !", callback_data=f"confirm_send_all_{notif_key}"),  # Add translation ‼️
         InlineKeyboardButton(text="🥱 No, not sending...", callback_data="back_to_admin_main")],  # Add translation ‼️
        [InlineKeyboardButton(text="🔙 Back", callback_data="notifications_admin_panel")]  # Add translation ‼️
    ])


# Button that returns main from info
async def get_detail_info_in_admin(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, "admin", "view_details"), callback_data="detail_info_in_admin")],
    ])


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
