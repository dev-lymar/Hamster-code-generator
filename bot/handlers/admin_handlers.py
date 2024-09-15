import asyncio
import logging
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message
from config import bot, BOT_ID, GAMES, GROUP_CHAT_ID
from database.database import (get_session, log_user_action, get_user_status_info, get_admin_chat_ids,
                               get_keys_count_for_games, get_users_list_admin_panel, get_user_details,
                               get_subscribed_users, get_user_role_and_ban_info)
from keyboards.inline import (get_action_buttons, get_admin_panel_keyboard, get_main_in_admin, get_detail_info_in_admin,
                              notification_menu, confirmation_button_notification)
from utils import get_translation
from states.form import Form, FormSendToUser
from utils import load_image

router = Router()


# Mapping between forwarded message IDs and user IDs
message_user_mapping = {}


# Admin panel handler
async def handle_admin_command_handler(session, message, user_id):
    admin_text = await get_translation(user_id, "admin", "panel_description")

    await bot.send_message(
        chat_id=message.chat.id,
        text=admin_text,
        reply_markup=await get_admin_panel_keyboard(session, user_id)
    )


# Get keys button admin panel
@router.callback_query(F.data == "keys_admin_panel")
async def keys_admin_panel_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        
        user_id = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id
        keys_count_message = await get_keys_count_for_games(session, GAMES)
        
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=keys_count_message,
            reply_markup=await get_main_in_admin(session, user_id)
        )


# Get users button admin panel
@router.callback_query(F.data == "users_admin_panel")
async def users_admin_panel_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id

        message_text = await get_users_list_admin_panel(session, GAMES)

        back_keyboard = await get_main_in_admin(session, user_id)
        detail_info_keyboard = await get_detail_info_in_admin(session, user_id)
        combined_keyboard = InlineKeyboardMarkup(
            inline_keyboard=detail_info_keyboard.inline_keyboard + back_keyboard.inline_keyboard
        )

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text,
            reply_markup=combined_keyboard
        )


@router.callback_query(F.data == "detail_info_in_admin")
async def request_user_id_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text="Please enter the user ID of the user whose information you wish to retrieve:"  # Add translation ‼️
    )

    await state.set_state(Form.user_id_entry)


# Get user detail button admin panel
@router.message(Form.user_id_entry)
async def user_detail_admin_panel(message: types.Message, state: FSMContext):
    user_detail_id = message.text.strip()

    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        keyboard = await get_main_in_admin(session, user_id)

        try:
            user_detail_id = int(user_detail_id)
        except ValueError:
            text = "<i><b>ID</b> must be an integer. Please do it again!</i>"  # Add translation ‼️
            await message.answer(text, reply_markup=keyboard)
            return

        try:
            user_details = await get_user_details(session, user_detail_id)
        except Exception as e:
            logging.error(f"Database error occurred: {e}")
            await message.answer(
                text="<i>Error occurred while fetching user details. Try again later.</i>",  # Add translation ‼️
                reply_markup=keyboard
            )
            return

        if "not_found" in user_details:
            text = "<i>User with this <b>ID</b> not found!</i>"  # Add translation ‼️
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(user_details, reply_markup=keyboard)

    await state.clear()


# Back to main menu(for admin)
@router.callback_query(F.data == "back_to_admin_main")
async def back_to_admin_main_menu_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        admin_text = await get_translation(user_id, "admin", "panel_description")
        keyboard = await get_admin_panel_keyboard(session, user_id)

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=admin_text,
            reply_markup=keyboard
        )


@router.callback_query(F.data == "notifications_admin_panel")
async def notification_menu_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        keyboard = await notification_menu(session, user_id)

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="🚨 Watch out! The panel for sending notifications to users 📤",  # Add translation ‼️
            reply_markup=keyboard
        )


@router.callback_query(F.data == "notifications_send_all")
async def confirm_send_all_notifications_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        await log_user_action(session, user_id, "Confirmation send notification")

        keyboard = await confirmation_button_notification(session, user_id)

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="‼️ <i>Send a notification to <b>ALL</b> users ?</i> ‼️",  # Add translation ‼️
            reply_markup=keyboard
        )


@router.callback_query(F.data == "notifications_send_self")
async def send_notification_to_myself_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        await log_user_action(session, user_id, "Sent ad to themselves")

        notification_text = await get_translation(user_id, "notifications", "second_notification")
        photo = await load_image("notification", specific_image="notificate-Bouncemasters.png")
        keyboard = await get_action_buttons(session, user_id)

        if photo:
            try:
                test_message = await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=photo,
                    caption=notification_text,
                    reply_markup=keyboard
                )
            except Exception as e:
                logging.error(f"Failed to send photo notification: {e}")
                error_text = f"Failed to send photo notification: {e}"
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=error_text
                )

        await asyncio.sleep(7)

        keyboard_after = await notification_menu(session, user_id)

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=test_message.message_id
        )
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="🚨 Watch out! The panel for sending notifications to users 📤",
            reply_markup=keyboard_after
        )


@router.callback_query(F.data == "notifications_confirm_send")
async def confirm_send_all_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        await log_user_action(session, user_id, "Started sending notifications to all users")

        # Getting a list of users for mailing
        users = await get_subscribed_users(session)

        photo = await load_image("notification", specific_image="notificate-Bouncemasters.png")

        for user in users:
            chat_id = user.chat_id
            first_name = user.first_name

            # Notification text
            notification_text = await get_translation(chat_id, "notifications", "second_notification")
            personalized_text = f"{first_name}, {notification_text}"
            keyboard = await get_action_buttons(session, chat_id)

            if photo:
                try:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=personalized_text,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logging.error(f"Failed to send photo notification to {chat_id}: {e}")
            else:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=personalized_text,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logging.error(f"Failed to send text notification to {chat_id}: {e}")

        keyboard_after = await get_admin_panel_keyboard(session, user_id)

        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="📬 <i>The mailing has been successfully <b>completed</b>!!</i> 📭",  # Add translation ‼️
            reply_markup=keyboard_after
        )


# Button for requesting user ID
@router.callback_query(F.data == "send_message_to_user")
async def request_user_id_for_message_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Enter <b>ID</b> of the user to whom you want to send the message(or <i>'отмена'/'cancel'</i> to exit):"
    )
    await callback.answer()
    await state.set_state(FormSendToUser.user_id_entry)


# Getting user ID
@router.message(FormSendToUser.user_id_entry)
async def get_user_id_for_message(message: types.Message, state: FSMContext):
    user_input = message.text.strip()

    if user_input.strip().lower() in ['cancel', 'отмена']:
        await message.answer("Process <i>canceled.</i> Return to the admin panel.")
        await state.clear()

        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        async with await get_session() as session:
            await handle_admin_command_handler(session, message, user_id)
        return

    try:
        # Try to convert the entered ID into a number
        user_id = int(user_input)
        await state.update_data(user_id=user_id)  # Save the user ID to a state
        await message.answer("Enter <b>message text</b> (or <i>'отмена'/'cancel'</i> to exit)")
        await state.set_state(FormSendToUser.message_text_entry)  # Switch to text query
    except ValueError:
        await message.answer("<b>User ID <i>should be a number.</i> Try again.</b>")


# Receive message text
@router.message(FormSendToUser.message_text_entry)
async def get_message_text(message: types.Message, state: FSMContext):
    message_text = message.text.strip()

    if message_text in ['cancel', 'отмена']:
        await message.answer("Process <b>canceled.</b> Return to the admin panel.")
        await state.clear()

        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        async with await get_session() as session:
            await handle_admin_command_handler(session, message, user_id)
        return

    await state.update_data(message_text=message_text)  # Save the message text to a state
    await message.answer("Now send the <b>picture</b> (or enter <i>'нет'/'no'</i>, if no picture is required):")
    await state.set_state(FormSendToUser.image_entry)  # Go to picture request


# Receiving a picture and sending a message
@router.message(FormSendToUser.image_entry)
async def process_image_and_send_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    message_text = data.get("message_text")

    if message.text and message.text.strip().lower() in ['нет', 'no']:
        # If a picture is not required
        try:
            await bot.send_message(chat_id=user_id, text=message_text)
            await message.answer(f"Message <b>successfully sent</b> to user with ID <i>{user_id}</i>.")
        except Exception as e:
            await message.answer(f"Failed to send a message to user ID {user_id}. Error: {e}")
    elif message.photo:
        # If a picture is sent
        photo = message.photo[-1].file_id  # Take the last one (highest quality)
        try:
            await bot.send_photo(chat_id=user_id, photo=photo, caption=message_text)
            await message.answer(f"Message with picture was successfully sent to user with ID {user_id}.")
        except Exception as e:
            await message.answer(f"Failed to send a picture message to user with ID {user_id}. Error: {e}")
    else:
        await message.answer("Please send a picture or enter 'нет'/'no' if you don't need one.")

    # Resetting state
    await state.clear()

    async with await get_session() as session:
        current_user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

        await handle_admin_command_handler(session, message, current_user_id)

    # Back to the admin panel
    await handle_admin_command_handler(message)


# Forward a message to all admins and optionally to a group chat
async def forward_message_to_admins(message: Message):
    admin_chat_ids = await get_admin_chat_ids()
    tasks = []
    message_ids = {}

    # Forward the message to all admins
    for admin_chat_id in admin_chat_ids:
        logging.info(f"Forwarding message from {message.chat.username} to admin {admin_chat_id}")
        try:
            task = bot.forward_message(
                chat_id=admin_chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            tasks.append(task)
        except Exception as e:
            logging.error(f"Failed to forward message to admin {admin_chat_id}: {e}")

    # Forward the message to the group chat if GROUP_CHAT_ID is defined
    if GROUP_CHAT_ID:
        logging.info(f"Forwarding message from {message.chat.username} to group {GROUP_CHAT_ID}")
        try:
            task = bot.forward_message(
                chat_id=GROUP_CHAT_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            tasks.append(task)
        except Exception as e:
            logging.error(f"Failed to forward message to group {GROUP_CHAT_ID}: {e}")

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
            logging.error(error_message)
            await send_error_to_admins(admin_chat_ids, error_message)

    return message_ids


# Send an error message to all admins
async def send_error_to_admins(admin_chat_ids: list[int], error_message: str) -> None:
    tasks = [
        bot.send_message(chat_id=admin_chat_id, text=error_message)
        for admin_chat_id in admin_chat_ids
    ]
    await asyncio.gather(*tasks)


def register_admin_handlers(dp):
    dp.include_router(router)