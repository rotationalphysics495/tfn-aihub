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
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client

from app.core.config import get_settings
from app.core.security import get_current_user, security
from app.models.user import CurrentUser
from app.schemas.action import (
    AcknowledgmentCreate,
    AcknowledgmentResponse,
    ActionCategory,
    ActionEngineConfig,
    ActionListResponse,
    FollowUpListItem,
    FollowUpListResponse,
    FollowUpUpdateRequest,
    FollowUpResponse,
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


@router.get("/followups", response_model=FollowUpListResponse)
async def list_followups(
    assigned_by: str = Query(
        "me",
        pattern=r"^(me|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$",
        description="Filter by assigner: 'me' (current user) or explicit UUID"
    ),
    status: str = Query(
        "all",
        pattern=r"^(assigned|in_progress|resolved|active|all)$",
        description="Status filter: assigned, in_progress, resolved, active (assigned+in_progress), or all"
    ),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum items to return"),
    offset: Optional[int] = Query(None, ge=0, description="Pagination offset"),
    current_user: CurrentUser = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    List follow-up assignments created by the current user.

    Story 13.5 AC#1: Returns follow-ups grouped by status for the
    "My Assignments" panel on the morning report.

    Requires authentication.
    """
    settings = get_settings()
    user_token = credentials.credentials

    try:
        client = create_client(settings.supabase_url, user_token)

        # Resolve assigned_by
        assigner_id = current_user.id if assigned_by == "me" else assigned_by

        # Build query
        query = (
            client.table("action_followups")
            .select("*")
            .eq("assigned_by", assigner_id)
        )

        # Apply status filter
        valid_statuses = {"assigned", "in_progress", "resolved"}
        if status == "active":
            query = query.in_("status", ["assigned", "in_progress"])
        elif status != "all" and status in valid_statuses:
            query = query.eq("status", status)

        # Get total count before pagination (for accurate total_count)
        is_paginated = limit is not None or offset is not None
        total_count = None
        if is_paginated:
            count_query = (
                client.table("action_followups")
                .select("id", count="exact")
                .eq("assigned_by", assigner_id)
            )
            if status == "active":
                count_query = count_query.in_("status", ["assigned", "in_progress"])
            elif status != "all" and status in valid_statuses:
                count_query = count_query.eq("status", status)
            count_result = count_query.execute()
            total_count = count_result.count if hasattr(count_result, 'count') and count_result.count is not None else len(count_result.data or [])

        # Apply pagination when explicitly requested
        if is_paginated:
            pg_offset = offset or 0
            pg_limit = limit or 50
            query = query.range(pg_offset, pg_offset + pg_limit - 1)

        result = query.execute()
        followups_data = result.data or []

        # Resolve assigned_to UUIDs to emails
        assigned_to_ids = list({f["assigned_to"] for f in followups_data})
        email_map: dict = {}
        if assigned_to_ids:
            try:
                users_result = client.rpc(
                    "get_user_emails", {"user_ids": assigned_to_ids}
                ).execute()
                if users_result.data:
                    for u in users_result.data:
                        email_map[u["id"]] = u["email"]
            except Exception:
                logger.warning("Failed to resolve user emails via RPC")

        # Build response items
        items = []
        for f in followups_data:
            # Use email from data if present, otherwise resolve from email_map
            if "assigned_to_email" not in f or f["assigned_to_email"] is None:
                f["assigned_to_email"] = email_map.get(f["assigned_to"])
            items.append(FollowUpListItem(**f))

        # Compute counts by status from returned items
        counts = {"assigned": 0, "in_progress": 0, "resolved": 0}
        for item in items:
            if item.status in counts:
                counts[item.status] += 1

        return FollowUpListResponse(
            followups=items,
            total_count=total_count if total_count is not None else len(items),
            counts_by_status=counts,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list follow-ups: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list follow-ups. Please try again.",
        )


@router.patch("/followups/{followup_id}", response_model=FollowUpResponse)
async def update_followup(
    followup_id: str = Path(
        ...,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        description="Follow-up UUID"
    ),
    update: FollowUpUpdateRequest = ...,
    current_user: CurrentUser = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Update a follow-up assignment status and/or note.

    Story 13.3 AC#1: Assignee can update follow-up status (partial update).
    AC#2: RLS denies unauthorized updates (user-scoped Supabase client).
    AC#3: Response includes current status and note for manager visibility.
    """
    # Validate at least one field is provided
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=422,
            detail="At least one field (status or note) must be provided",
        )

    settings = get_settings()
    user_token = credentials.credentials

    try:
        # Service-role client: check existence (SELECT bypasses user RLS)
        service_client = create_client(settings.supabase_url, settings.supabase_key)
        existence_check = (
            service_client.table("action_followups")
            .select("*")
            .eq("id", followup_id)
            .execute()
        )

        if not existence_check.data:
            raise HTTPException(status_code=404, detail="Follow-up not found")

        # User-scoped client: UPDATE with RLS enforcement
        user_client = create_client(settings.supabase_url, user_token)
        result = (
            user_client.table("action_followups")
            .update(update_data)
            .eq("id", followup_id)
            .execute()
        )

        if not result.data:
            # RLS blocked the update — user is not authorized
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update this follow-up",
            )

        record = result.data[0]
        return FollowUpResponse(**record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update follow-up {followup_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update follow-up. Please try again.",
        )
