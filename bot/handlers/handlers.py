import asyncio
import os
import random
import logging
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message, InlineKeyboardMarkup
from datetime import datetime, timezone
from config import bot, dp, BOT_ID, games, status_limits, set_commands, GROUP_CHAT_ID
from database.database import (get_session, get_or_create_user, update_user_language, log_user_action,
                               reset_daily_keys_if_needed, get_user_language, get_oldest_keys, update_keys_generated,
                               delete_keys, get_user_status_info, is_admin, get_admin_chat_ids,
                               get_keys_count_for_games, get_users_list_admin_panel, get_user_details)
from keyboards.inline import (get_action_buttons, get_settings_menu, create_language_keyboard,
                              get_main_from_info, get_admin_panel_keyboard, get_main_in_admin, get_detail_info_in_admin,
                              notification_menu, confirmation_button_notification)
from utils.helpers import load_translations, get_translation, escape_markdown, get_remaining_time
from states.form import Form

# Mapping between forwarded message IDs and user IDs
message_user_mapping = {}

translations = load_translations()


# Command handler /start
@dp.message(F.text == "/start")
async def send_welcome(message: types.Message, state: FSMContext):
    async with await get_session() as session:
        user = message.from_user
        user_id = user.id if user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        user_data = {
            'chat_id': chat_id,
            'user_id': user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'language_code': user.language_code
        }

        # Log user action
        await log_user_action(session, user_id, "/start command used")

        # Get or create user in DB
        user_record = await get_or_create_user(session, chat_id, user_data)

        if user_record is None:
            await message.answer("Error creating user.")
            return

        # Update user language if necessary
        if user_record.language_code != user_data['language_code']:
            await update_user_language(session, user_id, user_data['language_code'])

        # Receiving the translation
        translation = await get_translation(user_id, "welcome_message")
        welcome_text = translation.format(first_name=user.first_name)

        # Sending welcome message with photo
        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "welcome")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)
                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=welcome_text,
                    reply_markup=await get_action_buttons(session, user_id),
                    parse_mode="HTML"
                )
                return

        # Sending welcome message without photo
        await bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            reply_markup=await get_action_buttons(session, user_id),
            parse_mode="HTML"
        )


# Function to send keys menu after generating keys
async def send_keys_menu(message: types.Message, state: FSMContext):
    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        # Use the function to get the buttons
        buttons = await get_action_buttons(session, user_id)

        # Check if the directory exists and contains files
        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "key_generated")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)
                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id,
                    photo=photo,
                    caption=await get_translation(user_id, "chose_action"),
                    reply_markup=buttons,
                    parse_mode="HTML",
                )
                return
        await bot.send_message(
            chat_id,
            await get_translation(user_id, "chose_action"),
            parse_mode="HTML",
            reply_markup=buttons
        )


async def execute_change_language_logic(message: types.Message, user_id: int, state: FSMContext):
    async with await get_session() as session:
        # Ban check
        user_info = await get_user_status_info(session, user_id)
        if user_info.is_banned:
            await handle_banned_user(message)
            return

        # Log user action
        await log_user_action(session, user_id, "/change_lang command used")

        # Creating a keyboard using a separate function
        keyboard_markup = create_language_keyboard(translations)

        # Sending a message with the keypad
        lang_message = await bot.send_message(
            chat_id=message.chat.id,
            text=await get_translation(user_id, "choose_language"),
            reply_markup=keyboard_markup
        )

        # Saving message IDs in the state
        await state.update_data(lang_message_id=lang_message.message_id, prev_message_id=message.message_id)

        await state.set_state(Form.choosing_language)


# Change language command
@dp.message(F.text == "/change_lang")
async def change_language(message: types.Message, state: FSMContext):
    async with await get_session() as _:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        await execute_change_language_logic(message, user_id, state)


@dp.callback_query(F.data == "choose_language")
async def change_language_via_button(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    async with await get_session() as _:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )
        await execute_change_language_logic(callback_query.message, user_id, state)


# Language selection processing
@dp.callback_query(F.data.in_(translations.keys()))
async def set_language(callback_query: types.CallbackQuery, state: FSMContext):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )

        # Ban check
        user_info = await get_user_status_info(session, user_id)
        if user_info.is_banned:
            await handle_banned_user(callback_query.message)
            return

        selected_language = callback_query.data

        # Updating the language in the database
        await update_user_language(session, user_id, selected_language)
        await set_commands(bot, user_id, selected_language)

        # Forcibly query the language from the database again
        new_language = await get_user_language(session, user_id)
        logging.info(f"Language after update for user {user_id}: {new_language}")

        # Log user action
        await log_user_action(session, user_id, f"Language changed to {selected_language}")

        # Deleting the language selection message and the user's command message
        data = await state.get_data()
        if "lang_message_id" in data:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=data["lang_message_id"])
        if "prev_message_id" in data:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=data["prev_message_id"])
        if "user_command_message_id" in data:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=data["user_command_message_id"])

        # Sending confirmation and proceeding to game selection
        await bot.send_message(
            callback_query.message.chat.id,
            await get_translation(user_id, "language_selected")
        )

        # Displaying the updated action menu
        await send_keys_menu(callback_query.message, state)

        # Resetting the state
        await state.clear()


# Handling of "get_keys" button pressing
@dp.callback_query(F.data == "get_keys")
async def send_keys(callback_query: types.CallbackQuery, state: FSMContext):
    async with (await get_session()) as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )
        await callback_query.answer()

        user_info = await get_user_status_info(session, user_id)
        if user_info.is_banned:
            await handle_banned_user(callback_query.message)
            return

        current_date = datetime.now(timezone.utc).date()
        if user_info.last_reset_date != current_date:
            await reset_daily_keys_if_needed(session, user_id)
            user_info = await get_user_status_info(session, user_id)

        limit = status_limits.get(user_info.user_status, {}).get('daily_limit', 0)
        if user_info.daily_requests_count >= limit:
            await send_limit_reached_message(callback_query, user_id)
            return

        interval_minutes = status_limits[user_info.user_status]['interval_minutes']
        minutes, seconds = get_remaining_time(user_info.last_request_time, interval_minutes)
        if minutes > 0 or seconds > 0:
            translation = await get_translation(user_id, "wait_time_message")
            wait_message = translation.format(minutes=minutes, sec=seconds)
            await send_wait_time_message(callback_query, user_id, wait_message)
            return

        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=None
        )

        keys_list = []
        for game in games:
            keys = await get_oldest_keys(session, game)
            keys_list.append(keys)

        response_text = f"{escape_markdown(await get_translation(user_id, 'keys_generated_ok'))}\n\n"
        total_keys_in_request = 0

        for game, keys in zip(games, keys_list):
            if keys:
                total_keys_in_request += len(keys)
                response_text += f"*{escape_markdown(game)}*:\n"
                keys_to_delete = [key[0] for key in keys]
                response_text += "\n".join([f"`{escape_markdown(key)}`" for key in keys_to_delete]) + "\n\n"
                await delete_keys(session, game, keys_to_delete)
            else:
                response_text += (
                    f"{escape_markdown(await get_translation(user_id, 'no_keys_for'))} *{escape_markdown(game)}* "
                    f"{escape_markdown(await get_translation(user_id, 'no_keys_available'))} 😢\n\n")

        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=response_text.strip(),
            parse_mode="MarkdownV2"
        )

        if total_keys_in_request > 0:
            await update_keys_generated(session, user_id, total_keys_in_request)

        await send_keys_menu(callback_query.message, state)


# Function for sending a message when the daily limit is reached
async def send_limit_reached_message(callback_query: types.CallbackQuery, user_id: int):
    async with await get_session() as session:
        limit_message = await get_translation(user_id, "daily_limit_reached")
        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "wait")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                photo = FSInputFile(image_path)
                if callback_query.message.photo:
                    await bot.send_photo(
                        chat_id=callback_query.message.chat.id,
                        photo=photo,
                        caption=limit_message,
                        reply_markup=await get_action_buttons(session, user_id)
                    )
                    return
                else:
                    await bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id
                    )
                    await bot.send_photo(
                        chat_id=callback_query.message.chat.id,
                        photo=photo,
                        caption=limit_message,
                        parse_mode="HTML",
                        reply_markup=await get_action_buttons(session, user_id)
                    )
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=limit_message,
            reply_markup=await get_action_buttons(session, user_id)
        )


# Function for sending a message to tell you to wait and updating the image
async def send_wait_time_message(callback_query: types.CallbackQuery, user_id: int, wait_message: str):
    async with await get_session() as session:
        chat_id = callback_query.message.chat.id
        message_id = callback_query.message.message_id
        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "wait")

        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                # Create a new image object
                photo = FSInputFile(image_path)
                new_media = types.InputMediaPhoto(media=photo, caption=wait_message)

                if callback_query.message.photo:
                    # Updating the image and signature in a post
                    await bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=message_id,
                        media=new_media,
                        reply_markup=await get_action_buttons(session, user_id)
                    )
                    return
                else:
                    await bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id
                    )
                    await bot.send_photo(
                        chat_id=callback_query.message.chat.id,
                        photo=photo,
                        caption=wait_message,
                        parse_mode="HTML",
                        reply_markup=await get_action_buttons(session, user_id)
                    )

        # If image directory is missing or empty, update text or send a new text message
        if callback_query.message.text:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=wait_message,
                reply_markup=await get_action_buttons(session, user_id)
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=wait_message,
                reply_markup=await get_action_buttons(session, user_id)
            )


# Admin panel handler
@dp.message(F.text == "/admin")
async def admin_panel_handler(message: types.Message, state: FSMContext):
    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

        # Is user admin
        user_info = await get_user_status_info(session, user_id)
        if user_info.is_banned:
            await handle_banned_user(message)
            return
        # JOKE 🤡
        if user_info.user_role != 'admin':
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            not_admin_message = await get_translation(user_id, "not_admin_message")
            message_sent = await bot.send_message(
                chat_id=message.chat.id,
                text=not_admin_message,
            )
            await asyncio.sleep(3)
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=message_sent.message_id,
            )
            not_admin_message_second = await get_translation(user_id, "not_admin_message_second")
            message_sent = await bot.send_message(
                chat_id=message.chat.id,
                text=not_admin_message_second,
            )
            await asyncio.sleep(3)
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=message_sent.message_id,
            )

            # Normal
            await send_keys_menu(message, state)
            return

        admin_text = await get_translation(user_id, "admin_description")
        await bot.send_message(
            chat_id=message.chat.id,
            text=admin_text,
            reply_markup=await get_admin_panel_keyboard(session, user_id)
        )


# Get keys button admin panel
@dp.callback_query(F.data == "keys_admin_panel")
async def keys_admin_panel(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.chat.id
        keys_count_message = await get_keys_count_for_games(session, games)
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=keys_count_message,
            parse_mode="HTML",
            reply_markup=await get_main_in_admin(session, user_id)
        )


# Get users button admin panel
@dp.callback_query(F.data == "users_admin_panel")
async def users_admin_panel(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.chat.id

        users_list_admin_panel_message = await get_users_list_admin_panel(session)

        back_keyboard = await get_main_in_admin(session, user_id)
        detail_info_keyboard = await get_detail_info_in_admin(session, user_id)

        combined_keyboard = InlineKeyboardMarkup(
            inline_keyboard=detail_info_keyboard.inline_keyboard + back_keyboard.inline_keyboard
        )

        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=users_list_admin_panel_message,
            parse_mode="HTML",
            reply_markup=combined_keyboard
        )


@dp.callback_query(F.data == "detail_info_in_admin")
async def request_user_id(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="Пожалуйста, введите ID пользователя, информацию о котором вы хотите получить:"
    )

    await state.set_state(Form.waiting_for_user_id)


# Get user detail button admin panel
@dp.message(Form.waiting_for_user_id)
async def user_detail_admin_panel(message: types.Message, state: FSMContext):
    user_detail_id = message.text.strip()

    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        back_keyboard = await get_main_in_admin(session, user_id)

        try:
            user_detail_id = int(user_detail_id)
        except ValueError:
            text = "<i><b>ID</b> дожно быть целым числом. Пожалуйста, повторите снова!</i>"
            await message.answer(text, parse_mode="HTML", reply_markup=back_keyboard)
            return
        user_details = await get_user_details(session, user_detail_id)

        if "not_found" in user_details:
            text = "<i>Пользователь с таким <b>ID</b> не найден.</i>"
            await message.answer(text, parse_mode="HTML", reply_markup=back_keyboard)
        else:
            await message.answer(user_details, parse_mode="HTML", reply_markup=back_keyboard)

    await state.clear()


# Back to main menu(for admin)
@dp.callback_query(F.data == "back_to_admin_main")
async def back_to_admin_main_menu(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )
        admin_text = await get_translation(user_id, "admin_description")
        await log_user_action(session, user_id, "Return to main admin menu")
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=admin_text,
            reply_markup=await get_admin_panel_keyboard(session, user_id)
        )


@dp.callback_query(F.data == "notifications_admin_panel")
async def notification_menu_handler(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )
        await log_user_action(session, user_id, "Send notification menu")
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Панель рассылки !!!",
            reply_markup=await notification_menu(session, user_id)
        )


@dp.callback_query(F.data == "send_all")
async def confirmation_menu_handler(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )
        await log_user_action(session, user_id, "Confirmation send notification")
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Ты точно хочешь этого ???",
            reply_markup=await confirmation_button_notification(session, user_id)
        )


@dp.callback_query(F.data == "send_to_myself")
async def send_to_myself_handler(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )
        await bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )

        await log_user_action(session, user_id, "Sent ad to themselves")

        # Sending a ban notification
        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "notification")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                # Create a new image object
                photo = FSInputFile(image_path)

                test_message = await bot.send_photo(
                    chat_id=callback_query.message.chat.id,
                    photo=photo,
                    caption="Это ваше рекламное сообщение! Посмотрите на него!",
                    reply_markup=await get_action_buttons(session, user_id),
                    parse_mode="HTML"
                )
        else:
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text="Это ваше рекламное сообщение! Посмотрите на него!",
                reply_markup=await get_action_buttons(session, user_id),
                parse_mode="HTML"
            )
        await asyncio.sleep(2)
        await bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=test_message.message_id
        )

        # Return keyboard
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="Панель рассылки !!!",
            reply_markup=await notification_menu(session, user_id)
        )


# Handler of other messages (including ban check)
@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    async with await get_session() as session:
        user_id = message.from_user.id

        # Logging the receipt of a message
        logging.info(f"Received message from {message.from_user.username}: {message.text}")

        # Check whether the message is a reply to a forwarded message
        if message.reply_to_message and message.reply_to_message.message_id in message_user_mapping:
            original_user_id = message_user_mapping[message.reply_to_message.message_id]
            logging.info(f"Message is a reply from admin. Forwarding to user {original_user_id}.")
            await bot.send_message(chat_id=original_user_id, text=message.text)
            return

        # If the message came from a group, skip it
        if message.chat.id == GROUP_CHAT_ID:
            logging.info("Message received from the group chat, skipping response_text.")
            return

        await log_user_action(session, user_id, f"User message: {message.text}")

        # Forwarding message to administrators
        if not await is_admin(user_id):
            await forward_message_to_admins(message)

        response_text = await get_translation(user_id, "default_response")
        await message.answer(response_text)


# Handling banned users
async def handle_banned_user(message: types.Message):
    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        # User action logging
        await log_user_action(session, user_id, "Attempted interaction while banned")

        # Sending a ban notification
        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "banned")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id,
                    photo=photo,
                    caption=await get_translation(user_id, "ban_message")
                )
                return
        await bot.send_message(chat_id, await get_translation(user_id, "ban_message"))


# Settings button
@dp.callback_query(F.data == "settings")
async def show_settings_menu(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )

        # Ban check
        user_info = await get_user_status_info(session, user_id)
        if user_info.is_banned:
            await handle_banned_user(callback_query.message)
            return

        await log_user_action(session, user_id, "Settings menu opened")
        settings_message = await get_translation(user_id, "settings_message")

        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "generate")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)
                photo = FSInputFile(image_path)

                if callback_query.message.photo:
                    # If the previous message had a photo, update it
                    new_media = types.InputMediaPhoto(media=photo)
                    await bot.edit_message_media(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id,
                        media=new_media,
                    )
                    await bot.edit_message_caption(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id,
                        caption=settings_message,
                        parse_mode="HTML",
                        reply_markup=await get_settings_menu(session, user_id)
                    )
                else:
                    # Delete the old message without a photo and send a new one
                    await bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id
                    )
                    await bot.send_photo(
                        chat_id=callback_query.message.chat.id,
                        photo=photo,
                        caption=settings_message,
                        parse_mode="HTML",
                        reply_markup=await get_settings_menu(session, user_id)
                    )
            return

        # If no image directory or files, just edit the text message
        if callback_query.message.text:
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=settings_message,
                parse_mode="HTML",
                reply_markup=await get_settings_menu(session, user_id)
            )


@dp.callback_query(F.data == "info")
async def show_info_message(callback_query: types.CallbackQuery, state: FSMContext):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )

        await log_user_action(session, user_id, "Info opened")

        info_message = await get_translation(user_id, "info_message")

        if callback_query.message.photo:
            await bot.edit_message_caption(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                caption=info_message,
                parse_mode="HTML",
                reply_markup=await get_main_from_info(session, user_id)
            )
        else:
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=info_message,
                parse_mode="HTML",
                reply_markup=await get_main_from_info(session, user_id)
            )


# Back to main menu(for settings)
@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        )

        await log_user_action(session, user_id, "Return to main menu")
        main_menu_text = await get_translation(user_id, "chose_action")

        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "key_generated")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                # Create a new image object
                photo = FSInputFile(image_path)
                new_media = types.InputMediaPhoto(media=photo)
                if callback_query.message.photo:
                    await bot.edit_message_media(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id,
                        media=new_media,
                    )
                    await bot.edit_message_caption(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id,
                        caption=main_menu_text,
                        parse_mode="HTML",
                        reply_markup=await get_action_buttons(session, user_id)
                    )
                else:
                    await bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=callback_query.message.message_id
                    )
                    await bot.send_photo(
                        chat_id=callback_query.message.chat.id,
                        photo=photo,
                        caption=main_menu_text,
                        parse_mode="HTML",
                        reply_markup=await get_action_buttons(session, user_id)
                    )


# Forward a message to all admins and optionally to a group chat
async def forward_message_to_admins(message: Message):
    admin_chat_ids = await get_admin_chat_ids()
    tasks = []
    message_ids = {}

    # Forward the message to all admins
    for admin_chat_id in admin_chat_ids:
        logging.info(f"Forwarding message from {message.chat.username} to admin {admin_chat_id}")
        task = bot.forward_message(
            chat_id=admin_chat_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        tasks.append(task)

    # Forward the message to the group chat if GROUP_CHAT_ID is defined
    if GROUP_CHAT_ID:
        logging.info(f"Forwarding message from {message.chat.username} to group {GROUP_CHAT_ID}")
        task = bot.forward_message(
            chat_id=GROUP_CHAT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        tasks.append(task)

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
