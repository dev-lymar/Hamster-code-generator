import asyncio

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from bot.bot_config import bot, logger
from bot.handlers import register_handlers
from bot.middlewares.ban_check_middleware import BanCheckMiddleware
from config.redis_config import redis_manager


async def main():
    client = await redis_manager.get_client()
    try:
        logger.info("✅ | Starting the bot and initialising the Redis")

        dp = Dispatcher(storage=RedisStorage(client, state_ttl=600))

        dp.update.middleware(BanCheckMiddleware())
        register_handlers(dp)

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    finally:
        logger.info("📁 Closing the database and Redis connections")
        await redis_manager.close()

if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        loop.run_until_complete(loop.shutdown_asyncgens())
    except KeyboardInterrupt:
        logger.info("🛑 | Bot application is terminated by the `Ctrl+C` signal")
    finally:
        logger.info("🏁 | Bot application stopped!")
