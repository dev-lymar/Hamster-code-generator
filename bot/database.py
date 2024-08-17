import os
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
            last_generated_data TIMESTAMPTZ DEFAULT NOW(),
            total_keys_generated INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    cursor.close()


# Added new user to the database
def add_user(conn, chat_id, user_id, first_name, last_name, username, language_code):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (chat_id, user_id, first_name, last_name, username, language_code)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    ''', (chat_id, user_id, first_name, last_name, username, language_code))
    conn.commit()
    cursor.close()


# Update user language in the database
def update_user_language(conn, user_id, language_code):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET language_code = %s WHERE user_id = %s
    ''', (language_code, user_id))
    conn.commit()
    cursor.close()
