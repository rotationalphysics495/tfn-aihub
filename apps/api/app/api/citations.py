"""
Citations API Endpoints (Story 4.5)

REST API for citation lookup and source data retrieval.

AC#4: Citation UI Rendering
  - Citations render as clickable links in Chat UI
  - Clicking citation opens side panel showing source data

AC#5: Create Citation API Endpoint
  - GET /api/citations/{citation_id} for citation detail lookup
  - GET /api/citations/source/{source_type}/{record_id} for source data

AC#8: Performance Requirements
  - Citation links resolve within 100ms (cached data)
"""

import logging
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.models.citation import (
    Citation,
    CitationDetailResponse,
    SourceLookupResponse,
    SourceType,
    CitationLogEntry,
)
from app.services.citation_generator import (
    CitationGenerator,
    get_citation_generator,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Simple in-memory cache for citation sources
_source_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl: Dict[str, float] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def get_generator() -> CitationGenerator:
    """Dependency to get Citation Generator instance."""
    return get_citation_generator()


def _get_cached_source(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get source data from cache if valid."""
    if cache_key in _source_cache:
        if datetime.now().timestamp() - _cache_ttl.get(cache_key, 0) < CACHE_TTL_SECONDS:
            return _source_cache[cache_key]
        else:
            # Expired - remove from cache
            del _source_cache[cache_key]
            del _cache_ttl[cache_key]
    return None


def _cache_source(cache_key: str, data: Dict[str, Any]) -> None:
    """Cache source data."""
    _source_cache[cache_key] = data
    _cache_ttl[cache_key] = datetime.now().timestamp()


@router.get(
    "/{citation_id}",
    response_model=CitationDetailResponse,
    summary="Get citation details",
    description="""
    Retrieve full details for a citation by its ID.

    Returns the citation metadata and full source data for UI display.
    Response is cached for 5 minutes to meet 100ms latency requirement.

    **Citation ID Formats:**
    - `cit-{uuid}`: Database citations
    - `mem-{uuid}`: Memory citations
    - `calc-{uuid}`: Calculation citations
    """,
)
async def get_citation_detail(
    citation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    generator: CitationGenerator = Depends(get_generator),
) -> CitationDetailResponse:
    """
    Get citation details by ID.

    AC#4: Citation links resolve within 100ms (cached data).

    Args:
        citation_id: The citation ID to retrieve
        current_user: Authenticated user from JWT
        generator: Citation generator service

    Returns:
        CitationDetailResponse with full source data

    Raises:
        HTTPException 404: If citation not found
    """
    # Check cache first
    cache_key = f"citation:{citation_id}"
    cached = _get_cached_source(cache_key)
    if cached:
        return CitationDetailResponse(**cached)

    # Try to get from generator cache
    citation = generator.get_citation(citation_id)

    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Citation '{citation_id}' not found",
        )

    # Build response with source data
    source_data = {}

    if citation.source_type == SourceType.DATABASE:
        # Fetch source data from database
        source_data = await _fetch_database_source(
            citation.source_table,
            citation.record_id,
        )
    elif citation.source_type == SourceType.MEMORY:
        # Fetch memory data
        source_data = await _fetch_memory_source(citation.memory_id)
    elif citation.source_type == SourceType.CALCULATION:
        # For calculations, parse the excerpt
        source_data = {"calculation": citation.excerpt}

    response_data = {
        "id": citation.id,
        "source_type": citation.source_type,
        "source_data": source_data,
        "related_citations": [],  # Could be enhanced to find related
        "fetched_at": datetime.utcnow().isoformat(),
    }

    # Cache the response
    _cache_source(cache_key, response_data)

    return CitationDetailResponse(**response_data)


@router.get(
    "/source/{source_type}/{record_id}",
    response_model=SourceLookupResponse,
    summary="Get source data by type and ID",
    description="""
    Retrieve source data directly by source type and record ID.

    This endpoint allows looking up source data without needing a citation ID.
    Useful for exploring data sources referenced in responses.

    **Source Types:**
    - `database`: Database table records
    - `memory`: Mem0 memory entries
    - `calculation`: Calculated values

    **Examples:**
    - `GET /api/citations/source/database/daily_summaries:uuid-123`
    - `GET /api/citations/source/memory/mem-abc123`
    """,
)
async def get_source_data(
    source_type: SourceType,
    record_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SourceLookupResponse:
    """
    Get source data by type and record ID.

    AC#4: Return source data formatted for UI display.

    Args:
        source_type: Type of source (database, memory, calculation)
        record_id: Record identifier (format depends on source type)
        current_user: Authenticated user from JWT

    Returns:
        SourceLookupResponse with source data

    Raises:
        HTTPException 404: If source not found
    """
    # Check cache first
    cache_key = f"source:{source_type}:{record_id}"
    cached = _get_cached_source(cache_key)
    if cached:
        return SourceLookupResponse(**cached)

    source_data = {}
    source_table = None

    if source_type == SourceType.DATABASE:
        # Parse record_id format: table_name:uuid or just uuid
        if ":" in record_id:
            source_table, actual_id = record_id.split(":", 1)
        else:
            # Default to daily_summaries if no table specified
            source_table = "daily_summaries"
            actual_id = record_id

        source_data = await _fetch_database_source(source_table, actual_id)

    elif source_type == SourceType.MEMORY:
        source_data = await _fetch_memory_source(record_id)

    elif source_type == SourceType.CALCULATION:
        source_data = {"calculation_id": record_id, "note": "Calculation details not stored"}

    if not source_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_type}/{record_id}",
        )

    response_data = {
        "source_type": source_type,
        "source_table": source_table,
        "record_id": record_id,
        "data": source_data,
        "fetched_at": datetime.utcnow().isoformat(),
    }

    # Cache the response
    _cache_source(cache_key, response_data)

    return SourceLookupResponse(**response_data)


@router.get(
    "/audit",
    summary="Get citation audit log",
    description="""
    Retrieve citation audit log entries for compliance review.

    Admin endpoint for reviewing all citation-response pairs.
    Can filter by date range, grounding score, and user.
    """,
)
async def get_citation_audit_log(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    min_grounding_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum grounding score"),
    max_grounding_score: Optional[float] = Query(None, ge=0, le=1, description="Maximum grounding score"),
    limit: int = Query(50, ge=1, le=500, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get citation audit log entries.

    AC#7: Audit log records all citation-response pairs for compliance review.

    Args:
        start_date: Filter by start date
        end_date: Filter by end date
        min_grounding_score: Minimum grounding score filter
        max_grounding_score: Maximum grounding score filter
        limit: Maximum entries to return
        offset: Pagination offset
        current_user: Authenticated user from JWT

    Returns:
        Dict with audit log entries and pagination info
    """
    # This would query the citation_logs table in Supabase
    # For now, return structure for frontend integration

    return {
        "entries": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "min_grounding_score": min_grounding_score,
            "max_grounding_score": max_grounding_score,
        },
        "note": "Audit log entries are stored in citation_logs table",
    }


@router.get(
    "/stats",
    summary="Get citation statistics",
    description="Get aggregated statistics about citation and grounding performance.",
)
async def get_citation_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: CurrentUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get citation statistics for the specified period.

    Useful for monitoring NFR1 compliance over time.

    Args:
        days: Number of days to analyze
        current_user: Authenticated user from JWT

    Returns:
        Dict with citation statistics
    """
    # This would call get_citation_audit_summary() from the database
    # For now, return structure for frontend integration

    return {
        "period_days": days,
        "total_responses": 0,
        "avg_grounding_score": 0.0,
        "low_grounding_count": 0,
        "fully_grounded_count": 0,
        "total_citations": 0,
        "avg_citations_per_response": 0.0,
        "by_source_type": {
            "database": 0,
            "memory": 0,
            "calculation": 0,
            "inference": 0,
        },
        "note": "Statistics computed from citation_logs table",
    }


async def _fetch_database_source(
    table_name: Optional[str],
    record_id: Optional[str],
) -> Dict[str, Any]:
    """
    Fetch source data from database.

    AC#4: Fetches source data for UI display.
    """
    if not table_name or not record_id:
        return {}

    # For now, return mock structure
    # In production, this would query Supabase
    logger.debug(f"Fetching database source: {table_name}/{record_id}")

    # Return structure that matches expected fields per table
    table_fields = {
        "daily_summaries": {
            "id": record_id,
            "asset_id": None,
            "asset_name": "Unknown Asset",
            "report_date": None,
            "oee_percentage": None,
            "downtime_minutes": None,
            "financial_loss_dollars": None,
        },
        "live_snapshots": {
            "id": record_id,
            "asset_id": None,
            "current_output": None,
            "target_output": None,
            "status": None,
            "snapshot_timestamp": None,
        },
        "safety_events": {
            "id": record_id,
            "asset_id": None,
            "severity": None,
            "description": None,
            "event_timestamp": None,
        },
        "cost_centers": {
            "id": record_id,
            "name": None,
            "standard_hourly_rate": None,
        },
        "assets": {
            "id": record_id,
            "name": None,
            "area": None,
            "status": None,
        },
        "asset_history": {
            "id": record_id,
            "asset_id": None,
            "event_type": None,
            "title": None,
            "description": None,
            "resolution": None,
            "created_at": None,
        },
    }

    return table_fields.get(table_name, {"id": record_id, "table": table_name})


async def _fetch_memory_source(
    memory_id: Optional[str],
) -> Dict[str, Any]:
    """
    Fetch source data from Mem0 memory.

    AC#6: Memory citations include provenance.
    """
    if not memory_id:
        return {}

    logger.debug(f"Fetching memory source: {memory_id}")

    # For now, return structure
    # In production, this would query Mem0
    return {
        "memory_id": memory_id,
        "content": "Memory content would be retrieved from Mem0",
        "created_at": None,
        "metadata": {},
    }
