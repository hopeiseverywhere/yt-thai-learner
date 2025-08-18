import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from models.dict_schemas import TokenizedThaiWord


@dataclass
class SubtitleEntry:
    text: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass
class AlignedSubtitle:
    thai: SubtitleEntry
    english: SubtitleEntry
    overlap_score: float

@dataclass
class LearningEntry:
    thai_text: str
    english_text: str
    start_time: float
    duration: float
    overlap_score: float
    word_breakdown: List[TokenizedThaiWord]