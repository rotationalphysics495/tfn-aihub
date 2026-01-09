"""
Tests for Production Status Tool (Story 5.6)

Comprehensive test coverage for all acceptance criteria:
AC#1: Plant-Wide Production Status - Returns output vs target, variance, status for all assets
AC#2: Area-Filtered Production Status - Filters to assets in a specific area with totals
AC#3: Data Freshness Warning - Warns when data is stale (>30 minutes old)
AC#4: Status Indicators - ahead/on-track/behind based on 5% thresholds
AC#5: Summary Statistics - Total assets, counts by status, overall variance
AC#6: No Live Data Handling - Honest messaging when no data available
AC#7: Tool Registration - Auto-discovered by agent framework
AC#8: Caching Support - Returns cache metadata (live tier, 60 second TTL)
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, patch

from app.services.agent.base import Citation, ToolResult
from app.services.agent.data_source.protocol import (
    Asset,
    DataResult,
    ProductionStatus,
    ShiftTarget,
)
from app.services.agent.tools.production_status import (
    ProductionStatusTool,
    ProductionStatusInput,
    ProductionStatusOutput,
    AssetProductionStatus,
    ProductionStatusSummary,
    CACHE_TTL_LIVE,
    AHEAD_THRESHOLD,
    BEHIND_THRESHOLD,
    STALE_MINUTES,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def production_status_tool():
    """Create an instance of ProductionStatusTool."""
    return ProductionStatusTool()


@pytest.fixture
def mock_assets():
    """Create mock Asset objects."""
    return [
        Asset(id="asset-1", name="Grinder 1", source_id="G1", area="Grinding"),
        Asset(id="asset-2", name="Grinder 2", source_id="G2", area="Grinding"),
        Asset(id="asset-3", name="CAMA 800-1", source_id="C1", area="Packaging"),
        Asset(id="asset-4", name="Press 1", source_id="P1", area="Pressing"),
    ]


@pytest.fixture
def mock_live_snapshots():
    """Create mock ProductionStatus objects (live snapshots) with various statuses."""
    now = _utcnow()
    return [
        # Ahead of target
        ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Grinder 1",
            area="Grinding",
            snapshot_timestamp=now,
            current_output=1100,  # +10% ahead
            target_output=1000,
            output_variance=100,
            status="on_target",
        ),
        # On track
        ProductionStatus(
            id="snap-2",
            asset_id="asset-2",
            asset_name="Grinder 2",
            area="Grinding",
            snapshot_timestamp=now,
            current_output=980,  # -2% within threshold
            target_output=1000,
            output_variance=-20,
            status="on_target",
        ),
        # Behind target
        ProductionStatus(
            id="snap-3",
            asset_id="asset-3",
            asset_name="CAMA 800-1",
            area="Packaging",
            snapshot_timestamp=now,
            current_output=800,  # -20% behind
            target_output=1000,
            output_variance=-200,
            status="behind",
        ),
        # Far behind target
        ProductionStatus(
            id="snap-4",
            asset_id="asset-4",
            asset_name="Press 1",
            area="Pressing",
            snapshot_timestamp=now,
            current_output=600,  # -40% behind
            target_output=1000,
            output_variance=-400,
            status="behind",
        ),
    ]


@pytest.fixture
def mock_live_snapshots_stale():
    """Create mock ProductionStatus objects with stale data."""
    old_time = _utcnow() - timedelta(minutes=45)
    return [
        ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Grinder 1",
            area="Grinding",
            snapshot_timestamp=old_time,
            current_output=850,
            target_output=1000,
            output_variance=-150,
            status="behind",
        ),
    ]


@pytest.fixture
def mock_live_snapshots_grinding_area():
    """Create mock snapshots for Grinding area only."""
    now = _utcnow()
    return [
        ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Grinder 1",
            area="Grinding",
            snapshot_timestamp=now,
            current_output=1100,
            target_output=1000,
            output_variance=100,
            status="on_target",
        ),
        ProductionStatus(
            id="snap-2",
            asset_id="asset-2",
            asset_name="Grinder 2",
            area="Grinding",
            snapshot_timestamp=now,
            current_output=980,
            target_output=1000,
            output_variance=-20,
            status="on_target",
        ),
    ]


@pytest.fixture
def mock_shift_targets():
    """Create mock ShiftTarget objects."""
    return [
        ShiftTarget(id="target-1", asset_id="asset-1", target_output=1000, target_oee=85.0),
        ShiftTarget(id="target-2", asset_id="asset-2", target_output=1000, target_oee=85.0),
        ShiftTarget(id="target-3", asset_id="asset-3", target_output=1000, target_oee=85.0),
        ShiftTarget(id="target-4", asset_id="asset-4", target_output=1000, target_oee=85.0),
    ]


def create_data_result(data: Any, table_name: str, query: str = None) -> DataResult:
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
        query=query or f"Test query on {table_name}",
        row_count=row_count,
    )


# =============================================================================
# Test: Tool Properties (AC#7 Tool Registration)
# =============================================================================


class TestProductionStatusToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, production_status_tool):
        """AC#7: Tool name is 'production_status'."""
        assert production_status_tool.name == "production_status"

    def test_tool_description_for_intent_matching(self, production_status_tool):
        """AC#7: Tool description enables correct intent matching."""
        description = production_status_tool.description.lower()
        assert "production" in description
        assert "status" in description or "target" in description
        assert "how" in description or "doing" in description

    def test_tool_args_schema(self, production_status_tool):
        """AC#7: Args schema is ProductionStatusInput."""
        assert production_status_tool.args_schema == ProductionStatusInput

    def test_tool_citations_required(self, production_status_tool):
        """AC#7: Citations are required."""
        assert production_status_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestProductionStatusInput:
    """Tests for ProductionStatusInput validation."""

    def test_valid_input_no_area(self):
        """Test valid input with no area (plant-wide)."""
        input_model = ProductionStatusInput()
        assert input_model.area is None

    def test_valid_input_with_area(self):
        """Test valid input with area filter."""
        input_model = ProductionStatusInput(area="Grinding")
        assert input_model.area == "Grinding"


# =============================================================================
# Test: Plant-Wide Production Status (AC#1)
# =============================================================================


class TestPlantWideProductionStatus:
    """Tests for plant-wide production status queries."""

    @pytest.mark.asyncio
    async def test_plant_wide_returns_success(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#1: Successful plant-wide query returns all expected data."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert result.success is True
            assert result.data is not None
            assert result.data["scope"] == "all"

    @pytest.mark.asyncio
    async def test_plant_wide_returns_all_assets(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#1: Response includes status for each asset."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assets = result.data["assets"]
            assert len(assets) == 4  # All 4 assets

    @pytest.mark.asyncio
    async def test_plant_wide_includes_variance(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#1: Response includes variance (units and percentage)."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            for asset in result.data["assets"]:
                assert "variance_units" in asset
                assert "variance_percent" in asset

    @pytest.mark.asyncio
    async def test_plant_wide_sorted_by_variance_worst_first(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#1: Assets are sorted by variance (worst first)."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assets = result.data["assets"]
            variance_values = [a["variance_percent"] for a in assets]
            # Should be sorted ascending (most negative first)
            assert variance_values == sorted(variance_values)

    @pytest.mark.asyncio
    async def test_plant_wide_includes_data_freshness(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#1: Response includes data freshness timestamp."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert "data_freshness" in result.data
            for asset in result.data["assets"]:
                assert "snapshot_time" in asset


# =============================================================================
# Test: Area-Filtered Production Status (AC#2)
# =============================================================================


class TestAreaFilteredProductionStatus:
    """Tests for area-filtered production status queries."""

    @pytest.mark.asyncio
    async def test_area_filter_returns_area_assets_only(
        self,
        production_status_tool,
        mock_live_snapshots_grinding_area,
        mock_shift_targets,
    ):
        """AC#2: Filters to assets in the specified area only."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_live_snapshots_by_area.return_value = create_data_result(
                mock_live_snapshots_grinding_area, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun(area="Grinding")

            assert result.data["scope"] == "Grinding"
            assets = result.data["assets"]
            assert len(assets) == 2  # Only Grinding area assets
            for asset in assets:
                assert asset["area"] == "Grinding"

    @pytest.mark.asyncio
    async def test_area_filter_includes_area_totals(
        self,
        production_status_tool,
        mock_live_snapshots_grinding_area,
        mock_shift_targets,
    ):
        """AC#2: Shows area-level totals (total output, total target, variance)."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_live_snapshots_by_area.return_value = create_data_result(
                mock_live_snapshots_grinding_area, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun(area="Grinding")

            # Should have area totals
            assert result.data["area_output"] is not None
            assert result.data["area_target"] is not None
            assert result.data["area_variance_percent"] is not None

            # Verify calculation
            expected_output = 1100 + 980  # 2080
            expected_target = 1000 + 1000  # 2000
            assert result.data["area_output"] == expected_output
            assert result.data["area_target"] == expected_target

    @pytest.mark.asyncio
    async def test_area_filter_ranks_assets_by_performance(
        self,
        production_status_tool,
        mock_live_snapshots_grinding_area,
        mock_shift_targets,
    ):
        """AC#2: Ranks assets within the area by performance."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_live_snapshots_by_area.return_value = create_data_result(
                mock_live_snapshots_grinding_area, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun(area="Grinding")

            assets = result.data["assets"]
            variance_values = [a["variance_percent"] for a in assets]
            # Should be sorted by variance (worst first)
            assert variance_values == sorted(variance_values)


# =============================================================================
# Test: Data Freshness Warning (AC#3)
# =============================================================================


class TestDataFreshnessWarning:
    """Tests for data freshness warning functionality."""

    @pytest.mark.asyncio
    async def test_stale_data_includes_warning(
        self,
        production_status_tool,
        mock_live_snapshots_stale,
        mock_shift_targets,
    ):
        """AC#3: Includes warning when data is >30 minutes old."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots_stale, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert result.data["has_stale_warning"] is True
            assert result.data["stale_warning_message"] is not None
            assert "minutes ago" in result.data["stale_warning_message"].lower()

    @pytest.mark.asyncio
    async def test_fresh_data_no_warning(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#3: No warning when data is fresh."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert result.data["has_stale_warning"] is False
            assert result.data["stale_warning_message"] is None
            assert result.data["data_freshness"] == "live"

    @pytest.mark.asyncio
    async def test_stale_data_still_shows_values(
        self,
        production_status_tool,
        mock_live_snapshots_stale,
        mock_shift_targets,
    ):
        """AC#3: Still shows available data with the warning."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots_stale, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            # Still shows data even with warning
            assert len(result.data["assets"]) > 0
            assert result.data["summary"]["total_assets"] > 0


# =============================================================================
# Test: Status Indicators (AC#4)
# =============================================================================


class TestStatusIndicators:
    """Tests for status determination."""

    def test_ahead_status_threshold(self, production_status_tool):
        """AC#4: Assets >= 5% ahead are marked 'ahead'."""
        # Create a mock snapshot with +10% variance
        mock_snapshot = ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Test Asset",
            area="Test",
            snapshot_timestamp=_utcnow(),
            current_output=1100,  # +10%
            target_output=1000,
            output_variance=100,
            status="on_target",
        )
        mock_target = ShiftTarget(
            id="target-1", asset_id="asset-1", target_output=1000
        )

        result = production_status_tool._process_snapshot(
            mock_snapshot, {"asset-1": mock_target}
        )

        assert result.status == "ahead"
        assert result.status_color == "green"

    def test_on_track_status_threshold(self, production_status_tool):
        """AC#4: Assets within 5% are marked 'on_track'."""
        # Create a mock snapshot with -2% variance
        mock_snapshot = ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Test Asset",
            area="Test",
            snapshot_timestamp=_utcnow(),
            current_output=980,  # -2%
            target_output=1000,
            output_variance=-20,
            status="on_target",
        )
        mock_target = ShiftTarget(
            id="target-1", asset_id="asset-1", target_output=1000
        )

        result = production_status_tool._process_snapshot(
            mock_snapshot, {"asset-1": mock_target}
        )

        assert result.status == "on_track"
        assert result.status_color == "yellow"

    def test_behind_status_threshold(self, production_status_tool):
        """AC#4: Assets > 5% behind are marked 'behind'."""
        # Create a mock snapshot with -10% variance
        mock_snapshot = ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Test Asset",
            area="Test",
            snapshot_timestamp=_utcnow(),
            current_output=900,  # -10%
            target_output=1000,
            output_variance=-100,
            status="behind",
        )
        mock_target = ShiftTarget(
            id="target-1", asset_id="asset-1", target_output=1000
        )

        result = production_status_tool._process_snapshot(
            mock_snapshot, {"asset-1": mock_target}
        )

        assert result.status == "behind"
        assert result.status_color == "red"

    def test_edge_case_exactly_5_percent_ahead(self, production_status_tool):
        """AC#4: Exactly +5% is 'ahead'."""
        mock_snapshot = ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Test Asset",
            area="Test",
            snapshot_timestamp=_utcnow(),
            current_output=1050,  # Exactly +5%
            target_output=1000,
            output_variance=50,
            status="on_target",
        )
        mock_target = ShiftTarget(
            id="target-1", asset_id="asset-1", target_output=1000
        )

        result = production_status_tool._process_snapshot(
            mock_snapshot, {"asset-1": mock_target}
        )

        assert result.status == "ahead"

    def test_edge_case_exactly_5_percent_behind(self, production_status_tool):
        """AC#4: Exactly -5% is 'behind'."""
        mock_snapshot = ProductionStatus(
            id="snap-1",
            asset_id="asset-1",
            asset_name="Test Asset",
            area="Test",
            snapshot_timestamp=_utcnow(),
            current_output=950,  # Exactly -5%
            target_output=1000,
            output_variance=-50,
            status="behind",
        )
        mock_target = ShiftTarget(
            id="target-1", asset_id="asset-1", target_output=1000
        )

        result = production_status_tool._process_snapshot(
            mock_snapshot, {"asset-1": mock_target}
        )

        assert result.status == "behind"


# =============================================================================
# Test: Summary Statistics (AC#5)
# =============================================================================


class TestSummaryStatistics:
    """Tests for summary statistics calculation."""

    @pytest.mark.asyncio
    async def test_summary_includes_counts_by_status(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#5: Summary includes total assets and count by status."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            summary = result.data["summary"]
            assert summary["total_assets"] == 4
            assert summary["ahead_count"] == 1  # Grinder 1
            assert summary["on_track_count"] == 1  # Grinder 2
            assert summary["behind_count"] == 2  # CAMA, Press 1

    @pytest.mark.asyncio
    async def test_summary_includes_overall_variance(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#5: Summary includes overall variance."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            summary = result.data["summary"]
            # Total output: 1100 + 980 + 800 + 600 = 3480
            # Total target: 4000
            assert summary["total_output"] == 3480
            assert summary["total_target"] == 4000
            assert summary["total_variance_units"] == -520
            # -520/4000 = -13%
            assert summary["total_variance_percent"] == -13.0

    @pytest.mark.asyncio
    async def test_summary_highlights_assets_needing_attention(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#5: Summary highlights assets needing attention (behind)."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            summary = result.data["summary"]
            # Should list the assets that are behind
            assert len(summary["assets_needing_attention"]) > 0
            assert len(summary["assets_needing_attention"]) <= 5  # Max 5


# =============================================================================
# Test: No Live Data Handling (AC#6)
# =============================================================================


class TestNoLiveDataHandling:
    """Tests for no live data handling."""

    @pytest.mark.asyncio
    async def test_no_data_returns_helpful_message(
        self,
        production_status_tool,
        mock_shift_targets,
    ):
        """AC#6: Returns 'No real-time production data available' message."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert result.success is True
            assert result.data["no_data"] is True
            assert "no real-time production data" in result.data["message"].lower()

    @pytest.mark.asyncio
    async def test_no_data_suggests_troubleshooting(
        self,
        production_status_tool,
        mock_shift_targets,
    ):
        """AC#6: Suggests checking if polling pipeline is running."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert "suggestion" in result.data
            assert "polling" in result.data["suggestion"].lower()
            assert "troubleshooting" in result.data
            assert len(result.data["troubleshooting"]) > 0

    @pytest.mark.asyncio
    async def test_no_data_does_not_fabricate_values(
        self,
        production_status_tool,
        mock_shift_targets,
    ):
        """AC#6: Does NOT fabricate any values."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            # Should not have fake asset data
            assert "assets" not in result.data or result.data.get("assets") is None
            assert "summary" not in result.data or result.data.get("summary") is None


# =============================================================================
# Test: Citation Compliance (AC#1)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation and compliance."""

    @pytest.mark.asyncio
    async def test_response_includes_citations(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#1: All data includes citations."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            # Should have citations for live_snapshots and shift_targets
            assert len(result.citations) >= 2

    @pytest.mark.asyncio
    async def test_citation_format(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """Citations follow format with source, table, timestamp."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            for citation in result.citations:
                assert citation.source is not None
                assert citation.table is not None
                assert citation.timestamp is not None


# =============================================================================
# Test: Caching Support (AC#8)
# =============================================================================


class TestCachingSupport:
    """Tests for cache metadata."""

    @pytest.mark.asyncio
    async def test_cache_tier_is_live(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#8: Cache tier is 'live' for real-time data."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert result.metadata["cache_tier"] == "live"

    @pytest.mark.asyncio
    async def test_ttl_is_60_seconds(
        self,
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """AC#8: TTL is 60 seconds."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert result.metadata["ttl_seconds"] == CACHE_TTL_LIVE
            assert result.metadata["ttl_seconds"] == 60

    @pytest.mark.asyncio
    async def test_cache_metadata_on_no_data(
        self,
        production_status_tool,
        mock_shift_targets,
    ):
        """AC#8: Cache metadata included even on no data response."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert result.metadata["cache_tier"] == "live"
            assert result.metadata["ttl_seconds"] == 60


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_data_source_error_returns_friendly_message(
        self, production_status_tool
    ):
        """Returns user-friendly error message for data source errors."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="live_snapshots",
            )

            result = await production_status_tool._arun()

            assert result.success is False
            assert result.error_message is not None
            assert "Unable to retrieve" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(self, production_status_tool):
        """Unexpected errors are caught and logged."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.side_effect = RuntimeError(
                "Unexpected failure"
            )

            result = await production_status_tool._arun()

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
        production_status_tool,
        mock_live_snapshots,
        mock_shift_targets,
    ):
        """Follow-up questions are generated in metadata."""
        with patch(
            "app.services.agent.tools.production_status.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_live_snapshots, "live_snapshots"
            )
            mock_ds.get_all_shift_targets.return_value = create_data_result(
                mock_shift_targets, "shift_targets"
            )

            result = await production_status_tool._arun()

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3


# =============================================================================
# Test: Tool Registration (Integration)
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = ProductionStatusTool()
        assert tool is not None
        assert tool.name == "production_status"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = ProductionStatusTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)
