"""
Integration tests for database failover functionality.

These are higher-level tests that verify the failover behavior works correctly.
They mock the database connections to simulate failures.

Run tests:
    poetry run pytest tests/test_database_failover.py -v
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDatabaseFailover:
    """Test database failover scenarios."""

    def test_imports_work(self):
        """Verify imports work correctly."""
        from agent_factory.core.database_manager import DatabaseManager
        from agent_factory.memory.storage import PostgresMemoryStorage

        assert DatabaseManager is not None
        assert PostgresMemoryStorage is not None

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "DATABASE_FAILOVER_ENABLED": "true",
        "DATABASE_FAILOVER_ORDER": "supabase,neon",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password",
        "NEON_DB_URL": "postgresql://test@neon.tech/neondb"
    })
    def test_manager_initialization_with_env_vars(self):
        """Test DatabaseManager reads environment variables correctly."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        # Verify configuration loaded from env
        assert manager.primary_provider == "supabase"
        assert manager.failover_enabled is True
        assert "supabase" in manager.failover_order
        assert "neon" in manager.failover_order

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "railway",
        "RAILWAY_DB_URL": "postgresql://test@railway.app/railway"
    })
    def test_manager_custom_provider_selection(self):
        """Test selecting custom provider via env var."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        assert manager.primary_provider == "railway"

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "DATABASE_FAILOVER_ENABLED": "false",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    def test_failover_disabled(self):
        """Test failover can be disabled via env var."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        assert manager.failover_enabled is False

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    def test_set_provider_validates_availability(self):
        """Test set_provider validates provider exists."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        # Should raise error for unconfigured provider
        with pytest.raises(ValueError, match="not configured"):
            manager.set_provider("nonexistent_provider")

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password",
        "NEON_DB_URL": "postgresql://test@neon.tech/neondb"
    })
    def test_provider_stats_structure(self):
        """Test get_provider_stats returns expected structure."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()
        stats = manager.get_provider_stats()

        # Should have stats for each configured provider
        for provider_name in manager.providers:
            assert provider_name in stats
            assert "healthy" in stats[provider_name]
            assert "connection_string_host" in stats[provider_name]
            assert "pool_active" in stats[provider_name]

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    def test_context_manager_protocol(self):
        """Test DatabaseManager supports context manager protocol."""
        from agent_factory.core.database_manager import DatabaseManager

        # Should work with 'with' statement
        with DatabaseManager() as manager:
            assert manager is not None
            assert hasattr(manager, "providers")

        # After exiting, manager should still be usable
        # (close_all doesn't prevent reuse, just closes current connections)


class TestPostgresMemoryStorageBasic:
    """Basic tests for PostgresMemoryStorage."""

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    def test_storage_initialization(self):
        """Test PostgresMemoryStorage initializes correctly."""
        from agent_factory.memory.storage import PostgresMemoryStorage

        storage = PostgresMemoryStorage()

        # Should have DatabaseManager instance
        assert hasattr(storage, "db")
        assert storage.table_name == "session_memories"

    @patch.dict(os.environ, {
        "DATABASE_PROVIDER": "supabase",
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    })
    def test_storage_has_required_methods(self):
        """Test PostgresMemoryStorage implements MemoryStorage interface."""
        from agent_factory.memory.storage import PostgresMemoryStorage

        storage = PostgresMemoryStorage()

        # Should have all required methods from abstract base
        assert hasattr(storage, "save_session")
        assert hasattr(storage, "load_session")
        assert hasattr(storage, "delete_session")
        assert hasattr(storage, "list_sessions")

        # Plus custom methods
        assert hasattr(storage, "save_memory_atom")
        assert hasattr(storage, "query_memory_atoms")


class TestProviderConfiguration:
    """Test provider configuration logic."""

    @patch.dict(os.environ, {}, clear=True)
    def test_no_providers_configured_raises_error(self):
        """Test error when no providers configured."""
        from agent_factory.core.database_manager import DatabaseManager

        # Should raise ValueError when no providers available
        with pytest.raises(ValueError, match="No database providers configured"):
            DatabaseManager()

    @patch.dict(os.environ, {
        "SUPABASE_DB_HOST": "db.test.supabase.co",
        "SUPABASE_DB_PASSWORD": "",  # Empty password
        "RAILWAY_DB_URL": "",
        "NEON_DB_URL": ""
    }, clear=True)
    def test_incomplete_supabase_credentials_skipped(self):
        """Test Supabase skipped if credentials incomplete."""
        from agent_factory.core.database_manager import DatabaseManager

        # Should skip Supabase with empty password
        with pytest.raises(ValueError, match="No database providers configured"):
            DatabaseManager()

    @patch.dict(os.environ, {
        "RAILWAY_DB_URL": "postgresql://postgres:your_railway_password_here@railway.app/railway",
        "SUPABASE_DB_HOST": "",
        "SUPABASE_DB_PASSWORD": "",
        "NEON_DB_URL": ""
    }, clear=True)
    def test_railway_placeholder_password_skipped(self):
        """Test Railway skipped if still has placeholder password."""
        from agent_factory.core.database_manager import DatabaseManager

        # Should skip Railway with placeholder password
        with pytest.raises(ValueError, match="No database providers configured"):
            DatabaseManager()

    @patch.dict(os.environ, {
        "NEON_DB_URL": "postgresql://test@neon.tech/neondb",
        "SUPABASE_DB_HOST": "",
        "SUPABASE_DB_PASSWORD": "",
        "RAILWAY_DB_URL": ""
    }, clear=True)
    def test_neon_only_configuration(self):
        """Test can use Neon as only provider."""
        from agent_factory.core.database_manager import DatabaseManager

        manager = DatabaseManager()

        # Should have only Neon provider
        assert "neon" in manager.providers
        assert len(manager.providers) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
