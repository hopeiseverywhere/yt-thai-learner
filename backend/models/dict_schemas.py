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
    # raw fields
    id: int
    t_search: Optional[str] = field(default=None)  # t-search
    t_entry: Optional[str] = field(default=None)  # t-entry (Thai headword)
    e_entry: Optional[str] = field(default=None)  # e-entry (English headword)
    t_cat: Optional[str] = field(default=None)  # t-cat (Grammatical category)
    t_syn: Optional[str] = field(default=None)  # t-syn (Thai synonyms)
    t_sample: Optional[str] = field(
        default=None)  # t-sample (Thai sample sentence)
    t_ant: Optional[str] = field(default=None)  # t-ant (Thai antonyms)
    t_def: Optional[str] = field(default=None)  # t-def (Thai definition)
    e_related: Optional[str] = field(
        default=None)  # e-related (English related)
    t_num: Optional[str] = field(default=None)  # t-num (?)
    notes: Optional[str] = field(default=None)

    @property
    def headword(self) -> Optional[str]:
        """Prefer t-entry as the display headword; fall back to t-search"""
        return self.t_entry or self.t_search

    @property
    def category(self) -> Optional[str]:
        """Grammatical category"""
        return self.t_cat.lower() + "." if self.t_cat else None

    @staticmethod
    def from_row(row: Dict[str, str]) -> "DictionaryEntry":
        """
        Create an entry from a csv.DictReader row.
        Assumes the CSV headers exactly matches:
        id,t-search,t-entry,e-entry,t-cat,t-syn,t-sample,t-ant,t-def,e-related,t-num,notes
        """
        id_value = row.get("id") or row.get("\ufeffid")
        # Map CSV keys to dataclass fields and normalize
        return DictionaryEntry(
            id=int(id_value),
            t_search=_nz(row.get("t-search")),
            t_entry=_nz(row.get("t-entry")),
            e_entry=_nz(row.get("e-entry")),
            t_cat=_nz(row.get("t-cat")),
            t_syn=_nz(row.get("t-syn")),
            t_sample=_nz(row.get("t-sample")),
            t_ant=_nz(row.get("t-ant")),
            t_def=_nz(row.get("t-def")),
            e_related=_nz(row.get("e-related")),
            t_num=_nz(row.get("t-num")),
            notes=_nz(row.get("notes")),
        )


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
            if entry.e_entry:
                translations.add(entry.e_entry)
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
