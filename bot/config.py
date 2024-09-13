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
    '🏠 City Holder': 'https://t.me/cityholder/game?startapp=452792586',
    '🤖 TapSwap': 'https://t.me/tapswap_mirror_2_bot?start=r_452792586',
    '⭐ Major': 'https://t.me/major/start?startapp=452792586',
    '🪙 Blum': 'https://t.me/blum/app?startapp=ref_8U6nYohQav',
    '🐸 Frog Trader': 'https://t.me/xkucoinbot/kucoinminiapp?startapp'
                     '=cm91dGU9JTJGdGFwLWdhbWUlM0ZpbnZpdGVyVXNlcklkJTNENDUyNzkyNTg2JTI2cmNvZGUlM0Q=',
    '🔥 HOT Wallet': 'https://t.me/herewalletbot/app?startapp=9477477'
}

STATUSES = {
    "free": "🎮 <b>Обычный игрок</b> — Получай ключи и открывай двери, чтобы стать сильнее. 🚀",
    "friend": "🤝 <b>Друг проекта</b> — Тебе доступны эксклюзивные возможности, но впереди ещё больше! 🔥",
    "premium": "👑 <b>Элитный игрок!</b> Используй все свои привилегии и наслаждайся эксклюзивным контентом. ✨",
}

ACHIEVEMENTS = {
    "newcomer":
        "🌱 <b>Новичок</b> — <i>Ты только начал свой путь! Продолжай, впереди много возможностей!</i> 🚀",
    "key_seeker":
        "🔑 <b>Искатель ключей</b> — <i>Ты уже открыл несколько дверей, но впереди ждут более ценные ключи.</i> 💎",
    "bonus_hunter":
        "🎯 <b>Охотник за бонусами</b> — <i>С каждым новым ключом ты становишься сильнее. Открывай бонусы!</i> 🎁",
    "code_expert":
        "🧠 <b>Знаток кодов</b> — <i>Ты уже знаешь, как работает система. Продолжай улучшаться!</i> 📈",
    "key_master":
        "🏆 <b>Мастер ключей</b> — <i>Твои навыки восхищают! Достигай новых вершин!</i> 🗝️",
    "elite_player":
        "🚀 <b>Элитный игрок</b> — <i>Ты среди лучших. Элитные ключи открывают перед тобой новые возможности!</i> 💥",
    "game_legend":
        "🌟 <b>Легенда игр</b> — <i>Ты достиг почти всего! Оставайся в топе и собери все ключи!</i> 🏅",
    "absolute_leader":
        "👑 <b>Абсолютный лидер</b> — <i>Ты на вершине! Все ключи в твоем распоряжении, и ты пример для всех!</i> 🌍",
}


GAMES = [
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

# Forwarding message to group
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))


async def set_commands(bot: Bot, user_id: int, language_code: str):
    start_command_description = translations[language_code]["get_keys_key"]
    change_lang_command_description = translations[language_code]["choose_language"]
    admin_command_description = translations[language_code]["admin_command_description"]

    commands = [
        BotCommand(command="/start", description=start_command_description),
        BotCommand(command="/change_lang", description=change_lang_command_description),
        BotCommand(command="/admin", description=admin_command_description),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user_id))
