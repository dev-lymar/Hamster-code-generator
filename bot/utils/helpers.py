import os
import json
import logging
from datetime import datetime, timedelta, timezone
from database.database import get_user_language, get_session


def load_translations():
    translations_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations', 'translations.json')
    if os.path.exists(translations_path):
        try:
            with open(translations_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading translations: {e}")
    else:
        logging.warning("Translations file not found. Using default empty translations.")
    return {}


translations = load_translations()


# Get translations
async def get_translation(user_id: int, key: str) -> str:
    async with await get_session() as session:
        user_lang = await get_user_language(session, user_id)
        return translations.get(user_lang, {}).get(key, key)


def get_remaining_time(last_request_time, interval_minutes):
    if last_request_time is None:
        return 0, 0

    # Ensure the current time is in UTC
    current_time = datetime.now(timezone.utc)

    # Calculate the time when the next request can be made
    next_allowed_time = last_request_time + timedelta(minutes=interval_minutes)
    remaining_time = next_allowed_time - current_time
    remaining_seconds = remaining_time.total_seconds()

    if remaining_seconds > 0:
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return minutes, seconds
    else:
        return 0, 0
