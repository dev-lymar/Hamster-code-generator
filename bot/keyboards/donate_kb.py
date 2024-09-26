from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.back_to_main_kb import get_back_to_main_menu_button
from bot.utils import get_translation


async def get_payment_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    payment_button_text = await get_translation(user_id, "buttons", "pay")
    cancel_button_text = await get_translation(user_id, "buttons", "cancel_donation")

    builder.row(
        types.InlineKeyboardButton(text=payment_button_text, pay=True))
    builder.row(
        types.InlineKeyboardButton(text=cancel_button_text, callback_data="cancel_payment"))

    payment_kb_markup = builder.as_markup()
    return payment_kb_markup


async def get_donation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    main_menu_back = await get_back_to_main_menu_button(user_id)
    amount_button = await get_translation(user_id, "buttons", "custom_donate_amount")
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(text="1 ⭐️", callback_data="donate_1"),
        types.InlineKeyboardButton(text="10 🌟", callback_data="donate_10"),
        types.InlineKeyboardButton(text="50 ✨", callback_data="donate_50"),
    )
    builder.row(types.InlineKeyboardButton(text=amount_button, callback_data="donate_custom"))

    # Add a button to the main menu
    builder.row(*main_menu_back.inline_keyboard[0])

    donation_markup = builder.as_markup()
    return donation_markup


async def get_cancel_donation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    cancel_button_text = await get_translation(user_id, "buttons", "cancel_donation")

    builder.button(text=cancel_button_text, callback_data="cancel_custom_donation")

    cancel_donation_markup = builder.as_markup()
    return cancel_donation_markup
