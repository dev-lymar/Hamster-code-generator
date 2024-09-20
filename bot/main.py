import asyncio

from bot.bot_config import bot, logger, setup_dispatcher
from bot.database.database import close_db, init_db
from bot.handlers import register_handlers
from bot.middlewares.ban_check_middleware import BanCheckMiddleware
from bot.redis_client import close_redis_client, create_redis_client


async def main():
    await init_db()
    redis_client = await create_redis_client()
    try:
        dp = await setup_dispatcher(redis_client)
        logger.info("✅ | Starting the bot and initialising the database")
        dp.update.middleware(BanCheckMiddleware())
        register_handlers(dp)
        await dp.start_polling(bot)
    finally:
        logger.info("📁 Closing the database and Redis connections")
        await close_db()
        await close_redis_client(redis_client)

if __name__ == '__main__':
    try:
        logger.info("✅ | Starting `bot` application")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        loop.run_until_complete(loop.shutdown_asyncgens())
    except KeyboardInterrupt:
        logger.info("🛑 | Bot application is terminated by the `Ctrl+C` signal")
    finally:
        logger.info("🏁 | Bot application stopped!")
