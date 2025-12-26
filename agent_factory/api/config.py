"""API Configuration."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment."""
    
    # App
    app_name: str = "Rivet API"
    app_url: str = "https://rivet.io"
    api_url: str = "https://api.rivet.io"
    debug: bool = False
    
    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_basic: str = ""
    stripe_price_pro: str = ""
    stripe_price_enterprise: str = ""
    
    # Database
    database_url: str = ""
    
    # External APIs
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    telegram_bot_token: str = ""
    
    # Atlas CMMS
    atlas_api_url: str = "http://localhost:8080/api"
    atlas_api_key: str = ""
    
    # Redis (optional)
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
