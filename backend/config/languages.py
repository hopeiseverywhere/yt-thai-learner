from typing import Literal

ALLOWED_LANGUAGE_CODES = {
    "en", "th", "zh", "zh-Hans", "zh-Hant",
    "ja", "ko", "es", "fr", "de", "pt", "ru"
}

ALLOWED_LANGUAGE_NAMES = {
    "English", "Thai", "Chinese (Simplified)", "Chinese (Traditional)",
    "Japanese", "Korean", "Spanish", "French", "German", "Portuguese", "Russian"
}

AllowedLanguageCodes = Literal[
    "en", "th", "zh", "zh-Hans", "zh-Hant",
    "ja", "ko", "es", "fr", "de", "pt", "ru"
]

AllowedLanguageNames = Literal[
    "English", "Thai", "Chinese (Simplified)", "Chinese (Traditional)",
    "Japanese", "Korean", "Spanish", "French", "German", "Portuguese", "Russian"
]
