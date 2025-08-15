from collections import defaultdict
from typing import Optional, Dict, List, Set
import csv
import unicodedata
import re

from models.dict_schemas import DictionaryEntry, SearchResult

# Remove zero-width & odd spaces
_ZW_RE = re.compile(r"[\u200B\u200C\u200D\u2060\uFEFF]")
_WS_RE = re.compile(r"\s+")


def load_dictionary(path: str) -> List[DictionaryEntry]:
    """Load the whole CSV into a list of DictionaryEntry objects."""
    entries: List[DictionaryEntry] = []
    with open(path, newline="", encoding="utf-8-sig") as f:  # Handle BOM
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(DictionaryEntry.from_row(row))
    return entries


def normalize_text(text: Optional[str]) -> Optional[str]:
    """
    Unified text normalization for both Thai and general text.
    Handles zero-width chars, spaces, and Unicode normalization.
    """
    if text is None:
        return None

    # Strip regular + weird spaces (NBSP etc.)
    text = text.replace("\u00A0", " ").strip()
    text = _ZW_RE.sub("", text)  # Remove zero-width chars
    text = _WS_RE.sub(" ", text)  # Collapse spaces

    # NFC to fix combining mark order (critical for Thai)
    text = unicodedata.normalize("NFC", text)

    return text if text else None


def normalize_search_term(term: str) -> str:
    """
    Normalize a search term for consistent matching.
    Uses the same normalization as normalize_text but also lowercases
    """
    if not term:
        return ""

    normalized = normalize_text(term)
    return normalized.lower() if normalized else ""


def index_by_thai(entries: List[DictionaryEntry]) -> Dict[
    str, List[DictionaryEntry]]:
    """Build an index of Thai headwords for faster lookup."""
    buckets = defaultdict(dict)  # key -> {id: entry}

    for entry in entries:
        for key in (
            normalize_text(entry.t_entry), normalize_text(entry.t_search)):
            if key:
                buckets[key][
                    entry.id] = entry  # Overwrites duplicates of same id

    return {key: list(entries_dict.values()) for key, entries_dict in
            buckets.items()}


def search_dictionary(
    entries: List[DictionaryEntry],
    search_term: str,
    search_fields: Optional[Set[str]] = None
) -> SearchResult:
    """
    Search for dictionary entries with exact matches only.

    Args:
        entries: List of DictionaryEntry objects to search
        search_term: The word/phrase to search for (exact match)
        search_fields: Set of field names to search in. If None, searches main fields.

    Returns:
        SearchResult containing all exactly matching entries
    """
    if not search_term or not entries:
        return SearchResult(word=search_term, entries=[])

    # Normalize the search term
    normalized_search = normalize_search_term(search_term)

    # Default search fields (most commonly searched)
    if search_fields is None:
        search_fields = {
            't_search',  # Thai search term
            't_entry',  # Thai headword
            'e_entry',  # English headword
            't_syn',  # Thai synonyms
            'e_related'  # English related terms
        }

    matching_entries = []

    for entry in entries:
        if _entry_matches_exact(entry, normalized_search, search_fields):
            matching_entries.append(entry)

    # Sort by ID to maintain consistent ordering
    matching_entries.sort(key=lambda x: x.id)

    return SearchResult(word=search_term, entries=matching_entries)


def _entry_matches_exact(
    entry: DictionaryEntry,
    normalized_search: str,
    search_fields: Set[str]
) -> bool:
    """Check if a dictionary entry exactly matches the search term."""
    for field_name in search_fields:
        field_value = getattr(entry, field_name, None)

        if not field_value:
            continue

        # For synonyms and related terms, check each comma-separated item
        if field_name in {'t_syn', 'e_related'}:
            terms = [normalize_search_term(term.strip()) for term in
                     field_value.split(',')]
            if normalized_search in terms:
                return True
        else:
            # Exact match for single terms
            normalized_field = normalize_search_term(field_value)
            if normalized_field == normalized_search:
                return True

    return False


# Predefined search field sets for convenience
_HEADWORD_FIELDS = {'t_entry', 't_search'}
_ENGLISH_FIELDS = {'e_entry', 'e_related'}
_THAI_FIELDS = {'t_search', 't_entry', 't_syn'}
_SYNONYM_FIELDS = {'t_syn', 'e_related'}


def search_headwords_only(entries: List[DictionaryEntry],
    headword: str) -> SearchResult:
    """Search for exact matches in headword fields only. Excludes synonyms."""
    return search_dictionary(entries, headword, _HEADWORD_FIELDS)


def search_by_english(entries: List[DictionaryEntry],
    english_term: str) -> SearchResult:
    """Search for exact matches in English terms only."""
    return search_dictionary(entries, english_term, _ENGLISH_FIELDS)


def search_by_thai(entries: List[DictionaryEntry],
    thai_term: str) -> SearchResult:
    """Search for exact matches in Thai terms only."""
    return search_dictionary(entries, thai_term, _THAI_FIELDS)


def search_with_priority(entries: List[DictionaryEntry],
    search_term: str) -> SearchResult:
    """
    Search with priority: headwords first, then synonyms/related terms.
    Returns results sorted by priority (headword matches first).
    """
    if not search_term or not entries:
        return SearchResult(word=search_term, entries=[])

    normalized_search = normalize_search_term(search_term)

    headword_matches = []
    synonym_matches = []

    for entry in entries:
        # Check headwords first (highest priority)
        if _entry_matches_exact(entry, normalized_search, _HEADWORD_FIELDS):
            headword_matches.append(entry)
        # Check synonyms/related (lower priority) - only if not already matched as headword
        elif _entry_matches_exact(entry, normalized_search, _SYNONYM_FIELDS):
            synonym_matches.append(entry)

    # Combine with headwords first, then synonyms
    all_matches = headword_matches + synonym_matches
    all_matches.sort(key=lambda x: x.id)  # Secondary sort by ID

    return SearchResult(word=search_term, entries=all_matches)


# Convenience function - most users probably want headwords only for the "ติดตาม" use case
def search(entries: List[DictionaryEntry], term: str) -> SearchResult:
    """
    Default search function - searches headwords only for cleaner results.
    Use search_dictionary() for more control over search fields.
    """
    return search_headwords_only(entries, term)
