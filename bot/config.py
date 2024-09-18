import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv
from redis_client import create_redis_client

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


# Set up logging configuration
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, 'game_promo.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
# Reduce the logging level of SQLAlchemy to WARNING
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
