import logging
from aiogram import types, F, Router
from aiogram.exceptions import TelegramBadRequest
from config import bot, BOT_ID, GROUP_CHAT_ID
from database.database import (get_session, get_or_create_user, update_user_language, log_user_action,
                               get_user_language, get_oldest_keys, update_keys_generated,
                               delete_keys, get_user_status_info, is_admin, get_admin_chat_ids,
                               get_keys_count_for_games, get_users_list_admin_panel, get_user_details,
                               get_subscribed_users, get_user_role_and_ban_info, update_safety_keys_generated,
                               delete_safety_keys, get_safety_keys, check_user_limits, check_user_safety_limits,
                               get_keys_count_main_menu, get_user_stats)

from handlers.admin_handlers import message_user_mapping, forward_message_to_admins

router = Router()


# Handler of other messages
@router.message(F.text)
async def handle_message(message: types.Message):
    try:
        user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id

        # Check if message is a command
        if message.text.startswith("/"):
            logging.info(f"User with ID {user_id} used the /admin command.")
            return
        async with (await get_session() as session):
            logging.info(f"Received message from {message.from_user.username}: {message.text}")

            # Check: if the sender of the message is an admin, the message will be sent directly to the user
            if (await is_admin(user_id) and message.reply_to_message and
                    message.reply_to_message.message_id in message_user_mapping):
                original_user_id = message_user_mapping[message.reply_to_message.message_id]
                logging.info(f"Admin is replying to user {original_user_id}. Forwarding message.")
                await bot.send_message(chat_id=original_user_id, text=message.text)
                return

            # If the message came from a group, skip it
            if message.chat.id == GROUP_CHAT_ID:
                logging.info("Message received from the group chat, skipping response.")
                return

            try:
                await log_user_action(session, user_id, f"User message: {message.text}")
            except Exception as e:
                logging.error(f"Error logging user action: {e}")

            # Forwarding message to administrators
            await forward_message_to_admins(message)

            # Check to see if we can add reactions
            if hasattr(message, 'react'):
                emoji = types.ReactionTypeEmoji(emoji='👀')
                await message.react([emoji])
            else:
                logging.warning("The message object does not support reactions.")

    except TelegramBadRequest as e:
        logging.error(f"Failed to react to the message: {e}")
        # You can choose to notify the user, or just log the error and ignore it.
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")


def register_message_handler(dp):
    dp.include_router(router)
