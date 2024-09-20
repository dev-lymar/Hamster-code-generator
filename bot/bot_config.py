import os

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv

from config.logging_config import logging_setup

logger = logging_setup('app', 'app.log')

load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')

BOT_ID = int(API_TOKEN.split(':')[0])

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))


async def setup_dispatcher(redis_client):
    storage = RedisStorage(redis=redis_client, state_ttl=600)
    dp = Dispatcher(storage=storage)
    return dp


# Forwarding message to groups
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))
