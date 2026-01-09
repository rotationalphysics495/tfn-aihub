"""
Tests for Asset Lookup Tool (Story 5.3)

Comprehensive test coverage for all acceptance criteria:
AC#1: Asset Lookup by Name - Returns metadata, status, OEE, downtime
AC#2: Asset Not Found - Fuzzy Suggestions
AC#3: Asset Exists but No Recent Data
AC#4: Live Status Display with freshness
AC#5: Performance Summary - OEE trend, downtime
AC#6: Citation Compliance
AC#7: Cache TTL Requirements
AC#8: Error Handling
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.agent import (
    AssetCurrentStatus,
    AssetLookupInput,
    AssetLookupOutput,
    AssetMetadata,
    AssetPerformance,
    AssetStatus,
    OEETrend,
)
from app.services.agent.base import Citation, ToolResult
from app.services.agent.data_source.protocol import (
    Asset,
    DataResult,
    DowntimeEvent,
    OEEMetrics,
    ProductionStatus,
    ShiftTarget,
)
from app.services.agent.tools.asset_lookup import (
    AssetLookupTool,
    _normalize_asset_name,
    CACHE_TTL_LIVE,
    CACHE_TTL_METADATA,
    CACHE_TTL_PERFORMANCE,
    STALE_DATA_THRESHOLD_MINUTES,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def asset_lookup_tool():
    """Create an instance of AssetLookupTool."""
    return AssetLookupTool()


@pytest.fixture
def mock_asset():
    """Create a mock Asset object."""
    return Asset(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="Grinder 5",
        source_id="GRD005",
        area="Grinding",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )


@pytest.fixture
def mock_production_status():
    """Create a mock ProductionStatus object."""
    return ProductionStatus(
        id="660e8400-e29b-41d4-a716-446655440001",
        asset_id="550e8400-e29b-41d4-a716-446655440000",
        asset_name="Grinder 5",
        area="Grinding",
        snapshot_timestamp=_utcnow(),
        current_output=847,
        target_output=900,
        output_variance=-53,
        status="behind",
    )


@pytest.fixture
def mock_shift_target():
    """Create a mock ShiftTarget object."""
    return ShiftTarget(
        id="770e8400-e29b-41d4-a716-446655440002",
        asset_id="550e8400-e29b-41d4-a716-446655440000",
        target_output=900,
        shift="Day",
        effective_date=date.today(),
    )


@pytest.fixture
def mock_oee_metrics():
    """Create mock OEE metrics for 7 days."""
    base_date = date.today() - timedelta(days=1)
    metrics = []
    oee_values = [78.0, 80.5, 77.2, 82.1, 79.8, 76.5, 81.0]  # 7 days of data

    for i, oee in enumerate(oee_values):
        metrics.append(
            OEEMetrics(
                id=f"oee-{i}",
                asset_id="550e8400-e29b-41d4-a716-446655440000",
                report_date=base_date - timedelta(days=i),
                oee_percentage=Decimal(str(oee)),
                availability=Decimal("90.0"),
                performance=Decimal("87.0"),
                quality=Decimal("95.0"),
                actual_output=1800,
                target_output=2000,
                downtime_minutes=36,
                waste_count=10,
            )
        )
    return metrics


@pytest.fixture
def mock_downtime_events():
    """Create mock downtime events."""
    base_date = date.today() - timedelta(days=1)
    return [
        DowntimeEvent(
            id="dt-1",
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Grinder 5",
            report_date=base_date,
            downtime_minutes=60,
            reason_code="MJ001",
            reason_description="Material Jam",
        ),
        DowntimeEvent(
            id="dt-2",
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Grinder 5",
            report_date=base_date - timedelta(days=1),
            downtime_minutes=45,
            reason_code="MJ001",
            reason_description="Material Jam",
        ),
        DowntimeEvent(
            id="dt-3",
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Grinder 5",
            report_date=base_date - timedelta(days=2),
            downtime_minutes=30,
            reason_code="PM001",
            reason_description="Preventive Maintenance",
        ),
    ]


def create_data_result(data: Any, table_name: str) -> DataResult:
    """Helper to create DataResult objects for testing."""
    row_count = 0
    if data is not None:
        if isinstance(data, list):
            row_count = len(data)
        elif data:
            row_count = 1

    return DataResult(
        data=data,
        source_name="supabase",
        table_name=table_name,
        query_timestamp=_utcnow(),
        query=f"Test query on {table_name}",
        row_count=row_count,
    )


# =============================================================================
# Test: Name Normalization (AC#2 helper)
# =============================================================================


class TestNameNormalization:
    """Tests for asset name normalization function."""

    def test_normalize_lowercase(self):
        """Test lowercase conversion."""
        assert _normalize_asset_name("GRINDER 5") == "grinder 5"
        assert _normalize_asset_name("Grinder 5") == "grinder 5"

    def test_normalize_remove_special_chars(self):
        """Test removal of special characters."""
        assert _normalize_asset_name("Grinder #5") == "grinder 5"
        assert _normalize_asset_name("Grinder-5") == "grinder 5"
        assert _normalize_asset_name("Grinder_5") == "grinder 5"

    def test_normalize_add_space_before_numbers(self):
        """Test adding space before trailing numbers."""
        assert _normalize_asset_name("grinder5") == "grinder 5"
        assert _normalize_asset_name("CAMA800") == "cama 800"

    def test_normalize_collapse_spaces(self):
        """Test collapsing multiple spaces."""
        assert _normalize_asset_name("Grinder  5") == "grinder 5"
        assert _normalize_asset_name("Grinder   #   5") == "grinder 5"

    def test_normalize_strip_whitespace(self):
        """Test stripping leading/trailing whitespace."""
        assert _normalize_asset_name("  Grinder 5  ") == "grinder 5"

    def test_normalize_complex_names(self):
        """Test complex asset name variations."""
        assert _normalize_asset_name("CAMA-800-1") == "cama 800 1"
        assert _normalize_asset_name("Line_A_Machine_1") == "line a machine 1"


# =============================================================================
# Test: Tool Properties (AC#5 Tool Registration)
# =============================================================================


class TestAssetLookupToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, asset_lookup_tool):
        """Test tool name property."""
        assert asset_lookup_tool.name == "asset_lookup"

    def test_tool_description(self, asset_lookup_tool):
        """Test tool description for intent matching."""
        assert "asset" in asset_lookup_tool.description.lower()
        assert "status" in asset_lookup_tool.description.lower()
        assert "machine" in asset_lookup_tool.description.lower()

    def test_tool_args_schema(self, asset_lookup_tool):
        """Test args_schema is AssetLookupInput."""
        assert asset_lookup_tool.args_schema == AssetLookupInput

    def test_tool_citations_required(self, asset_lookup_tool):
        """Test citations_required is True."""
        assert asset_lookup_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestAssetLookupInput:
    """Tests for AssetLookupInput validation."""

    def test_valid_input(self):
        """Test valid input creation."""
        input_model = AssetLookupInput(asset_name="Grinder 5")
        assert input_model.asset_name == "Grinder 5"
        assert input_model.include_performance is True
        assert input_model.days_back == 7

    def test_input_with_options(self):
        """Test input with custom options."""
        input_model = AssetLookupInput(
            asset_name="Test Asset",
            include_performance=False,
            days_back=14,
        )
        assert input_model.include_performance is False
        assert input_model.days_back == 14

    def test_input_days_back_bounds(self):
        """Test days_back validation bounds."""
        # Valid minimum
        input_model = AssetLookupInput(asset_name="Test", days_back=1)
        assert input_model.days_back == 1

        # Valid maximum
        input_model = AssetLookupInput(asset_name="Test", days_back=90)
        assert input_model.days_back == 90

        # Invalid: below minimum
        with pytest.raises(ValueError):
            AssetLookupInput(asset_name="Test", days_back=0)

        # Invalid: above maximum
        with pytest.raises(ValueError):
            AssetLookupInput(asset_name="Test", days_back=91)


# =============================================================================
# Test: Asset Found with Full Data (AC#1)
# =============================================================================


class TestAssetFoundWithFullData:
    """Tests for successful asset lookup with all data available."""

    @pytest.mark.asyncio
    async def test_asset_found_returns_success(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_shift_target,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """AC#1: Successful asset lookup returns all expected data."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Configure mock responses
            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert result.success is True
            assert result.data is not None
            assert result.data["found"] is True

    @pytest.mark.asyncio
    async def test_asset_found_includes_metadata(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_shift_target,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """AC#1: Response includes asset metadata (name, area, cost center)."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            metadata = result.data["metadata"]
            assert metadata is not None
            assert metadata["name"] == "Grinder 5"
            assert metadata["area"] == "Grinding"
            assert metadata["id"] == "550e8400-e29b-41d4-a716-446655440000"

    @pytest.mark.asyncio
    async def test_asset_found_includes_current_status(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_shift_target,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """AC#1: Response includes current status (running/down/idle)."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            status = result.data["current_status"]
            assert status is not None
            assert status["status"] in ["running", "down", "idle", "unknown"]
            assert status["output_current"] == 847
            assert status["output_target"] == 900

    @pytest.mark.asyncio
    async def test_asset_found_includes_performance(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_shift_target,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """AC#1: Response includes 7-day average OEE and top downtime reason."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            performance = result.data["performance"]
            assert performance is not None
            assert performance["avg_oee"] is not None
            assert 70 <= performance["avg_oee"] <= 100
            assert performance["top_downtime_reason"] == "Material Jam"


# =============================================================================
# Test: Asset Not Found (AC#2)
# =============================================================================


class TestAssetNotFound:
    """Tests for asset not found handling."""

    @pytest.mark.asyncio
    async def test_asset_not_found_message(self, asset_lookup_tool):
        """AC#2: Response states 'I don't have data for [asset name]'."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Asset not found
            mock_ds.get_asset_by_name.return_value = create_data_result(
                None, "assets"
            )
            # Return some suggestions
            mock_ds.get_similar_assets.return_value = create_data_result(
                [
                    Asset(
                        id="1",
                        name="Grinder 1",
                        source_id="G1",
                    ),
                    Asset(
                        id="2",
                        name="Grinder 2",
                        source_id="G2",
                    ),
                ],
                "assets",
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 12")

            assert result.success is True
            assert result.data["found"] is False
            assert "I don't have data for" in result.data["message"]
            assert "Grinder 12" in result.data["message"]

    @pytest.mark.asyncio
    async def test_asset_not_found_provides_suggestions(self, asset_lookup_tool):
        """AC#2: Lists similar assets the user might have meant."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                None, "assets"
            )
            mock_ds.get_similar_assets.return_value = create_data_result(
                [
                    Asset(id="1", name="Grinder 1", source_id="G1"),
                    Asset(id="2", name="Grinder 2", source_id="G2"),
                    Asset(id="3", name="Grinder 3", source_id="G3"),
                ],
                "assets",
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 12")

            assert result.data["suggestions"] is not None
            assert len(result.data["suggestions"]) <= 5
            assert "Grinder 1" in result.data["suggestions"]

    @pytest.mark.asyncio
    async def test_asset_not_found_no_fabrication(self, asset_lookup_tool):
        """AC#2: Response does NOT fabricate data."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                None, "assets"
            )
            mock_ds.get_similar_assets.return_value = create_data_result(
                [], "assets"
            )

            result = await asset_lookup_tool._arun(asset_name="NonExistent")

            # Should not have any actual data
            assert result.data["metadata"] is None
            assert result.data["current_status"] is None
            assert result.data["performance"] is None


# =============================================================================
# Test: Asset Exists but No Recent Data (AC#3)
# =============================================================================


class TestAssetNoRecentData:
    """Tests for asset found but no recent production data."""

    @pytest.mark.asyncio
    async def test_no_recent_data_shows_metadata(
        self, asset_lookup_tool, mock_asset
    ):
        """AC#3: Response shows available metadata."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                None, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            # Empty OEE data
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert result.success is True
            assert result.data["found"] is True
            assert result.data["metadata"] is not None
            assert result.data["metadata"]["name"] == "Grinder 5"

    @pytest.mark.asyncio
    async def test_no_recent_data_message(self, asset_lookup_tool, mock_asset):
        """AC#3: Indicates 'No production data available for the last X days'."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                None, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            performance = result.data["performance"]
            assert performance["no_data"] is True
            assert "No production data available" in performance["message"]


# =============================================================================
# Test: Live Status Display (AC#4)
# =============================================================================


class TestLiveStatusDisplay:
    """Tests for live status handling."""

    @pytest.mark.asyncio
    async def test_live_status_running(
        self, asset_lookup_tool, mock_asset, mock_production_status
    ):
        """AC#4: Current status properly determined as running."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(
                asset_name="Grinder 5", include_performance=True
            )

            status = result.data["current_status"]
            assert status["status"] == "running"

    @pytest.mark.asyncio
    async def test_live_status_freshness_timestamp(
        self, asset_lookup_tool, mock_asset, mock_production_status
    ):
        """AC#4: Response includes data freshness timestamp."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            status = result.data["current_status"]
            assert status["last_updated"] is not None

    @pytest.mark.asyncio
    async def test_live_status_stale_warning(self, asset_lookup_tool, mock_asset):
        """AC#4: Warning if data is stale (>30 minutes old)."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Create stale snapshot (45 minutes old)
            stale_status = ProductionStatus(
                id="stale-1",
                asset_id="550e8400-e29b-41d4-a716-446655440000",
                asset_name="Grinder 5",
                area="Grinding",
                snapshot_timestamp=_utcnow() - timedelta(minutes=45),
                current_output=800,
                target_output=900,
                output_variance=-100,
                status="behind",
            )

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                stale_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            status = result.data["current_status"]
            assert status["data_stale"] is True
            assert status["stale_warning"] is not None


# =============================================================================
# Test: Performance Summary (AC#5)
# =============================================================================


class TestPerformanceSummary:
    """Tests for performance summary calculations."""

    @pytest.mark.asyncio
    async def test_oee_average_calculation(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """AC#5: 7-day average OEE percentage calculated correctly."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            performance = result.data["performance"]
            assert performance["avg_oee"] is not None
            # Expected: average of [78.0, 80.5, 77.2, 82.1, 79.8, 76.5, 81.0] = ~79.3
            assert 78 <= performance["avg_oee"] <= 81

    def test_oee_trend_improving(self, asset_lookup_tool):
        """AC#5: OEE trend indicator - improving."""
        # DB returns newest first, so [85, 82, 80, 78, 75, 72, 70] means
        # oldest values (70, 72, 75) were low, recent values (85, 82, 80) are higher = IMPROVING
        values = [85, 82, 80, 78, 75, 72, 70]  # Newest first, showing improvement
        trend = asset_lookup_tool._calculate_oee_trend(values)
        assert trend == OEETrend.IMPROVING

    def test_oee_trend_declining(self, asset_lookup_tool):
        """AC#5: OEE trend indicator - declining."""
        # DB returns newest first, so [70, 72, 75, 78, 80, 82, 85] means
        # oldest values (85, 82, 80) were high, recent values (70, 72, 75) are lower = DECLINING
        values = [70, 72, 75, 78, 80, 82, 85]  # Newest first, showing decline
        trend = asset_lookup_tool._calculate_oee_trend(values)
        assert trend == OEETrend.DECLINING

    def test_oee_trend_stable(self, asset_lookup_tool):
        """AC#5: OEE trend indicator - stable."""
        # Stable: minimal change between halves
        values = [78, 79, 78, 79, 78, 79, 78]  # Stable
        trend = asset_lookup_tool._calculate_oee_trend(values)
        assert trend == OEETrend.STABLE

    def test_oee_trend_insufficient_data(self, asset_lookup_tool):
        """AC#5: OEE trend indicator - insufficient data."""
        # Less than 4 data points
        values = [78, 79, 80]
        trend = asset_lookup_tool._calculate_oee_trend(values)
        assert trend == OEETrend.INSUFFICIENT_DATA

    @pytest.mark.asyncio
    async def test_downtime_pareto(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """AC#5: Top downtime reason with percentage contribution."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            performance = result.data["performance"]
            assert performance["top_downtime_reason"] == "Material Jam"
            # Material Jam: 60 + 45 = 105 out of 135 total = ~77.8%
            assert performance["top_downtime_percent"] > 70


# =============================================================================
# Test: Citation Compliance (AC#6)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation and compliance."""

    @pytest.mark.asyncio
    async def test_citations_generated(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """AC#6: All data points include citations."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert len(result.citations) > 0
            # Should have citations for: assets, live_snapshots, shift_targets, daily_summaries (oee), daily_summaries (downtime)
            assert len(result.citations) >= 5

    @pytest.mark.asyncio
    async def test_citation_format(
        self, asset_lookup_tool, mock_asset, mock_production_status
    ):
        """AC#6: Citations follow format with source, table, timestamp."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            for citation in result.citations:
                assert citation.source is not None
                assert citation.table is not None
                assert citation.timestamp is not None


# =============================================================================
# Test: Cache TTL Requirements (AC#7)
# =============================================================================


class TestCacheTTLRequirements:
    """Tests for cache tier metadata."""

    @pytest.mark.asyncio
    async def test_cache_tier_live(
        self, asset_lookup_tool, mock_asset, mock_production_status
    ):
        """AC#7: Live status data has 60 second TTL."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert result.metadata["cache_tier"] == "live"
            assert result.metadata["ttl_seconds"] == CACHE_TTL_LIVE

    @pytest.mark.asyncio
    async def test_cache_tier_static(self, asset_lookup_tool, mock_asset):
        """AC#7: Asset metadata has 1 hour TTL when no live data."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                None, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert result.metadata["cache_tier"] == "static"
            assert result.metadata["ttl_seconds"] == CACHE_TTL_METADATA


# =============================================================================
# Test: Error Handling (AC#8)
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_data_source_error_returns_friendly_message(
        self, asset_lookup_tool
    ):
        """AC#8: User-friendly error message for data source errors."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="assets",
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert result.success is False
            assert result.error_message is not None
            assert "Unable to retrieve" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(self, asset_lookup_tool):
        """AC#8: Unexpected errors are caught and logged."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.side_effect = RuntimeError(
                "Unexpected failure"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert result.success is False
            assert result.error_message is not None
            assert "unexpected error" in result.error_message.lower()


# =============================================================================
# Test: Follow-up Question Generation
# =============================================================================


class TestFollowUpQuestions:
    """Tests for follow-up question generation."""

    @pytest.mark.asyncio
    async def test_follow_up_questions_generated(
        self,
        asset_lookup_tool,
        mock_asset,
        mock_production_status,
        mock_oee_metrics,
        mock_downtime_events,
    ):
        """Follow-up questions are generated in metadata."""
        with patch(
            "app.services.agent.tools.asset_lookup.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_live_snapshot.return_value = create_data_result(
                mock_production_status, "live_snapshots"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                mock_downtime_events, "daily_summaries"
            )

            result = await asset_lookup_tool._arun(asset_name="Grinder 5")

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3

    def test_follow_up_questions_context_aware(self, asset_lookup_tool):
        """Follow-up questions are based on data context."""
        # Test with low OEE
        output = AssetLookupOutput(
            found=True,
            metadata=AssetMetadata(
                id="1",
                name="Grinder 5",
                source_id="G5",
                area="Grinding",
            ),
            performance=AssetPerformance(
                avg_oee=65.0,  # Low OEE
                oee_trend=OEETrend.DECLINING,
                top_downtime_reason="Material Jam",
            ),
        )

        questions = asset_lookup_tool._generate_follow_up_questions(output)

        # Should include question about low OEE
        assert any("OEE" in q for q in questions)


# =============================================================================
# Test: Tool Registration (Integration)
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = AssetLookupTool()
        assert tool is not None
        assert tool.name == "asset_lookup"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = AssetLookupTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)
