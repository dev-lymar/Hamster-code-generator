import os
from datetime import datetime, timezone, timedelta
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# DB Connection Details
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")


# Creates and returns a database connection.
async def create_database_connection():
    try:
        return await asyncpg.connect(
            database=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise


# Centralized query execution function
async def execute_query(conn, query, params=None, fetch_one=False):
    async with conn.transaction():
        if params is None:
            params = []
        if fetch_one:
            return await conn.fetchrow(query, *params)
        else:
            return await conn.execute(query, *params)


# Creates the users table if it does not exist.
async def create_table_users(conn):
    query = '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL UNIQUE,
            user_id BIGINT NOT NULL UNIQUE,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            username VARCHAR(100),
            registration_date TIMESTAMPTZ DEFAULT NOW(),
            language_code VARCHAR(10),
            preferred_currency VARCHAR(3),
            is_banned BOOLEAN DEFAULT FALSE,
            user_status VARCHAR(20) DEFAULT 'free',
            user_role VARCHAR(20) DEFAULT 'user',
            referral_code VARCHAR(50),
            referred_by VARCHAR(50),
            is_subscribed BOOLEAN DEFAULT TRUE,
            daily_requests_count INTEGER DEFAULT 0,
            last_reset_date DATE DEFAULT CURRENT_DATE,
            last_request_time TIMESTAMPTZ NULL,
            total_keys_generated INTEGER DEFAULT 0,
            notes TEXT
        )
    '''
    await execute_query(conn, query)


# Creates the user_logs table if it does not exist.
async def create_table_logs(conn):
    query = '''
        CREATE TABLE IF NOT EXISTS user_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            action TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
    '''
    await execute_query(conn, query)


# Adds new user to the database
async def add_user(conn, chat_id, user_id, first_name, last_name, username, language_code):
    query = '''
        INSERT INTO users (chat_id, user_id, first_name, last_name, username, language_code)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (user_id) DO NOTHING
    '''
    await execute_query(conn, query, (chat_id, user_id, first_name, last_name, username, language_code))


# Get user language
async def get_user_language(conn, user_id):
    query = '''
        SELECT language_code FROM users WHERE user_id = $1
    '''
    result = await execute_query(conn, query, (user_id,), fetch_one=True)
    return result['language_code'] if result else "en"


# Updates user language in the database
async def update_user_language(conn, user_id, language_code):
    query = '''
        UPDATE users SET language_code = $1 WHERE user_id = $2
    '''
    await execute_query(conn, query, (language_code, user_id))


# Resets daily keys if needed
async def reset_daily_keys_if_needed(conn, user_id):
    query = '''
        SELECT last_reset_date FROM users WHERE user_id = $1
    '''
    result = await execute_query(conn, query, (user_id,), fetch_one=True)

    if result is None:
        return

    last_reset_date = result['last_reset_date']
    current_date = datetime.now(timezone.utc).date()

    if last_reset_date != current_date:
        # Update the reset date and reset the key counter
        update_query = '''
            UPDATE users
            SET daily_requests_count = 0, last_reset_date = $1
            WHERE user_id = $2
        '''
        await execute_query(conn, update_query, (current_date, user_id))


# Checks if the user is banned
async def is_user_banned(conn, user_id):
    query = '''
        SELECT is_banned FROM users WHERE user_id = $1
    '''
    result = await execute_query(conn, query, (user_id,), fetch_one=True)
    return result['is_banned'] if result else False


# Logs user action
async def log_user_action(conn, user_id, action):
    query = '''
        INSERT INTO user_logs (user_id, action)
        VALUES ($1, $2)
    '''
    await execute_query(conn, query, (user_id, action))


# Getting oldest keys for the game
async def get_oldest_keys(conn, game_name, limit=4):
    table_name = game_name.replace(" ", "_").lower()
    query = f"SELECT promo_code FROM {table_name} ORDER BY created_at ASC LIMIT $1"
    result = await conn.fetch(query, limit)
    return result


# Deleting used keys
async def delete_keys(conn, game_name, keys):
    table_name = game_name.replace(" ", "_").lower()
    query = f"DELETE FROM {table_name} WHERE promo_code = ANY($1)"
    await conn.execute(query, keys)


# Update key count and time of the last request
async def update_keys_generated(conn, user_id, keys_generated):
    current_date = datetime.now(timezone.utc).date()
    query = '''
        UPDATE users
        SET total_keys_generated = total_keys_generated + $1,
            daily_requests_count = daily_requests_count + 1,
            last_request_time = NOW(),
            last_reset_date = $2
        WHERE user_id = $3
    '''
    await execute_query(conn, query, (keys_generated, current_date, user_id))


# Check user limits
async def check_user_limits(conn, user_id, status_limits):
    query = '''
        SELECT user_status, daily_requests_count, last_reset_date
        FROM users WHERE user_id = $1
    '''
    result = await execute_query(conn, query, (user_id,), fetch_one=True)

    if result:
        user_status = result['user_status']
        daily_requests_count = result['daily_requests_count']
        last_reset_date = result['last_reset_date']
        current_date = datetime.now(timezone.utc).date()

        # Update data if a new day has passed
        if last_reset_date != current_date:
            await reset_daily_keys_if_needed(conn, user_id)
            daily_requests_count = 0

        # Checking limits by user status
        limit = status_limits[user_status]['daily_limit']
        if daily_requests_count >= limit:
            return False  # The limit has been reached
    return True  # The limit has not been reached


# Getting the time of the last request and user status
async def get_last_request_time(conn, user_id):
    query = '''
        SELECT last_request_time, user_status 
        FROM users 
        WHERE user_id = $1
    '''
    return await execute_query(conn, query, (user_id,), fetch_one=True)


# Calculation of the remaining time until the next request
def get_remaining_time(last_request_time, interval_minutes):
    if last_request_time is None:
        return 0, 0  # If no requests have been made yet, return 0

    now = datetime.now(timezone.utc)
    elapsed_time = now - last_request_time
    remaining_time = timedelta(minutes=interval_minutes) - elapsed_time

    if remaining_time.total_seconds() > 0:
        minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
        return minutes, seconds
    return 0, 0  # If the waiting time has elapsed, return 0
