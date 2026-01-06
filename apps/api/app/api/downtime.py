"""
Downtime API Endpoints

Provides endpoints for downtime events and Pareto analysis.

Story: 2.5 - Downtime Pareto Analysis
AC: #1 - Downtime Data Retrieval
AC: #2 - Pareto Analysis Calculation
AC: #5 - Financial Impact Integration
AC: #6 - Safety Reason Code Highlighting
AC: #7 - Time Window Toggle
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser
from app.models.downtime import (
    CostOfLossSummary,
    DataSource,
    DowntimeEvent,
    DowntimeEventsResponse,
    ParetoItem,
    ParetoResponse,
    SafetyEventDetail,
)
from app.services.downtime_analysis import DowntimeAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


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


def parse_data_source(source: Optional[str]) -> DataSource:
    """Parse source parameter into DataSource enum."""
    if source == "live":
        return DataSource.LIVE_SNAPSHOTS
    return DataSource.DAILY_SUMMARIES


def get_last_updated(data_source: DataSource, records: List[dict]) -> str:
    """Get the last updated timestamp for the data."""
    if data_source == DataSource.LIVE_SNAPSHOTS:
        if records:
            timestamps = [r.get("snapshot_timestamp") for r in records if r.get("snapshot_timestamp")]
            if timestamps:
                return max(timestamps)
        return datetime.utcnow().isoformat() + "Z"
    else:
        yesterday = date.today() - timedelta(days=1)
        return f"{yesterday.isoformat()}T06:00:00Z"


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/events",
    response_model=DowntimeEventsResponse,
    summary="Get Downtime Events",
    description="Retrieve downtime events from the analytical cache with optional filtering."
)
async def get_downtime_events(
    start_date: Optional[date] = Query(
        None,
        description="Start date for query range (defaults to yesterday)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for query range (defaults to start_date)"
    ),
    asset_id: Optional[str] = Query(
        None,
        description="Filter by specific asset UUID"
    ),
    area: Optional[str] = Query(
        None,
        description="Filter by plant area"
    ),
    source: Optional[str] = Query(
        None,
        description="Data source: 'yesterday' for daily_summaries (T-1), 'live' for live_snapshots (T-15m)"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of events to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of records to skip for pagination"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> DowntimeEventsResponse:
    """
    Get downtime events with financial impact calculations.

    This endpoint retrieves downtime events from either:
    - daily_summaries (T-1 data) - default
    - live_snapshots (T-15m data) - when source='live'

    Each event includes calculated financial impact based on the asset's
    cost center hourly rate.

    Query Parameters:
        - start_date: Start of date range (default: yesterday)
        - end_date: End of date range (default: same as start_date)
        - asset_id: Filter by specific asset
        - area: Filter by plant area
        - source: 'yesterday' or 'live'
        - limit: Max records (1-500, default 50)
        - offset: Pagination offset

    Returns:
        DowntimeEventsResponse with events, totals, and metadata
    """
    try:
        client = await get_supabase_client()
        service = DowntimeAnalysisService(client)

        data_source = parse_data_source(source)

        # Get raw data based on source
        if data_source == DataSource.LIVE_SNAPSHOTS:
            raw_records = await service.get_downtime_from_live_snapshots(
                asset_id=asset_id,
                area=area,
            )
        else:
            raw_records = await service.get_downtime_from_daily_summaries(
                start_date=start_date,
                end_date=end_date,
                asset_id=asset_id,
                area=area,
            )

        # Transform to downtime events with financial calculations
        all_events = await service.transform_to_downtime_events(
            raw_records, data_source
        )

        # Calculate totals before pagination
        total_count = len(all_events)
        total_downtime_minutes = sum(e.duration_minutes for e in all_events)
        total_financial_impact = round(sum(e.financial_impact for e in all_events), 2)

        # Apply pagination
        paginated_events = all_events[offset:offset + limit]

        last_updated = get_last_updated(data_source, raw_records)

        return DowntimeEventsResponse(
            events=paginated_events,
            total_count=total_count,
            total_downtime_minutes=total_downtime_minutes,
            total_financial_impact=total_financial_impact,
            data_source=data_source.value,
            last_updated=last_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching downtime events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch downtime events"
        )


@router.get(
    "/pareto",
    response_model=ParetoResponse,
    summary="Get Downtime Pareto Analysis",
    description="Calculate Pareto distribution of downtime by reason code."
)
async def get_downtime_pareto(
    start_date: Optional[date] = Query(
        None,
        description="Start date for query range (defaults to yesterday)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for query range (defaults to start_date)"
    ),
    asset_id: Optional[str] = Query(
        None,
        description="Filter by specific asset UUID"
    ),
    area: Optional[str] = Query(
        None,
        description="Filter by plant area"
    ),
    source: Optional[str] = Query(
        None,
        description="Data source: 'yesterday' for daily_summaries (T-1), 'live' for live_snapshots (T-15m)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> ParetoResponse:
    """
    Get Pareto analysis of downtime by reason code.

    Calculates:
    - Total downtime per reason code
    - Percentage of total downtime
    - Cumulative percentage
    - Financial impact per reason
    - 80% threshold indicator (Pareto principle)

    Results are sorted by descending downtime duration.

    Query Parameters:
        - start_date: Start of date range (default: yesterday)
        - end_date: End of date range
        - asset_id: Filter by specific asset
        - area: Filter by plant area
        - source: 'yesterday' or 'live'

    Returns:
        ParetoResponse with items sorted by duration and 80% threshold index
    """
    try:
        client = await get_supabase_client()
        service = DowntimeAnalysisService(client)

        data_source = parse_data_source(source)

        # Get raw data
        if data_source == DataSource.LIVE_SNAPSHOTS:
            raw_records = await service.get_downtime_from_live_snapshots(
                asset_id=asset_id,
                area=area,
            )
        else:
            raw_records = await service.get_downtime_from_daily_summaries(
                start_date=start_date,
                end_date=end_date,
                asset_id=asset_id,
                area=area,
            )

        # Transform to downtime events
        events = await service.transform_to_downtime_events(raw_records, data_source)

        # Calculate Pareto distribution
        pareto_items, threshold_80_index = service.calculate_pareto(events)

        # Calculate totals
        total_downtime_minutes = sum(e.duration_minutes for e in events)
        total_financial_impact = round(sum(e.financial_impact for e in events), 2)
        total_events = len(events)

        last_updated = get_last_updated(data_source, raw_records)

        return ParetoResponse(
            items=pareto_items,
            total_downtime_minutes=total_downtime_minutes,
            total_financial_impact=total_financial_impact,
            total_events=total_events,
            data_source=data_source.value,
            last_updated=last_updated,
            threshold_80_index=threshold_80_index,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating Pareto analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate Pareto analysis"
        )


@router.get(
    "/summary",
    response_model=CostOfLossSummary,
    summary="Get Cost of Loss Summary",
    description="Get summary widget data for the Cost of Loss display."
)
async def get_cost_of_loss_summary(
    start_date: Optional[date] = Query(
        None,
        description="Start date for query range (defaults to yesterday)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for query range (defaults to start_date)"
    ),
    asset_id: Optional[str] = Query(
        None,
        description="Filter by specific asset UUID"
    ),
    area: Optional[str] = Query(
        None,
        description="Filter by plant area"
    ),
    source: Optional[str] = Query(
        None,
        description="Data source: 'yesterday' for daily_summaries (T-1), 'live' for live_snapshots (T-15m)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> CostOfLossSummary:
    """
    Get summary data for the Cost of Loss widget.

    Provides:
    - Total financial loss in dollars
    - Total downtime in minutes and hours
    - Top reason code with percentage
    - Safety event counts

    Query Parameters:
        - start_date: Start of date range (default: yesterday)
        - end_date: End of date range
        - asset_id: Filter by specific asset
        - area: Filter by plant area
        - source: 'yesterday' or 'live'

    Returns:
        CostOfLossSummary with aggregated metrics
    """
    try:
        client = await get_supabase_client()
        service = DowntimeAnalysisService(client)

        data_source = parse_data_source(source)

        # Get raw data
        if data_source == DataSource.LIVE_SNAPSHOTS:
            raw_records = await service.get_downtime_from_live_snapshots(
                asset_id=asset_id,
                area=area,
            )
        else:
            raw_records = await service.get_downtime_from_daily_summaries(
                start_date=start_date,
                end_date=end_date,
                asset_id=asset_id,
                area=area,
            )

        # Transform and calculate
        events = await service.transform_to_downtime_events(raw_records, data_source)
        pareto_items, _ = service.calculate_pareto(events)

        last_updated = get_last_updated(data_source, raw_records)

        return service.build_cost_of_loss_summary(
            events=events,
            pareto_items=pareto_items,
            data_source=data_source.value,
            last_updated=last_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cost of loss summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cost of loss summary"
        )


@router.get(
    "/safety/{event_id}",
    response_model=SafetyEventDetail,
    summary="Get Safety Event Detail",
    description="Get detailed information about a specific safety event."
)
async def get_safety_event_detail(
    event_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> SafetyEventDetail:
    """
    Get detailed information about a specific safety event.

    Used for the safety event detail modal/panel.

    Path Parameters:
        - event_id: UUID of the safety event

    Returns:
        SafetyEventDetail with full event information
    """
    try:
        client = await get_supabase_client()
        service = DowntimeAnalysisService(client)

        detail = await service.get_safety_event_detail(event_id)

        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Safety event {event_id} not found"
            )

        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching safety event detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch safety event detail"
        )


@router.get(
    "/areas",
    response_model=List[str],
    summary="Get Available Areas",
    description="Get list of unique plant areas for filtering."
)
async def get_downtime_areas(
    current_user: CurrentUser = Depends(get_current_user),
) -> List[str]:
    """
    Get list of unique plant areas for filter dropdown.

    Returns:
        List of unique area names
    """
    try:
        client = await get_supabase_client()

        response = client.table("assets").select("area").execute()

        if not response.data:
            return []

        # Get unique non-null areas
        areas = set()
        for asset in response.data:
            area = asset.get("area")
            if area:
                areas.add(area)

        return sorted(list(areas))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch areas"
        )
