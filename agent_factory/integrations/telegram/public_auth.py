"""
Public Telegram Bot Authentication & Authorization
Multi-tenant mode with rate limiting and admin controls
"""

import os
import psycopg2
from functools import wraps
from typing import Optional, Callable
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class PublicAuth:
    """Authentication and authorization for public multi-tenant bot"""

    def __init__(self):
        self.db_url = os.environ.get('NEON_DB_URL')
        if not self.db_url:
            raise ValueError("NEON_DB_URL not found in environment")

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)

    def is_admin(self, telegram_id: int) -> bool:
        """Check if telegram user is an admin"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM admin_users WHERE telegram_id = %s",
                (telegram_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"Error checking admin status: {e}")
            return False

    def get_admin_role(self, telegram_id: int) -> Optional[str]:
        """Get admin role (admin, super_admin, support)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role FROM admin_users WHERE telegram_id = %s",
                (telegram_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting admin role: {e}")
            return None

    def check_rate_limit(self, user_id: str, action_type: str, limit: int, window_minutes: int = 60) -> bool:
        """Check if user is within rate limit"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT check_rate_limit(%s::uuid, %s, %s, %s)",
                (user_id, action_type, limit, window_minutes)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else False
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return False

    def get_user_tier(self, user_id: str) -> str:
        """Get user's subscription tier"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tier FROM rivet_users WHERE id = %s::uuid",
                (user_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else 'free'
        except Exception as e:
            print(f"Error getting user tier: {e}")
            return 'free'

    def get_tier_limits(self, tier: str) -> dict:
        """Get tier limits configuration"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT questions_per_month, machines_max, prints_per_machine, "
                "voice_minutes_per_month, ocr_scans_per_month, features "
                "FROM tier_limits WHERE tier = %s",
                (tier,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return {
                    'questions_per_month': result[0],
                    'machines_max': result[1],
                    'prints_per_machine': result[2],
                    'voice_minutes_per_month': result[3],
                    'ocr_scans_per_month': result[4],
                    'features': result[5]
                }
            return {}
        except Exception as e:
            print(f"Error getting tier limits: {e}")
            return {}

    def log_usage_event(self, user_id: str, event_type: str, event_data: dict = None,
                       tokens_used: int = 0, cost_usd: float = 0.0):
        """Log usage event for analytics and billing"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usage_events (user_id, event_type, event_data, tokens_used, cost_usd) "
                "VALUES (%s::uuid, %s, %s::jsonb, %s, %s)",
                (user_id, event_type, event_data or {}, tokens_used, cost_usd)
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error logging usage event: {e}")


# Global auth instance
auth = PublicAuth()


def admin_only(func: Callable):
    """Decorator to restrict command to admins only"""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        telegram_id = update.effective_user.id
        if not auth.is_admin(telegram_id):
            await update.message.reply_text(
                "This command is restricted to administrators."
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def super_admin_only(func: Callable):
    """Decorator to restrict command to super admins only"""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        telegram_id = update.effective_user.id
        role = auth.get_admin_role(telegram_id)
        if role != 'super_admin':
            await update.message.reply_text(
                "This command is restricted to super administrators."
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def public_command(func: Callable):
    """Decorator for public commands (no restrictions, just logging)"""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        # Log public command usage
        telegram_id = update.effective_user.id
        command = update.message.text.split()[0] if update.message else "unknown"
        # Could add usage logging here if needed
        return await func(update, context, *args, **kwargs)
    return wrapper


def rate_limited(action_type: str, limit: int, window_minutes: int = 60):
    """Decorator to apply rate limiting to commands"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            # BETA MODE: Skip rate limiting entirely
            beta_mode = os.getenv("BETA_MODE", "true").lower() == "true"
            if beta_mode:
                return await func(update, context, *args, **kwargs)

            # Normal rate limiting (post-beta)
            user_id = context.user_data.get('user_id')
            if not user_id:
                await update.message.reply_text(
                    "Please use /start first to initialize your account."
                )
                return

            # Check rate limit
            if not auth.check_rate_limit(user_id, action_type, limit, window_minutes):
                await update.message.reply_text(
                    f"Rate limit exceeded. You can perform {limit} {action_type} actions "
                    f"per {window_minutes} minutes. Please try again later."
                )
                return

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
