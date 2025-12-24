"""
Multi-provider database manager with automatic failover.

Supports Supabase, Railway, and Neon (all PostgreSQL + pgvector).
Provides unified interface with automatic failover, connection pooling,
and health checks.

Example Usage:
    >>> from agent_factory.core.database_manager import DatabaseManager
    >>>
    >>> # Auto-selects provider from DATABASE_PROVIDER env var
    >>> db = DatabaseManager()
    >>>
    >>> # Execute query with automatic failover
    >>> result = db.execute_query("SELECT version()")
    >>> print(result)
    >>>
    >>> # Check provider health
    >>> if db.health_check('supabase'):
    >>>     print("Supabase is healthy")
    >>>
    >>> # Force specific provider
    >>> db.set_provider('railway')
    >>> result = db.execute_query("SELECT COUNT(*) FROM knowledge_atoms")

Architecture:
    - Supports 3 providers: Supabase, Railway, Neon
    - All use PostgreSQL + pgvector extension
    - Automatic failover on connection/query errors
    - Connection pooling per provider (psycopg pool)
    - Health checks before operations
    - Thread-safe for concurrent access

Configuration:
    Environment variables:
    - DATABASE_PROVIDER: Primary provider (supabase, railway, neon)
    - DATABASE_FAILOVER_ENABLED: Enable failover (true/false)
    - DATABASE_FAILOVER_ORDER: Failover sequence (comma-separated)
    - SUPABASE_URL: Supabase project URL
    - SUPABASE_SERVICE_ROLE_KEY: Supabase API key
    - RAILWAY_DB_URL: Railway connection string
    - NEON_DB_URL: Neon connection string
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseProvider:
    """
    Abstract base for database providers.

    Each provider implements connection logic for a specific PostgreSQL service.
    """

    def __init__(self, name: str, connection_string: str):
        """
        Initialize provider.

        Args:
            name: Provider name (supabase, railway, neon)
            connection_string: PostgreSQL connection URL
        """
        self.name = name
        self.connection_string = connection_string
        self._pool = None
        self._last_health_check = 0
        self._health_check_ttl = 60  # Cache health status for 60 seconds
        self._is_healthy = False

    def get_connection(self):
        """
        Get database connection from pool.

        Returns:
            psycopg connection object

        Raises:
            ImportError: If psycopg not installed
            Exception: If connection fails
        """
        try:
            import psycopg
        except ImportError:
            raise ImportError(
                "psycopg required for database connections. "
                "Install with: poetry add 'psycopg[binary]'"
            )

        # Create connection pool if not exists
        if self._pool is None:
            from psycopg_pool import ConnectionPool
            self._pool = ConnectionPool(
                self.connection_string,
                min_size=2,        # Keep 2 connections warm
                max_size=20,       # Allow up to 20 concurrent connections
                timeout=15.0       # Wait up to 15 seconds for connection
            )
            logger.info(f"Created connection pool for {self.name}")

        # Get connection from pool
        return self._pool.getconn()

    def release_connection(self, conn):
        """Release connection back to pool."""
        if self._pool:
            self._pool.putconn(conn)

    def health_check(self) -> bool:
        """
        Check if provider is healthy.

        Returns True if can connect and execute simple query.
        Caches result for 60 seconds to avoid overhead.

        Returns:
            bool: True if healthy, False otherwise
        """
        # Return cached health status if recent
        now = time.time()
        if now - self._last_health_check < self._health_check_ttl:
            return self._is_healthy

        # Perform health check
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                self._is_healthy = result == (1,)
                self._last_health_check = now

                if self._is_healthy:
                    logger.debug(f"{self.name} health check: PASS")
                else:
                    logger.warning(f"{self.name} health check: FAIL (unexpected result)")

                return self._is_healthy

        except Exception as e:
            logger.warning(f"{self.name} health check: FAIL ({str(e)})")
            self._is_healthy = False
            self._last_health_check = now
            return False

        finally:
            if conn:
                self.release_connection(conn)

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_mode: str = "all"
    ) -> Any:
        """
        Execute query on this provider.

        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch_mode: 'all', 'one', 'none' (for INSERT/UPDATE/DELETE)

        Returns:
            Query results based on fetch_mode

        Raises:
            Exception: If query execution fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)

                # Handle different fetch modes
                if fetch_mode == "all":
                    result = cur.fetchall()
                elif fetch_mode == "one":
                    result = cur.fetchone()
                elif fetch_mode == "none":
                    result = None
                else:
                    raise ValueError(f"Invalid fetch_mode: {fetch_mode}")

                conn.commit()
                return result

        except Exception as e:
            if conn:
                conn.rollback()
            raise

        finally:
            if conn:
                self.release_connection(conn)

    def close(self):
        """Close connection pool."""
        if self._pool:
            self._pool.close()
            logger.info(f"Closed connection pool for {self.name}")


class LocalDatabaseProvider(DatabaseProvider):
    """
    Local SQLite database provider for final fallback.

    Uses SQLite as local persistent storage when all cloud providers fail.
    Provides same interface as PostgreSQL providers for seamless failover.
    """

    def __init__(self, db_path: str = "data/local.db"):
        """
        Initialize local SQLite provider.

        Args:
            db_path: Path to SQLite database file (default: data/local.db)
        """
        super().__init__("local", f"sqlite:///{db_path}")
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_schema()

    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        import pathlib
        pathlib.Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize SQLite schema if needed."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create conversation_states table (SQLite compatible)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_states (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    conversation_type TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    data TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                )
            """)

            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_conversation_states_user
                ON conversation_states(user_id, conversation_type)
            """)

            conn.commit()
            conn.close()
            logger.info(f"Initialized local SQLite database at {self.db_path}")

        except Exception as e:
            logger.warning(f"Failed to initialize local database: {e}")

    def get_connection(self):
        """Get SQLite connection."""
        import sqlite3
        return sqlite3.connect(self.db_path)

    def release_connection(self, conn):
        """Close SQLite connection."""
        if conn:
            conn.close()

    def health_check(self) -> bool:
        """SQLite is always healthy (local file)."""
        import pathlib
        return pathlib.Path(self.db_path).parent.exists()

    def execute_query(self, query: str, params: Optional[Tuple] = None, fetch_mode: str = "all") -> Any:
        """Execute query on SQLite with PostgreSQL compatibility."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Convert PostgreSQL-style placeholders ($1, $2) to SQLite (?, ?)
            sqlite_query = query.replace("$1", "?").replace("$2", "?").replace("$3", "?").replace("$4", "?").replace("$5", "?")

            # Execute query
            if params:
                cursor.execute(sqlite_query, params)
            else:
                cursor.execute(sqlite_query)

            # Handle different fetch modes
            if fetch_mode == "all":
                result = cursor.fetchall()
            elif fetch_mode == "one":
                result = cursor.fetchone()
            elif fetch_mode == "none":
                result = None
            else:
                raise ValueError(f"Invalid fetch_mode: {fetch_mode}")

            conn.commit()
            return result

        except Exception as e:
            if conn:
                conn.rollback()
            raise

        finally:
            if conn:
                self.release_connection(conn)


class DatabaseManager:
    """
    Multi-provider database manager with automatic failover.

    Features:
    - Supports Supabase, Railway, Neon (PostgreSQL + pgvector)
    - Automatic failover on connection/query errors
    - Connection pooling per provider
    - Health checks with caching (60s TTL)
    - Thread-safe operations

    Environment Variables:
        DATABASE_PROVIDER: Primary provider (default: supabase)
        DATABASE_FAILOVER_ENABLED: Enable failover (default: true)
        DATABASE_FAILOVER_ORDER: Failover sequence (default: supabase,railway,neon)

    Example:
        >>> db = DatabaseManager()
        >>>
        >>> # Query with automatic failover
        >>> rows = db.execute_query("SELECT * FROM knowledge_atoms LIMIT 10")
        >>>
        >>> # Force specific provider
        >>> db.set_provider('neon')
        >>> version = db.execute_query("SELECT version()", fetch_mode="one")
    """

    def __init__(self):
        """Initialize database manager with all configured providers."""
        self.providers: Dict[str, DatabaseProvider] = {}
        self.primary_provider = os.getenv("DATABASE_PROVIDER", "neon")
        self.failover_enabled = os.getenv("DATABASE_FAILOVER_ENABLED", "true").lower() == "true"
        # Cloud providers first, local SQLite as final fallback
        self.failover_order = os.getenv("DATABASE_FAILOVER_ORDER", "neon,supabase,railway,local").split(",")

        # Initialize providers
        self._init_providers()

        logger.info(f"DatabaseManager initialized: primary={self.primary_provider}, "
                   f"failover={'enabled' if self.failover_enabled else 'disabled'}, "
                   f"order={self.failover_order}")

    def _init_providers(self):
        """Initialize all available providers."""
        # Supabase provider
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase_db_password = os.getenv("SUPABASE_DB_PASSWORD")
        supabase_db_host = os.getenv("SUPABASE_DB_HOST")

        if supabase_url and supabase_db_password and supabase_db_host:
            # Build connection string for direct PostgreSQL access
            conn_str = f"postgresql://postgres:{supabase_db_password}@{supabase_db_host}:5432/postgres"
            self.providers["supabase"] = DatabaseProvider("supabase", conn_str)
            logger.info("Initialized Supabase provider")
        else:
            logger.warning("Supabase credentials incomplete, skipping provider")

        # Railway provider
        railway_db_url = os.getenv("RAILWAY_DB_URL")
        if railway_db_url and "your_railway_password_here" not in railway_db_url:
            self.providers["railway"] = DatabaseProvider("railway", railway_db_url)
            logger.info("Initialized Railway provider")
        else:
            logger.warning("Railway credentials incomplete, skipping provider")

        # Neon provider
        neon_db_url = os.getenv("NEON_DB_URL")
        if neon_db_url:
            self.providers["neon"] = DatabaseProvider("neon", neon_db_url)
            logger.info("Initialized Neon provider")
        else:
            logger.warning("Neon credentials incomplete, skipping provider")

        # Local SQLite provider (always available as final fallback)
        local_db_path = os.getenv("LOCAL_DB_PATH", "data/local.db")
        try:
            self.providers["local"] = LocalDatabaseProvider(local_db_path)
            logger.info(f"Initialized Local SQLite provider at {local_db_path}")
        except Exception as e:
            logger.warning(f"Failed to initialize local provider: {e}")

        # Validate at least one provider available
        if not self.providers:
            raise ValueError(
                "No database providers configured. "
                "Set at least one of: SUPABASE_URL, RAILWAY_DB_URL, NEON_DB_URL"
            )

    def set_provider(self, provider_name: str):
        """
        Set the primary provider.

        Args:
            provider_name: Provider to use (supabase, railway, neon)

        Raises:
            ValueError: If provider not configured
        """
        if provider_name not in self.providers:
            raise ValueError(
                f"Provider '{provider_name}' not configured. "
                f"Available: {list(self.providers.keys())}"
            )

        self.primary_provider = provider_name
        logger.info(f"Primary provider set to: {provider_name}")

    def health_check(self, provider_name: Optional[str] = None) -> bool:
        """
        Check health of provider(s).

        Args:
            provider_name: Specific provider to check, or None for primary

        Returns:
            bool: True if healthy, False otherwise
        """
        if provider_name:
            if provider_name not in self.providers:
                logger.warning(f"Provider '{provider_name}' not configured")
                return False
            return self.providers[provider_name].health_check()
        else:
            return self.providers[self.primary_provider].health_check()

    def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all providers.

        Returns:
            dict: {provider_name: is_healthy}
        """
        return {
            name: provider.health_check()
            for name, provider in self.providers.items()
        }

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_mode: str = "all"
    ) -> Any:
        """
        Execute query with automatic failover.

        Tries primary provider first, then failover providers in order
        if failover is enabled.

        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch_mode: 'all', 'one', 'none'

        Returns:
            Query results based on fetch_mode

        Raises:
            Exception: If all providers fail
        """
        # Determine which providers to try
        if self.failover_enabled:
            providers_to_try = [
                p for p in self.failover_order
                if p in self.providers
            ]
        else:
            providers_to_try = [self.primary_provider]

        last_error = None

        # Try each provider in order
        for provider_name in providers_to_try:
            provider = self.providers[provider_name]

            # Skip unhealthy providers (except if it's the last one)
            if provider_name != providers_to_try[-1]:
                if not provider.health_check():
                    logger.warning(f"Skipping unhealthy provider: {provider_name}")
                    continue

            try:
                logger.debug(f"Executing query on {provider_name}")
                result = provider.execute_query(query, params, fetch_mode)

                # Log if we failed over to non-primary
                if provider_name != self.primary_provider:
                    logger.warning(
                        f"Executed on failover provider '{provider_name}' "
                        f"(primary '{self.primary_provider}' unavailable)"
                    )

                return result

            except Exception as e:
                last_error = e
                logger.error(f"Query failed on {provider_name}: {str(e)}")

                # If this was the last provider, raise
                if provider_name == providers_to_try[-1]:
                    raise

                # Otherwise, continue to next provider
                logger.info(f"Failing over to next provider...")
                continue

        # Should never reach here, but just in case
        raise Exception(f"All database providers failed. Last error: {last_error}")

    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all providers.

        Returns:
            dict: {provider_name: {healthy: bool, ...}}
        """
        return {
            name: {
                "healthy": provider.health_check(),
                "connection_string_host": urlparse(provider.connection_string).hostname,
                "pool_active": provider._pool is not None
            }
            for name, provider in self.providers.items()
        }

    def close_all(self):
        """Close all provider connection pools."""
        for provider in self.providers.values():
            provider.close()
        logger.info("All database connections closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connections."""
        self.close_all()
        return False
