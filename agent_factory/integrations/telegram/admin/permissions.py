"""
Permission Management for Telegram Admin Panel

Provides role-based access control for admin commands:
- Admin: Full access to all features
- Viewer: Read-only access
- Blocked: No access

Usage:
    from agent_factory.integrations.telegram.admin.permissions import require_admin

    @require_admin
    async def handle_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Only authorized admins can access this
        pass
"""

import os
import logging
from typing import Optional, Callable
from functools import wraps
from enum import Enum

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """User roles for admin panel"""
    ADMIN = "admin"
    VIEWER = "viewer"
    BLOCKED = "blocked"


class PermissionManager:
    """
    Manages user permissions for admin panel.

    Attributes:
        admins: Set of user IDs with admin access
        viewers: Set of user IDs with read-only access
    """

    def __init__(self):
        """Initialize permission manager from environment"""
        # Load authorized users from .env
        authorized = os.getenv("AUTHORIZED_TELEGRAM_USERS", "")
        self.admins = set()

        if authorized:
            user_ids = [uid.strip() for uid in authorized.split(",") if uid.strip()]
            self.admins = {int(uid) for uid in user_ids if uid.isdigit()}

        # Viewers (read-only access) - can be added later
        self.viewers = set()

        logger.info(f"Permissions initialized: {len(self.admins)} admins, {len(self.viewers)} viewers")

    def get_role(self, user_id: int) -> Role:
        """
        Get role for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            User role (admin/viewer/blocked)
        """
        if user_id in self.admins:
            return Role.ADMIN
        elif user_id in self.viewers:
            return Role.VIEWER
        else:
            return Role.BLOCKED

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admins

    def is_viewer(self, user_id: int) -> bool:
        """Check if user is viewer"""
        return user_id in self.viewers

    def has_access(self, user_id: int) -> bool:
        """Check if user has any access (admin or viewer)"""
        return self.is_admin(user_id) or self.is_viewer(user_id)

    def can_write(self, user_id: int) -> bool:
        """Check if user can perform write operations (admin only)"""
        return self.is_admin(user_id)

    def add_admin(self, user_id: int):
        """Add user as admin"""
        self.admins.add(user_id)
        if user_id in self.viewers:
            self.viewers.remove(user_id)
        logger.info(f"Added admin: {user_id}")

    def add_viewer(self, user_id: int):
        """Add user as viewer (read-only)"""
        if user_id not in self.admins:
            self.viewers.add(user_id)
            logger.info(f"Added viewer: {user_id}")

    def remove_access(self, user_id: int):
        """Remove all access from user"""
        self.admins.discard(user_id)
        self.viewers.discard(user_id)
        logger.info(f"Removed access: {user_id}")

    def log_access_attempt(self, user_id: int, command: str, allowed: bool):
        """Log access attempts for audit"""
        status = "ALLOWED" if allowed else "DENIED"
        role = self.get_role(user_id).value
        logger.info(f"Access {status}: user={user_id} role={role} command={command}")


# Global permission manager instance
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """Get global permission manager instance"""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin role for command.

    Usage:
        @require_admin
        async def handle_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Only admins can access this
            pass
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        pm = get_permission_manager()

        if not pm.is_admin(user_id):
            role = pm.get_role(user_id)
            pm.log_access_attempt(user_id, func.__name__, allowed=False)

            await update.message.reply_text(
                "❌ *Access Denied*\n\n"
                "This command requires admin privileges.\n"
                f"Your role: {role.value}\n\n"
                "Contact the system administrator if you need access.",
                parse_mode="Markdown"
            )
            return

        pm.log_access_attempt(user_id, func.__name__, allowed=True)
        return await func(update, context, *args, **kwargs)

    return wrapper


def require_access(func: Callable) -> Callable:
    """
    Decorator to require any access (admin or viewer).

    Usage:
        @require_access
        async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Admins and viewers can access this
            pass
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        pm = get_permission_manager()

        if not pm.has_access(user_id):
            pm.log_access_attempt(user_id, func.__name__, allowed=False)

            await update.message.reply_text(
                "❌ *Access Denied*\n\n"
                "You are not authorized to use this bot.\n\n"
                "Contact the system administrator if you need access.",
                parse_mode="Markdown"
            )
            return

        pm.log_access_attempt(user_id, func.__name__, allowed=True)
        return await func(update, context, *args, **kwargs)

    return wrapper
