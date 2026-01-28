"""
Safety Alert Service

Service for managing safety events and alerts for Story 2.6.
Provides:
- Safety event retrieval with financial context
- Active alert management
- Acknowledgement handling
- Dashboard status aggregation

Integrates with cost_centers for financial impact calculation (FR5).
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.core.config import get_settings
from app.models.safety import (
    AcknowledgeResponse,
    ActiveSafetyAlertsResponse,
    DashboardStatusResponse,
    SafetyEventResponse,
    SafetyEventsResponse,
    SeverityLevel,
)

logger = logging.getLogger(__name__)

# Default hourly rate when cost center data is unavailable
DEFAULT_HOURLY_RATE = 150.0


class SafetyAlertService:
    """
    Service for safety event and alert management.

    Provides methods for:
    - Fetching safety events with asset details
    - Calculating financial impact using cost_centers
    - Managing acknowledgements
    - Aggregating dashboard status
    """

    def __init__(self, supabase_client):
        """
        Initialize the service with a Supabase client.

        Args:
            supabase_client: Authenticated Supabase client instance
        """
        self.client = supabase_client
        self.settings = get_settings()
        self._assets_cache: Dict[str, dict] = {}
        self._cost_centers_cache: Dict[str, float] = {}

    async def _get_assets_map(self) -> Dict[str, dict]:
        """
        Get a mapping of asset_id to asset info with caching.

        Returns:
            Dict mapping asset_id to {name, area, source_id}
        """
        if self._assets_cache:
            return self._assets_cache

        response = self.client.table("assets").select(
            "id, name, area, source_id"
        ).execute()

        if response.data:
            self._assets_cache = {
                asset["id"]: {
                    "name": asset.get("name", "Unknown"),
                    "area": asset.get("area"),
                    "source_id": asset.get("source_id"),
                }
                for asset in response.data
            }

        return self._assets_cache

    async def _get_cost_centers_map(self) -> Dict[str, float]:
        """
        Get a mapping of asset_id to standard_hourly_rate.

        Returns:
            Dict mapping asset_id to hourly rate
        """
        if self._cost_centers_cache:
            return self._cost_centers_cache

        response = self.client.table("cost_centers").select(
            "asset_id, standard_hourly_rate"
        ).execute()

        if response.data:
            self._cost_centers_cache = {
                cc["asset_id"]: float(cc.get("standard_hourly_rate", DEFAULT_HOURLY_RATE) or DEFAULT_HOURLY_RATE)
                for cc in response.data
            }

        return self._cost_centers_cache

    def _calculate_financial_impact(
        self,
        duration_minutes: Optional[int],
        asset_id: Optional[str],
        cost_centers_map: Dict[str, float]
    ) -> Optional[float]:
        """
        Calculate financial impact for a safety event.

        Formula: (duration_minutes / 60) * standard_hourly_rate

        Args:
            duration_minutes: Duration of the safety event in minutes
            asset_id: The asset ID to look up hourly rate
            cost_centers_map: Mapping of asset IDs to hourly rates

        Returns:
            Financial impact in dollars, or None if duration unknown
        """
        if duration_minutes is None or duration_minutes <= 0:
            return None

        hourly_rate = DEFAULT_HOURLY_RATE
        if asset_id and asset_id in cost_centers_map:
            hourly_rate = cost_centers_map[asset_id]

        return round((duration_minutes / 60.0) * hourly_rate, 2)

    def _build_safety_event_response(
        self,
        record: dict,
        assets_map: Dict[str, dict],
        cost_centers_map: Dict[str, float],
    ) -> SafetyEventResponse:
        """
        Build a SafetyEventResponse from a database record.

        Args:
            record: Raw record from safety_events table
            assets_map: Asset ID to info mapping
            cost_centers_map: Cost center ID to rate mapping

        Returns:
            SafetyEventResponse with all fields populated
        """
        asset_id = record.get("asset_id")
        asset_info = assets_map.get(asset_id, {"name": "Unknown", "area": None})

        # Calculate financial impact if duration is known (lookup by asset_id)
        duration_minutes = record.get("duration_minutes")
        financial_impact = self._calculate_financial_impact(
            duration_minutes, asset_id, cost_centers_map
        )

        return SafetyEventResponse(
            id=UUID(record["id"]),
            asset_id=UUID(asset_id),
            asset_name=asset_info.get("name", "Unknown"),
            area=asset_info.get("area"),
            event_timestamp=record.get("event_timestamp"),
            reason_code=record.get("reason_code", "Safety Issue"),
            severity=SeverityLevel(record.get("severity", "critical")),
            description=record.get("description"),
            source_record_id=record.get("source_record_id"),
            duration_minutes=duration_minutes,
            acknowledged=record.get("is_resolved", False),
            acknowledged_at=record.get("resolved_at"),
            acknowledged_by=UUID(record["resolved_by"]) if record.get("resolved_by") else None,
            financial_impact=financial_impact,
            created_at=record.get("created_at"),
        )

    async def get_safety_events(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        asset_id: Optional[str] = None,
    ) -> SafetyEventsResponse:
        """
        Get recent safety events with optional filtering.

        Args:
            limit: Maximum number of events to return (default 50)
            since: Only return events after this timestamp
            asset_id: Filter by specific asset

        Returns:
            SafetyEventsResponse with events and count
        """
        try:
            query = self.client.table("safety_events").select("*")

            if since:
                query = query.gte("event_timestamp", since.isoformat())

            if asset_id:
                query = query.eq("asset_id", asset_id)

            # Order by timestamp descending (most recent first)
            query = query.order("event_timestamp", desc=True).limit(limit)

            response = query.execute()
            records = response.data or []

            # Load asset and cost center mappings
            assets_map = await self._get_assets_map()
            cost_centers_map = await self._get_cost_centers_map()

            # Build response objects
            events = [
                self._build_safety_event_response(record, assets_map, cost_centers_map)
                for record in records
            ]

            return SafetyEventsResponse(
                events=events,
                count=len(events),
                last_updated=datetime.utcnow().isoformat() + "Z",
            )

        except Exception as e:
            logger.error(f"Error fetching safety events: {e}")
            raise

    async def get_active_alerts(self) -> ActiveSafetyAlertsResponse:
        """
        Get currently active (unacknowledged) safety alerts.

        Returns:
            ActiveSafetyAlertsResponse with active alerts
        """
        try:
            # Query for unacknowledged safety events
            # Check both 'acknowledged' (new field) and 'is_resolved' (existing field)
            query = self.client.table("safety_events").select("*")
            query = query.eq("is_resolved", False)
            query = query.order("event_timestamp", desc=True)

            response = query.execute()
            records = response.data or []

            # Load mappings
            assets_map = await self._get_assets_map()
            cost_centers_map = await self._get_cost_centers_map()

            # Build response objects
            events = [
                self._build_safety_event_response(record, assets_map, cost_centers_map)
                for record in records
            ]

            return ActiveSafetyAlertsResponse(
                events=events,
                count=len(events),
                last_updated=datetime.utcnow().isoformat() + "Z",
            )

        except Exception as e:
            logger.error(f"Error fetching active safety alerts: {e}")
            raise

    async def acknowledge_event(
        self,
        event_id: str,
        acknowledged_by: Optional[str] = None,
    ) -> AcknowledgeResponse:
        """
        Acknowledge a safety event.

        Args:
            event_id: The safety event ID to acknowledge
            acknowledged_by: Optional user ID who acknowledged

        Returns:
            AcknowledgeResponse with updated event
        """
        try:
            # Update the safety event
            update_data = {
                "is_resolved": True,
                "resolved_at": datetime.utcnow().isoformat(),
            }

            if acknowledged_by:
                update_data["resolved_by"] = acknowledged_by

            response = self.client.table("safety_events").update(
                update_data
            ).eq("id", event_id).execute()

            if not response.data:
                return AcknowledgeResponse(
                    success=False,
                    event=None,
                    message=f"Safety event {event_id} not found",
                )

            # Build response with updated event
            record = response.data[0]
            assets_map = await self._get_assets_map()
            cost_centers_map = await self._get_cost_centers_map()

            event = self._build_safety_event_response(
                record, assets_map, cost_centers_map
            )

            logger.info(f"Safety event {event_id} acknowledged")

            return AcknowledgeResponse(
                success=True,
                event=event,
                message="Safety event acknowledged successfully",
            )

        except Exception as e:
            logger.error(f"Error acknowledging safety event: {e}")
            return AcknowledgeResponse(
                success=False,
                event=None,
                message=f"Failed to acknowledge event: {str(e)}",
            )

    async def get_dashboard_status(self) -> DashboardStatusResponse:
        """
        Get dashboard status including safety alert count.

        Returns:
            DashboardStatusResponse with safety alert count and asset status
        """
        try:
            # Get active safety alerts count
            safety_query = self.client.table("safety_events").select(
                "id", count="exact"
            ).eq("is_resolved", False)
            safety_response = safety_query.execute()
            safety_count = safety_response.count or 0

            # Get latest snapshots for asset status
            snapshots_response = self.client.table("live_snapshots").select(
                "asset_id, status, snapshot_timestamp"
            ).order("snapshot_timestamp", desc=True).execute()

            # Get latest snapshot per asset
            latest_by_asset = {}
            for snapshot in (snapshots_response.data or []):
                asset_id = snapshot["asset_id"]
                if asset_id not in latest_by_asset:
                    latest_by_asset[asset_id] = snapshot

            # Count by status
            on_target = 0
            below_target = 0
            above_target = 0
            last_poll_time = None

            for snapshot in latest_by_asset.values():
                status = snapshot.get("status", "")
                if status == "on_target":
                    on_target += 1
                elif status in ("behind", "below_target"):
                    below_target += 1
                elif status in ("ahead", "above_target"):
                    above_target += 1

                # Track latest poll time
                ts = snapshot.get("snapshot_timestamp")
                if ts and (last_poll_time is None or ts > last_poll_time):
                    last_poll_time = ts

            return DashboardStatusResponse(
                safety_alert_count=safety_count,
                safety_alerts_active=safety_count > 0,
                total_assets=len(latest_by_asset),
                assets_on_target=on_target,
                assets_below_target=below_target,
                assets_above_target=above_target,
                last_poll_time=last_poll_time,
            )

        except Exception as e:
            logger.error(f"Error fetching dashboard status: {e}")
            raise

    async def get_safety_event_by_id(
        self,
        event_id: str,
    ) -> Optional[SafetyEventResponse]:
        """
        Get a single safety event by ID.

        Args:
            event_id: The safety event ID

        Returns:
            SafetyEventResponse or None if not found
        """
        try:
            response = self.client.table("safety_events").select("*").eq(
                "id", event_id
            ).execute()

            if not response.data:
                return None

            record = response.data[0]
            assets_map = await self._get_assets_map()
            cost_centers_map = await self._get_cost_centers_map()

            return self._build_safety_event_response(
                record, assets_map, cost_centers_map
            )

        except Exception as e:
            logger.error(f"Error fetching safety event {event_id}: {e}")
            raise
