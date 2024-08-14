import asyncio
import os
import random
import time
import sqlite3
import uuid
import httpx
from loguru import logger

# converting milliseconds to seconds
EVENTS_DELAY = 20000 / 1000


def create_database(db_name="hamster.db"):
    conn = sqlite3.connect(db_name)
    return conn


def create_table_for_game(conn, game_name):
    table_name = game_name.replace(" ", "_").lower()
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            promo_code TEXT,
            created_at TIMEsTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


async def load_proxies(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                proxies = [line.strip() for line in file if line.strip()]
                random.shuffle(proxies)
                if proxies:
                    return proxies
                else:
                    logger.info(f"Proxy file {file_path} is empty. Using system's IP.")
                    return [None]
        else:
            logger.info(f"Proxy file {file_path} not found. Using system's IP.")
            return [None]
    except Exception as e:
        logger.error(f"Error reading proxy file {file_path}: {e}")
        return [None]


async def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_numbers = ''.join(str(random.randint(0, 9)) for _ in range(19))
    return f"{timestamp}-{random_numbers}"


async def login(client_id, app_token, proxies, retries=5):
    for attempt in range(retries):
        proxy = random.choice(proxies) if proxies else None
        async with httpx.AsyncClient(proxies={"http://": proxy, "https://": proxy} if proxy else None) as client:
            try:
                response = await client.post(
                    'https://api.gamepromo.io/promo/login-client',
                    json={'appToken': app_token, 'clientId': client_id, 'clientOrigin': 'deviceid'}
                )
                response.raise_for_status()
                data = response.json()
                return data['clientToken']
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to login (attempt {attempt + 1}/{retries}): {e.response.json()}")
            except Exception as e:
                logger.error(f"Unexpected error during login (attempt {attempt + 1}/{retries}): {e}")
        await asyncio.sleep(2)  # Delay before retrying
    logger.error("Maximum login attempts reached. Returning None.")
    return None


async def emulate_progress(client_token, promo_id, proxies):
    proxy = random.choice(proxies) if proxies else None
    async with httpx.AsyncClient(proxies={"http://": proxy, "https://": proxy} if proxy else None) as client:
        response = await client.post(
            'https://api.gamepromo.io/promo/register-event',
            headers={'Authorization': f'Bearer {client_token}'},
            json={'promoId': promo_id, 'eventId': str(uuid.uuid4()), 'eventOrigin': 'undefined'}
        )
        response.raise_for_status()
        data = response.json()
        return data['hasCode']


async def generate_key(client_token, promo_id, proxies):
    proxy = random.choice(proxies) if proxies else None
    async with httpx.AsyncClient(proxies={"http://": proxy, "https://": proxy} if proxy else None, timeout=20.0) as client:
        response = await client.post(
            'https://api.gamepromo.io/promo/create-code',
            headers={'Authorization': f'Bearer {client_token}'},
            json={'promoId': promo_id}
        )
        response.raise_for_status()
        data = response.json()
        return data['promoCode']


async def generate_key_process(app_token, promo_id, proxies):
    client_id = await generate_client_id()
    client_token = await login(client_id, app_token, proxies)
    if not client_token:
        return None

    for _ in range(4):
        await asyncio.sleep(EVENTS_DELAY * (random.random() / 3 + 1))
        try:
            has_code = await emulate_progress(client_token, promo_id, proxies)
        except httpx.HTTPStatusError:
            continue

        if has_code:
            break

    try:
        key = await generate_key(client_token, promo_id, proxies)
        return key
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to generate key: {e.response.json()}")
        return None


async def main(game_choice, proxy_file):
    proxies = await load_proxies(proxy_file)
    game = {
        1: {
            'name': 'Riding Extreme 3D',
            'appToken': 'd28721be-fd2d-4b45-869e-9f253b554e50',
            'promoId': '43e35910-c168-4634-ad4f-52fd764a843f',
        },
        2: {
            'name': 'Chain Cube 2048',
            'appToken': 'd1690a07-3780-4068-810f-9b5bbf2931b2',
            'promoId': 'b4170868-cef0-424f-8eb9-be0622e8e8e3',
        },
        3: {
            'name': 'My Clone Army',
            'appToken': '74ee0b5b-775e-4bee-974f-63e7f4d5bacb',
            'promoId': 'fe693b26-b342-4159-8808-15e3ff7f8767',
        },
        4: {
            'name': 'Train Miner',
            'appToken': '82647f43-3f87-402d-88dd-09a90025313f',
            'promoId': 'c4480ac7-e178-4973-8061-9ed5b2e17954',
        }
    }[game_choice]

    conn = create_database()
    try:
        create_table_for_game(conn, game['name'])

        cursor = conn.cursor()
        table_name = game['name'].replace(" ", "_").lower()

        while True:
            key = await generate_key_process(game['appToken'], game['promoId'], proxies)
            if key:
                cursor.execute(f"INSERT INTO {table_name} (promo_code) VALUES (?)", (key,))
                conn.commit()
                print(f"Generated key: {key} (saved to {table_name} table)")
            else:
                print("Failed to generate key.")
    finally:
        conn.close()


if __name__ == "__main__":
    print("Select a game:")
    for key, value in {
        1: 'Riding Extreme 3D',
        2: 'Chain Cube 2048',
        3: 'My Clone Army',
        4: 'Train Miner'
    }.items():
        print(f"{key}: {value}")

    game_choice = int(input("Enter the game number: "))
    proxy_file = "proxies.txt"

    asyncio.run(main(game_choice, proxy_file))
