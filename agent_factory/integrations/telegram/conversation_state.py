"""
Persistent Conversation State Manager

Provides rock-solid multi-tier persistent state for Telegram conversations.
Prevents data loss from connection interruptions, bot restarts, or database failures.

Features:
- Multi-tier database fallback (Neon → Supabase → Railway → Local SQLite)
- Save state after every user input
- Resume interrupted conversations
- Auto-expire abandoned conversations (24h TTL)
- Thread-safe operations

Usage:
    from agent_factory.integrations.telegram.conversation_state import ConversationStateManager

    # Initialize manager
    state_manager = ConversationStateManager()

    # Save state after each user input
    await state_manager.save_state(
        user_id="123456",
        conversation_type="add_machine",
        current_state="MANUFACTURER",
        data={"nickname": "Test Relay", "manufacturer": "Siemens"}
    )

    # Load state to resume
    state = await state_manager.load_state(user_id="123456", conversation_type="add_machine")
    if state:
        print(f"Resuming from {state['current_state']}")

    # Clear state when conversation completes
    await state_manager.clear_state(user_id="123456", conversation_type="add_machine")
"""

import logging
import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from agent_factory.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ConversationStateManager:
    """
    Manages persistent conversation state with multi-tier database fallback.

    Architecture:
    - Tries cloud databases first (Neon, Supabase, Railway)
    - Falls back to local SQLite if all cloud providers fail
    - Saves state after every user interaction
    - Allows resuming interrupted conversations
    - Auto-expires abandoned conversations after 24 hours
    """

    def __init__(self):
        """Initialize conversation state manager with database connection."""
        self.db = DatabaseManager()
        logger.info("ConversationStateManager initialized with multi-tier fallback")

    async def save_state(
        self,
        user_id: str,
        conversation_type: str,
        current_state: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Save conversation state to database with automatic failover.

        Args:
            user_id: Telegram user ID
            conversation_type: Type of conversation ('add_machine', 'troubleshoot', etc.)
            current_state: Current conversation state ('NICKNAME', 'MANUFACTURER', etc.)
            data: Dictionary of collected data so far

        Returns:
            True if saved successfully, False otherwise

        Example:
            await state_manager.save_state(
                user_id="123456",
                conversation_type="add_machine",
                current_state="MANUFACTURER",
                data={"nickname": "Test Relay", "manufacturer": "Siemens"}
            )
        """
        try:
            # Generate unique ID for new state
            state_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)

            # Convert data dict to JSON string
            data_json = json.dumps(data)

            # Upsert query (INSERT or UPDATE if exists)
            query = """
                INSERT INTO conversation_states (id, user_id, conversation_type, current_state, data, expires_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (user_id, conversation_type)
                DO UPDATE SET current_state = $4, data = $5, updated_at = NOW()
            """

            self.db.execute_query(
                query,
                (state_id, user_id, conversation_type, current_state, data_json, expires_at.isoformat()),
                fetch_mode="none"
            )

            logger.info(f"Saved conversation state: user={user_id}, type={conversation_type}, state={current_state}")
            return True

        except Exception as e:
            logger.error(f"Failed to save conversation state: {e}", exc_info=True)
            return False

    async def load_state(
        self,
        user_id: str,
        conversation_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load conversation state from database.

        Args:
            user_id: Telegram user ID
            conversation_type: Type of conversation

        Returns:
            Dictionary with state data if found, None otherwise

        Example:
            state = await state_manager.load_state(user_id="123456", conversation_type="add_machine")
            if state:
                print(f"Current state: {state['current_state']}")
                print(f"Data: {state['data']}")
        """
        try:
            query = """
                SELECT id, current_state, data, created_at, updated_at
                FROM conversation_states
                WHERE user_id = $1 AND conversation_type = $2 AND expires_at > NOW()
            """

            result = self.db.execute_query(query, (user_id, conversation_type), fetch_mode="one")

            if result:
                state_id, current_state, data_json, created_at, updated_at = result

                # Parse JSON data
                data = json.loads(data_json) if isinstance(data_json, str) else data_json

                return {
                    "id": state_id,
                    "current_state": current_state,
                    "data": data,
                    "created_at": created_at,
                    "updated_at": updated_at
                }

            return None

        except Exception as e:
            logger.error(f"Failed to load conversation state: {e}", exc_info=True)
            return None

    async def clear_state(
        self,
        user_id: str,
        conversation_type: str
    ) -> bool:
        """
        Clear conversation state when conversation completes or is cancelled.

        Args:
            user_id: Telegram user ID
            conversation_type: Type of conversation

        Returns:
            True if cleared successfully, False otherwise

        Example:
            await state_manager.clear_state(user_id="123456", conversation_type="add_machine")
        """
        try:
            query = """
                DELETE FROM conversation_states
                WHERE user_id = $1 AND conversation_type = $2
            """

            self.db.execute_query(query, (user_id, conversation_type), fetch_mode="none")

            logger.info(f"Cleared conversation state: user={user_id}, type={conversation_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear conversation state: {e}", exc_info=True)
            return False

    async def cleanup_expired(self) -> int:
        """
        Delete expired conversation states (cleanup job).

        Returns:
            Number of states deleted

        Example:
            # Run periodically (e.g., daily cron job)
            deleted = await state_manager.cleanup_expired()
            print(f"Cleaned up {deleted} expired conversations")
        """
        try:
            query = """
                DELETE FROM conversation_states
                WHERE expires_at < NOW()
            """

            # SQLite doesn't support RETURNING, so we count first
            count_query = "SELECT COUNT(*) FROM conversation_states WHERE expires_at < NOW()"
            count_result = self.db.execute_query(count_query, fetch_mode="one")
            count = count_result[0] if count_result else 0

            self.db.execute_query(query, fetch_mode="none")

            logger.info(f"Cleaned up {count} expired conversation states")
            return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired states: {e}", exc_info=True)
            return 0


# Global singleton instance
_state_manager_instance: Optional[ConversationStateManager] = None


def get_state_manager() -> ConversationStateManager:
    """
    Get global ConversationStateManager singleton.

    Returns:
        Shared ConversationStateManager instance

    Example:
        from agent_factory.integrations.telegram.conversation_state import get_state_manager

        state_manager = get_state_manager()
        await state_manager.save_state(...)
    """
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = ConversationStateManager()
    return _state_manager_instance
