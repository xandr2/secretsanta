"""Application configuration management.

This module handles loading configuration from environment variables
for Google OAuth, database, and other application settings.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        database_url: Database connection URL
        google_client_id: Google OAuth client ID
        google_client_secret: Google OAuth client secret
        secret_key: Secret key for session encryption
        telegram_bot_token: Telegram bot token (optional)
    """

    database_url: str = "sqlite+aiosqlite:///./data/santa.db"
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None  # Optional: override auto-detected redirect URI
    secret_key: str = os.urandom(32).hex()
    telegram_bot_token: Optional[str] = None
    telegram_bot_username: Optional[str] = None
    # Cookie settings for session middleware
    cookie_secure: bool = False  # Set to True for HTTPS in production
    cookie_same_site: str = "lax"  # Options: "lax", "strict", "none"
    cookie_domain: Optional[str] = None  # Optional: set cookie domain (e.g., ".xandr2.com")
    log_level: str = "info"  # Log level for uvicorn: "critical", "error", "warning", "info", "debug", "trace"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

