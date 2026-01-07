"""
Memory API Endpoints (Story 4.1)

REST API for memory storage and retrieval operations.

AC#6: Memory Service API with proper error handling
AC#7: Protected endpoints with Supabase JWT authentication
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.models.memory import (
    MemoryInput,
    MemoryOutput,
    MemoryStoreResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryListResponse,
    MemoryContextResponse,
    AssetHistoryResponse,
)
from app.services.memory import (
    MemoryService,
    MemoryServiceError,
    get_memory_service,
    extract_asset_from_message,
)
from app.services.memory.asset_detector import get_asset_detector

logger = logging.getLogger(__name__)

router = APIRouter()


def get_service() -> MemoryService:
    """Dependency to get memory service instance."""
    return get_memory_service()


@router.post(
    "",
    response_model=MemoryStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a memory",
    description="Store user interaction in vector memory with optional asset linking.",
)
async def store_memory(
    memory_input: MemoryInput,
    current_user: CurrentUser = Depends(get_current_user),
    service: MemoryService = Depends(get_service),
) -> MemoryStoreResponse:
    """
    Store a memory from user interaction.

    AC#3: Stores memory with user_id from JWT claims.
    AC#4: Includes asset_id in metadata when provided or detected.
    AC#7: Protected with Supabase JWT authentication.

    Args:
        memory_input: Messages and optional metadata to store
        current_user: Authenticated user from JWT
        service: Memory service instance

    Returns:
        MemoryStoreResponse with storage status

    Raises:
        HTTPException 503: If memory service is not configured
        HTTPException 500: If storage fails
    """
    try:
        # Build metadata with user_id
        metadata = memory_input.metadata.model_dump() if memory_input.metadata else {}

        # AC#4: Auto-detect asset from messages if not provided
        if not metadata.get("asset_id"):
            for msg in memory_input.messages:
                if msg.role == "user":
                    detected_asset = await extract_asset_from_message(msg.content)
                    if detected_asset:
                        metadata["asset_id"] = detected_asset
                        logger.info(f"Auto-detected asset: {detected_asset}")
                        break

        # Convert messages to dict format
        messages = [msg.model_dump() for msg in memory_input.messages]

        # AC#3: Store with user_id from JWT
        result = await service.add_memory(
            messages=messages,
            user_id=current_user.id,
            metadata=metadata,
        )

        logger.info(f"Memory stored for user {current_user.id}: {result.get('id')}")

        return MemoryStoreResponse(
            id=result.get("id", ""),
            status="stored",
            message="Memory stored successfully",
        )

    except MemoryServiceError as e:
        logger.error(f"Memory service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store memory. Please try again.",
        )


@router.get(
    "/search",
    response_model=MemorySearchResponse,
    summary="Search memories",
    description="Semantic search for relevant memories using vector similarity.",
)
async def search_memories(
    query: str = Query(..., description="Search query text", min_length=1),
    limit: int = Query(5, description="Maximum results", ge=1, le=50),
    threshold: float = Query(0.7, description="Minimum similarity", ge=0.0, le=1.0),
    asset_id: Optional[str] = Query(None, description="Filter by asset_id"),
    current_user: CurrentUser = Depends(get_current_user),
    service: MemoryService = Depends(get_service),
) -> MemorySearchResponse:
    """
    Search for relevant memories using semantic similarity.

    AC#5: Retrieves memories using semantic similarity search.
    AC#5: Filters by user_id for personalization.
    AC#7: Protected with Supabase JWT authentication.

    Args:
        query: Search query text
        limit: Maximum number of results (default 5)
        threshold: Minimum similarity threshold (default 0.7)
        asset_id: Optional asset filter
        current_user: Authenticated user from JWT
        service: Memory service instance

    Returns:
        MemorySearchResponse with matching memories
    """
    try:
        # AC#5: Search with user_id filter
        results = await service.search_memory(
            query=query,
            user_id=current_user.id,
            limit=limit,
            threshold=threshold,
            asset_id=asset_id,
        )

        # Convert to response format
        memories = [
            MemoryOutput(
                id=mem.get("id", str(i)),
                memory=mem.get("memory", mem.get("content", "")),
                score=mem.get("score", mem.get("similarity")),
                metadata=mem.get("metadata"),
            )
            for i, mem in enumerate(results)
        ]

        logger.debug(f"Search returned {len(memories)} results for user {current_user.id}")

        return MemorySearchResponse(
            query=query,
            count=len(memories),
            memories=memories,
        )

    except MemoryServiceError as e:
        logger.error(f"Memory service error: {e}")
        # AC#6: Graceful degradation - return empty results
        return MemorySearchResponse(
            query=query,
            count=0,
            memories=[],
        )
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        # Return empty results instead of error for search
        return MemorySearchResponse(
            query=query,
            count=0,
            memories=[],
        )


@router.get(
    "",
    response_model=MemoryListResponse,
    summary="Get all memories",
    description="Retrieve all memories for the authenticated user.",
)
async def get_all_memories(
    limit: int = Query(50, description="Maximum results", ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    service: MemoryService = Depends(get_service),
) -> MemoryListResponse:
    """
    Get all memories for the authenticated user.

    AC#6: Provides get_all_memories() method.
    AC#7: Protected with Supabase JWT authentication.

    Args:
        limit: Maximum number of memories to return
        current_user: Authenticated user from JWT
        service: Memory service instance

    Returns:
        MemoryListResponse with all user memories
    """
    try:
        results = await service.get_all_memories(
            user_id=current_user.id,
            limit=limit,
        )

        # Convert to response format
        memories = [
            MemoryOutput(
                id=mem.get("id", str(i)),
                memory=mem.get("memory", mem.get("content", "")),
                score=mem.get("score", mem.get("similarity")),
                metadata=mem.get("metadata"),
            )
            for i, mem in enumerate(results)
        ]

        return MemoryListResponse(
            user_id=current_user.id,
            count=len(memories),
            memories=memories,
        )

    except MemoryServiceError as e:
        logger.error(f"Memory service error: {e}")
        return MemoryListResponse(
            user_id=current_user.id,
            count=0,
            memories=[],
        )
    except Exception as e:
        logger.error(f"Failed to get memories: {e}")
        return MemoryListResponse(
            user_id=current_user.id,
            count=0,
            memories=[],
        )


@router.get(
    "/asset/{asset_id}",
    response_model=AssetHistoryResponse,
    summary="Get asset history",
    description="Retrieve memory history for a specific asset.",
)
async def get_asset_history(
    asset_id: str,
    limit: int = Query(10, description="Maximum results", ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
    service: MemoryService = Depends(get_service),
) -> AssetHistoryResponse:
    """
    Get memory history for a specific asset.

    AC#4: Retrieves memories linked to asset_id in metadata.
    AC#7: Protected with Supabase JWT authentication.

    Args:
        asset_id: Asset identifier from Plant Object Model
        limit: Maximum number of memories to return
        current_user: Authenticated user from JWT
        service: Memory service instance

    Returns:
        AssetHistoryResponse with asset-related memories
    """
    try:
        # Get asset info for response
        detector = get_asset_detector()
        asset_info = await detector.get_asset_info(asset_id)
        asset_name = asset_info.get("name") if asset_info else None

        # AC#4: Retrieve asset-specific memories
        results = await service.get_asset_history(
            asset_id=asset_id,
            user_id=current_user.id,
            limit=limit,
        )

        # Convert to response format
        memories = [
            MemoryOutput(
                id=mem.get("id", str(i)),
                memory=mem.get("memory", mem.get("content", "")),
                score=mem.get("score", mem.get("similarity")),
                metadata=mem.get("metadata"),
            )
            for i, mem in enumerate(results)
        ]

        return AssetHistoryResponse(
            asset_id=asset_id,
            asset_name=asset_name,
            count=len(memories),
            memories=memories,
        )

    except MemoryServiceError as e:
        logger.error(f"Memory service error: {e}")
        return AssetHistoryResponse(
            asset_id=asset_id,
            asset_name=None,
            count=0,
            memories=[],
        )
    except Exception as e:
        logger.error(f"Failed to get asset history: {e}")
        return AssetHistoryResponse(
            asset_id=asset_id,
            asset_name=None,
            count=0,
            memories=[],
        )


@router.get(
    "/context",
    response_model=MemoryContextResponse,
    summary="Get context for query",
    description="Get relevant context for a query in LangChain-compatible format.",
)
async def get_context_for_query(
    query: str = Query(..., description="Current query", min_length=1),
    asset_id: Optional[str] = Query(None, description="Optional asset filter"),
    limit: int = Query(5, description="Maximum context items", ge=1, le=20),
    current_user: CurrentUser = Depends(get_current_user),
    service: MemoryService = Depends(get_service),
) -> MemoryContextResponse:
    """
    Get relevant context formatted for LangChain integration.

    AC#8: Returns context in LangChain-compatible format.
    AC#7: Protected with Supabase JWT authentication.

    Args:
        query: Current user query
        asset_id: Optional asset to include asset-specific history
        limit: Maximum number of context items
        current_user: Authenticated user from JWT
        service: Memory service instance

    Returns:
        MemoryContextResponse with LangChain-compatible messages
    """
    try:
        # AC#8: Get context in LangChain format
        context = await service.get_context_for_query(
            query=query,
            user_id=current_user.id,
            asset_id=asset_id,
            limit=limit,
        )

        return MemoryContextResponse(
            query=query,
            context=context,
        )

    except MemoryServiceError as e:
        logger.error(f"Memory service error: {e}")
        return MemoryContextResponse(
            query=query,
            context=[],
        )
    except Exception as e:
        logger.error(f"Failed to get context: {e}")
        return MemoryContextResponse(
            query=query,
            context=[],
        )


@router.get(
    "/status",
    summary="Memory service status",
    description="Check if the memory service is properly configured and initialized.",
)
async def get_memory_status(
    service: MemoryService = Depends(get_service),
) -> dict:
    """
    Get memory service status.

    Returns:
        Dict with configuration and initialization status
    """
    return {
        "configured": service.is_configured(),
        "initialized": service.is_initialized(),
        "status": "ready" if service.is_initialized() else (
            "not_configured" if not service.is_configured() else "not_initialized"
        ),
    }
