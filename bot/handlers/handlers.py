import asyncio
import logging
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from config import bot, BOT_ID
from common.static_data import GAMES, STATUS_LIMITS, SUPPORTED_LANGUAGES
from database.database import (
    get_session, get_or_create_user, update_user_language, log_user_action,
    get_user_language, get_oldest_keys, update_keys_generated,
    delete_keys, get_user_status_info,
    check_user_limits, check_user_safety_limits,
    get_keys_count_main_menu, get_user_stats, update_safety_keys_generated,
    delete_safety_keys, get_safety_keys
)
from handlers.command_setup import set_user_commands
from keyboards.back_to_main_kb import get_back_to_main_menu_button
from keyboards.donate_kb import get_donation_keyboard
from keyboards.referral_links_kb import referral_links_keyboard
from keyboards.inline import get_action_buttons, get_settings_menu, create_language_keyboard, instruction_prem_button
from utils import get_translation, get_available_languages, load_image
from utils.helpers import get_remaining_time
from states.form import Form
from utils.services import generate_user_stats

router = Router()


# Command handler /start
async def welcome_command_handler(session, message, user_id, chat_id, user):
    try:
        # Define the user language, if it is not supported - set English
        user_language_code = user.language_code if user.language_code in SUPPORTED_LANGUAGES else 'en'

        user_data = {
            'chat_id': chat_id,
            'user_id': user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'language_code': user_language_code
        }

        await log_user_action(session, user_id, "/start command used")

        user_record = await get_or_create_user(session, chat_id, user_data)

        if user_record is None:
            await message.answer("Error creating user.")
            return

        # Update user language if necessary
        if user_record.language_code != user_data['language_code']:
            await update_user_language(session, user_id, user_data['language_code'])

        translation = await get_translation(user_id, "common", "welcome")
        welcome_text = translation.format(first_name=user.first_name)

        photo = await load_image("welcome")
        if photo:
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=welcome_text,
                    reply_markup=await get_action_buttons(session, user_id)
                )
                return
            except Exception as e:
                logging.error(f"Failed to send photo in welcome message: {e}")

            await bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
                reply_markup=await get_action_buttons(session, user_id)
            )
    except Exception as e:
        logging.error(f"Error in welcome_command_handler: {e}")

        await message.answer("An error occurred while processing your request.")


# Function to send keys menu after generating keys
async def send_menu_handler(message: types.Message, is_back_to_menu: bool = False):
    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        # Use the function to get the buttons
        buttons = await get_action_buttons(session, user_id)
        caption = await get_translation(user_id, "messages", "choose_action")
        keys_data = await get_keys_count_main_menu(session, GAMES)

        photo = await load_image("key_generated")
        if photo:
            if is_back_to_menu and message.photo:
                await bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message.message_id,
                    media=types.InputMediaPhoto(media=photo, caption=caption.format(
                        keys_today=keys_data['keys_today'],
                        premium_keys_today=keys_data['premium_keys_today']
                    )),
                    reply_markup=buttons
                )
            else:
                await bot.send_photo(
                    chat_id,
                    photo=photo,
                    caption=caption.format(
                        keys_today=keys_data['keys_today'],
                        premium_keys_today=keys_data['premium_keys_today']
                    ),
                    reply_markup=buttons
                )
            return
        if is_back_to_menu and message.text:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message.message_id,
                text=caption.format(
                    keys_today=keys_data['keys_today'],
                    premium_keys_today=keys_data['premium_keys_today']
                ),
                reply_markup=buttons
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=caption.format(
                    keys_today=keys_data['keys_today'],
                    premium_keys_today=keys_data['premium_keys_today']
                ),
                reply_markup=buttons
            )


@router.callback_query(F.data == "referral_links")
async def referral_links_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id

    photo = await load_image("premium")
    if photo:
        caption_ref_link = await get_translation(user_id, "messages", "referral_links_intro")
        new_media = types.InputMediaPhoto(media=photo, caption=caption_ref_link)
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        keyboard = await referral_links_keyboard(user_id)

        if callback.message.photo:
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=new_media,
                reply_markup=keyboard
            )
        else:
            await bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption_ref_link,
                reply_markup=keyboard
            )


async def change_language_logic_handler(message: types.Message, user_id: int, state: FSMContext):
    async with await get_session() as session:

        # Log user action
        await log_user_action(session, user_id, "/change_lang command used")

        available_languages = get_available_languages()

        # Creating a keyboard using a separate function
        keyboard_markup = create_language_keyboard(available_languages)

        # Sending a message with the keypad
        lang_message = await bot.send_message(
            chat_id=message.chat.id,
            text=await get_translation(user_id, "common", "choose_language"),
            reply_markup=keyboard_markup
        )

        # Saving message IDs in the state
        await state.update_data(lang_message_id=lang_message.message_id, prev_message_id=message.message_id)

        await state.set_state(Form.language_selection)


@router.callback_query(F.data == "settings_choose_language")
async def language_button_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    async with await get_session() as _:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )
        await change_language_logic_handler(callback.message, user_id, state)


# Language selection processing
@router.callback_query(F.data.in_(get_available_languages().keys()))
async def set_language(callback: types.CallbackQuery, state: FSMContext):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        selected_language = callback.data

        # Updating the language in the database
        await update_user_language(session, user_id, selected_language)

        await get_user_language(session, user_id)

        # Set commands for the selected language
        await set_user_commands(bot, user_id)

        # Forcibly query the language from the database again
        new_language = await get_user_language(session, user_id)
        logging.info(f"Language after update for user {user_id}: {new_language}")

        # Log user action
        await log_user_action(session, user_id, f"Language changed to {selected_language}")

        # Deleting the language selection message and the user's command message
        data = await state.get_data()
        if "lang_message_id" in data:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=data["lang_message_id"])
        if "prev_message_id" in data:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=data["prev_message_id"])
        if "user_command_message_id" in data:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=data["user_command_message_id"])

        await callback.answer(await get_translation(user_id, "common", "language_selected"))

        # Displaying the updated action menu
        await send_menu_handler(callback.message)

        # Resetting the state
        await state.clear()


# Handling of "get_keys" button pressing
@router.callback_query(F.data == "keys_regular")
async def keys_handler(callback: types.CallbackQuery):
    try:
        async with (await get_session()) as session:
            user_id = (
                callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
            )
            await callback.answer()

            user_info = await get_user_status_info(session, user_id)

            # Checking the request limit
            if not await check_user_limits(session, user_id, STATUS_LIMITS):
                await send_daily_limit_reached_handler(callback, user_id)
                return

            # Checking the interval between requests
            interval_minutes = STATUS_LIMITS[user_info.user_status]['interval_minutes']
            minutes, seconds = get_remaining_time(user_info.last_request_time, interval_minutes)
            if minutes > 0 or seconds > 0:
                wait_message_template = await get_translation(user_id, "messages", "wait_time_without_hours")
                wait_message = wait_message_template.format(minutes=minutes, sec=seconds)
                await send_wait_time_handler(callback, user_id, wait_message)
                return

            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None
            )

            keys_list = []
            for game in GAMES:
                keys = await get_oldest_keys(session, game)
                keys_list.append(keys)

            response_text_template = await get_translation(user_id, "messages", 'keys_generated_success')
            response_text = f"{response_text_template}\n\n"
            total_keys_in_request = 0

            for game, keys in zip(GAMES, keys_list):
                if keys:
                    total_keys_in_request += len(keys)
                    response_text += f"<b>{game}</b>:\n"
                    keys_to_delete = [key for key in keys]
                    response_text += "\n".join([f"<code>{key}</code>" for key in keys_to_delete]) + "\n\n"
                    await delete_keys(session, game, keys_to_delete)
                else:
                    no_keys_template = await get_translation(user_id, "messages", 'no_keys_available')
                    response_text += no_keys_template.format(game=game)

            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=response_text.strip()
            )

            if total_keys_in_request > 0:
                await update_keys_generated(session, user_id, total_keys_in_request)

            await send_menu_handler(callback.message)

    except Exception as e:
        logging.error(f"Error processing get_keys: {e}")
        error_text = await get_translation(user_id, "messages", "error_handler")

        await callback.answer(error_text)


# Handling of "get_safety_keys" button pressing
@router.callback_query(F.data == "keys_premium")
async def safety_keys_handler(callback: types.CallbackQuery):
    try:
        async with (await get_session()) as session:
            user_id = (
                callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
            )
            await callback.answer()

            logging.info(f"User {user_id} press prem keys")
            user_info = await get_user_status_info(session, user_id)

            if user_info.user_status not in ['premium']:
                not_prem_message = await get_translation(user_id, "messages", "not_premium_access")
                photo = await load_image("premium")
                if photo:
                    await bot.delete_message(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.message_id
                    )
                    await bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=photo,
                        caption=not_prem_message,
                        reply_markup=await instruction_prem_button(session, user_id)
                    )
                    return
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=not_prem_message,
                    reply_markup=await instruction_prem_button(session, user_id)
                )

            # Checking the limit of requests for safety keys
            if not await check_user_safety_limits(session, user_id, STATUS_LIMITS):
                message_to_update = await send_daily_limit_reached_handler(callback, user_id)

                await asyncio.sleep(1.5)

                support_message = await get_translation(user_id, "messages", "support_project_prompt")
                photo = await load_image("premium")
                if photo:
                    await bot.edit_message_media(
                        chat_id=callback.message.chat.id,
                        message_id=message_to_update.message_id,
                        media=types.InputMediaPhoto(media=photo, caption=support_message),
                        reply_markup=await get_action_buttons(session, user_id)
                    )
                else:
                    await bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=message_to_update.message_id,
                        text=support_message,
                        reply_markup=await get_action_buttons(session, user_id)
                    )
                return

            # Checking the interval between requests
            interval_minutes = STATUS_LIMITS[user_info.user_status]['safety_interval_minutes']
            minutes, seconds = get_remaining_time(user_info.last_safety_keys_request_time, interval_minutes)
            if minutes > 59:
                hours = minutes // 60
                minutes = minutes % 60
                wait_message_template = await get_translation(user_id, "messages", "wait_time_with_hours")
                wait_message = wait_message_template.format(hours=hours, minutes=minutes, sec=seconds)
            else:
                wait_message_template = await get_translation(user_id, "messages", "wait_time_without_hours")
                wait_message = wait_message_template.format(minutes=minutes, sec=seconds)

            if minutes > 0 or seconds > 0:
                await send_wait_time_handler(callback, user_id, wait_message)
                return

            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None
            )

            keys_list = []
            for game in GAMES:
                keys = await get_safety_keys(session, game)
                keys_list.append(keys)

            response_text_template = await get_translation(user_id, "messages", 'premium_keys_generated_success')
            response_text = f"{response_text_template}\n\n"
            total_keys_in_request = 0

            for game, keys in zip(GAMES, keys_list):
                if keys:
                    total_keys_in_request += len(keys)
                    response_text += f"<b>{game}</b>:\n"
                    keys_to_delete = [key[0] for key in keys]
                    response_text += "\n".join([f"<code>{key}</code>" for key in keys_to_delete]) + "\n\n"
                    await delete_safety_keys(session, game, keys_to_delete)
                else:
                    no_keys_template = await get_translation(user_id, "messages", 'no_keys_available')
                    response_text += no_keys_template.format(game=game)

            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=response_text.strip()
            )

            if total_keys_in_request > 0:
                await update_safety_keys_generated(session, user_id, total_keys_in_request)

            await send_menu_handler(callback.message)

    except Exception as e:
        logging.error(f"Error processing get_keys: {e}")
        error_text = await get_translation(user_id, "messages", "error_handler")

        await callback.answer(error_text)


# Function for sending a message when the daily limit is reached
async def send_daily_limit_reached_handler(callback: types.CallbackQuery, user_id: int):
    async with await get_session() as session:
        limit_message = await get_translation(user_id, "messages", "daily_limit_exceeded")

        photo = await load_image("premium")
        if photo:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
            return await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=photo,
                caption=limit_message,
                reply_markup=await get_action_buttons(session, user_id)
            )
        return await bot.send_message(
            chat_id=callback.message.chat.id,
            text=limit_message,
            reply_markup=await get_action_buttons(session, user_id)
        )


# Function for sending a message to tell you to wait and updating the image
async def send_wait_time_handler(callback: types.CallbackQuery, user_id: int, wait_message: str):
    async with await get_session() as session:
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        photo = await load_image("premium")
        if photo:
            new_media = types.InputMediaPhoto(media=photo, caption=wait_message)

            if callback.message.photo:
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
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id
                )
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=photo,
                    caption=wait_message,
                    reply_markup=await get_action_buttons(session, user_id)
                )
        # If image directory is missing or empty
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )
        await bot.send_message(
            chat_id=chat_id,
            text=wait_message,
            reply_markup=await get_action_buttons(session, user_id)
        )


# Handling banned users
async def banned_user_handler(message: types.Message):
    async with await get_session() as session:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id = message.chat.id

        # User action logging
        await log_user_action(session, user_id, "Attempted interaction while banned")

        photo = await load_image("banned")
        if photo:
            await bot.send_photo(
                chat_id,
                photo=photo,
                caption=await get_translation(user_id, "common", "ban_notification")
            )
            return
        await bot.send_message(chat_id, await get_translation(user_id, "common", "ban_notification"))


# Settings button
@router.callback_query(F.data == "settings_menu")
async def settings_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        await log_user_action(session, user_id, "Settings menu opened")
        settings_message = await get_translation(user_id, "buttons", "settings")
        photo = await load_image("settings")
        if photo:
            new_media = types.InputMediaPhoto(media=photo, caption=settings_message)
            if callback.message.photo:
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=new_media,
                    reply_markup=await get_settings_menu(session, user_id)
                )
            else:
                await bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id
                )
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=photo,
                    caption=settings_message,
                    reply_markup=await get_settings_menu(session, user_id)
                )
            return
        if callback.message.text:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=settings_message,
                reply_markup=await get_settings_menu(session, user_id)
            )


# User statistic
@router.callback_query(F.data == "user_stats")
async def user_stats_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id

        await log_user_action(session, user_id, "User checked stats")

        user_data = await get_user_stats(session, user_id, GAMES)
        if not user_data:
            await callback.answer("User not found!")

        user_stats = await generate_user_stats(user_data)

        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        stats_translation = await get_translation(user_id, "messages", "user_stats")
        user_status = await get_translation(user_id, "statuses", f"{user_stats['user_status']}")
        achievement_name = await get_translation(user_id, "achievements", f"{user_stats['achievement_name']}")

        info_caption = stats_translation.format(
            achievement_name=achievement_name,
            keys_today=user_stats['keys_today'],
            premium_keys_today=user_stats['premium_keys_today'],
            keys_total=user_stats['keys_total'],
            premium_keys_total=user_stats['premium_keys_total'],
            user_status=user_status,
        )
        keyboard = await get_back_to_main_menu_button(user_id)

        if callback.message.photo:
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=info_caption,
                reply_markup=keyboard
            )
        else:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=info_caption,
                reply_markup=keyboard
            )


@router.callback_query(F.data == "user_info")
async def info_handler(callback: types.CallbackQuery):
    async with await get_session() as session:
        user_id = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        await log_user_action(session, user_id, "Info opened")
        await callback.answer()

        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        info_caption = await get_translation(user_id, "messages", "info_description")
        keyboard = await get_donation_keyboard(user_id)

        if callback.message.photo:
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=info_caption,
                reply_markup=keyboard
            )
        else:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=info_caption,
                reply_markup=keyboard
            )


# Back to main menu(for settings)
@router.callback_query(F.data == "main_menu_back")
async def back_to_main_menu_handler(callback: types.CallbackQuery):
    await callback.answer()
    await send_menu_handler(callback.message, is_back_to_menu=True)


def register_all_handlers(dp):
    dp.include_router(router)
