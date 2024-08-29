import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.game_models import Base as GameBase


load_dotenv()

DATABASE_URL = (f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@"
                f"{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}")

# Creating an asynchronous engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20
)

# Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Function for creating a database and tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(GameBase.metadata.create_all)


# Receiving a session
async def get_session() -> AsyncSession:
    return AsyncSessionLocal()


# Closing the connection
async def close_db():
    await engine.dispose()
