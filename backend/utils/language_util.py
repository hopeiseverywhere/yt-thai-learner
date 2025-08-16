# from typing import Dict, List, Optional
#
# LANGUAGE_NAMES = {
#     # Common languages
#     "en": "English",
#     "th": "Thai",
#     "zh": "Chinese (Simplified)",
#     "zh-Hans": "Chinese (Simplified)",
#     "zh-Hant": "Chinese (Traditional)",
#     "zh-TW": "Chinese (Traditional)",
#     "zh-CN": "Chinese (Simplified)",
#     "ja": "Japanese",
#     "ko": "Korean",
#     "es": "Spanish",
#     "fr": "French",
#     "de": "German",
#     "it": "Italian",
#     "pt": "Portuguese",
#     "pt-PT": "Portuguese (Portugal)",
#     "pt-BR": "Portuguese (Brazil)",
#     "ru": "Russian",
#     "ar": "Arabic",
#     "hi": "Hindi",
#     "bn": "Bengali",
#     "ur": "Urdu",
#     "id": "Indonesian",
#     "ms": "Malay",
#     "vi": "Vietnamese",
#     "fil": "Filipino",
#     "tl": "Tagalog"
# }
#
#
# def get_language_name(code: str) -> str:
#     """
#     Get the full language name from a language code.
#
#     Args:
#         code: Language code (e.g., 'en', 'th', 'zh-Hans')
#
#     Returns:
#         Full language name or the code itself if not found
#     """
#     return LANGUAGE_NAMES.get(code.lower(), code)
#
#
# def get_language_code(name: str) -> Optional[str]:
#     """
#     Get the language code from a full language name.
#
#     Args:
#         name: Full language name (e.g., 'English', 'Thai')
#
#     Returns:
#         Language code or None if not found
#     """
#     name_lower = name.lower()
#     for code, lang_name in LANGUAGE_NAMES.items():
#         if lang_name.lower() == name_lower:
#             return code
#     return None
#
#
# def is_valid_language_code(code: str) -> bool:
#     """
#     Check if a language code is valid.
#
#     Args:
#         code: Language code to validate
#
#     Returns:
#         True if valid, False otherwise
#     """
#     return code.lower() in LANGUAGE_NAMES