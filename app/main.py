import asyncio
import multiprocessing
from promo_functions import create_table_for_game, gen, create_database
from games import games


async def safe_gen(game):
    # Create a table if it does not exist
    conn = create_database()
    create_table_for_game(conn, game['name'])
    conn.close()  # Close the connection after creating a table

    while True:
        try:
            await gen(game)
        except Exception as error:
            print(f"Ошибка в игре {game['name']}: {error}")
            print(f"Перезапуск задачи для игры {game['name']}...")
            await asyncio.sleep(1)  # Delay before restarting


def start_game_process(game):
    print(f"Запуск процесса для игры {game['name']}")
    asyncio.run(safe_gen(game))


if __name__ == "__main__":
    processes = []
    for game in games:
        p = multiprocessing.Process(target=start_game_process, args=(game,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
