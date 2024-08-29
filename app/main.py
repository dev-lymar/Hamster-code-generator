import asyncio
from game_promo_manager import gen
from games import games
from database import init_db


async def run_all_games():
    await init_db()  # Creating tables before starting work
    tasks = [gen(game) for game in games]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(run_all_games())
