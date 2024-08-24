import asyncio
import logging.handlers
import os
from config import bot, dp
from database.database import create_database_connection, create_table_users, create_table_logs
import handlers.handlers

# Set up logging configuration
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, 'game_promo.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
    ]
)


async def main():
    conn = await create_database_connection()
    try:
        await create_table_users(conn)
        await create_table_logs(conn)
    finally:
        await conn.close()

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
