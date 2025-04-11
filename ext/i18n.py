import gettext


class I18n:
    def __init__(self):
        self.languages = ['en_US', 'es_ES']
        self.modules = ['bot', 'lvl', 'util']
        self.translations = self._load_translations()
        self.current_lang = self.default_lang = 'en_US'

    def _load_translations(self):
        """Load translations for all modules and languages."""
        translations = {lang: {} for lang in self.languages}
        for lang in self.languages:
            for module in self.modules:
                try:
                    translations[lang][module] = gettext.translation(
                        module, localedir='locales', languages=[lang]
                    )
                except FileNotFoundError:
                    translations[lang][module] = gettext.NullTranslations()
        return translations

    def set_lang(self, language):
        """Set the global current language."""
        self.current_lang = language if language in self.languages else self.default_language

    def get_translation(self, key, language=None):
        """Search for the key across all modules for a specific language."""
        lang = language if language else self.current_lang
        for module in self.modules:
            translation = self.translations[lang].get(module, gettext.NullTranslations())
            translated_text = translation.gettext(key)
            if translated_text != key:
                return translated_text
        return key 

# Global instance and _
i18n = I18n()
_ = lambda key: i18n.get_translation(key)
