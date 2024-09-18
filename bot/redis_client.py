import os
from dotenv import load_dotenv

import redis.asyncio as redis

load_dotenv()

# Configuring the Redis client
redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=os.getenv('REDIS_PORT', 6379),
    decode_responses=True
)
