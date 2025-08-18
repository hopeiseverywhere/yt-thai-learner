from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Iterator
import unicodedata


def _nz(s: Optional[str]) -> Optional[str]:
    """Normalize and return None for empty strings."""
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    # Thai (and English) Unicode normalization
    return unicodedata.normalize("NFC", s)


@dataclass(frozen=True)
class DictionaryEntry:
    # Core identification
    id: int

    # Thai fields (common to both CSVs)
    t_word: Optional[str] = field(default=None)  # Main Thai word
    t_syn: Optional[str] = field(default=None)  # Thai synonyms
    t_ant: Optional[str] = field(default=None)  # Thai antonyms
    t_def: Optional[str] = field(default=None)  # Thai definition

    # English fields (different names in each CSV)
    freq_english: Optional[str] = field(default=None)  # Frequency CSV English
    e_dict: Optional[str] = field(default=None)  # Full CSV English dict
    e_dict_v: Optional[str] = field(
        default=None)  # Full CSV English dict variant
    rom_english: Optional[str] = field(
        default=None)  # Full CSV romanization English
    e_related: Optional[str] = field(default=None)  # Related English terms

    # Pronunciation fields
    freq_ipa: Optional[str] = field(default=None)  # IPA from frequency CSV
    romanization: Optional[str] = field(default=None)  # Romanization
    phonetic: Optional[str] = field(default=None)  # Phonetic transcription

    # Categories
    dict_category: Optional[str] = field(default=None)  # Grammar category
    rom_category: Optional[str] = field(default=None)  # Romanization category

    # Frequency-specific fields
    freq_rank: Optional[int] = field(
        default=None)  # Frequency rank (top 4000 only)
    frequency: Optional[int] = field(
        default=None)  # Usage frequency (top 4000 only)
    freq_example: Optional[str] = field(
        default=None)  # Example from frequency list

    # Dictionary-specific fields
    t_sample_sentence: Optional[str] = field(
        default=None)  # Sample sentence (full dict)
    sample_sentence: Optional[str] = field(
        default=None)  # Alternative sample field
    match_score: Optional[float] = field(
        default=None)  # Match score (full dict)

    # Common metadata
    etymology: Optional[str] = field(default=None)  # Word etymology
    domain: Optional[str] = field(default=None)  # Domain/field
    match_type: Optional[str] = field(
        default=None)  # How this entry was matched

    # Reference IDs
    smart_match_id: Optional[int] = field(
        default=None)  # Smart match ID (freq only)
    dict_id: Optional[int] = field(default=None)  # Original dict ID
    rom_id: Optional[int] = field(default=None)  # Original rom ID

    @property
    def headword(self) -> Optional[str]:
        """Main Thai headword"""
        return self.t_word

    @property
    def category(self) -> Optional[str]:
        """Primary grammatical category"""
        if self.dict_category:
            return self.dict_category.upper()
        elif self.rom_category:
            return self.rom_category.upper()
        return None

    @property
    def primary_english(self) -> Optional[str]:
        """Get the best English translation available"""
        return (self.freq_english or self.e_dict or self.e_dict_v or
                self.rom_english or self.e_related)

    @property
    def primary_romanization(self) -> Optional[str]:
        """Get the best romanization available"""
        return self.romanization or self.freq_ipa or self.phonetic

    @property
    def primary_sample(self) -> Optional[str]:
        """Get the best sample sentence available"""
        return (self.freq_example or self.sample_sentence or
                self.t_sample_sentence)

    @property
    def is_high_frequency(self) -> bool:
        """Check if this is a high-frequency word"""
        return self.freq_rank is not None

    @property
    def csv_type(self) -> str:
        """Determine which CSV type this entry came from"""
        if self.freq_rank is not None:
            return "frequency_4000"
        else:
            return "full_dictionary"

    @staticmethod
    def from_frequency_csv_row(row: Dict[str, str]) -> "DictionaryEntry":
        """
        Create entry from frequency CSV (top 4000 words)
        Format: id,freq_rank,t_word,freq_english,freq_ipa,frequency,freq_example,
               smart_match_id,dict_id,rom_id,e_dict,e_dict_v,dict_category,
               rom_category,romanization,phonetic,sample_sentence,t_def,t_syn,
               t_ant,e_related,etymology,domain,match_type
        """
        id_value = row.get("id") or row.get("\ufeffid")

        def to_int_or_none(value):
            if value and value.strip() and value.strip().lower() != 'null':
                try:
                    return int(value)
                except ValueError:
                    return None
            return None

        def to_float_or_none(value):
            if value and value.strip() and value.strip().lower() != 'null':
                try:
                    return float(value)
                except ValueError:
                    return None
            return None

        return DictionaryEntry(
            id=int(id_value),
            freq_rank=to_int_or_none(row.get("freq_rank")),
            t_word=_nz(row.get("t_word")),
            freq_english=_nz(row.get("freq_english")),
            freq_ipa=_nz(row.get("freq_ipa")),
            frequency=to_int_or_none(row.get("frequency")),
            freq_example=_nz(row.get("freq_example")),
            smart_match_id=to_int_or_none(row.get("smart_match_id")),
            dict_id=to_int_or_none(row.get("dict_id")),
            rom_id=to_int_or_none(row.get("rom_id")),
            e_dict=_nz(row.get("e_dict")),
            e_dict_v=_nz(row.get("e_dict_v")),
            dict_category=_nz(row.get("dict_category")),
            rom_category=_nz(row.get("rom_category")),
            romanization=_nz(row.get("romanization")),
            phonetic=_nz(row.get("phonetic")),
            sample_sentence=_nz(row.get("sample_sentence")),
            t_def=_nz(row.get("t_def")),
            t_syn=_nz(row.get("t_syn")),
            t_ant=_nz(row.get("t_ant")),
            e_related=_nz(row.get("e_related")),
            etymology=_nz(row.get("etymology")),
            domain=_nz(row.get("domain")),
            match_type=_nz(row.get("match_type"))
        )

    @staticmethod
    def from_full_csv_row(row: Dict[str, str]) -> "DictionaryEntry":
        """
        Create entry from full dictionary CSV
        Format: id,dict_id,rom_id,t_word,e_dict_v,rom_english,dict_category,
               rom_category,romanization,phonetic,match_score,t_sample_sentence,
               t_def,t_syn,t_ant,e_related,etymology,domain,match_type
        """
        id_value = row.get("id") or row.get("\ufeffid")

        def to_int_or_none(value):
            if value and value.strip() and value.strip().lower() != 'null':
                try:
                    return int(value)
                except ValueError:
                    return None
            return None

        def to_float_or_none(value):
            if value and value.strip() and value.strip().lower() != 'null':
                try:
                    return float(value)
                except ValueError:
                    return None
            return None

        return DictionaryEntry(
            id=int(id_value),
            dict_id=to_int_or_none(row.get("dict_id")),
            rom_id=to_int_or_none(row.get("rom_id")),
            t_word=_nz(row.get("t_word")),
            e_dict_v=_nz(row.get("e_dict_v")),
            rom_english=_nz(row.get("rom_english")),
            dict_category=_nz(row.get("dict_category")),
            rom_category=_nz(row.get("rom_category")),
            romanization=_nz(row.get("romanization")),
            phonetic=_nz(row.get("phonetic")),
            match_score=to_float_or_none(row.get("match_score")),
            t_sample_sentence=_nz(row.get("t_sample_sentence")),
            t_def=_nz(row.get("t_def")),
            t_syn=_nz(row.get("t_syn")),
            t_ant=_nz(row.get("t_ant")),
            e_related=_nz(row.get("e_related")),
            etymology=_nz(row.get("etymology")),
            domain=_nz(row.get("domain")),
            match_type=_nz(row.get("match_type"))
        )

    @staticmethod
    def from_row(row: Dict[str, str]) -> "DictionaryEntry":
        """
        Auto-detect CSV format and create appropriate entry
        """
        # Check if this is frequency CSV (has freq_rank)
        if "freq_rank" in row:
            return DictionaryEntry.from_frequency_csv_row(row)
        else:
            return DictionaryEntry.from_full_csv_row(row)


@dataclass
class SearchResult:
    """
    Represents search results for a single word/term (Thai)
    Contains multiple dictionary entries that match the same headword
    """
    word: str  # The normalized search term
    entries: List[DictionaryEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of entries found for this word"""
        return len(self.entries)

    @property
    def is_empty(self) -> bool:
        """True if no entries were found"""
        return len(self.entries) == 0

    @property
    def headword(self) -> Optional[str]:
        """Get the primary headword from the first entry"""
        return self.entries[0].headword if self.entries else None

    def get_by_cat(self, cat: str) -> List[DictionaryEntry]:
        """Get entries filtered by grammatical category"""
        cat_upper = cat.upper()
        return [entry for entry in self.entries if entry.category == cat_upper]

    def get_by_id(self, entry_id: int) -> Optional[DictionaryEntry]:
        """Get a specific entry by its ID"""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_english_translations(self) -> List[str]:
        """Get all unique English translations"""
        translations = set()
        for entry in self.entries:
            if entry.e_dict is not None:
                translations.add(entry.e_dict)
            elif entry.e_dict_v is not None:
                translations.add(entry.e_dict_v)
            elif entry.rom_english is not None:
                translations.add(entry.rom_english)
        return sorted(translations)

    def get_grammatical_category(self) -> List[str]:
        """Get all grammatical category for this word"""
        cat_set = set()
        for entry in self.entries:
            if entry.category:
                cat_set.add(entry.category)
        return sorted(cat_set)

    def group_by_pos(self) -> Dict[str, List[DictionaryEntry]]:
        """Group entries by part of speech."""
        groups = defaultdict(list)
        for entry in self.entries:
            pos = entry.category or "UNKNOWN"
            groups[pos].append(entry)
        return dict(groups)

    def __iter__(self) -> Iterator[DictionaryEntry]:
        """Allow iteration over entries."""
        return iter(self.entries)

    def __len__(self) -> int:
        """Allow len() to work on SearchResult."""
        return len(self.entries)

    def __bool__(self) -> bool:
        """Allow truthiness check (True if entries exist)."""
        return len(self.entries) > 0


@dataclass
class TokenizedThaiWord:
    """
    A Thai word with thai, transliteration and english meaning
    """
    thai: str
    transliterated: str
    english_translations: List[str]
