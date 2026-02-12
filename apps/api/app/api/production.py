"""
Production API Endpoints

Provides endpoints for production throughput data visualization.

Story: 2.3 - Throughput Dashboard
AC: #2 - Actual vs Target Visualization
AC: #5 - Real-time Data Binding
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser
from app.schemas.production import (
    AssetDetail,
    ProductAttainment,
    ScheduleAttainmentResponse,
    ShiftBreakdown,
    VarianceCallout,
    WorkcenterEntry,
    WorkcenterScheduleAttainment,
    WorkcenterSummaryResponse,
)

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


@router.get(
    "/workcenter-summary",
    response_model=WorkcenterSummaryResponse,
    summary="Get Workcenter Production Summary",
    description="Retrieve production data grouped by workcenter for a given date.",
)
async def get_workcenter_summary(
    report_date: Optional[date] = Query(
        None,
        alias="date",
        description="Report date (YYYY-MM-DD). Defaults to yesterday (T-1).",
    ),
    shift: Optional[str] = Query(
        None,
        description="Optional shift filter (morning, afternoon, night). Returns only that shift's data.",
    ),
    current_user: CurrentUser = Depends(get_current_user),
) -> WorkcenterSummaryResponse:
    """
    Get production summary grouped by workcenter (area).

    Queries assets, daily_summaries, shift_targets, and optionally shift_summaries,
    then aggregates by asset area to produce per-workcenter totals and per-asset breakdowns.

    Story 11.1 AC#1: Workcenter-grouped response with aggregations
    Story 11.1 AC#2: Empty data returns 200 with message
    Story 11.1 AC#3: Date defaults to T-1
    Story 17.4 AC#1: shift_breakdown array with per-shift metrics
    Story 17.4 AC#2: Optional shift filter parameter
    """
    try:
        # AC#3: Default to yesterday if no date provided
        if report_date is None:
            report_date = date.today() - timedelta(days=1)

        # Validate shift parameter if provided
        valid_shifts = {"morning", "afternoon", "night"}
        if shift is not None and shift not in valid_shifts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid shift value '{shift}'. Must be one of: {', '.join(sorted(valid_shifts))}",
            )

        client = await get_supabase_client()

        # Query 1: Fetch all assets
        assets_response = client.table("assets").select("id, name, area").execute()

        # Query 2: Fetch daily_summaries for the requested date
        summaries_response = (
            client.table("daily_summaries")
            .select("asset_id, units_produced, oee, downtime_minutes")
            .eq("date", report_date.isoformat())
            .execute()
        )

        # AC#2: If no summary data, return empty with message
        if not summaries_response.data:
            return WorkcenterSummaryResponse(
                workcenters=[],
                report_date=report_date,
                message=f"No data available for {report_date.isoformat()}",
            )

        # Query 3: Fetch all shift_targets
        targets_response = (
            client.table("shift_targets")
            .select("asset_id, target_units")
            .execute()
        )

        # Query 4 (Story 17.4): Fetch shift_summaries for shift breakdown
        shift_query = (
            client.table("shift_summaries")
            .select("asset_id, shift, oee, downtime_minutes, units_produced")
            .eq("date", report_date.isoformat())
        )
        if shift:
            shift_query = shift_query.eq("shift", shift)
        shift_summaries_response = shift_query.execute()

        # Build lookup maps
        # Assets: id -> {name, area}
        assets_map: Dict[str, dict] = {}
        for asset in (assets_response.data or []):
            area = asset.get("area")
            if not area:
                continue  # Skip assets with NULL/empty area
            assets_map[asset["id"]] = {
                "name": asset["name"],
                "area": area,
            }

        # Summaries: asset_id -> summary data
        summaries_map: Dict[str, dict] = {}
        for summary in summaries_response.data:
            summaries_map[summary["asset_id"]] = summary

        # Targets: asset_id -> total target (sum across all shifts)
        targets_map: Dict[str, int] = {}
        for target in (targets_response.data or []):
            asset_id = target["asset_id"]
            targets_map[asset_id] = targets_map.get(asset_id, 0) + (target.get("target_units") or 0)

        # Shift summaries: asset_id -> list of shift records
        shift_data_map: Dict[str, List[dict]] = {}
        for row in (shift_summaries_response.data or []):
            aid = row.get("asset_id")
            if aid:
                shift_data_map.setdefault(aid, []).append(row)

        # When a specific shift is selected, use shift data as primary metrics
        if shift:
            if shift_data_map:
                # Override summaries_map with shift-specific data
                for asset_id, shift_rows in shift_data_map.items():
                    if shift_rows:
                        sr = shift_rows[0]  # One row per shift per asset
                        summaries_map[asset_id] = {
                            "asset_id": asset_id,
                            "units_produced": sr.get("units_produced") or 0,
                            "oee": sr.get("oee"),
                            "downtime_minutes": sr.get("downtime_minutes"),
                        }
            else:
                # No shift data available for this filter — zero out daily summaries
                # so we don't misleadingly show daily aggregates as shift data
                for asset_id in list(summaries_map.keys()):
                    summaries_map[asset_id] = {
                        "asset_id": asset_id,
                        "units_produced": 0,
                        "oee": None,
                        "downtime_minutes": None,
                    }

        # Group by workcenter (area)
        workcenters: Dict[str, List[AssetDetail]] = {}
        for asset_id, summary in summaries_map.items():
            asset_info = assets_map.get(asset_id)
            if not asset_info:
                continue  # Skip if asset not found or has no area

            area = asset_info["area"]
            actual = summary.get("units_produced") or 0
            target = targets_map.get(asset_id, 0)
            oee_val = summary.get("oee")
            downtime = summary.get("downtime_minutes")

            asset_detail = AssetDetail(
                asset_id=asset_id,
                asset_name=asset_info["name"],
                actual_output=actual,
                target_output=target,
                attainment_pct=calculate_percentage(actual, target),
                oee=float(oee_val) if oee_val is not None else None,
                downtime_minutes=int(downtime) if downtime is not None else None,
                hit_target=actual >= target,
            )

            if area not in workcenters:
                workcenters[area] = []
            workcenters[area].append(asset_detail)

        # Build workcenter entries
        workcenter_entries: List[WorkcenterEntry] = []
        for area_name in sorted(workcenters.keys()):
            asset_details = workcenters[area_name]
            total_actual = sum(a.actual_output for a in asset_details)
            total_target = sum(a.target_output for a in asset_details)
            assets_hit = sum(1 for a in asset_details if a.hit_target)
            assets_missed = len(asset_details) - assets_hit

            # Story 17.4 AC#1: Build shift_breakdown when not filtering by shift
            wc_shift_breakdown: Optional[List[ShiftBreakdown]] = None
            if not shift:
                # Aggregate shift data across all assets in this workcenter
                shift_agg: Dict[str, dict] = {}
                for ad in asset_details:
                    asset_shifts = shift_data_map.get(ad.asset_id, [])
                    for sr in asset_shifts:
                        s_name = sr.get("shift", "unknown")
                        if s_name not in shift_agg:
                            shift_agg[s_name] = {
                                "actual": 0,
                                "target": 0,
                                "oee_sum": 0.0,
                                "oee_count": 0,
                                "downtime": 0,
                            }
                        agg = shift_agg[s_name]
                        agg["actual"] += sr.get("units_produced") or 0
                        agg["downtime"] += sr.get("downtime_minutes") or 0
                        oee_v = sr.get("oee")
                        if oee_v is not None:
                            agg["oee_sum"] += float(oee_v)
                            agg["oee_count"] += 1

                # Build per-shift target: divide workcenter target evenly across shifts with data
                num_shifts = len(shift_agg) if shift_agg else 1

                if shift_agg:
                    breakdown_list = []
                    for s_name in ["morning", "afternoon", "night"]:
                        if s_name not in shift_agg:
                            continue
                        agg = shift_agg[s_name]
                        s_actual = agg["actual"]
                        s_target = total_target // num_shifts
                        s_oee = round(agg["oee_sum"] / agg["oee_count"], 2) if agg["oee_count"] > 0 else None
                        breakdown_list.append(ShiftBreakdown(
                            shift=s_name,
                            actual_output=s_actual,
                            target_output=s_target,
                            attainment_pct=calculate_percentage(s_actual, s_target),
                            oee=s_oee,
                            downtime_minutes=agg["downtime"],
                        ))
                    wc_shift_breakdown = breakdown_list if breakdown_list else None

            entry = WorkcenterEntry(
                workcenter=area_name,
                total_actual=total_actual,
                total_target=total_target,
                attainment_pct=calculate_percentage(total_actual, total_target),
                assets_hit=assets_hit,
                assets_missed=assets_missed,
                assets=asset_details,
                shift_breakdown=wc_shift_breakdown,
            )
            workcenter_entries.append(entry)

        return WorkcenterSummaryResponse(
            workcenters=workcenter_entries,
            report_date=report_date,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workcenter summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch workcenter summary data",
        )


@router.get(
    "/schedule-attainment",
    response_model=ScheduleAttainmentResponse,
    summary="Get Schedule Attainment Data",
    description="Compare scheduled vs. actual production by product per workcenter.",
)
async def get_schedule_attainment(
    report_date: date = Query(
        ...,
        alias="date",
        description="Date in YYYY-MM-DD format",
    ),
    area: Optional[str] = Query(None, description="Filter by plant area"),
    current_user: CurrentUser = Depends(get_current_user),
) -> ScheduleAttainmentResponse:
    """
    Get schedule attainment with per-workcenter product breakdown and variance callouts.

    Story 12.5 AC#1: Per-workcenter schedule attainment with product breakdown
    Story 12.5 AC#2: Product swap variance callouts
    Story 12.5 AC#3: No schedule returns 200 with message
    Story 12.5 AC#5: Optional area filter
    """
    try:
        date_str = report_date.isoformat()
        client = await get_supabase_client()

        # Query production_schedule for the requested date
        schedule_response = (
            client.table("production_schedule")
            .select("id, asset_id, product_id, scheduled_quantity, scheduled_date, shift")
            .eq("scheduled_date", date_str)
            .execute()
        )

        # AC#3: No schedule data -> return early with message
        if not schedule_response.data:
            return ScheduleAttainmentResponse(
                date=date_str,
                workcenters=[],
                has_data=False,
                message="No schedule data for this date",
            )

        # Query production_actuals for the requested date
        actuals_response = (
            client.table("production_actuals")
            .select("id, asset_id, product_id, actual_quantity, production_date, shift")
            .eq("production_date", date_str)
            .execute()
        )

        # Query assets and products for name resolution
        assets_response = client.table("assets").select("id, name, area").execute()
        products_response = client.table("products").select("id, name").execute()

        # Build lookup maps
        assets_map: Dict[str, dict] = {}
        for asset in (assets_response.data or []):
            asset_area = asset.get("area")
            if not asset_area:
                continue
            assets_map[asset["id"]] = {
                "name": asset["name"],
                "area": asset_area,
            }

        # AC#5: Apply area filter if specified (case-insensitive)
        if area:
            assets_map = {
                k: v for k, v in assets_map.items()
                if v.get("area") and v["area"].lower() == area.lower()
            }

        products_map: Dict[str, str] = {}
        for product in (products_response.data or []):
            products_map[product["id"]] = product["name"]

        # Group schedule entries by (asset_id, shift) -> list of entries
        schedule_by_asset_shift: Dict[tuple, list] = {}
        for entry in schedule_response.data:
            key = (entry["asset_id"], entry["shift"])
            if key not in schedule_by_asset_shift:
                schedule_by_asset_shift[key] = []
            schedule_by_asset_shift[key].append(entry)

        # Group actuals entries by (asset_id, shift) -> list of entries
        actuals_by_asset_shift: Dict[tuple, list] = {}
        for entry in (actuals_response.data or []):
            key = (entry["asset_id"], entry["shift"])
            if key not in actuals_by_asset_shift:
                actuals_by_asset_shift[key] = []
            actuals_by_asset_shift[key].append(entry)

        # Collect all (asset_id, shift) pairs from both schedule and actuals
        all_keys = set(schedule_by_asset_shift.keys()) | set(actuals_by_asset_shift.keys())

        # Group results by workcenter (area)
        workcenter_data: Dict[str, dict] = {}

        for asset_id, shift in all_keys:
            # Skip assets not in our filtered assets_map
            if asset_id not in assets_map:
                continue

            asset_info = assets_map[asset_id]
            asset_name = asset_info["name"]
            wc_name = asset_info["area"]

            if wc_name not in workcenter_data:
                workcenter_data[wc_name] = {
                    "products": {},  # product_id -> {scheduled, actual}
                    "variances": [],
                    "total_scheduled": 0,
                    "total_actual": 0,
                }

            wc = workcenter_data[wc_name]

            sched_entries = schedule_by_asset_shift.get((asset_id, shift), [])
            actual_entries = actuals_by_asset_shift.get((asset_id, shift), [])

            # Build product_id sets for this (asset, shift)
            sched_product_ids = {e["product_id"] for e in sched_entries}
            actual_product_ids = {e["product_id"] for e in actual_entries}

            # Build lookup for scheduled quantities by product_id
            sched_by_product: Dict[str, int] = {}
            for e in sched_entries:
                pid = e["product_id"]
                sched_by_product[pid] = sched_by_product.get(pid, 0) + (e.get("scheduled_quantity") or 0)

            # Build lookup for actual quantities by product_id
            actual_by_product: Dict[str, int] = {}
            for e in actual_entries:
                pid = e["product_id"]
                actual_by_product[pid] = actual_by_product.get(pid, 0) + (e.get("actual_quantity") or 0)

            # Detect swaps: scheduled products not in actuals AND actual products not in schedule
            # on the same (asset, shift)
            missing_products = sched_product_ids - actual_product_ids
            unscheduled_products = actual_product_ids - sched_product_ids

            # Generate swap callouts when both missing and unscheduled exist on same (asset, shift)
            if missing_products and unscheduled_products:
                for missing_pid in missing_products:
                    scheduled_product_name = products_map.get(missing_pid, missing_pid)
                    scheduled_qty = sched_by_product.get(missing_pid, 0)
                    for unsched_pid in unscheduled_products:
                        actual_product_name = products_map.get(unsched_pid, unsched_pid)
                        wc["variances"].append(VarianceCallout(
                            asset_name=asset_name,
                            message=(
                                f"{asset_name} ran {actual_product_name} instead of "
                                f"scheduled {scheduled_product_name} — "
                                f"{scheduled_qty} units of {scheduled_product_name} still needed"
                            ),
                            variance_type="swap",
                        ))

            # Generate missing callouts for scheduled products with no actual at all
            # (only if not already covered by swap)
            if missing_products and not unscheduled_products:
                for missing_pid in missing_products:
                    scheduled_product_name = products_map.get(missing_pid, missing_pid)
                    wc["variances"].append(VarianceCallout(
                        asset_name=asset_name,
                        message=f"Scheduled {scheduled_product_name} but no production recorded",
                        variance_type="missing",
                    ))

            # Generate unscheduled callouts for actual products with no schedule
            # (only if not already covered by swap)
            if unscheduled_products and not missing_products:
                for unsched_pid in unscheduled_products:
                    actual_product_name = products_map.get(unsched_pid, unsched_pid)
                    wc["variances"].append(VarianceCallout(
                        asset_name=asset_name,
                        message=f"Produced {actual_product_name} but not scheduled",
                        variance_type="unscheduled",
                    ))

            # Accumulate product attainment data
            # Scheduled products
            for pid, sched_qty in sched_by_product.items():
                actual_qty = actual_by_product.get(pid, 0)
                if pid not in wc["products"]:
                    wc["products"][pid] = {"scheduled": 0, "actual": 0}
                wc["products"][pid]["scheduled"] += sched_qty
                wc["products"][pid]["actual"] += actual_qty
                wc["total_scheduled"] += sched_qty
                wc["total_actual"] += actual_qty

            # Unscheduled products (actual only, not in schedule for this asset/shift)
            for pid in unscheduled_products:
                actual_qty = actual_by_product.get(pid, 0)
                if pid not in wc["products"]:
                    wc["products"][pid] = {"scheduled": 0, "actual": 0}
                wc["products"][pid]["actual"] += actual_qty
                wc["total_actual"] += actual_qty

        # Build response workcenter entries
        workcenter_entries: List[WorkcenterScheduleAttainment] = []
        for wc_name in sorted(workcenter_data.keys()):
            wc = workcenter_data[wc_name]

            product_list: List[ProductAttainment] = []
            for pid, qty_data in wc["products"].items():
                sched_qty = qty_data["scheduled"]
                actual_qty = qty_data["actual"]
                att_pct = calculate_percentage(actual_qty, sched_qty)
                product_list.append(ProductAttainment(
                    product_name=products_map.get(pid, pid),
                    product_id=pid,
                    scheduled_quantity=sched_qty,
                    actual_quantity=actual_qty,
                    attainment_pct=att_pct,
                ))

            total_sched = wc["total_scheduled"]
            total_act = wc["total_actual"]
            overall_pct = calculate_percentage(total_act, total_sched)

            workcenter_entries.append(WorkcenterScheduleAttainment(
                workcenter=wc_name,
                products=product_list,
                variances=wc["variances"],
                overall_attainment_pct=overall_pct,
            ))

        return ScheduleAttainmentResponse(
            date=date_str,
            workcenters=workcenter_entries,
            has_data=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schedule attainment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch schedule attainment data",
        )
