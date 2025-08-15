from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from typing import Optional, List, Dict, Any, Tuple
import os


class TranscriptService:
    @staticmethod
    def _get_api_instance() -> YouTubeTranscriptApi:
        """Create YouTubeTranscriptApi instance with optional proxy configuration."""
        # Check for proxy configuration in environment variables
        http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
        
        if http_proxy or https_proxy:
            print(f"Using proxy configuration - HTTP: {http_proxy}, HTTPS: {https_proxy}")
            proxy_config = GenericProxyConfig(
                http_url=http_proxy,
                https_url=https_proxy or http_proxy  # fallback to http_proxy if https not set
            )
            return YouTubeTranscriptApi(proxy_config=proxy_config)
        else:
            return YouTubeTranscriptApi()

    @staticmethod
    def get_available_transcripts(video_id: str) -> Dict[str, Any]:
        """Get available transcripts and translatable languages for a video."""
        try:
            ytt_api = TranscriptService._get_api_instance()
            transcript_list = ytt_api.list(video_id)
        except VideoUnavailable:
            raise HTTPException(status_code=404, detail="Video unavailable or does not exist.")
        except TranscriptsDisabled:
            raise HTTPException(status_code=404, detail="Transcripts are disabled for this video.")
        except Exception as e:
            error_msg = str(e)
            if "blocking requests" in error_msg.lower() or "ip" in error_msg.lower():
                raise HTTPException(
                    status_code=503, 
                    detail="YouTube is blocking requests from this IP address. Please configure a proxy using HTTP_PROXY and HTTPS_PROXY environment variables, or try again later from a different network."
                )
            raise HTTPException(status_code=500, detail=f"Failed to list transcripts: {e}")

        avail = []
        for t in transcript_list:
            avail.append({
                "language": t.language,
                "language_code": t.language_code,
                "is_generated": t.is_generated,
                "is_translatable": t.is_translatable,
            })
        
        # Also include language codes that can be translated to
        try:
            first_transcript = transcript_list.find_transcript([avail[0]['language_code']])
            translatable_to = sorted({x['language_code'] for x in first_transcript.translation_languages}) if first_transcript.translation_languages else []
        except Exception:
            translatable_to = []

        return {
            "video_id": video_id, 
            "available": avail, 
            "translatable_to": translatable_to
        }

    @staticmethod
    def fetch_transcript(
        video_id: str, 
        lang: Optional[str] = None, 
        translate_to: Optional[str] = None
    ) -> Tuple[List[dict], dict]:
        """Fetch transcript data with optional language preference and translation."""
        try:
            ytt_api = TranscriptService._get_api_instance()

            # Step 1 — get available transcripts
            transcript_list = ytt_api.list(video_id)

            # Step 2 — pick transcript based on lang param (or first available if not provided)
            if lang:
                transcript = transcript_list.find_transcript([lang])
            else:
                # just take the first one
                transcript = transcript_list[0]

            # Step 3 — optionally translate
            if translate_to:
                if transcript.is_translatable:
                    transcript = transcript.translate(translate_to)
                else:
                    raise HTTPException(status_code=400, detail=f"Transcript cannot be translated to {translate_to}")

            # Step 4 — fetch and return
            fetched_transcript = transcript.fetch()
            
            # Convert to raw data format
            data = fetched_transcript.to_raw_data()

            metadata = {
                "video_id": video_id,
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "is_translatable": transcript.is_translatable,
            }
            return data, metadata

        except NoTranscriptFound:
            raise HTTPException(status_code=404, detail=f"No transcript found for language {lang or 'default'}")
        except TranscriptsDisabled:
            raise HTTPException(status_code=404, detail="Transcripts are disabled for this video.")
        except VideoUnavailable:
            raise HTTPException(status_code=404, detail="Video unavailable or does not exist.")
        except Exception as e:
            error_msg = str(e)
            if "blocking requests" in error_msg.lower() or "ip" in error_msg.lower():
                raise HTTPException(
                    status_code=503, 
                    detail="YouTube is blocking requests from this IP address. Please configure a proxy using HTTP_PROXY and HTTPS_PROXY environment variables, or try again later from a different network."
                )
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
