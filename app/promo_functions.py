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


def create_database():
    conn = psycopg2.connect(
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT
    )
    return conn


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


class GamePromo:
    def __init__(self, game):
        self.game = game
        self.token = None
        self.session = aiohttp.ClientSession()  # Create a session once

    async def close_session(self):
        await self.session.close()

    async def generate_client_id(self):
        timestamp = int(time.time() * 1000)
        random_numbers = ''.join(str(random.randint(0, 9)) for _ in range(19))
        return f"{timestamp}-{random_numbers}"

    async def login_client(self):
        client_id = await self.generate_client_id()
        proxy = self.game['proxy']

        try:
            auth = aiohttp.BasicAuth(proxy['user'], proxy['pass']) if proxy['user'] and proxy['pass'] else None
            async with self.session.post(
                'https://api.gamepromo.io/promo/login-client',
                json={
                    'appToken': self.game['app_token'],
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
                self.token = data['clientToken']
                print(f"- Токен для игры {self.game['name']} сформирован")
        except Exception as error:
            print(f"Ошибка при входе клиента для игры {self.game['name']}: {error}")
            await asyncio.sleep(self.game['base_delay'] * (random.random() / 3 + 1) + 5)
            await self.login_client()

    async def register_event(self):
        event_id = str(uuid.uuid4())
        proxy = self.game['proxy']

        for attempt in range(self.game['attempts']):
            try:
                auth = aiohttp.BasicAuth(proxy['user'], proxy['pass']) if proxy['user'] and proxy['pass'] else None
                async with self.session.post(
                    'https://api.gamepromo.io/promo/register-event',
                    json={
                        'promoId': self.game['promo_id'],
                        'eventId': event_id,
                        'eventOrigin': 'undefined'
                    },
                    proxy=proxy['url'],
                    proxy_auth=auth,
                    headers={
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json; charset=utf-8',
                    }
                ) as response:
                    data = await response.json()
                    if data.get('hasCode', False):
                        return True
                    else:
                        await asyncio.sleep(self.game['base_delay'] * (random.random() / 3 + 1) + 5)
            except Exception as error:
                print(f"Ошибка при регистрации события для игры {self.game['name']}: {error}")
                await asyncio.sleep(5)
        print(f"- Не удалось зарегистрировать событие для {self.game['name']}, перезапуск")
        return False

    async def create_code(self):
        proxy = self.game['proxy']
        response = None
        auth = aiohttp.BasicAuth(proxy['user'], proxy['pass']) if proxy['user'] and proxy['pass'] else None
        while not response or not response.get('promoCode'):
            try:
                async with self.session.post(
                    'https://api.gamepromo.io/promo/create-code',
                    json={'promoId': self.game['promo_id']},
                    proxy=proxy['url'],
                    proxy_auth=auth,
                    headers={
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json; charset=utf-8',
                    }
                ) as resp:
                    response = await resp.json()
            except Exception as error:
                print(f"Ошибка при создании кода для игры {self.game['name']}: {error}")
                await asyncio.sleep(1)
        return response['promoCode']

    async def gen_promo_code(self):
        await self.login_client()

        if await self.register_event():
            return await self.create_code()
        return None


async def gen(game):
    table_name = game['name'].replace(" ", "_").lower()
    promo = GamePromo(game)

    while True:
        code_data = await promo.gen_promo_code()

        if code_data:
            conn = create_database()
            try:
                cursor = conn.cursor()
                cursor.execute(sql.SQL("INSERT INTO {} (promo_code) VALUES (%s)").format(sql.Identifier(table_name)),
                               (code_data,))
                conn.commit()
                print(f"- Промокод {code_data} сгенерирован и сохранен в таблицу {table_name}")
            except Exception as e:
                print(f"Ошибка при сохранении промокода для игры {game['name']}: {e}")
            finally:
                cursor.close()
                conn.close()

        await asyncio.sleep(1)  # Add a short pause before next generation

    await promo.close_session()
