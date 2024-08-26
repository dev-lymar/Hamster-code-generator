import asyncio
import aiohttp
import os
import time
import random
import uuid
import logging.handlers
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models.game_models import BikeRide3D, ChainCube2048, TrainMiner, MergeAway, TwerkRace3D, Polysphere, MowAndTrim, MudRacing

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
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
    ]
)

logger = logging.getLogger(__name__)


class GamePromo:
    def __init__(self, game):
        self.game = game
        self.token = None
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        await self.session.close()

    async def generate_client_id(self):
        timestamp = int(time.time() * 1000)
        random_numbers = ''.join(str(random.randint(0, 9)) for _ in range(19))
        return f"{timestamp}-{random_numbers}"

    async def login_client(self):
        client_id = await self.generate_client_id()
        proxy = self.game['proxy']

        parsed_url = urlparse(f"http://{proxy}")
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
                    proxy=f"http://{proxy}",
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
                parsed_url = urlparse(f"http://{proxy}")
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
                        proxy=f"http://{proxy}",
                        proxy_auth=auth,
                        headers={
                            'Authorization': f'Bearer {self.token}',
                            'Content-Type': 'application/json; charset=utf-8',
                        }
                ) as response:
                    if 'text/html' in response.headers.get('Content-Type', ''):
                        error_text = await response.text()
                        logger.error(
                            f"Server Error: {response.status} - {self.game['name']} proxy IP: {ip}, Port: {port} - Unexpected HTML response")
                        logger.error(
                            f"HTML Response: {error_text[:500]}...")
                        continue

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
        parsed_url = urlparse(f"http://{proxy}")
        username = parsed_url.username
        password = parsed_url.password
        auth = aiohttp.BasicAuth(username, password) if username and password else None
        while not response or not response.get('promoCode'):
            try:
                async with self.session.post(
                        'https://api.gamepromo.io/promo/create-code',
                        json={'promoId': self.game['promo_id']},
                        proxy=f"http://{proxy}",
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

    async def save_code_to_db(self, code_data: str, game_name: str):
        session = await get_session()
        try:
            table_mapping = {
                'Bike Ride 3D': BikeRide3D,
                'Chain Cube 2048': ChainCube2048,
                'Train Miner': TrainMiner,
                'Merge Away': MergeAway,
                'Twerk Race 3D': TwerkRace3D,
                'Polysphere': Polysphere,
                'Mow and Trim': MowAndTrim,
                'Mud Racing': MudRacing
            }
            GameTable = table_mapping.get(game_name)
            if GameTable:
                table_entry = GameTable(promo_code=code_data)
                session.add(table_entry)
                await session.commit()
                logger.info(f"--KEY-- {code_data} saved in table {game_name.replace(' ', '_').lower()}")
        except Exception as e:
            logger.error(f"Failed to save promo code {code_data} for game {game_name}: {e}")
            await session.rollback()
        finally:
            await session.close()

    async def gen_promo_code(self):
        await self.login_client()

        if await self.register_event():
            promo_code = await self.create_code()
            if promo_code:
                await self.save_code_to_db(promo_code, self.game['name'])
            return promo_code
        return None


async def gen(game):
    promo = GamePromo(game)

    try:
        while True:
            code_data = await promo.gen_promo_code()

            if code_data:
                await asyncio.sleep(1)
    finally:
        await promo.close_session()
