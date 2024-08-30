import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from utils.helpers import load_translations


load_dotenv()

translations = load_translations()

API_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = int(API_TOKEN.split(':')[0])
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

games = [
    'Train Miner',
    'Chain Cube 2048',
    'Merge Away',
    'Twerk Race 3D',
    'Polysphere',
    'Mow and Trim',
    'Cafe Dash',
    'Zoopolis',
    'Gangs Wars'
]

status_limits = {
    'free': {'daily_limit': 5, 'interval_minutes': 10},
    'friend': {'daily_limit': 15, 'interval_minutes': 10},
    'premium': {'daily_limit': 50, 'interval_minutes': 10}
}

# Forwarding message to group
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))


async def set_commands(bot: Bot, user_id: int, language_code: str):
    command_description = translations[language_code]["choose_language"]

    commands = [
        BotCommand(command="/change_lang", description=command_description)
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user_id))
