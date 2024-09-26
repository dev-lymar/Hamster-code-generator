from datetime import datetime, timezone

from bot.utils.static_data import ACHIEVEMENTS


def calculate_achievement(total_keys: int, days_in_bot: int) -> str:
    total_keys = total_keys or 0

    if total_keys <= 150 and days_in_bot <= 5:
        return ACHIEVEMENTS[0]
    elif 151 <= total_keys <= 300 and 6 < days_in_bot <= 10:
        return ACHIEVEMENTS[1]
    elif 301 <= total_keys <= 450 and 11 < days_in_bot <= 15:
        return ACHIEVEMENTS[2]
    elif 451 <= total_keys <= 600 and 16 < days_in_bot <= 20:
        return ACHIEVEMENTS[3]
    elif 601 <= total_keys <= 750 and 21 < days_in_bot <= 25:
        return ACHIEVEMENTS[4]
    elif 901 <= total_keys <= 1050 and 26 < days_in_bot <= 30:
        return ACHIEVEMENTS[5]
    elif 1051 <= total_keys <= 1200 and 31 < days_in_bot <= 35:
        return ACHIEVEMENTS[6]
    elif total_keys > 1200 and days_in_bot > 36:
        return ACHIEVEMENTS[7]
    return ACHIEVEMENTS[1]  # Default


def calculate_days_in_bot(registration_date: datetime) -> int:
    current_time = datetime.now(timezone.utc)
    return (current_time - registration_date).days


async def generate_user_stats(user_data) -> dict:
    days_in_bot = calculate_days_in_bot(user_data.get("registration_date", None))
    total_keys_generated = user_data.get("total_keys_generated", 0) or 0
    keys_today = user_data.get("keys_today", 0) or 0

    achievement = calculate_achievement(
        total_keys=total_keys_generated,
        days_in_bot=days_in_bot
    )
    user_status = user_data.get("user_status", "free")
    return {
        "achievement_name": achievement,
        "keys_today": keys_today,
        "keys_total": total_keys_generated,
        "user_status": user_status,
    }
