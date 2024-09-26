import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import func, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from bot.bot_config import logger
from config.redis_config import redis_manager as redis_client
from db.database import get_session

from .models import User, UserLog

load_dotenv()


async def load_keys_to_cache(session: AsyncSession, game_name: str, limit: int = 2000) -> None:
    """Loading keys from the database into the Redis cache."""
    try:
        client = await redis_client.get_client()

        # Load missing keys from the database
        table_name: str = game_name.replace(" ", "_").lower()
        query = text(f"SELECT promo_code FROM {table_name} ORDER BY created_at ASC LIMIT :limit")
        result = await session.execute(query, {'limit': limit})
        keys: List[str] = [row[0] for row in result.fetchall()]

        if keys:
            await client.rpush(f"keys:{game_name}", *keys)
            await client.expire(f"keys:{game_name}", 7200)
            logger.info(f"✅ {len(keys)} new keys loaded into cache for game: {game_name}")
        else:
            logger.info(f"❌ No new keys found in the database for game: {game_name}")
    except Exception as e:
        logger.error(f"Error loading keys to cache for game {game_name}: {e}")


# Adds new user to the database
async def get_or_create_user(session: AsyncSession, chat_id: int, user_data: Dict[str, Any]) -> Optional[User]:
    try:
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        user_record: Optional[User] = result.scalar_one_or_none()

        if user_record is None:
            new_user = User(**user_data)
            session.add(new_user)
            await session.commit()
            return new_user

        return user_record
    except Exception as e:
        logger.error(f"Error in get_or_create_user for chat_id {chat_id}: {e}")
        await session.rollback()
        return None


# Get user language
async def get_user_language(session: AsyncSession, user_id: int) -> str:
    try:
        result = await session.execute(select(User.language_code).filter(User.user_id == user_id))
        user_language: Optional[str] = result.scalar_one_or_none()
        return user_language if user_language else "en"
    except Exception as e:
        logger.error(f"Error in get_user_language: {e}")
        await session.rollback()
        return "en"


# Updates user language in the database
async def update_user_language(session: AsyncSession, user_id: int, language_code: str) -> None:
    try:
        result = await session.execute(select(User).filter(User.user_id == user_id))
        user: Optional[User] = result.scalar_one_or_none()
        if user:
            user.language_code = language_code
            await session.commit()
    except Exception as e:
        logger.error(f"Error in update_user_language: {e}")
        await session.rollback()


# Resets daily keys if needed
async def reset_daily_keys_if_needed(session: AsyncSession, user_id: int) -> None:
    try:
        current_date = datetime.now(timezone.utc).date()

        result = await session.execute(
            select(User).filter(User.user_id == user_id)
        )
        user: Optional[User] = result.scalar_one_or_none()
        if user and user.last_reset_date != current_date:
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(daily_requests_count=0, last_reset_date=current_date)
            )
            await session.commit()
    except Exception as e:
        logger.error(f"Error in reset_daily_keys_if_needed: {e}")
        await session.rollback()


# Logs user action
async def log_user_action(session: AsyncSession, user_id: int, action: str) -> None:
    try:
        new_log = UserLog(user_id=user_id, action=action)
        session.add(new_log)
        await session.commit()
    except Exception as e:
        logger.error(f"Error in log_user_action: {e}")
        await session.rollback()


# Getting the oldest keys for the game
async def get_keys(session: AsyncSession, game_name: str, limit: int = 4) -> List[str]:
    """Retrieving keys from Redis cache, reloading from the database if necessary."""
    try:
        client = await redis_client.get_client()

        # Get the current number of keys in cache
        cached_keys_count: int = await client.llen(f"keys:{game_name}")

        # Reload if the number of cached keys falls below the threshold
        if cached_keys_count <= 0:
            logger.info(f"Not enough keys ({cached_keys_count}). Reloading new keys for {game_name}.")
            await load_keys_to_cache(session, game_name, 2000)

        # Retrieve keys without deleting them, to delete them later via delete_keys
        cached_keys: List[bytes] = await client.lrange(f"keys:{game_name}", 0, limit - 1)

        # Convert bytes to strings (if keys are stored as bytes)
        cached_keys: List[str] = [key.decode('utf-8') if isinstance(key, bytes) else key for key in cached_keys]
        if cached_keys:
            return cached_keys
        else:
            logger.error(f"Failed to retrieve keys even after reloading cache for game: {game_name}")
            return []
    except Exception as e:
        logger.error(f"Error in get_keys for game {game_name}: {e}")
        return []


# Deleting used keys
async def delete_keys(session: AsyncSession, game_name: str, keys: List[str]) -> None:
    """Deleting keys from the database and cache"""
    try:
        client = await redis_client.get_client()
        # Deleting keys from the database
        table_name: str = game_name.replace(" ", "_").lower()
        query = text(f"DELETE FROM {table_name} WHERE promo_code = ANY(:keys)")
        await session.execute(query, {'keys': keys})
        await session.commit()

        # Deleting keys from the cache
        for key in keys:
            await client.lrem(f"keys:{game_name}", 0, key)
    except Exception as e:
        logger.error(f"Error in delete_keys for game {game_name}: {e}")
        await session.rollback()


# Update key count and time of the last request
async def update_keys_generated(session: AsyncSession, user_id: int, keys_generated: int) -> None:
    # Get the current time in UTC with timezone info
    try:
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
    except Exception as e:
        logger.error(f"Error in update_keys_generated for user {user_id}: {e}")
        await session.rollback()


# Check user limits
async def check_user_limits(session: AsyncSession, user_id: int, status_limits: Dict[str, Dict[str, int]]) -> bool:
    try:
        result = await session.execute(
            select(User.user_status, User.daily_requests_count, User.last_reset_date)
            .filter(User.user_id == user_id)
        )
        user: Optional[User] = result.one_or_none()

        if user:
            current_date = datetime.now(timezone.utc).date()

            # Check if the counter needs to be reset
            if user.last_reset_date != current_date:
                await reset_daily_keys_if_needed(session, user_id)
                daily_requests_count = 0
            else:
                daily_requests_count = user.daily_requests_count

            # Checking limits
            limit: int = status_limits.get(user.user_status, {}).get('daily_limit', 0)
            if daily_requests_count >= limit:
                return False
        return True
    except Exception as e:
        logger.error(f"Error in check_user_limits for user {user_id}: {e}")
        return False


# Check for ban, status, user limits
async def get_user_status_info(session: AsyncSession, user_id: int) -> Optional[User]:
    try:
        result = await session.execute(
            select(
                User.is_banned,
                User.last_request_time,
                User.user_status,
                User.daily_requests_count,
                User.last_reset_date,
            ).filter(User.user_id == user_id)
        )
        return result.one_or_none()
    except Exception as e:
        logger.error(f"Error in get_user_status_info for user {user_id}: {e}")
        return None


# Check for ban and role
async def get_user_role_and_ban_info(session: AsyncSession, user_id: int) -> Optional[User]:
    try:
        result = await session.execute(
            select(User.is_banned, User.user_role).filter(User.user_id == user_id)
        )
        return result.one_or_none()
    except Exception as e:
        logger.error(f"Error in get_user_role_and_ban_info for user {user_id}: {e}")
        return None


# Check if a user is admin
async def is_admin(user_id: int) -> bool:
    try:
        async with await get_session() as session:
            user_info = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user: Optional[User] = user_info.scalars().first()
            if user and user.user_role == 'admin':
                return True
            return False
    except Exception as e:
        logger.error(f"Error in is_admin for user {user_id}: {e}")
        return False


# Get admin chat IDs
async def get_admin_chat_ids() -> List[int]:
    try:
        async with await get_session() as session:
            result = await session.execute(
                select(User.chat_id).where(User.user_role == 'admin')
            )
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error in get_admin_chat_ids: {e}")
        return []


# Get count games keys in DB
async def get_keys_count_for_games(session: AsyncSession, games: List[str]) -> str:
    try:
        regular_results: List[str] = ["<i>Quantity</i>....<b>Game</b>\n"]

        for game in games:
            table_name: str = game.replace(" ", "_").lower()
            query = text(f"SELECT COUNT(*) FROM {table_name}")
            result = await session.execute(query)
            keys_count: int = result.scalar()
            regular_results.append(f"<i>{keys_count}</i>......<b>{game}</b>")

        return "\n".join(regular_results)
    except Exception as e:
        logger.error(f"Error in get_keys_count_for_games: {e}")
        return "<i>Error retrieving keys count.</i>"


# Get users list for admin panel
async def get_users_list_admin_panel(session: AsyncSession, games: List[str]) -> str:
    try:
        # Query to count the total number of users
        user_count_result = await session.execute(
            select(func.count(User.user_id))
        )
        users_count: int = user_count_result.scalar()

        keys_today: int = await get_daily_requests_count(session)

        keys_today_total: int = keys_today * len(games) * 4

        user_list: List[str] = [
            f"<i>Всего пользователей:  <b>{users_count}</b>\n(нажми ID что бы скопировать)</i>\n",
            f"<i>Сегодня забрали ключей:  <b>{keys_today_total}</b></i>\n",
        ]

        return "\n".join(user_list)
    except Exception as e:
        logger.error(f"Error in get_users_list_admin_panel: {e}")
        return "<i>Error retrieving users list.</i>"


# Get user detail for admin panel
async def get_user_details(session: AsyncSession, user_id: int) -> str:
    try:
        result = await session.execute(
            select(
                User.user_id, User.chat_id, User.first_name, User.last_name, User.username,
                User.registration_date, User.language_code,
                User.is_banned, User.user_status, User.user_role,
                User.is_subscribed, User.daily_requests_count,
                User.last_request_time, User.total_keys_generated, User.notes
            ).filter(User.user_id == user_id)
        )
        user: Optional[User] = result.one_or_none()

        if user is None:
            return f"<i>User with ID {user_id} not found.</i>"

        details: List[str] = [
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
    except Exception as e:
        logger.error(f"Error in get_user_details for user {user_id}: {e}")
        return f"<i>Error retrieving details for user {user_id}.</i>"


async def get_subscribed_users(session: AsyncSession):
    try:
        stmt = select(
            User.chat_id, User.first_name, User.is_subscribed).where(User.is_subscribed)
        result = await session.execute(stmt)
        users = result.fetchall()
        return users
    except Exception as e:
        logger.error(f"Error in get_subscribed_users: {e}")
        return []


# Get users list for admin panel
async def get_keys_count_main_menu(session: AsyncSession, games: List[str]) -> Dict[str, int]:
    try:
        keys_today: int = await get_daily_requests_count(session)
        POPULARITY_COEFFICIENT: int = int(os.getenv('POPULARITY_COEFFICIENT', 1))

        keys_today_total: int = keys_today * len(games) * 4 * POPULARITY_COEFFICIENT
        keys_dict = {
            'keys_today': keys_today_total,
        }
        return keys_dict
    except Exception as e:
        logger.error(f"Error in get_keys_count_main_menu: {e}")
        return {'keys_today': 0}


# Get daily requests count for regular keys
async def get_daily_requests_count(session: AsyncSession) -> int:
    try:
        today = datetime.utcnow().date()
        result = await session.execute(
            select(func.sum(func.coalesce(User.daily_requests_count, 0)))
            .where(User.last_reset_date == today)
        )
        return result.scalar() or 0
    except Exception as e:
        logger.error(f"Error in get_daily_requests_count: {e}")
        return 0


# Get user stats for statistic function
async def get_user_stats(session: AsyncSession, user_id: int, games: List[str]) -> Dict[str, Any]:
    try:
        result = await session.execute(
            select(
                User.registration_date,
                User.user_status,
                User.daily_requests_count,
                User.total_keys_generated,
            ).filter(User.user_id == user_id)
        )
        user_data = result.fetchone()
        if not user_data:
            raise KeyError(f"User with ID {user_id} not found or missing data.")
        keys_today: int = user_data[2] * (len(games) * 4 + 4)
        return {
            "registration_date": user_data[0],
            "user_status": user_data[1],
            "keys_today": keys_today,
            "total_keys_generated": user_data[3],
        }
    except KeyError as e:
        logger.error(f"KeyError in get_user_stats: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_user_stats for user {user_id}: {e}")
        return {
            "registration_date": None,
            "user_status": "unknown",
            "keys_today": 0,
            "total_keys_generated": 0,
        }
