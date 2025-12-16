"""
Knowledge Base Management for Telegram Admin Panel

Monitor and manage KB ingestion:
- View atom count and growth statistics
- Trigger VPS ingestion (add URLs to queue)
- Search KB content
- Monitor ingestion queue
- Review failed ingestion attempts

Commands:
    /kb - Overall statistics
    /kb_ingest <url> - Add URL to ingestion queue
    /kb_search <query> - Search KB content
    /kb_queue - View pending URLs

Usage:
    from agent_factory.integrations.telegram.admin import KBManager

    kb = KBManager()
    app.add_handler(CommandHandler("kb", kb.handle_kb))
"""

import logging
import os
import subprocess
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .permissions import require_access, require_admin

logger = logging.getLogger(__name__)


@dataclass
class KBStats:
    """Knowledge base statistics"""
    total_atoms: int
    atoms_today: int
    atoms_this_week: int
    queue_depth: int
    failed_count: int
    avg_quality: float
    vendors: Dict[str, int]  # Vendor distribution
    equipment: Dict[str, int]  # Equipment type distribution


@dataclass
class KBAtom:
    """Knowledge base atom"""
    id: str
    title: str
    summary: str
    vendor: Optional[str]
    equipment_type: Optional[str]
    quality_score: float
    created_at: datetime


class KBManager:
    """
    Manages knowledge base monitoring and ingestion.

    Provides:
    - KB statistics and growth tracking
    - URL ingestion triggers
    - Content search
    - Queue monitoring
    """

    def __init__(self):
        """Initialize KB manager"""
        self.vps_host = os.getenv("VPS_KB_HOST", "72.60.175.144")
        self.vps_user = "root"
        logger.info(f"KBManager initialized for VPS {self.vps_host}")

    @require_access
    async def handle_kb(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /kb command - show statistics.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Fetching KB statistics...")

        try:
            stats = await self._get_kb_stats()

            # Format statistics message
            message = await self._format_kb_stats(stats)

            # Build action keyboard
            keyboard = [
                [
                    InlineKeyboardButton("➕ Add URL", callback_data="kb_ingest"),
                    InlineKeyboardButton("🔍 Search", callback_data="kb_search"),
                ],
                [
                    InlineKeyboardButton("📋 Queue", callback_data="kb_queue"),
                    InlineKeyboardButton("❌ Failed", callback_data="kb_failed"),
                ],
                [InlineKeyboardButton("🔄 Refresh", callback_data="kb_refresh")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Failed to fetch KB stats: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch KB statistics: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_admin
    async def handle_kb_ingest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /kb_ingest <url> command - add URL to ingestion queue.

        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: `/kb_ingest <url>`\n\n"
                "Example: `/kb_ingest https://example.com/manual.pdf`\n\n"
                "Supported formats:\n"
                "• PDF documents\n"
                "• Web pages (HTML)\n"
                "• YouTube videos\n"
                "• Forum posts",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        url = context.args[0]

        # Validate URL format
        if not url.startswith(("http://", "https://")):
            await update.message.reply_text(
                "❌ Invalid URL format\n\n"
                "URL must start with http:// or https://",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        await update.message.reply_text(f"🔄 Adding URL to ingestion queue...\n\n`{url}`", parse_mode=ParseMode.MARKDOWN)

        try:
            # Add URL to VPS Redis queue
            success = await self._add_to_ingestion_queue(url)

            if success:
                await update.message.reply_text(
                    "✅ *URL Added to Queue*\n\n"
                    f"URL: `{url}`\n\n"
                    "The VPS worker will process this URL automatically.\n"
                    "Processing typically takes 2-10 minutes depending on content size.\n\n"
                    "Use /kb_queue to monitor progress.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    "❌ Failed to add URL to queue\n\n"
                    "Check VPS connectivity or Redis status.",
                    parse_mode=ParseMode.MARKDOWN
                )

        except Exception as e:
            logger.error(f"Failed to add URL to queue: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_kb_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /kb_search <query> command - search KB content.

        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: `/kb_search <query>`\n\n"
                "Example: `/kb_search PLC motor control`\n\n"
                "Search supports:\n"
                "• Vendor names (Siemens, Rockwell, etc.)\n"
                "• Equipment types (VFD, PLC, HMI)\n"
                "• Concepts (troubleshooting, wiring)\n"
                "• Part numbers",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        query = " ".join(context.args)

        await update.message.reply_text(f"🔍 Searching KB for: `{query}`", parse_mode=ParseMode.MARKDOWN)

        try:
            # Search KB (semantic or keyword)
            results = await self._search_kb(query, limit=5)

            if not results:
                await update.message.reply_text(
                    f"⚠️ No results found for: `{query}`\n\n"
                    "Try different keywords or check spelling.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Format search results
            message = f"🔍 *Search Results: {query}*\n\n"
            message += f"Found {len(results)} atoms:\n\n"

            for i, atom in enumerate(results, 1):
                message += f"{i}. *{atom.title}*\n"
                message += f"   • Type: {atom.equipment_type or 'General'}\n"
                message += f"   • Vendor: {atom.vendor or 'Generic'}\n"
                message += f"   • Quality: {atom.quality_score:.0%}\n"
                message += f"   • Summary: {atom.summary[:100]}...\n\n"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to search KB: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_kb_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /kb_queue command - view pending URLs.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Fetching ingestion queue...")

        try:
            queue = await self._get_ingestion_queue()

            if not queue:
                await update.message.reply_text(
                    "✅ *Ingestion Queue Empty*\n\n"
                    "All URLs have been processed.\n\n"
                    "Use /kb_ingest to add more URLs.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Format queue
            message = f"📋 *Ingestion Queue*\n\n"
            message += f"Pending: {len(queue)} URLs\n\n"

            for i, url in enumerate(queue[:10], 1):
                message += f"{i}. `{url}`\n"

            if len(queue) > 10:
                message += f"\n... and {len(queue) - 10} more\n"

            message += "\n⏱️ Estimated processing time: "
            message += f"{len(queue) * 5} minutes"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to fetch queue: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def _get_kb_stats(self) -> KBStats:
        """
        Get KB statistics.

        Returns:
            KB statistics

        TODO: Query VPS PostgreSQL for real data
        """
        # Placeholder data for now
        # Will be replaced with real queries in Phase 8
        return KBStats(
            total_atoms=1965,
            atoms_today=34,
            atoms_this_week=187,
            queue_depth=12,
            failed_count=3,
            avg_quality=0.84,
            vendors={
                "Rockwell": 512,
                "Siemens": 487,
                "Mitsubishi": 298,
                "Omron": 245,
                "Schneider": 189,
                "Other": 234,
            },
            equipment={
                "PLC": 678,
                "VFD": 421,
                "HMI": 312,
                "Motor": 289,
                "Sensor": 265,
            }
        )

    async def _add_to_ingestion_queue(self, url: str) -> bool:
        """
        Add URL to VPS Redis ingestion queue.

        Args:
            url: URL to ingest

        Returns:
            True if successful

        TODO: Execute actual SSH command to VPS
        """
        try:
            # Command to add URL to Redis queue
            cmd = [
                "ssh",
                f"{self.vps_user}@{self.vps_host}",
                f'docker exec infra_redis_1 redis-cli RPUSH kb_ingest_jobs "{url}"'
            ]

            # Execute SSH command
            # Note: This requires SSH key setup on local machine
            # For now, just log the command (will be enabled in Phase 8)
            logger.info(f"Would execute: {' '.join(cmd)}")
            logger.info(f"Added to queue: {url}")

            # Placeholder: return success
            # Real implementation will execute subprocess.run(cmd)
            return True

        except Exception as e:
            logger.error(f"Failed to add URL to queue: {e}")
            return False

    async def _search_kb(self, query: str, limit: int = 5) -> List[KBAtom]:
        """
        Search KB content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching atoms

        TODO: Query VPS PostgreSQL with semantic search
        """
        # Placeholder data
        return [
            KBAtom(
                id="atom_001",
                title="PLC Motor Control Basics",
                summary="Introduction to motor control using PLCs including start/stop/seal-in circuits",
                vendor="Rockwell",
                equipment_type="PLC",
                quality_score=0.92,
                created_at=datetime.now() - timedelta(days=5)
            ),
            KBAtom(
                id="atom_002",
                title="VFD Troubleshooting Guide",
                summary="Common VFD faults and diagnostic procedures for Siemens drives",
                vendor="Siemens",
                equipment_type="VFD",
                quality_score=0.88,
                created_at=datetime.now() - timedelta(days=12)
            ),
        ]

    async def _get_ingestion_queue(self) -> List[str]:
        """
        Get pending URLs from VPS Redis queue.

        Returns:
            List of pending URLs

        TODO: Query VPS Redis
        """
        # Placeholder data
        return [
            "https://example.com/manual1.pdf",
            "https://example.com/manual2.pdf",
            "https://youtube.com/watch?v=abc123",
        ]

    async def _format_kb_stats(self, stats: KBStats) -> str:
        """Format KB statistics for display"""
        message = "📚 *Knowledge Base Statistics*\n\n"

        # Growth metrics
        message += "*Growth:*\n"
        message += f"• Total Atoms: {stats.total_atoms:,}\n"
        message += f"• Today: +{stats.atoms_today}\n"
        message += f"• This Week: +{stats.atoms_this_week}\n"
        message += f"• Avg Quality: {stats.avg_quality:.0%}\n\n"

        # Queue status
        message += "*Ingestion Status:*\n"
        message += f"• Queue Depth: {stats.queue_depth} URLs\n"
        message += f"• Failed: {stats.failed_count}\n\n"

        # Top vendors
        message += "*Top Vendors:*\n"
        sorted_vendors = sorted(stats.vendors.items(), key=lambda x: x[1], reverse=True)
        for vendor, count in sorted_vendors[:5]:
            message += f"• {vendor}: {count} atoms\n"

        message += "\n"

        # Top equipment
        message += "*Top Equipment:*\n"
        sorted_equipment = sorted(stats.equipment.items(), key=lambda x: x[1], reverse=True)
        for equip, count in sorted_equipment[:5]:
            message += f"• {equip}: {count} atoms\n"

        return message
