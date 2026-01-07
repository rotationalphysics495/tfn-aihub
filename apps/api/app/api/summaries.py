"""
Summaries API Endpoints

Provides endpoints for daily summaries and AI-generated smart summaries.

Story: 3.5 - Smart Summary Generator
AC: #7 - API Endpoint for Summary Retrieval
"""

import logging
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.schemas.summary import (
    GenerateSummaryRequest,
    LLMHealthResponse,
    SmartSummaryResponse,
    TokenUsageSummary,
)
from app.services.ai.smart_summary import (
    SmartSummaryService,
    SmartSummaryError,
    get_smart_summary_service,
)
from app.services.ai.llm_client import check_llm_health

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Existing Daily Summary Endpoints
# =============================================================================

class DailySummary(BaseModel):
    id: UUID
    asset_id: UUID
    date: date
    oee: float
    waste: float
    financial_loss: float
    smart_summary: Optional[str] = None


@router.get("/daily", response_model=List[DailySummary])
async def list_daily_summaries(
    asset_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List daily summaries, optionally filtered by asset. Requires authentication."""
    return []


@router.get("/daily/{summary_date}", response_model=List[DailySummary])
async def get_daily_summary(
    summary_date: date, current_user: CurrentUser = Depends(get_current_user)
):
    """Get daily summaries for a specific date. Requires authentication."""
    return []


# =============================================================================
# Smart Summary Endpoints (Story 3.5)
# =============================================================================

@router.get(
    "/smart/{summary_date}",
    response_model=SmartSummaryResponse,
    summary="Get Smart Summary",
    description="""
    Get AI-generated smart summary for a specific date.

    AC#7: Returns cached summary if available, 404 if no summary exists.
    Supports ?regenerate=true to force new generation.
    """,
)
async def get_smart_summary(
    summary_date: date,
    regenerate: bool = Query(
        False,
        description="Force regeneration even if cached"
    ),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get the AI-generated smart summary for a specific date.

    Story 3.5 AC#7:
    - Returns cached summary if available
    - Returns 404 if no summary exists for that date
    - Supports ?regenerate=true to force new generation
    - Protected with Supabase JWT authentication
    """
    service = get_smart_summary_service()

    try:
        if regenerate:
            # Force regeneration
            logger.info(f"Regenerating smart summary for {summary_date}")
            summary = await service.generate_smart_summary(
                target_date=summary_date,
                regenerate=True,
            )
        else:
            # Try to get cached summary first
            summary = await service.get_cached_summary(summary_date)

            if summary is None:
                # AC#7: Returns 404 if no summary exists
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No smart summary found for {summary_date}. "
                           f"Use POST /api/summaries/generate to create one."
                )

        return SmartSummaryResponse(
            id=summary.id,
            date=summary.date,
            summary_text=summary.summary_text,
            citations=summary.citations_json,
            model_used=summary.model_used,
            prompt_tokens=summary.prompt_tokens,
            completion_tokens=summary.completion_tokens,
            generation_duration_ms=summary.generation_duration_ms,
            is_fallback=summary.is_fallback,
            created_at=summary.created_at,
        )

    except HTTPException:
        raise
    except SmartSummaryError as e:
        logger.error(f"Smart summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve smart summary: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting smart summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/generate",
    response_model=SmartSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Smart Summary",
    description="""
    Manually trigger smart summary generation.

    AC#7: POST endpoint for manual generation trigger.
    """,
)
async def generate_smart_summary(
    request: GenerateSummaryRequest = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Manually trigger generation of a smart summary.

    Story 3.5 AC#7:
    - POST /api/summaries/generate for manual trigger
    - Defaults to T-1 if no date specified
    - Protected with Supabase JWT authentication
    """
    service = get_smart_summary_service()

    # Default to T-1 if no date specified
    target_date = (
        request.target_date if request and request.target_date
        else date.today() - timedelta(days=1)
    )
    regenerate = request.regenerate if request else False

    try:
        logger.info(f"Generating smart summary for {target_date}")

        summary = await service.generate_smart_summary(
            target_date=target_date,
            regenerate=regenerate,
        )

        return SmartSummaryResponse(
            id=summary.id,
            date=summary.date,
            summary_text=summary.summary_text,
            citations=summary.citations_json,
            model_used=summary.model_used,
            prompt_tokens=summary.prompt_tokens,
            completion_tokens=summary.completion_tokens,
            generation_duration_ms=summary.generation_duration_ms,
            is_fallback=summary.is_fallback,
            created_at=summary.created_at,
        )

    except SmartSummaryError as e:
        logger.error(f"Smart summary generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate smart summary: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error generating smart summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during generation"
        )


@router.delete(
    "/smart/{summary_date}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate Smart Summary Cache",
    description="Invalidate cached summary for a date (triggers regeneration on next request).",
)
async def invalidate_smart_summary(
    summary_date: date,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Invalidate cached smart summary for a date.

    Story 3.5 AC#6: Cache invalidation when source data is updated.
    """
    service = get_smart_summary_service()

    try:
        await service.invalidate_cache(summary_date)
        logger.info(f"Invalidated smart summary cache for {summary_date}")
        return None

    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache"
        )


@router.get(
    "/usage",
    response_model=TokenUsageSummary,
    summary="Get Token Usage Summary",
    description="Get aggregated LLM token usage for cost management.",
)
async def get_token_usage(
    start_date: Optional[date] = Query(None, description="Start of period"),
    end_date: Optional[date] = Query(None, description="End of period"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get aggregated token usage summary.

    Story 3.5 AC#10: Daily/monthly token usage tracked for cost management.
    """
    service = get_smart_summary_service()

    try:
        usage = await service.get_token_usage_summary(
            start_date=start_date,
            end_date=end_date,
        )

        return TokenUsageSummary(**usage)

    except Exception as e:
        logger.error(f"Failed to get token usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token usage"
        )


@router.get(
    "/health/llm",
    response_model=LLMHealthResponse,
    summary="LLM Health Check",
    description="Check LLM service connectivity and configuration.",
)
async def llm_health_check():
    """
    Check LLM service health.

    Story 3.5 AC#1: Connection validated on startup with health check.
    Note: This endpoint is public for monitoring purposes.
    """
    try:
        result = await check_llm_health()
        return LLMHealthResponse(**result)

    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return LLMHealthResponse(
            status="error",
            provider="unknown",
            message=f"Health check failed: {str(e)}",
            healthy=False,
        )
