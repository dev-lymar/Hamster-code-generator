import asyncio
import os
import random
import logging
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from config import bot, dp, BOT_ID, games, status_limits, set_commands
from database.database import (get_session, get_or_create_user, update_user_language, log_user_action,
                               reset_daily_keys_if_needed, is_user_banned, get_user_language,
                               get_oldest_keys, update_keys_generated, delete_keys, check_user_limits,
                               get_last_request_time)
from keyboards.inline import get_action_buttons, get_settings_menu, create_language_keyboard
from utils.helpers import load_translations, get_translation, escape_markdown, get_remaining_time
from states.form import Form

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
                    chat_id,
                    photo=photo,
                    caption=welcome_text,
                    reply_markup=await get_action_buttons(session, user_id)
                )
                return

        # Sending welcome message without photo
        await bot.send_message(chat_id, text=welcome_text, reply_markup=await get_action_buttons(session, user_id))


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
        if await is_user_banned(session, user_id):
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
        await state.update_data(lang_message_id=lang_message.message_id)

        await state.set_state(Form.choosing_language)


# Change language command
@dp.message(F.text == "/change_lang")
async def change_language(message: types.Message, state: FSMContext):
    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        await execute_change_language_logic(message, user_id, state)


@dp.callback_query(F.data == "choose_language")
async def change_language_via_button(callback_query: types.CallbackQuery, state: FSMContext):
    async with await get_session() as session:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        await execute_change_language_logic(callback_query.message, user_id, state)


# Language selection processing
@dp.callback_query(F.data.in_(translations.keys()))
async def set_language(callback_query: types.CallbackQuery, state: FSMContext):
    async with await get_session() as session:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id

        # Ban check
        if await is_user_banned(session, user_id):
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
    async with await get_session() as session:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id
        await callback_query.answer()
        # Ban check
        if await is_user_banned(session, user_id):
            await handle_banned_user(callback_query.message)
            return

        # Check for reaching the limit of keys per day
        if not await check_user_limits(session, user_id, status_limits):
            await send_limit_reached_message(callback_query, user_id)
            return

        # Checking the time of the last request
        last_request_time, user_status = await get_last_request_time(session, user_id)
        interval_minutes = status_limits[user_status]['interval_minutes']

        # Calculation of remaining time
        minutes, seconds = get_remaining_time(last_request_time, interval_minutes)
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

        tasks = [get_oldest_keys(session, game) for game in games]
        keys_list = await asyncio.gather(*tasks)

        # If the limit is not reached, continue processing
        response_text = f"{escape_markdown(await get_translation(user_id, 'keys_generated_ok'))}\n\n"
        total_keys_in_request = 0

        for game, keys in zip(games, keys_list):
            if keys:
                total_keys_in_request += len(keys)
                response_text += f"*{escape_markdown(game)}*:\n"
                keys_to_delete = []
                for key in keys:
                    promo_code = key[0]
                    response_text += f"`{escape_markdown(promo_code)}`\n"
                    keys_to_delete.append(promo_code)
                response_text += "\n"
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
        image_dir = os.path.join(os.path.dirname(__file__), "..", "images", "wait")
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(image_dir, random_image)

                photo = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id=callback_query.message.chat.id,
                    photo=photo,
                    caption=await get_translation(user_id, "daily_limit_reached"),
                    reply_markup=await get_action_buttons(session, user_id)
                )
                return
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=await get_translation(user_id, "daily_limit_reached"),
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

                # Updating the image and signature in a post
                await bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=new_media,
                    reply_markup=await get_action_buttons(session, user_id)
                )
                return

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


# Handler of other messages (including ban check)
@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

        # Ban check
        if await is_user_banned(session, user_id):
            await handle_banned_user(message)
            return

        # Reset daily keys if needed
        await reset_daily_keys_if_needed(session, user_id)

        # Logging a user's message
        await log_user_action(session, user_id, f"User message: {message.text}")

        # Response to user post
        await message.answer(await get_translation(user_id, "default_response"))


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


@dp.callback_query(F.data == "settings")
async def show_settings_menu(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id

        # Ban check
        if await is_user_banned(session, user_id):
            await handle_banned_user(callback_query.message)
            return

        await log_user_action(session, user_id, "Settings menu opened")

        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=await get_settings_menu(session, user_id)
        )


@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    async with await get_session() as session:
        user_id = callback_query.from_user.id if callback_query.from_user.id != BOT_ID else callback_query.message.chat.id

        # Ban check
        if await is_user_banned(session, user_id):
            await handle_banned_user(callback_query.message)
            return

        await log_user_action(session, user_id, "Return to main menu")

        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=await get_action_buttons(session, user_id)
        )
