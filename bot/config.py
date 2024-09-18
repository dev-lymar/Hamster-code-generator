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


# Forwarding message to group§
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))
