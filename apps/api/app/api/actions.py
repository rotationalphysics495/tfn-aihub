"""
Action List API Endpoints

REST API for accessing the prioritized Daily Action List.

Story: 3.1 - Action Engine Logic
AC: #8 - API Endpoint for Action List
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.schemas.action import (
    AcknowledgmentCreate,
    AcknowledgmentResponse,
    ActionCategory,
    ActionEngineConfig,
    ActionListResponse,
)
from app.services.action_engine import get_action_engine, ActionEngine

logger = logging.getLogger(__name__)

router = APIRouter()


def get_engine() -> ActionEngine:
    """Dependency to get the Action Engine instance."""
    return get_action_engine()


def _build_config_override(
    engine: ActionEngine,
    target_oee: Optional[float] = None,
    financial_threshold: Optional[float] = None,
) -> Optional[ActionEngineConfig]:
    """
    Build a request-scoped config override if any overrides are specified.

    Thread-safe: creates a new config instance rather than mutating singleton.
    """
    if target_oee is None and financial_threshold is None:
        return None

    base_config = engine._get_config()
    return ActionEngineConfig(
        target_oee_percentage=target_oee if target_oee is not None else base_config.target_oee_percentage,
        financial_loss_threshold=financial_threshold if financial_threshold is not None else base_config.financial_loss_threshold,
        oee_high_gap_threshold=base_config.oee_high_gap_threshold,
        oee_medium_gap_threshold=base_config.oee_medium_gap_threshold,
        financial_high_threshold=base_config.financial_high_threshold,
        financial_medium_threshold=base_config.financial_medium_threshold,
    )


@router.get("/daily", response_model=ActionListResponse)
async def get_daily_action_list(
    report_date: Optional[date] = Query(
        None,
        alias="date",
        description="Report date (defaults to T-1/yesterday)"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of action items to return"
    ),
    category_filter: Optional[ActionCategory] = Query(
        None,
        alias="category",
        description="Filter by category (safety, oee, financial)"
    ),
    target_oee: Optional[float] = Query(
        None,
        ge=0,
        le=100,
        description="Override target OEE percentage"
    ),
    financial_threshold: Optional[float] = Query(
        None,
        ge=0,
        description="Override financial loss threshold (USD)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    engine: ActionEngine = Depends(get_engine),
):
    """
    Get the prioritized daily action list.

    Returns action items sorted by priority:
    1. Safety events (critical) - always first
    2. OEE below target - sorted by gap magnitude
    3. Financial loss above threshold - sorted by loss amount

    Query Parameters:
    - date: Report date in YYYY-MM-DD format (defaults to yesterday)
    - limit: Maximum items to return (1-100)
    - category: Filter to single category (safety/oee/financial)
    - target_oee: Override target OEE percentage
    - financial_threshold: Override financial loss threshold

    Requires authentication.
    """
    try:
        # Build request-scoped config override (thread-safe, AC #6)
        config_override = _build_config_override(engine, target_oee, financial_threshold)

        # Generate action list (Story 13.1: pass user_id for acknowledgment enrichment)
        response = await engine.generate_action_list(
            target_date=report_date,
            limit=limit,
            category_filter=category_filter,
            use_cache=config_override is None,  # Skip cache when using overrides
            config_override=config_override,
            user_id=current_user.id,
        )

        logger.info(
            f"Action list requested by {current_user.id}: "
            f"{response.total_count} items for {response.report_date}"
        )

        return response

    except Exception as e:
        logger.error(f"Failed to get action list: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate action list. Please try again."
        )


@router.get("/safety", response_model=ActionListResponse)
async def get_safety_actions(
    report_date: Optional[date] = Query(
        None,
        alias="date",
        description="Report date (defaults to T-1/yesterday)"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of action items to return"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    engine: ActionEngine = Depends(get_engine),
):
    """
    Get safety-related actions only.

    Returns only safety event action items, all marked as critical priority.
    Sorted by severity then timestamp.

    Requires authentication.
    """
    return await engine.generate_action_list(
        target_date=report_date,
        limit=limit,
        category_filter=ActionCategory.SAFETY,
        use_cache=True,
    )


@router.get("/oee", response_model=ActionListResponse)
async def get_oee_actions(
    report_date: Optional[date] = Query(
        None,
        alias="date",
        description="Report date (defaults to T-1/yesterday)"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of action items to return"
    ),
    target_oee: Optional[float] = Query(
        None,
        ge=0,
        le=100,
        description="Override target OEE percentage"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    engine: ActionEngine = Depends(get_engine),
):
    """
    Get OEE-related actions only.

    Returns only OEE below target action items, sorted by gap magnitude.

    Requires authentication.
    """
    config_override = _build_config_override(engine, target_oee=target_oee)

    return await engine.generate_action_list(
        target_date=report_date,
        limit=limit,
        category_filter=ActionCategory.OEE,
        use_cache=config_override is None,
        config_override=config_override,
    )


@router.get("/financial", response_model=ActionListResponse)
async def get_financial_actions(
    report_date: Optional[date] = Query(
        None,
        alias="date",
        description="Report date (defaults to T-1/yesterday)"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of action items to return"
    ),
    financial_threshold: Optional[float] = Query(
        None,
        ge=0,
        description="Override financial loss threshold (USD)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    engine: ActionEngine = Depends(get_engine),
):
    """
    Get financial-related actions only.

    Returns only financial loss action items, sorted by loss amount.

    Requires authentication.
    """
    config_override = _build_config_override(engine, financial_threshold=financial_threshold)

    return await engine.generate_action_list(
        target_date=report_date,
        limit=limit,
        category_filter=ActionCategory.FINANCIAL,
        use_cache=config_override is None,
        config_override=config_override,
    )


@router.post("/{action_id}/acknowledge", response_model=AcknowledgmentResponse)
async def acknowledge_action(
    action_id: str = Path(
        ...,
        pattern=r"^action-(safety|oee|financial)-[a-z0-9]+$",
        description="Action item ID (format: action-{category}-{hex12})"
    ),
    body: AcknowledgmentCreate = AcknowledgmentCreate(),
    report_date: Optional[date] = Query(
        None,
        alias="date",
        description="Report date (defaults to T-1/yesterday)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    engine: ActionEngine = Depends(get_engine),
):
    """
    Acknowledge an action item.

    Story 13.1 AC#1: Creates or updates an acknowledgment record.
    AC#2: Upsert behavior - returns 201 for new, 200 for updated.
    AC#4: Requires authentication.

    Args:
        action_id: The action item ID to acknowledge
        body: Optional note
        report_date: Report date (defaults to yesterday)
    """
    if report_date is None:
        report_date = date.today() - timedelta(days=1)

    try:
        client = engine._get_client()

        # Check if acknowledgment already exists (for 201 vs 200 differentiation)
        # Note: minor TOCTOU race between SELECT and UPSERT is acceptable —
        # worst case is a 201 returned instead of 200 on concurrent requests.
        # Data integrity is guaranteed by the upsert + unique constraint.
        existing = (
            client.table("action_acknowledgments")
            .select("id")
            .eq("action_item_id", action_id)
            .eq("user_id", current_user.id)
            .eq("report_date", report_date.isoformat())
            .execute()
        )
        is_new = not existing.data

        # Upsert the acknowledgment (AC#2)
        upsert_data = {
            "action_item_id": action_id,
            "user_id": current_user.id,
            "report_date": report_date.isoformat(),
            "acknowledged_at": datetime.utcnow().isoformat(),
        }
        if body.note is not None:
            upsert_data["note"] = body.note

        result = (
            client.table("action_acknowledgments")
            .upsert(upsert_data, on_conflict="action_item_id,user_id,report_date")
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create acknowledgment")

        record = result.data[0]
        response_data = AcknowledgmentResponse(
            id=record["id"],
            action_item_id=record["action_item_id"],
            user_id=record["user_id"],
            acknowledged_at=record["acknowledged_at"],
            note=record.get("note"),
            report_date=record["report_date"],
        )

        status_code = 201 if is_new else 200
        logger.info(
            f"Action {action_id} acknowledged by {current_user.id} "
            f"({'created' if is_new else 'updated'}) for {report_date}"
        )
        return JSONResponse(
            status_code=status_code,
            content=response_data.model_dump(mode="json"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge action {action_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to acknowledge action item. Please try again."
        )


@router.post("/invalidate-cache")
async def invalidate_action_cache(
    report_date: Optional[date] = Query(
        None,
        alias="date",
        description="Specific date to invalidate (or all if not specified)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    engine: ActionEngine = Depends(get_engine),
):
    """
    Invalidate the action list cache.

    Used by Pipeline A completion hook to trigger cache refresh
    after new data ingestion.

    Requires authentication.
    """
    engine.invalidate_cache(report_date)

    return {
        "success": True,
        "message": f"Cache invalidated for {'all dates' if report_date is None else report_date.isoformat()}"
    }
