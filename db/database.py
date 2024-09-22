import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()


def get_database_url() -> str:
    """Generates a database URL from environment variables."""
    return (f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@"
            f"{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}")


# Creating an asynchronous engine
engine = create_async_engine(get_database_url(), echo=False, pool_size=5, max_overflow=10)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Receiving a session
async def get_session() -> AsyncSession:
    """Creates an asynchronous session"""
    return AsyncSessionLocal()
