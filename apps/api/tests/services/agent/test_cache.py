"""
Tests for Tool Response Caching Service (Story 5.8)

AC#1: Cache Hit Behavior - Cached responses returned with cached_at timestamp
AC#2: Tiered Cache TTLs - live (60s), daily (15min), static (1hr)
AC#3: Cache Key Strategy - tool_name:user_id:params_hash
AC#4: Cache Invalidation - Support for pattern-based and tier-based invalidation
AC#5: Force Refresh Bypass - force_refresh parameter skips cache lookup
AC#6: Cache Decorator Pattern - @cached_tool decorator for easy integration
AC#7: Cache Statistics - Track hits, misses, and invalidations
AC#8: Memory-Efficient - TTLCache with configurable max size and LRU eviction
"""

import asyncio
import os
import pytest
import time
from datetime import datetime, timezone
from typing import Type
from unittest.mock import AsyncMock, patch, MagicMock

from pydantic import BaseModel, Field

# Set test environment variables before importing cache module
os.environ["CACHE_ENABLED"] = "true"
os.environ["CACHE_MAX_SIZE"] = "100"
os.environ["CACHE_LIVE_TTL"] = "60"
os.environ["CACHE_DAILY_TTL"] = "900"
os.environ["CACHE_STATIC_TTL"] = "3600"


class TestCacheKeyGeneration:
    """Tests for cache key generation (AC#3)."""

    def test_generate_key_basic(self):
        """AC#3: Key includes tool_name, user_id, and params_hash."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)
        key = cache.generate_key(
            tool_name="asset_lookup",
            user_id="user-123",
            params={"asset_name": "Grinder 5"},
        )

        assert key.startswith("asset_lookup:user-123:")
        # Should have a 12-character hash suffix
        parts = key.split(":")
        assert len(parts) == 3
        assert len(parts[2]) == 12

    def test_generate_key_different_users(self):
        """AC#3: Different users have separate cache entries."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        key1 = cache.generate_key(
            tool_name="oee_query",
            user_id="user-A",
            params={"scope": "plant"},
        )
        key2 = cache.generate_key(
            tool_name="oee_query",
            user_id="user-B",
            params={"scope": "plant"},
        )

        assert key1 != key2
        assert "user-A" in key1
        assert "user-B" in key2

    def test_generate_key_different_params(self):
        """AC#3: Different parameter values create separate entries."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        key1 = cache.generate_key(
            tool_name="oee_query",
            user_id="user-123",
            params={"scope": "plant"},
        )
        key2 = cache.generate_key(
            tool_name="oee_query",
            user_id="user-123",
            params={"scope": "Grinding"},
        )

        assert key1 != key2

    def test_generate_key_consistent(self):
        """AC#3: Same inputs produce consistent key."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        params = {"asset_name": "Grinder 5", "days_back": 7}

        key1 = cache.generate_key("asset_lookup", "user-123", params)
        key2 = cache.generate_key("asset_lookup", "user-123", params)

        assert key1 == key2

    def test_generate_key_param_order_independent(self):
        """Key generation is order-independent for params."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        params1 = {"a": 1, "b": 2}
        params2 = {"b": 2, "a": 1}

        key1 = cache.generate_key("tool", "user", params1)
        key2 = cache.generate_key("tool", "user", params2)

        assert key1 == key2

    def test_generate_key_handles_none_params(self):
        """AC#3: Handle None and empty parameters."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        key1 = cache.generate_key("tool", "user", None)
        key2 = cache.generate_key("tool", "user", {})

        # Both should generate valid keys
        assert key1.startswith("tool:user:")
        assert key2.startswith("tool:user:")
        # Empty dict and None should produce same result
        assert key1 == key2

    def test_generate_key_filters_internal_params(self):
        """Key generation filters out user_id and force_refresh from params."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        params_with_internal = {
            "scope": "plant",
            "user_id": "will-be-filtered",
            "force_refresh": True,
        }
        params_without_internal = {"scope": "plant"}

        key1 = cache.generate_key("tool", "user", params_with_internal)
        key2 = cache.generate_key("tool", "user", params_without_internal)

        assert key1 == key2


class TestCacheOperations:
    """Tests for cache get/set operations (AC#1)."""

    def test_cache_set_and_get(self):
        """AC#1: Cache hit returns cached response."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        key = "tool:user:abc123"
        value = {"data": {"oee": 87.5}, "success": True}

        cache.set(key, "daily", value)
        cached = cache.get(key, "daily")

        assert cached is not None
        assert cached["data"]["oee"] == 87.5

    def test_cache_get_adds_cached_at_timestamp(self):
        """AC#1: Cached response includes cached_at timestamp."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        key = "tool:user:abc123"
        value = {"data": {"value": 100}, "metadata": {}}

        cache.set(key, "daily", value)
        cached = cache.get(key, "daily")

        assert "cached_at" in cached["metadata"]
        assert "cache_tier" in cached["metadata"]
        assert cached["metadata"]["cache_tier"] == "daily"

    def test_cache_miss_returns_none(self):
        """Cache miss returns None."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        result = cache.get("nonexistent:key:here", "daily")
        assert result is None

    def test_cache_disabled(self):
        """Cache operations are no-ops when disabled."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)
        cache.enabled = False

        cache.set("key", "daily", {"data": 123})
        result = cache.get("key", "daily")

        assert result is None

    def test_cache_none_tier(self):
        """Items with 'none' tier are not cached."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        cache.set("key", "none", {"data": 123})
        result = cache.get("key", "none")

        assert result is None


class TestCacheTiers:
    """Tests for tiered cache TTLs (AC#2)."""

    def test_cache_has_three_tiers(self):
        """AC#2: Cache has live, daily, and static tiers."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        assert "live" in cache._caches
        assert "daily" in cache._caches
        assert "static" in cache._caches

    def test_cache_tiers_are_separate(self):
        """Entries in different tiers are separate."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        cache.set("same:key:here", "live", {"data": "live_data"})
        cache.set("same:key:here", "daily", {"data": "daily_data"})

        live_result = cache.get("same:key:here", "live")
        daily_result = cache.get("same:key:here", "daily")

        assert live_result["data"] == "live_data"
        assert daily_result["data"] == "daily_data"


class TestCacheStatistics:
    """Tests for cache statistics tracking (AC#7)."""

    def test_cache_tracks_hits(self):
        """AC#7: Cache tracks hit count."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)
        cache.reset_stats()

        cache.set("key", "daily", {"data": 123})
        cache.get("key", "daily")
        cache.get("key", "daily")

        stats = cache.get_stats()
        assert stats["hits"] == 2

    def test_cache_tracks_misses(self):
        """AC#7: Cache tracks miss count."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)
        cache.reset_stats()

        cache.get("nonexistent1", "daily")
        cache.get("nonexistent2", "daily")

        stats = cache.get_stats()
        assert stats["misses"] == 2

    def test_cache_calculates_hit_rate(self):
        """AC#7: Cache calculates hit rate percentage."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)
        cache.reset_stats()

        cache.set("key", "daily", {"data": 123})
        cache.get("key", "daily")  # hit
        cache.get("key", "daily")  # hit
        cache.get("nonexistent", "daily")  # miss
        cache.get("nonexistent", "daily")  # miss

        stats = cache.get_stats()
        assert stats["hit_rate_percent"] == 50.0

    def test_cache_stats_entries_by_tier(self):
        """AC#7: Stats include entries by tier."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        cache.set("live1", "live", {"data": 1})
        cache.set("daily1", "daily", {"data": 2})
        cache.set("daily2", "daily", {"data": 3})
        cache.set("static1", "static", {"data": 4})

        stats = cache.get_stats()
        assert stats["entries_by_tier"]["live"] == 1
        assert stats["entries_by_tier"]["daily"] == 2
        assert stats["entries_by_tier"]["static"] == 1
        assert stats["total_entries"] == 4


class TestCacheInvalidation:
    """Tests for cache invalidation (AC#4)."""

    def test_invalidate_by_tier(self):
        """AC#4: Can invalidate an entire tier."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        cache.set("key1", "daily", {"data": 1})
        cache.set("key2", "daily", {"data": 2})
        cache.set("key3", "live", {"data": 3})

        count = cache.invalidate(tier="daily")

        assert count == 2
        assert cache.get("key1", "daily") is None
        assert cache.get("key2", "daily") is None
        assert cache.get("key3", "live") is not None

    def test_invalidate_by_tool_name(self):
        """AC#4: Can invalidate by tool name."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        cache.set("oee_query:user1:abc", "daily", {"data": 1})
        cache.set("oee_query:user2:def", "daily", {"data": 2})
        cache.set("asset_lookup:user1:ghi", "daily", {"data": 3})

        count = cache.invalidate(tool_name="oee_query")

        assert count == 2
        assert cache.get("oee_query:user1:abc", "daily") is None
        assert cache.get("oee_query:user2:def", "daily") is None
        assert cache.get("asset_lookup:user1:ghi", "daily") is not None

    def test_invalidate_by_pattern(self):
        """AC#4: Can invalidate by pattern with wildcard."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        cache.set("tool:user1:abc", "daily", {"data": 1})
        cache.set("tool:user1:def", "daily", {"data": 2})
        cache.set("tool:user2:ghi", "daily", {"data": 3})

        count = cache.invalidate(pattern="user1:*")

        assert count == 2
        assert cache.get("tool:user1:abc", "daily") is None
        assert cache.get("tool:user1:def", "daily") is None
        assert cache.get("tool:user2:ghi", "daily") is not None

    def test_invalidate_all(self):
        """Can clear all cache entries."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)

        cache.set("key1", "live", {"data": 1})
        cache.set("key2", "daily", {"data": 2})
        cache.set("key3", "static", {"data": 3})

        count = cache.invalidate_all()

        assert count == 3
        assert cache.get("key1", "live") is None
        assert cache.get("key2", "daily") is None
        assert cache.get("key3", "static") is None

    def test_invalidation_tracked_in_stats(self):
        """AC#4: Cache invalidation is logged in stats."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=100)
        cache.reset_stats()

        cache.set("key1", "daily", {"data": 1})
        cache.set("key2", "daily", {"data": 2})

        cache.invalidate(tier="daily")

        stats = cache.get_stats()
        assert stats["invalidations"] == 2


class TestCacheDecorator:
    """Tests for @cached_tool decorator (AC#6)."""

    @pytest.mark.asyncio
    async def test_decorator_caches_tool_result(self):
        """AC#6: Decorator caches tool results."""
        from app.services.agent.cache import cached_tool, reset_tool_cache
        from app.services.agent.base import ManufacturingTool, ToolResult

        reset_tool_cache()

        call_count = 0

        class MockInput(BaseModel):
            value: str

        class TestTool(ManufacturingTool):
            name: str = "test_tool"
            description: str = "Test tool"
            args_schema: Type[BaseModel] = MockInput

            @cached_tool(tier="daily")
            async def _arun(self, value: str, **kwargs) -> ToolResult:
                nonlocal call_count
                call_count += 1
                return self._create_success_result(
                    data={"value": value, "call": call_count}
                )

        tool = TestTool()

        # First call should execute the tool
        result1 = await tool._arun(value="test", user_id="user1")
        assert call_count == 1
        assert result1.data["value"] == "test"

        # Second call should return cached result
        result2 = await tool._arun(value="test", user_id="user1")
        assert call_count == 1  # Still 1, not executed again
        assert result2.data["call"] == 1  # Same call number

    @pytest.mark.asyncio
    async def test_decorator_force_refresh_bypasses_cache(self):
        """AC#5: force_refresh bypasses cache lookup."""
        from app.services.agent.cache import cached_tool, reset_tool_cache
        from app.services.agent.base import ManufacturingTool, ToolResult

        reset_tool_cache()

        call_count = 0

        class MockInput(BaseModel):
            value: str

        class TestTool(ManufacturingTool):
            name: str = "test_tool_refresh"
            description: str = "Test tool"
            args_schema: Type[BaseModel] = MockInput

            @cached_tool(tier="daily")
            async def _arun(self, value: str, **kwargs) -> ToolResult:
                nonlocal call_count
                call_count += 1
                return self._create_success_result(
                    data={"value": value, "call": call_count}
                )

        tool = TestTool()

        # First call
        result1 = await tool._arun(value="test", user_id="user1")
        assert call_count == 1

        # Force refresh should bypass cache
        result2 = await tool._arun(value="test", user_id="user1", force_refresh=True)
        assert call_count == 2  # Executed again
        assert result2.data["call"] == 2  # New call number

    @pytest.mark.asyncio
    async def test_decorator_different_params_different_cache(self):
        """Decorator caches separately for different params."""
        from app.services.agent.cache import cached_tool, reset_tool_cache
        from app.services.agent.base import ManufacturingTool, ToolResult

        reset_tool_cache()

        class MockInput(BaseModel):
            scope: str

        class TestTool(ManufacturingTool):
            name: str = "test_tool_params"
            description: str = "Test tool"
            args_schema: Type[BaseModel] = MockInput

            @cached_tool(tier="daily")
            async def _arun(self, scope: str, **kwargs) -> ToolResult:
                return self._create_success_result(data={"scope": scope})

        tool = TestTool()

        # Different params should have separate cache entries
        result1 = await tool._arun(scope="plant", user_id="user1")
        result2 = await tool._arun(scope="Grinding", user_id="user1")

        assert result1.data["scope"] == "plant"
        assert result2.data["scope"] == "Grinding"


class TestCacheSingleton:
    """Tests for cache singleton pattern."""

    def test_get_tool_cache_returns_singleton(self):
        """get_tool_cache returns the same instance."""
        from app.services.agent.cache import get_tool_cache, reset_tool_cache

        reset_tool_cache()

        cache1 = get_tool_cache()
        cache2 = get_tool_cache()

        assert cache1 is cache2

    def test_reset_tool_cache_creates_new_instance(self):
        """reset_tool_cache creates a new instance."""
        from app.services.agent.cache import get_tool_cache, reset_tool_cache

        cache1 = get_tool_cache()
        reset_tool_cache()
        cache2 = get_tool_cache()

        assert cache1 is not cache2


class TestCacheMaxSize:
    """Tests for cache max size (AC#8)."""

    def test_cache_respects_max_size(self):
        """AC#8: Cache respects max_size configuration."""
        from app.services.agent.cache import ToolCacheService

        cache = ToolCacheService(max_size=3)

        # Add 4 entries - one should be evicted
        cache.set("key1", "daily", {"data": 1})
        cache.set("key2", "daily", {"data": 2})
        cache.set("key3", "daily", {"data": 3})
        cache.set("key4", "daily", {"data": 4})

        # Should have max 3 entries in daily tier
        stats = cache.get_stats()
        assert stats["entries_by_tier"]["daily"] <= 3


class TestForceRefreshContext:
    """Tests for force_refresh context variable (AC#5)."""

    def test_set_and_get_force_refresh(self):
        """Can set and get force_refresh context variable."""
        from app.services.agent.cache import set_force_refresh, get_force_refresh

        # Default should be False
        assert get_force_refresh() is False

        # Set to True
        set_force_refresh(True)
        assert get_force_refresh() is True

        # Reset to False
        set_force_refresh(False)
        assert get_force_refresh() is False

    @pytest.mark.asyncio
    async def test_decorator_respects_context_variable(self):
        """AC#5: Decorator reads force_refresh from context variable."""
        from app.services.agent.cache import (
            cached_tool, reset_tool_cache, set_force_refresh
        )
        from app.services.agent.base import ManufacturingTool, ToolResult

        reset_tool_cache()
        set_force_refresh(False)

        call_count = 0

        class MockInput(BaseModel):
            value: str

        class TestTool(ManufacturingTool):
            name: str = "test_tool_context"
            description: str = "Test tool"
            args_schema: Type[BaseModel] = MockInput

            @cached_tool(tier="daily")
            async def _arun(self, value: str, **kwargs) -> ToolResult:
                nonlocal call_count
                call_count += 1
                return self._create_success_result(
                    data={"value": value, "call": call_count}
                )

        tool = TestTool()

        # First call - should cache
        result1 = await tool._arun(value="test", user_id="user1")
        assert call_count == 1

        # Second call - should return cached (context is False)
        result2 = await tool._arun(value="test", user_id="user1")
        assert call_count == 1  # Still 1

        # Set context to force_refresh=True
        set_force_refresh(True)

        # Third call - should bypass cache due to context
        result3 = await tool._arun(value="test", user_id="user1")
        assert call_count == 2  # Now 2 because cache was bypassed

        # Reset context
        set_force_refresh(False)
