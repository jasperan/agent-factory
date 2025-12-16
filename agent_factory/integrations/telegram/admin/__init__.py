"""
Telegram Admin Panel - Universal Remote Control

Comprehensive admin interface for Agent Factory with:
- Agent monitoring and control
- Content review and approval
- GitHub Actions integration
- KB management
- Analytics dashboard
- System health checks

Usage:
    from agent_factory.integrations.telegram.admin import AdminDashboard

    admin = AdminDashboard()
    app.add_handler(CommandHandler("admin", admin.handle_admin))
"""

from .dashboard import AdminDashboard
from .permissions import PermissionManager, require_admin

__all__ = [
    "AdminDashboard",
    "PermissionManager",
    "require_admin",
]
