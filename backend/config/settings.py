from pydantic import field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # Transcript Configuration
    transcript_temp_dir: str = "./temp/transcripts"
    transcript_retention_days: int = 7
    enable_local_save: bool = True

    # Proxy Configuration
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None

    # API Configuration
    api_title: str = "YouTube Subtitles Downloader"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    @field_validator('transcript_temp_dir')
    def validate_temp_dir(cls, v):
        # Ensure path is absolute for consistency
        return str(Path(v).resolve())

    @field_validator('transcript_retention_days')
    def validate_retention_days(cls, v):
        if v < 1:
            raise ValueError('Retention days must be at least 1')
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
