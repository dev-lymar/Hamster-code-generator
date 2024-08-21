import asyncio
import aiohttp
import time
import random
import uuid
import logging.handlers
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

load_dotenv()

# Configuring logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file = os.path.join(log_directory, 'game_promo.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
    ]
)

logger = logging.getLogger(__name__)

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

        # Parsing URL to extract the login and password
        parsed_url = urlparse(proxy)
        username = parsed_url.username
        password = parsed_url.password

        try:
            auth = aiohttp.BasicAuth(username, password) if username and password else None
            async with self.session.post(
                    'https://api.gamepromo.io/promo/login-client',
                    json={
                        'appToken': self.game['app_token'],
                        'clientId': client_id,
                        'clientOrigin': 'deviceid'
                    },
                    proxy=proxy,
                    proxy_auth=auth,
                    headers={
                        'Content-Type': 'application/json; charset=utf-8',
                    }
            ) as response:
                data = await response.json()
                self.token = data['clientToken']
                logger.info(f"Token: {self.game['name']} proxy: {proxy} generated")
        except Exception as error:
            logger.error(f"Client login error {self.game['name']} proxy: {proxy}: {error}")
            await asyncio.sleep(self.game['base_delay'] + random.uniform(0.1, 3) + 5)
            await self.login_client()

    async def register_event(self):
        event_id = str(uuid.uuid4())
        proxy = self.game['proxy']

        for attempt in range(self.game['attempts']):
            try:
                parsed_url = urlparse(proxy)
                username = parsed_url.username
                password = parsed_url.password
                ip = parsed_url.hostname
                port = parsed_url.port
                auth = aiohttp.BasicAuth(username, password) if username and password else None
                async with self.session.post(
                        'https://api.gamepromo.io/promo/register-event',
                        json={
                            'promoId': self.game['promo_id'],
                            'eventId': event_id,
                            'eventOrigin': 'undefined'
                        },
                        proxy=proxy,
                        proxy_auth=auth,
                        headers={
                            'Authorization': f'Bearer {self.token}',
                            'Content-Type': 'application/json; charset=utf-8',
                        }
                ) as response:
                    # Check if the response is HTML
                    if 'text/html' in response.headers.get('Content-Type', ''):
                        error_text = await response.text()
                        logger.error(
                            f"Server Error: {response.status} - {self.game['name']} proxy IP: {ip}, Port: {port} - Unexpected HTML response")
                        logger.error(
                            f"HTML Response: {error_text[:500]}...")
                        continue  # Let's move on to the next attempt

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Server Error: {response.status} - {self.game['name']} proxy IP: {ip}, Port: {port}")
                        logger.error(f"Response body: {error_text}")

                        if response.status == 400 and "TooManyRegister" in error_text:
                            delay_time = self.game['base_delay'] + random.uniform(5, 25) + random.uniform(1, 3)
                            logger.warning(
                                f"New delay time {delay_time:.2f} sec.")
                            await asyncio.sleep(delay_time)
                            continue

                        await asyncio.sleep(random.uniform(3, 6))
                        continue

                    if 'application/json' in response.headers.get('Content-Type'):
                        data = await response.json()
                        if data.get('hasCode', False):
                            logger.info(
                                f"Event {self.game['name']} proxy: {proxy} successfully registered")
                            return True
                    else:
                        logger.warning(f"Unexpected response from the server: {await response.text()}")
                        await asyncio.sleep(5)
                        continue

            except Exception as error:
                logger.error(
                    f"Error in event registration {self.game['name']} proxy: {proxy}: {error}")
                await asyncio.sleep(5)
        logger.error(f"Failed to register an event for {self.game['name']} proxy: {proxy}, restart!")
        return False

    async def create_code(self):
        proxy = self.game['proxy']
        response = None
        parsed_url = urlparse(proxy)
        username = parsed_url.username
        password = parsed_url.password
        auth = aiohttp.BasicAuth(username, password) if username and password else None
        while not response or not response.get('promoCode'):
            try:
                async with self.session.post(
                        'https://api.gamepromo.io/promo/create-code',
                        json={'promoId': self.game['promo_id']},
                        proxy=proxy,
                        proxy_auth=auth,
                        headers={
                            'Authorization': f'Bearer {self.token}',
                            'Content-Type': 'application/json; charset=utf-8',
                        }
                ) as resp:
                    response = await resp.json()
            except Exception as error:
                logger.error(f"Error creating code {self.game['name']} proxy: {proxy}: {error}")
                await asyncio.sleep(random.uniform(1, 3.5))
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
                logger.info(f"--KEY-- {code_data} generated and stored in a table {table_name}")
            except Exception as e:
                parsed_url = urlparse(f"http://{game['proxy']}")
                ip = parsed_url.hostname
                port = parsed_url.port
                logger.error(f"Error saving key: {game['name']} proxy: {ip}:{port} - {e}")
            finally:
                cursor.close()
                conn.close()
        # Add a short pause before next generation
        await asyncio.sleep(1)

    await promo.close_session()
