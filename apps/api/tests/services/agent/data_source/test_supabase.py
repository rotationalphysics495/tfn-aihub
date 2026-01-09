"""
Tests for SupabaseDataSource (Story 5.2)

AC#2: Supabase DataSource Implementation
AC#4: Asset Data Methods
AC#5: OEE Data Methods
AC#6: Downtime Data Methods
AC#7: Live Data Methods
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.agent.data_source.supabase import SupabaseDataSource
from app.services.agent.data_source.protocol import (
    Asset,
    DataResult,
    OEEMetrics,
    DowntimeEvent,
    ProductionStatus,
    ShiftTarget,
)
from app.services.agent.data_source.exceptions import (
    DataSourceConfigurationError,
    DataSourceQueryError,
)


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def data_source(mock_supabase_client):
    """Create SupabaseDataSource with mock client."""
    return SupabaseDataSource(client=mock_supabase_client)


class TestSupabaseDataSourceInit:
    """Tests for SupabaseDataSource initialization."""

    def test_source_name(self, data_source):
        """AC#2: Source name is 'supabase'."""
        assert data_source.source_name == "supabase"

    def test_client_injection(self, mock_supabase_client):
        """Client can be injected for testing."""
        ds = SupabaseDataSource(client=mock_supabase_client)
        assert ds._client is mock_supabase_client

    @patch("app.services.agent.data_source.supabase.get_settings")
    def test_lazy_client_initialization_no_config(self, mock_settings):
        """Raises error when Supabase not configured."""
        mock_settings.return_value.supabase_url = ""
        mock_settings.return_value.supabase_key = ""

        ds = SupabaseDataSource()

        with pytest.raises(DataSourceConfigurationError):
            _ = ds.client


class TestAssetMethods:
    """Tests for Asset Data Methods (AC#4)."""

    @pytest.mark.asyncio
    async def test_get_asset_found(self, data_source, mock_supabase_client):
        """AC#4: Get asset by ID returns Asset data."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123-456",
                "name": "Grinder 5",
                "source_id": "LOC-GRN-005",
                "area": "Grinding",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }]
        )

        result = await data_source.get_asset("123-456")

        assert isinstance(result, DataResult)
        assert result.source_name == "supabase"
        assert result.table_name == "assets"
        assert result.row_count == 1
        assert isinstance(result.data, Asset)
        assert result.data.id == "123-456"
        assert result.data.name == "Grinder 5"

    @pytest.mark.asyncio
    async def test_get_asset_not_found(self, data_source, mock_supabase_client):
        """AC#4: Get asset returns None when not found."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = await data_source.get_asset("nonexistent")

        assert result.data is None
        assert result.row_count == 0

    @pytest.mark.asyncio
    async def test_get_asset_by_name_exact_match(self, data_source, mock_supabase_client):
        """AC#4: Get asset by name with exact match."""
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123-456",
                "name": "Grinder 5",
                "source_id": "LOC-GRN-005",
                "area": "Grinding",
            }]
        )

        result = await data_source.get_asset_by_name("Grinder 5")

        assert result.has_data
        assert result.data.name == "Grinder 5"

    @pytest.mark.asyncio
    async def test_get_asset_by_name_fuzzy_match(self, data_source, mock_supabase_client):
        """AC#4: Fuzzy name matching when exact match fails."""
        # First call (exact match) returns empty
        # Second call (fuzzy match) returns result
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.side_effect = [
            MagicMock(data=[]),  # No exact match
            MagicMock(data=[{   # Fuzzy match found
                "id": "123-456",
                "name": "Grinder 5",
                "source_id": "LOC-GRN-005",
                "area": "Grinding",
            }]),
        ]

        result = await data_source.get_asset_by_name("grinder")

        assert result.has_data
        assert "Grinder 5" in result.data.name

    @pytest.mark.asyncio
    async def test_get_assets_by_area(self, data_source, mock_supabase_client):
        """AC#4: Get all assets in an area."""
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "name": "Grinder 1", "source_id": "G1", "area": "Grinding"},
                {"id": "2", "name": "Grinder 2", "source_id": "G2", "area": "Grinding"},
            ]
        )

        result = await data_source.get_assets_by_area("Grinding")

        assert result.row_count == 2
        assert len(result.data) == 2
        assert all(isinstance(a, Asset) for a in result.data)

    @pytest.mark.asyncio
    async def test_get_similar_assets(self, data_source, mock_supabase_client):
        """AC#4: Get similar assets for suggestions."""
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "name": "Grinder 1", "source_id": "G1", "area": "Grinding"},
                {"id": "2", "name": "Grinder 2", "source_id": "G2", "area": "Grinding"},
                {"id": "3", "name": "Grinder 5", "source_id": "G5", "area": "Grinding"},
            ]
        )

        result = await data_source.get_similar_assets("grind", limit=5)

        assert result.row_count == 3
        assert all("Grinder" in a.name for a in result.data)

    @pytest.mark.asyncio
    async def test_get_all_assets(self, data_source, mock_supabase_client):
        """Get all assets returns complete list."""
        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "name": "Asset 1", "source_id": "A1", "area": "Area1"},
                {"id": "2", "name": "Asset 2", "source_id": "A2", "area": "Area2"},
            ]
        )

        result = await data_source.get_all_assets()

        assert result.row_count == 2


class TestOEEMethods:
    """Tests for OEE Data Methods (AC#5)."""

    @pytest.mark.asyncio
    async def test_get_oee_single_asset(self, data_source, mock_supabase_client):
        """AC#5: Get OEE metrics for an asset in date range."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "1",
                    "asset_id": "456",
                    "report_date": "2026-01-08",
                    "oee_percentage": 87.5,
                    "actual_output": 950,
                    "target_output": 1000,
                    "downtime_minutes": 45,
                    "waste_count": 5,
                    "financial_loss_dollars": 1500.00,
                    "smart_summary_text": "Good performance",
                }
            ]
        )

        result = await data_source.get_oee(
            asset_id="456",
            start_date=date(2026, 1, 8),
            end_date=date(2026, 1, 8),
        )

        assert result.source_name == "supabase"
        assert result.table_name == "daily_summaries"
        assert result.row_count == 1
        assert isinstance(result.data[0], OEEMetrics)
        assert result.data[0].oee_percentage == Decimal("87.5")

    @pytest.mark.asyncio
    async def test_get_oee_by_area(self, data_source, mock_supabase_client):
        """AC#5: Get OEE filtered by area."""
        # First call gets assets in area
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "name": "Grinder 1", "source_id": "G1", "area": "Grinding"},
                {"id": "2", "name": "Grinder 2", "source_id": "G2", "area": "Grinding"},
            ]
        )

        # Second call gets OEE data
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "oee1",
                    "asset_id": "1",
                    "report_date": "2026-01-08",
                    "oee_percentage": 85.0,
                },
                {
                    "id": "oee2",
                    "asset_id": "2",
                    "report_date": "2026-01-08",
                    "oee_percentage": 90.0,
                },
            ]
        )

        result = await data_source.get_oee_by_area(
            area="Grinding",
            start_date=date(2026, 1, 8),
            end_date=date(2026, 1, 8),
        )

        assert result.table_name == "daily_summaries"


class TestDowntimeMethods:
    """Tests for Downtime Data Methods (AC#6)."""

    @pytest.mark.asyncio
    async def test_get_downtime_single_asset(self, data_source, mock_supabase_client):
        """AC#6: Get downtime records with reasons and durations."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.gt.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "1",
                    "asset_id": "456",
                    "report_date": "2026-01-08",
                    "downtime_minutes": 120,
                    "financial_loss_dollars": 2500.00,
                }
            ]
        )

        result = await data_source.get_downtime(
            asset_id="456",
            start_date=date(2026, 1, 8),
            end_date=date(2026, 1, 8),
        )

        assert result.table_name == "daily_summaries"
        assert result.row_count == 1
        assert isinstance(result.data[0], DowntimeEvent)
        assert result.data[0].downtime_minutes == 120

    @pytest.mark.asyncio
    async def test_get_downtime_by_area(self, data_source, mock_supabase_client):
        """AC#6: Downtime supports area-level queries."""
        # First call gets assets
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "name": "Grinder 1", "source_id": "G1", "area": "Grinding"},
            ]
        )

        # Second call gets downtime
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.gte.return_value.lte.return_value.gt.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "1",
                    "asset_id": "1",
                    "report_date": "2026-01-08",
                    "downtime_minutes": 60,
                    "financial_loss_dollars": 1000.00,
                }
            ]
        )

        result = await data_source.get_downtime_by_area(
            area="Grinding",
            start_date=date(2026, 1, 8),
            end_date=date(2026, 1, 8),
        )

        assert result.row_count == 1
        assert result.data[0].asset_name == "Grinder 1"


class TestLiveDataMethods:
    """Tests for Live Data Methods (AC#7)."""

    @pytest.mark.asyncio
    async def test_get_live_snapshot(self, data_source, mock_supabase_client):
        """AC#7: Get current live snapshot with freshness timestamp."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "snap1",
                    "asset_id": "456",
                    "snapshot_timestamp": "2026-01-09T10:30:00Z",
                    "current_output": 450,
                    "target_output": 500,
                    "output_variance": -50,
                    "status": "behind",
                    "assets": {"name": "Grinder 5", "area": "Grinding"},
                }
            ]
        )

        result = await data_source.get_live_snapshot("456")

        assert result.source_name == "supabase"
        assert result.table_name == "live_snapshots"
        assert isinstance(result.data, ProductionStatus)
        assert result.data.current_output == 450
        assert result.data.status == "behind"
        assert result.data.asset_name == "Grinder 5"

    @pytest.mark.asyncio
    async def test_get_live_snapshot_not_found(self, data_source, mock_supabase_client):
        """AC#7: Returns None when no snapshot exists."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = await data_source.get_live_snapshot("nonexistent")

        assert result.data is None
        assert result.row_count == 0

    @pytest.mark.asyncio
    async def test_get_live_snapshots_by_area(self, data_source, mock_supabase_client):
        """AC#7: Get live snapshots filtered by area."""
        # First call gets assets in area
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "name": "Grinder 1", "source_id": "G1", "area": "Grinding"},
                {"id": "2", "name": "Grinder 2", "source_id": "G2", "area": "Grinding"},
            ]
        )

        # Subsequent calls get snapshots for each asset
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = [
            MagicMock(data=[{
                "id": "snap1",
                "asset_id": "1",
                "snapshot_timestamp": "2026-01-09T10:30:00Z",
                "current_output": 450,
                "target_output": 500,
                "output_variance": -50,
                "status": "behind",
                "assets": {"name": "Grinder 1", "area": "Grinding"},
            }]),
            MagicMock(data=[{
                "id": "snap2",
                "asset_id": "2",
                "snapshot_timestamp": "2026-01-09T10:30:00Z",
                "current_output": 520,
                "target_output": 500,
                "output_variance": 20,
                "status": "ahead",
                "assets": {"name": "Grinder 2", "area": "Grinding"},
            }]),
        ]

        result = await data_source.get_live_snapshots_by_area("Grinding")

        assert result.table_name == "live_snapshots"
        assert len(result.data) == 2


class TestShiftTargetMethods:
    """Tests for Shift Target Methods."""

    @pytest.mark.asyncio
    async def test_get_shift_target(self, data_source, mock_supabase_client):
        """Get current shift target for an asset."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "target1",
                    "asset_id": "456",
                    "target_output": 1000,
                    "shift": "Day",
                    "effective_date": "2026-01-01",
                }
            ]
        )

        result = await data_source.get_shift_target("456")

        assert result.table_name == "shift_targets"
        assert isinstance(result.data, ShiftTarget)
        assert result.data.target_output == 1000

    @pytest.mark.asyncio
    async def test_get_shift_target_not_found(self, data_source, mock_supabase_client):
        """Returns None when no target exists."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = await data_source.get_shift_target("nonexistent")

        assert result.data is None


class TestSafetyEventMethods:
    """Tests for Safety Event Methods."""

    @pytest.mark.asyncio
    async def test_get_safety_events(self, data_source, mock_supabase_client):
        """Get safety events for an asset."""
        mock_query = MagicMock()
        mock_supabase_client.table.return_value.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.order.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "event1",
                    "asset_id": "456",
                    "event_timestamp": "2026-01-09T08:00:00Z",
                    "reason_code": "SAFETY-001",
                    "severity": "high",
                    "description": "Equipment malfunction",
                    "is_resolved": False,
                    "resolved_at": None,
                    "assets": {"name": "Grinder 5", "area": "Grinding"},
                }
            ]
        )

        result = await data_source.get_safety_events(
            asset_id="456",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 9),
            include_resolved=False,
        )

        assert result.table_name == "safety_events"
        assert result.row_count == 1


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_get_asset_query_error(self, data_source, mock_supabase_client):
        """Raises DataSourceQueryError on database error."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception(
            "Database connection lost"
        )

        with pytest.raises(DataSourceQueryError) as exc_info:
            await data_source.get_asset("123")

        assert "Database connection lost" in str(exc_info.value)
        assert exc_info.value.source_name == "supabase"


class TestDataResultFormat:
    """Tests for DataResult format (AC#3)."""

    @pytest.mark.asyncio
    async def test_data_result_includes_source_metadata(self, data_source, mock_supabase_client):
        """AC#3: DataResult includes source_name, table_name, query_timestamp."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123",
                "name": "Grinder 5",
                "source_id": "G5",
                "area": "Grinding",
            }]
        )

        result = await data_source.get_asset("123")

        assert result.source_name == "supabase"
        assert result.table_name == "assets"
        assert result.query_timestamp is not None
        assert isinstance(result.query_timestamp, datetime)

    @pytest.mark.asyncio
    async def test_data_result_includes_query_for_debugging(self, data_source, mock_supabase_client):
        """AC#3: DataResult includes optional query for debugging."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123",
                "name": "Grinder 5",
                "source_id": "G5",
                "area": "Grinding",
            }]
        )

        result = await data_source.get_asset("123")

        assert result.query is not None
        assert "assets" in result.query
