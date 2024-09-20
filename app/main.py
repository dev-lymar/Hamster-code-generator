import asyncio

from app.game_promo_manager import gen
from app.games import games


async def run_all_games():
    tasks = [gen(game) for game in games]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(run_all_games())
