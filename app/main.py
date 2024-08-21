import asyncio
from game_promo_manager import create_table_for_game, gen, create_database, logger
from games import games
from urllib.parse import urlparse


async def safe_gen(game):
    conn = create_database()
    create_table_for_game(conn, game['name'])
    conn.close()

    while True:
        try:
            await gen(game)
        except Exception as error:
            parsed_url = urlparse(f"http://{game['proxy']}")
            ip = parsed_url.hostname
            port = parsed_url.port

            logger.error(f"--GAME ERROR-- {game['name']} proxy: {ip}:{port} - {error}")
            logger.info(f"Restarting task for the game {game['name']} proxy: {ip}:{port}...")
            await asyncio.sleep(1)


async def run_all_games():
    tasks = [safe_gen(game) for game in games]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run_all_games())
