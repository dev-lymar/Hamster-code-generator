from aiogram import BaseMiddleware, types
from aiogram.types import Update
from database.database import get_user_status_info, get_session
from handlers.handlers import handle_banned_user


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        # Check if the event is a callback request
        if isinstance(event.callback_query, types.CallbackQuery):
            user_id = event.callback_query.from_user.id

            # Ban check
            async with await get_session() as session:
                user_info = await get_user_status_info(session, user_id)
                if user_info.is_banned:
                    await handle_banned_user(event.callback_query.message)
                    return

        # Check if the event is a command
        elif isinstance(event.message, types.Message) and event.message.text.startswith('/'):
            user_id = event.message.from_user.id

            # Ban check
            async with await get_session() as session:
                user_info = await get_user_status_info(session, user_id)
                if user_info.is_banned:
                    await handle_banned_user(event.message)
                    return

        return await handler(event, data)
