import asyncio
import logging.handlers
import os
from config import bot, dp
from database.database import init_db, close_db
from handlers import handlers  # noqa: F401
from handlers.payment import payment_router

# Set up logging configuration
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, 'game_promo.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
    ]
)
# Reduce the logging level of SQLAlchemy to WARNING
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

dp.include_router(payment_router)


async def main():
    await init_db()
    try:
        logging.info("✅ | Starting the bot and initialising the database")
        await dp.start_polling(bot)
    finally:
        logging.info("📁 Closing the database connection")
        await close_db()

if __name__ == '__main__':
    try:
        logging.info("✅ | Starting bot application")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 | Bot application is terminated by the Ctrl+C signal")
    finally:
        logging.info("🏁 | Bot application stopped!")
