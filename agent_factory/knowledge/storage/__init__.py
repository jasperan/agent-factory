"""
Vector Storage Factory

Provides unified interface for creating vector storage backends.

Usage:
    >>> from agent_factory.knowledge.storage import create_vector_store
    >>>
    >>> # Use default backend (from VECTOR_STORE_BACKEND env var, defaults to postgres)
    >>> store = create_vector_store()
    >>>
    >>> # Explicitly specify backend
    >>> postgres_store = create_vector_store("postgres")
    >>> chroma_store = create_vector_store("chromadb")
    >>>
    >>> # Use with context manager
    >>> with create_vector_store("postgres") as store:
    ...     results = store.search("equipment_manuals", "fault code F3002")

Environment Variables:
    VECTOR_STORE_BACKEND: Storage backend to use ("postgres" or "chromadb")
                          Defaults to "postgres"
    CHROMA_PERSIST_DIR: Directory for ChromaDB persistence
                        Defaults to "./chroma_db"
"""

import os
import logging
from typing import Optional

from agent_factory.knowledge.storage.abstract_vector_store import (
    AbstractVectorStore,
    SearchResult,
    StorageError
)
from agent_factory.knowledge.storage.postgres_vector_store import PostgresVectorStore
from agent_factory.knowledge.storage.chromadb_vector_store import ChromaDBVectorStore

logger = logging.getLogger(__name__)

# Export key classes
__all__ = [
    "create_vector_store",
    "AbstractVectorStore",
    "PostgresVectorStore",
    "ChromaDBVectorStore",
    "SearchResult",
    "StorageError",
    "get_default_backend"
]


def get_default_backend() -> str:
    """
    Get the default storage backend from environment.

    Returns:
        Backend name ("postgres" or "chromadb")
    """
    backend = os.getenv("VECTOR_STORE_BACKEND", "postgres").lower()

    if backend not in ["postgres", "chromadb"]:
        logger.warning(
            f"Invalid VECTOR_STORE_BACKEND: {backend}. "
            "Defaulting to 'postgres'. Valid options: postgres, chromadb"
        )
        backend = "postgres"

    return backend


def create_vector_store(backend: Optional[str] = None) -> AbstractVectorStore:
    """
    Create a vector storage backend instance.

    Args:
        backend: Storage backend to use ("postgres" or "chromadb").
                If None, uses VECTOR_STORE_BACKEND env var (defaults to "postgres").

    Returns:
        AbstractVectorStore implementation

    Raises:
        ValueError: If backend is invalid
        StorageError: If backend initialization fails

    Examples:
        >>> # Use default (environment variable or postgres)
        >>> store = create_vector_store()
        >>>
        >>> # Explicitly use PostgreSQL
        >>> postgres = create_vector_store("postgres")
        >>>
        >>> # Explicitly use ChromaDB
        >>> chroma = create_vector_store("chromadb")
    """
    # Determine backend
    if backend is None:
        backend = get_default_backend()
    else:
        backend = backend.lower()

    logger.info(f"Creating vector store with backend: {backend}")

    # Create appropriate backend
    try:
        if backend == "postgres":
            return PostgresVectorStore()
        elif backend == "chromadb":
            return ChromaDBVectorStore()
        else:
            raise ValueError(
                f"Unknown backend: {backend}. "
                "Valid options: postgres, chromadb"
            )
    except Exception as e:
        logger.error(f"Failed to create {backend} vector store: {e}")
        raise StorageError(f"Backend initialization failed: {e}")


# Singleton instances (cached)
_postgres_instance: Optional[PostgresVectorStore] = None
_chromadb_instance: Optional[ChromaDBVectorStore] = None


def get_vector_store(backend: Optional[str] = None, use_singleton: bool = True) -> AbstractVectorStore:
    """
    Get a vector storage backend instance.

    Similar to create_vector_store, but optionally caches instances as singletons.

    Args:
        backend: Storage backend ("postgres" or "chromadb")
        use_singleton: If True, returns cached instance (default True)

    Returns:
        AbstractVectorStore implementation

    Examples:
        >>> # Get singleton instance (cached)
        >>> store1 = get_vector_store("postgres")
        >>> store2 = get_vector_store("postgres")
        >>> assert store1 is store2  # Same instance
        >>>
        >>> # Get new instance (not cached)
        >>> store3 = get_vector_store("postgres", use_singleton=False)
        >>> assert store1 is not store3  # Different instances
    """
    global _postgres_instance, _chromadb_instance

    if backend is None:
        backend = get_default_backend()
    else:
        backend = backend.lower()

    if not use_singleton:
        return create_vector_store(backend)

    # Return cached instance
    if backend == "postgres":
        if _postgres_instance is None:
            _postgres_instance = PostgresVectorStore()
        return _postgres_instance
    elif backend == "chromadb":
        if _chromadb_instance is None:
            _chromadb_instance = ChromaDBVectorStore()
        return _chromadb_instance
    else:
        raise ValueError(f"Unknown backend: {backend}")


def reset_singletons():
    """
    Reset singleton instances (useful for testing).

    Closes any open connections before clearing instances.
    """
    global _postgres_instance, _chromadb_instance

    if _postgres_instance is not None:
        _postgres_instance.close()
        _postgres_instance = None

    if _chromadb_instance is not None:
        _chromadb_instance.close()
        _chromadb_instance = None

    logger.info("Singleton instances reset")
