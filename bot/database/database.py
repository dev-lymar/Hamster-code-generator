import os
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from dotenv import load_dotenv
from datetime import datetime, timezone

from .models import Base, User, UserLog

load_dotenv()

# Database connection
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"

# Creating an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Creating a session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Function for creating a database and tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Session retrieval
async def get_session() -> AsyncSession:
    session = AsyncSessionLocal()
    return session


# Closing connections
async def close_db():
    await engine.dispose()


# Adds new user to the database
async def get_or_create_user(session: AsyncSession, chat_id: int, user_data: dict):
    existing_user = await session.execute(
        select(User).where(User.chat_id == chat_id)
    )
    user_record = existing_user.scalar_one_or_none()

    if user_record is None:
        new_user = User(**user_data)
        session.add(new_user)
        try:
            await session.commit()
            return new_user
        except IntegrityError:
            await session.rollback()
            return None
    else:
        return user_record


# Get user language
async def get_user_language(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User.language_code).filter(User.user_id == user_id))
    user_language = result.scalar_one_or_none()
    return user_language if user_language else "en"


# Updates user language in the database
async def update_user_language(session: AsyncSession, user_id: int, language_code: str):
    result = await session.execute(select(User).filter(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.language_code = language_code
        await session.commit()


# Resets daily keys if needed
async def reset_daily_keys_if_needed(session: AsyncSession, user_id: int):
    current_date = datetime.now(timezone.utc).date()

    result = await session.execute(
        select(User).filter(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    if user and user.last_reset_date != current_date:
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(daily_requests_count=0, last_reset_date=current_date)
        )
        await session.commit()


# Checks if the user is banned
async def is_user_banned(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(User.is_banned).filter(User.user_id == user_id))
    user = result.scalar_one_or_none()
    return user if user else False


# Logs user action
async def log_user_action(session: AsyncSession, user_id: int, action: str):
    new_log = UserLog(user_id=user_id, action=action)
    session.add(new_log)
    await session.commit()


# Getting oldest keys for the game
async def get_oldest_keys(session: AsyncSession, game_name: str, limit: int = 4):
    table_name = game_name.replace(" ", "_").lower()
    query = text(f"SELECT promo_code FROM {table_name} ORDER BY created_at ASC LIMIT :limit")
    result = await session.execute(query, {'limit': limit})
    return result.fetchall()


# Deleting used keys
async def delete_keys(session: AsyncSession, game_name: str, keys: list):
    table_name = game_name.replace(" ", "_").lower()
    query = text(f"DELETE FROM {table_name} WHERE promo_code = ANY(:keys)")
    await session.execute(query, {'keys': keys})
    await session.commit()


# Update key count and time of the last request
async def update_keys_generated(session: AsyncSession, user_id: int, keys_generated: int):
    current_date = datetime.now(timezone.utc).date()
    current_time = datetime.now(timezone.utc).replace(tzinfo=None)

    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(
            total_keys_generated=User.total_keys_generated + keys_generated,
            daily_requests_count=User.daily_requests_count + 1,
            last_request_time=current_time,
            last_reset_date=current_date
        )
    )
    await session.commit()


# Check user limits
async def check_user_limits(session: AsyncSession, user_id: int, status_limits: dict) -> bool:
    result = await session.execute(
        select(User.user_status, User.daily_requests_count, User.last_reset_date)
        .filter(User.user_id == user_id)
    )
    user = result.one_or_none()

    if user:
        current_date = datetime.now(timezone.utc).date()

        # Check if the counter needs to be reset
        if user.last_reset_date != current_date:
            await reset_daily_keys_if_needed(session, user_id)
            daily_requests_count = 0
        else:
            daily_requests_count = user.daily_requests_count

        # Checking limits
        limit = status_limits.get(user.user_status, {}).get('daily_limit', 0)
        if daily_requests_count >= limit:
            return False  # Limit has been reached
    return True


# Getting the time of the last request and user status
async def get_last_request_time(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(User.last_request_time, User.user_status)
        .filter(User.user_id == user_id)
    )
    return result.one_or_none()
