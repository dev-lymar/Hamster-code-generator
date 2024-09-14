import os

from database.database import get_session, get_user_language
from translations import TranslationManager


async def get_translations(user_id: int, category: str, key: str) -> str:
    async with await get_session() as session:
        user_lang = await get_user_language(session, user_id)
        translation_manager = TranslationManager(
            translations_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations', 'locales')
        )
        return translation_manager.get_translation(user_lang, category, key)
