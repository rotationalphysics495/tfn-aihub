"""
Live Pulse Ticker API Endpoints

Provides the aggregated live pulse data for the Command Center ticker display.

Story: 2.9 - Live Pulse Ticker
AC: #2 - Production Status Display
AC: #3 - Financial Context Integration
AC: #4 - Safety Alert Integration
AC: #5 - Data Source Integration
AC: #6 - Performance Requirements
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Response Models (per Story 2.9 API Response Schema)
# =============================================================================


class MachineStatus(BaseModel):
    """Machine status breakdown."""

    running: int = Field(0, description="Number of machines running")
    idle: int = Field(0, description="Number of machines idle")
    down: int = Field(0, description="Number of machines down")
    total: int = Field(0, description="Total number of machines")


class ActiveDowntime(BaseModel):
    """Active downtime event."""

    asset_name: str = Field(..., description="Name of the asset")
    reason_code: str = Field(..., description="Downtime reason code")
    duration_minutes: int = Field(0, description="Duration in minutes")


class ProductionData(BaseModel):
    """Production metrics for the live pulse ticker."""

    current_output: int = Field(0, description="Current total output")
    target_output: int = Field(0, description="Target output")
    output_percentage: float = Field(0.0, description="Percentage of target achieved")
    oee_percentage: float = Field(0.0, description="Current OEE percentage")
    machine_status: MachineStatus = Field(
        default_factory=MachineStatus, description="Machine status breakdown"
    )
    active_downtime: List[ActiveDowntime] = Field(
        default_factory=list, description="List of active downtime events"
    )


class FinancialData(BaseModel):
    """Financial context for the live pulse ticker."""

    shift_to_date_loss: float = Field(0.0, description="Total $ loss for current shift")
    rolling_15_min_loss: float = Field(0.0, description="$ loss in last 15 min window")
    currency: str = Field("USD", description="Currency code")


class SafetyIncident(BaseModel):
    """Active safety incident."""

    id: str = Field(..., description="Safety event UUID")
    asset_name: str = Field(..., description="Name of the affected asset")
    detected_at: str = Field(..., description="ISO timestamp of detection")
    severity: str = Field(..., description="Severity level")


class SafetyData(BaseModel):
    """Safety alert data for the live pulse ticker."""

    has_active_incident: bool = Field(False, description="Whether any active incidents exist")
    active_incidents: List[SafetyIncident] = Field(
        default_factory=list, description="List of active safety incidents"
    )


class MetaData(BaseModel):
    """Metadata about the live pulse data."""

    data_age: int = Field(0, description="Seconds since last update")
    is_stale: bool = Field(False, description="True if dataAge > 1200 (20 min)")


class LivePulseResponse(BaseModel):
    """Complete live pulse ticker response."""

    timestamp: str = Field(..., description="ISO 8601 timestamp of this response")
    production: ProductionData = Field(
        default_factory=ProductionData, description="Production metrics"
    )
    financial: FinancialData = Field(
        default_factory=FinancialData, description="Financial context"
    )
    safety: SafetyData = Field(
        default_factory=SafetyData, description="Safety alert data"
    )
    meta: MetaData = Field(
        default_factory=MetaData, description="Data freshness metadata"
    )


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


def calculate_data_age(snapshot_timestamp: Optional[str]) -> tuple[int, bool]:
    """
    Calculate the age of data in seconds and staleness flag.

    Args:
        snapshot_timestamp: ISO timestamp of the latest snapshot

    Returns:
        Tuple of (age_in_seconds, is_stale)
        is_stale is True if age > 1200 seconds (20 minutes)
    """
    if not snapshot_timestamp:
        return 0, True

    try:
        # Parse timestamp - normalize to UTC for consistent comparison
        ts = snapshot_timestamp.replace("Z", "+00:00")
        if "+" not in ts and "-" not in ts[10:]:
            # Assume UTC if no timezone specified
            ts = ts + "+00:00"
        snapshot_dt = datetime.fromisoformat(ts)

        # Convert to naive UTC for comparison
        if snapshot_dt.tzinfo is not None:
            # Convert to UTC and remove timezone info for comparison
            from datetime import timezone
            snapshot_dt = snapshot_dt.astimezone(timezone.utc).replace(tzinfo=None)

        # Compare with current UTC time (both naive)
        now = datetime.utcnow()
        age_seconds = int((now - snapshot_dt).total_seconds())
        age_seconds = max(0, age_seconds)  # Don't return negative values

        # 20 minutes = 1200 seconds threshold for staleness
        is_stale = age_seconds > 1200

        return age_seconds, is_stale
    except (ValueError, TypeError):
        return 0, True


# =============================================================================
# Endpoint
# =============================================================================


@router.get(
    "",
    response_model=LivePulseResponse,
    summary="Get Live Pulse Ticker Data",
    description="Retrieve aggregated live pulse data for the Command Center ticker display."
)
async def get_live_pulse_data(
    current_user: CurrentUser = Depends(get_current_user),
) -> LivePulseResponse:
    """
    Get live pulse ticker data.

    Aggregates data from multiple sources:
    - live_snapshots: Production metrics (throughput, OEE)
    - safety_events: Active safety incidents
    - cost_centers: Financial calculations

    Returns a consolidated response for the Live Pulse ticker component.

    Story: 2.9 - Live Pulse Ticker
    AC: #2 - Production Status Display
    AC: #3 - Financial Context Integration
    AC: #4 - Safety Alert Integration
    AC: #5 - Data Source Integration
    AC: #6 - Performance Requirements
    """
    try:
        settings = get_settings()
        client = await get_supabase_client()

        # Initialize response data
        now = datetime.utcnow()
        response_timestamp = now.isoformat() + "Z"

        # Track latest snapshot timestamp for data freshness
        latest_snapshot_time: Optional[str] = None

        # =====================================================================
        # 1. Fetch Assets with Cost Centers
        # =====================================================================

        assets_response = client.table("assets").select(
            "id, name, area, source_id"
        ).execute()
        assets_map = {}
        for asset in assets_response.data or []:
            assets_map[asset["id"]] = {
                "name": asset["name"],
                "area": asset.get("area"),
                "source_id": asset.get("source_id"),
            }

        # Load cost centers for financial calculations
        cost_centers_response = client.table("cost_centers").select(
            "asset_id, standard_hourly_rate"
        ).execute()
        cost_centers_map = {}
        for cc in cost_centers_response.data or []:
            cost_centers_map[cc["asset_id"]] = {
                "hourly_rate": Decimal(str(cc.get("standard_hourly_rate") or settings.default_hourly_rate)),
                "cost_per_unit": Decimal(str(settings.default_cost_per_unit)),  # Not in schema - use default
            }

        # =====================================================================
        # 2. Fetch Latest Live Snapshots for Production Data
        # =====================================================================

        # Get latest snapshot per asset
        # Note: Schema only has: id, asset_id, snapshot_timestamp, current_output, target_output, output_variance, status
        snapshots_response = client.table("live_snapshots").select(
            "id, asset_id, snapshot_timestamp, current_output, target_output, output_variance, status"
        ).order("snapshot_timestamp", desc=True).execute()

        # Group by asset, taking latest per asset
        latest_snapshots = {}
        for snapshot in snapshots_response.data or []:
            asset_id = snapshot.get("asset_id")
            if asset_id and asset_id not in latest_snapshots:
                latest_snapshots[asset_id] = snapshot

        # Aggregate production metrics
        total_output = 0
        total_target = 0
        total_oee = 0.0
        oee_count = 0

        running_count = 0
        idle_count = 0
        down_count = 0

        active_downtime_list = []
        total_financial_loss = Decimal("0")

        for asset_id, snapshot in latest_snapshots.items():
            # Track latest timestamp
            ts = snapshot.get("snapshot_timestamp")
            if ts:
                if latest_snapshot_time is None or ts > latest_snapshot_time:
                    latest_snapshot_time = ts

            # Production metrics
            current = snapshot.get("current_output") or 0
            target = snapshot.get("target_output") or 0
            total_output += current
            total_target += target

            # OEE - calculate from output variance if available (schema doesn't have oee_percentage)
            # OEE approximation: current_output / target_output * 100
            if current > 0 and target > 0:
                oee = (current / target) * 100
                total_oee += oee
                oee_count += 1

            # Machine status based on snapshot status field
            status_val = snapshot.get("status", "on_target")
            if status_val == "down":
                down_count += 1
            elif status_val == "idle":
                idle_count += 1
            else:
                # "ahead", "on_target", "behind" all mean running
                running_count += 1

            # Note: downtime_reason and financial_loss_dollars are not in the schema
            # These would need to be calculated from other sources or added to schema

        # Calculate aggregated metrics
        output_percentage = 0.0
        if total_target > 0:
            output_percentage = round((total_output / total_target) * 100, 1)

        avg_oee = 0.0
        if oee_count > 0:
            avg_oee = round(total_oee / oee_count, 1)

        total_machines = len(assets_map)

        # Assets without recent snapshots are considered idle (no data)
        assets_with_snapshots = set(latest_snapshots.keys())
        assets_without_snapshots = set(assets_map.keys()) - assets_with_snapshots
        idle_count += len(assets_without_snapshots)

        # =====================================================================
        # 3. Fetch Safety Events (Active/Unresolved)
        # =====================================================================

        safety_response = client.table("safety_events").select(
            "id, asset_id, event_timestamp, reason_code, severity, is_resolved"
        ).eq("is_resolved", False).execute()

        active_incidents = []
        for event in safety_response.data or []:
            asset_id = event.get("asset_id")
            asset_info = assets_map.get(asset_id, {})
            active_incidents.append(
                SafetyIncident(
                    id=str(event.get("id")),
                    asset_name=asset_info.get("name", "Unknown"),
                    detected_at=event.get("event_timestamp", response_timestamp),
                    severity=event.get("severity", "medium"),
                )
            )

        has_active_incident = len(active_incidents) > 0

        # =====================================================================
        # 4. Calculate Financial Context
        # =====================================================================

        # Shift-to-date loss: total accumulated from all snapshots
        shift_to_date_loss = float(total_financial_loss.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ))

        # Rolling 15-min loss: latest snapshot financial values only
        # (This is an approximation - ideally would sum last 15 min of snapshots)
        rolling_15_min_loss = 0.0
        fifteen_min_ago = now - timedelta(minutes=15)

        for asset_id, snapshot in latest_snapshots.items():
            ts_str = snapshot.get("snapshot_timestamp", "")
            try:
                ts = ts_str.replace("Z", "+00:00")
                if "+" not in ts and "-" not in ts[10:]:
                    ts = ts + "+00:00"
                snapshot_dt = datetime.fromisoformat(ts)
                snapshot_dt = snapshot_dt.replace(tzinfo=None)

                if snapshot_dt >= fifteen_min_ago:
                    loss = snapshot.get("financial_loss_dollars") or 0
                    rolling_15_min_loss += float(loss)
            except (ValueError, TypeError):
                continue

        rolling_15_min_loss = round(rolling_15_min_loss, 2)

        # =====================================================================
        # 5. Calculate Data Freshness
        # =====================================================================

        data_age, is_stale = calculate_data_age(latest_snapshot_time)

        # =====================================================================
        # 6. Build Response
        # =====================================================================

        return LivePulseResponse(
            timestamp=response_timestamp,
            production=ProductionData(
                current_output=total_output,
                target_output=total_target,
                output_percentage=output_percentage,
                oee_percentage=avg_oee,
                machine_status=MachineStatus(
                    running=running_count,
                    idle=idle_count,
                    down=down_count,
                    total=total_machines,
                ),
                active_downtime=active_downtime_list[:5],  # Limit to 5 for display
            ),
            financial=FinancialData(
                shift_to_date_loss=shift_to_date_loss,
                rolling_15_min_loss=rolling_15_min_loss,
                currency=settings.financial_currency,
            ),
            safety=SafetyData(
                has_active_incident=has_active_incident,
                active_incidents=active_incidents,
            ),
            meta=MetaData(
                data_age=data_age,
                is_stale=is_stale,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching live pulse data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live pulse data"
        )
