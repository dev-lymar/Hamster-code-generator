import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import func, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select

from bot.bot_config import logger
from bot.redis_client import create_redis_client

from .models import Base, User, UserLog

load_dotenv()
redis_client = create_redis_client()


async def load_keys_to_cache(session: AsyncSession, game_name: str, limit: int = 2000):
    """Loading keys from the database into the Redis cache."""
    # Load missing keys from the database
    table_name = game_name.replace(" ", "_").lower()
    query = text(f"SELECT promo_code FROM {table_name} ORDER BY created_at ASC LIMIT :limit")
    result = await session.execute(query, {'limit': limit})
    keys = [row[0] for row in result.fetchall()]

    if keys:
        await redis_client.rpush(f"keys:{game_name}", *keys)
        logger.info(f"✅ {len(keys)} new keys loaded into cache for game: {game_name}")
    else:
        logger.info(f"❌ No new keys found in the database for game: {game_name}")


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


# Resets daily safety keys if needed
async def reset_daily_safety_keys_if_needed(session: AsyncSession, user_id: int):
    current_date = datetime.now(timezone.utc).date()

    result = await session.execute(
        select(User).filter(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    if user and user.last_reset_date_safety_keys != current_date:
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                daily_safety_keys_requests_count=0,
                last_reset_date_safety_keys=current_date,
            )
        )
        await session.commit()


# Logs user action
async def log_user_action(session: AsyncSession, user_id: int, action: str):
    new_log = UserLog(user_id=user_id, action=action)
    session.add(new_log)
    await session.commit()


# Getting the oldest keys for the game
async def get_oldest_keys(session: AsyncSession, game_name: str, limit: int = 4):
    """Retrieving the oldest keys using Redis cache, reloading from the database if necessary."""
    if game_name.lower() == "fluff crusade":
        limit = 8

    # Get the current number of keys in the cache
    cached_keys_count = await redis_client.llen(f"keys:{game_name}")

    # Reload if the number of cached keys falls below the threshold
    if cached_keys_count <= 0:
        logger.info(f"Not enough keys ({cached_keys_count}). Reloading new keys for {game_name}.")
        await load_keys_to_cache(session, game_name, 2000)

    # Fetch the oldest keys again after reloading
    cached_keys = await redis_client.lrange(f"keys:{game_name}", 0, limit - 1)

    if cached_keys:
        # Remove issued keys from the cache
        await redis_client.ltrim(f"keys:{game_name}", len(cached_keys), -1)
        logger.info(f"Issued {len(cached_keys)}/{cached_keys_count} keys from cache for game: {game_name}")
        return cached_keys
    else:
        logger.error(f"Failed to retrieve keys even after reloading cache for game: {game_name}")
        return []


# Getting safety keys with new tables for the game
async def get_safety_keys(session: AsyncSession, game_name: str, limit: int = 4):
    table_name = f"safety.{game_name.replace(' ', '_').lower()}"
    if table_name == "safety.fluff_crusade":
        limit = 8
    query = text(f"SELECT promo_code FROM {table_name} ORDER BY created_at ASC LIMIT :limit")
    result = await session.execute(query, {'limit': limit})
    return result.fetchall()


# Deleting used keys
async def delete_keys(session: AsyncSession, game_name: str, keys: list):
    """Deleting keys from the database and cache"""

    # Deleting keys from the database
    table_name = game_name.replace(" ", "_").lower()
    query = text(f"DELETE FROM {table_name} WHERE promo_code = ANY(:keys)")
    await session.execute(query, {'keys': keys})
    await session.commit()

    # Deleting keys from the cache
    for key in keys:
        await redis_client.lrem(f"keys:{game_name}", 0, key)
    logger.info(f"Deleted {len(keys)} keys from both cache and database for game: {game_name}")


# Deleting used safety keys
async def delete_safety_keys(session: AsyncSession, game_name: str, keys: list):
    table_name = f"safety.{game_name.replace(' ', '_').lower()}"
    query = text(f"DELETE FROM {table_name} WHERE promo_code = ANY(:keys)")
    await session.execute(query, {'keys': keys})
    await session.commit()


# Update key count and time of the last request
async def update_keys_generated(session: AsyncSession, user_id: int, keys_generated: int):
    # Get the current time in UTC with timezone info
    current_time = datetime.now(timezone.utc)

    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(
            total_keys_generated=User.total_keys_generated + keys_generated,
            daily_requests_count=User.daily_requests_count + 1,
            last_request_time=current_time,
            last_reset_date=current_time.date()
        )
    )
    await session.commit()


# Update safety key count and time of the last request
async def update_safety_keys_generated(session: AsyncSession, user_id: int, keys_generated: int):
    current_time = datetime.now(timezone.utc)

    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(
            total_safety_keys_generated=User.total_safety_keys_generated + keys_generated,
            daily_safety_keys_requests_count=User.daily_safety_keys_requests_count + 1,
            last_safety_keys_request_time=current_time,
            last_reset_date_safety_keys=current_time.date()
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


# Check user safety limits
async def check_user_safety_limits(session: AsyncSession, user_id: int, status_limits: dict) -> bool:
    result = await session.execute(
        select(User.user_status, User.daily_safety_keys_requests_count, User.last_reset_date_safety_keys)
        .filter(User.user_id == user_id)
    )
    user = result.one_or_none()

    if user:
        current_date = datetime.now(timezone.utc).date()

        # Check if the counter needs to be reset
        if user.last_reset_date_safety_keys != current_date:
            await reset_daily_safety_keys_if_needed(session, user_id)
            daily_safety_keys_requests_count = 0
        else:
            daily_safety_keys_requests_count = user.daily_safety_keys_requests_count

        # Checking limits
        limit = status_limits.get(user.user_status, {}).get('safety_daily_limit', 0)
        if daily_safety_keys_requests_count >= limit:
            return False  # Limit has been reached
    return True


# Check for ban, status, user limits
async def get_user_status_info(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(
            User.is_banned,
            User.last_request_time,
            User.last_safety_keys_request_time,
            User.user_status,
            User.daily_requests_count,
            User.daily_safety_keys_requests_count,
            User.last_reset_date,
            User.last_reset_date_safety_keys
        ).filter(User.user_id == user_id)
    )
    return result.one_or_none()


# Check for ban and role
async def get_user_role_and_ban_info(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(User.is_banned, User.user_role).filter(User.user_id == user_id)
    )
    return result.one_or_none()


# Check if a user is admin
async def is_admin(user_id: int) -> bool:
    async with await get_session() as session:
        user_info = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_info.scalars().first()
        if user and user.user_role == 'admin':
            return True
        return False


# Get admin chat IDs
async def get_admin_chat_ids():
    async with await get_session() as session:
        result = await session.execute(
            select(User.chat_id).where(User.user_role == 'admin')
        )
        return [row[0] for row in result.fetchall()]


# Get count games keys in DB
async def get_keys_count_for_games(session: AsyncSession, games: list) -> list:
    regular_results = ["<i>Quantity</i>....<b>Game</b>\n"]
    safety_results = ["\n<i>Quantity</i>....<b>Game (safety)</b>\n"]

    for game in games:
        table_name = game.replace(" ", "_").lower()
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        result = await session.execute(query)
        keys_count = result.scalar()
        regular_results.append(f"<i>{keys_count}</i>......<b>{game}</b>")
        safety_table_name = f"safety.{table_name}"
        safety_query = text(f"SELECT COUNT(*) FROM {safety_table_name}")
        try:
            safety_result = await session.execute(safety_query)
            safety_keys_count = safety_result.scalar()
            safety_results.append(f"<i>{safety_keys_count}</i>......<b>{game} (safety)</b>")
        except Exception as e:
            safety_results.append(f"<i>Table not found</i>......<b>{game} (safety). Error: {e}</b>")

    return "\n".join(regular_results + safety_results)


# Get users list for admin panel
async def get_users_list_admin_panel(session: AsyncSession, games: list):

    # Query to count the total number of users
    user_count_result = await session.execute(
        select(func.count(User.user_id))
    )
    users_count = user_count_result.scalar()

    keys_today = await get_daily_requests_count(session)
    premium_keys_today = await get_daily_safety_requests_count(session)

    keys_today_total = keys_today * len(games) * 4
    premium_keys_today_total = premium_keys_today * len(games) * 4

    user_list = [
        f"<i>Всего пользователей:  <b>{users_count}</b>\n(нажми ID что бы скопировать)</i>\n",
        f"<i>Сегодня забрали ключей:  <b>{keys_today_total}</b></i>\n",
        f"<i>Сегодня забрали прем ключей:  <b>{premium_keys_today_total}</b></i>\n",
    ]

    return "\n".join(user_list)


# Get user detail for admin panel
async def get_user_details(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(
        select(
            User.user_id, User.chat_id, User.first_name, User.last_name, User.username,
            User.registration_date, User.language_code,
            User.is_banned, User.user_status, User.user_role,
            User.is_subscribed, User.daily_requests_count,
            User.last_request_time, User.total_keys_generated, User.notes
        ).filter(User.user_id == user_id)
    )
    user = result.one_or_none()

    if user is None:
        return f"<i>User with ID {user_id} not found.</i>"

    if user:
        details = [
            f"<b>User Details:</b>\n"
            f"<b>ID</b>: <code>{user.user_id}</code>\n"
            f"<b>First Name</b>: {user.first_name or 'N/A'}\n"
            f"<b>Last Name</b>: {user.last_name or 'N/A'}\n"
            f"<b>Username</b>: @{user.username or 'N/A'}\n"
            f"<b>Registration</b>: {user.registration_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"<b>Language</b>: {user.language_code or 'N/A'}\n"
            f"<b>Role</b>: {user.user_role}\n"
            f"<b>Status</b>: {user.user_status or '<i>not provided</i>'}\n"
            f"<b>Subscription</b>: {'Active' if user.is_subscribed else 'Inactive'}\n"
            f"<b>Banned</b>: {'Yes' if user.is_banned else 'No'}\n"
            f"<b>Keys Generated</b>: {user.total_keys_generated}\n"
            f"<b>Keys Generated Today</b>: {user.daily_requests_count}\n"
            f"<b>Last Request</b>: "
            f"{user.last_request_time.strftime('%Y-%m-%d %H:%M:%S') if user.last_request_time else 'N/A'}\n"
            f"<b>Notes</b>: {user.notes or 'N/A'}"
        ]
    return "\n".join(details)


async def get_subscribed_users(session):
    stmt = select(
        User.chat_id, User.first_name, User.is_subscribed).where(User.is_subscribed)
    result = await session.execute(stmt)
    users = result.fetchall()
    return users


# Get users list for admin panel
async def get_keys_count_main_menu(session: AsyncSession, games: list):
    keys_today = await get_daily_requests_count(session)
    premium_keys_today = await get_daily_safety_requests_count(session)
    POPULARITY_COEFFICIENT = int(os.getenv('POPULARITY_COEFFICIENT', 1))

    keys_today_total = keys_today * len(games) * 4 * POPULARITY_COEFFICIENT
    premium_keys_today_total = premium_keys_today * len(games) * 4 * POPULARITY_COEFFICIENT
    keys_dict = {
        'keys_today': keys_today_total,
        'premium_keys_today': premium_keys_today_total
    }
    return keys_dict


# Get daily requests count for regular keys
async def get_daily_requests_count(session: AsyncSession) -> int:
    today = datetime.utcnow().date()
    result = await session.execute(
        select(func.sum(func.coalesce(User.daily_requests_count, 0)))
        .where(User.last_reset_date == today)
    )
    return result.scalar() or 0


# Get daily requests count for safety (premium) keys
async def get_daily_safety_requests_count(session: AsyncSession) -> int:
    today = datetime.utcnow().date()
    result = await session.execute(
        select(func.sum(func.coalesce(User.daily_safety_keys_requests_count, 0)))
        .where(User.last_reset_date_safety_keys == today)
    )
    return result.scalar() or 0


# Get user stats for statistic function
async def get_user_stats(session: AsyncSession, user_id: int, games: list) -> dict:
    result = await session.execute(
        select(
            User.registration_date,
            User.user_status,
            User.daily_requests_count,
            User.daily_safety_keys_requests_count,
            User.total_keys_generated,
            User.total_safety_keys_generated,
        ).filter(User.user_id == user_id)
    )
    user_data = result.fetchone()
    if not user_data:
        raise KeyError(f"User with ID {user_id} not found or missing data.")
    keys_today = user_data[2] * (len(games) * 4 + 4)
    premium_keys_today = (user_data[3] or 0) * (len(games) * 4 + 4)
    return {
        "registration_date": user_data[0],
        "user_status": user_data[1],
        "keys_today": keys_today,
        "premium_keys_today": premium_keys_today,
        "total_keys_generated": user_data[4],
        "total_safety_keys_generated": user_data[5],
    }
