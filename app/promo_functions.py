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
async def login_client(app_token, proxy_url, proxy_user, proxy_pass):
    client_id = await generate_client_id()
    async with aiohttp.ClientSession() as session:
        try:
            auth = aiohttp.BasicAuth(proxy_user, proxy_pass) if proxy_user and proxy_pass else None
            async with session.post(
                'https://api.gamepromo.io/promo/login-client',
                json={
                    'appToken': app_token,
                    'clientId': client_id,
                    'clientOrigin': 'deviceid'
                },
                proxy=proxy_url,
                proxy_auth=auth,
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                }
            ) as response:
                data = await response.json()
                return data['clientToken']
        except Exception as error:
            print(f'Ошибка при входе клиента: {error}')
            await asyncio.sleep(5)
            return await login_client(app_token, proxy_url, proxy_user, proxy_pass)


# Event registration
async def register_event(token, promo_id, proxy_url, proxy_user, proxy_pass):
    event_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        try:
            auth = aiohttp.BasicAuth(proxy_user, proxy_pass) if proxy_user and proxy_pass else None
            async with session.post(
                'https://api.gamepromo.io/promo/register-event',
                json={
                    'promoId': promo_id,
                    'eventId': event_id,
                    'eventOrigin': 'undefined'
                },
                proxy=proxy_url,
                proxy_auth=auth,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json; charset=utf-8',
                }
            ) as response:
                data = await response.json()
                if not data.get('hasCode', False):
                    await asyncio.sleep(5)
                    return await register_event(token, promo_id, proxy_url, proxy_user, proxy_pass)
                else:
                    return True
        except Exception as error:
            await asyncio.sleep(5)
            return await register_event(token, promo_id, proxy_url, proxy_user, proxy_pass)


# Creating a promo code
async def create_code(token, promo_id, proxy_url, proxy_user, proxy_pass):
    async with aiohttp.ClientSession() as session:
        response = None
        auth = aiohttp.BasicAuth(proxy_user, proxy_pass) if proxy_user and proxy_pass else None
        while not response or not response.get('promoCode'):
            try:
                async with session.post(
                    'https://api.gamepromo.io/promo/create-code',
                    json={
                        'promoId': promo_id
                    },
                    proxy=proxy_url,
                    proxy_auth=auth,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json; charset=utf-8',
                    }
                ) as resp:
                    response = await resp.json()
            except Exception as error:
                print(f'Ошибка при создании кода: {error}')
                await asyncio.sleep(1)
        return response['promoCode']


# Generating and saving a promo code
async def gen(game, proxy_url, proxy_user, proxy_pass):
    table_name = game['name'].replace(" ", "_").lower()
    token = await login_client(game['app_token'], proxy_url, proxy_user, proxy_pass)
    print(f"Токен: {token}")

    await register_event(token, game['promo_id'], proxy_url, proxy_user, proxy_pass)
    code_data = await create_code(token, game['promo_id'], proxy_url, proxy_user, proxy_pass)
    print('Сгенерированный код:', code_data)

    # Open a new database connection
    conn = create_database()
    try:
        cursor = conn.cursor()
        cursor.execute(sql.SQL("INSERT INTO {} (promo_code) VALUES (%s)").format(sql.Identifier(table_name)), (code_data,))
        conn.commit()
        print(f"Промокод {code_data} сохранен в таблицу {table_name}")
    except Exception as e:
        print(f"Ошибка при сохранении промокода: {e}")
    finally:
        # Close the connection to the database
        cursor.close()
        conn.close()
