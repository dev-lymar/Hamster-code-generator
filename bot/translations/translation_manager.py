import json
import os
from typing import Dict, List

from bot.bot_config import logger


class TranslationManager:
    def __init__(self, translations_dir: str) -> None:
        self.translations_dir = translations_dir
        self.cache = {}

    def load_translations(self, language_code: str) -> Dict[str, Dict[str, str]]:
        """Loading translations by language code with caching"""
        if language_code in self.cache:
            return self.cache[language_code]

        translations_path = os.path.join(self.translations_dir, f"{language_code}.json")

        if os.path.exists(translations_path):
            try:
                with open(translations_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    self.cache[language_code] = translations
                    return translations
            except Exception as e:
                logger.error(f"Error loading translations for {language_code}: {e}")
        else:
            logger.warning(f"Translations file not found for {language_code}. Using default empty translations.")

        return {}

    def get_translation(self, language_code: str, category: str, key: str) -> str:
        """Getting translation by key and category"""
        translations = self.load_translations(language_code)
        return translations.get(category, {}).get(key, key)

    def get_available_languages(self) -> List[str]:
        """Getting a list of available languages from files"""
        return [filename.split('.')[0] for filename in os.listdir(self.translations_dir) if filename.endswith('.json')]
