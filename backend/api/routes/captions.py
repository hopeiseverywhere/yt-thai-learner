from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Literal
from io import StringIO
import os

from models.ytb_schemas import DownloadRequest
from backend.utils.ytb_helpers import parse_video_id, transcript_to_srt, transcript_to_vtt
from services.transcript_service import TranscriptService

router = APIRouter()


@router.get("/config")
async def get_config():
    """Get current proxy configuration status."""
    http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    
    return {
        "proxy_configured": bool(http_proxy or https_proxy),
        "http_proxy_set": bool(http_proxy),
        "https_proxy_set": bool(https_proxy),
        "note": "Set HTTP_PROXY and HTTPS_PROXY environment variables to use a proxy for YouTube requests"
    }


@router.get("/available")
async def list_available(
    url: str = Query(..., description="YouTube URL or 11-char video ID")
):
    """List available transcript languages/tracks for a video."""
    video_id = parse_video_id(url)
    return TranscriptService.get_available_transcripts(video_id)


@router.get("/download")
async def download_get(
    url: str = Query(..., description="YouTube URL or 11-char video ID"),
    lang: Optional[str] = Query(None, description="Preferred language code (e.g. 'en', 'th'). If omitted, we'll pick the first available."),
    translate_to: Optional[str] = Query(None, description="Translate transcript to this language code if possible."),
    fmt: Literal['json', 'srt', 'vtt'] = Query('srt', description="Output format"),
    filename: Optional[str] = Query(None, description="Optional filename without extension")
):
    return await _download_common(url, lang, translate_to, fmt, filename)


@router.post("/download")
async def download_post(req: DownloadRequest):
    return await _download_common(req.url, req.lang, req.translate_to, req.fmt, req.filename)


async def _download_common(url: str, lang: Optional[str], translate_to: Optional[str], fmt: str, filename: Optional[str]):
    video_id = parse_video_id(url)
    print(f"Processing download for video_id: {video_id}, lang: {lang}, translate_to: {translate_to}, format: {fmt}")
    
    # Fetch transcript data
    try:
        data, metadata = TranscriptService.fetch_transcript(video_id, lang, translate_to)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        print(f"Unexpected error in _download_common: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

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
    return StreamingResponse(StringIO(body), media_type=media_type, headers=headers)
