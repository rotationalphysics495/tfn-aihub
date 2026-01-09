"""
DataSource Protocol Definition (Story 5.2)

Defines the interface for all data source implementations with:
- Protocol-based abstraction for database access
- DataResult wrapper for consistent response format
- Type models for domain objects

AC#1: DataSource Protocol Definition
- Protocol defines async methods for all common data operations
- Each method returns DataResult with data + source metadata
- Protocol compatible with both Supabase and future MSSQL

AC#3: DataResult Response Format
- Response wrapped in DataResult object
- Includes source_name, table_name, query_timestamp
- Metadata available for citation generation
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# =============================================================================
# Domain Models
# =============================================================================


class Asset(BaseModel):
    """Asset from Plant Object Model."""

    id: str = Field(..., description="Asset UUID")
    name: str = Field(..., description="Human-readable asset name")
    source_id: str = Field(..., description="Maps to MSSQL locationName")
    area: Optional[str] = Field(None, description="Plant area location")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class OEEMetrics(BaseModel):
    """OEE metrics from daily summaries."""

    id: str = Field(..., description="Record UUID")
    asset_id: str = Field(..., description="Asset UUID")
    report_date: date = Field(..., description="Report date")
    oee_percentage: Optional[Decimal] = Field(None, description="OEE percentage 0-100")
    availability: Optional[Decimal] = Field(None, description="Availability component")
    performance: Optional[Decimal] = Field(None, description="Performance component")
    quality: Optional[Decimal] = Field(None, description="Quality component")
    actual_output: Optional[int] = Field(None, description="Actual production output")
    target_output: Optional[int] = Field(None, description="Target production output")
    downtime_minutes: Optional[int] = Field(None, description="Total downtime in minutes")
    downtime_reasons: Optional[dict] = Field(
        None, description="Downtime reasons breakdown: {reason_code: minutes}"
    )
    waste_count: Optional[int] = Field(None, description="Number of waste items")
    financial_loss_dollars: Optional[Decimal] = Field(
        None, description="Calculated financial loss"
    )
    smart_summary_text: Optional[str] = Field(None, description="AI-generated summary")


class DowntimeEvent(BaseModel):
    """Downtime event with reason and duration."""

    id: str = Field(..., description="Event UUID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Asset name for display")
    report_date: date = Field(..., description="Date of downtime")
    downtime_minutes: int = Field(..., description="Duration in minutes")
    reason_code: Optional[str] = Field(None, description="Downtime reason code")
    reason_description: Optional[str] = Field(None, description="Reason description")
    financial_loss_dollars: Optional[Decimal] = Field(
        None, description="Financial impact"
    )


class ProductionStatus(BaseModel):
    """Live production snapshot status."""

    id: str = Field(..., description="Snapshot UUID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Asset name")
    area: Optional[str] = Field(None, description="Plant area")
    snapshot_timestamp: datetime = Field(..., description="When snapshot was taken")
    current_output: Optional[int] = Field(None, description="Current production count")
    target_output: Optional[int] = Field(None, description="Target production count")
    output_variance: Optional[int] = Field(None, description="Variance from target")
    status: str = Field(..., description="Status: on_target, behind, or ahead")


class ShiftTarget(BaseModel):
    """Shift target for an asset."""

    id: str = Field(..., description="Target UUID")
    asset_id: str = Field(..., description="Asset UUID")
    target_output: int = Field(..., description="Production target")
    target_oee: Optional[float] = Field(None, description="Target OEE percentage (0-100)")
    shift: Optional[str] = Field(None, description="Shift name")
    effective_date: Optional[date] = Field(None, description="Effective date")


class SafetyEvent(BaseModel):
    """Safety event from safety_events table.

    Story 6.1: Enhanced with area field for filtering.
    Note: Database uses `is_resolved` boolean; we derive `resolution_status` for API.
    """

    id: str = Field(..., description="Event UUID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Asset name")
    area: Optional[str] = Field(None, description="Plant area from joined assets table")
    event_timestamp: datetime = Field(..., description="When event occurred")
    reason_code: str = Field(..., description="Safety reason code")
    severity: str = Field(..., description="Severity level: critical/high/medium/low")
    description: Optional[str] = Field(None, description="Event description")
    is_resolved: bool = Field(default=False, description="Whether event is resolved (from DB)")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    @property
    def resolution_status(self) -> str:
        """Derive resolution status from is_resolved flag.

        Story 6.1: Maps DB boolean to status string.
        - resolved: is_resolved=True
        - open: is_resolved=False (default for unresolved)
        Note: 'under_investigation' not distinguishable from 'open' in current schema.
        """
        return "resolved" if self.is_resolved else "open"


class FinancialMetrics(BaseModel):
    """Financial metrics from daily_summaries joined with cost_centers.

    Story 6.2: Enhanced metrics for financial impact calculation.
    Story 6.3: Added downtime_reasons for root cause extraction.
    """

    id: str = Field(..., description="Record UUID (from daily_summaries)")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Asset name")
    area: Optional[str] = Field(None, description="Plant area")
    report_date: date = Field(..., description="Report date")
    downtime_minutes: int = Field(default=0, description="Total downtime in minutes")
    waste_count: int = Field(default=0, description="Number of waste items")
    # Story 6.3: downtime_reasons JSONB for root cause extraction
    downtime_reasons: Optional[dict] = Field(
        None, description="Downtime reasons breakdown: {reason_code: minutes}"
    )
    # Cost center data (may be None if not configured)
    standard_hourly_rate: Optional[Decimal] = Field(
        None, description="$/hour for downtime calculation (from cost_centers)"
    )
    cost_per_unit: Optional[Decimal] = Field(
        None, description="$/unit for waste calculation (from cost_centers)"
    )

    @property
    def has_cost_data(self) -> bool:
        """Check if cost center data is available for financial calculations."""
        return self.standard_hourly_rate is not None or self.cost_per_unit is not None


# =============================================================================
# DataResult Response Wrapper
# =============================================================================


class DataResult(BaseModel):
    """
    Wrapper for data source responses with metadata for citations.

    AC#3: DataResult Response Format
    - data: The actual query result
    - source_name: Database source identifier (e.g., "supabase")
    - table_name: Table queried (e.g., "daily_summaries")
    - query_timestamp: When the query was executed
    - query: Optional SQL query for debugging
    - row_count: Number of rows returned
    """

    data: Any = Field(..., description="The actual query result")
    source_name: str = Field(..., description="Data source identifier (e.g., 'supabase')")
    table_name: str = Field(..., description="Database table queried")
    query_timestamp: datetime = Field(
        default_factory=_utcnow, description="When the query was executed"
    )
    query: Optional[str] = Field(None, description="SQL query for debugging (optional)")
    row_count: int = Field(default=0, description="Number of rows returned")

    def to_citation_metadata(self) -> dict:
        """
        Convert DataResult to metadata dict for Citation creation.

        Returns dict suitable for ManufacturingTool._create_citation()
        """
        return {
            "source": self.source_name,
            "table": self.table_name,
            "query": self.query or f"Query on {self.table_name}",
        }

    @property
    def has_data(self) -> bool:
        """Check if result contains data."""
        if self.data is None:
            return False
        if isinstance(self.data, list) and len(self.data) == 0:
            return False
        return True


# =============================================================================
# DataSource Protocol
# =============================================================================


@runtime_checkable
class DataSource(Protocol):
    """
    Protocol defining the interface for all data sources.

    AC#1: DataSource Protocol Definition
    - All methods are async for non-blocking database access
    - Each method returns DataResult with data + source metadata
    - Protocol is compatible with Supabase and future MSSQL

    Implementations:
    - SupabaseDataSource: Supabase PostgreSQL (primary)
    - MSSQLDataSource: MSSQL read-only source (future)
    - CompositeDataSource: Router for multi-source configurations
    """

    # =========================================================================
    # Asset Methods (AC#4)
    # =========================================================================

    async def get_asset(self, asset_id: str) -> DataResult:
        """
        Get asset by ID.

        Args:
            asset_id: UUID of the asset

        Returns:
            DataResult with Asset data or None if not found
        """
        ...

    async def get_asset_by_name(self, name: str) -> DataResult:
        """
        Get asset by name with fuzzy matching.

        Uses case-insensitive matching, falls back to partial match
        if exact match not found.

        Args:
            name: Asset name to search for

        Returns:
            DataResult with Asset data or None if not found
        """
        ...

    async def get_assets_by_area(self, area: str) -> DataResult:
        """
        Get all assets in an area.

        Args:
            area: Plant area name (e.g., "Grinding")

        Returns:
            DataResult with list of Asset objects
        """
        ...

    async def get_similar_assets(self, name: str, limit: int = 5) -> DataResult:
        """
        Get assets with similar names for suggestions.

        Used when exact match fails to provide helpful alternatives.

        Args:
            name: Search term
            limit: Maximum number of suggestions

        Returns:
            DataResult with list of similar Asset objects
        """
        ...

    async def get_all_assets(self) -> DataResult:
        """
        Get all assets in the system.

        Returns:
            DataResult with list of all Asset objects
        """
        ...

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

        Args:
            asset_id: UUID of the asset
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            DataResult with list of OEEMetrics
        """
        ...

    async def get_oee_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get aggregated OEE for all assets in an area.

        Args:
            area: Plant area name
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataResult with list of OEEMetrics for all assets in area
        """
        ...

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

        Args:
            asset_id: UUID of the asset
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataResult with list of DowntimeEvent objects
        """
        ...

    async def get_downtime_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get downtime records for all assets in an area.

        Args:
            area: Plant area name
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataResult with list of DowntimeEvent objects
        """
        ...

    # =========================================================================
    # Live Data Methods (AC#7)
    # =========================================================================

    async def get_live_snapshot(self, asset_id: str) -> DataResult:
        """
        Get current live snapshot for an asset.

        Returns the most recent snapshot for real-time status.

        Args:
            asset_id: UUID of the asset

        Returns:
            DataResult with ProductionStatus or None if no snapshot
        """
        ...

    async def get_live_snapshots_by_area(self, area: str) -> DataResult:
        """
        Get live snapshots for all assets in an area.

        Returns most recent snapshot for each asset.

        Args:
            area: Plant area name

        Returns:
            DataResult with list of ProductionStatus objects
        """
        ...

    async def get_all_live_snapshots(self) -> DataResult:
        """
        Get live snapshots for all assets in the system.

        Returns most recent snapshot for each asset.

        Returns:
            DataResult with list of ProductionStatus objects
        """
        ...

    # =========================================================================
    # Target Methods
    # =========================================================================

    async def get_shift_target(self, asset_id: str) -> DataResult:
        """
        Get current shift target for an asset.

        Returns the most recently effective target.

        Args:
            asset_id: UUID of the asset

        Returns:
            DataResult with ShiftTarget or None if no target set
        """
        ...

    async def get_all_shift_targets(self) -> DataResult:
        """
        Get shift targets for all assets in the system.

        Returns the most recently effective target for each asset.

        Returns:
            DataResult with list of ShiftTarget objects
        """
        ...

    # =========================================================================
    # Safety Methods
    # =========================================================================

    async def get_safety_events(
        self,
        asset_id: Optional[str],
        start_date: date,
        end_date: date,
        include_resolved: bool = False,
        area: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> DataResult:
        """
        Get safety events for an asset or all assets.

        Story 6.1: Enhanced with area and severity filtering.

        Args:
            asset_id: UUID of asset, or None for all assets
            start_date: Start of date range
            end_date: End of date range
            include_resolved: Whether to include resolved events
            area: Optional area name to filter by (e.g., 'Packaging')
            severity: Optional severity level to filter by ('critical', 'high', 'medium', 'low')

        Returns:
            DataResult with list of SafetyEvent objects
        """
        ...

    # =========================================================================
    # Financial Methods (Story 6.2)
    # =========================================================================

    async def get_financial_metrics(
        self,
        start_date: date,
        end_date: date,
        asset_id: Optional[str] = None,
        area: Optional[str] = None,
    ) -> DataResult:
        """
        Get financial metrics for assets in date range.

        Story 6.2: Query daily_summaries joined with cost_centers for
        financial impact calculations.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            asset_id: Optional UUID of specific asset
            area: Optional area name to filter by

        Returns:
            DataResult with list of FinancialMetrics objects
            DataResult.data includes has_cost_data flag for detecting missing cost centers
        """
        ...

    # =========================================================================
    # Cost of Loss Methods (Story 6.3)
    # =========================================================================

    async def get_cost_of_loss(
        self,
        start_date: date,
        end_date: date,
        area: Optional[str] = None,
    ) -> DataResult:
        """
        Get cost of loss data for analysis.

        Story 6.3: Query daily_summaries joined with cost_centers and assets
        for cost of loss analysis. Includes downtime_reasons JSONB for
        root cause extraction.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            area: Optional area name to filter by

        Returns:
            DataResult with list of FinancialMetrics objects including
            downtime_reasons for root cause extraction
        """
        ...
