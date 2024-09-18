import asyncio
import logging
from config import bot, setup_dispatcher
from database.database import init_db, close_db
from redis_client import create_redis_client, close_redis_client
from handlers import register_handlers
from middlewares.ban_check_middleware import BanCheckMiddleware


async def main():
    await init_db()
    redis_client = await create_redis_client()
    try:
        dp = await setup_dispatcher(redis_client)
        logging.info("✅ | Starting the bot and initialising the database")
        dp.update.middleware(BanCheckMiddleware())
        register_handlers(dp)
        await dp.start_polling(bot)
    finally:
        logging.info("📁 Closing the database and Redis connections")
        await close_db()
        await close_redis_client(redis_client)

if __name__ == '__main__':
    try:
        logging.info("✅ | Starting bot application")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        loop.run_until_complete(loop.shutdown_asyncgens())
    except KeyboardInterrupt:
        logging.info("🛑 | Bot application is terminated by the Ctrl+C signal")
    finally:
        logging.info("🏁 | Bot application stopped!")
