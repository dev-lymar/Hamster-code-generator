import os
import psycopg2
from psycopg2 import sql

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
    table_name = "users"
    cursor = conn.cursor()
    cursor.execute(sql.SQL('''
        CREATE TABLE IF NOT EXISTS {} (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL UNIQUE,
            user_id BIGINT NOT NULL UNIQUE,
            first_name VARChAR(100),
            last_name VARCHAR(100),
            username VARCHAR(100),
            language VARCHAR(10),
            last_generated_data TIMESTAMPTZ DEFAULT NOW()
            total_keys_generated INTEGER DEFAULT 0
        )
    ''').format(sql.Identifier(table_name)))
    conn.commit()
