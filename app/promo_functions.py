import asyncio
import aiohttp
import time
import random
import uuid
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

load_dotenv()

# DB
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")


# Connecting to PostgreSQL database
def create_database():
    conn = psycopg2.connect(
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT
    )
    return conn


# Creating a table for the game
def create_table_for_game(conn, game_name):
    table_name = game_name.replace(" ", "_").lower()
    cursor = conn.cursor()
    cursor.execute(sql.SQL('''
        CREATE TABLE IF NOT EXISTS {} (
            id SERIAL PRIMARY KEY,
            promo_code TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''').format(sql.Identifier(table_name)))
    conn.commit()


# Generation of unique client_id
async def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_numbers = ''.join(str(random.randint(0, 9)) for _ in range(19))
    return f"{timestamp}-{random_numbers}"


# Login client
async def login_client(game):
    client_id = await generate_client_id()
    proxy = game['proxy']

    async with aiohttp.ClientSession() as session:
        try:
            auth = aiohttp.BasicAuth(proxy['user'], proxy['pass']) if proxy['user'] and proxy['pass'] else None
            async with session.post(
                'https://api.gamepromo.io/promo/login-client',
                json={
                    'appToken': game['app_token'],
                    'clientId': client_id,
                    'clientOrigin': 'deviceid'
                },
                proxy=proxy['url'],
                proxy_auth=auth,
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                }
            ) as response:
                data = await response.json()
                print(f"- Токен для игры {game['name']} сформирован")
                return data['clientToken']
        except Exception as error:
            print(f"Ошибка при входе клиента для игры {game['name']}: {error}")
            await asyncio.sleep(game['base_delay'] * (random.random() / 3 + 1) + 5)
            return await login_client(game)


# Event registration
async def register_event(game, token):
    event_id = str(uuid.uuid4())
    proxy = game['proxy']

    async with aiohttp.ClientSession() as session:
        for attempt in range(game['attempts']):  # Используем количество попыток из game
            try:
                auth = aiohttp.BasicAuth(proxy['user'], proxy['pass']) if proxy['user'] and proxy['pass'] else None
                async with session.post(
                    'https://api.gamepromo.io/promo/register-event',
                    json={
                        'promoId': game['promo_id'],
                        'eventId': event_id,
                        'eventOrigin': 'undefined'
                    },
                    proxy=proxy['url'],
                    proxy_auth=auth,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json; charset=utf-8',
                    }
                ) as response:
                    data = await response.json()
                    if data.get('hasCode', False):
                        return True
                    else:
                        await asyncio.sleep(game['base_delay'] * (random.random() / 3 + 1) + 5)
            except Exception as error:
                print(f"Ошибка при регистрации события для игры {game['name']}: {error}")
                await asyncio.sleep(5)
        print(f"- Не удалось зарегистрировать событие для {game['name']}, перезапуск")
        return False


# Creating a promo code
async def create_code(game, token):
    proxy = game['proxy']

    async with aiohttp.ClientSession() as session:
        response = None
        auth = aiohttp.BasicAuth(proxy['user'], proxy['pass']) if proxy['user'] and proxy['pass'] else None
        while not response or not response.get('promoCode'):
            try:
                async with session.post(
                    'https://api.gamepromo.io/promo/create-code',
                    json={
                        'promoId': game['promo_id']
                    },
                    proxy=proxy['url'],
                    proxy_auth=auth,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json; charset=utf-8',
                    }
                ) as resp:
                    response = await resp.json()
            except Exception as error:
                print(f"Ошибка при создании кода для игры {game['name']}: {error}")
                await asyncio.sleep(1)
        return response['promoCode']


# Generating and saving a promo code
async def gen(game):
    table_name = game['name'].replace(" ", "_").lower()
    while True:
        token = await login_client(game)

        if await register_event(game, token):
            code_data = await create_code(game, token)

            # Open a new database connection
            conn = create_database()
            try:
                cursor = conn.cursor()
                cursor.execute(sql.SQL("INSERT INTO {} (promo_code) VALUES (%s)").format(sql.Identifier(table_name)),
                               (code_data,))
                conn.commit()
                print(f"- Промокод {code_data} сгенерирован и сохранен в таблицу {table_name}")
                break
            except Exception as e:
                print(f"Ошибка при сохранении промокода для игры {game['name']}: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            continue
