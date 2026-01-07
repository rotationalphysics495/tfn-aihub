"""
Asset History API Endpoints (Story 4.4)

REST API for asset history storage and retrieval operations.

AC#3: History Storage API
AC#6: Performance Requirements
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.models.asset_history import (
    AssetHistoryCreate,
    AssetHistoryRead,
    AssetHistoryCreateResponse,
    AssetHistoryListResponse,
    AssetHistorySearchResponse,
    AssetHistorySearchResult,
    AIContextRequest,
    AIContextResponse,
    EventType,
)
from app.services.asset_history_service import (
    AssetHistoryService,
    AssetHistoryServiceError,
    get_asset_history_service,
)
from app.services.ai_context_service import (
    AIContextService,
    AIContextServiceError,
    get_ai_context_service,
)
from app.services.mem0_asset_service import (
    Mem0AssetService,
    get_mem0_asset_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_history_service() -> AssetHistoryService:
    """Dependency to get asset history service instance."""
    return get_asset_history_service()


def get_context_service() -> AIContextService:
    """Dependency to get AI context service instance."""
    return get_ai_context_service()


def get_mem0_service() -> Mem0AssetService:
    """Dependency to get Mem0 asset service instance."""
    return get_mem0_asset_service()


@router.post(
    "/{asset_id}/history",
    response_model=AssetHistoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create asset history entry",
    description="Create a new history entry for an asset with automatic embedding generation.",
)
async def create_history_entry(
    asset_id: UUID,
    entry: AssetHistoryCreate,
    current_user: CurrentUser = Depends(get_current_user),
    history_service: AssetHistoryService = Depends(get_history_service),
    mem0_service: Mem0AssetService = Depends(get_mem0_service),
) -> AssetHistoryCreateResponse:
    """
    Create a new asset history entry.

    AC#3 Task 6.2: POST /api/assets/{asset_id}/history endpoint.
    AC#3: History entries automatically generate Mem0 memories on creation.
    AC#5: Protected by Supabase Auth JWT validation.

    Args:
        asset_id: Asset UUID to add history for
        entry: History entry data
        current_user: Authenticated user from JWT
        history_service: Asset history service
        mem0_service: Mem0 asset service for memory storage

    Returns:
        AssetHistoryCreateResponse with created entry ID

    Raises:
        HTTPException 503: If service is not configured
        HTTPException 500: If creation fails
    """
    try:
        # Create history entry in database
        created = await history_service.create_history_entry(
            asset_id=asset_id,
            entry=entry,
            user_id=UUID(current_user.id),
        )

        # Also store in Mem0 for memory integration (AC#2)
        try:
            if mem0_service.is_configured():
                await mem0_service.add_history_entry_to_mem0(
                    asset_id=asset_id,
                    event_type=entry.event_type,
                    title=entry.title,
                    description=entry.description,
                    resolution=entry.resolution,
                )
        except Exception as e:
            # Log but don't fail if Mem0 storage fails
            logger.warning(f"Failed to store in Mem0: {e}")

        logger.info(
            f"History entry created for asset {asset_id} "
            f"by user {current_user.id}: {created.id}"
        )

        return AssetHistoryCreateResponse(
            id=created.id,
            status="created",
            message="Asset history entry created successfully",
        )

    except AssetHistoryServiceError as e:
        logger.error(f"History service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create history entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create history entry. Please try again.",
        )


@router.get(
    "/{asset_id}/history",
    response_model=AssetHistoryListResponse,
    summary="Get asset history",
    description="Retrieve paginated history entries for an asset.",
)
async def get_asset_history(
    asset_id: UUID,
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(10, description="Items per page", ge=1, le=100),
    event_type: Optional[List[EventType]] = Query(
        None, description="Filter by event types"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    history_service: AssetHistoryService = Depends(get_history_service),
) -> AssetHistoryListResponse:
    """
    Get paginated history for an asset.

    AC#3 Task 6.3: GET /api/assets/{asset_id}/history with pagination.
    AC#6: Support for assets with 1000+ history entries.

    Args:
        asset_id: Asset UUID to get history for
        page: Page number (1-indexed)
        page_size: Items per page
        event_type: Optional filter by event types
        current_user: Authenticated user from JWT
        history_service: Asset history service

    Returns:
        AssetHistoryListResponse with paginated entries
    """
    try:
        items, pagination = await history_service.get_asset_history(
            asset_id=asset_id,
            page=page,
            page_size=page_size,
            event_types=event_type,
        )

        return AssetHistoryListResponse(
            items=items,
            pagination=pagination,
        )

    except AssetHistoryServiceError as e:
        logger.error(f"History service error: {e}")
        # Return empty result on error for graceful degradation
        return AssetHistoryListResponse(
            items=[],
            pagination={
                "total": 0,
                "page": page,
                "page_size": page_size,
                "has_next": False,
            },
        )
    except Exception as e:
        logger.error(f"Failed to get asset history: {e}")
        return AssetHistoryListResponse(
            items=[],
            pagination={
                "total": 0,
                "page": page,
                "page_size": page_size,
                "has_next": False,
            },
        )


@router.get(
    "/{asset_id}/history/search",
    response_model=AssetHistorySearchResponse,
    summary="Search asset history",
    description="Semantic search within asset history entries.",
)
async def search_asset_history(
    asset_id: UUID,
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(5, description="Maximum results", ge=1, le=50),
    event_type: Optional[List[EventType]] = Query(
        None, description="Filter by event types"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    history_service: AssetHistoryService = Depends(get_history_service),
) -> AssetHistorySearchResponse:
    """
    Semantic search within asset history.

    AC#3 Task 6.4: GET /api/assets/{asset_id}/history/search with query param.
    AC#6: Semantic search returns results within 1 second.

    Args:
        asset_id: Asset UUID to search history for
        q: Search query text
        limit: Maximum number of results
        event_type: Optional filter by event types
        current_user: Authenticated user from JWT
        history_service: Asset history service

    Returns:
        AssetHistorySearchResponse with ranked results
    """
    try:
        results = await history_service.search_asset_history(
            asset_id=asset_id,
            query=q,
            limit=limit,
            event_types=event_type,
        )

        return AssetHistorySearchResponse(
            query=q,
            asset_id=asset_id,
            results=results,
            count=len(results),
        )

    except AssetHistoryServiceError as e:
        logger.error(f"Search error: {e}")
        # Return empty results on error
        return AssetHistorySearchResponse(
            query=q,
            asset_id=asset_id,
            results=[],
            count=0,
        )
    except Exception as e:
        logger.error(f"Failed to search asset history: {e}")
        return AssetHistorySearchResponse(
            query=q,
            asset_id=asset_id,
            results=[],
            count=0,
        )


@router.get(
    "/{asset_id}/history/context",
    response_model=AIContextResponse,
    summary="Get AI context for asset",
    description="Get relevant history formatted for LLM context injection.",
)
async def get_ai_context(
    asset_id: UUID,
    query: str = Query(..., description="Query for context matching", min_length=1),
    limit: int = Query(5, description="Maximum history entries", ge=1, le=20),
    max_tokens: int = Query(2000, description="Maximum tokens", ge=100, le=8000),
    temporal_weighting: bool = Query(True, description="Apply temporal weighting"),
    current_user: CurrentUser = Depends(get_current_user),
    context_service: AIContextService = Depends(get_context_service),
) -> AIContextResponse:
    """
    Get relevant asset history formatted for AI context.

    AC#4: Service function retrieves relevant asset history for AI prompts.
    AC#8: Formatted output suitable for LLM context injection.

    Args:
        asset_id: Asset UUID
        query: Query for semantic matching
        limit: Maximum history entries to include
        max_tokens: Maximum tokens for context output
        temporal_weighting: Apply temporal weighting to ranking
        current_user: Authenticated user from JWT
        context_service: AI context service

    Returns:
        AIContextResponse with formatted context
    """
    try:
        response = await context_service.get_context_for_asset(
            asset_id=asset_id,
            query=query,
            limit=limit,
            max_tokens=max_tokens,
            include_temporal_weighting=temporal_weighting,
        )

        return response

    except AIContextServiceError as e:
        logger.error(f"Context service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get AI context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI context. Please try again.",
        )


@router.get(
    "/history/multi-asset",
    response_model=AssetHistorySearchResponse,
    summary="Search history across multiple assets",
    description="Search history by area or asset group for multi-asset queries.",
)
async def search_multi_asset_history(
    q: str = Query(..., description="Search query", min_length=1),
    area: Optional[str] = Query(None, description="Filter by plant area"),
    asset_ids: Optional[List[UUID]] = Query(None, description="Specific asset IDs"),
    limit: int = Query(10, description="Maximum results", ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
    history_service: AssetHistoryService = Depends(get_history_service),
) -> AssetHistorySearchResponse:
    """
    Search history across multiple assets.

    AC#4 Task 4.6: Supports multi-asset queries (e.g., "all grinding area machines").

    Args:
        q: Search query text
        area: Optional plant area filter
        asset_ids: Optional specific asset IDs
        limit: Maximum number of results
        current_user: Authenticated user from JWT
        history_service: Asset history service

    Returns:
        AssetHistorySearchResponse with results across assets
    """
    try:
        results = await history_service.get_multi_asset_history(
            area=area,
            asset_ids=asset_ids,
            query=q,
            limit=limit,
        )

        # Use first asset_id or a placeholder for the response
        response_asset_id = results[0].asset_id if results else UUID(
            "00000000-0000-0000-0000-000000000000"
        )

        return AssetHistorySearchResponse(
            query=q,
            asset_id=response_asset_id,
            results=results,
            count=len(results),
        )

    except AssetHistoryServiceError as e:
        logger.error(f"Multi-asset search error: {e}")
        return AssetHistorySearchResponse(
            query=q,
            asset_id=UUID("00000000-0000-0000-0000-000000000000"),
            results=[],
            count=0,
        )
    except Exception as e:
        logger.error(f"Failed to search multi-asset history: {e}")
        return AssetHistorySearchResponse(
            query=q,
            asset_id=UUID("00000000-0000-0000-0000-000000000000"),
            results=[],
            count=0,
        )


@router.get(
    "/history/status",
    summary="Asset history service status",
    description="Check if the asset history service is properly configured.",
)
async def get_history_status(
    history_service: AssetHistoryService = Depends(get_history_service),
    mem0_service: Mem0AssetService = Depends(get_mem0_service),
) -> dict:
    """
    Get asset history service status.

    Returns:
        Dict with configuration status
    """
    return {
        "asset_history_service": "ready",
        "mem0_configured": mem0_service.is_configured(),
        "mem0_initialized": mem0_service.is_initialized(),
        "status": "ready",
    }
