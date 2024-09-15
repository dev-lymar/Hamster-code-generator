from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from utils import get_translation


async def set_user_commands(bot: Bot, user_id: int):
    # Получаем переводы команд на основе языка пользователя
    start_bot_desc = await get_translation(user_id, "commands", "start_bot")
    change_language_desc = await get_translation(user_id, "commands", "change_language")
    admin_panel_desc = await get_translation(user_id, "commands", "admin_panel")

    # Создаем список команд
    commands = [
        BotCommand(command="/start", description=start_bot_desc),
        BotCommand(command="/change_lang", description=change_language_desc),
        BotCommand(command="/admin", description=admin_panel_desc),
    ]

    # Устанавливаем команды для пользователя на основе его языка
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user_id))
