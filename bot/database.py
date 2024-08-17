import os
from datetime import date
import psycopg2

from dotenv import load_dotenv

load_dotenv()

# DB Connection Details
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")


# Creates and returns a database connection.
def create_database_connection():
    conn = psycopg2.connect(
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT
    )
    return conn


# Creates the users table if it does not exist.
def create_table_users(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL UNIQUE,
            user_id BIGINT NOT NULL UNIQUE,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            username VARCHAR(100),
            language_code VARCHAR(10),
            is_banned BOOLEAN DEFAULT FALSE,
            user_status VARCHAR(20) DEFAULT 'free',
            daily_keys_generated INTEGER DEFAULT 0,
            last_reset_date DATE DEFAULT CURRENT_DATE,
            last_generated_data TIMESTAMPTZ DEFAULT NOW(),
            total_keys_generated INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    cursor.close()


# Creates the user_logs table if it does not exist.
def create_table_logs(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            action TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    conn.commit()
    cursor.close()


# Adds new user to the database
def add_user(conn, chat_id, user_id, first_name, last_name, username, language_code):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (chat_id, user_id, first_name, last_name, username, language_code)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    ''', (chat_id, user_id, first_name, last_name, username, language_code))
    conn.commit()
    cursor.close()


# Get user language
def get_user_language(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT language_code FROM users WHERE user_id = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else "ru"


# Updates user language in the database
def update_user_language(conn, user_id, language_code):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET language_code = %s WHERE user_id = %s
    ''', (language_code, user_id))
    conn.commit()
    cursor.close()


# Resets daily keys if needed
def reset_daily_keys_if_needed(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT last_reset_date FROM users WHERE user_id = %s
    ''', (user_id,))
    result = cursor.fetchone()

    if result is None:
        # Если пользователь не найден, просто пропускаем (либо можно обработать это как ошибку)
        cursor.close()
        return

    last_reset_date = result[0]

    if last_reset_date != date.today():
        cursor.execute('''
            UPDATE users
            SET daily_keys_generated = 0, last_reset_date = CURRENT_DATE
            WHERE user_id = %s
        ''', (user_id,))
        conn.commit()
    cursor.close()


# Checks if the user is banned
def is_user_banned(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT is_banned FROM users WHERE user_id = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else False


# Logs user action
def log_user_action(conn, user_id, action):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_logs (user_id, action)
        VALUES (%s, %s)
    ''', (user_id, action))
    conn.commit()
    cursor.close()
