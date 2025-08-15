from pydantic import BaseModel
from typing import Optional, Literal


class DownloadRequest(BaseModel):
    url: str
    lang: Optional[str] = None  # e.g. 'en', 'th'
    translate_to: Optional[str] = None  # e.g. 'en'
    fmt: Literal['json', 'srt', 'vtt'] = 'srt'
    filename: Optional[str] = None
