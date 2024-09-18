import os

import redis.asyncio as redis
import logging
from dotenv import load_dotenv

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
        logging.info("✅ Redis client connected successfully")
        return client
    except Exception as e:
        logging.error(f"❌ Failed to connect to Redis: {e}")
        raise
