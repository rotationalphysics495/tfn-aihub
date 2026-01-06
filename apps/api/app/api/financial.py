"""
Financial Impact API Endpoints

Provides endpoints for financial impact calculations and data retrieval.

Story: 2.7 - Financial Impact Calculator
AC: #5 - API Endpoint for Financial Data
"""

import logging
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser
from app.schemas.financial import (
    FinancialImpactResponse,
    LiveFinancialImpact,
    AssetFinancialContext,
)
from app.services.financial import get_financial_service, FinancialServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class FinancialSummaryResponse(BaseModel):
    """Summary of financial impact across multiple assets."""

    total_downtime_loss: float = Field(0.0, description="Total downtime loss in dollars")
    total_waste_loss: float = Field(0.0, description="Total waste loss in dollars")
    total_loss: float = Field(0.0, description="Combined total loss in dollars")
    total_downtime_minutes: int = Field(0, description="Total downtime in minutes")
    total_waste_count: int = Field(0, description="Total waste count")
    asset_count: int = Field(0, description="Number of assets included")
    currency: str = Field("USD", description="Currency code")
    period_start: date = Field(..., description="Start date of period")
    period_end: date = Field(..., description="End date of period")
    data_source: str = Field(..., description="Data source used")
    last_updated: str = Field(..., description="ISO timestamp of data freshness")


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


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/impact/{asset_id}",
    response_model=FinancialImpactResponse,
    summary="Get Financial Impact for Asset",
    description="Calculate and retrieve financial impact for a specific asset over a date range."
)
async def get_financial_impact(
    asset_id: str,
    start_date: Optional[date] = Query(
        None,
        description="Start date of period (defaults to yesterday)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date of period (defaults to start_date)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> FinancialImpactResponse:
    """
    Get financial impact for a single asset.

    Calculates:
    - Downtime loss: (downtime_minutes / 60) * standard_hourly_rate
    - Waste loss: waste_count * cost_per_unit
    - Total loss: downtime_loss + waste_loss

    The response includes the rates used (from cost_centers or defaults)
    and indicates if default rates were used via is_estimated flag.

    Path Parameters:
        - asset_id: UUID of the asset

    Query Parameters:
        - start_date: Start of date range (default: yesterday)
        - end_date: End of date range (default: same as start_date)

    Returns:
        FinancialImpactResponse with calculated losses and breakdown
    """
    try:
        # Default to yesterday (T-1)
        if start_date is None:
            start_date = date.today() - timedelta(days=1)

        if end_date is None:
            end_date = start_date

        # Validate date range
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date must be >= start_date"
            )

        service = get_financial_service()
        result = await service.get_financial_impact(
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date
        )

        return result

    except FinancialServiceError as e:
        logger.error(f"Financial service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching financial impact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch financial impact"
        )


@router.get(
    "/impact/{asset_id}/live",
    response_model=LiveFinancialImpact,
    summary="Get Live Financial Impact for Asset",
    description="Get accumulated financial impact for current shift from live data."
)
async def get_live_financial_impact(
    asset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> LiveFinancialImpact:
    """
    Get live financial impact for an asset's current shift.

    Returns accumulated financial losses from live_snapshots data,
    updated every 15 minutes by the Live Pulse pipeline.

    Path Parameters:
        - asset_id: UUID of the asset

    Returns:
        LiveFinancialImpact with current shift accumulated values
    """
    try:
        service = get_financial_service()
        result = await service.get_live_financial_impact(asset_id=asset_id)
        return result

    except FinancialServiceError as e:
        logger.error(f"Financial service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching live financial impact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live financial impact"
        )


@router.get(
    "/summary",
    response_model=FinancialSummaryResponse,
    summary="Get Financial Summary",
    description="Get aggregated financial impact across all assets or filtered by criteria."
)
async def get_financial_summary(
    start_date: Optional[date] = Query(
        None,
        description="Start date of period (defaults to yesterday)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date of period (defaults to start_date)"
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
) -> FinancialSummaryResponse:
    """
    Get aggregated financial summary across assets.

    Aggregates financial losses from daily_summaries or live_snapshots
    with optional filtering by plant area.

    Query Parameters:
        - start_date: Start of date range (default: yesterday)
        - end_date: End of date range (default: same as start_date)
        - area: Filter by plant area
        - source: 'yesterday' or 'live'

    Returns:
        FinancialSummaryResponse with aggregated totals
    """
    from datetime import datetime

    try:
        settings = get_settings()
        client = await get_supabase_client()

        # Default dates
        if start_date is None:
            start_date = date.today() - timedelta(days=1)
        if end_date is None:
            end_date = start_date

        use_live = source == "live"
        data_source = "live_snapshots" if use_live else "daily_summaries"

        # Get assets if filtering by area
        asset_filter = None
        if area:
            assets_response = client.table("assets").select("id").eq("area", area).execute()
            asset_ids = [a["id"] for a in (assets_response.data or [])]
            if not asset_ids:
                return FinancialSummaryResponse(
                    total_downtime_loss=0.0,
                    total_waste_loss=0.0,
                    total_loss=0.0,
                    total_downtime_minutes=0,
                    total_waste_count=0,
                    asset_count=0,
                    currency=settings.financial_currency,
                    period_start=start_date,
                    period_end=end_date,
                    data_source=data_source,
                    last_updated=datetime.utcnow().isoformat() + "Z",
                )
            asset_filter = asset_ids

        # Query data
        if use_live:
            query = client.table("live_snapshots").select(
                "asset_id, financial_loss_dollars"
            )
            if asset_filter:
                query = query.in_("asset_id", asset_filter)
            response = query.execute()

            # Aggregate
            total_loss = 0.0
            asset_ids_seen = set()
            for record in response.data or []:
                total_loss += record.get("financial_loss_dollars") or 0.0
                asset_ids_seen.add(record.get("asset_id"))

            last_updated = datetime.utcnow().isoformat() + "Z"

            return FinancialSummaryResponse(
                total_downtime_loss=0.0,  # Not available in live snapshots by default
                total_waste_loss=0.0,
                total_loss=round(total_loss, 2),
                total_downtime_minutes=0,
                total_waste_count=0,
                asset_count=len(asset_ids_seen),
                currency=settings.financial_currency,
                period_start=start_date,
                period_end=end_date,
                data_source=data_source,
                last_updated=last_updated,
            )
        else:
            # Query daily_summaries
            query = client.table("daily_summaries").select(
                "asset_id, downtime_minutes, waste, financial_loss"
            )

            if start_date == end_date:
                query = query.eq("date", start_date.isoformat())
            else:
                query = query.gte("date", start_date.isoformat())
                query = query.lte("date", end_date.isoformat())

            if asset_filter:
                query = query.in_("asset_id", asset_filter)

            response = query.execute()

            # Load cost centers for calculation
            service = get_financial_service()
            service.load_cost_centers()

            # Aggregate
            total_downtime_minutes = 0
            total_waste_count = 0
            total_downtime_loss = 0.0
            total_waste_loss = 0.0
            asset_ids_seen = set()

            for record in response.data or []:
                asset_id = record.get("asset_id")
                downtime = record.get("downtime_minutes") or 0
                waste = record.get("waste") or 0

                total_downtime_minutes += downtime
                total_waste_count += waste
                asset_ids_seen.add(asset_id)

                # Calculate financial impact
                from decimal import Decimal
                hourly_rate, _ = service.get_hourly_rate(asset_id)
                cost_per_unit, _ = service.get_cost_per_unit(asset_id)

                downtime_loss = service.calculate_downtime_loss(downtime, hourly_rate)
                waste_loss = service.calculate_waste_loss(waste, cost_per_unit)

                total_downtime_loss += float(downtime_loss)
                total_waste_loss += float(waste_loss)

            total_loss = total_downtime_loss + total_waste_loss
            last_updated = f"{start_date.isoformat()}T06:00:00Z"

            return FinancialSummaryResponse(
                total_downtime_loss=round(total_downtime_loss, 2),
                total_waste_loss=round(total_waste_loss, 2),
                total_loss=round(total_loss, 2),
                total_downtime_minutes=total_downtime_minutes,
                total_waste_count=total_waste_count,
                asset_count=len(asset_ids_seen),
                currency=settings.financial_currency,
                period_start=start_date,
                period_end=end_date,
                data_source=data_source,
                last_updated=last_updated,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching financial summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch financial summary"
        )


@router.get(
    "/context/{asset_id}",
    response_model=AssetFinancialContext,
    summary="Get Asset Financial Context",
    description="Get the financial context (rates) for a specific asset."
)
async def get_asset_financial_context(
    asset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> AssetFinancialContext:
    """
    Get financial context for an asset.

    Returns the standard_hourly_rate and cost_per_unit for the asset,
    indicating whether default values are being used.

    Path Parameters:
        - asset_id: UUID of the asset

    Returns:
        AssetFinancialContext with rates and is_estimated flag
    """
    try:
        service = get_financial_service()
        service.load_cost_centers()
        service.load_assets()

        asset_info = service._asset_cache.get(asset_id, {})
        asset_name = asset_info.get("name")

        hourly_rate, hourly_estimated = service.get_hourly_rate(asset_id)
        cost_per_unit, cost_estimated = service.get_cost_per_unit(asset_id)

        return AssetFinancialContext(
            asset_id=asset_id,
            asset_name=asset_name,
            standard_hourly_rate=float(hourly_rate),
            cost_per_unit=float(cost_per_unit),
            is_estimated=hourly_estimated or cost_estimated,
        )

    except FinancialServiceError as e:
        logger.error(f"Financial service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching asset financial context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch asset financial context"
        )
