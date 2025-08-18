from typing import List, Dict, Optional, Any
from dataclasses import dataclass

import re
from pythainlp.util import normalize

from models.dict_schemas import TokenizedThaiWord
from models.subtitle_schemas import AlignedSubtitle, SubtitleEntry, \
    LearningEntry
from utils.local_transcript_util import \
    find_transcript_with_content  # Import your function
from services.dictionary_service import dict_service_freq, dict_service_full
from utils.word_util import process_thai_word
from pythainlp.tokenize import word_tokenize


class SubtitleAlignmentService:
    def __init__(self, overlap_threshold: float = 0.3):
        self.overlap_threshold = overlap_threshold

    def get_subtitles_for_video(self, video_id: str) -> Dict[
        str, Optional[Dict]]:
        """
        Get both Thai and English subtitles for a video ID

        Returns:
            dict with 'thai' and 'english' keys containing subtitle data
        """
        thai_data = find_transcript_with_content(video_id, "Thai")
        english_data = find_transcript_with_content(video_id, "English")

        return {
            "thai": thai_data,
            "english": english_data
        }

    def extract_subtitle_entries(self, transcript_data: Dict[str, Any]) -> List[
        SubtitleEntry]:
        """
        Extract subtitle entries from transcript data, filtering out sound effects
        """
        if not transcript_data or not transcript_data.get("transcript_data"):
            return []

        entries = []
        for item in transcript_data["transcript_data"]:
            # Filter out sound effects and empty text
            text = item.get("text", "").strip()
            if text and not text.startswith('['):
                entries.append(SubtitleEntry(
                    text=text,
                    start=item.get("start", 0.0),
                    duration=item.get("duration", 0.0)
                ))

        return entries

    def calculate_overlap(self, thai_sub: SubtitleEntry,
        eng_sub: SubtitleEntry) -> float:
        """Calculate temporal overlap between two subtitles"""
        overlap_start = max(thai_sub.start, eng_sub.start)
        overlap_end = min(thai_sub.end, eng_sub.end)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_duration = overlap_end - overlap_start
        min_duration = min(thai_sub.duration, eng_sub.duration)

        return overlap_duration / min_duration if min_duration > 0 else 0.0

    def align_subtitles(self, thai_subs: List[SubtitleEntry],
        eng_subs: List[SubtitleEntry]) -> List[AlignedSubtitle]:
        """Align Thai and English subtitles using efficient two-pointer approach"""
        aligned = []

        if not thai_subs or not eng_subs:
            return aligned

        thai_idx = 0
        eng_idx = 0

        while thai_idx < len(thai_subs) and eng_idx < len(eng_subs):
            thai_sub = thai_subs[thai_idx]

            best_match = None
            best_score = 0.0
            best_eng_idx = eng_idx

            # Look ahead in English subtitles for overlaps
            temp_eng_idx = eng_idx
            while temp_eng_idx < len(eng_subs):
                eng_sub = eng_subs[temp_eng_idx]

                # If English subtitle starts too late, no point checking further
                if eng_sub.start > thai_sub.end:
                    break

                # If English subtitle ends before Thai starts, skip it
                if eng_sub.end < thai_sub.start:
                    temp_eng_idx += 1
                    continue

                # Calculate overlap
                overlap = self.calculate_overlap(thai_sub, eng_sub)

                if overlap > best_score and overlap >= self.overlap_threshold:
                    best_score = overlap
                    best_match = eng_sub
                    best_eng_idx = temp_eng_idx

                temp_eng_idx += 1

            # If we found a match, add it to aligned results
            if best_match:
                aligned.append(AlignedSubtitle(
                    thai=thai_sub,
                    english=best_match,
                    overlap_score=best_score
                ))

            # Move to next Thai subtitle
            thai_idx += 1

            if best_match and best_eng_idx >= eng_idx:
                # Move eng_idx to just before the matched subtitle to allow for
                # potential overlaps with the next Thai subtitle
                eng_idx = max(eng_idx, best_eng_idx)

        return aligned

    @staticmethod
    def is_thai_word(text: str) -> bool:
        """
        Check if a word contains Thai characters
        Thai Unicode range: \u0E00-\u0E7F
        """
        # Remove whitespace and check if any Thai characters exist
        # text = text.strip()
        if not text:
            return False

        # Check if the text contains any Thai characters
        thai_pattern = r'[\u0E00-\u0E7F]'
        return bool(re.search(thai_pattern, text))

    def process_thai_sentence(self, thai_text: str) -> List[
        TokenizedThaiWord]:
        """
        Process a Thai sentence into word breakdown with translations
        """
        thai_text = normalize(thai_text)
        tokens = word_tokenize(thai_text, keep_whitespace=False)
        word_breakdown = []

        for token in tokens:
            if token.strip() and self.is_thai_word(token):  # Skip empty tokens

                processed_word = process_thai_word(token, dict_service_freq, dict_service_full)
                word_breakdown.append(
                    processed_word)  # Already a TokenizedThaiWord

        return word_breakdown

    def create_learning_entries(self,
        aligned_subs: List[AlignedSubtitle]) -> List[LearningEntry]:
        """
        Convert aligned subtitles into learning entries with word analysis
        """
        learning_entries = []

        for aligned_sub in aligned_subs:
            word_breakdown = self.process_thai_sentence(
                aligned_sub.thai.text)


            learning_entry = LearningEntry(
                thai_text=aligned_sub.thai.text,
                english_text=aligned_sub.english.text,
                start_time=aligned_sub.thai.start,
                duration=aligned_sub.thai.duration,
                overlap_score=aligned_sub.overlap_score,
                word_breakdown=word_breakdown
            )

            learning_entries.append(learning_entry)

        return learning_entries

    def process_video_for_learning(self, video_id: str) -> Dict[str, Any]:
        """
        Main method: Process a video ID to create learning materials

        Returns:
            Dict containing learning entries and metadata
        """
        # Get subtitle data
        subtitle_data = self.get_subtitles_for_video(video_id)

        thai_data = subtitle_data.get("thai")
        english_data = subtitle_data.get("english")

        # Check if we have both languages
        if not thai_data or not english_data:
            missing = []
            if not thai_data:
                missing.append("Thai")
            if not english_data:
                missing.append("English")

            return {
                "success": False,
                "error": f"Missing subtitles for: {', '.join(missing)}",
                "learning_entries": []
            }

        # Extract subtitle entries
        thai_subs = self.extract_subtitle_entries(thai_data)
        eng_subs = self.extract_subtitle_entries(english_data)

        if not thai_subs or not eng_subs:
            return {
                "success": False,
                "error": "No valid subtitle entries found",
                "learning_entries": []
            }

        # Align subtitles
        aligned_subs = self.align_subtitles(thai_subs, eng_subs)

        if not aligned_subs:
            return {
                "success": False,
                "error": "Could not align any subtitles",
                "learning_entries": []
            }

        # Create learning entries
        learning_entries = self.create_learning_entries(aligned_subs)

        return {
            "success": True,
            "video_id": video_id,
            "total_thai_subs": len(thai_subs),
            "total_english_subs": len(eng_subs),
            "aligned_count": len(aligned_subs),
            "alignment_rate": len(aligned_subs) / len(
                thai_subs) if thai_subs else 0,
            "learning_entries": [
                {
                    "thai_text": entry.thai_text,
                    "english_text": entry.english_text,
                    "start_time": entry.start_time,
                    "duration": entry.duration,
                    "overlap_score": entry.overlap_score,
                    "word_breakdown": [
                        {
                            "thai": word.thai,
                            "transliterated": word.transliterated,
                            "english_translations": word.english_translations
                        }
                        for word in entry.word_breakdown
                    ]
                }
                for entry in learning_entries
            ]
        }


# Instance
subtitle_alignment_service = SubtitleAlignmentService()
