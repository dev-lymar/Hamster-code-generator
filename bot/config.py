import os
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from utils.helpers import load_translations


load_dotenv()

translations = load_translations()

API_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = int(API_TOKEN.split(':')[0])
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Supported languages
SUPPORTED_LANGUAGES = ['ru', 'sk', 'en', 'uk', 'es', 'fr', 'tr', 'ar']

REFERRAL_LINKS = {
    'Cats 🐈‍⬛': 'https://t.me/catsgang_bot/join?startapp=Lv39AXNhcBvwK6ZWcoGpD',
    '😺 Catizen': 'https://t.me/catizenbot/gameapp?startapp=r_2779_5703457',
    '🏠 City Holder': 'https://t.me/blum/app?startapp=ref_8U6nYohQav',
    '🤖 TapSwap': 'https://t.me/tapswap_mirror_2_bot?start=r_452792586',
    '⭐ Major': 'https://t.me/major/start?startapp=452792586',
    '🪙 Blum': 'https://t.me/cityholder/game?startapp=452792586',
    '🐸 Frog Trader': 'https://t.me/xkucoinbot/kucoinminiapp?startapp'
                     '=cm91dGU9JTJGdGFwLWdhbWUlM0ZpbnZpdGVyVXNlcklkJTNENDUyNzkyNTg2JTI2cmNvZGUlM0Q=',
    '🔥 HOT Wallet': 'https://t.me/herewalletbot/app?startapp=9477477'
}


GAMES = [
    'Stone Age',
    'Fluff Crusade',
    'Tile Trio',
    'Mow and Trim',
    'Train Miner',
    'Chain Cube 2048',
    'Merge Away',
    'Zoopolis',
    'Twerk Race 3D',
    'Polysphere',
]

STATUS_LIMITS = {
    'free': {'daily_limit': 3, 'interval_minutes': 10},
    'friend': {'daily_limit': 15, 'interval_minutes': 10},
    'premium': {
        'daily_limit': 5, 'interval_minutes': 10,
        'safety_daily_limit': 2, 'safety_interval_minutes': 120
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
