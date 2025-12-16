"""
Main Admin Dashboard for Telegram

Provides the central control interface with inline keyboard menu:
- 🤖 Agents (monitoring and control)
- 📝 Content (review and approval)
- 🚀 Deploy (GitHub Actions)
- 📚 KB (knowledge base management)
- 📊 Metrics (analytics dashboard)
- ⚙️ System (health checks)

Usage:
    from agent_factory.integrations.telegram.admin import AdminDashboard

    admin = AdminDashboard()
    app.add_handler(CommandHandler("admin", admin.handle_admin))
    app.add_handler(CallbackQueryHandler(admin.handle_callback, pattern="^menu_"))
"""

import logging
from typing import Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

from .permissions import require_access, get_permission_manager
from .command_parser import CommandParser

logger = logging.getLogger(__name__)


class AdminDashboard:
    """
    Main dashboard for Telegram admin panel.

    Provides menu-based interface for all admin functions.
    Routes requests to specialized managers (agents, content, etc).
    """

    def __init__(self):
        """Initialize admin dashboard"""
        self.command_parser = CommandParser()
        self.permission_manager = get_permission_manager()

        # Managers will be initialized in Phase 2-7
        self.agent_manager = None
        self.content_reviewer = None
        self.github_actions = None
        self.kb_manager = None
        self.analytics = None
        self.system_control = None

        logger.info("AdminDashboard initialized")

    @require_access
    async def handle_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /admin command - show main menu.

        Args:
            update: Telegram update
            context: Callback context
        """
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Admin"
        role = self.permission_manager.get_role(user_id)

        # Build main menu keyboard
        keyboard = [
            [
                InlineKeyboardButton("🤖 Agents", callback_data="menu_agents"),
                InlineKeyboardButton("📝 Content", callback_data="menu_content"),
            ],
            [
                InlineKeyboardButton("🚀 Deploy", callback_data="menu_deploy"),
                InlineKeyboardButton("📚 KB", callback_data="menu_kb"),
            ],
            [
                InlineKeyboardButton("📊 Metrics", callback_data="menu_metrics"),
                InlineKeyboardButton("⚙️ System", callback_data="menu_system"),
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="menu_help"),
                InlineKeyboardButton("🔄 Refresh", callback_data="menu_refresh"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Build status summary
        status = await self._get_system_status()

        message = (
            f"🎛️ *Agent Factory Admin Panel*\n\n"
            f"Welcome, {user_name}!\n"
            f"Role: `{role.value}`\n\n"
            f"*Quick Status:*\n"
            f"{status}\n\n"
            f"Select a section to manage:"
        )

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"Admin panel opened by user {user_id}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle inline keyboard button callbacks.

        Args:
            update: Telegram update
            context: Callback context
        """
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        user_id = update.effective_user.id

        logger.info(f"Admin callback: {callback_data} from user {user_id}")

        # Route to appropriate handler
        if callback_data == "menu_agents":
            await self._show_agents_menu(query, context)
        elif callback_data == "menu_content":
            await self._show_content_menu(query, context)
        elif callback_data == "menu_deploy":
            await self._show_deploy_menu(query, context)
        elif callback_data == "menu_kb":
            await self._show_kb_menu(query, context)
        elif callback_data == "menu_metrics":
            await self._show_metrics_menu(query, context)
        elif callback_data == "menu_system":
            await self._show_system_menu(query, context)
        elif callback_data == "menu_help":
            await self._show_help(query, context)
        elif callback_data == "menu_refresh":
            await self._refresh_dashboard(query, context)
        elif callback_data == "menu_back":
            await self._back_to_main(query, context)

    async def _show_agents_menu(self, query, context):
        """Show agents submenu"""
        keyboard = [
            [InlineKeyboardButton("📊 View Status", callback_data="agents_status")],
            [InlineKeyboardButton("📜 View Logs", callback_data="agents_logs")],
            [InlineKeyboardButton("⏸️ Stop Agent", callback_data="agents_stop")],
            [InlineKeyboardButton("▶️ Start Agent", callback_data="agents_start")],
            [InlineKeyboardButton("◀️ Back", callback_data="menu_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🤖 *Agent Management*\n\n"
            "Monitor and control your agents:\n"
            "• View real-time status\n"
            "• Stream logs\n"
            "• Start/stop agents\n"
            "• Performance metrics\n\n"
            "Select an action:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _show_content_menu(self, query, context):
        """Show content review submenu"""
        keyboard = [
            [InlineKeyboardButton("📋 Approval Queue", callback_data="content_queue")],
            [InlineKeyboardButton("🎥 YouTube", callback_data="content_youtube")],
            [InlineKeyboardButton("💬 Reddit", callback_data="content_reddit")],
            [InlineKeyboardButton("📱 Social Media", callback_data="content_social")],
            [InlineKeyboardButton("◀️ Back", callback_data="menu_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Get pending count (placeholder for now)
        pending_count = "..."

        await query.edit_message_text(
            "📝 *Content Review*\n\n"
            f"Pending approval: {pending_count}\n\n"
            "Review and approve content before publishing:\n"
            "• YouTube videos\n"
            "• Reddit posts\n"
            "• Social media content\n\n"
            "Select content type:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _show_deploy_menu(self, query, context):
        """Show deployment submenu"""
        keyboard = [
            [InlineKeyboardButton("🚀 Deploy to VPS", callback_data="deploy_vps")],
            [InlineKeyboardButton("🔄 View Workflows", callback_data="deploy_workflows")],
            [InlineKeyboardButton("📊 Workflow Status", callback_data="deploy_status")],
            [InlineKeyboardButton("◀️ Back", callback_data="menu_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🚀 *Deployment & CI/CD*\n\n"
            "Trigger GitHub Actions workflows:\n"
            "• Deploy to VPS\n"
            "• Run tests\n"
            "• View workflow status\n\n"
            "⚠️ Admin only\n\n"
            "Select an action:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _show_kb_menu(self, query, context):
        """Show KB management submenu"""
        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="kb_stats")],
            [InlineKeyboardButton("➕ Add URL", callback_data="kb_ingest")],
            [InlineKeyboardButton("🔍 Search", callback_data="kb_search")],
            [InlineKeyboardButton("📋 Queue Status", callback_data="kb_queue")],
            [InlineKeyboardButton("◀️ Back", callback_data="menu_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📚 *Knowledge Base Management*\n\n"
            "Manage your KB ingestion:\n"
            "• View atom count & growth\n"
            "• Add URLs to ingest\n"
            "• Search KB content\n"
            "• Monitor queue\n\n"
            "Select an action:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _show_metrics_menu(self, query, context):
        """Show analytics submenu"""
        keyboard = [
            [InlineKeyboardButton("📊 Today's Stats", callback_data="metrics_today")],
            [InlineKeyboardButton("💰 Cost Breakdown", callback_data="metrics_costs")],
            [InlineKeyboardButton("💵 Revenue", callback_data="metrics_revenue")],
            [InlineKeyboardButton("📈 Weekly Report", callback_data="metrics_week")],
            [InlineKeyboardButton("◀️ Back", callback_data="menu_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📊 *Analytics Dashboard*\n\n"
            "Monitor performance and costs:\n"
            "• Daily statistics\n"
            "• API cost breakdown\n"
            "• Revenue tracking\n"
            "• Weekly reports\n\n"
            "Select a view:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _show_system_menu(self, query, context):
        """Show system control submenu"""
        keyboard = [
            [InlineKeyboardButton("💚 Health Check", callback_data="system_health")],
            [InlineKeyboardButton("💾 Database Status", callback_data="system_db")],
            [InlineKeyboardButton("🖥️ VPS Status", callback_data="system_vps")],
            [InlineKeyboardButton("🔄 Restart Service", callback_data="system_restart")],
            [InlineKeyboardButton("◀️ Back", callback_data="menu_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⚙️ *System Control*\n\n"
            "Monitor and manage infrastructure:\n"
            "• Health checks\n"
            "• Database connectivity\n"
            "• VPS service status\n"
            "• Service restarts\n\n"
            "⚠️ Admin only\n\n"
            "Select an action:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _show_help(self, query, context):
        """Show help information"""
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        help_text = (
            "📖 *Admin Panel Help*\n\n"
            "*Commands:*\n"
            "`/admin` - Open main menu\n"
            "`/agents` - Quick agent status\n"
            "`/content` - Quick content queue\n"
            "`/deploy` - Quick deployment\n"
            "`/kb` - Quick KB stats\n"
            "`/metrics` - Quick analytics\n"
            "`/health` - Quick health check\n\n"
            "*Voice Commands (future):*\n"
            "Send voice message with command:\n"
            "• \"Show agent status\"\n"
            "• \"Deploy to production\"\n"
            "• \"Approve latest content\"\n\n"
            "*Permissions:*\n"
            "• Admin: Full control\n"
            "• Viewer: Read-only access\n\n"
            "*Support:*\n"
            "Contact system administrator"
        )

        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _refresh_dashboard(self, query, context):
        """Refresh main dashboard"""
        # Get updated status
        status = await self._get_system_status()

        keyboard = [
            [
                InlineKeyboardButton("🤖 Agents", callback_data="menu_agents"),
                InlineKeyboardButton("📝 Content", callback_data="menu_content"),
            ],
            [
                InlineKeyboardButton("🚀 Deploy", callback_data="menu_deploy"),
                InlineKeyboardButton("📚 KB", callback_data="menu_kb"),
            ],
            [
                InlineKeyboardButton("📊 Metrics", callback_data="menu_metrics"),
                InlineKeyboardButton("⚙️ System", callback_data="menu_system"),
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="menu_help"),
                InlineKeyboardButton("🔄 Refresh", callback_data="menu_refresh"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"🎛️ *Agent Factory Admin Panel*\n\n"
            f"*Quick Status:*\n"
            f"{status}\n\n"
            f"Refreshed at {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"Select a section to manage:"
        )

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _back_to_main(self, query, context):
        """Return to main menu"""
        await self._refresh_dashboard(query, context)

    async def _get_system_status(self) -> str:
        """
        Get quick system status for dashboard.

        Returns:
            Formatted status string
        """
        # Placeholder - will be implemented in later phases
        status_lines = [
            "• Agents: ... running",
            "• Content: ... pending",
            "• KB: ... atoms",
            "• System: ...",
        ]

        return "\n".join(status_lines)
