import asyncio

from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.bot_config import bot
from bot.database.database import get_user_role_and_ban_info
from bot.handlers.handlers import send_menu_handler
from bot.utils import get_translation
from db.database import get_session


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        async with await get_session() as session:
            user_id = message.from_user.id
            user_info = await get_user_role_and_ban_info(session, user_id)

            if user_info.user_role != 'admin':
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                not_admin_message = await get_translation(user_id, "admin", "no_access")
                message_sent = await bot.send_message(
                    chat_id=message.chat.id,
                    text=not_admin_message,
                )
                await asyncio.sleep(1)
                await bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message_sent.message_id,
                )

                await send_menu_handler(message)
                return False

            return True
