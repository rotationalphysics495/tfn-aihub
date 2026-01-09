"""
Supabase DataSource Implementation (Story 5.2)

Implements the DataSource protocol for Supabase PostgreSQL.

AC#2: Supabase DataSource Implementation
- Connects using existing Supabase client from config
- All protocol methods are implemented
- Queries use existing Supabase table structures

AC#4: Asset Data Methods
AC#5: OEE Data Methods
AC#6: Downtime Data Methods
AC#7: Live Data Methods
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

from app.core.config import get_settings
from app.services.agent.data_source.protocol import (
    Asset,
    DataResult,
    DowntimeEvent,
    OEEMetrics,
    ProductionStatus,
    SafetyEvent,
    ShiftTarget,
)
from app.services.agent.data_source.exceptions import (
    DataSourceConfigurationError,
    DataSourceConnectionError,
    DataSourceQueryError,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class SupabaseDataSource:
    """
    Supabase implementation of the DataSource protocol.

    AC#2: Supabase DataSource Implementation
    - Connects using existing Supabase client from config
    - All protocol methods are implemented
    - Queries use existing Supabase table structures
    """

    def __init__(self, client: Optional[Client] = None):
        """
        Initialize SupabaseDataSource.

        Args:
            client: Optional Supabase client for testing.
                   If None, creates client from settings.
        """
        self.source_name = "supabase"
        self._client = client

    @property
    def client(self) -> Client:
        """Get or create Supabase client (lazy initialization)."""
        if self._client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise DataSourceConfigurationError(
                    "Supabase URL and key must be configured",
                    source_name=self.source_name,
                )
            try:
                self._client = create_client(
                    settings.supabase_url, settings.supabase_key
                )
            except Exception as e:
                raise DataSourceConnectionError(
                    f"Failed to connect to Supabase: {str(e)}",
                    source_name=self.source_name,
                )
        return self._client

    def _create_result(
        self,
        data: Any,
        table_name: str,
        query: Optional[str] = None,
    ) -> DataResult:
        """
        Create a DataResult wrapper for query responses.

        AC#3: Wrap all responses in DataResult
        """
        row_count = 0
        if data is not None:
            if isinstance(data, list):
                row_count = len(data)
            elif data:
                row_count = 1

        return DataResult(
            data=data,
            source_name=self.source_name,
            table_name=table_name,
            query_timestamp=_utcnow(),
            query=query,
            row_count=row_count,
        )

    def _parse_asset(self, row: Dict[str, Any]) -> Asset:
        """Parse a database row into an Asset model."""
        return Asset(
            id=str(row["id"]),
            name=row["name"],
            source_id=row["source_id"],
            area=row.get("area"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _parse_oee_metrics(self, row: Dict[str, Any]) -> OEEMetrics:
        """Parse a database row into an OEEMetrics model."""
        return OEEMetrics(
            id=str(row["id"]),
            asset_id=str(row["asset_id"]),
            report_date=row["report_date"],
            oee_percentage=(
                Decimal(str(row["oee_percentage"]))
                if row.get("oee_percentage") is not None
                else None
            ),
            availability=(
                Decimal(str(row["availability"]))
                if row.get("availability") is not None
                else None
            ),
            performance=(
                Decimal(str(row["performance"]))
                if row.get("performance") is not None
                else None
            ),
            quality=(
                Decimal(str(row["quality"]))
                if row.get("quality") is not None
                else None
            ),
            actual_output=row.get("actual_output"),
            target_output=row.get("target_output"),
            downtime_minutes=row.get("downtime_minutes"),
            waste_count=row.get("waste_count"),
            financial_loss_dollars=(
                Decimal(str(row["financial_loss_dollars"]))
                if row.get("financial_loss_dollars") is not None
                else None
            ),
            smart_summary_text=row.get("smart_summary_text"),
        )

    def _parse_production_status(self, row: Dict[str, Any]) -> ProductionStatus:
        """Parse a database row into a ProductionStatus model."""
        # Handle nested asset data from joins
        asset_data = row.get("assets", {}) or {}

        return ProductionStatus(
            id=str(row["id"]),
            asset_id=str(row["asset_id"]),
            asset_name=asset_data.get("name"),
            area=asset_data.get("area"),
            snapshot_timestamp=row["snapshot_timestamp"],
            current_output=row.get("current_output"),
            target_output=row.get("target_output"),
            output_variance=row.get("output_variance"),
            status=row["status"],
        )

    def _parse_shift_target(self, row: Dict[str, Any]) -> ShiftTarget:
        """Parse a database row into a ShiftTarget model."""
        return ShiftTarget(
            id=str(row["id"]),
            asset_id=str(row["asset_id"]),
            target_output=row["target_output"],
            shift=row.get("shift"),
            effective_date=row.get("effective_date"),
        )

    def _parse_safety_event(self, row: Dict[str, Any]) -> SafetyEvent:
        """Parse a database row into a SafetyEvent model."""
        asset_data = row.get("assets", {}) or {}

        return SafetyEvent(
            id=str(row["id"]),
            asset_id=str(row["asset_id"]),
            asset_name=asset_data.get("name"),
            event_timestamp=row["event_timestamp"],
            reason_code=row["reason_code"],
            severity=row["severity"],
            description=row.get("description"),
            is_resolved=row.get("is_resolved", False),
            resolved_at=row.get("resolved_at"),
        )

    # =========================================================================
    # Asset Methods (AC#4)
    # =========================================================================

    async def get_asset(self, asset_id: str) -> DataResult:
        """
        Get asset by ID.

        AC#4: Asset Data Methods
        """
        try:
            result = (
                self.client.table("assets")
                .select("*")
                .eq("id", asset_id)
                .limit(1)
                .execute()
            )

            asset = None
            if result.data and len(result.data) > 0:
                asset = self._parse_asset(result.data[0])

            return self._create_result(
                data=asset,
                table_name="assets",
                query=f"SELECT * FROM assets WHERE id = '{asset_id}'",
            )

        except Exception as e:
            logger.error(f"Failed to get asset {asset_id}: {e}")
            raise DataSourceQueryError(
                f"Failed to get asset: {str(e)}",
                source_name=self.source_name,
                table_name="assets",
            )

    async def get_asset_by_name(self, name: str) -> DataResult:
        """
        Get asset by name with fuzzy matching.

        AC#4: Fuzzy name matching for user queries
        """
        try:
            # Try exact case-insensitive match first
            result = (
                self.client.table("assets")
                .select("*")
                .ilike("name", name)
                .limit(1)
                .execute()
            )

            if not result.data:
                # Try partial match with wildcards
                result = (
                    self.client.table("assets")
                    .select("*")
                    .ilike("name", f"%{name}%")
                    .limit(1)
                    .execute()
                )

            asset = None
            if result.data and len(result.data) > 0:
                asset = self._parse_asset(result.data[0])

            return self._create_result(
                data=asset,
                table_name="assets",
                query=f"SELECT * FROM assets WHERE name ILIKE '%{name}%'",
            )

        except Exception as e:
            logger.error(f"Failed to get asset by name '{name}': {e}")
            raise DataSourceQueryError(
                f"Failed to get asset by name: {str(e)}",
                source_name=self.source_name,
                table_name="assets",
            )

    async def get_assets_by_area(self, area: str) -> DataResult:
        """
        Get all assets in an area.

        AC#4: Asset Data Methods
        """
        try:
            result = (
                self.client.table("assets")
                .select("*")
                .ilike("area", area)
                .order("name")
                .execute()
            )

            assets = [self._parse_asset(row) for row in (result.data or [])]

            return self._create_result(
                data=assets,
                table_name="assets",
                query=f"SELECT * FROM assets WHERE area ILIKE '{area}'",
            )

        except Exception as e:
            logger.error(f"Failed to get assets by area '{area}': {e}")
            raise DataSourceQueryError(
                f"Failed to get assets by area: {str(e)}",
                source_name=self.source_name,
                table_name="assets",
            )

    async def get_similar_assets(self, name: str, limit: int = 5) -> DataResult:
        """
        Get assets with similar names for suggestions.

        AC#4: Fuzzy name matching support
        """
        try:
            result = (
                self.client.table("assets")
                .select("*")
                .ilike("name", f"%{name}%")
                .limit(limit)
                .execute()
            )

            assets = [self._parse_asset(row) for row in (result.data or [])]

            return self._create_result(
                data=assets,
                table_name="assets",
                query=f"SELECT * FROM assets WHERE name ILIKE '%{name}%' LIMIT {limit}",
            )

        except Exception as e:
            logger.error(f"Failed to get similar assets for '{name}': {e}")
            raise DataSourceQueryError(
                f"Failed to get similar assets: {str(e)}",
                source_name=self.source_name,
                table_name="assets",
            )

    async def get_all_assets(self) -> DataResult:
        """
        Get all assets in the system.
        """
        try:
            result = (
                self.client.table("assets")
                .select("*")
                .order("name")
                .execute()
            )

            assets = [self._parse_asset(row) for row in (result.data or [])]

            return self._create_result(
                data=assets,
                table_name="assets",
                query="SELECT * FROM assets ORDER BY name",
            )

        except Exception as e:
            logger.error(f"Failed to get all assets: {e}")
            raise DataSourceQueryError(
                f"Failed to get all assets: {str(e)}",
                source_name=self.source_name,
                table_name="assets",
            )

    # =========================================================================
    # OEE Methods (AC#5)
    # =========================================================================

    async def get_oee(
        self,
        asset_id: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get OEE metrics for an asset in date range.

        AC#5: OEE Data Methods - includes availability, performance, quality breakdown
        """
        try:
            result = (
                self.client.table("daily_summaries")
                .select("*")
                .eq("asset_id", asset_id)
                .gte("report_date", start_date.isoformat())
                .lte("report_date", end_date.isoformat())
                .order("report_date", desc=True)
                .execute()
            )

            metrics = [self._parse_oee_metrics(row) for row in (result.data or [])]

            return self._create_result(
                data=metrics,
                table_name="daily_summaries",
                query=(
                    f"SELECT * FROM daily_summaries "
                    f"WHERE asset_id = '{asset_id}' "
                    f"AND report_date BETWEEN '{start_date}' AND '{end_date}'"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get OEE for asset {asset_id}: {e}")
            raise DataSourceQueryError(
                f"Failed to get OEE metrics: {str(e)}",
                source_name=self.source_name,
                table_name="daily_summaries",
            )

    async def get_oee_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get OEE for all assets in an area.

        AC#5: Data can be filtered by asset, area, or plant-wide
        """
        try:
            # Get assets in the area first
            assets_result = await self.get_assets_by_area(area)
            if not assets_result.data:
                return self._create_result(
                    data=[],
                    table_name="daily_summaries",
                    query=f"No assets found in area '{area}'",
                )

            asset_ids = [asset.id for asset in assets_result.data]

            # Get OEE data for all assets in area
            result = (
                self.client.table("daily_summaries")
                .select("*, assets!inner(name, area)")
                .in_("asset_id", asset_ids)
                .gte("report_date", start_date.isoformat())
                .lte("report_date", end_date.isoformat())
                .order("report_date", desc=True)
                .execute()
            )

            metrics = [self._parse_oee_metrics(row) for row in (result.data or [])]

            return self._create_result(
                data=metrics,
                table_name="daily_summaries",
                query=(
                    f"SELECT * FROM daily_summaries "
                    f"WHERE area = '{area}' "
                    f"AND report_date BETWEEN '{start_date}' AND '{end_date}'"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get OEE for area '{area}': {e}")
            raise DataSourceQueryError(
                f"Failed to get OEE for area: {str(e)}",
                source_name=self.source_name,
                table_name="daily_summaries",
            )

    # =========================================================================
    # Downtime Methods (AC#6)
    # =========================================================================

    async def get_downtime(
        self,
        asset_id: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get downtime records for an asset.

        AC#6: Downtime Data Methods - returns with reasons and durations
        """
        try:
            # Downtime data is in daily_summaries (downtime_minutes field)
            result = (
                self.client.table("daily_summaries")
                .select("id, asset_id, report_date, downtime_minutes, financial_loss_dollars")
                .eq("asset_id", asset_id)
                .gte("report_date", start_date.isoformat())
                .lte("report_date", end_date.isoformat())
                .gt("downtime_minutes", 0)  # Only records with downtime
                .order("report_date", desc=True)
                .execute()
            )

            events = []
            for row in (result.data or []):
                events.append(
                    DowntimeEvent(
                        id=str(row["id"]),
                        asset_id=str(row["asset_id"]),
                        report_date=row["report_date"],
                        downtime_minutes=row.get("downtime_minutes", 0),
                        financial_loss_dollars=(
                            Decimal(str(row["financial_loss_dollars"]))
                            if row.get("financial_loss_dollars") is not None
                            else None
                        ),
                    )
                )

            return self._create_result(
                data=events,
                table_name="daily_summaries",
                query=(
                    f"SELECT * FROM daily_summaries "
                    f"WHERE asset_id = '{asset_id}' "
                    f"AND downtime_minutes > 0 "
                    f"AND report_date BETWEEN '{start_date}' AND '{end_date}'"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get downtime for asset {asset_id}: {e}")
            raise DataSourceQueryError(
                f"Failed to get downtime: {str(e)}",
                source_name=self.source_name,
                table_name="daily_summaries",
            )

    async def get_downtime_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get downtime records for all assets in an area.

        AC#6: Data supports asset or area-level queries
        """
        try:
            # Get assets in the area first
            assets_result = await self.get_assets_by_area(area)
            if not assets_result.data:
                return self._create_result(
                    data=[],
                    table_name="daily_summaries",
                    query=f"No assets found in area '{area}'",
                )

            asset_ids = [asset.id for asset in assets_result.data]
            asset_names = {asset.id: asset.name for asset in assets_result.data}

            result = (
                self.client.table("daily_summaries")
                .select("id, asset_id, report_date, downtime_minutes, financial_loss_dollars")
                .in_("asset_id", asset_ids)
                .gte("report_date", start_date.isoformat())
                .lte("report_date", end_date.isoformat())
                .gt("downtime_minutes", 0)
                .order("downtime_minutes", desc=True)
                .execute()
            )

            events = []
            for row in (result.data or []):
                events.append(
                    DowntimeEvent(
                        id=str(row["id"]),
                        asset_id=str(row["asset_id"]),
                        asset_name=asset_names.get(str(row["asset_id"])),
                        report_date=row["report_date"],
                        downtime_minutes=row.get("downtime_minutes", 0),
                        financial_loss_dollars=(
                            Decimal(str(row["financial_loss_dollars"]))
                            if row.get("financial_loss_dollars") is not None
                            else None
                        ),
                    )
                )

            return self._create_result(
                data=events,
                table_name="daily_summaries",
                query=(
                    f"SELECT * FROM daily_summaries "
                    f"WHERE area = '{area}' AND downtime_minutes > 0"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get downtime for area '{area}': {e}")
            raise DataSourceQueryError(
                f"Failed to get downtime for area: {str(e)}",
                source_name=self.source_name,
                table_name="daily_summaries",
            )

    # =========================================================================
    # Live Data Methods (AC#7)
    # =========================================================================

    async def get_live_snapshot(self, asset_id: str) -> DataResult:
        """
        Get current live snapshot for an asset.

        AC#7: Includes data freshness timestamp
        """
        try:
            result = (
                self.client.table("live_snapshots")
                .select("*, assets!inner(name, area)")
                .eq("asset_id", asset_id)
                .order("snapshot_timestamp", desc=True)
                .limit(1)
                .execute()
            )

            status = None
            if result.data and len(result.data) > 0:
                status = self._parse_production_status(result.data[0])

            return self._create_result(
                data=status,
                table_name="live_snapshots",
                query=(
                    f"SELECT * FROM live_snapshots "
                    f"WHERE asset_id = '{asset_id}' "
                    f"ORDER BY snapshot_timestamp DESC LIMIT 1"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get live snapshot for asset {asset_id}: {e}")
            raise DataSourceQueryError(
                f"Failed to get live snapshot: {str(e)}",
                source_name=self.source_name,
                table_name="live_snapshots",
            )

    async def get_live_snapshots_by_area(self, area: str) -> DataResult:
        """
        Get live snapshots for all assets in an area.

        AC#7: Supports filtering by area
        """
        try:
            # Get assets in the area first
            assets_result = await self.get_assets_by_area(area)
            if not assets_result.data:
                return self._create_result(
                    data=[],
                    table_name="live_snapshots",
                    query=f"No assets found in area '{area}'",
                )

            asset_ids = [asset.id for asset in assets_result.data]

            # Get most recent snapshot for each asset
            # Using a subquery approach via multiple calls (Supabase limitation)
            snapshots = []
            for asset in assets_result.data:
                result = (
                    self.client.table("live_snapshots")
                    .select("*, assets!inner(name, area)")
                    .eq("asset_id", asset.id)
                    .order("snapshot_timestamp", desc=True)
                    .limit(1)
                    .execute()
                )
                if result.data and len(result.data) > 0:
                    snapshots.append(self._parse_production_status(result.data[0]))

            return self._create_result(
                data=snapshots,
                table_name="live_snapshots",
                query=(
                    f"SELECT * FROM live_snapshots "
                    f"WHERE area = '{area}' (latest per asset)"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get live snapshots for area '{area}': {e}")
            raise DataSourceQueryError(
                f"Failed to get live snapshots for area: {str(e)}",
                source_name=self.source_name,
                table_name="live_snapshots",
            )

    # =========================================================================
    # Target Methods
    # =========================================================================

    async def get_shift_target(self, asset_id: str) -> DataResult:
        """
        Get current shift target for an asset.
        """
        try:
            today = date.today()

            result = (
                self.client.table("shift_targets")
                .select("*")
                .eq("asset_id", asset_id)
                .lte("effective_date", today.isoformat())
                .order("effective_date", desc=True)
                .limit(1)
                .execute()
            )

            target = None
            if result.data and len(result.data) > 0:
                target = self._parse_shift_target(result.data[0])

            return self._create_result(
                data=target,
                table_name="shift_targets",
                query=(
                    f"SELECT * FROM shift_targets "
                    f"WHERE asset_id = '{asset_id}' "
                    f"AND effective_date <= '{today}' "
                    f"ORDER BY effective_date DESC LIMIT 1"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get shift target for asset {asset_id}: {e}")
            raise DataSourceQueryError(
                f"Failed to get shift target: {str(e)}",
                source_name=self.source_name,
                table_name="shift_targets",
            )

    # =========================================================================
    # Safety Methods
    # =========================================================================

    async def get_safety_events(
        self,
        asset_id: Optional[str],
        start_date: date,
        end_date: date,
        include_resolved: bool = False,
    ) -> DataResult:
        """
        Get safety events for an asset or all assets.
        """
        try:
            query = self.client.table("safety_events").select(
                "*, assets!inner(name, area)"
            )

            if asset_id:
                query = query.eq("asset_id", asset_id)

            query = (
                query.gte("event_timestamp", start_date.isoformat())
                .lte("event_timestamp", end_date.isoformat())
            )

            if not include_resolved:
                query = query.eq("is_resolved", False)

            result = query.order("event_timestamp", desc=True).execute()

            events = [self._parse_safety_event(row) for row in (result.data or [])]

            return self._create_result(
                data=events,
                table_name="safety_events",
                query=(
                    f"SELECT * FROM safety_events "
                    f"WHERE event_timestamp BETWEEN '{start_date}' AND '{end_date}'"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to get safety events: {e}")
            raise DataSourceQueryError(
                f"Failed to get safety events: {str(e)}",
                source_name=self.source_name,
                table_name="safety_events",
            )
