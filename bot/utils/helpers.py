import os
import random
from datetime import datetime, timedelta, timezone

from aiogram.types import FSInputFile

from bot.bot_config import logger


async def load_image(subfolder: str, specific_image: str = None) -> FSInputFile | None:
    base_image_dir = os.path.join(os.path.dirname(__file__), "..", "images", subfolder)

    if os.path.exists(base_image_dir) and os.path.isdir(base_image_dir):
        # If a specific image is specified
        if specific_image:
            image_path = os.path.join(base_image_dir, specific_image)
            if os.path.isfile(image_path):
                return FSInputFile(image_path)
            else:
                logger.error(f"Image {specific_image} not found in {base_image_dir}.")
                return None
        # If no specific image is specified, select a random image
        else:
            image_files = [f for f in os.listdir(base_image_dir) if os.path.isfile(os.path.join(base_image_dir, f))]
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(base_image_dir, random_image)
                return FSInputFile(image_path)

    logger.error(f"Directory {base_image_dir} does not exist or is not a directory.")
    return None


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
