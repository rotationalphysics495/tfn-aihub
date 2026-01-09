"""
Tool Response Caching Service (Story 5.8)

Provides caching for agent tool responses with tiered TTLs.

AC#1: Cache Hit Behavior - Cached responses returned with cached_at timestamp
AC#2: Tiered Cache TTLs - live (60s), daily (15min), static (1hr)
AC#3: Cache Key Strategy - tool_name:user_id:params_hash
AC#4: Cache Invalidation - Support for pattern-based and tier-based invalidation
AC#5: Force Refresh Bypass - force_refresh parameter skips cache lookup
AC#6: Cache Decorator Pattern - @cached_tool decorator for easy integration
AC#7: Cache Statistics - Track hits, misses, and invalidations
AC#8: Memory-Efficient - TTLCache with configurable max size and LRU eviction
"""

import contextvars
import hashlib
import json
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional

from cachetools import TTLCache

from app.core.config import get_settings

logger = logging.getLogger(__name__)


# Context variable for force_refresh flag (Story 5.8 AC#5)
# This allows the agent executor to set force_refresh and have it accessible
# in the @cached_tool decorator without modifying LangChain's tool invocation
_force_refresh_context: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "force_refresh", default=False
)


def set_force_refresh(value: bool) -> None:
    """Set the force_refresh flag in the current context."""
    _force_refresh_context.set(value)


def get_force_refresh() -> bool:
    """Get the force_refresh flag from the current context."""
    return _force_refresh_context.get()


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


def _get_cache_tiers() -> Dict[str, int]:
    """
    Get cache tier TTLs from settings.

    AC#2: Tiered Cache TTLs
    - live: 60 seconds (real-time production data)
    - daily: 15 minutes (OEE, downtime summaries)
    - static: 1 hour (asset metadata)
    - none: 0 (never cached)
    """
    settings = get_settings()
    return {
        "live": settings.cache_live_ttl,
        "daily": settings.cache_daily_ttl,
        "static": settings.cache_static_ttl,
        "none": 0,
    }


class ToolCacheService:
    """
    Service for caching tool responses with tiered TTLs.

    AC#8: Memory-Efficient Implementation
    - Uses cachetools TTLCache for in-memory storage
    - Configurable max size (default: 1000 entries per tier)
    - LRU eviction when cache is full
    """

    def __init__(self, max_size: Optional[int] = None):
        """
        Initialize the cache service.

        Args:
            max_size: Maximum entries per tier (default from settings)
        """
        settings = get_settings()
        self.max_size = max_size or settings.cache_max_size
        self.enabled = settings.cache_enabled

        # Get tier TTLs
        self._tiers = _get_cache_tiers()

        # Create separate TTLCache instances for each tier
        # AC#2: Each tier has its own cache with appropriate TTL
        self._caches: Dict[str, TTLCache] = {}
        for tier, ttl in self._tiers.items():
            if ttl > 0:
                self._caches[tier] = TTLCache(maxsize=self.max_size, ttl=ttl)

        # AC#7: Statistics tracking
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
        }

        logger.info(
            f"ToolCacheService initialized: enabled={self.enabled}, "
            f"max_size={self.max_size}, tiers={list(self._caches.keys())}"
        )

    def generate_key(
        self,
        tool_name: str,
        user_id: str,
        params: Dict[str, Any],
    ) -> str:
        """
        Generate unique cache key for a tool invocation.

        AC#3: Cache Key Strategy
        - Format: {tool_name}:{user_id}:{params_hash}
        - Different users have separate cache entries
        - Different parameter values create separate entries

        Args:
            tool_name: Name of the tool
            user_id: User identifier
            params: Tool parameters

        Returns:
            Cache key string
        """
        # Handle None or empty params
        if not params:
            params = {}

        # Filter out None values and internal parameters
        filtered_params = {
            k: v for k, v in params.items()
            if v is not None and k not in ("user_id", "force_refresh")
        }

        # Sort params for consistent hashing
        sorted_params = json.dumps(filtered_params, sort_keys=True, default=str)

        # Generate MD5 hash (12 chars is sufficient for uniqueness)
        params_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]

        return f"{tool_name}:{user_id}:{params_hash}"

    def get(self, key: str, tier: str) -> Optional[Dict[str, Any]]:
        """
        Get cached value if exists and not expired.

        AC#1: Cache Hit Behavior
        - Returns cached response with cached_at timestamp
        - Tracks hit/miss statistics

        Args:
            key: Cache key
            tier: Cache tier (live, daily, static)

        Returns:
            Cached value dict or None if not found
        """
        if not self.enabled or tier == "none":
            return None

        cache = self._caches.get(tier)
        if cache is None:
            return None

        try:
            value = cache.get(key)
            if value is not None:
                self._stats["hits"] += 1
                logger.debug(f"Cache HIT: {key} (tier: {tier})")
                return value
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")

        self._stats["misses"] += 1
        logger.debug(f"Cache MISS: {key} (tier: {tier})")
        return None

    def set(self, key: str, tier: str, value: Dict[str, Any]) -> None:
        """
        Store value in cache.

        AC#1: Adds cached_at timestamp to metadata

        Args:
            key: Cache key
            tier: Cache tier
            value: Value to cache (dict)
        """
        if not self.enabled or tier == "none":
            return

        cache = self._caches.get(tier)
        if cache is None:
            return

        try:
            # Add cache metadata
            # Make a copy to avoid mutating the original
            cached_value = dict(value)
            cached_value["metadata"] = dict(cached_value.get("metadata", {}))
            cached_value["metadata"]["cached_at"] = _utcnow().isoformat()
            cached_value["metadata"]["cache_tier"] = tier
            cached_value["metadata"]["cache_key"] = key

            cache[key] = cached_value
            logger.debug(f"Cache SET: {key} (tier: {tier})")
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")

    def invalidate(
        self,
        pattern: Optional[str] = None,
        tier: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> int:
        """
        Invalidate cache entries.

        AC#4: Cache Invalidation on Events
        - Support invalidation by tier (clears entire tier)
        - Support invalidation by pattern (wildcard matching)
        - Support invalidation by tool name
        - Logs all invalidation events

        Args:
            pattern: Pattern to match (supports * wildcard)
            tier: Specific tier to clear entirely
            tool_name: Clear all entries for a specific tool

        Returns:
            Number of entries invalidated
        """
        invalidated = 0

        if tier and tier in self._caches:
            # Clear specific tier entirely
            count = len(self._caches[tier])
            self._caches[tier].clear()
            invalidated = count
            logger.info(f"Cache tier '{tier}' cleared: {count} entries")

        elif tool_name:
            # Clear entries for a specific tool
            for cache in self._caches.values():
                keys_to_delete = [
                    k for k in list(cache.keys())
                    if k.startswith(f"{tool_name}:")
                ]
                for key in keys_to_delete:
                    try:
                        del cache[key]
                        invalidated += 1
                    except KeyError:
                        pass  # Already evicted
            logger.info(f"Cache entries for tool '{tool_name}' cleared: {invalidated}")

        elif pattern:
            # Clear entries matching pattern
            # Convert wildcard pattern to prefix match
            match_prefix = pattern.replace("*", "")
            for cache in self._caches.values():
                keys_to_delete = [
                    k for k in list(cache.keys())
                    if match_prefix in k
                ]
                for key in keys_to_delete:
                    try:
                        del cache[key]
                        invalidated += 1
                    except KeyError:
                        pass
            logger.info(f"Cache entries matching '{pattern}' cleared: {invalidated}")

        self._stats["invalidations"] += invalidated
        return invalidated

    def invalidate_all(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Total number of entries invalidated
        """
        invalidated = 0
        for tier, cache in self._caches.items():
            count = len(cache)
            cache.clear()
            invalidated += count
            logger.debug(f"Cache tier '{tier}' cleared: {count} entries")

        self._stats["invalidations"] += invalidated
        logger.info(f"All caches cleared: {invalidated} total entries")
        return invalidated

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        AC#7: Cache Statistics
        - Total cache entries
        - Hits and misses count
        - Hit rate percentage
        - Entries by tier

        Returns:
            Dict with cache statistics
        """
        entries_by_tier = {
            tier: len(cache)
            for tier, cache in self._caches.items()
        }

        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "enabled": self.enabled,
            "max_size_per_tier": self.max_size,
            "total_entries": sum(entries_by_tier.values()),
            "entries_by_tier": entries_by_tier,
            "tier_ttls": {k: v for k, v in self._tiers.items() if v > 0},
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "invalidations": self._stats["invalidations"],
        }

    def reset_stats(self) -> None:
        """Reset statistics counters (primarily for testing)."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
        }


# Module-level singleton instance
_tool_cache: Optional[ToolCacheService] = None


def get_tool_cache() -> ToolCacheService:
    """
    Get the singleton ToolCacheService instance.

    Returns:
        ToolCacheService instance
    """
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = ToolCacheService()
    return _tool_cache


def reset_tool_cache() -> None:
    """
    Reset the singleton cache instance.

    Primarily used for testing.
    """
    global _tool_cache
    _tool_cache = None


def cached_tool(tier: str = "daily"):
    """
    Decorator for caching tool responses.

    AC#6: Cache Decorator Pattern
    - Handles cache lookup before tool execution
    - Stores result in cache after execution
    - Adds cached_at timestamp to metadata
    - Supports force_refresh bypass

    Usage:
        @cached_tool(tier="daily")
        async def _arun(self, **kwargs) -> ToolResult:
            ...

    Args:
        tier: Cache tier - "live" (60s), "daily" (15min), "static" (1hr), "none"

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Import here to avoid circular dependency
            from app.services.agent.base import ToolResult

            cache = get_tool_cache()

            # AC#5: Check for force_refresh from both kwargs and context variable
            # The context variable is set by the agent executor, kwargs is a fallback
            force_refresh = kwargs.pop("force_refresh", False) or get_force_refresh()

            # Generate cache key
            # AC#3: Key includes tool_name, user_id, and hashed params
            tool_name = getattr(self, "name", func.__name__)
            user_id = kwargs.get("user_id", "anonymous")
            cache_key = cache.generate_key(tool_name, user_id, kwargs)

            # Check cache (unless force_refresh)
            if not force_refresh:
                cached = cache.get(cache_key, tier)
                if cached is not None:
                    # AC#1: Return cached result with cached_at timestamp
                    logger.debug(f"Returning cached result for {tool_name}")

                    # Reconstruct ToolResult from cached dict
                    # The cached_at is already in metadata from cache.set()
                    return ToolResult(**cached)

            # Execute tool
            result = await func(self, *args, **kwargs)

            # Store in cache
            # AC#1: The cache.set() adds cached_at timestamp
            cache.set(cache_key, tier, result.model_dump())

            return result

        # Store tier info on the wrapper for introspection
        wrapper._cache_tier = tier
        return wrapper

    return decorator
