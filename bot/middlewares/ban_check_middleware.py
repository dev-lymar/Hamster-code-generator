from aiogram import BaseMiddleware, types
from aiogram.types import Update
from database.database import get_user_status_info, get_session
from handlers.handlers import handle_banned_user


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        # Проверка, является ли событие callback-запросом
        if isinstance(event.callback_query, types.CallbackQuery):
            user_id = event.callback_query.from_user.id

            # Проверка на бан
            async with await get_session() as session:
                user_info = await get_user_status_info(session, user_id)
                if user_info.is_banned:
                    await handle_banned_user(event.callback_query.message)  # Обрабатываем как сообщение
                    return  # Останавливаем обработку события

        # Проверка, является ли событие командой
        elif isinstance(event.message, types.Message) and event.message.text.startswith('/'):
            user_id = event.message.from_user.id

            # Проверка на бан
            async with await get_session() as session:
                user_info = await get_user_status_info(session, user_id)
                if user_info.is_banned:
                    await handle_banned_user(event.message)  # Обрабатываем команду как сообщение
                    return  # Останавливаем обработку события

        # Если событие не callback-запрос или команда, либо пользователь не забанен, передаем обработку дальше
        return await handler(event, data)
