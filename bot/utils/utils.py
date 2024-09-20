import os

from bot.database.database import get_user_language
from bot.translations import TranslationManager
from db.database import get_session


async def get_translation(user_id: int, category: str, key: str) -> str:
    async with await get_session() as session:
        user_lang = await get_user_language(session, user_id)
        translation_manager = TranslationManager(
            translations_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations', 'locales')
        )
        return translation_manager.get_translation(user_lang, category, key)


def get_available_languages() -> dict:
    """Getting the list of available languages via TranslationManager"""
    translations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations', 'locales')
    translation_manager = TranslationManager(translations_dir)
    languages_dict = {}

    available_languages = translation_manager.get_available_languages()

    for lang_code in available_languages:
        language_name = translation_manager.get_translation(lang_code, 'language', 'name')
        languages_dict[lang_code] = language_name

    return languages_dict
