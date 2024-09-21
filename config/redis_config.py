import os

from dotenv import load_dotenv
from redis.asyncio import ConnectionPool, Redis

from bot.bot_config import logger

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def create_redis_pool():
    """Creating and configuring the Redis pool"""
    try:
        pool = ConnectionPool.from_url(REDIS_URL)
        redis_client = Redis(connection_pool=pool)
        logger.info("✅ Redis client connected successfully")
        return redis_client
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        raise


async def close_redis_pool(redis_client):
    """Closing a Redis pool"""
    if redis_client:
        try:
            await redis_client.aclose()
            logger.info("📁 Redis connection closed successfully")
        except Exception as e:
            logger.error(f"❌ Failed to close Redis connection: {e}")
