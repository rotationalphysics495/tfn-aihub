"""
Action Plans CRUD API Endpoints

REST API for managing action plans lifecycle.

Story: 16.2 - Action Plans CRUD API
AC#1: POST /api/v1/action-plans - Create action plan
AC#2: GET /api/v1/action-plans - List action plans with filters/sorting/pagination
AC#3: PATCH /api/v1/action-plans/{id} - Update action plan with change logging
AC#4: POST /api/v1/action-plans/{id}/updates - Add progress update
AC#5: POST /api/v1/action-plans/{id}/verify - Verify action plan completion
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials

from supabase import create_client

from app.core.config import get_settings
from app.core.security import get_current_user, security
from app.models.user import CurrentUser
from app.schemas.action_plan import (
    ActionPlanCreate,
    ActionPlanListResponse,
    ActionPlanResponse,
    ActionPlanStatus,
    ActionPlanPriority,
    ActionPlanUpdate,
    ActionPlanUpdateCreate,
    ActionPlanUpdateResponse,
    ActionPlanVerifyRequest,
    PRIORITY_SORT_MAP,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper functions
# =============================================================================


def _get_supabase_client():
    """Get a service-role Supabase client for database operations."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


def _get_user_client(token: str):
    """Get a user-scoped Supabase client for RLS enforcement."""
    settings = get_settings()
    return create_client(settings.supabase_url, token)


def _build_change_description(old_record: dict, update_data: dict) -> tuple[str, Optional[str]]:
    """
    Compare old record with update data and build a change description.

    Returns:
        Tuple of (update_text, status_change)
    """
    changes = []
    status_change = None

    for field, new_value in update_data.items():
        old_value = old_record.get(field)
        if str(old_value) != str(new_value):
            if field == "status":
                status_change = f"{old_value} -> {new_value}"
                changes.append(f"Status changed from {old_value} to {new_value}")
            elif field == "due_date":
                changes.append(f"Due date updated from {old_value} to {new_value}")
            else:
                display_field = field.replace("_", " ").capitalize()
                changes.append(f"{display_field} updated")

    update_text = ". ".join(changes) if changes else "Plan updated"
    return update_text, status_change


def _sort_plans(plans: list) -> list:
    """Sort plans by priority (critical first) then due_date ascending (nulls last)."""

    def sort_key(plan):
        priority_val = plan.get("priority")
        if priority_val:
            try:
                priority_rank = PRIORITY_SORT_MAP.get(
                    ActionPlanPriority(priority_val), 99
                )
            except ValueError:
                priority_rank = 99
        else:
            priority_rank = 99

        due_date = plan.get("due_date")
        # Nulls sort last
        due_date_key = due_date if due_date else "9999-99-99"

        return (priority_rank, due_date_key)

    return sorted(plans, key=sort_key)


# =============================================================================
# AC#1: POST / - Create action plan
# =============================================================================


@router.post("", response_model=ActionPlanResponse, status_code=201)
async def create_action_plan(
    plan: ActionPlanCreate,
    current_user: CurrentUser = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Create a new action plan (AC#1).

    The plan is created with status='open' and the current user as owner.
    Uses user-scoped Supabase client for RLS enforcement.
    """
    user_token = credentials.credentials

    try:
        # Build insert data
        insert_data = plan.model_dump(exclude_unset=True)
        insert_data["status"] = "open"
        insert_data["owner_id"] = current_user.id

        # Use user-scoped client for RLS enforcement
        user_client = _get_user_client(user_token)
        result = (
            user_client.table("action_plans")
            .insert(insert_data)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create action plan")

        return ActionPlanResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create action plan: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create action plan. Please try again.",
        )


# =============================================================================
# AC#2: GET / - List action plans with filters and sorting
# =============================================================================


@router.get("", response_model=ActionPlanListResponse)
async def list_action_plans(
    status: Optional[ActionPlanStatus] = Query(None, description="Filter by status"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    priority: Optional[ActionPlanPriority] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List action plans with optional filters, sorted by priority then due_date (AC#2).

    Uses service-role client since all authenticated users can read all plans.
    Python-side sorting with PRIORITY_SORT_MAP for priority ranking.
    """
    try:
        service_client = _get_supabase_client()
        query = service_client.table("action_plans").select("*")

        # Apply filters
        if status:
            query = query.eq("status", status.value)
        if asset_id:
            query = query.eq("asset_id", asset_id)
        if owner_id:
            query = query.eq("owner_id", owner_id)
        if priority:
            query = query.eq("priority", priority.value)

        result = query.execute()
        all_plans = result.data or []

        # Python-side sorting by priority then due_date
        sorted_plans = _sort_plans(all_plans)

        # Calculate pagination
        total_count = len(sorted_plans)
        offset = (page - 1) * page_size
        paginated_plans = sorted_plans[offset:offset + page_size]

        return ActionPlanListResponse(
            items=[ActionPlanResponse(**p) for p in paginated_plans],
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list action plans: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list action plans. Please try again.",
        )


# =============================================================================
# GET /{plan_id} - Get single action plan
# =============================================================================


@router.get("/{plan_id}", response_model=ActionPlanResponse)
async def get_action_plan(
    plan_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a single action plan by ID."""
    try:
        service_client = _get_supabase_client()
        result = (
            service_client.table("action_plans")
            .select("*")
            .eq("id", plan_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Action plan not found")

        return ActionPlanResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get action plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get action plan. Please try again.",
        )


# =============================================================================
# AC#3: PATCH /{plan_id} - Update action plan with change logging
# =============================================================================


@router.patch("/{plan_id}", response_model=ActionPlanResponse)
async def update_action_plan(
    plan_id: str,
    update: ActionPlanUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update an action plan with change logging (AC#3).

    Uses service-role client so any authenticated team member can update any plan
    (e.g. status transitions by non-owners). Change is logged with the acting user's ID.
    Auto-generates an action_plan_updates record describing the changes.
    """
    # Validate at least one field is provided
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided for update",
        )

    try:
        service_client = _get_supabase_client()

        # Check existence
        existence_check = (
            service_client.table("action_plans")
            .select("*")
            .eq("id", plan_id)
            .execute()
        )

        if not existence_check.data:
            raise HTTPException(status_code=404, detail="Action plan not found")

        old_record = existence_check.data[0]

        # Service-role UPDATE — any authenticated user can update
        result = (
            service_client.table("action_plans")
            .update(update_data)
            .eq("id", plan_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update action plan")

        updated_record = result.data[0]

        # Auto-generate change log entry
        update_text, status_change = _build_change_description(old_record, update_data)

        change_log_data = {
            "action_plan_id": plan_id,
            "author_id": current_user.id,
            "update_text": update_text,
            "status_change": status_change,
        }

        service_client.table("action_plan_updates").insert(change_log_data).execute()

        return ActionPlanResponse(**updated_record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update action plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update action plan. Please try again.",
        )


# =============================================================================
# AC#4: POST /{plan_id}/updates - Add progress update
# =============================================================================


@router.post(
    "/{plan_id}/updates",
    response_model=ActionPlanUpdateResponse,
    status_code=201,
)
async def add_progress_update(
    plan_id: str,
    update: ActionPlanUpdateCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Add a progress update to an action plan (AC#4).

    If status_change is provided, the plan's status is also updated.
    """
    try:
        service_client = _get_supabase_client()

        # Check plan exists
        plan_check = (
            service_client.table("action_plans")
            .select("*")
            .eq("id", plan_id)
            .execute()
        )

        if not plan_check.data:
            raise HTTPException(status_code=404, detail="Action plan not found")

        existing_plan = plan_check.data[0]

        # Build status_change string if applicable
        status_change_str = None
        if update.status_change:
            old_status = existing_plan.get("status", "unknown")
            status_change_str = f"{old_status} -> {update.status_change.value}"

        # Insert update record
        update_data = {
            "action_plan_id": plan_id,
            "author_id": current_user.id,
            "update_text": update.update_text,
            "status_change": status_change_str,
        }

        insert_result = (
            service_client.table("action_plan_updates")
            .insert(update_data)
            .execute()
        )

        if not insert_result.data:
            raise HTTPException(
                status_code=500, detail="Failed to create progress update"
            )

        # If status_change is provided, update the plan's status
        if update.status_change:
            service_client.table("action_plans").update(
                {"status": update.status_change.value}
            ).eq("id", plan_id).execute()

        return ActionPlanUpdateResponse(**insert_result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add progress update for plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to add progress update. Please try again.",
        )


# =============================================================================
# GET /{plan_id}/updates - List progress updates
# =============================================================================


@router.get("/{plan_id}/updates", response_model=List[ActionPlanUpdateResponse])
async def list_plan_updates(
    plan_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List progress updates for an action plan in chronological order."""
    try:
        service_client = _get_supabase_client()

        # Check plan exists
        plan_check = (
            service_client.table("action_plans")
            .select("id")
            .eq("id", plan_id)
            .execute()
        )

        if not plan_check.data:
            raise HTTPException(status_code=404, detail="Action plan not found")

        # Fetch updates sorted chronologically
        updates_result = (
            service_client.table("action_plan_updates")
            .select("*")
            .eq("action_plan_id", plan_id)
            .order("created_at", desc=False)
            .execute()
        )

        return [
            ActionPlanUpdateResponse(**u) for u in (updates_result.data or [])
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list updates for plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list progress updates. Please try again.",
        )


# =============================================================================
# AC#5: POST /{plan_id}/verify - Verify action plan completion
# =============================================================================


@router.post("/{plan_id}/verify", response_model=ActionPlanResponse)
async def verify_action_plan(
    plan_id: str,
    body: Optional[ActionPlanVerifyRequest] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Verify an action plan completion (AC#5).

    The plan must be in 'completed' status. Uses service-role client since
    verification can be done by any authenticated user (cross-user verification).
    """
    try:
        service_client = _get_supabase_client()

        # Check plan exists and status
        plan_check = (
            service_client.table("action_plans")
            .select("*")
            .eq("id", plan_id)
            .execute()
        )

        if not plan_check.data:
            raise HTTPException(status_code=404, detail="Action plan not found")

        existing_plan = plan_check.data[0]
        current_status = existing_plan.get("status")

        if current_status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Action plan must be in 'completed' status to verify. Current status: '{current_status}'",
            )

        # Update to verified using service-role client (cross-user verification)
        now = datetime.now(timezone.utc).isoformat()
        verify_data = {
            "status": "verified",
            "verified_by": current_user.id,
            "verified_at": now,
        }

        update_result = (
            service_client.table("action_plans")
            .update(verify_data)
            .eq("id", plan_id)
            .execute()
        )

        if not update_result.data:
            raise HTTPException(
                status_code=500, detail="Failed to verify action plan"
            )

        # Create update record for verification
        verification_notes = ""
        if body and body.verification_notes:
            verification_notes = f". Notes: {body.verification_notes}"

        log_data = {
            "action_plan_id": plan_id,
            "author_id": current_user.id,
            "update_text": f"Action plan verified{verification_notes}",
            "status_change": "completed -> verified",
        }

        service_client.table("action_plan_updates").insert(log_data).execute()

        return ActionPlanResponse(**update_result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify action plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to verify action plan. Please try again.",
        )
