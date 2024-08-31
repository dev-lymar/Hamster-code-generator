from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_translation


# Buttons that returns the button bar
async def get_action_buttons(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(user_id, "get_keys_key"), callback_data="get_keys")],
        [InlineKeyboardButton(text=await get_translation(user_id, "settings_key"), callback_data="settings"),
         InlineKeyboardButton(text=await get_translation(user_id, "info_key"), callback_data="info")],
    ])


# Buttons that returns settings menu
async def get_settings_menu(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(
            user_id, "choose_language_key"), callback_data="choose_language")],
        [InlineKeyboardButton(text=await get_translation(user_id, "back_key"), callback_data="back_to_main")],
    ])


# Button that returns main from info
async def get_main_from_info(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(user_id, "back_key"), callback_data="back_to_main")],
    ])


# Function that returns admin panel
async def get_admin_panel_keyboard(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(user_id, "admin_keys_key"), callback_data="keys_admin_panel"),
         InlineKeyboardButton(
             text=await get_translation(user_id, "admin_users_key"), callback_data="users_admin_panel")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "admin_notifications_key"), callback_data="notifications_admin_panel")],
        [InlineKeyboardButton(text="Стать обычным человеком...", callback_data="back_to_main")]
    ])


# Button that returns main from info
async def get_main_in_admin(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(user_id, "back_key"), callback_data="back_to_admin_main")],
    ])


# Notification menu
async def notification_menu(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить себе", callback_data="send_to_myself"),
         InlineKeyboardButton(text="Отправить всем !", callback_data="send_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_main")]
    ])


# Confirmation button
async def confirmation_button_notification(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да !", callback_data="confirm_send"),
         InlineKeyboardButton(text="Нет, не отправлять...", callback_data="cancel_send")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="notifications_admin_panel")]
    ])


# Button that returns main from info
async def get_detail_info_in_admin(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, "admin_detail_info_key"), callback_data="detail_info_in_admin")],
    ])


# Creating a keyboard with language keys
def create_language_keyboard(translations):
    language_buttons = []
    for lang_code, translation_data in translations.items():
        language_buttons.append(
            InlineKeyboardButton(text=translation_data["language_name"], callback_data=lang_code)
        )
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[language_buttons[i:i + 2] for i in range(0, len(language_buttons), 2)]
    )
    return keyboard_markup
