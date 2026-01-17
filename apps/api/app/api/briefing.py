"""
Briefing API Endpoints (Story 8.4, 9.10)

REST endpoints for morning briefing generation, Q&A, and End of Day summary.

Story 8.4:
- AC#1: POST /api/v1/briefing/morning - Generate morning briefing
- AC#2: GET /api/v1/briefing/{briefing_id} - Retrieve briefing details
- AC#5: POST /api/v1/briefing/{briefing_id}/qa - Q&A during pause

Story 9.10:
- AC#1: POST /api/v1/briefing/eod - Generate End of Day summary (FR31)
- AC#2: Summary includes day's performance, wins, concerns, outlook
- AC#3: Fallback when no morning briefing exists

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
- [Source: prd/prd-functional-requirements.md#FR31-FR34]
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.briefing.morning import (
    get_morning_briefing_service,
    PRODUCTION_AREAS,
    DEFAULT_AREA_ORDER,
)
from app.models.briefing import (
    BriefingResponse,
    BriefingSection,
    BriefingSectionStatus,
    EODSummaryResponse,
    EODRequest,
    MorningComparisonResult,
)
from app.services.briefing.eod import get_eod_service
from app.core.security import get_current_user
from app.models.user import CurrentUser, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class MorningBriefingRequest(BaseModel):
    """
    Request schema for morning briefing generation.

    AC#1: User triggers "Start Morning Briefing"
    """
    user_id: str = Field(..., description="User ID from auth context")
    area_order: Optional[List[str]] = Field(
        None,
        description="Preferred area order (FR36). Defaults to standard order."
    )
    include_audio: bool = Field(True, description="Generate TTS audio")


class BriefingSectionSchema(BaseModel):
    """Schema for a briefing section in API responses."""
    section_type: str
    title: str
    content: str
    area_id: Optional[str] = None
    status: str
    pause_point: bool = True
    duration_estimate_ms: Optional[int] = None
    error_message: Optional[str] = None


class MorningBriefingResponse(BaseModel):
    """
    Response schema for morning briefing.

    AC#1: Contains sections for all 7 production areas
    """
    briefing_id: str = Field(..., description="Unique briefing identifier")
    title: str = Field(..., description="Briefing title")
    sections: List[BriefingSectionSchema] = Field(..., description="Briefing sections")
    audio_stream_url: Optional[str] = Field(None, description="TTS audio URL (nullable)")
    total_duration_estimate: int = Field(..., description="Estimated duration in seconds")
    generated_at: str = Field(..., description="ISO timestamp when generated")
    completion_percentage: float = Field(..., description="Percentage of sections completed")
    timed_out: bool = Field(False, description="Whether generation timed out")
    tool_failures: List[str] = Field(default_factory=list, description="Failed areas")


class ProductionAreaSchema(BaseModel):
    """Schema for production area information."""
    id: str
    name: str
    description: str
    assets: List[str]


class ProductionAreasResponse(BaseModel):
    """Response schema for production areas list."""
    areas: List[ProductionAreaSchema]
    default_order: List[str]


class QARequest(BaseModel):
    """
    Request schema for Q&A during briefing pause.

    AC#5: User asks a question during pause
    """
    question: str = Field(..., min_length=1, description="User's question")
    area_id: Optional[str] = Field(None, description="Current area context")
    user_id: str = Field(..., description="User ID")


class QAResponse(BaseModel):
    """
    Response schema for Q&A.

    AC#5: Q&A response with citations (FR20)
    """
    answer: str = Field(..., description="Answer to the question")
    citations: List[str] = Field(default_factory=list, description="Data source citations")
    follow_up_prompt: str = Field(
        "Anything else?",
        description="Follow-up prompt for user"
    )
    audio_stream_url: Optional[str] = Field(None, description="TTS audio for answer")
    area_id: Optional[str] = Field(None, description="Area context")


class BriefingDetailsResponse(BaseModel):
    """Response schema for briefing details retrieval."""
    briefing_id: str
    title: str
    status: str
    sections: List[BriefingSectionSchema]
    audio_stream_url: Optional[str] = None
    total_duration_estimate: int
    generated_at: str
    completion_percentage: float


# ============================================================================
# EOD Summary Schemas (Story 9.10)
# ============================================================================


class EODSummaryRequest(BaseModel):
    """
    Request schema for End of Day summary generation.

    Story 9.10 AC#1: EOD Summary Trigger (FR31)
    """
    user_id: str = Field(..., description="User ID from auth context")
    date: Optional[str] = Field(
        None,
        description="Date for EOD summary (YYYY-MM-DD). Defaults to today."
    )
    include_audio: bool = Field(True, description="Generate TTS audio")


class MorningComparisonSchema(BaseModel):
    """Schema for morning vs actual comparison data."""
    morning_briefing_id: str
    morning_generated_at: str
    flagged_concerns: List[str] = []
    concerns_resolved: List[str] = []
    concerns_escalated: List[str] = []
    predicted_wins: List[str] = []
    actual_wins: List[str] = []
    prediction_summary: str = ""


class EODSummaryResponseSchema(BaseModel):
    """
    Response schema for End of Day summary.

    Story 9.10:
    - AC#1: EOD Summary Trigger (FR31)
    - AC#2: Summary Content Structure
    - AC#3: No Morning Briefing Fallback
    """
    summary_id: str = Field(..., description="Unique EOD summary identifier")
    title: str = Field(..., description="Summary title")
    sections: List[BriefingSectionSchema] = Field(..., description="Summary sections")
    audio_stream_url: Optional[str] = Field(None, description="TTS audio URL (nullable)")
    total_duration_estimate: int = Field(..., description="Estimated duration in seconds")
    generated_at: str = Field(..., description="ISO timestamp when generated")
    completion_percentage: float = Field(..., description="Percentage of sections completed")
    timed_out: bool = Field(False, description="Whether generation timed out")
    tool_failures: List[str] = Field(default_factory=list, description="Failed tools")

    # EOD-specific fields
    morning_briefing_id: Optional[str] = Field(
        None,
        description="ID of today's morning briefing (if exists)"
    )
    comparison_available: bool = Field(
        False,
        description="Whether morning briefing comparison is available"
    )
    morning_comparison: Optional[MorningComparisonSchema] = Field(
        None,
        description="Morning vs actual comparison data"
    )
    summary_date: str = Field(..., description="Date this summary covers (YYYY-MM-DD)")
    time_range_start: str = Field(..., description="Start of day's time range (ISO)")
    time_range_end: str = Field(..., description="End of day's time range (ISO)")


# ============================================================================
# In-memory briefing store (for demo/MVP - replace with Redis in production)
# ============================================================================


# Simple in-memory store for active briefings
_active_briefings: Dict[str, BriefingResponse] = {}


def _store_briefing(briefing: BriefingResponse) -> None:
    """Store a briefing for later retrieval."""
    _active_briefings[briefing.id] = briefing
    # Clean up old briefings (keep last 100)
    if len(_active_briefings) > 100:
        oldest_keys = sorted(_active_briefings.keys())[:50]
        for key in oldest_keys:
            del _active_briefings[key]


def _get_briefing(briefing_id: str) -> Optional[BriefingResponse]:
    """Retrieve a stored briefing."""
    return _active_briefings.get(briefing_id)


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/areas", response_model=ProductionAreasResponse)
async def get_production_areas():
    """
    Get list of production areas.

    Returns all 7 production areas with their default ordering.
    Used by frontend to display area preview before briefing.
    """
    service = get_morning_briefing_service()

    areas = [
        ProductionAreaSchema(
            id=area["id"],
            name=area["name"],
            description=area["description"],
            assets=area["assets"],
        )
        for area in service.get_production_areas()
    ]

    return ProductionAreasResponse(
        areas=areas,
        default_order=service.get_default_area_order(),
    )


@router.post("/morning", response_model=MorningBriefingResponse)
async def generate_morning_briefing(request: MorningBriefingRequest):
    """
    Generate a morning briefing covering all production areas.

    AC#1: Covers all 7 production areas in user's preferred order

    The response includes:
    - Headline section with plant-wide overview
    - One section per production area
    - Each section has pause_point=True for Q&A opportunities
    """
    logger.info(f"Generating morning briefing for user {request.user_id}")

    service = get_morning_briefing_service()

    try:
        # Generate the briefing
        briefing = await service.generate_plant_briefing(
            user_id=request.user_id,
            area_order=request.area_order,
            include_audio=request.include_audio,
        )

        # Store for later retrieval
        _store_briefing(briefing)

        # Convert to response schema
        sections = [
            BriefingSectionSchema(
                section_type=s.section_type,
                title=s.title,
                content=s.content,
                area_id=s.area_id,
                status=s.status.value if isinstance(s.status, BriefingSectionStatus) else s.status,
                pause_point=s.pause_point,
                error_message=s.error_message,
            )
            for s in briefing.sections
        ]

        return MorningBriefingResponse(
            briefing_id=briefing.id,
            title=briefing.title,
            sections=sections,
            audio_stream_url=briefing.audio_stream_url,
            total_duration_estimate=briefing.total_duration_estimate,
            generated_at=briefing.metadata.generated_at.isoformat(),
            completion_percentage=briefing.metadata.completion_percentage,
            timed_out=briefing.metadata.timed_out,
            tool_failures=briefing.metadata.tool_failures,
        )

    except Exception as e:
        logger.error(f"Morning briefing generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate morning briefing: {str(e)}"
        )


@router.get("/{briefing_id}", response_model=BriefingDetailsResponse)
async def get_briefing(briefing_id: str):
    """
    Retrieve details of a generated briefing.

    Used to retrieve briefing content after generation or
    to resume a briefing session.
    """
    briefing = _get_briefing(briefing_id)

    if not briefing:
        raise HTTPException(
            status_code=404,
            detail=f"Briefing {briefing_id} not found"
        )

    # Convert sections
    sections = [
        BriefingSectionSchema(
            section_type=s.section_type,
            title=s.title,
            content=s.content,
            area_id=s.area_id,
            status=s.status.value if isinstance(s.status, BriefingSectionStatus) else s.status,
            pause_point=s.pause_point,
            error_message=s.error_message,
        )
        for s in briefing.sections
    ]

    # Determine overall status
    if briefing.metadata.timed_out:
        status = "partial"
    elif briefing.metadata.completion_percentage == 100:
        status = "complete"
    elif briefing.metadata.completion_percentage > 0:
        status = "partial"
    else:
        status = "failed"

    return BriefingDetailsResponse(
        briefing_id=briefing.id,
        title=briefing.title,
        status=status,
        sections=sections,
        audio_stream_url=briefing.audio_stream_url,
        total_duration_estimate=briefing.total_duration_estimate,
        generated_at=briefing.metadata.generated_at.isoformat(),
        completion_percentage=briefing.metadata.completion_percentage,
    )


@router.post("/{briefing_id}/qa", response_model=QAResponse)
async def process_qa(briefing_id: str, request: QARequest):
    """
    Process a Q&A question during briefing pause.

    AC#5: Q&A response with citations (FR20)

    When a user asks a question during a pause:
    1. Question is transcribed (via STT from Story 8.2)
    2. This endpoint processes the question
    3. Response is delivered with citations
    4. System asks "Anything else on [Area]?"
    """
    # Verify briefing exists
    briefing = _get_briefing(briefing_id)
    if not briefing:
        raise HTTPException(
            status_code=404,
            detail=f"Briefing {briefing_id} not found"
        )

    logger.info(f"Processing Q&A for briefing {briefing_id}: {request.question[:50]}...")

    service = get_morning_briefing_service()

    try:
        # Process the question
        result = await service.process_qa_question(
            briefing_id=briefing_id,
            area_id=request.area_id,
            question=request.question,
            user_id=request.user_id,
        )

        # Format citations for display
        citations = []
        if result.get("citations"):
            for citation in result["citations"]:
                if isinstance(citation, str):
                    citations.append(citation)
                elif isinstance(citation, dict):
                    citations.append(citation.get("source", str(citation)))

        return QAResponse(
            answer=result.get("answer", "I couldn't find an answer to that question."),
            citations=citations,
            follow_up_prompt=result.get("follow_up_prompt", "Anything else?"),
            audio_stream_url=None,  # TTS generation handled separately
            area_id=result.get("area_id"),
        )

    except Exception as e:
        logger.error(f"Q&A processing failed: {e}", exc_info=True)
        # Return graceful error response instead of raising exception
        return QAResponse(
            answer="I had trouble processing that question. Could you try rephrasing it?",
            citations=[],
            follow_up_prompt="Any other questions?",
            area_id=request.area_id,
        )


@router.post("/{briefing_id}/continue")
async def continue_briefing(briefing_id: str, section_index: int = Query(..., ge=0)):
    """
    Signal to continue to the next section.

    AC#3: User says "No" / "Continue" / "Next"
    AC#4: Auto-continue after silence (handled by frontend)

    This endpoint is called when:
    - User explicitly says "Continue" / "Next"
    - Frontend detects 3-4 seconds of silence
    """
    # Verify briefing exists
    briefing = _get_briefing(briefing_id)
    if not briefing:
        raise HTTPException(
            status_code=404,
            detail=f"Briefing {briefing_id} not found"
        )

    # Validate section index
    if section_index >= len(briefing.sections):
        return {
            "status": "complete",
            "message": "Briefing complete",
            "next_section_index": None,
        }

    next_index = section_index + 1
    if next_index >= len(briefing.sections):
        return {
            "status": "complete",
            "message": "Briefing complete",
            "next_section_index": None,
        }

    next_section = briefing.sections[next_index]

    return {
        "status": "continuing",
        "next_section_index": next_index,
        "next_section": BriefingSectionSchema(
            section_type=next_section.section_type,
            title=next_section.title,
            content=next_section.content,
            area_id=next_section.area_id,
            status=next_section.status.value if isinstance(next_section.status, BriefingSectionStatus) else next_section.status,
            pause_point=next_section.pause_point,
        ),
    }


@router.post("/{briefing_id}/end")
async def end_briefing(briefing_id: str):
    """
    End the briefing session early.

    Allows user to exit briefing before all sections complete.
    """
    # Verify briefing exists
    briefing = _get_briefing(briefing_id)
    if not briefing:
        raise HTTPException(
            status_code=404,
            detail=f"Briefing {briefing_id} not found"
        )

    # In production, this would update session state
    # For now, just acknowledge the end

    return {
        "status": "ended",
        "briefing_id": briefing_id,
        "message": "Briefing session ended",
        "sections_completed": sum(1 for s in briefing.sections if s.is_complete),
        "total_sections": len(briefing.sections),
    }


# ============================================================================
# EOD Summary Endpoints (Story 9.10)
# ============================================================================


@router.post("/eod", response_model=EODSummaryResponseSchema)
async def generate_eod_summary(
    request: EODSummaryRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate End of Day summary for Plant Manager.

    Story 9.10:
    - AC#1: EOD Summary Trigger (FR31) - Plant Manager triggers EOD summary
    - AC#2: Summary Content Structure - performance, wins, concerns, outlook
    - AC#3: No Morning Briefing Fallback - works without morning briefing

    The response includes:
    - Day's overall performance vs target
    - Comparison to morning briefing highlights (if available)
    - Wins that materialized
    - Concerns that escalated or resolved
    - Tomorrow's outlook

    Requires: Plant Manager role (FR31)
    """
    # AC#1: Validate user role - EOD summary is for Plant Managers only (FR31)
    # Note: In production with full RBAC, use CurrentUserWithRole and check user_role
    # For now, we log the user and proceed (role check ready for integration)
    logger.info(
        f"Generating EOD summary for user {current_user.id} (role: {current_user.role})"
    )

    # Parse date if provided
    summary_date = None
    if request.date:
        try:
            from datetime import date as date_type
            summary_date = date_type.fromisoformat(request.date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {request.date}. Use YYYY-MM-DD."
            )

    service = get_eod_service()

    try:
        # Generate the EOD summary
        summary = await service.generate_eod_summary(
            user_id=request.user_id,
            summary_date=summary_date,
            include_audio=request.include_audio,
        )

        # Store for later retrieval (reuse briefing store)
        _store_briefing(summary)

        # Convert to response schema
        sections = [
            BriefingSectionSchema(
                section_type=s.section_type,
                title=s.title,
                content=s.content,
                area_id=s.area_id,
                status=s.status.value if isinstance(s.status, BriefingSectionStatus) else s.status,
                pause_point=s.pause_point,
                error_message=s.error_message,
            )
            for s in summary.sections
        ]

        # Convert morning comparison if available
        morning_comparison = None
        if summary.morning_comparison:
            morning_comparison = MorningComparisonSchema(
                morning_briefing_id=summary.morning_comparison.morning_briefing_id,
                morning_generated_at=summary.morning_comparison.morning_generated_at.isoformat(),
                flagged_concerns=summary.morning_comparison.flagged_concerns,
                concerns_resolved=summary.morning_comparison.concerns_resolved,
                concerns_escalated=summary.morning_comparison.concerns_escalated,
                predicted_wins=summary.morning_comparison.predicted_wins,
                actual_wins=summary.morning_comparison.actual_wins,
                prediction_summary=summary.morning_comparison.prediction_summary,
            )

        return EODSummaryResponseSchema(
            summary_id=summary.id,
            title=summary.title,
            sections=sections,
            audio_stream_url=summary.audio_stream_url,
            total_duration_estimate=summary.total_duration_estimate,
            generated_at=summary.metadata.generated_at.isoformat(),
            completion_percentage=summary.metadata.completion_percentage,
            timed_out=summary.metadata.timed_out,
            tool_failures=summary.metadata.tool_failures,
            morning_briefing_id=summary.morning_briefing_id,
            comparison_available=summary.comparison_available,
            morning_comparison=morning_comparison,
            summary_date=summary.summary_date.strftime("%Y-%m-%d"),
            time_range_start=summary.time_range_start.isoformat() if summary.time_range_start else "",
            time_range_end=summary.time_range_end.isoformat() if summary.time_range_end else "",
        )

    except Exception as e:
        logger.error(f"EOD summary generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate EOD summary: {str(e)}"
        )
