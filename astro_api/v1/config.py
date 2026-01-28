"""
API Configuration and Settings
Uses Pydantic Settings for type-safe config management
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = "Vedic Astrology AI API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API Keys
    openai_api_key: str = Field(default="", alias="KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    
    # Rate Limiting
    max_requests_per_minute: int = 30
    
    # CORS Settings
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Use `get_settings.cache_clear()` to reload settings.
    """
    return Settings()


# Singleton instance for convenience
settings = get_settings()
