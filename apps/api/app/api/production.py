"""
Production API Endpoints

Provides endpoints for production throughput data visualization.

Story: 2.3 - Throughput Dashboard
AC: #2 - Actual vs Target Visualization
AC: #5 - Real-time Data Binding
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Data Models
# =============================================================================


class ThroughputStatus(str):
    """Status categories for throughput performance."""
    ON_TARGET = "on_target"
    BEHIND = "behind"
    CRITICAL = "critical"


class AssetThroughput(BaseModel):
    """Throughput data for a single asset."""

    id: str = Field(..., description="Asset UUID")
    name: str = Field(..., description="Asset name")
    area: Optional[str] = Field(None, description="Plant area")
    actual_output: int = Field(..., description="Current actual output")
    target_output: int = Field(..., description="Target output")
    variance: int = Field(..., description="Variance (actual - target)")
    percentage: float = Field(..., description="Percentage of target achieved")
    status: str = Field(..., description="Status: on_target, behind, or critical")
    snapshot_timestamp: str = Field(..., description="ISO timestamp of the snapshot")


class ThroughputResponse(BaseModel):
    """Response model for throughput dashboard data."""

    assets: List[AssetThroughput] = Field(default_factory=list)
    last_updated: str = Field(..., description="ISO timestamp of last update")
    total_assets: int = Field(0, description="Total number of assets")
    on_target_count: int = Field(0, description="Count of assets on target")
    behind_count: int = Field(0, description="Count of assets behind target")
    critical_count: int = Field(0, description="Count of assets critically behind")


# =============================================================================
# Helper Functions
# =============================================================================


def calculate_status(actual: int, target: int) -> str:
    """
    Calculate throughput status based on actual vs target.

    Status thresholds:
    - on_target: Actual >= Target (percentage >= 100%)
    - behind: Actual < Target by < 10% (percentage >= 90% and < 100%)
    - critical: Actual < Target by >= 10% (percentage < 90%)

    Note: 'critical' is labeled as 'ahead' in the DB schema but represents
    critically behind per the story requirements.
    """
    if target == 0:
        return ThroughputStatus.ON_TARGET  # Avoid division by zero

    percentage = (actual / target) * 100

    if percentage >= 100:
        return ThroughputStatus.ON_TARGET
    elif percentage >= 90:
        return ThroughputStatus.BEHIND
    else:
        return ThroughputStatus.CRITICAL


def calculate_percentage(actual: int, target: int) -> float:
    """Calculate percentage of target achieved."""
    if target == 0:
        return 100.0  # Avoid division by zero

    percentage = (actual / target) * 100
    return round(percentage, 1)


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
    "/throughput",
    response_model=ThroughputResponse,
    summary="Get Throughput Dashboard Data",
    description="Retrieve actual vs target throughput data for all assets from live snapshots."
)
async def get_throughput_data(
    area: Optional[str] = Query(None, description="Filter by asset area"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: on_target, behind, or critical"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> ThroughputResponse:
    """
    Get throughput dashboard data with actual vs target metrics for all assets.

    This endpoint retrieves the latest snapshot for each asset from the
    live_snapshots table and calculates variance and status indicators.

    Query Parameters:
        - area: Filter assets by plant area
        - status: Filter by performance status (on_target, behind, critical)

    Returns:
        ThroughputResponse with asset throughput data and summary counts
    """
    try:
        client = await get_supabase_client()

        # Get latest snapshots using Supabase query builder
        # First get all assets
        assets_response = client.table("assets").select("id, name, area, source_id").execute()

        if not assets_response.data:
            return ThroughputResponse(
                assets=[],
                last_updated=datetime.utcnow().isoformat() + "Z",
                total_assets=0,
                on_target_count=0,
                behind_count=0,
                critical_count=0,
            )

        assets_map = {
            asset["id"]: {
                "name": asset["name"],
                "area": asset.get("area"),
                "source_id": asset.get("source_id"),
            }
            for asset in assets_response.data
        }

        # Apply area filter if specified
        if area:
            assets_map = {
                k: v for k, v in assets_map.items()
                if v.get("area") and v["area"].lower() == area.lower()
            }

        if not assets_map:
            return ThroughputResponse(
                assets=[],
                last_updated=datetime.utcnow().isoformat() + "Z",
                total_assets=0,
                on_target_count=0,
                behind_count=0,
                critical_count=0,
            )

        # Get latest snapshots for these assets
        # Order by snapshot_timestamp desc and limit to get most recent per asset
        snapshots_response = client.table("live_snapshots").select(
            "id, asset_id, snapshot_timestamp, current_output, target_output, output_variance, status"
        ).order("snapshot_timestamp", desc=True).execute()

        if not snapshots_response.data:
            # No snapshots, return assets with zero values
            asset_throughputs = []
            for asset_id, asset_info in assets_map.items():
                throughput = AssetThroughput(
                    id=asset_id,
                    name=asset_info["name"],
                    area=asset_info.get("area"),
                    actual_output=0,
                    target_output=0,
                    variance=0,
                    percentage=0.0,
                    status=ThroughputStatus.ON_TARGET,
                    snapshot_timestamp=datetime.utcnow().isoformat() + "Z",
                )
                asset_throughputs.append(throughput)

            return ThroughputResponse(
                assets=asset_throughputs,
                last_updated=datetime.utcnow().isoformat() + "Z",
                total_assets=len(asset_throughputs),
                on_target_count=len(asset_throughputs),
                behind_count=0,
                critical_count=0,
            )

        # Find latest snapshot per asset
        latest_by_asset = {}
        for snapshot in snapshots_response.data:
            asset_id = snapshot["asset_id"]
            if asset_id not in latest_by_asset:
                latest_by_asset[asset_id] = snapshot

        # Build response
        asset_throughputs = []
        on_target_count = 0
        behind_count = 0
        critical_count = 0
        latest_timestamp = None

        for asset_id, asset_info in assets_map.items():
            snapshot = latest_by_asset.get(asset_id)

            if snapshot:
                actual = snapshot.get("current_output", 0) or 0
                target = snapshot.get("target_output", 0) or 0
                variance = actual - target
                percentage = calculate_percentage(actual, target)
                throughput_status = calculate_status(actual, target)
                snapshot_time = snapshot.get("snapshot_timestamp", datetime.utcnow().isoformat())
            else:
                actual = 0
                target = 0
                variance = 0
                percentage = 0.0
                throughput_status = ThroughputStatus.ON_TARGET
                snapshot_time = datetime.utcnow().isoformat() + "Z"

            # Apply status filter if specified
            if status_filter and throughput_status != status_filter:
                continue

            throughput = AssetThroughput(
                id=asset_id,
                name=asset_info["name"],
                area=asset_info.get("area"),
                actual_output=actual,
                target_output=target,
                variance=variance,
                percentage=percentage,
                status=throughput_status,
                snapshot_timestamp=snapshot_time,
            )
            asset_throughputs.append(throughput)

            # Count by status
            if throughput_status == ThroughputStatus.ON_TARGET:
                on_target_count += 1
            elif throughput_status == ThroughputStatus.BEHIND:
                behind_count += 1
            else:
                critical_count += 1

            # Track latest timestamp
            if latest_timestamp is None or snapshot_time > latest_timestamp:
                latest_timestamp = snapshot_time

        # Sort by status priority (critical first, then behind, then on_target)
        status_order = {
            ThroughputStatus.CRITICAL: 0,
            ThroughputStatus.BEHIND: 1,
            ThroughputStatus.ON_TARGET: 2,
        }
        asset_throughputs.sort(key=lambda x: (status_order.get(x.status, 3), -x.variance))

        return ThroughputResponse(
            assets=asset_throughputs,
            last_updated=latest_timestamp or datetime.utcnow().isoformat() + "Z",
            total_assets=len(asset_throughputs),
            on_target_count=on_target_count,
            behind_count=behind_count,
            critical_count=critical_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching throughput data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch throughput data"
        )


@router.get(
    "/throughput/areas",
    response_model=List[str],
    summary="Get Available Asset Areas",
    description="Retrieve list of unique asset areas for filtering."
)
async def get_asset_areas(
    current_user: CurrentUser = Depends(get_current_user),
) -> List[str]:
    """
    Get list of unique asset areas for filter dropdown.

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
        logger.error(f"Error fetching asset areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch asset areas"
        )
