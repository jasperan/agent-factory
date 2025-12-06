"""
Tests for agent_factory.tools.cache module.

Tests caching system:
- Cache set/get operations
- TTL expiration
- Cache invalidation
- Statistics tracking
- LRU eviction
- Tool caching decorator
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from agent_factory.tools.cache import (
    CacheManager,
    cached_tool,
    generate_cache_key,
    get_global_cache,
    clear_global_cache
)


class TestCacheManager:
    """Test cache manager functionality."""

    def test_cache_set_get(self):
        """REQ-DET-005: Set and get cached values."""
        cache = CacheManager()

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_cache_miss(self):
        """REQ-DET-005: Return None on cache miss."""
        cache = CacheManager()

        result = cache.get("nonexistent")
        assert result is None

    def test_cache_expiration(self):
        """REQ-DET-005: Entries expire after TTL."""
        cache = CacheManager(default_ttl=1)  # 1 second

        cache.set("key", "value", ttl=1)

        # Should exist immediately
        assert cache.get("key") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key") is None

    def test_cache_invalidation(self):
        """REQ-DET-005: Manual cache invalidation."""
        cache = CacheManager()

        cache.set("key", "value")
        assert cache.get("key") == "value"

        cache.invalidate("key")
        assert cache.get("key") is None

    def test_cache_clear(self):
        """REQ-DET-005: Clear all cache entries."""
        cache = CacheManager()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self):
        """REQ-DET-005: Track cache statistics."""
        cache = CacheManager(enable_stats=True)

        # Set and get
        cache.set("key", "value")
        cache.get("key")  # Hit
        cache.get("missing")  # Miss

        stats = cache.stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["total_requests"] == 2

    def test_max_size_enforcement(self):
        """REQ-DET-005: Enforce maximum cache size with LRU eviction."""
        cache = CacheManager(max_size=3)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All should exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Add one more (should evict least recently used)
        cache.set("key4", "value4")

        # Size should still be 3
        stats = cache.stats()
        assert stats["size"] == 3

    def test_custom_ttl_per_entry(self):
        """REQ-DET-005: Custom TTL per cache entry."""
        cache = CacheManager(default_ttl=60)

        # Set with custom short TTL
        cache.set("short", "value", ttl=1)

        # Set with default TTL
        cache.set("long", "value")

        # Wait
        time.sleep(1.1)

        # Short should be expired, long should still exist
        assert cache.get("short") is None
        assert cache.get("long") == "value"


class TestCacheKey:
    """Test cache key generation."""

    def test_generate_key_from_args(self):
        """REQ-DET-005: Generate cache key from arguments."""
        key1 = generate_cache_key("arg1", "arg2")
        key2 = generate_cache_key("arg1", "arg2")

        # Same args should generate same key
        assert key1 == key2

    def test_different_args_different_keys(self):
        """REQ-DET-005: Different args generate different keys."""
        key1 = generate_cache_key("arg1")
        key2 = generate_cache_key("arg2")

        assert key1 != key2

    def test_kwargs_in_key(self):
        """REQ-DET-005: Include kwargs in cache key."""
        key1 = generate_cache_key("arg", param1="value1")
        key2 = generate_cache_key("arg", param1="value2")

        assert key1 != key2

    def test_key_order_independence(self):
        """REQ-DET-005: Kwargs order doesn't affect key."""
        key1 = generate_cache_key(a=1, b=2)
        key2 = generate_cache_key(b=2, a=1)

        # Same kwargs (different order) should generate same key
        assert key1 == key2


class TestCachedToolDecorator:
    """Test @cached_tool decorator."""

    def test_cached_function(self):
        """REQ-DET-005: Decorator caches function results."""
        cache = CacheManager()
        call_count = [0]

        @cached_tool(cache_manager=cache)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1

        # Second call (should use cache)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not called again

    def test_cached_different_args(self):
        """REQ-DET-005: Different args not cached together."""
        cache = CacheManager()
        call_count = [0]

        @cached_tool(cache_manager=cache)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count[0] == 2  # Called twice

    def test_cached_with_ttl(self):
        """REQ-DET-005: Decorator respects TTL."""
        cache = CacheManager()
        call_count = [0]

        @cached_tool(cache_manager=cache, ttl=1)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2

        # First call
        expensive_function(5)
        assert call_count[0] == 1

        # Immediate second call (cached)
        expensive_function(5)
        assert call_count[0] == 1

        # Wait for expiration
        time.sleep(1.1)

        # Call after expiration (not cached)
        expensive_function(5)
        assert call_count[0] == 2


class TestGlobalCache:
    """Test global cache convenience functions."""

    def test_get_global_cache(self):
        """REQ-DET-005: Get global cache instance."""
        cache = get_global_cache()

        assert cache is not None
        assert isinstance(cache, CacheManager)

    def test_global_cache_singleton(self):
        """REQ-DET-005: Global cache is singleton."""
        cache1 = get_global_cache()
        cache2 = get_global_cache()

        assert cache1 is cache2

    def test_clear_global_cache(self):
        """REQ-DET-005: Clear global cache."""
        cache = get_global_cache()
        cache.set("key", "value")

        clear_global_cache()

        assert cache.get("key") is None


class TestCacheCleanup:
    """Test automatic cleanup of expired entries."""

    def test_periodic_cleanup(self):
        """REQ-DET-005: Expired entries cleaned up periodically."""
        cache = CacheManager(cleanup_interval=0.5)

        # Add entries with short TTL
        cache.set("key1", "value1", ttl=0.3)
        cache.set("key2", "value2", ttl=0.3)

        # Wait for expiration AND cleanup interval
        time.sleep(0.6)

        # Trigger cleanup by accessing cache (forces check since interval passed)
        cache.get("any_key")

        # Check internal cache is cleaned
        assert len(cache._cache) == 0
