from typing import Any, Dict, List, Optional

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InputFile, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_config import BOT_ID, bot, logger
from bot.db_handler.db_service import (
    check_user_limits,
    delete_keys,
    get_keys,
    get_keys_count_main_menu,
    get_or_create_user,
    get_user_language,
    get_user_stats,
    get_user_status_info,
    log_user_action,
    update_keys_generated,
    update_user_language,
)
from bot.handlers.command_setup import set_user_commands
from bot.keyboards.back_to_main_kb import get_back_to_main_menu_button
from bot.keyboards.donate_kb import get_donation_keyboard
from bot.keyboards.inline import (
    create_language_keyboard,
    get_action_buttons,
    get_settings_menu,
)
from bot.keyboards.referral_links_kb import referral_links_keyboard
from bot.states.form import Form
from bot.utils import get_available_languages, get_translation, load_image
from bot.utils.services import generate_user_stats
from bot.utils.static_data import GAMES, STATUS_LIMITS, SUPPORTED_LANGUAGES
from bot.utils.utils import get_remaining_time
from db.database import get_session

router = Router()


# Command handler /start
async def welcome_command_handler(
        session: AsyncSession, message: types.Message, user_id: int, chat_id: int, user: types.User) -> None:
    try:
        # Define the user language, if it is not supported - set English
        user_language_code: str = user.language_code if user.language_code in SUPPORTED_LANGUAGES else 'en'

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

        translation: str = await get_translation(user_id, "common", "welcome")
        welcome_text: str = translation.format(first_name=user.first_name)

        photo: Optional[InputFile] = await load_image("welcome")
        if photo:
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=welcome_text,
                    reply_markup=await get_action_buttons(user_id)
                )
                return
            except Exception as e:
                logger.error(f"Failed to send photo in welcome message: {e}")

            await bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
                reply_markup=await get_action_buttons(user_id)
            )
        else:
            await message.answer(
                text=welcome_text,
                reply_markup=await get_action_buttons(user_id)
            )
    except Exception as e:
        logger.error(f"Error in welcome_command_handler: {e}")

        await message.answer("An error occurred while processing your request.")


# Function to send keys menu after generating keys
async def send_menu_handler(message: types.Message, is_back_to_menu: bool = False) -> None:
    async with await get_session() as session:
        user_id: int = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id: int = message.chat.id

        # Use the function to get the buttons
        buttons: InlineKeyboardMarkup = await get_action_buttons(user_id)
        caption: str = await get_translation(user_id, "messages", "choose_action")
        keys_data: Dict = await get_keys_count_main_menu(session, GAMES)

        photo: Optional[InputFile] = await load_image("key_generated")
        if photo:
            if is_back_to_menu and message.photo:
                await bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message.message_id,
                    media=types.InputMediaPhoto(media=photo, caption=caption.format(
                        keys_today=keys_data['keys_today'],
                    )),
                    reply_markup=buttons
                )
            else:
                await bot.send_photo(
                    chat_id,
                    photo=photo,
                    caption=caption.format(
                        keys_today=keys_data['keys_today'],
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
                ),
                reply_markup=buttons
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=caption.format(
                    keys_today=keys_data['keys_today'],
                ),
                reply_markup=buttons
            )


@router.callback_query(F.data == "referral_links")
async def referral_links_handler(callback: types.CallbackQuery) -> None:
    user_id: int = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id

    photo: Optional[InputFile] = await load_image("premium")

    caption_ref_link: str = await get_translation(user_id, "messages", "referral_links_intro")
    chat_id: int = callback.message.chat.id
    message_id: int = callback.message.message_id
    keyboard: InlineKeyboardMarkup = await referral_links_keyboard(user_id)
    await callback.answer()

    if photo:
        new_media: InputMediaPhoto = types.InputMediaPhoto(media=photo, caption=caption_ref_link)

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
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=caption_ref_link,
            reply_markup=keyboard
        )


async def change_language_logic_handler(message: types.Message, user_id: int, state: FSMContext) -> None:
    async with await get_session() as session:

        # Log user action
        await log_user_action(session, user_id, "/change_lang command used")

        available_languages: Dict = get_available_languages()

        # Creating a keyboard using a separate function
        keyboard_markup: InlineKeyboardMarkup = create_language_keyboard(available_languages)

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
async def language_button_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    async with await get_session() as _:
        user_id: int = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )
        await change_language_logic_handler(callback.message, user_id, state)


# Language selection processing
@router.callback_query(F.data.in_(get_available_languages().keys()))
async def set_language(callback: types.CallbackQuery, state: FSMContext) -> None:
    async with await get_session() as session:
        user_id: int = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        selected_language: str = callback.data

        # Updating the language in the database
        await update_user_language(session, user_id, selected_language)

        await get_user_language(session, user_id)

        # Set commands for the selected language
        await set_user_commands(bot, user_id)

        # Forcibly query the language from the database again
        new_language: str = await get_user_language(session, user_id)
        logger.info(f"Language after update for user {user_id}: {new_language}")

        # Log user action
        await log_user_action(session, user_id, f"Language changed to {selected_language}")

        # Deleting the language selection message and the user's command message
        data: Dict = await state.get_data()
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
async def keys_handler(callback: types.CallbackQuery) -> None:
    try:
        async with (await get_session()) as session:
            user_id: int = (
                callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
            )
            await callback.answer()

            user_info = await get_user_status_info(session, user_id)

            # Checking the request limit
            if not await check_user_limits(session, user_id, STATUS_LIMITS):
                await send_daily_limit_reached_handler(callback, user_id)
                return

            # Checking the interval between requests
            interval_minutes: int = STATUS_LIMITS[user_info.user_status]['interval_minutes']
            minutes, seconds = get_remaining_time(user_info.last_request_time, interval_minutes)
            if minutes > 0 or seconds > 0:
                wait_message_template: str = await get_translation(user_id, "messages", "wait_time_without_hours")
                wait_message = wait_message_template.format(minutes=minutes, sec=seconds)
                await send_wait_time_handler(callback, user_id, wait_message)
                return

            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None
            )

            keys_list: List[Dict[str, str]] = []
            for game in GAMES:
                keys: Dict[str, str] = await get_keys(session, game)
                keys_list.append(keys)

            response_text_template: str = await get_translation(user_id, "messages", 'keys_generated_success')
            response_text: str = f"{response_text_template}\n\n"
            total_keys_in_request: int = 0

            for game, keys in zip(GAMES, keys_list):
                if keys:
                    total_keys_in_request += len(keys)
                    response_text += f"<b>{game}</b>:\n"
                    keys_to_delete: List[str] = [key for key in keys]
                    response_text += "\n".join([f"<code>{key}</code>" for key in keys_to_delete]) + "\n\n"
                    await delete_keys(session, game, keys_to_delete)
                else:
                    no_keys_template: str = await get_translation(user_id, "messages", 'no_keys_available')
                    response_text += no_keys_template.format(game=game)

            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=response_text.strip()
            )

            if total_keys_in_request > 0:
                await update_keys_generated(session, user_id, total_keys_in_request)

            await send_menu_handler(callback.message)

    except Exception as e:
        logger.error(f"Error processing get_keys: {e}")
        error_text: str = await get_translation(user_id, "messages", "error_handler")
        await callback.answer(error_text)


# Function for sending a message when the daily limit is reached
async def send_daily_limit_reached_handler(callback: types.CallbackQuery, user_id: int) -> None:
    limit_message: str = await get_translation(user_id, "messages", "daily_limit_exceeded")

    photo: Optional[InputFile] = await load_image("premium")
    if photo:
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )
        return await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=photo,
            caption=limit_message,
            reply_markup=await get_action_buttons(user_id)
        )
    return await bot.send_message(
        chat_id=callback.message.chat.id,
        text=limit_message,
        reply_markup=await get_action_buttons(user_id)
    )


# Function for sending a message to tell you to wait and updating the image
async def send_wait_time_handler(callback: types.CallbackQuery, user_id: int, wait_message: str) -> None:
    chat_id: int = callback.message.chat.id
    message_id: int = callback.message.message_id
    photo: Optional[InputFile] = await load_image("premium")
    if photo:
        new_media: InputMediaPhoto = types.InputMediaPhoto(media=photo, caption=wait_message)

        if callback.message.photo:
            # Updating the image and signature in a post
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=new_media,
                reply_markup=await get_action_buttons(user_id)
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
                reply_markup=await get_action_buttons(user_id)
            )
    # If image directory is missing or empty
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id
    )
    await bot.send_message(
        chat_id=chat_id,
        text=wait_message,
        reply_markup=await get_action_buttons(user_id)
    )


# Handling banned users
async def banned_user_handler(message: types.Message) -> None:
    async with await get_session() as session:
        user_id: int = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
        chat_id: int = message.chat.id

        # User action logger
        await log_user_action(session, user_id, "Attempted interaction while banned")

        photo: Optional[InputFile] = await load_image("banned")
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
async def settings_handler(callback: types.CallbackQuery) -> None:
    async with await get_session() as session:
        user_id: int = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        await log_user_action(session, user_id, "Settings menu opened")
        settings_message: str = await get_translation(user_id, "messages", "settings_intro")
        photo: Optional[InputFile] = await load_image("settings")
        if photo:
            new_media: InputMediaPhoto = types.InputMediaPhoto(media=photo, caption=settings_message)
            if callback.message.photo:
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=new_media,
                    reply_markup=await get_settings_menu(user_id)
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
                    reply_markup=await get_settings_menu(user_id)
                )
            return
        if callback.message.text:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=settings_message,
                reply_markup=await get_settings_menu(user_id)
            )


# User statistic
@router.callback_query(F.data == "user_stats")
async def user_stats_handler(callback: types.CallbackQuery) -> None:
    async with await get_session() as session:
        user_id: int = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id

        await log_user_action(session, user_id, "User checked stats")

        user_data = await get_user_stats(session, user_id, GAMES)
        if not user_data:
            await callback.answer("User not found!")

        user_stats: Dict[str, Any] = await generate_user_stats(user_data)

        chat_id: int = callback.message.chat.id
        message_id: int = callback.message.message_id
        stats_translation: str = await get_translation(user_id, "messages", "user_stats")
        user_status: str = await get_translation(user_id, "statuses", f"{user_stats['user_status']}")
        achievement_name: str = await get_translation(user_id, "achievements", f"{user_stats['achievement_name']}")

        info_caption = stats_translation.format(
            achievement_name=achievement_name,
            keys_today=user_stats['keys_today'],
            keys_total=user_stats['keys_total'],
            user_status=user_status,
        )
        keyboard: InlineKeyboardMarkup = await get_back_to_main_menu_button(user_id)

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
async def info_handler(callback: types.CallbackQuery) -> None:
    async with await get_session() as session:
        user_id: int = (
            callback.from_user.id if callback.from_user.id != BOT_ID else callback.message.chat.id
        )

        await log_user_action(session, user_id, "Info opened")
        await callback.answer()

        chat_id: int = callback.message.chat.id
        message_id: int = callback.message.message_id
        info_caption: str = await get_translation(user_id, "messages", "info_description")
        keyboard: InlineKeyboardMarkup = await get_donation_keyboard(user_id)

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
async def back_to_main_menu_handler(callback: types.CallbackQuery) -> None:
    await callback.answer()
    await send_menu_handler(callback.message, is_back_to_menu=True)


def register_all_handlers(dp) -> None:
    dp.include_router(router)
