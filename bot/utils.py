import os
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_language


# Load translations from json
def load_translations():
    translations_path = os.path.join(os.path.dirname(__file__), 'translations.json')
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
async def get_translation(conn, user_id, key):
    user_lang = await get_user_language(conn, user_id)
    return translations.get(user_lang, {}).get(key, key)


# Function that returns the button bar
async def get_action_buttons(conn, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await get_translation(conn, user_id, "get_keys"), callback_data="get_keys")],
    ])


# Shields special characters in text for MarkdownV2.
def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)


# Calculation of the remaining time until the next request
def get_remaining_time(last_request_time, interval_minutes):
    if last_request_time is None:
        return 0, 0  # If no requests have been made yet, return 0

    now = datetime.now(timezone.utc)
    elapsed_time = now - last_request_time
    remaining_time = timedelta(minutes=interval_minutes) - elapsed_time

    if remaining_time.total_seconds() > 0:
        minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
        return minutes, seconds
    return 0, 0  # If the waiting time has elapsed, return 0
