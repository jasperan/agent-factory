"""
Content Review System for Telegram Admin Panel

Approve/reject pending content before publishing:
- YouTube videos
- Reddit posts
- Social media content

Features:
- Approval queue with filters
- Content preview (text, metadata)
- Quality scores and citations
- Inline approve/reject buttons
- Database status updates
- Audit logging

Commands:
    /content - View pending queue (all types)
    /content youtube - Filter YouTube videos
    /content reddit - Filter Reddit posts
    /content social - Filter social media

Usage:
    from agent_factory.integrations.telegram.admin import ContentReviewer

    reviewer = ContentReviewer()
    app.add_handler(CommandHandler("content", reviewer.handle_content))
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .permissions import require_access, require_admin

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Types of content for review"""
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    SOCIAL = "social"
    ALL = "all"


class ContentStatus(str, Enum):
    """Content approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


@dataclass
class ContentItem:
    """Content item for review"""
    id: int
    content_type: ContentType
    title: str
    content: str
    metadata: Dict[str, Any]
    quality_score: float
    status: ContentStatus
    created_at: datetime
    agent_id: Optional[str] = None


class ContentReviewer:
    """
    Manages content review and approval workflow.

    Provides:
    - Approval queue with filtering
    - Content preview
    - Approve/reject actions
    - Database updates
    """

    def __init__(self):
        """Initialize content reviewer"""
        # Will integrate with database in Phase 8
        self.db = None
        logger.info("ContentReviewer initialized")

    @require_access
    async def handle_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /content command - show approval queue.

        Args:
            update: Telegram update
            context: Callback context
        """
        # Parse filter argument
        content_filter = ContentType.ALL
        if context.args and len(context.args) > 0:
            filter_arg = context.args[0].lower()
            if filter_arg in ["youtube", "yt"]:
                content_filter = ContentType.YOUTUBE
            elif filter_arg in ["reddit", "r"]:
                content_filter = ContentType.REDDIT
            elif filter_arg in ["social", "s"]:
                content_filter = ContentType.SOCIAL

        await update.message.reply_text(f"🔄 Fetching content queue ({content_filter.value})...")

        try:
            # Get pending content
            items = await self._get_pending_content(content_filter)

            if not items:
                await update.message.reply_text(
                    f"✅ *No pending content*\n\n"
                    f"Filter: {content_filter.value}\n\n"
                    "All content has been reviewed!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Show first item with navigation
            await self._show_content_item(update, context, items[0], index=0, total=len(items))

        except Exception as e:
            logger.error(f"Failed to fetch content queue: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch content queue: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_admin
    async def handle_approve(self, content_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Approve content item.

        Args:
            content_id: Content ID to approve
            update: Telegram update
            context: Callback context
        """
        try:
            # Update database
            success = await self._approve_content(content_id, update.effective_user.id)

            if success:
                await update.callback_query.answer("✅ Approved!")
                await update.callback_query.edit_message_text(
                    f"✅ *Content Approved*\n\n"
                    f"Content ID: {content_id}\n"
                    f"Status: Approved for publishing\n\n"
                    "Content will be published automatically.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.callback_query.answer("❌ Failed to approve")

        except Exception as e:
            logger.error(f"Failed to approve content: {e}")
            await update.callback_query.answer(f"❌ Error: {str(e)}")

    @require_admin
    async def handle_reject(self, content_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Reject content item.

        Args:
            content_id: Content ID to reject
            update: Telegram update
            context: Callback context
        """
        try:
            # Update database
            success = await self._reject_content(content_id, update.effective_user.id)

            if success:
                await update.callback_query.answer("❌ Rejected")
                await update.callback_query.edit_message_text(
                    f"❌ *Content Rejected*\n\n"
                    f"Content ID: {content_id}\n"
                    f"Status: Rejected\n\n"
                    "Content will not be published.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.callback_query.answer("❌ Failed to reject")

        except Exception as e:
            logger.error(f"Failed to reject content: {e}")
            await update.callback_query.answer(f"❌ Error: {str(e)}")

    async def _show_content_item(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        item: ContentItem,
        index: int,
        total: int
    ):
        """
        Display content item with approve/reject buttons.

        Args:
            update: Telegram update
            context: Callback context
            item: Content item to display
            index: Current item index
            total: Total items in queue
        """
        # Format content message
        message = await self._format_content_item(item, index, total)

        # Build action keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"content_approve_{item.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"content_reject_{item.id}"),
            ],
            [
                InlineKeyboardButton("✏️ Edit", callback_data=f"content_edit_{item.id}"),
                InlineKeyboardButton("👁️ Preview", callback_data=f"content_preview_{item.id}"),
            ],
        ]

        # Add navigation if multiple items
        if total > 1:
            nav_buttons = []
            if index > 0:
                nav_buttons.append(
                    InlineKeyboardButton("⬅️ Previous", callback_data=f"content_prev_{index}")
                )
            if index < total - 1:
                nav_buttons.append(
                    InlineKeyboardButton("Next ➡️", callback_data=f"content_next_{index}")
                )
            if nav_buttons:
                keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("◀️ Back to Menu", callback_data="menu_back")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def _get_pending_content(self, content_filter: ContentType) -> List[ContentItem]:
        """
        Get pending content from database.

        Args:
            content_filter: Content type filter

        Returns:
            List of pending content items

        TODO: Query actual database (content_queue table)
        """
        # Placeholder data for now
        return [
            ContentItem(
                id=1,
                content_type=ContentType.YOUTUBE,
                title="PLC Basics Tutorial - Part 1",
                content="In this video, we'll cover the fundamentals of PLCs including...",
                metadata={
                    "duration": "8:32",
                    "keywords": ["PLC", "tutorial", "basics"],
                    "citations": 5,
                },
                quality_score=0.87,
                status=ContentStatus.PENDING,
                created_at=datetime.now(),
                agent_id="youtube_publisher"
            ),
            ContentItem(
                id=2,
                content_type=ContentType.REDDIT,
                title="Answer: How to troubleshoot VFD faults?",
                content="The most common VFD faults are:\n1. Overcurrent\n2. Overvoltage\n3. DC bus issues...",
                metadata={
                    "subreddit": "r/PLC",
                    "post_id": "abc123",
                    "citations": 3,
                },
                quality_score=0.92,
                status=ContentStatus.PENDING,
                created_at=datetime.now(),
                agent_id="reddit_responder"
            ),
        ]

    async def _approve_content(self, content_id: int, user_id: int) -> bool:
        """
        Approve content in database.

        Args:
            content_id: Content ID
            user_id: User who approved

        Returns:
            True if successful

        TODO: Update database status to 'approved'
        """
        logger.info(f"Content {content_id} approved by user {user_id}")
        # Will update database in Phase 8
        return True

    async def _reject_content(self, content_id: int, user_id: int) -> bool:
        """
        Reject content in database.

        Args:
            content_id: Content ID
            user_id: User who rejected

        Returns:
            True if successful

        TODO: Update database status to 'rejected'
        """
        logger.info(f"Content {content_id} rejected by user {user_id}")
        # Will update database in Phase 8
        return True

    async def _format_content_item(self, item: ContentItem, index: int, total: int) -> str:
        """Format content item for display"""
        # Content type emoji
        type_emoji = {
            ContentType.YOUTUBE: "🎥",
            ContentType.REDDIT: "💬",
            ContentType.SOCIAL: "📱",
        }.get(item.content_type, "📄")

        message = f"{type_emoji} *Content Review* ({index + 1}/{total})\n\n"

        message += f"*{item.title}*\n\n"

        # Metadata
        message += "*Details:*\n"
        message += f"• Type: {item.content_type.value}\n"
        message += f"• Quality: {item.quality_score:.0%}\n"
        message += f"• Agent: {item.agent_id or 'Unknown'}\n"
        message += f"• Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}\n"

        # Additional metadata
        if "citations" in item.metadata:
            message += f"• Citations: {item.metadata['citations']}\n"
        if "duration" in item.metadata:
            message += f"• Duration: {item.metadata['duration']}\n"
        if "keywords" in item.metadata:
            keywords = ", ".join(item.metadata['keywords'][:3])
            message += f"• Keywords: {keywords}\n"

        message += "\n"

        # Content preview (truncate if long)
        content_preview = item.content[:300]
        if len(item.content) > 300:
            content_preview += "..."

        message += "*Content Preview:*\n"
        message += f"```\n{content_preview}\n```\n\n"

        # Quality assessment
        if item.quality_score >= 0.9:
            message += "✅ High quality - recommended for approval\n"
        elif item.quality_score >= 0.7:
            message += "⚠️ Acceptable quality - review carefully\n"
        else:
            message += "❌ Low quality - consider rejection\n"

        return message
