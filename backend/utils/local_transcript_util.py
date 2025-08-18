import re
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings


# --- Local file saving functions ---

def get_temp_dir() -> Path:
    """Get the temp directory for saving transcripts"""
    return Path(settings.transcript_temp_dir)


def get_index_file_path() -> Path:
    """Get the path to the index file"""
    return get_temp_dir() / "index.json"


def ensure_temp_directory() -> Path:
    """Ensure the temp directory exists and return the path"""
    temp_dir = get_temp_dir()

    # Create date-based subdirectory
    today = datetime.now().strftime('%Y-%m-%d')
    daily_dir = temp_dir / today

    try:
        daily_dir.mkdir(parents=True, exist_ok=True)
        return daily_dir
    except Exception as e:
        print(f"Warning: Could not create temp directory {daily_dir}: {e}")
        return temp_dir


def generate_filename(video_id: str, language: str,
    metadata: Dict[str, Any]) -> str:
    """Generate a unique filename for the transcript"""
    # timestamp = datetime.now().strftime('%H%M%S')

    # Add translation info if applicable
    if metadata.get('translated_from'):
        lang_part = f"{metadata['translated_from']}-to-{language}"
    else:
        lang_part = language

    # Sanitize video_id for filename
    safe_video_id = re.sub(r'[^\w\-]', '', video_id)

    return f"{safe_video_id}_{lang_part}.json"


# --- Index Management ---
def load_index() -> Dict[str, Dict[str, Any]]:
    """Load the video index from file."""
    index_file = get_index_file_path()
    try:
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load index: {e}")
    return {}


def save_index(index_data: Dict[str, Dict[str, Any]]) -> None:
    """Save the video index to file."""
    index_file = get_index_file_path()
    try:
        # Ensure directory exists
        index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save index: {e}")


def update_index(video_id: str, language: str, file_path: str,
    metadata: Dict[str, Any]) -> None:
    """Update the index when a new transcript is saved."""
    index = load_index()

    # Create unique key for video_id + language combination
    key = f"{video_id}_{language}"

    index[key] = {
        "video_id": video_id,
        "language": language,
        "file_path": file_path,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "saved_at": datetime.now().isoformat(),
        "metadata": metadata
    }

    save_index(index)


# --- Search Transcript Management ---
def find_transcript_by_video_id(video_id: str, language: str = None) -> \
    Optional[Dict[str, Any]]:
    """Find transcript file path using the index."""
    index = load_index()

    if language:
        # Look for specific language
        key = f"{video_id}_{language}"
        if key in index:
            entry = index[key]
            file_path = Path(entry["file_path"])
            if file_path.exists():
                return entry
    else:
        # Look for any language for this video
        for key, entry in index.items():
            if entry["video_id"] == video_id:
                file_path = Path(entry["file_path"])
                if file_path.exists():
                    return entry

    return None


def find_transcript_with_content(video_id: str, language: str = None) -> \
    Optional[Dict[str, Any]]:
    """
    Find transcript file and return both index info and full content.
    Returns combined data with index metadata + actual transcript content.
    """
    index = load_index()

    if language:
        # Look for specific language
        key = f"{video_id}_{language}"
        if key in index:
            entry = index[key]
            file_path = Path(entry["file_path"])
            if file_path.exists():
                # Load the actual transcript content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = json.load(f)

                    # Combine index info with file content
                    return {
                        "index_info": entry,
                        "content": file_content,
                        "transcript_data": file_content.get("transcript_data",
                                                            []),
                        "metadata": file_content.get("metadata", {}),
                        "transcript_count": file_content.get("transcript_count",
                                                             0),
                        "fetched_at": file_content.get("fetched_at"),
                        "source_url": file_content.get("source_url")
                    }
                except Exception as e:
                    print(f"Error loading transcript content: {e}")
                    # Return just index info if file can't be read
                    return {"index_info": entry, "content": None,
                            "error": "Failed to load content"}
    else:
        # Look for any language for this video
        for key, entry in index.items():
            if entry["video_id"] == video_id:
                file_path = Path(entry["file_path"])
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = json.load(f)

                        return {
                            "index_info": entry,
                            "content": file_content,
                            "transcript_data": file_content.get(
                                "transcript_data", []),
                            "metadata": file_content.get("metadata", {}),
                            "transcript_count": file_content.get(
                                "transcript_count", 0),
                            "fetched_at": file_content.get("fetched_at"),
                            "source_url": file_content.get("source_url")
                        }
                    except Exception as e:
                        print(f"Error loading transcript content: {e}")
                        return {"index_info": entry, "content": None,
                                "error": "Failed to load content"}

    return None


def find_all_transcripts_with_content(video_id: str) -> List[Dict[str, Any]]:
    """
    Find all transcripts for a video ID and return index info + content for each.
    """
    index = load_index()
    results = []

    for key, entry in index.items():
        if entry["video_id"] == video_id:
            file_path = Path(entry["file_path"])
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = json.load(f)

                    result = {
                        "index_info": entry,
                        "content": file_content,
                        "transcript_data": file_content.get("transcript_data",
                                                            []),
                        "metadata": file_content.get("metadata", {}),
                        "transcript_count": file_content.get("transcript_count",
                                                             0),
                        "fetched_at": file_content.get("fetched_at"),
                        "source_url": file_content.get("source_url")
                    }
                    results.append(result)
                except Exception as e:
                    print(f"Error loading transcript content for {key}: {e}")
                    # Still include entry with error info
                    results.append({
                        "index_info": entry,
                        "content": None,
                        "error": "Failed to load content"
                    })

    return results


def cleanup_index() -> int:
    """Remove index entries for files that no longer exist"""
    index = load_index()
    cleaned_count = 0

    keys_to_remove = []
    for key, entry in index.items():
        file_path = Path(entry["file_path"])
        if not file_path.exists():
            keys_to_remove.append(key)
            cleaned_count += 1

    for key in keys_to_remove:
        del index[key]

    if cleaned_count > 0:
        save_index(index)
        print(f"Cleaned up {cleaned_count} stale index entries")

    return cleaned_count


# --- File Operations ---
def save_transcript_to_file(
    video_id: str,
    transcript_data: List[dict],
    metadata: Dict[str, Any],
    source_url: Optional[str] = None
) -> Optional[str]:
    """
    Save transcript data to a local JSON file.
    Overwrites existing file with same video_id and language.
    Returns the file path if successful, None if failed.
    """
    # Check if saving is enabled
    if not settings.enable_local_save:
        return None

    try:
        # Ensure directory exists
        save_dir = ensure_temp_directory()

        # Generate simple filename
        language = metadata.get('language', 'unknown')
        filename = generate_filename(video_id, language, metadata)
        file_path = save_dir / filename

        # Prepare data to save
        save_data = {
            "video_id": video_id,
            "source_url": source_url or f"https://youtube.com/watch?v={video_id}",
            "fetched_at": datetime.now().isoformat(),
            "metadata": metadata,
            "transcript_count": len(transcript_data),
            "transcript_data": transcript_data
        }

        # Save to file (will overwrite if exists)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"Transcript saved: {file_path}")

        # Update index
        update_index(video_id, language, str(file_path), metadata)

        return str(file_path)

    except Exception as e:
        print(f"Warning: Failed to save transcript to file: {e}")
        return None


def load_transcript_from_file(video_id: str, language: str = None) -> Optional[
    Dict[str, Any]]:
    """
    Load transcript using index for fast lookup.
    Returns the transcript data if found, None otherwise.
    """
    # Try index first (fast)
    index_entry = find_transcript_by_video_id(video_id, language)
    if index_entry:
        file_path = Path(index_entry["file_path"])
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded transcript from index: {file_path}")
                return data
        except Exception:
            # File exists in index but not on disk, clean up
            print(f"Stale index entry, falling back to directory search")

    # Fallback to directory search (slow)
    return _load_transcript_from_directory(video_id, language)


def _load_transcript_from_directory(video_id: str, language: str = None) -> \
    Optional[Dict[str, Any]]:
    """
    Fallback method to search for transcript in directories
    """
    try:
        temp_dir = get_temp_dir()
        if not temp_dir.exists():
            return None

        # Simple filename pattern: videoid_lang.json
        if language:
            filename = f"{video_id}_{language}.json"
        else:
            # If no language specified, look for any file starting with video_id
            pattern = f"{video_id}_*.json"

        # Check today and yesterday's directories
        for days_back in range(2):
            check_date = datetime.now() - timedelta(days=days_back)
            date_str = check_date.strftime('%Y-%m-%d')
            date_dir = temp_dir / date_str

            if date_dir.exists():
                if language:
                    # Look for specific file
                    file_path = date_dir / filename
                    if file_path.exists():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                print(
                                    f"Loaded transcript from directory: {file_path}")
                                return data
                        except Exception:
                            continue
                else:
                    # Look for any file matching video_id pattern
                    for file_path in date_dir.glob(f"{video_id}_*.json"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if data.get('video_id') == video_id:
                                    print(
                                        f"Loaded transcript from directory: {file_path}")
                                    return data
                        except Exception:
                            continue

        return None

    except Exception as e:
        print(f"Warning: Failed to load transcript from directory: {e}")
        return None


def cleanup_old_files(days_to_keep: int = None) -> int:
    """
    Clean up transcript files older than specified days.
    Also cleans up the index.
    Returns the number of files deleted.
    """
    if days_to_keep is None:
        days_to_keep = settings.transcript_retention_days

    try:
        temp_dir = get_temp_dir()
        if not temp_dir.exists():
            return 0

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0

        # Clean up old daily directories
        for date_dir in temp_dir.iterdir():
            if date_dir.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}',
                                              date_dir.name):
                try:
                    dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                    if dir_date < cutoff_date:
                        # Delete all files in the directory
                        for file_path in date_dir.iterdir():
                            if file_path.is_file() and file_path.suffix == '.json':
                                file_path.unlink()
                                deleted_count += 1

                        # Remove empty directory
                        if not any(date_dir.iterdir()):
                            date_dir.rmdir()

                except ValueError:
                    continue  # Skip directories that don't match date format

        # Clean up stale index entries
        index_cleaned = cleanup_index()

        if deleted_count > 0:
            print(
                f"Cleaned up {deleted_count} old transcript files and {index_cleaned} stale index entries")

        return deleted_count

    except Exception as e:
        print(f"Warning: Failed to cleanup old files: {e}")
        return 0


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about cached transcript files."""
    try:
        temp_dir = get_temp_dir()
        if not temp_dir.exists():
            return {"total_files": 0, "total_size": 0, "directories": [],
                    "index_entries": 0}

        total_files = 0
        total_size = 0
        directories = []

        for date_dir in temp_dir.iterdir():
            if date_dir.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}',
                                              date_dir.name):
                dir_files = 0
                dir_size = 0

                for file_path in date_dir.glob("*.json"):
                    if file_path.is_file():
                        dir_files += 1
                        dir_size += file_path.stat().st_size

                if dir_files > 0:
                    directories.append({
                        "date": date_dir.name,
                        "files": dir_files,
                        "size_bytes": dir_size
                    })
                    total_files += dir_files
                    total_size += dir_size

        # Get index stats
        index = load_index()
        index_entries = len(index)

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "index_entries": index_entries,
            "directories": sorted(directories, key=lambda x: x["date"],
                                  reverse=True)
        }

    except Exception as e:
        print(f"Warning: Failed to get cache stats: {e}")
        return {"error": str(e)}
