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

# Supported languages
SUPPORTED_LANGUAGES = ['ru', 'sk', 'en', 'uk']

GAMES = [
    'Zoopolis',
    # 'Gangs Wars',
    # 'Cafe Dash',
    'Mow and Trim',
    'Chain Cube 2048',
    'Train Miner',
    'Merge Away',
    'Twerk Race 3D',
    'Polysphere',
    # 'Tile Trio',
    'Fluff Crusade',
]

STATUS_LIMITS = {
    'free': {'daily_limit': 5, 'interval_minutes': 10},
    'friend': {'daily_limit': 15, 'interval_minutes': 10},
    'premium': {
        'daily_limit': 5, 'interval_minutes': 10,
        'safety_daily_limit': 2, 'safety_interval_minutes': 360
    }
}

# Forwarding message to group
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))


async def set_commands(bot: Bot, user_id: int, language_code: str):
    start_command_description = translations[language_code]["get_keys_key"]
    change_lang_command_description = translations[language_code]["choose_language"]
    admin_command_description = translations[language_code]["admin_command_description"]

    commands = [
        BotCommand(command="/start", description=start_command_description),
        BotCommand(command="/change_lang", description=change_lang_command_description),
        BotCommand(command="/admin", description=admin_command_description)
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user_id))
