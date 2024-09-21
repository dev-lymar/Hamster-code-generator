import os

from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from config.logging_config import logging_setup

logger = logging_setup('app', 'app.log')

load_dotenv()


# Forwarding message to groups
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", 0))

API_TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = int(API_TOKEN.split(':')[0])
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
