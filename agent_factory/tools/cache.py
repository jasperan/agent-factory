"""
Result caching system for tools.

Provides:
- In-memory cache with TTL
- Cache statistics
- Decorator for easy integration
- Optional Redis backend (future)

Example:
    >>> from agent_factory.tools.cache import CacheManager
    >>> cache = CacheManager(default_ttl=3600)
    >>> cache.set("key", "value", ttl=60)
    >>> value = cache.get("key")
    >>> print(cache.stats())
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps


@dataclass
class CacheEntry:
    """Single cache entry with TTL."""
    value: Any
    expires_at: float  # Unix timestamp
    created_at: float
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expires_at

    def touch(self):
        """Increment hit counter."""
        self.hits += 1


class CacheManager:
    """
    Manages result caching for tools.

    Features:
    - TTL-based expiration
    - Automatic cleanup of expired entries
    - Cache statistics (hits, misses, size)
    - Max size enforcement (LRU eviction)

    Example:
        >>> cache = CacheManager(default_ttl=3600, max_size=1000)
        >>> cache.set("expensive_result", result, ttl=600)
        >>> cached = cache.get("expensive_result")
        >>> stats = cache.stats()
    """

    def __init__(
        self,
        default_ttl: int = 3600,      # 1 hour
        max_size: int = 1000,          # Max cached items
        enable_stats: bool = True,
        cleanup_interval: int = 300    # 5 minutes
    ):
        """
        Initialize cache manager.

        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of cached items
            enable_stats: Track cache statistics
            cleanup_interval: How often to clean expired entries (seconds)
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enable_stats = enable_stats

        self._cache: Dict[str, CacheEntry] = {}
        self._last_cleanup = time.time()
        self._cleanup_interval = cleanup_interval

        # Statistics
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        # Periodic cleanup
        self._maybe_cleanup()

        entry = self._cache.get(key)

        if entry is None:
            if self.enable_stats:
                self._misses += 1
            return None

        # Check expiration
        if entry.is_expired():
            del self._cache[key]
            if self.enable_stats:
                self._misses += 1
            return None

        # Hit!
        if self.enable_stats:
            self._hits += 1
        entry.touch()

        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Cache a value.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: self.default_ttl)
        """
        ttl = ttl if ttl is not None else self.default_ttl

        # Enforce max size (simple LRU - remove least recently used)
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_one()

        expires_at = time.time() + ttl
        created_at = time.time()

        self._cache[key] = CacheEntry(
            value=value,
            expires_at=expires_at,
            created_at=created_at
        )

    def invalidate(self, key: str):
        """
        Remove entry from cache.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        if self.enable_stats:
            self._hits = 0
            self._misses = 0

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, size, hit_rate
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total
        }

    def _evict_one(self):
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find entry with oldest access (lowest hits + oldest created_at)
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hits, self._cache[k].created_at)
        )
        del self._cache[oldest_key]

    def _maybe_cleanup(self):
        """Clean up expired entries if interval passed."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
            self._last_cleanup = now

    def _cleanup(self):
        """Remove all expired entries."""
        expired = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired:
            del self._cache[key]


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments.

    Uses JSON serialization and MD5 hash.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Create stable representation
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())  # Sort for consistency
    }

    # Serialize and hash
    try:
        key_str = json.dumps(key_data, sort_keys=True, default=str)
    except (TypeError, ValueError):
        # Fallback to string representation
        key_str = str(key_data)

    return hashlib.md5(key_str.encode()).hexdigest()


def cached_tool(
    cache_manager: Optional[CacheManager] = None,
    ttl: Optional[int] = None,
    key_prefix: str = ""
):
    """
    Decorator to cache tool results.

    Example:
        >>> cache = CacheManager()
        >>> @cached_tool(cache_manager=cache, ttl=600)
        ... def expensive_operation(query: str) -> str:
        ...     # ... expensive work ...
        ...     return result

    Args:
        cache_manager: CacheManager instance (creates default if None)
        ttl: TTL for cached results
        key_prefix: Prefix for cache keys (useful for namespacing)

    Returns:
        Decorated function
    """
    # Create default cache if not provided
    if cache_manager is None:
        cache_manager = CacheManager()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}{func.__name__}:{generate_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache_manager.set(cache_key, result, ttl=ttl)

            return result

        # Attach cache manager for access
        wrapper.cache_manager = cache_manager

        return wrapper

    return decorator


class ToolCache:
    """
    Wrapper to add caching to existing tools.

    Example:
        >>> from agent_factory.tools.research_tools import CurrentTimeTool
        >>> cache = CacheManager()
        >>> cached_tool = ToolCache(CurrentTimeTool(), cache, ttl=60)
        >>> # Now tool results are cached for 60 seconds
    """

    def __init__(
        self,
        tool: Any,
        cache_manager: CacheManager,
        ttl: Optional[int] = None
    ):
        """
        Wrap a tool with caching.

        Args:
            tool: LangChain tool instance
            cache_manager: CacheManager instance
            ttl: TTL for cached results (default: cache_manager default)
        """
        self.tool = tool
        self.cache_manager = cache_manager
        self.ttl = ttl

        # Wrap the _run method
        original_run = tool._run

        @wraps(original_run)
        def cached_run(*args, **kwargs):
            # Generate cache key
            cache_key = f"{tool.name}:{generate_cache_key(*args, **kwargs)}"

            # Try cache
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            # Execute
            result = original_run(*args, **kwargs)

            # Cache
            cache_manager.set(cache_key, result, ttl=self.ttl)

            return result

        tool._run = cached_run

    def __getattr__(self, name):
        """Proxy all other attributes to the wrapped tool."""
        return getattr(self.tool, name)


# Default global cache (optional convenience)
_global_cache: Optional[CacheManager] = None


def get_global_cache() -> CacheManager:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def clear_global_cache():
    """Clear global cache."""
    global _global_cache
    if _global_cache:
        _global_cache.clear()
