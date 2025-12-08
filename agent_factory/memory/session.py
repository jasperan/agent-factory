"""
Session management for multi-turn conversations.

Provides:
- Session class for managing conversation state
- User metadata and preferences
- Session persistence through storage backends
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent_factory.memory.history import Message, MessageHistory
from agent_factory.memory.storage import MemoryStorage, InMemoryStorage


@dataclass
class Session:
    """
    User conversation session.

    Manages:
    - Unique session ID
    - User identification
    - Conversation history
    - User metadata (preferences, facts)
    - Session lifecycle (created, last active)
    - Cached agent executors (for memory persistence)

    Example:
        >>> session = Session(user_id="alice")
        >>> session.add_user_message("My name is Alice")
        >>> session.add_assistant_message("Nice to meet you, Alice!")
        >>> session.save()
    """

    session_id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    user_id: str = ""
    history: MessageHistory = field(default_factory=MessageHistory)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    storage: Optional[MemoryStorage] = None
    _cached_agents: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        """Initialize storage if not provided."""
        if self.storage is None:
            self.storage = InMemoryStorage()

    def add_user_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a user message to the session.

        Args:
            content: Message content
            metadata: Optional message metadata

        Returns:
            The created Message object
        """
        self._update_activity()
        return self.history.add_message("user", content, metadata)

    def add_assistant_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add an assistant message to the session.

        Args:
            content: Message content
            metadata: Optional message metadata

        Returns:
            The created Message object
        """
        self._update_activity()
        return self.history.add_message("assistant", content, metadata)

    def add_system_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a system message to the session.

        Args:
            content: Message content
            metadata: Optional message metadata

        Returns:
            The created Message object
        """
        self._update_activity()
        return self.history.add_message("system", content, metadata)

    def get_full_context(
        self,
        max_tokens: Optional[int] = None
    ) -> List[Message]:
        """
        Get full conversation context.

        Args:
            max_tokens: Optional maximum tokens for context window

        Returns:
            List of messages (all or within token limit)
        """
        if max_tokens:
            return self.history.get_context_window(max_tokens=max_tokens)
        return self.history.get_messages()

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """
        Get recent messages.

        Args:
            limit: Number of recent messages

        Returns:
            List of recent messages
        """
        return self.history.get_messages(limit=limit)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set session metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self._update_activity()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get session metadata.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history.clear()
        self._update_activity()

    def get_agent_executor(self, agent_type: str) -> Optional[Any]:
        """
        Get cached agent executor for this session.

        Args:
            agent_type: Type of agent (research, coding, bob)

        Returns:
            Cached agent executor or None if not found

        Example:
            >>> agent = session.get_agent_executor("bob")
        """
        return self._cached_agents.get(agent_type)

    def set_agent_executor(self, agent_type: str, executor: Any) -> None:
        """
        Cache agent executor for this session.

        This allows the agent's memory to persist across invocations,
        enabling multi-turn conversations with context retention.

        Args:
            agent_type: Type of agent (research, coding, bob)
            executor: Agent executor instance

        Example:
            >>> session.set_agent_executor("bob", bob_executor)
        """
        self._cached_agents[agent_type] = executor
        self._update_activity()

    def clear_agent_cache(self) -> None:
        """
        Clear all cached agent executors.

        Used when resetting a session to ensure fresh agent memory.

        Example:
            >>> session.clear_agent_cache()
        """
        self._cached_agents.clear()
        self._update_activity()

    def save(self) -> None:
        """Persist session to storage."""
        if self.storage:
            self.storage.save_session(self)

    def _update_activity(self) -> None:
        """Update last active timestamp."""
        self.last_active = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "history": self.history.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        storage: Optional[MemoryStorage] = None
    ) -> "Session":
        """
        Create session from dictionary.

        Args:
            data: Dictionary data
            storage: Optional storage backend

        Returns:
            Session instance
        """
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            history=MessageHistory.from_dict(data.get("history", {})),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            storage=storage,
        )

    @classmethod
    def load(
        cls,
        session_id: str,
        storage: Optional[MemoryStorage] = None
    ) -> Optional["Session"]:
        """
        Load session from storage.

        Args:
            session_id: Session ID to load
            storage: Storage backend to load from

        Returns:
            Session instance or None if not found
        """
        if storage is None:
            storage = InMemoryStorage()

        return storage.load_session(session_id)

    def __len__(self) -> int:
        """Return number of messages in session."""
        return len(self.history)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Session(id={self.session_id[:8]}..., "
            f"user={self.user_id}, "
            f"messages={len(self.history)})"
        )
