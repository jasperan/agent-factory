"""
Telegram bot integration for Agent Factory.

Provides full-featured Telegram bot with:
- Multi-agent support (research, coding, bob)
- Session management (per-user state)
- Security (rate limiting, PII filtering, user whitelist)
- Approval workflows (Factor 7 preview)

Usage:
    >>> from agent_factory.integrations.telegram import TelegramBot, TelegramConfig
    >>> config = TelegramConfig.from_env()
    >>> bot = TelegramBot(config)
    >>> await bot.run()
"""

from .bot import TelegramBot
from .config import TelegramConfig
from .session_manager import TelegramSessionManager
from .formatters import ResponseFormatter

__all__ = [
    "TelegramBot",
    "TelegramConfig",
    "TelegramSessionManager",
    "ResponseFormatter"
]
