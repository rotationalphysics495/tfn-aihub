# Story 5.8: Tool Response Caching

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **tool responses to be cached with appropriate TTLs**,
so that **repeated queries are fast and database load is reduced**.

## Acceptance Criteria

1. **Cache Hit Behavior**
   - GIVEN a user asks the same question twice within the cache TTL
   - WHEN the second request is processed
   - THEN the cached response is returned
   - AND the response includes `cached_at` timestamp in metadata
   - AND the database is NOT queried again

2. **Tiered Cache TTLs**
   - GIVEN different data types have different freshness requirements
   - WHEN tools return responses
   - THEN they are cached according to their tier:
     - Live Data (Production Status, Alert Check): 60 seconds
     - Daily Data (OEE, Downtime, Financial): 15 minutes (900 seconds)
     - Static Data (Asset Lookup metadata): 1 hour (3600 seconds)
   - AND cache tier is determined by tool configuration

3. **Cache Key Strategy**
   - GIVEN cache needs to differentiate between requests
   - WHEN a cache key is generated
   - THEN it includes: tool_name, user_id, and hashed query parameters
   - AND different users have separate cache entries
   - AND different parameter values create separate entries

4. **Cache Invalidation on Events**
   - GIVEN a safety event occurs (from safety_events table)
   - WHEN the Action List or related caches are checked
   - THEN relevant caches are invalidated
   - AND the next request fetches fresh data
   - AND cache invalidation is logged

5. **Force Refresh Bypass**
   - GIVEN a developer needs to debug or get fresh data
   - WHEN they call an endpoint with `force_refresh=true`
   - THEN the cache is bypassed
   - AND fresh data is fetched from the database
   - AND the fresh data is stored in cache (replacing old entry)

6. **Cache Decorator Pattern**
   - GIVEN tools need caching behavior
   - WHEN implementing caching
   - THEN a `@cached_tool` decorator is available
   - AND the decorator handles cache lookup, storage, and key generation
   - AND tools can specify their cache tier in configuration

7. **Cache Statistics Endpoint**
   - GIVEN operators need to monitor cache performance
   - WHEN they call GET /api/cache/stats
   - THEN the response includes:
     - Total cache entries
     - Hits and misses count
     - Hit rate percentage
     - Entries by tier
   - AND the endpoint is admin-only

8. **Memory-Efficient Implementation**
   - GIVEN cache should not consume excessive memory
   - WHEN implementing the cache
   - THEN `cachetools` TTLCache is used for in-memory storage
   - AND maximum cache size is configurable (default: 1000 entries)
   - AND LRU eviction removes oldest entries when full

## Tasks / Subtasks

- [ ] Task 1: Create Cache Service (AC: #6, #8)
  - [ ] 1.1 Create `apps/api/app/services/agent/cache.py`
  - [ ] 1.2 Install and configure `cachetools` library
  - [ ] 1.3 Create TTLCache instances for each tier
  - [ ] 1.4 Implement cache_key_generator() function
  - [ ] 1.5 Implement get_cached() method
  - [ ] 1.6 Implement set_cached() method
  - [ ] 1.7 Add max size configuration
  - [ ] 1.8 Create unit tests for cache service

- [ ] Task 2: Create Cache Decorator (AC: #6)
  - [ ] 2.1 Add @cached_tool decorator to cache.py
  - [ ] 2.2 Support tier parameter (live, daily, static)
  - [ ] 2.3 Handle cache lookup before tool execution
  - [ ] 2.4 Store result in cache after execution
  - [ ] 2.5 Add cached_at timestamp to metadata
  - [ ] 2.6 Create unit tests for decorator

- [ ] Task 3: Implement Cache Key Generation (AC: #3)
  - [ ] 3.1 Create hash_params() function for parameter hashing
  - [ ] 3.2 Format: {tool_name}:{user_id}:{params_hash}
  - [ ] 3.3 Handle None and empty parameters
  - [ ] 3.4 Ensure consistent key generation
  - [ ] 3.5 Create tests for key generation

- [ ] Task 4: Update Tools with Caching (AC: #2)
  - [ ] 4.1 Add @cached_tool(tier="static") to AssetLookupTool
  - [ ] 4.2 Add @cached_tool(tier="daily") to OEEQueryTool
  - [ ] 4.3 Add @cached_tool(tier="daily") to DowntimeAnalysisTool
  - [ ] 4.4 Add @cached_tool(tier="live") to ProductionStatusTool
  - [ ] 4.5 Create integration tests for each tool

- [ ] Task 5: Implement Force Refresh (AC: #5)
  - [ ] 5.1 Add force_refresh parameter to agent endpoint
  - [ ] 5.2 Pass force_refresh to cache decorator
  - [ ] 5.3 Skip cache lookup when force_refresh=true
  - [ ] 5.4 Still store fresh result in cache
  - [ ] 5.5 Create tests for force refresh behavior

- [ ] Task 6: Implement Cache Invalidation (AC: #4)
  - [ ] 6.1 Create invalidate_cache() method
  - [ ] 6.2 Support invalidation by tool name
  - [ ] 6.3 Support invalidation by pattern (e.g., "action_list:*")
  - [ ] 6.4 Add event listener for safety_events changes
  - [ ] 6.5 Log invalidation events
  - [ ] 6.6 Create tests for invalidation

- [ ] Task 7: Create Cache Stats Endpoint (AC: #7)
  - [ ] 7.1 Create `apps/api/app/api/cache.py` router
  - [ ] 7.2 Implement GET /api/cache/stats endpoint
  - [ ] 7.3 Track hits and misses counters
  - [ ] 7.4 Calculate hit rate percentage
  - [ ] 7.5 Group entries by tier
  - [ ] 7.6 Add admin-only authentication
  - [ ] 7.7 Create tests for stats endpoint

- [ ] Task 8: Add Configuration (AC: #8)
  - [ ] 8.1 Add CACHE_MAX_SIZE to config.py (default: 1000)
  - [ ] 8.2 Add CACHE_ENABLED to config.py (default: true)
  - [ ] 8.3 Add tier TTLs to config (overridable)
  - [ ] 8.4 Update .env.example with cache settings
  - [ ] 8.5 Create tests for configuration

## Dev Notes

### Architecture Compliance

This story implements **NFR7: Tool Response Caching** from the PRD Addendum. It provides performance optimization for the agent tools while respecting data freshness requirements.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/cache.py`
**Pattern:** Decorator pattern with TTLCache

### Technical Requirements

**Cache Tier Configuration:**
```
| Tier   | TTL      | Use Cases                          |
|--------|----------|------------------------------------|
| live   | 60s      | ProductionStatus, AlertCheck       |
| daily  | 15min    | OEE, Downtime, Financial Impact    |
| static | 1hr      | Asset metadata, Cost Centers       |
| none   | 0s       | Memory Recall (never cached)       |
```

**Cache Flow Diagram:**
```
Tool._arun() called
    |
    v
+-------------------+
| @cached_tool      |
| decorator         |
+-------------------+
    |
    +---> Generate cache key
    |     {tool}:{user}:{params_hash}
    |
    +---> Check cache
    |         |
    |         +---> HIT: Return cached ToolResult
    |         |           (add cached_at to metadata)
    |         |
    |         +---> MISS: Execute tool._arun()
    |                     |
    |                     v
    |               Store result in cache
    |                     |
    |                     v
    |               Return fresh ToolResult
    |
    +---> force_refresh=true?
              Skip cache lookup, always execute
```

### Cache Service Implementation

**cache.py Core Structure:**
```python
from typing import Optional, Any, Dict, Callable
from functools import wraps
from datetime import datetime
import hashlib
import json
from cachetools import TTLCache
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Cache tier TTLs (in seconds)
CACHE_TIERS = {
    "live": 60,       # 1 minute
    "daily": 900,     # 15 minutes
    "static": 3600,   # 1 hour
    "none": 0         # No caching
}

class ToolCacheService:
    """Service for caching tool responses with tiered TTLs."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.enabled = settings.CACHE_ENABLED

        # Create separate caches for each tier
        self._caches: Dict[str, TTLCache] = {
            tier: TTLCache(maxsize=max_size, ttl=ttl)
            for tier, ttl in CACHE_TIERS.items()
            if ttl > 0
        }

        # Statistics tracking
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0
        }

    def generate_key(
        self,
        tool_name: str,
        user_id: str,
        params: Dict[str, Any]
    ) -> str:
        """Generate unique cache key for a tool invocation."""
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        return f"{tool_name}:{user_id}:{params_hash}"

    def get(
        self,
        key: str,
        tier: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached value if exists and not expired."""
        if not self.enabled or tier == "none":
            return None

        cache = self._caches.get(tier)
        if cache is None:
            return None

        value = cache.get(key)
        if value is not None:
            self._stats["hits"] += 1
            logger.debug(f"Cache HIT: {key}")
            return value

        self._stats["misses"] += 1
        logger.debug(f"Cache MISS: {key}")
        return None

    def set(
        self,
        key: str,
        tier: str,
        value: Dict[str, Any]
    ) -> None:
        """Store value in cache."""
        if not self.enabled or tier == "none":
            return

        cache = self._caches.get(tier)
        if cache is None:
            return

        # Add cached_at timestamp
        value["metadata"] = value.get("metadata", {})
        value["metadata"]["cached_at"] = datetime.utcnow().isoformat()
        value["metadata"]["cache_tier"] = tier
        value["metadata"]["cache_key"] = key

        cache[key] = value
        logger.debug(f"Cache SET: {key} (tier: {tier})")

    def invalidate(self, pattern: str = None, tier: str = None) -> int:
        """Invalidate cache entries matching pattern or tier."""
        invalidated = 0

        if tier and tier in self._caches:
            # Clear specific tier
            count = len(self._caches[tier])
            self._caches[tier].clear()
            invalidated = count
        elif pattern:
            # Clear entries matching pattern
            for cache in self._caches.values():
                keys_to_delete = [
                    k for k in cache.keys()
                    if pattern.replace("*", "") in k
                ]
                for key in keys_to_delete:
                    del cache[key]
                    invalidated += 1

        self._stats["invalidations"] += invalidated
        logger.info(f"Cache invalidated: {invalidated} entries")
        return invalidated

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0

        entries_by_tier = {
            tier: len(cache)
            for tier, cache in self._caches.items()
        }

        return {
            "enabled": self.enabled,
            "max_size_per_tier": self.max_size,
            "total_entries": sum(entries_by_tier.values()),
            "entries_by_tier": entries_by_tier,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "invalidations": self._stats["invalidations"]
        }


# Singleton instance
tool_cache = ToolCacheService(max_size=settings.CACHE_MAX_SIZE)


def cached_tool(tier: str = "daily"):
    """Decorator for caching tool responses.

    Usage:
        @cached_tool(tier="daily")
        async def _arun(self, **kwargs) -> ToolResult:
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Check for force_refresh
            force_refresh = kwargs.pop("force_refresh", False)

            # Generate cache key
            tool_name = getattr(self, "name", func.__name__)
            user_id = kwargs.get("user_id", "anonymous")
            cache_key = tool_cache.generate_key(tool_name, user_id, kwargs)

            # Check cache (unless force_refresh)
            if not force_refresh:
                cached = tool_cache.get(cache_key, tier)
                if cached:
                    # Return cached result with updated metadata
                    from app.services.agent.base import ToolResult
                    return ToolResult(**cached)

            # Execute tool
            result = await func(self, *args, **kwargs)

            # Store in cache
            tool_cache.set(cache_key, tier, result.dict())

            return result
        return wrapper
    return decorator
```

### Tool Integration Example

**asset_lookup.py with Caching:**
```python
from app.services.agent.cache import cached_tool

class AssetLookupTool(ManufacturingTool):
    name: str = "asset_lookup"
    cache_tier: str = "static"  # Asset metadata changes rarely

    @cached_tool(tier="static")
    async def _arun(self, asset_name: str, user_id: str = None) -> ToolResult:
        # ... existing implementation ...
        pass
```

**production_status.py with Caching:**
```python
from app.services.agent.cache import cached_tool

class ProductionStatusTool(ManufacturingTool):
    name: str = "production_status"
    cache_tier: str = "live"  # Live data needs short TTL

    @cached_tool(tier="live")
    async def _arun(self, area: str = None, user_id: str = None) -> ToolResult:
        # ... existing implementation ...
        pass
```

### Cache Stats Endpoint

**api/cache.py:**
```python
from fastapi import APIRouter, Depends
from app.services.agent.cache import tool_cache
from app.core.auth import get_admin_user

router = APIRouter(prefix="/api/cache", tags=["cache"])

@router.get("/stats")
async def get_cache_stats(admin: dict = Depends(get_admin_user)):
    """Get cache statistics (admin only)."""
    return tool_cache.get_stats()

@router.post("/invalidate")
async def invalidate_cache(
    pattern: str = None,
    tier: str = None,
    admin: dict = Depends(get_admin_user)
):
    """Invalidate cache entries (admin only)."""
    count = tool_cache.invalidate(pattern=pattern, tier=tier)
    return {"invalidated": count}
```

### Force Refresh in Agent Endpoint

**agent.py Updates:**
```python
class AgentChatRequest(BaseModel):
    message: str
    force_refresh: bool = False  # Bypass cache

@router.post("/api/agent/chat")
async def agent_chat(
    request: AgentChatRequest,
    user: dict = Depends(get_current_user)
):
    # Pass force_refresh to agent
    response = await agent.process_message(
        message=request.message,
        user_id=user["id"],
        force_refresh=request.force_refresh
    )
    return response
```

### Environment Variables

**Add to config.py and .env.example:**
```python
# Cache settings
CACHE_ENABLED: bool = True
CACHE_MAX_SIZE: int = 1000  # Max entries per tier
CACHE_LIVE_TTL: int = 60    # Override live tier TTL
CACHE_DAILY_TTL: int = 900  # Override daily tier TTL
CACHE_STATIC_TTL: int = 3600 # Override static tier TTL
```

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── agent/
│   │       └── cache.py              # Cache service and decorator
│   └── api/
│       └── cache.py                  # Cache stats endpoint
├── tests/
│   ├── test_cache_service.py         # Cache service tests
│   └── test_cache_decorator.py       # Decorator tests
```

**Dependencies to add to requirements.txt:**
```
cachetools>=5.3.0
```

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework) - ToolResult schema
- Stories 5.3-5.6 (Core Tools) - Tools to add caching to

**Blocked By:** Stories 5.1-5.6

**Enables:**
- Epic 6 & 7 - All future tools use caching pattern

### Testing Strategy

1. **Unit Tests:**
   - Cache key generation consistency
   - Cache get/set operations
   - TTL expiration behavior
   - Cache invalidation
   - Statistics tracking
   - Decorator behavior
   - Force refresh bypass

2. **Integration Tests:**
   - Tool caching end-to-end
   - Cache hit verification (no DB query)
   - Different users separate cache
   - Stats endpoint response

3. **Performance Tests:**
   - Cache hit vs miss latency
   - Memory usage under load
   - LRU eviction behavior

4. **Manual Testing:**
   - Query same data twice, verify faster second response
   - Use force_refresh, verify fresh data
   - Check stats endpoint in browser

### NFR Compliance

- **NFR7 (Tool Response Caching):** Tiered caching with appropriate TTLs
- **NFR2 (Latency):** Cached responses return in <100ms
- Memory efficient with configurable max size

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#NFR7: Tool Response Caching] - Caching requirements
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#8.1 Cache Tiers] - TTL specifications
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.8] - Story requirements
- [cachetools Documentation](https://cachetools.readthedocs.io/) - TTLCache reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

