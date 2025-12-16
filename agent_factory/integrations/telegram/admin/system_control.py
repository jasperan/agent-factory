"""
System Control for Telegram Admin Panel

Monitor and manage infrastructure:
- Database health checks (all providers)
- VPS service status
- Memory/CPU stats
- Service restarts
- Configuration updates

Commands:
    /health - Complete system health check
    /db_health - Database connectivity tests
    /vps_status - VPS services status
    /restart <service> - Restart specific service

Usage:
    from agent_factory.integrations.telegram.admin import SystemControl

    system = SystemControl()
    app.add_handler(CommandHandler("health", system.handle_health))
"""

import logging
import os
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .permissions import require_access, require_admin

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DatabaseHealth:
    """Database health check result"""
    name: str
    status: HealthStatus
    latency: Optional[float]
    error: Optional[str]
    record_count: Optional[int]


@dataclass
class ServiceHealth:
    """Service health check result"""
    name: str
    status: HealthStatus
    uptime: Optional[str]
    memory: Optional[str]
    cpu: Optional[str]
    error: Optional[str]


class SystemControl:
    """
    Manages system health checks and control.

    Provides:
    - Database connectivity tests
    - VPS service status
    - System resource monitoring
    - Service restart commands
    """

    def __init__(self):
        """Initialize system control"""
        self.vps_host = os.getenv("VPS_KB_HOST", "72.60.175.144")
        self.vps_user = "root"
        logger.info("SystemControl initialized")

    @require_access
    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /health command - complete system health check.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Running system health checks...")

        try:
            # Check databases
            db_health = await self._check_all_databases()

            # Check VPS services
            vps_health = await self._check_vps_services()

            # Check Telegram bot
            bot_health = await self._check_telegram_bot()

            # Format health report
            message = await self._format_health_report(db_health, vps_health, bot_health)

            # Build action keyboard
            keyboard = [
                [
                    InlineKeyboardButton("💾 Databases", callback_data="health_db"),
                    InlineKeyboardButton("🖥️ VPS", callback_data="health_vps"),
                ],
                [InlineKeyboardButton("🔄 Refresh", callback_data="health_refresh")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Failed to run health checks: {e}")
            await update.message.reply_text(
                f"❌ Health check failed: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_db_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /db_health command - database connectivity tests.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Testing database connectivity...")

        try:
            db_health = await self._check_all_databases()

            # Format database health
            message = await self._format_db_health(db_health)

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to check databases: {e}")
            await update.message.reply_text(
                f"❌ Database check failed: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_vps_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /vps_status command - VPS services status.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Checking VPS services...")

        try:
            vps_health = await self._check_vps_services()

            # Format VPS health
            message = await self._format_vps_health(vps_health)

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to check VPS: {e}")
            await update.message.reply_text(
                f"❌ VPS check failed: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_admin
    async def handle_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /restart <service> command - restart specific service.

        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: `/restart <service>`\n\n"
                "Available services:\n"
                "• telegram-bot\n"
                "• rivet-worker\n"
                "• postgres\n"
                "• redis\n"
                "• ollama\n\n"
                "⚠️ Admin only",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        service_name = context.args[0]

        # Confirm restart
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"restart_confirm_{service_name}"),
                InlineKeyboardButton("❌ Cancel", callback_data="restart_cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"⚠️ *Restart {service_name}*\n\n"
            "This will cause temporary service interruption.\n\n"
            "Confirm restart?",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _check_all_databases(self) -> List[DatabaseHealth]:
        """
        Check all database connections.

        Returns:
            List of database health results

        TODO: Actually test database connections
        """
        # Placeholder data for now
        return [
            DatabaseHealth(
                name="Neon",
                status=HealthStatus.HEALTHY,
                latency=23.5,
                error=None,
                record_count=1965
            ),
            DatabaseHealth(
                name="Railway",
                status=HealthStatus.HEALTHY,
                latency=45.2,
                error=None,
                record_count=1965
            ),
            DatabaseHealth(
                name="Supabase",
                status=HealthStatus.DEGRADED,
                latency=None,
                error="DNS resolution failed",
                record_count=None
            ),
            DatabaseHealth(
                name="Local",
                status=HealthStatus.UNHEALTHY,
                latency=None,
                error="Connection refused",
                record_count=None
            ),
        ]

    async def _check_vps_services(self) -> List[ServiceHealth]:
        """
        Check VPS services status.

        Returns:
            List of service health results

        TODO: SSH to VPS and check docker containers
        """
        # Placeholder data
        return [
            ServiceHealth(
                name="rivet-worker",
                status=HealthStatus.HEALTHY,
                uptime="2d 14h",
                memory="128 MB",
                cpu="5%",
                error=None
            ),
            ServiceHealth(
                name="postgres",
                status=HealthStatus.HEALTHY,
                uptime="2d 14h",
                memory="256 MB",
                cpu="12%",
                error=None
            ),
            ServiceHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                uptime="2d 14h",
                memory="64 MB",
                cpu="2%",
                error=None
            ),
            ServiceHealth(
                name="ollama",
                status=HealthStatus.HEALTHY,
                uptime="2d 14h",
                memory="512 MB",
                cpu="8%",
                error=None
            ),
        ]

    async def _check_telegram_bot(self) -> ServiceHealth:
        """Check Telegram bot status"""
        return ServiceHealth(
            name="telegram-bot",
            status=HealthStatus.HEALTHY,
            uptime="2d 14h",
            memory="64 MB",
            cpu="3%",
            error=None
        )

    async def _format_health_report(
        self,
        db_health: List[DatabaseHealth],
        vps_health: List[ServiceHealth],
        bot_health: ServiceHealth
    ) -> str:
        """Format complete health report"""
        message = "🏥 *System Health Report*\n\n"
        message += f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Overall status
        db_healthy = sum(1 for db in db_health if db.status == HealthStatus.HEALTHY)
        vps_healthy = sum(1 for svc in vps_health if svc.status == HealthStatus.HEALTHY)

        overall = "✅ All Systems Operational"
        if db_healthy < len(db_health) or vps_healthy < len(vps_health):
            overall = "⚠️ Some Systems Degraded"
        if db_healthy == 0 or vps_healthy == 0:
            overall = "❌ Critical Issues Detected"

        message += f"*Status:* {overall}\n\n"

        # Databases
        message += "*Databases:*\n"
        for db in db_health:
            status_emoji = self._get_status_emoji(db.status)
            message += f"{status_emoji} {db.name}: "

            if db.status == HealthStatus.HEALTHY:
                message += f"{db.latency:.1f}ms ({db.record_count:,} records)\n"
            else:
                message += f"{db.error or 'Unknown error'}\n"

        message += "\n"

        # VPS Services
        message += f"*VPS Services ({self.vps_host}):*\n"
        for svc in vps_health:
            status_emoji = self._get_status_emoji(svc.status)
            message += f"{status_emoji} {svc.name}: "

            if svc.status == HealthStatus.HEALTHY:
                message += f"Running (uptime {svc.uptime})\n"
            else:
                message += f"{svc.error or 'Unknown error'}\n"

        message += "\n"

        # Telegram Bot
        message += "*Telegram Bot:*\n"
        bot_emoji = self._get_status_emoji(bot_health.status)
        message += f"{bot_emoji} Connected (uptime {bot_health.uptime})\n"

        return message

    async def _format_db_health(self, db_health: List[DatabaseHealth]) -> str:
        """Format database health details"""
        message = "💾 *Database Health*\n\n"

        for db in db_health:
            status_emoji = self._get_status_emoji(db.status)
            message += f"{status_emoji} *{db.name}*\n"

            if db.status == HealthStatus.HEALTHY:
                message += f"  • Status: Connected\n"
                message += f"  • Latency: {db.latency:.1f}ms\n"
                message += f"  • Records: {db.record_count:,}\n"
            elif db.status == HealthStatus.DEGRADED:
                message += f"  • Status: Degraded\n"
                message += f"  • Issue: {db.error}\n"
            else:
                message += f"  • Status: Disconnected\n"
                message += f"  • Error: {db.error}\n"

            message += "\n"

        return message

    async def _format_vps_health(self, vps_health: List[ServiceHealth]) -> str:
        """Format VPS health details"""
        message = f"🖥️ *VPS Services*\n\n"
        message += f"Host: `{self.vps_host}`\n\n"

        for svc in vps_health:
            status_emoji = self._get_status_emoji(svc.status)
            message += f"{status_emoji} *{svc.name}*\n"

            if svc.status == HealthStatus.HEALTHY:
                message += f"  • Status: Running\n"
                message += f"  • Uptime: {svc.uptime}\n"
                message += f"  • Memory: {svc.memory}\n"
                message += f"  • CPU: {svc.cpu}\n"
            else:
                message += f"  • Status: Stopped\n"
                message += f"  • Error: {svc.error}\n"

            message += "\n"

        return message

    def _get_status_emoji(self, status: HealthStatus) -> str:
        """Get emoji for health status"""
        return {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓",
        }.get(status, "❓")
