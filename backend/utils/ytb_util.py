import re
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from io import StringIO
from config.settings import settings

# --- Video ID parsing ---
VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})")


def parse_video_id(url_or_id: str) -> str:
    """
    Extract YouTube video ID from URL or validate existing ID.
    Args:
        url_or_id: YouTube URL or 11-character video ID
    Returns:
        11-character video ID
    Raises:
        HTTPException: If video ID cannot be parsed
    """
    url_or_id = url_or_id.strip()

    # Already looks like an 11-char ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id

    # Extract from URL
    match = VIDEO_ID_RE.search(url_or_id)
    if match:
        return match.group(1)

    raise HTTPException(
        status_code=400,
        detail="Could not parse YouTube video ID from 'url'. Provide a full URL or the 11-character video ID."
    )


# --- Timestamp formatting ---
def seconds_to_timestamp_srt(s: float) -> str:
    """
        Convert seconds to SRT timestamp format (HH:MM:SS,mmm)
        Args:
            s: Time in seconds
        Returns:
            Formatted timestamp string
        """
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    millis = int(round((s - int(s)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def seconds_to_timestamp_vtt(s: float) -> str:
    """
        Convert seconds to VTT timestamp format (HH:MM:SS.mmm)
        Args:
            s: Time in seconds
        Returns:
            Formatted timestamp string
    """
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    millis = int(round((s - int(s)) * 1000))
    # VTT uses '.' as decimal separator
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


# --- Format converters ---
def transcript_to_srt(transcript: List[dict]) -> str:
    """
   Convert transcript data to SRT format.
   Args:
       transcript: List of transcript items with 'text', 'start', 'duration'
   Returns:
       SRT formatted string
   """
    # Each item has: {"text": str, "start": float, "duration": float}
    out = StringIO()
    for i, item in enumerate(transcript, start=1):
        start = item.get("start", 0.0)
        dur = item.get("duration", 0.0)
        end = start + dur
        text = (item.get("text") or "").replace("\n", "\n")
        out.write(
            f"{i}\n{seconds_to_timestamp_srt(start)} --> {seconds_to_timestamp_srt(end)}\n{text}\n\n")
    return out.getvalue()


def transcript_to_vtt(transcript: List[dict]) -> str:
    """
        Convert transcript data to VTT format.
        Args:
            transcript: List of transcript items with 'text', 'start', 'duration'
        Returns:
            VTT formatted string
    """
    out = StringIO()
    out.write("WEBVTT\n\n")
    for item in transcript:
        start = item.get("start", 0.0)
        dur = item.get("duration", 0.0)
        end = start + dur
        text = (item.get("text") or "").replace("\n", "\n")
        out.write(
            f"{seconds_to_timestamp_vtt(start)} --> {seconds_to_timestamp_vtt(end)}\n{text}\n\n")
    return out.getvalue()
