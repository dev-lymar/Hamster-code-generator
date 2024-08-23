import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = int(API_TOKEN.split(':')[0])
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

games = [
    'Bike Ride 3D',
    'Train Miner',
    'Chain Cube 2048',
    'My Clone Army',
    'Merge Away',
    'Twerk Race 3D',
    'Polysphere',
    'Mud Racing',
    'Mow and Trim'
]

status_limits = {
    'free': {'daily_limit': 10, 'interval_minutes': 10},
    'friend': {'daily_limit': 25, 'interval_minutes': 10},
    'premium': {'daily_limit': 50, 'interval_minutes': 10}
}


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/change_lang", description="Change language / Сменить язык")
    ]
    await bot.set_my_commands(commands)
