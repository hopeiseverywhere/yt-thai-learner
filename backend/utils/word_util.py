# utils/word_util.py - Optimized version

from pythainlp import transliterate
from models.dict_schemas import TokenizedThaiWord
from services.dictionary_service import DictionaryService
from functools import lru_cache
from typing import List, Dict, Optional

# Global cache for word processing results
_word_cache: Dict[str, TokenizedThaiWord] = {}


@lru_cache(maxsize=10000)
def _cached_transliterate(word: str) -> str:
    """Cached transliteration to avoid repeated calls"""
    return transliterate(word, engine="icu")


def process_thai_word(word: str,
    dict_service_freq: DictionaryService,
    dict_service_full: Optional[DictionaryService] = None) -> TokenizedThaiWord:
    """Process a single Thai word into a TokenizedThaiWord with caching"""

    # Check cache first
    if word in _word_cache:
        return _word_cache[word]

    # Get transliteration (cached)
    transliterated = _cached_transliterate(word)

    # Search for English translations using the service
    search_result = dict_service_freq.search_word(word)
    english_translations = search_result.get_english_translations() if search_result else []

    if len(english_translations) == 0 and dict_service_full is not None:
        search_result = dict_service_full.search_word(word)
        english_translations = search_result.get_english_translations() if search_result else []

    # Create result
    result = TokenizedThaiWord(
        thai=word,
        transliterated=transliterated,
        english_translations=english_translations
    )

    # Cache the result
    _word_cache[word] = result

    return result


def process_thai_words_batch(dict_service: DictionaryService,
    words: List[str]) -> List[TokenizedThaiWord]:
    """Process multiple Thai words efficiently with batch operations"""

    results = []
    uncached_words = []
    word_to_index = {}

    # First pass: check cache and collect uncached words
    for i, word in enumerate(words):
        if word in _word_cache:
            results.append(_word_cache[word])
        else:
            # Mark as needing processing
            results.append(None)
            uncached_words.append(word)
            word_to_index[word] = i

    # Batch process uncached words
    if uncached_words:
        # Batch transliteration
        transliterations = {word: _cached_transliterate(word) for word in
                            uncached_words}

        # Batch dictionary lookups (if your dictionary service supports it)
        for word in uncached_words:
            search_result = dict_service.search_word(word)
            english_translations = search_result.get_english_translations() if search_result else []

            # Create result
            processed_word = TokenizedThaiWord(
                thai=word,
                transliterated=transliterations[word],
                english_translations=english_translations
            )

            # Cache and store
            _word_cache[word] = processed_word
            results[word_to_index[word]] = processed_word

    return results


def clear_word_cache():
    """Clear the word processing cache"""
    global _word_cache
    _word_cache.clear()


def get_cache_stats():
    """Get cache statistics for debugging"""
    return {
        "cache_size": len(_word_cache),
        "cached_words": list(_word_cache.keys())[:10]  # First 10
    }
