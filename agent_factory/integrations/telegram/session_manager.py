"""
Telegram session management.

Maps Telegram chat IDs to Agent Factory sessions with lifecycle management.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict

from agent_factory.memory.session import Session
from agent_factory.memory.storage import InMemoryStorage


class TelegramSessionManager:
    """
    Manages chat sessions mapped to Agent Factory Sessions.

    Features:
    - Chat ID → Session mapping
    - Agent type per chat
    - Rate limiting per user
    - Session lifecycle (creation, reset, expiry)
    - Usage tracking

    Example:
        >>> manager = TelegramSessionManager()
        >>> session = manager.get_or_create(chat_id=12345, agent_type="bob")
        >>> manager.set_agent_type(12345, "research")
        >>> manager.reset_session(12345)
    """

    def __init__(self):
        """Initialize session manager."""
        # Chat ID → Agent Factory Session
        self.sessions: Dict[int, Session] = {}

        # Chat ID → agent type (research, coding, bob)
        self.agent_types: Dict[int, str] = {}

        # Chat ID → list of message timestamps (for rate limiting)
        self.message_times: Dict[int, list] = defaultdict(list)

        # Chat ID → last activity timestamp
        self.last_active: Dict[int, datetime] = {}

        # Approval workflow state
        self.pending_approvals: Dict[int, dict] = {}  # chat_id → approval data

    def get_or_create(
        self,
        chat_id: int,
        agent_type: str = "bob"
    ) -> Session:
        """
        Get existing session or create new one.

        Args:
            chat_id: Telegram chat ID
            agent_type: Agent type (research, coding, bob)

        Returns:
            Session instance for this chat

        Example:
            >>> session = manager.get_or_create(12345, "research")
        """
        if chat_id not in self.sessions:
            self.sessions[chat_id] = Session(
                user_id=f"telegram_{chat_id}",
                storage=InMemoryStorage()
            )
            self.agent_types[chat_id] = agent_type

        self.last_active[chat_id] = datetime.now()
        return self.sessions[chat_id]

    def reset_session(self, chat_id: int) -> None:
        """
        Clear session history for chat.

        Removes session, agent type, and message history.
        Does NOT remove rate limit data (prevent abuse).

        Args:
            chat_id: Telegram chat ID

        Example:
            >>> manager.reset_session(12345)
        """
        if chat_id in self.sessions:
            del self.sessions[chat_id]
        if chat_id in self.agent_types:
            del self.agent_types[chat_id]
        if chat_id in self.last_active:
            del self.last_active[chat_id]
        if chat_id in self.pending_approvals:
            del self.pending_approvals[chat_id]

    def set_agent_type(self, chat_id: int, agent_type: str) -> None:
        """
        Set agent type for chat.

        Does NOT clear history - use reset_session() for that.

        Args:
            chat_id: Telegram chat ID
            agent_type: New agent type

        Example:
            >>> manager.set_agent_type(12345, "coding")
        """
        self.agent_types[chat_id] = agent_type
        self.last_active[chat_id] = datetime.now()

    def get_agent_type(self, chat_id: int) -> str:
        """
        Get current agent type for chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Agent type string (defaults to "bob")

        Example:
            >>> agent_type = manager.get_agent_type(12345)
            'bob'
        """
        return self.agent_types.get(chat_id, "bob")

    def check_rate_limit(
        self,
        chat_id: int,
        limit: int = 10,
        window_seconds: int = 60
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if user is within rate limit.

        Args:
            chat_id: Telegram chat ID
            limit: Max messages per window
            window_seconds: Time window in seconds (default 60)

        Returns:
            Tuple of (is_allowed, seconds_to_wait)
            - is_allowed: True if within limit
            - seconds_to_wait: Seconds until next message allowed (if rate limited)

        Example:
            >>> allowed, wait_time = manager.check_rate_limit(12345, limit=10)
            >>> if not allowed:
            ...     print(f"Wait {wait_time} seconds")
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old timestamps
        self.message_times[chat_id] = [
            ts for ts in self.message_times[chat_id]
            if ts > window_start
        ]

        # Check limit
        if len(self.message_times[chat_id]) >= limit:
            # Calculate wait time
            oldest_in_window = min(self.message_times[chat_id])
            wait_until = oldest_in_window + timedelta(seconds=window_seconds)
            wait_seconds = int((wait_until - now).total_seconds()) + 1
            return False, wait_seconds

        # Add current timestamp
        self.message_times[chat_id].append(now)
        return True, None

    def cleanup_expired(self, ttl_hours: int = 24) -> int:
        """
        Remove sessions inactive for longer than TTL.

        Args:
            ttl_hours: Time-to-live in hours

        Returns:
            Number of sessions cleaned up

        Example:
            >>> cleaned = manager.cleanup_expired(ttl_hours=24)
            >>> print(f"Cleaned {cleaned} expired sessions")
        """
        now = datetime.now()
        expiry_threshold = now - timedelta(hours=ttl_hours)

        expired_chats = [
            chat_id for chat_id, last_active in self.last_active.items()
            if last_active < expiry_threshold
        ]

        for chat_id in expired_chats:
            self.reset_session(chat_id)

        return len(expired_chats)

    def get_stats(self) -> dict:
        """
        Get session statistics.

        Returns:
            Dictionary with stats:
            - active_sessions: Number of active sessions
            - agent_distribution: Count per agent type
            - total_messages: Total message count (rate limit tracking)

        Example:
            >>> stats = manager.get_stats()
            >>> print(f"Active: {stats['active_sessions']}")
        """
        agent_counts = defaultdict(int)
        for agent_type in self.agent_types.values():
            agent_counts[agent_type] += 1

        total_messages = sum(
            len(times) for times in self.message_times.values()
        )

        return {
            "active_sessions": len(self.sessions),
            "agent_distribution": dict(agent_counts),
            "total_messages": total_messages
        }

    # Approval workflow methods (Factor 7)

    def set_pending_approval(
        self,
        chat_id: int,
        action: str,
        details: dict
    ) -> str:
        """
        Store pending approval request.

        Args:
            chat_id: Telegram chat ID
            action: Action requiring approval
            details: Action details

        Returns:
            Approval ID

        Example:
            >>> approval_id = manager.set_pending_approval(
            ...     12345,
            ...     "delete_files",
            ...     {"count": 23, "pattern": "test_*.py"}
            ... )
        """
        approval_id = f"approval_{chat_id}_{datetime.now().timestamp()}"
        self.pending_approvals[chat_id] = {
            "id": approval_id,
            "action": action,
            "details": details,
            "timestamp": datetime.now()
        }
        return approval_id

    def get_pending_approval(self, chat_id: int) -> Optional[dict]:
        """Get pending approval for chat."""
        return self.pending_approvals.get(chat_id)

    def clear_pending_approval(self, chat_id: int) -> None:
        """Clear pending approval for chat."""
        if chat_id in self.pending_approvals:
            del self.pending_approvals[chat_id]
