import asyncio
import logging
from config import bot, setup_dispatcher
from database.database import init_db, close_db
from handlers import register_handlers
from middlewares.ban_check_middleware import BanCheckMiddleware


async def main():
    await init_db()
    try:
        dp = await setup_dispatcher()
        logging.info("✅ | Starting the bot and initialising the database")
        dp.update.middleware(BanCheckMiddleware())
        register_handlers(dp)
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
