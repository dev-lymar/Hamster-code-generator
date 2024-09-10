from datetime import datetime, timezone

from config import ACHIEVEMENTS


def calculate_achievement(total_keys: int, total_premium_keys: int, days_in_bot: int) -> dict:
    total_keys = total_keys or 0
    total_premium_keys = total_premium_keys or 0

    if total_keys <= 150 and days_in_bot <= 5:
        return ACHIEVEMENTS["newcomer"]
    elif 151 <= total_keys <= 300 and 6 < days_in_bot <= 10:
        return ACHIEVEMENTS["key_seeker"]
    elif 301 <= total_keys <= 500 and 11 < days_in_bot <= 15:
        return ACHIEVEMENTS["bonus_hunter"]
    elif 500 <= total_keys <= 1000 and days_in_bot > 15:
        return ACHIEVEMENTS["code_expert"]
    elif 301 <= total_keys <= 500 and total_premium_keys <= 150 and days_in_bot <= 10:
        return ACHIEVEMENTS["key_master"]
    elif 151 <= total_premium_keys <= 300 and 11 <= days_in_bot <= 17:
        return ACHIEVEMENTS["elite_player"]
    elif total_premium_keys > 500 and days_in_bot > 17:
        return ACHIEVEMENTS["game_legend"]
    elif total_keys > 1500 or total_premium_keys > 300 and days_in_bot > 25:
        return ACHIEVEMENTS["absolute_leader"]
    return ACHIEVEMENTS["newcomer"]  # Default


def calculate_days_in_bot(registration_date):
    current_time = datetime.now(timezone.utc)
    return (current_time - registration_date).days


async def generate_user_stats(user_data) -> dict:
    days_in_bot = calculate_days_in_bot(user_data.get("registration_date", None))
    total_keys_generated = user_data.get("total_keys_generated", 0) or 0
    total_safety_keys_generated = user_data.get("total_safety_keys_generated", 0) or 0
    keys_today = user_data.get("keys_today", 0) or 0
    premium_keys_today = user_data.get("premium_keys_today", 0) or 0

    achievement = calculate_achievement(
        total_keys=total_keys_generated,
        total_premium_keys=total_safety_keys_generated,
        days_in_bot=days_in_bot
    )
    return {
        "achievement_name": achievement,
        "keys_today": keys_today,
        "premium_keys_today": premium_keys_today,
        "keys_total": total_keys_generated,
        "premium_keys_total": total_safety_keys_generated,
        "user_status": user_data.get("user_status", "free"),
    }