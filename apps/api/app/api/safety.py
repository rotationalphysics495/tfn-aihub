"""
Safety Alert API Endpoints

Provides endpoints for safety event management and alerting.

Story: 2.6 - Safety Alert System
AC: #3 - Safety API Endpoints
AC: #5 - Link to specific asset
AC: #9 - Safety count in header/status
AC: #10 - Financial impact context
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser
from app.models.safety import (
    AcknowledgeRequest,
    AcknowledgeResponse,
    ActiveSafetyAlertsResponse,
    DashboardStatusResponse,
    SafetyEventResponse,
    SafetyEventsResponse,
)
from app.services.safety_service import SafetyAlertService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def validate_uuid(event_id: str) -> UUID:
    """
    Validate and parse a UUID string.

    Args:
        event_id: String representation of UUID

    Returns:
        Parsed UUID object

    Raises:
        HTTPException: If the string is not a valid UUID
    """
    try:
        return UUID(event_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event_id format: {event_id}. Must be a valid UUID."
        )


async def get_supabase_client():
    """Get Supabase client for database operations."""
    from supabase import create_client

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase not configured"
        )

    return create_client(settings.supabase_url, settings.supabase_key)


# =============================================================================
# Safety Event Endpoints
# =============================================================================


@router.get(
    "/events",
    response_model=SafetyEventsResponse,
    summary="Get Safety Events",
    description="Retrieve recent safety events with optional filtering."
)
async def get_safety_events(
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of events to return"
    ),
    since: Optional[str] = Query(
        None,
        description="Return events after this ISO8601 timestamp"
    ),
    asset_id: Optional[str] = Query(
        None,
        description="Filter by specific asset UUID"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> SafetyEventsResponse:
    """
    Get recent safety events.

    Returns safety events sorted by timestamp (most recent first).
    Each event includes:
    - Asset name and area for linking (AC #5)
    - Financial impact calculated from cost_centers (AC #10)
    - Acknowledgement status

    Query Parameters:
        - limit: Maximum events to return (1-500, default 50)
        - since: ISO8601 timestamp to filter events after
        - asset_id: Filter by specific asset

    Returns:
        SafetyEventsResponse with events array and count
    """
    try:
        client = await get_supabase_client()
        service = SafetyAlertService(client)

        # Parse since parameter
        since_datetime = None
        if since:
            try:
                since_datetime = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid 'since' timestamp format. Use ISO8601."
                )

        return await service.get_safety_events(
            limit=limit,
            since=since_datetime,
            asset_id=asset_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching safety events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch safety events"
        )


@router.get(
    "/active",
    response_model=ActiveSafetyAlertsResponse,
    summary="Get Active Safety Alerts",
    description="Get currently active (unacknowledged) safety alerts."
)
async def get_active_alerts(
    current_user: CurrentUser = Depends(get_current_user),
) -> ActiveSafetyAlertsResponse:
    """
    Get active (unacknowledged) safety alerts.

    Returns all safety events that have not been acknowledged.
    This endpoint is used by:
    - The safety alert banner (AC #4)
    - The header safety count indicator (AC #9)
    - The Live Pulse view integration (AC #4, #5)

    Returns:
        ActiveSafetyAlertsResponse with active alerts and count
    """
    try:
        client = await get_supabase_client()
        service = SafetyAlertService(client)

        return await service.get_active_alerts()

    except Exception as e:
        logger.error(f"Error fetching active safety alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active safety alerts"
        )


@router.get(
    "/status",
    response_model=DashboardStatusResponse,
    summary="Get Dashboard Status",
    description="Get dashboard status including safety alert count."
)
async def get_dashboard_status(
    current_user: CurrentUser = Depends(get_current_user),
) -> DashboardStatusResponse:
    """
    Get dashboard status with safety alert count.

    Returns aggregated status including:
    - Safety alert count (AC #9)
    - Asset production status counts
    - Last poll timestamp

    This endpoint is used by the Command Center header
    to display the safety alert indicator.

    Returns:
        DashboardStatusResponse with safety_alert_count and asset metrics
    """
    try:
        client = await get_supabase_client()
        service = SafetyAlertService(client)

        return await service.get_dashboard_status()

    except Exception as e:
        logger.error(f"Error fetching dashboard status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard status"
        )


@router.post(
    "/acknowledge/{event_id}",
    response_model=AcknowledgeResponse,
    summary="Acknowledge Safety Event",
    description="Acknowledge a safety event to dismiss the alert."
)
async def acknowledge_safety_event(
    event_id: str = Path(..., description="UUID of the safety event to acknowledge"),
    request: Optional[AcknowledgeRequest] = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> AcknowledgeResponse:
    """
    Acknowledge a safety event.

    When acknowledged:
    - The event is marked as resolved
    - The event no longer appears in active alerts
    - The alert banner is dismissed (AC #6)

    Path Parameters:
        - event_id: UUID of the safety event to acknowledge

    Request Body:
        - acknowledged_by: Optional user ID (defaults to current user)

    Returns:
        AcknowledgeResponse with success status and updated event

    Raises:
        400: Invalid event_id format
        404: Safety event not found
    """
    # Validate UUID format
    validate_uuid(event_id)

    try:
        client = await get_supabase_client()
        service = SafetyAlertService(client)

        # Use current user if not specified
        acknowledged_by = None
        if request and request.acknowledged_by:
            acknowledged_by = request.acknowledged_by
        elif current_user and current_user.id:
            acknowledged_by = current_user.id

        result = await service.acknowledge_event(
            event_id=event_id,
            acknowledged_by=acknowledged_by,
        )

        # Raise 404 if event not found
        if not result.success and result.message and "not found" in result.message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Safety event {event_id} not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging safety event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge safety event"
        )


# =============================================================================
# Single Event Detail Endpoint (must be last due to path variable)
# =============================================================================


@router.get(
    "/{event_id}",
    response_model=SafetyEventResponse,
    summary="Get Safety Event Detail",
    description="Get detailed information about a specific safety event."
)
async def get_safety_event(
    event_id: str = Path(..., description="UUID of the safety event"),
    current_user: CurrentUser = Depends(get_current_user),
) -> SafetyEventResponse:
    """
    Get detailed information about a safety event.

    Path Parameters:
        - event_id: UUID of the safety event

    Returns:
        SafetyEventResponse with full event details including:
        - Asset name and area for linking (AC #5)
        - Financial impact from cost_centers (AC #10)
        - Acknowledgement status

    Raises:
        400: Invalid event_id format
        404: Safety event not found
    """
    # Validate UUID format
    validate_uuid(event_id)

    try:
        client = await get_supabase_client()
        service = SafetyAlertService(client)

        event = await service.get_safety_event_by_id(event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Safety event {event_id} not found"
            )

        return event

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching safety event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch safety event"
        )
