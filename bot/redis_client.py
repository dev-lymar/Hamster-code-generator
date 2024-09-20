import os

import redis.asyncio as redis
from dotenv import load_dotenv

from bot.bot_config import logger

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = os.getenv("REDIS_DB", 0)


def create_redis_client():
    """Creating and configuring the Redis client"""
    try:
        client = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        logger.info("✅ Redis client connected successfully")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        raise


async def close_redis_client(redis_client):
    """Closing a Redis client"""
    if redis_client:
        await redis_client.close()
        logger.info("📁 Redis connection closed")
