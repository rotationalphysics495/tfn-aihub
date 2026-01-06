"""
Downtime Analysis Service

Service class for calculating Pareto distribution and financial impact
of downtime events for Story 2.5 - Downtime Pareto Analysis.

Implements:
- Pareto calculation by reason code
- Financial impact calculation using cost_centers.standard_hourly_rate
- Safety event detection and highlighting
- Filtering by asset, area, shift, and date range
"""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from app.core.config import get_settings
from app.models.downtime import (
    CostOfLossSummary,
    DataSource,
    DowntimeEvent,
    ParetoItem,
    ParetoResponse,
    SafetyEventDetail,
)

logger = logging.getLogger(__name__)

# Safety-related reason code patterns
SAFETY_KEYWORDS = [
    "safety",
    "safety issue",
    "emergency stop",
    "e-stop",
    "hazard",
    "injury",
    "accident",
]

# Default hourly rate when cost center data is unavailable
DEFAULT_HOURLY_RATE = 150.0


class DowntimeAnalysisService:
    """
    Service for downtime Pareto analysis and financial impact calculations.

    Provides methods for:
    - Fetching and transforming downtime events from analytical cache
    - Calculating Pareto distribution by reason code
    - Computing financial impact using cost center rates
    - Identifying and prioritizing safety-related events
    """

    def __init__(self, supabase_client):
        """
        Initialize the service with a Supabase client.

        Args:
            supabase_client: Authenticated Supabase client instance
        """
        self.client = supabase_client
        self.settings = get_settings()
        self._assets_cache: Dict = {}
        self._cost_centers_cache: Dict = {}

    async def get_assets_map(self) -> Dict[str, dict]:
        """
        Get a mapping of asset_id to asset info with caching.

        Returns:
            Dict mapping asset_id to {name, area, source_id, cost_center_id}
        """
        if self._assets_cache:
            return self._assets_cache

        response = self.client.table("assets").select(
            "id, name, area, source_id, cost_center_id"
        ).execute()

        if response.data:
            self._assets_cache = {
                asset["id"]: {
                    "name": asset.get("name", "Unknown"),
                    "area": asset.get("area"),
                    "source_id": asset.get("source_id"),
                    "cost_center_id": asset.get("cost_center_id"),
                }
                for asset in response.data
            }

        return self._assets_cache

    async def get_cost_centers_map(self) -> Dict[str, float]:
        """
        Get a mapping of cost_center_id to standard_hourly_rate.

        Returns:
            Dict mapping cost_center_id to hourly rate
        """
        if self._cost_centers_cache:
            return self._cost_centers_cache

        response = self.client.table("cost_centers").select(
            "id, standard_hourly_rate"
        ).execute()

        if response.data:
            self._cost_centers_cache = {
                cc["id"]: float(cc.get("standard_hourly_rate", DEFAULT_HOURLY_RATE) or DEFAULT_HOURLY_RATE)
                for cc in response.data
            }

        return self._cost_centers_cache

    def is_safety_related(self, reason_code: str) -> bool:
        """
        Check if a reason code is safety-related.

        Args:
            reason_code: The downtime reason code

        Returns:
            True if the reason code matches safety patterns
        """
        if not reason_code:
            return False

        reason_lower = reason_code.lower()
        return any(keyword in reason_lower for keyword in SAFETY_KEYWORDS)

    def calculate_financial_impact(
        self,
        downtime_minutes: int,
        cost_center_id: Optional[str],
        cost_centers_map: Dict[str, float]
    ) -> float:
        """
        Calculate financial impact for downtime.

        Formula: (downtime_minutes / 60) * standard_hourly_rate

        Args:
            downtime_minutes: Duration of downtime in minutes
            cost_center_id: The cost center ID for the asset
            cost_centers_map: Mapping of cost center IDs to hourly rates

        Returns:
            Financial impact in dollars
        """
        hourly_rate = DEFAULT_HOURLY_RATE
        if cost_center_id and cost_center_id in cost_centers_map:
            hourly_rate = cost_centers_map[cost_center_id]

        return round((downtime_minutes / 60.0) * hourly_rate, 2)

    async def get_downtime_from_daily_summaries(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        asset_id: Optional[str] = None,
        area: Optional[str] = None,
    ) -> List[dict]:
        """
        Get downtime data from daily_summaries table (T-1 data).

        Args:
            start_date: Start of date range (defaults to yesterday)
            end_date: End of date range (defaults to yesterday)
            asset_id: Optional asset filter
            area: Optional area filter

        Returns:
            List of downtime records from daily summaries
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=1)
        if end_date is None:
            end_date = start_date

        query = self.client.table("daily_summaries").select("*")
        query = query.gte("report_date", start_date.isoformat())
        query = query.lte("report_date", end_date.isoformat())

        if asset_id:
            query = query.eq("asset_id", asset_id)

        response = query.execute()
        records = response.data or []

        # If area filter, we need to filter after fetching assets
        if area:
            assets_map = await self.get_assets_map()
            records = [
                r for r in records
                if r.get("asset_id") in assets_map and
                assets_map[r["asset_id"]].get("area", "").lower() == area.lower()
            ]

        return records

    async def get_downtime_from_live_snapshots(
        self,
        asset_id: Optional[str] = None,
        area: Optional[str] = None,
    ) -> List[dict]:
        """
        Get the most recent live snapshot for each asset (T-15m data).

        Args:
            asset_id: Optional asset filter
            area: Optional area filter

        Returns:
            List of latest snapshots per asset
        """
        query = self.client.table("live_snapshots").select("*")

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

        records = list(latest_by_asset.values())

        # Apply area filter if specified
        if area:
            assets_map = await self.get_assets_map()
            records = [
                r for r in records
                if r.get("asset_id") in assets_map and
                assets_map[r["asset_id"]].get("area", "").lower() == area.lower()
            ]

        return records

    async def get_safety_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        asset_id: Optional[str] = None,
    ) -> List[dict]:
        """
        Get safety events from the safety_events table.

        Args:
            start_date: Start of date range
            end_date: End of date range
            asset_id: Optional asset filter

        Returns:
            List of safety event records
        """
        query = self.client.table("safety_events").select("*")

        if start_date:
            query = query.gte("event_timestamp", f"{start_date.isoformat()}T00:00:00Z")
        if end_date:
            query = query.lte("event_timestamp", f"{end_date.isoformat()}T23:59:59Z")
        if asset_id:
            query = query.eq("asset_id", asset_id)

        query = query.order("event_timestamp", desc=True)

        response = query.execute()
        return response.data or []

    async def transform_to_downtime_events(
        self,
        raw_records: List[dict],
        data_source: DataSource,
        include_safety: bool = True,
    ) -> List[DowntimeEvent]:
        """
        Transform raw database records into DowntimeEvent models.

        Args:
            raw_records: Raw records from database
            data_source: Source of the data
            include_safety: Whether to include safety event details

        Returns:
            List of DowntimeEvent objects with financial impact calculated
        """
        assets_map = await self.get_assets_map()
        cost_centers_map = await self.get_cost_centers_map()
        events = []

        for record in raw_records:
            asset_id = record.get("asset_id")
            if not asset_id or asset_id not in assets_map:
                continue

            asset_info = assets_map[asset_id]

            # Get downtime minutes from appropriate field
            if data_source == DataSource.DAILY_SUMMARIES:
                downtime_minutes = record.get("downtime_minutes", 0) or 0
                # For daily summaries, create a synthetic reason code
                reason_code = record.get("reason_code", "Unspecified")
                if not reason_code or reason_code == "null":
                    reason_code = "Unspecified"
                event_timestamp = f"{record.get('report_date')}T00:00:00Z"
            else:  # Live snapshots
                # Live snapshots might not have downtime, use output_variance as indicator
                downtime_minutes = record.get("downtime_minutes", 0) or 0
                reason_code = record.get("reason_code", "Unspecified") or "Unspecified"
                event_timestamp = record.get("snapshot_timestamp", datetime.utcnow().isoformat())

            # Skip if no actual downtime
            if downtime_minutes <= 0:
                continue

            # Calculate financial impact
            cost_center_id = asset_info.get("cost_center_id")
            financial_impact = self.calculate_financial_impact(
                downtime_minutes, cost_center_id, cost_centers_map
            )

            # Check if safety-related
            is_safety = self.is_safety_related(reason_code)

            event = DowntimeEvent(
                id=record.get("id"),
                asset_id=asset_id,
                asset_name=asset_info["name"],
                area=asset_info.get("area"),
                reason_code=reason_code,
                duration_minutes=downtime_minutes,
                event_timestamp=event_timestamp,
                end_timestamp=None,  # Calculated if needed
                financial_impact=financial_impact,
                is_safety_related=is_safety,
                severity=record.get("severity") if is_safety else None,
                description=record.get("description"),
            )
            events.append(event)

        # Sort by duration descending, with safety events first
        events.sort(key=lambda e: (not e.is_safety_related, -e.duration_minutes))

        return events

    def calculate_pareto(
        self,
        events: List[DowntimeEvent],
        group_by: str = "reason_code"
    ) -> Tuple[List[ParetoItem], int]:
        """
        Calculate Pareto distribution from downtime events.

        Groups events by the specified field (default: reason_code) and
        calculates total minutes, percentage, and cumulative percentage.

        Args:
            events: List of downtime events
            group_by: Field to group by (default: "reason_code")

        Returns:
            Tuple of (Pareto items sorted by descending duration, index of 80% threshold)
        """
        if not events:
            return [], None

        # Aggregate by group_by field
        aggregates: Dict[str, dict] = defaultdict(
            lambda: {
                "total_minutes": 0,
                "financial_impact": 0.0,
                "event_count": 0,
                "is_safety_related": False,
            }
        )

        for event in events:
            key = getattr(event, group_by, "Unknown") or "Unknown"
            aggregates[key]["total_minutes"] += event.duration_minutes
            aggregates[key]["financial_impact"] += event.financial_impact
            aggregates[key]["event_count"] += 1
            if event.is_safety_related:
                aggregates[key]["is_safety_related"] = True

        # Calculate total downtime for percentages
        total_minutes = sum(agg["total_minutes"] for agg in aggregates.values())
        if total_minutes == 0:
            return [], None

        # Build Pareto items sorted by descending total minutes
        pareto_items = []
        for reason_code, agg in aggregates.items():
            percentage = (agg["total_minutes"] / total_minutes) * 100
            pareto_items.append(
                ParetoItem(
                    reason_code=reason_code,
                    total_minutes=agg["total_minutes"],
                    percentage=round(percentage, 1),
                    cumulative_percentage=0.0,  # Will be calculated next
                    financial_impact=round(agg["financial_impact"], 2),
                    event_count=agg["event_count"],
                    is_safety_related=agg["is_safety_related"],
                )
            )

        # Sort by descending total minutes (highest downtime first)
        pareto_items.sort(key=lambda x: -x.total_minutes)

        # Calculate cumulative percentages and find 80% threshold
        cumulative = 0.0
        threshold_80_index = None
        for i, item in enumerate(pareto_items):
            cumulative += item.percentage
            item.cumulative_percentage = round(cumulative, 1)
            if threshold_80_index is None and cumulative >= 80.0:
                threshold_80_index = i

        return pareto_items, threshold_80_index

    def build_cost_of_loss_summary(
        self,
        events: List[DowntimeEvent],
        pareto_items: List[ParetoItem],
        data_source: str,
        last_updated: str,
    ) -> CostOfLossSummary:
        """
        Build the Cost of Loss summary widget data.

        Args:
            events: List of downtime events
            pareto_items: Calculated Pareto items
            data_source: Data source used
            last_updated: Timestamp of data freshness

        Returns:
            CostOfLossSummary with aggregated metrics
        """
        total_financial_loss = sum(e.financial_impact for e in events)
        total_downtime_minutes = sum(e.duration_minutes for e in events)
        total_downtime_hours = round(total_downtime_minutes / 60.0, 2)

        # Get top reason from pareto
        top_reason_code = None
        top_reason_percentage = None
        if pareto_items:
            top_reason_code = pareto_items[0].reason_code
            top_reason_percentage = pareto_items[0].percentage

        # Count safety events
        safety_events = [e for e in events if e.is_safety_related]
        safety_events_count = len(safety_events)
        safety_downtime_minutes = sum(e.duration_minutes for e in safety_events)

        return CostOfLossSummary(
            total_financial_loss=round(total_financial_loss, 2),
            total_downtime_minutes=total_downtime_minutes,
            total_downtime_hours=total_downtime_hours,
            top_reason_code=top_reason_code,
            top_reason_percentage=top_reason_percentage,
            safety_events_count=safety_events_count,
            safety_downtime_minutes=safety_downtime_minutes,
            data_source=data_source,
            last_updated=last_updated,
        )

    async def get_safety_event_detail(self, event_id: str) -> Optional[SafetyEventDetail]:
        """
        Get detailed information about a safety event.

        Args:
            event_id: The safety event ID

        Returns:
            SafetyEventDetail or None if not found
        """
        response = self.client.table("safety_events").select("*").eq("id", event_id).execute()

        if not response.data:
            return None

        record = response.data[0]
        assets_map = await self.get_assets_map()
        asset_id = record.get("asset_id")
        asset_info = assets_map.get(asset_id, {"name": "Unknown"})

        return SafetyEventDetail(
            id=record.get("id"),
            asset_id=asset_id,
            asset_name=asset_info.get("name", "Unknown"),
            area=asset_info.get("area"),
            event_timestamp=record.get("event_timestamp"),
            reason_code=record.get("reason_code"),
            severity=record.get("severity", "unknown"),
            description=record.get("description"),
            duration_minutes=None,  # Would need to calculate from paired events
            financial_impact=None,  # Would need cost center data
            is_resolved=record.get("is_resolved", False),
            resolved_at=record.get("resolved_at"),
        )
