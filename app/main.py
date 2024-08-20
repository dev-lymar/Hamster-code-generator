import asyncio
from game_promo_manager import create_table_for_game, gen, create_database, logger
from games import games


async def safe_gen(game):
    conn = create_database()
    create_table_for_game(conn, game['name'])
    conn.close()

    while True:
        try:
            await gen(game)
        except Exception as error:
            logger.error(f"Ошибка в игре {game['name']} с прокси {game['proxy']['url']}: {error}")
            logger.info(f"Перезапуск задачи для игры {game['name']} с прокси {game['proxy']['url']}...")
            await asyncio.sleep(1)


async def run_all_games():
    tasks = [safe_gen(game) for game in games]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run_all_games())
