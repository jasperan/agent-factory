"""
Tests for DatabaseManager - Multi-provider PostgreSQL with failover.

Test Coverage:
- Provider initialization
- Health checks (with caching)
- Query execution with automatic failover
- Connection pooling
- Provider switching
- Error handling

Run tests:
    poetry run pytest tests/test_database_manager.py -v
    poetry run pytest tests/test_database_manager.py::TestDatabaseManager::test_health_check -v

Note: These tests use mocks to avoid requiring live database connections.
"""

import os
import sys
import time
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDatabaseProvider:
    """Test DatabaseProvider class."""

    @patch.dict(os.environ, {
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_provider_initialization(self, mock_psycopg):
        """Test provider initializes with connection string."""
        from agent_factory.core.database_manager import DatabaseProvider

        provider = DatabaseProvider(
            "supabase",
            "postgresql://postgres:password@localhost:5432/postgres"
        )

        assert provider.name == "supabase"
        assert "postgresql://" in provider.connection_string
        assert provider._pool is None  # Pool created lazily

    @patch("agent_factory.core.database_manager.psycopg")
    def test_health_check_success(self, mock_psycopg):
        """Test successful health check."""
        from agent_factory.core.database_manager import DatabaseProvider

        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock pool
        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("agent_factory.core.database_manager.ConnectionPool", return_value=mock_pool):
            provider = DatabaseProvider("test", "postgresql://test")

            # Health check should pass
            assert provider.health_check() is True

            # Verify query was executed
            mock_cursor.execute.assert_called_once_with("SELECT 1")

    @patch("agent_factory.core.database_manager.psycopg")
    def test_health_check_failure(self, mock_psycopg):
        """Test health check handles connection errors."""
        from agent_factory.core.database_manager import DatabaseProvider

        # Mock pool that raises exception
        mock_pool = MagicMock()
        mock_pool.getconn.side_effect = Exception("Connection failed")

        with patch("agent_factory.core.database_manager.ConnectionPool", return_value=mock_pool):
            provider = DatabaseProvider("test", "postgresql://test")

            # Health check should fail gracefully
            assert provider.health_check() is False

    @patch("agent_factory.core.database_manager.psycopg")
    def test_health_check_caching(self, mock_psycopg):
        """Test health check results are cached for 60 seconds."""
        from agent_factory.core.database_manager import DatabaseProvider

        # Mock successful connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("agent_factory.core.database_manager.ConnectionPool", return_value=mock_pool):
            provider = DatabaseProvider("test", "postgresql://test")

            # First health check
            assert provider.health_check() is True
            assert mock_cursor.execute.call_count == 1

            # Second health check (should use cache)
            assert provider.health_check() is True
            assert mock_cursor.execute.call_count == 1  # Not called again

            # Simulate time passing (cache expires)
            provider._last_health_check = time.time() - 61

            # Third health check (cache expired, should query again)
            assert provider.health_check() is True
            assert mock_cursor.execute.call_count == 2

    @patch("agent_factory.core.database_manager.psycopg")
    def test_execute_query_select(self, mock_psycopg):
        """Test executing SELECT query."""
        from agent_factory.core.database_manager import DatabaseProvider

        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, "test"), (2, "test2")]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("agent_factory.core.database_manager.ConnectionPool", return_value=mock_pool):
            provider = DatabaseProvider("test", "postgresql://test")

            result = provider.execute_query("SELECT * FROM test", fetch_mode="all")

            assert result == [(1, "test"), (2, "test2")]
            mock_cursor.execute.assert_called_once_with("SELECT * FROM test")
            mock_conn.commit.assert_called_once()

    @patch("agent_factory.core.database_manager.psycopg")
    def test_execute_query_with_params(self, mock_psycopg):
        """Test executing query with parameters."""
        from agent_factory.core.database_manager import DatabaseProvider

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (42,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("agent_factory.core.database_manager.ConnectionPool", return_value=mock_pool):
            provider = DatabaseProvider("test", "postgresql://test")

            result = provider.execute_query(
                "SELECT COUNT(*) FROM test WHERE id = %s",
                params=(123,),
                fetch_mode="one"
            )

            assert result == (42,)
            mock_cursor.execute.assert_called_once_with(
                "SELECT COUNT(*) FROM test WHERE id = %s",
                (123,)
            )


class TestDatabaseManager:
    """Test DatabaseManager class."""

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "DATABASE_FAILOVER_ENABLED": "true",
        "DATABASE_FAILOVER_ORDER": "supabase,railway,neon",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password",
        "SUPABASE_URL": "https://test.supabase.co",
        "NEON_DB_URL": "postgresql://test@neon.tech/neondb",
        "RAILWAY_DB_URL": "postgresql://test@railway.app/railway"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_manager_initialization(self, mock_psycopg):
        """Test DatabaseManager initializes with configured providers."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        assert manager.primary_provider == "supabase"
        assert manager.failover_enabled is True
        assert manager.failover_order == ["supabase", "railway", "neon"]
        assert "supabase" in manager.providers
        assert "neon" in manager.providers
        assert "railway" in manager.providers

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "neon",
        "NEON_DB_URL": "postgresql://test@neon.tech/neondb"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_manager_custom_provider(self, mock_psycopg):
        """Test DatabaseManager with custom primary provider."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        assert manager.primary_provider == "neon"

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_set_provider(self, mock_psycopg):
        """Test switching primary provider."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()
        assert manager.primary_provider == "supabase"

        # Can't switch to unconfigured provider
        with pytest.raises(ValueError):
            manager.set_provider("invalid_provider")

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "DATABASE_FAILOVER_ENABLED": "true",
        "DATABASE_FAILOVER_ORDER": "supabase,neon",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password",
        "NEON_DB_URL": "postgresql://test@neon.tech/neondb"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_execute_query_with_failover(self, mock_psycopg):
        """Test query execution with automatic failover."""
        from agent_factory.core.database_manager import DatabaseManager

        # Mock connection for both providers
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("success",)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("agent_factory.core.database_manager.ConnectionPool", return_value=mock_pool):
            manager = DatabaseManager()

            # Mock: Supabase fails, Neon succeeds
            supabase_provider = manager.providers["supabase"]
            neon_provider = manager.providers["neon"]

            supabase_provider.health_check = MagicMock(return_value=False)
            neon_provider.health_check = MagicMock(return_value=True)
            neon_provider.execute_query = MagicMock(return_value=[("success",)])

            result = manager.execute_query("SELECT 'test'")

            # Should skip unhealthy supabase and use neon
            assert result == [("success",)]
            neon_provider.execute_query.assert_called_once()

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "DATABASE_FAILOVER_ENABLED": "false",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_execute_query_no_failover(self, mock_psycopg):
        """Test query execution with failover disabled."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()
        assert manager.failover_enabled is False

        # With failover disabled, should only try primary
        supabase_provider = manager.providers["supabase"]
        supabase_provider.execute_query = MagicMock(side_effect=Exception("Connection failed"))

        with pytest.raises(Exception, match="Connection failed"):
            manager.execute_query("SELECT 'test'")

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password",
        "NEON_DB_URL": "postgresql://test@neon.tech/neondb"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_health_check_all(self, mock_psycopg):
        """Test checking health of all providers."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        # Mock health checks
        manager.providers["supabase"].health_check = MagicMock(return_value=True)
        manager.providers["neon"].health_check = MagicMock(return_value=False)

        results = manager.health_check_all()

        assert results["supabase"] is True
        assert results["neon"] is False

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_get_provider_stats(self, mock_psycopg):
        """Test getting provider statistics."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        # Mock health check
        manager.providers["supabase"].health_check = MagicMock(return_value=True)

        stats = manager.get_provider_stats()

        assert "supabase" in stats
        assert stats["supabase"]["healthy"] is True
        assert "connection_string_host" in stats["supabase"]

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_context_manager(self, mock_psycopg):
        """Test DatabaseManager as context manager."""
        from agent_factory.core.database_manager import DatabaseManager

        with DatabaseManager() as manager:
            assert manager.primary_provider == "supabase"

        # After exiting context, connections should be closed
        # (In real implementation, this would close pools)


class TestPostgresMemoryStorage:
    """Test PostgresMemoryStorage class."""

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_storage_initialization(self, mock_psycopg):
        """Test PostgresMemoryStorage initializes DatabaseManager."""
        from agent_factory.memory.storage import PostgresMemoryStorage

        storage = PostgresMemoryStorage()

        assert storage.table_name == "session_memories"
        assert hasattr(storage, "db")

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_save_session(self, mock_psycopg):
        """Test saving session to PostgreSQL."""
        from agent_factory.memory.storage import PostgresMemoryStorage
        from agent_factory.memory.session import Session

        storage = PostgresMemoryStorage()

        # Mock database execute_query
        storage.db.execute_query = MagicMock()

        # Create test session
        session = Session(user_id="test_user", storage=storage)
        session.add_user_message("Hello")
        session.add_assistant_message("Hi there")

        # Save session
        storage.save_session(session)

        # Should have called execute_query multiple times
        # (1 DELETE + 1 INSERT metadata + 2 INSERT messages)
        assert storage.db.execute_query.call_count == 4

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_load_session(self, mock_psycopg):
        """Test loading session from PostgreSQL."""
        from agent_factory.memory.storage import PostgresMemoryStorage
        import json

        storage = PostgresMemoryStorage()

        # Mock database responses
        metadata_row = [
            ("test_user", json.dumps({
                "created_at": "2025-12-12T10:00:00",
                "last_active": "2025-12-12T10:05:00",
                "metadata": {},
                "message_count": 2
            }))
        ]

        message_rows = [
            (json.dumps({
                "role": "user",
                "content": "Hello",
                "timestamp": "2025-12-12T10:00:00",
                "metadata": {},
                "message_index": 0
            }),),
            (json.dumps({
                "role": "assistant",
                "content": "Hi there",
                "timestamp": "2025-12-12T10:01:00",
                "metadata": {},
                "message_index": 1
            }),)
        ]

        storage.db.execute_query = MagicMock(side_effect=[metadata_row, message_rows])

        # Load session
        session = storage.load_session("test_session_id")

        assert session is not None
        assert session.user_id == "test_user"
        assert len(session.history.get_messages()) == 2

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_delete_session(self, mock_psycopg):
        """Test deleting session from PostgreSQL."""
        from agent_factory.memory.storage import PostgresMemoryStorage

        storage = PostgresMemoryStorage()

        # Mock database responses
        storage.db.execute_query = MagicMock(side_effect=[
            [(5,)],  # COUNT query returns 5
            None     # DELETE query
        ])

        result = storage.delete_session("test_session_id")

        assert result is True
        assert storage.db.execute_query.call_count == 2

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    @patch("agent_factory.core.database_manager.psycopg")
    def test_list_sessions(self, mock_psycopg):
        """Test listing sessions from PostgreSQL."""
        from agent_factory.memory.storage import PostgresMemoryStorage

        storage = PostgresMemoryStorage()

        # Mock database response
        storage.db.execute_query = MagicMock(return_value=[
            ("session_1",),
            ("session_2",),
            ("session_3",)
        ])

        sessions = storage.list_sessions()

        assert len(sessions) == 3
        assert "session_1" in sessions
        assert "session_2" in sessions
        assert "session_3" in sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
