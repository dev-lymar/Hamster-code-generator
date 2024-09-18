import redis

redis_client = redis.StrictRedis(
    host='localhost',
    port=6379,
    decode_responses=True
)

try:
    redis_client.ping()
    print("Successfully connected to Redis!")
except redis.ConnectionError:
    print("Could not connect to Redis.")
