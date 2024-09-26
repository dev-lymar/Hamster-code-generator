import asyncio
from typing import Dict, List, Optional

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardMarkup, Message

from bot.bot_config import BOT_ID, GROUP_CHAT_ID, bot, logger
from bot.db_handler.db_service import (
    get_admin_chat_ids,
    get_keys_count_for_games,
    get_subscribed_users,
    get_user_details,
    get_users_list_admin_panel,
    log_user_action,
)
from bot.keyboards.admin_kb import (
    confirmation_button_notification,
    get_admin_panel_keyboard,
    get_detail_info_in_admin,
    get_main_admin,
    notification_menu,
)
from bot.keyboards.referral_links_kb import referral_links_keyboard
from bot.states.form import Form, FormSendToUser
from bot.utils import get_translation, load_image
from bot.utils.static_data import GAMES
from db.database import get_session

router = Router()


# Mapping between forwarded message IDs and user IDs
message_user_mapping: Dict[int, int] = {}


# Admin panel handler
async def handle_admin_command_handler(message: types.Message, user_id: int) -> None:
    admin_text: str = await get_translation(user_id, "admin", "panel_description")

    await bot.send_message(
        chat_id=message.chat.id,
        text=admin_text,
        reply_markup=await get_admin_panel_keyboard(user_id)
    )


# Get keys button admin panel
@router.callback_query(F.data == "keys_admin_panel")
async def keys_admin_panel_handler(callback: types.CallbackQuery) -> None:
    async with await get_session() as session:
        user_id: int = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id
        keys_count_message: str = await get_keys_count_for_games(session, GAMES)

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=keys_count_message,
            reply_markup=await get_main_admin(user_id)
        )


# Get users button admin panel
@router.callback_query(F.data == "users_admin_panel")
async def users_admin_panel_handler(callback: types.CallbackQuery) -> None:
    async with await get_session() as session:
        user_id: int = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id
        message_text: str = await get_users_list_admin_panel(session, GAMES)
        back_keyboard: InlineKeyboardMarkup = await get_main_admin(user_id)
        detail_info_keyboard: InlineKeyboardMarkup = await get_detail_info_in_admin(user_id)
        combined_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
            inline_keyboard=detail_info_keyboard.inline_keyboard + back_keyboard.inline_keyboard
        )

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text,
            reply_markup=combined_keyboard
        )


@router.callback_query(F.data == "detail_info_in_admin")
async def request_user_id_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="Please enter the user ID of the user whose information you wish to retrieve:"  # Add translation ‼️
    )

    await state.set_state(Form.user_id_entry)


# Get user detail button admin panel
@router.message(Form.user_id_entry)
async def user_detail_admin_panel(message: types.Message, state: FSMContext) -> None:
    user_detail_id: str = message.text.strip()

    async with await get_session() as session:
        user_id: int = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        keyboard: InlineKeyboardMarkup = await get_main_admin(user_id)

        try:
            user_detail_id: int = int(user_detail_id)
        except ValueError:
            await message.answer("<i><b>ID</b> must be an integer. Please do it again!</i>", reply_markup=keyboard)
            return

        try:
            user_details: str = await get_user_details(session, user_detail_id)
        except Exception as e:
            logger.error(f"Database error occurred: {e}")
            await message.answer(
                text="<i>Error occurred while fetching user details. Try again later.</i>",
                reply_markup=keyboard
            )
            return

        if "not_found" in user_details:
            await message.answer("<i>User with this <b>ID</b> not found!</i>", reply_markup=keyboard)
        else:
            await message.answer(user_details, reply_markup=keyboard)

    await state.clear()


# Back to main menu(for admin)
@router.callback_query(F.data == "back_to_admin_main")
async def back_to_admin_main_menu_handler(callback: types.CallbackQuery) -> None:
    user_id: int = (
        callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
    )
    admin_text: str = await get_translation(user_id, "admin", "panel_description")
    keyboard: InlineKeyboardMarkup = await get_admin_panel_keyboard(user_id)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=admin_text,
        reply_markup=keyboard
    )


@router.callback_query(F.data == "notifications_admin_panel")
async def notification_menu_handler(callback: types.CallbackQuery) -> None:
    keyboard: InlineKeyboardMarkup = await notification_menu()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="🚨 Watch out! The panel for sending notifications to users 📤",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('send_self_'))
async def send_notification_to_self_handler(callback: types.CallbackQuery) -> None:
    notif_key: str = callback.data.split('send_self_')[-1]

    async with await get_session() as session:
        user_id: int = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        await log_user_action(session, user_id, "Sent ad to themselves")

        notification_text: str = await get_translation(user_id, "notifications", notif_key)
        photo: Optional[FSInputFile] = await load_image("notification", specific_image=f"{notif_key}.png")
        keyboard: InlineKeyboardMarkup = await referral_links_keyboard(user_id)

        try:
            test_message = await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=photo,
                caption=notification_text,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send photo notification: {e}")
            error_text: str = f"Failed to send photo notification: {e}"
            test_message = await bot.send_message(
                chat_id=callback.message.chat.id,
                text=error_text
            )

        await asyncio.sleep(7)

        keyboard_after: InlineKeyboardMarkup = await notification_menu()

        if test_message:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=test_message.message_id
            )
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text="🚨 Watch out! The panel for sending notifications to users 📤",
                reply_markup=keyboard_after
            )
        else:
            logger.warning("Photo notification was not sent, so no message to delete.")


@router.callback_query(F.data.startswith('send_all_'))
async def confirm_send_all_notifications_handler(callback: types.CallbackQuery) -> None:
    notif_key: str = callback.data.split('send_all_')[-1]

    async with await get_session() as session:
        user_id: int = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        await log_user_action(session, user_id, "Confirmation send notification")

        keyboard: InlineKeyboardMarkup = await confirmation_button_notification(notif_key)

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="‼️ <i>Send a notification to <b>ALL</b> users ?</i> ‼️",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith('confirm_send_all_'))
async def confirm_send_all_handler(callback: types.CallbackQuery) -> None:
    notif_key: str = callback.data.split('confirm_send_all_')[-1]

    async with await get_session() as session:
        user_id: int = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        await log_user_action(session, user_id, "Started sending notifications to all users")

        # Getting a list of users for mailing
        users: List[types.User] = await get_subscribed_users(session)

        photo: Optional[FSInputFile] = await load_image("notification", specific_image=f"{notif_key}.png")

        for user in users:
            chat_id: int = user.chat_id
            first_name: str = user.first_name

            # Notification text
            notification_text: str = await get_translation(chat_id, "notifications", notif_key)
            personalized_text: str = f"{first_name}, {notification_text}"
            keyboard: InlineKeyboardMarkup = await referral_links_keyboard(chat_id)

            if photo:
                try:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=personalized_text,
                        reply_markup=keyboard
                    )
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.error(f"Failed to send photo notification to {chat_id}: {e}")
            else:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=personalized_text,
                        reply_markup=keyboard
                    )
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.error(f"Failed to send text notification to {chat_id}: {e}")

        keyboard_after: InlineKeyboardMarkup = await get_admin_panel_keyboard(user_id)

        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="📬 <i>The mailing has been successfully <b>completed</b>!!</i> 📭",  # Add translation ‼️
            reply_markup=keyboard_after
        )


# Button for requesting user ID
@router.callback_query(F.data == "send_message_to_user")
async def request_user_id_for_message_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        "Enter <b>ID</b> of the user to whom you want to send the message(or <i>'отмена'/'cancel'</i> to exit):"
    )
    await callback.answer()
    await state.set_state(FormSendToUser.user_id_entry)


# Getting user ID
@router.message(FormSendToUser.user_id_entry)
async def get_user_id_for_message(message: types.Message, state: FSMContext) -> None:
    user_input: str = message.text.strip()

    if user_input.strip().lower() in ['cancel', 'отмена']:
        await message.answer("Process <i>canceled.</i> Return to the admin panel.")
        await state.clear()

        user_id: int = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        await handle_admin_command_handler(message, user_id)
        return

    try:
        # Try to convert the entered ID into a number
        user_id: int = int(user_input)
        await state.update_data(user_id=user_id)  # Save the user ID to a state
        await message.answer("Enter <b>message text</b> (or <i>'отмена'/'cancel'</i> to exit)")
        await state.set_state(FormSendToUser.message_text_entry)  # Switch to text query
    except ValueError:
        await message.answer("<b>User ID <i>should be a number.</i> Try again.</b>")


# Receive message text
@router.message(FormSendToUser.message_text_entry)
async def get_message_text(message: types.Message, state: FSMContext) -> None:
    message_text: str = message.text.strip()

    if message_text in ['cancel', 'отмена']:
        await message.answer("Process <b>canceled.</b> Return to the admin panel.")
        await state.clear()

        user_id: int = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        await handle_admin_command_handler(message, user_id)
        return

    await state.update_data(message_text=message_text)  # Save the message text to a state
    await message.answer("Now send the <b>picture</b> (or enter <i>'нет'/'no'</i>, if no picture is required):")
    await state.set_state(FormSendToUser.image_entry)  # Go to picture request


# Receiving a picture and sending a message
@router.message(FormSendToUser.image_entry)
async def process_image_and_send_message(message: types.Message, state: FSMContext) -> None:
    data: Dict[str, str] = await state.get_data()
    user_id: int = int(data.get("user_id"))
    message_text: str = data.get("message_text")

    if message.text and message.text.strip().lower() in ['нет', 'no']:
        # If a picture is not required
        try:
            await bot.send_message(chat_id=user_id, text=message_text)
            await message.answer(f"Message <b>successfully sent</b> to user with ID <i>{user_id}</i>.")
        except Exception as e:
            await message.answer(f"Failed to send a message to user ID {user_id}. Error: {e}")
    elif message.photo:
        # If a picture is sent
        photo: str = message.photo[-1].file_id  # Take the last one (highest quality)
        try:
            await bot.send_photo(chat_id=user_id, photo=photo, caption=message_text)
            await message.answer(f"Message with picture was successfully sent to user with ID {user_id}.")
        except Exception as e:
            await message.answer(f"Failed to send a picture message to user with ID {user_id}. Error: {e}")
    else:
        await message.answer("Please send a picture or enter 'нет'/'no' if you don't need one.")

    # Resetting state
    await state.clear()

    current_user_id: int = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    await handle_admin_command_handler(message, current_user_id)

    # Back to the admin panel
    await handle_admin_command_handler(message, user_id)


# Forward a message to all admins and optionally to a group chat
async def forward_message_to_admins(message: Message) -> Dict[int, int]:
    admin_chat_ids: List[int] = await get_admin_chat_ids()
    tasks = []
    message_ids: Dict[int, int] = {}

    # Forward the message to all admins
    for admin_chat_id in admin_chat_ids:
        logger.info(f"Forwarding message from {message.chat.username} to admin {admin_chat_id}")
        try:
            task = bot.forward_message(
                chat_id=admin_chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to forward message to admin {admin_chat_id}: {e}")

    # Forward the message to the group chat if GROUP_CHAT_ID is defined
    if GROUP_CHAT_ID:
        logger.info(f"Forwarding message from {message.chat.username} to group {GROUP_CHAT_ID}")
        try:
            task = bot.forward_message(
                chat_id=GROUP_CHAT_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to forward message to group {GROUP_CHAT_ID}: {e}")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Save the message IDs to allow admins to reply
    for admin_chat_id, result in zip(admin_chat_ids + [GROUP_CHAT_ID], results):
        if isinstance(result, types.Message):
            message_ids[admin_chat_id] = result.message_id
            message_user_mapping[result.message_id] = message.from_user.id

    # Handle any exceptions that were raised during execution
    for result in results:
        if isinstance(result, Exception):
            error_message = (
                f"Failed to forward message from {message.chat.username} to group {GROUP_CHAT_ID} "
                f"due to error: {str(result)[:50]}"
            )
            logger.error(error_message)
            await send_error_to_admins(admin_chat_ids, error_message)

    return message_ids


# Send an error message to all admins
async def send_error_to_admins(admin_chat_ids: list[int], error_message: str) -> None:
    tasks = [
        bot.send_message(chat_id=admin_chat_id, text=error_message)
        for admin_chat_id in admin_chat_ids
    ]
    await asyncio.gather(*tasks)


def register_admin_handlers(dp) -> None:
    dp.include_router(router)
