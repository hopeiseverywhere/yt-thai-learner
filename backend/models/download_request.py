# from pydantic import BaseModel, field_validator
# from typing import Optional, Literal, Union
#
# # Define the same allowed languages as in your router
# ALLOWED_LANGUAGE_CODES = {
#     "en", "th", "zh", "zh-Hans", "zh-Hant",
#     "ja", "ko", "es", "fr", "de", "pt", "ru"
# }
#
# ALLOWED_LANGUAGE_NAMES = {
#     "English", "Thai", "Chinese (Simplified)", "Chinese (Traditional)",
#     "Japanese", "Korean", "Spanish", "French", "German", "Portuguese", "Russian"
# }
#
# AllowedLanguageCodes = Literal[
#     "en", "th", "zh", "zh-Hans", "zh-Hant",
#     "ja", "ko", "es", "fr", "de", "pt", "ru"
# ]
#
# AllowedLanguageNames = Literal[
#     "English", "Thai", "Chinese (Simplified)", "Chinese (Traditional)",
#     "Japanese", "Korean", "Spanish", "French", "German", "Portuguese", "Russian"
# ]
#
#
# class DownloadRequest(BaseModel):
#     url: str
#     lang: Optional[str] = None  # e.g. 'en', 'th'
#     translate_to: Optional[str] = None  # e.g. 'en'
#     fmt: Literal['json', 'srt', 'vtt'] = 'srt'
#     filename: Optional[str] = None
#
#     @field_validator('lang', 'translate_to')
#     def validate_language(cls, v):
#         """Validate and normalize language input to language codes"""
#         if v is not None:
#             normalized = normalize_language_input(v)
#             return normalized
#         return v
#
#
# def normalize_language_input(lang_input: Union[str, None]) -> Union[str, None]:
#     """Convert language name to code, or return code if already a code."""
#     if lang_input is None:
#         return None
#
#     # Import here to avoid circular imports
#     try:
#         from utils.language_util import get_language_code
#     except ImportError:
#         # Fallback if utils not available
#         name_to_code = {
#             "English": "en", "Thai": "th", "Chinese (Simplified)": "zh-Hans",
#             "Chinese (Traditional)": "zh-Hant", "Japanese": "ja",
#             "Korean": "ko",
#             "Spanish": "es", "French": "fr", "German": "de", "Portuguese": "pt",
#             "Russian": "ru"
#         }
#         get_language_code = lambda x: name_to_code.get(x)
#
#     # Check if it's already a valid code
#     if lang_input in ALLOWED_LANGUAGE_CODES:
#         return lang_input
#
#     # Try to convert from name to code
#     code = get_language_code(lang_input)
#     if code and code in ALLOWED_LANGUAGE_CODES:
#         return code
#
#     # If we reach here, the input is invalid
#     allowed_options = list(ALLOWED_LANGUAGE_CODES) + list(
#         ALLOWED_LANGUAGE_NAMES)
#     raise ValueError(
#         f'Language "{lang_input}" is not allowed. Must be one of: {sorted(allowed_options)}')