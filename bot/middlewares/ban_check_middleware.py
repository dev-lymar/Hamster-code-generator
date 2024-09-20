from aiogram import BaseMiddleware, types
from aiogram.types import Update

from bot.database.database import get_user_status_info
from bot.handlers.handlers import banned_user_handler
from db.database import get_session


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        # Check if the event is a callback request
        if isinstance(event.callback_query, types.CallbackQuery):
            user_id = event.callback_query.from_user.id

            # Ban check
            async with await get_session() as session:
                user_info = await get_user_status_info(session, user_id)
                if user_info and user_info.is_banned:
                    await banned_user_handler(event.callback_query.message)
                    return

        # Check if the event is a command
        elif isinstance(event.message, types.Message) and event.message.text.startswith('/'):
            user_id = event.message.from_user.id

            # Ban check
            async with await get_session() as session:
                user_info = await get_user_status_info(session, user_id)
                if user_info and user_info.is_banned:
                    await banned_user_handler(event.message)
                    return

        return await handler(event, data)
