from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.helpers import get_translation
from .back_to_main_kb import get_back_to_main_menu_button


# Buttons that returns the button bar
async def get_action_buttons(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, key="get_safety_keys_key"), callback_data="get_safety_keys")],
        [InlineKeyboardButton(text=await get_translation(user_id, "get_keys_key"), callback_data="get_keys")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "ref_links_button_label"), callback_data="referral_links")],
        [InlineKeyboardButton(text=await get_translation(user_id, "settings_key"), callback_data="settings"),
         InlineKeyboardButton(
             text=await get_translation(user_id, "user_stats_button_label"), callback_data="user_stats")],
        [InlineKeyboardButton(text=await get_translation(user_id, "info_key"), callback_data="info")],
    ])


# Buttons that returns settings menu
async def get_settings_menu(session, user_id):
    main_menu_back = await get_back_to_main_menu_button(user_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, "choose_language_key"), callback_data="choose_language")],
        main_menu_back.inline_keyboard[0],
    ])


# Button instruction premium
async def instruction_prem_button(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await get_translation(user_id, "prem_support_button"), url="https://t.me/bot_support_hamster")],
        [InlineKeyboardButton(text=await get_translation(user_id, "back_key"), callback_data="main_menu_back")]
    ])


# Function that returns admin panel
async def get_admin_panel_keyboard(session, user_id):
    main_menu_back = await get_back_to_main_menu_button(user_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(user_id, "admin_keys_key"), callback_data="keys_admin_panel"),
         InlineKeyboardButton(
             text=await get_translation(user_id, "admin_users_key"), callback_data="users_admin_panel")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "send_message_to_user"), callback_data="send_message_to_user")],
        [InlineKeyboardButton(
            text=await get_translation(user_id, "admin_notifications_key"), callback_data="notifications_admin_panel")],
        main_menu_back.inline_keyboard[0]
    ])


# Button that returns main from info
async def get_main_in_admin(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(user_id, "back_key"), callback_data="back_to_admin_main")],
    ])


# Notification menu
async def notification_menu(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Send to yourself", callback_data="send_to_myself"),  # Add translation ‼️
         InlineKeyboardButton(text="📤 Send to all !", callback_data="send_all")],  # Add translation ‼️
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_admin_main")]  # Add translation ‼️
    ])


# Confirmation button
async def confirmation_button_notification(session, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤡 YES !", callback_data="confirm_send"),  # Add translation ‼️
         InlineKeyboardButton(text="🥱 No, not sending...", callback_data="back_to_admin_main")],  # Add translation ‼️
        [InlineKeyboardButton(text="🔙 Back", callback_data="notifications_admin_panel")]  # Add translation ‼️
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
