"""
Telegram bot configuration and security settings.

Provides:
- TelegramConfig: Bot configuration with security defaults
- Security settings: Rate limiting, validation, PII filtering
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class TelegramConfig(BaseModel):
    """
    Telegram bot configuration with security built-in.

    Security features:
    - Rate limiting (messages per minute)
    - Max message length validation
    - Session TTL (auto-expire old sessions)
    - User whitelist (optional access control)
    - PII filtering
    - Agent execution timeout

    Example:
        >>> config = TelegramConfig(bot_token="123:ABC")
        >>> config.rate_limit
        10
    """

    # Required
    bot_token: str = Field(..., description="Bot token from @BotFather")

    # Security settings
    rate_limit: int = Field(
        default=10,
        description="Max messages per minute per user",
        ge=1,
        le=60
    )

    max_message_length: int = Field(
        default=4000,
        description="Max chars per user message",
        ge=100,
        le=10000
    )

    session_ttl_hours: int = Field(
        default=24,
        description="Hours until session expires",
        ge=1,
        le=168  # 1 week max
    )

    allowed_users: Optional[List[int]] = Field(
        default=None,
        description="Whitelist of allowed chat IDs (None = all users)"
    )

    # Feature flags
    enable_pii_filtering: bool = Field(
        default=True,
        description="Filter PII from responses"
    )

    typing_indicator: bool = Field(
        default=True,
        description="Show typing... while processing"
    )

    # Performance
    max_agent_execution_time: int = Field(
        default=60,
        description="Max seconds for agent execution",
        ge=10,
        le=300  # 5 minutes max
    )

    max_response_chunks: int = Field(
        default=5,
        description="Max message chunks for long responses",
        ge=1,
        le=10
    )

    # Monitoring
    log_conversations: bool = Field(
        default=False,
        description="Log conversation content (GDPR: should be False)"
    )

    @field_validator('bot_token')
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate bot token format."""
        if not v or len(v) < 10:
            raise ValueError("Invalid bot token")
        if ':' not in v:
            raise ValueError("Bot token must contain ':'")
        return v

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        """
        Load configuration from environment variables.

        Environment variables:
        - TELEGRAM_BOT_TOKEN (required)
        - TELEGRAM_RATE_LIMIT (optional)
        - TELEGRAM_ALLOWED_USERS (optional, comma-separated)

        Returns:
            TelegramConfig instance

        Raises:
            ValueError: If TELEGRAM_BOT_TOKEN not set

        Example:
            >>> config = TelegramConfig.from_env()
        """
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not set. "
                "Get token from @BotFather and add to .env"
            )

        # Parse allowed users
        allowed_users = None
        allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USERS")
        if allowed_users_str:
            allowed_users = [
                int(uid.strip())
                for uid in allowed_users_str.split(",")
                if uid.strip()
            ]

        return cls(
            bot_token=bot_token,
            rate_limit=int(os.getenv("TELEGRAM_RATE_LIMIT", "10")),
            allowed_users=allowed_users,
            log_conversations=os.getenv("TELEGRAM_LOG_CONVERSATIONS", "false").lower() == "true"
        )
