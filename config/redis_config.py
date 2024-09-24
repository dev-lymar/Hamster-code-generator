import os

from dotenv import load_dotenv
from redis.asyncio import ConnectionPool, Redis

from bot.bot_config import logger

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisClientManager:
    def __init__(self, url):
        self.connection_pool = ConnectionPool.from_url(url)
        self.redis_client = Redis(connection_pool=self.connection_pool)
        logger.info("✅ Redis client initialized")

    async def get_client(self):
        return self.redis_client

    async def close(self):
        await self.connection_pool.disconnect()
        logger.info("📁 Redis connection closed successfully")


redis_manager = RedisClientManager(REDIS_URL)
