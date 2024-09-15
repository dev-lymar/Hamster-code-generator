import os
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()


API_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = int(API_TOKEN.split(':')[0])
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Supported languages
SUPPORTED_LANGUAGES = ['en', 'ru', 'uk', 'sk', 'es', 'fr', 'tr', 'ar', 'de', 'fa', 'ur', 'hi']

REFERRAL_LINKS = {
    'Cats 🐈‍⬛': 'https://t.me/catsgang_bot/join?startapp=Lv39AXNhcBvwK6ZWcoGpD',
    '🅧 X Empire': 't.me/empirebot/game?startapp=hero452792586',
    '🥠 Hrum': 't.me/hrummebot/game?startapp=ref452792586',
    '😺 Catizen': 'https://t.me/catizenbot/gameapp?startapp=r_2779_5703457',
    '🏠 CITY Holder': 'https://t.me/cityholder/game?startapp=452792586',
    '🤖 TapSwap': 'https://t.me/tapswap_mirror_2_bot?start=r_452792586',
    '⚫️ DotCoin': 'https://t.me/dotcoin_bot?start=r_452792586',
    '⭐ Major': 'https://t.me/major/start?startapp=452792586',
    '🪙 Blum': 'https://t.me/blum/app?startapp=ref_8U6nYohQav',
    '🐸 Frog Trader': 'https://t.me/xkucoinbot/kucoinminiapp?startapp'
                     '=cm91dGU9JTJGdGFwLWdhbWUlM0ZpbnZpdGVyVXNlcklkJTNENDUyNzkyNTg2JTI2cmNvZGUlM0Q=',
    '🔥 HOT Wallet': 'https://t.me/herewalletbot/app?startapp=9477477'
}


ACHIEVEMENTS = [
    "newcomer", "key_seeker",
    "bonus_hunter", "code_expert",
    "key_master", "elite_player",
    "game_legend", "absolute_leader"
]


GAMES = [
    'Hide Ball',
    'Bouncemasters',
    'Merge Away',
    'Stone Age',
    'Train Miner',
    'Mow and Trim',
    'Chain Cube 2048',
    'Fluff Crusade',
    'Polysphere',
    'Twerk Race 3D',
    'Zoopolis',
    'Tile Trio',
]

STATUS_LIMITS = {
    'free': {'daily_limit': 2, 'interval_minutes': 10},
    'friend': {'daily_limit': 5, 'interval_minutes': 10},
    'premium': {
        'daily_limit': 4, 'interval_minutes': 10,
        'safety_daily_limit': 2, 'safety_interval_minutes': 240
    }
}

# Forwarding message to group§
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))
