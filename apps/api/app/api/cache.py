"""
Cache API Endpoints (Story 5.8)

REST API for cache statistics and management.

AC#7: Cache Statistics Endpoint
- GET /api/cache/stats returns cache statistics
- Endpoint is admin-only (requires authentication)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user, require_admin
from app.models.user import CurrentUser
from app.services.agent.cache import get_tool_cache

logger = logging.getLogger(__name__)

router = APIRouter()


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    enabled: bool = Field(..., description="Whether caching is enabled")
    max_size_per_tier: int = Field(..., description="Maximum entries per tier")
    total_entries: int = Field(..., description="Total entries across all tiers")
    entries_by_tier: dict = Field(..., description="Entry count by tier")
    tier_ttls: dict = Field(..., description="TTL in seconds for each tier")
    hits: int = Field(..., description="Total cache hits")
    misses: int = Field(..., description="Total cache misses")
    hit_rate_percent: float = Field(..., description="Hit rate as percentage")
    invalidations: int = Field(..., description="Total invalidations")


class CacheInvalidateResponse(BaseModel):
    """Response model for cache invalidation."""

    invalidated: int = Field(..., description="Number of entries invalidated")
    message: str = Field(..., description="Human-readable result message")


@router.get(
    "/stats",
    response_model=CacheStatsResponse,
    summary="Get cache statistics",
    description="""
    Get statistics about the tool response cache.

    **Story 5.8 AC#7: Cache Statistics Endpoint**
    - Returns total cache entries
    - Returns hits and misses count
    - Returns hit rate percentage
    - Returns entries by tier

    **Authentication:** Required (admin only)
    """,
)
async def get_cache_stats(
    current_user: CurrentUser = Depends(require_admin),
) -> CacheStatsResponse:
    """
    Get cache statistics.

    AC#7: Cache Statistics Endpoint
    - Returns cache performance metrics
    - Admin-only access

    Args:
        current_user: Authenticated admin user from JWT

    Returns:
        CacheStatsResponse with cache statistics
    """
    cache = get_tool_cache()
    stats = cache.get_stats()

    logger.info(f"Cache stats requested by user {current_user.id}")

    return CacheStatsResponse(**stats)


@router.post(
    "/invalidate",
    response_model=CacheInvalidateResponse,
    summary="Invalidate cache entries",
    description="""
    Invalidate cache entries by pattern, tier, or tool name.

    **Story 5.8 AC#4: Cache Invalidation**
    - Clear entries matching a pattern (e.g., "asset_lookup:*")
    - Clear an entire tier (e.g., "live")
    - Clear all entries for a specific tool

    **Authentication:** Required (admin only)
    """,
)
async def invalidate_cache(
    pattern: Optional[str] = Query(
        None,
        description="Pattern to match cache keys (supports * wildcard)"
    ),
    tier: Optional[str] = Query(
        None,
        description="Cache tier to clear entirely: live, daily, or static"
    ),
    tool_name: Optional[str] = Query(
        None,
        description="Clear all cache entries for a specific tool"
    ),
    current_user: CurrentUser = Depends(require_admin),
) -> CacheInvalidateResponse:
    """
    Invalidate cache entries.

    AC#4: Cache Invalidation
    - Logs all invalidation events
    - Returns count of invalidated entries

    Args:
        pattern: Pattern to match (supports * wildcard)
        tier: Specific tier to clear
        tool_name: Clear entries for a specific tool
        current_user: Authenticated user from JWT

    Returns:
        CacheInvalidateResponse with invalidation count
    """
    # Validate tier if provided
    valid_tiers = ["live", "daily", "static"]
    if tier and tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
        )

    # Must provide at least one filter
    if not any([pattern, tier, tool_name]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least one of: pattern, tier, or tool_name",
        )

    cache = get_tool_cache()
    count = cache.invalidate(pattern=pattern, tier=tier, tool_name=tool_name)

    # Build descriptive message
    if tier:
        message = f"Cleared {count} entries from '{tier}' tier"
    elif tool_name:
        message = f"Cleared {count} entries for tool '{tool_name}'"
    elif pattern:
        message = f"Cleared {count} entries matching pattern '{pattern}'"
    else:
        message = f"Cleared {count} entries"

    logger.info(
        f"Cache invalidation by user {current_user.id}: {message}"
    )

    return CacheInvalidateResponse(
        invalidated=count,
        message=message,
    )


@router.post(
    "/clear",
    response_model=CacheInvalidateResponse,
    summary="Clear all cache entries",
    description="""
    Clear all cache entries across all tiers.

    **Use with caution** - this will clear the entire cache.

    **Authentication:** Required (admin only)
    """,
)
async def clear_cache(
    current_user: CurrentUser = Depends(require_admin),
) -> CacheInvalidateResponse:
    """
    Clear all cache entries.

    Args:
        current_user: Authenticated user from JWT

    Returns:
        CacheInvalidateResponse with total invalidation count
    """
    cache = get_tool_cache()
    count = cache.invalidate_all()

    logger.warning(
        f"Full cache clear by user {current_user.id}: {count} entries"
    )

    return CacheInvalidateResponse(
        invalidated=count,
        message=f"Cleared all {count} cache entries",
    )
