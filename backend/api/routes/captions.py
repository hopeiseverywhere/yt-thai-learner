from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Literal
from io import StringIO
import os

from config.languages import AllowedLanguageNames, AllowedLanguageCodes
from utils.ytb_util import (
    parse_video_id, transcript_to_srt, transcript_to_vtt,
)
from utils.local_transcript_util import (save_transcript_to_file, cleanup_old_files,
                                         load_transcript_from_file, get_cache_stats,
                                         find_transcript_by_video_id, load_index,
                                         cleanup_index,
                                         find_all_transcripts_with_content,
                                         find_transcript_with_content)
from services.transcript_service import TranscriptService
from config.settings import settings

router = APIRouter()


@router.get("/config")
async def get_config():
    """Get current proxy and cache configuration status"""
    http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')

    return {
        "proxy_configured": bool(http_proxy or https_proxy),
        "http_proxy_set": bool(http_proxy),
        "https_proxy_set": bool(https_proxy),
        "local_save_enabled": settings.enable_local_save,
        "temp_directory": settings.transcript_temp_dir,
        "retention_days": settings.transcript_retention_days,
        "note": "Set HTTP_PROXY and HTTPS_PROXY environment variables to use a proxy for YouTube requests"
    }


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get statistics about cached transcript files."""
    return get_cache_stats()


@router.post("/cache/cleanup")
async def cleanup_cache(days_to_keep: Optional[int] = Query(None,
                                                            description="Days to keep (default from env)")):
    """Clean up old cached transcript files."""
    deleted_count = cleanup_old_files(days_to_keep)
    return {
        "deleted_files": deleted_count,
        "message": f"Cleaned up {deleted_count} old transcript files"
    }


@router.get("/search/{video_id}")
async def search_cached_transcripts(
    video_id: str,
    lang: Optional[AllowedLanguageNames] = Query(None,
                                                 description="Specific language (e.g. 'English, 'Thai') to search for"),
    include_content: bool = Query(True,
                                  description="Include actual transcript content in response")
):
    """Search for cached transcripts by video ID with full content"""

    if include_content:
        if lang:
            # Search for specific language with content
            result = find_transcript_with_content(video_id, lang)
            if result:
                return {
                    "found": True,
                    "video_id": video_id,
                    "language": lang,
                    "transcript": result
                }
            else:
                return {
                    "found": False,
                    "video_id": video_id,
                    "language": lang,
                    "message": f"No cached transcript found for {video_id} in {lang}"
                }
        else:
            # Search for all languages with content
            results = find_all_transcripts_with_content(video_id)
            return {
                "found": len(results) > 0,
                "video_id": video_id,
                "count": len(results),
                "transcripts": results
            }
    else:
        # Original behavior - index info only
        if lang:
            result = find_transcript_by_video_id(video_id, lang)
            if result:
                return {"found": True, "transcript": result}
            else:
                return {"found": False,
                        "message": f"No cached transcript found for {video_id} in {lang}"}
        else:
            index = load_index()
            results = []
            for key, entry in index.items():
                if entry["video_id"] == video_id:
                    results.append(entry)

            return {
                "found": len(results) > 0,
                "count": len(results),
                "transcripts": results
            }


@router.get("/index/stats")
async def get_index_stats():
    """Get statistics about the transcript index"""
    index = load_index()
    unique_videos = set()
    languages = {}

    for entry in index.values():
        unique_videos.add(entry["video_id"])
        lang = entry["language"]
        languages[lang] = languages.get(lang, 0) + 1

    return {
        "total_entries": len(index),
        "unique_videos": len(unique_videos),
        "languages": languages
    }


@router.post("/index/cleanup")
async def cleanup_index_endpoint():
    """Clean up transcript index entries"""
    cleaned_count = cleanup_index()
    return {
        "cleaned_entries": cleaned_count,
        "message": f"Cleaned up {cleaned_count} stale index entries"
    }


@router.get("/available")
async def list_available(
    url: str = Query(..., description="YouTube URL or 11-char video ID")
):
    """List available transcript languages/tracks for a video"""
    video_id = parse_video_id(url)
    return TranscriptService.get_available_transcripts(video_id)


@router.get("/download")
async def download_get(
    url: str = Query(..., description="YouTube URL or 11-char video ID"),
    lang: Optional[AllowedLanguageCodes] = Query(None,
                                                 description="Preferred language code (e.g. 'en', 'th'). If omitted, we'll pick the first available."),
    translate_to: Optional[AllowedLanguageCodes] = Query(None,
                                                         description="Translate transcript to this language code if possible."),
    fmt: Literal['json', 'srt', 'vtt'] = Query('json',
                                               description="Output format"),
    filename: Optional[str] = Query(None,
                                    description="Optional filename without extension")
):
    return await _download_common(url, lang, translate_to, fmt, filename)


# @router.post("/download")
# async def download_post(req: DownloadRequest):
#     return await _download_common(req.url, req.lang, req.translate_to, req.fmt,
#                                   req.filename)


async def _download_common(url: str, lang: Optional[AllowedLanguageNames],
    translate_to: Optional[AllowedLanguageCodes], fmt: str,
    filename: Optional[str],
    use_cache: bool = True):
    video_id = parse_video_id(url)
    print(
        f"Processing download for video_id: {video_id}, lang: {lang}, translate_to: {translate_to}, format: {fmt}")

    # Try to load from cache first
    cached_data = None
    if use_cache:
        target_lang = translate_to or lang
        cached_data = load_transcript_from_file(video_id, target_lang)
        if cached_data:
            print(f"Using cached transcript for {video_id}")
            data = cached_data['transcript_data']
            metadata = cached_data['metadata']
            metadata['from_cache'] = True

    # Fetch from API if not cached
    if not cached_data:
        try:
            data, metadata = TranscriptService.fetch_transcript(video_id, lang,
                                                                translate_to)
            metadata['from_cache'] = False

            # Save to local file (async, don't block response)
            save_transcript_to_file(video_id, data, metadata, url)

        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            print(f"Unexpected error in _download_common: {e}")
            raise HTTPException(status_code=500,
                                detail=f"Unexpected error: {e}")

    # Prepare output
    if fmt == 'json':
        return JSONResponse(content={
            **metadata,
            "items": data,
        })

    if fmt == 'srt':
        body = transcript_to_srt(data)
        media_type = 'application/x-subrip'
        ext = 'srt'
    elif fmt == 'vtt':
        body = transcript_to_vtt(data)
        media_type = 'text/vtt'
        ext = 'vtt'
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

    fname = filename or f"{video_id}_{metadata.get('language', 'xx')}"
    headers = {
        "Content-Disposition": f"attachment; filename=\"{fname}.{ext}\""
    }
    return StreamingResponse(StringIO(body), media_type=media_type,
                             headers=headers)
