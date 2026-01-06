"""
OEE API Endpoints

Provides endpoints for OEE (Overall Equipment Effectiveness) metrics.

Story: 2.4 - OEE Metrics View
AC: #2 - OEE metrics computed from daily_summaries (T-1) and live_snapshots (T-15m)
AC: #5 - OEE values update within 60 seconds of new data ingestion
AC: #7 - OEE targets from shift_targets shown alongside actual values
AC: #10 - API endpoint returns OEE data with proper error handling
"""

import logging
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser
from app.services.oee_calculator import (
    AssetOEE,
    OEEComponents,
    calculate_oee_from_daily_summary,
    calculate_oee_from_live_snapshot,
    calculate_plant_wide_oee,
    get_default_oee_target,
    get_oee_status,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Enums and Data Models
# =============================================================================


class DataSource(str, Enum):
    """Data source for OEE calculations."""
    DAILY_SUMMARIES = "daily_summaries"
    LIVE_SNAPSHOTS = "live_snapshots"


class OEEStatus(str, Enum):
    """OEE status classification."""
    GREEN = "green"    # >= 85%
    YELLOW = "yellow"  # 70-84%
    RED = "red"        # < 70%
    UNKNOWN = "unknown"


class PlantOEE(BaseModel):
    """Plant-wide OEE metrics."""

    overall: Optional[float] = Field(None, description="Overall OEE percentage")
    availability: Optional[float] = Field(None, description="Availability component percentage")
    performance: Optional[float] = Field(None, description="Performance component percentage")
    quality: Optional[float] = Field(None, description="Quality component percentage")
    target: float = Field(..., description="OEE target percentage")
    status: str = Field(..., description="OEE status: green, yellow, red, or unknown")


class AssetOEEResponse(BaseModel):
    """OEE metrics for a single asset."""

    asset_id: str = Field(..., description="Asset UUID")
    name: str = Field(..., description="Asset name")
    area: Optional[str] = Field(None, description="Plant area")
    oee: Optional[float] = Field(None, description="Overall OEE percentage")
    availability: Optional[float] = Field(None, description="Availability component")
    performance: Optional[float] = Field(None, description="Performance component")
    quality: Optional[float] = Field(None, description="Quality component")
    target: float = Field(..., description="OEE target percentage")
    status: str = Field(..., description="OEE status")


class OEEResponse(BaseModel):
    """Complete OEE response including plant-wide and asset-level metrics."""

    plant_oee: PlantOEE = Field(..., description="Plant-wide OEE summary")
    assets: List[AssetOEEResponse] = Field(default_factory=list, description="Per-asset OEE data")
    data_source: str = Field(..., description="Data source used: daily_summaries or live_snapshots")
    last_updated: str = Field(..., description="ISO timestamp of data freshness")


class AssetOEEDetailResponse(BaseModel):
    """Detailed OEE response for a single asset."""

    asset_id: str = Field(..., description="Asset UUID")
    name: str = Field(..., description="Asset name")
    area: Optional[str] = Field(None, description="Plant area")
    oee: Optional[float] = Field(None, description="Overall OEE percentage")
    availability: Optional[float] = Field(None, description="Availability component")
    performance: Optional[float] = Field(None, description="Performance component")
    quality: Optional[float] = Field(None, description="Quality component")
    target: float = Field(..., description="OEE target percentage")
    status: str = Field(..., description="OEE status")
    data_source: str = Field(..., description="Data source used")
    last_updated: str = Field(..., description="ISO timestamp of data")


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


async def get_assets_map(client) -> dict:
    """Get a mapping of asset_id to asset info."""
    response = client.table("assets").select("id, name, area, source_id").execute()

    if not response.data:
        return {}

    return {
        asset["id"]: {
            "name": asset["name"],
            "area": asset.get("area"),
            "source_id": asset.get("source_id"),
        }
        for asset in response.data
    }


async def get_shift_targets_map(client) -> dict:
    """Get a mapping of asset_id to shift target info."""
    response = client.table("shift_targets").select(
        "asset_id, target_output, shift, effective_date"
    ).execute()

    if not response.data:
        return {}

    # Return the most recent target per asset
    targets = {}
    for target in response.data:
        asset_id = target["asset_id"]
        if asset_id not in targets:
            targets[asset_id] = target
        else:
            # Use the one with more recent effective_date
            current_date = targets[asset_id].get("effective_date")
            new_date = target.get("effective_date")
            if new_date and (not current_date or new_date > current_date):
                targets[asset_id] = target

    return targets


async def get_daily_summaries(
    client,
    report_date: Optional[date] = None,
    asset_id: Optional[str] = None,
) -> List[dict]:
    """Get daily summaries for the specified date."""
    if report_date is None:
        report_date = date.today() - timedelta(days=1)  # Yesterday (T-1)

    query = client.table("daily_summaries").select("*")
    query = query.eq("report_date", report_date.isoformat())

    if asset_id:
        query = query.eq("asset_id", asset_id)

    response = query.execute()
    return response.data or []


async def get_latest_live_snapshots(
    client,
    asset_id: Optional[str] = None,
) -> List[dict]:
    """Get the most recent live snapshot for each asset."""
    query = client.table("live_snapshots").select("*")

    if asset_id:
        query = query.eq("asset_id", asset_id)

    # Order by timestamp descending to get latest first
    query = query.order("snapshot_timestamp", desc=True)

    response = query.execute()

    if not response.data:
        return []

    # Get only the most recent snapshot per asset
    latest_by_asset = {}
    for snapshot in response.data:
        aid = snapshot["asset_id"]
        if aid not in latest_by_asset:
            latest_by_asset[aid] = snapshot

    return list(latest_by_asset.values())


def build_asset_oee_list(
    assets_map: dict,
    data_records: List[dict],
    targets_map: dict,
    data_source: DataSource,
) -> List[AssetOEE]:
    """Build a list of AssetOEE objects from data records."""
    asset_oee_list = []

    for record in data_records:
        asset_id = record.get("asset_id")
        if not asset_id or asset_id not in assets_map:
            continue

        asset_info = assets_map[asset_id]
        target_info = targets_map.get(asset_id, {})

        # Calculate OEE based on data source
        if data_source == DataSource.DAILY_SUMMARIES:
            oee_components = calculate_oee_from_daily_summary(record, target_info)
        else:
            oee_components = calculate_oee_from_live_snapshot(record, target_info)

        # Get target from shift_targets or use default
        target_value = target_info.get("target_output")
        # For OEE target, use default percentage (85%)
        oee_target = get_default_oee_target()

        asset_oee = AssetOEE(
            asset_id=asset_id,
            name=asset_info["name"],
            area=asset_info.get("area"),
            oee=oee_components.overall,
            availability=oee_components.availability,
            performance=oee_components.performance,
            quality=oee_components.quality,
            target=oee_target,
            status=oee_components.status,
        )
        asset_oee_list.append(asset_oee)

    return asset_oee_list


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/plant",
    response_model=OEEResponse,
    summary="Get Plant-Wide OEE Summary",
    description="Retrieve plant-wide OEE metrics with per-asset breakdown."
)
async def get_plant_oee(
    source: Optional[str] = Query(
        None,
        description="Data source: 'yesterday' for daily_summaries (T-1), 'live' for live_snapshots (T-15m)"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> OEEResponse:
    """
    Get plant-wide OEE summary with all asset breakdowns.

    Query Parameters:
        - source: 'yesterday' for T-1 data, 'live' for T-15m data (default: yesterday)

    Returns:
        OEEResponse with plant_oee, assets array, data_source, and last_updated
    """
    try:
        client = await get_supabase_client()

        # Determine data source
        use_live = source == "live"
        data_source = DataSource.LIVE_SNAPSHOTS if use_live else DataSource.DAILY_SUMMARIES

        # Get assets and targets
        assets_map = await get_assets_map(client)
        targets_map = await get_shift_targets_map(client)

        if not assets_map:
            return OEEResponse(
                plant_oee=PlantOEE(
                    overall=None,
                    availability=None,
                    performance=None,
                    quality=None,
                    target=get_default_oee_target(),
                    status="unknown",
                ),
                assets=[],
                data_source=data_source.value,
                last_updated=datetime.utcnow().isoformat() + "Z",
            )

        # Get data based on source
        if use_live:
            data_records = await get_latest_live_snapshots(client)
            # Find the most recent timestamp
            if data_records:
                timestamps = [r.get("snapshot_timestamp") for r in data_records if r.get("snapshot_timestamp")]
                last_updated = max(timestamps) if timestamps else datetime.utcnow().isoformat() + "Z"
            else:
                last_updated = datetime.utcnow().isoformat() + "Z"
        else:
            yesterday = date.today() - timedelta(days=1)
            data_records = await get_daily_summaries(client, report_date=yesterday)
            last_updated = f"{yesterday.isoformat()}T06:00:00Z"  # Morning report time

        # Build asset OEE list
        asset_oee_list = build_asset_oee_list(
            assets_map, data_records, targets_map, data_source
        )

        # Calculate plant-wide OEE
        plant_components = calculate_plant_wide_oee(asset_oee_list)

        # Build response
        plant_oee = PlantOEE(
            overall=plant_components.overall,
            availability=plant_components.availability,
            performance=plant_components.performance,
            quality=plant_components.quality,
            target=get_default_oee_target(),
            status=plant_components.status,
        )

        assets_response = [
            AssetOEEResponse(
                asset_id=a.asset_id,
                name=a.name,
                area=a.area,
                oee=a.oee,
                availability=a.availability,
                performance=a.performance,
                quality=a.quality,
                target=a.target,
                status=a.status,
            )
            for a in asset_oee_list
        ]

        # Sort assets by OEE (lowest first, so attention-needed assets appear first)
        assets_response.sort(key=lambda x: (x.oee is None, x.oee or 0))

        return OEEResponse(
            plant_oee=plant_oee,
            assets=assets_response,
            data_source=data_source.value,
            last_updated=last_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching plant OEE: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch OEE data"
        )


@router.get(
    "/assets",
    response_model=List[AssetOEEResponse],
    summary="Get Per-Asset OEE Breakdown",
    description="Retrieve OEE metrics for all assets."
)
async def get_assets_oee(
    source: Optional[str] = Query(
        None,
        description="Data source: 'yesterday' for T-1, 'live' for T-15m"
    ),
    area: Optional[str] = Query(None, description="Filter by plant area"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by OEE status: green, yellow, or red"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> List[AssetOEEResponse]:
    """
    Get OEE metrics for all assets with optional filtering.

    Query Parameters:
        - source: 'yesterday' or 'live'
        - area: Filter by plant area
        - status: Filter by OEE status (green, yellow, red)

    Returns:
        List of AssetOEEResponse objects
    """
    try:
        client = await get_supabase_client()

        # Determine data source
        use_live = source == "live"
        data_source = DataSource.LIVE_SNAPSHOTS if use_live else DataSource.DAILY_SUMMARIES

        # Get assets and targets
        assets_map = await get_assets_map(client)
        targets_map = await get_shift_targets_map(client)

        if not assets_map:
            return []

        # Apply area filter to assets_map
        if area:
            assets_map = {
                k: v for k, v in assets_map.items()
                if v.get("area") and v["area"].lower() == area.lower()
            }

        # Get data based on source
        if use_live:
            data_records = await get_latest_live_snapshots(client)
        else:
            yesterday = date.today() - timedelta(days=1)
            data_records = await get_daily_summaries(client, report_date=yesterday)

        # Build asset OEE list
        asset_oee_list = build_asset_oee_list(
            assets_map, data_records, targets_map, data_source
        )

        # Apply status filter
        if status_filter:
            asset_oee_list = [a for a in asset_oee_list if a.status == status_filter.lower()]

        # Build response
        assets_response = [
            AssetOEEResponse(
                asset_id=a.asset_id,
                name=a.name,
                area=a.area,
                oee=a.oee,
                availability=a.availability,
                performance=a.performance,
                quality=a.quality,
                target=a.target,
                status=a.status,
            )
            for a in asset_oee_list
        ]

        # Sort by OEE (lowest first)
        assets_response.sort(key=lambda x: (x.oee is None, x.oee or 0))

        return assets_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching assets OEE: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch OEE data"
        )


@router.get(
    "/assets/{asset_id}",
    response_model=AssetOEEDetailResponse,
    summary="Get Single Asset OEE Detail",
    description="Retrieve detailed OEE metrics for a specific asset."
)
async def get_asset_oee_detail(
    asset_id: str,
    source: Optional[str] = Query(
        None,
        description="Data source: 'yesterday' for T-1, 'live' for T-15m"
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> AssetOEEDetailResponse:
    """
    Get detailed OEE metrics for a single asset.

    Path Parameters:
        - asset_id: UUID of the asset

    Query Parameters:
        - source: 'yesterday' or 'live'

    Returns:
        AssetOEEDetailResponse with full OEE details
    """
    try:
        client = await get_supabase_client()

        # Get asset info
        asset_response = client.table("assets").select(
            "id, name, area"
        ).eq("id", asset_id).execute()

        if not asset_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )

        asset_info = asset_response.data[0]

        # Get target
        targets_response = client.table("shift_targets").select(
            "target_output"
        ).eq("asset_id", asset_id).execute()

        target_info = targets_response.data[0] if targets_response.data else {}

        # Determine data source
        use_live = source == "live"
        data_source = DataSource.LIVE_SNAPSHOTS if use_live else DataSource.DAILY_SUMMARIES

        # Get data
        if use_live:
            snapshots = await get_latest_live_snapshots(client, asset_id=asset_id)
            data_record = snapshots[0] if snapshots else None
            last_updated = data_record.get("snapshot_timestamp") if data_record else datetime.utcnow().isoformat() + "Z"
        else:
            yesterday = date.today() - timedelta(days=1)
            summaries = await get_daily_summaries(client, report_date=yesterday, asset_id=asset_id)
            data_record = summaries[0] if summaries else None
            last_updated = f"{yesterday.isoformat()}T06:00:00Z"

        if not data_record:
            # Return response with null values
            return AssetOEEDetailResponse(
                asset_id=asset_id,
                name=asset_info["name"],
                area=asset_info.get("area"),
                oee=None,
                availability=None,
                performance=None,
                quality=None,
                target=get_default_oee_target(),
                status="unknown",
                data_source=data_source.value,
                last_updated=last_updated,
            )

        # Calculate OEE
        if use_live:
            oee_components = calculate_oee_from_live_snapshot(data_record, target_info)
        else:
            oee_components = calculate_oee_from_daily_summary(data_record, target_info)

        return AssetOEEDetailResponse(
            asset_id=asset_id,
            name=asset_info["name"],
            area=asset_info.get("area"),
            oee=oee_components.overall,
            availability=oee_components.availability,
            performance=oee_components.performance,
            quality=oee_components.quality,
            target=get_default_oee_target(),
            status=oee_components.status,
            data_source=data_source.value,
            last_updated=last_updated,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching asset OEE detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch OEE data"
        )


@router.get(
    "/areas",
    response_model=List[str],
    summary="Get Available Asset Areas",
    description="Retrieve list of unique asset areas for filtering."
)
async def get_oee_areas(
    current_user: CurrentUser = Depends(get_current_user),
) -> List[str]:
    """
    Get list of unique asset areas for OEE filter dropdown.

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
        logger.error(f"Error fetching OEE areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch areas"
        )
