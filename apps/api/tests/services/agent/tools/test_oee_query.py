"""
Tests for OEE Query Tool (Story 5.4)

Comprehensive test coverage for all acceptance criteria:
AC#1: Asset-Level OEE Query - Returns OEE with A/P/Q breakdown and target comparison
AC#2: Area-Level OEE Query - Returns aggregated OEE with asset ranking
AC#3: Time Range Support - Parses natural language time ranges
AC#4: Target Comparison - Shows variance from target
AC#5: No Data Handling - Honest messaging when data is missing
AC#6: OEE Component Breakdown - Identifies biggest opportunity
AC#7: Tool Registration - Auto-discovered by agent framework
AC#8: Caching Support - Returns cache metadata (daily tier, 15 min TTL)
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.agent import OEETrend
from app.services.agent.base import Citation, ToolResult
from app.services.agent.data_source.protocol import (
    Asset,
    DataResult,
    OEEMetrics,
    ShiftTarget,
)
from app.services.agent.tools.oee_query import (
    OEEQueryTool,
    OEEQueryInput,
    OEEQueryOutput,
    OEEComponentBreakdown,
    OEEAssetResult,
    CACHE_TTL_DAILY,
    DEFAULT_TARGET_OEE,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def oee_query_tool():
    """Create an instance of OEEQueryTool."""
    return OEEQueryTool()


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
def mock_assets_in_area():
    """Create multiple mock assets for area testing."""
    return [
        Asset(id="asset-1", name="Grinder 1", source_id="G1", area="Grinding"),
        Asset(id="asset-2", name="Grinder 2", source_id="G2", area="Grinding"),
        Asset(id="asset-3", name="Grinder 3", source_id="G3", area="Grinding"),
        Asset(id="asset-4", name="Grinder 5", source_id="G5", area="Grinding"),
    ]


@pytest.fixture
def mock_shift_target():
    """Create a mock ShiftTarget object with target_oee."""
    return ShiftTarget(
        id="770e8400-e29b-41d4-a716-446655440002",
        asset_id="550e8400-e29b-41d4-a716-446655440000",
        target_output=900,
        target_oee=85.0,
        shift="Day",
        effective_date=date.today(),
    )


@pytest.fixture
def mock_shift_target_no_oee():
    """Create a mock ShiftTarget without target_oee."""
    return ShiftTarget(
        id="770e8400-e29b-41d4-a716-446655440002",
        asset_id="550e8400-e29b-41d4-a716-446655440000",
        target_output=900,
        target_oee=None,
        shift="Day",
        effective_date=date.today(),
    )


@pytest.fixture
def mock_oee_metrics():
    """Create mock OEE metrics for 7 days."""
    base_date = date.today() - timedelta(days=1)
    metrics = []
    # OEE values that average around 79.3%
    oee_values = [78.0, 80.5, 77.2, 82.1, 79.8, 76.5, 81.0]
    avail_values = [85.0, 86.0, 84.0, 87.0, 85.0, 83.0, 86.0]
    perf_values = [92.0, 93.0, 91.0, 94.0, 93.0, 92.0, 94.0]
    qual_values = [99.5, 99.8, 99.3, 99.6, 99.4, 99.7, 99.5]

    for i in range(7):
        metrics.append(
            OEEMetrics(
                id=f"oee-{i}",
                asset_id="550e8400-e29b-41d4-a716-446655440000",
                report_date=base_date - timedelta(days=i),
                oee_percentage=Decimal(str(oee_values[i])),
                availability=Decimal(str(avail_values[i])),
                performance=Decimal(str(perf_values[i])),
                quality=Decimal(str(qual_values[i])),
                actual_output=1800,
                target_output=2000,
                downtime_minutes=36,
                waste_count=10,
            )
        )
    return metrics


@pytest.fixture
def mock_oee_metrics_area():
    """Create mock OEE metrics for multiple assets in an area."""
    base_date = date.today() - timedelta(days=1)
    metrics = []

    # Asset 1: High performer
    for i in range(7):
        metrics.append(
            OEEMetrics(
                id=f"oee-a1-{i}",
                asset_id="asset-1",
                report_date=base_date - timedelta(days=i),
                oee_percentage=Decimal("85.0"),
                availability=Decimal("90.0"),
                performance=Decimal("95.0"),
                quality=Decimal("99.5"),
                actual_output=1900,
                target_output=2000,
                downtime_minutes=20,
            )
        )

    # Asset 2: Medium performer
    for i in range(7):
        metrics.append(
            OEEMetrics(
                id=f"oee-a2-{i}",
                asset_id="asset-2",
                report_date=base_date - timedelta(days=i),
                oee_percentage=Decimal("78.0"),
                availability=Decimal("85.0"),
                performance=Decimal("92.0"),
                quality=Decimal("99.0"),
                actual_output=1750,
                target_output=2000,
                downtime_minutes=30,
            )
        )

    # Asset 3: Low performer
    for i in range(7):
        metrics.append(
            OEEMetrics(
                id=f"oee-a3-{i}",
                asset_id="asset-3",
                report_date=base_date - timedelta(days=i),
                oee_percentage=Decimal("65.0"),
                availability=Decimal("75.0"),
                performance=Decimal("88.0"),
                quality=Decimal("98.5"),
                actual_output=1400,
                target_output=2000,
                downtime_minutes=60,
            )
        )

    # Asset 4: Very low performer
    for i in range(7):
        metrics.append(
            OEEMetrics(
                id=f"oee-a4-{i}",
                asset_id="asset-4",
                report_date=base_date - timedelta(days=i),
                oee_percentage=Decimal("55.0"),
                availability=Decimal("65.0"),
                performance=Decimal("85.0"),
                quality=Decimal("99.5"),
                actual_output=1200,
                target_output=2000,
                downtime_minutes=90,
            )
        )

    return metrics


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


class TestOEEQueryToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, oee_query_tool):
        """AC#7: Tool name is 'oee_query'."""
        assert oee_query_tool.name == "oee_query"

    def test_tool_description_for_intent_matching(self, oee_query_tool):
        """AC#7: Tool description enables correct intent matching for OEE questions."""
        description = oee_query_tool.description.lower()
        assert "oee" in description
        assert "efficiency" in description
        assert "effectiveness" in description
        assert "asset" in description
        assert "area" in description

    def test_tool_args_schema(self, oee_query_tool):
        """AC#7: Args schema is OEEQueryInput."""
        assert oee_query_tool.args_schema == OEEQueryInput

    def test_tool_citations_required(self, oee_query_tool):
        """AC#7: Citations are required."""
        assert oee_query_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestOEEQueryInput:
    """Tests for OEEQueryInput validation."""

    def test_valid_input_minimal(self):
        """Test valid input with just scope."""
        input_model = OEEQueryInput(scope="Grinder 5")
        assert input_model.scope == "Grinder 5"
        assert input_model.time_range == "yesterday"

    def test_valid_input_with_time_range(self):
        """Test valid input with custom time range."""
        input_model = OEEQueryInput(scope="Grinding", time_range="last week")
        assert input_model.scope == "Grinding"
        assert input_model.time_range == "last week"

    def test_scope_required(self):
        """Test that scope is required."""
        with pytest.raises(ValueError):
            OEEQueryInput()


# =============================================================================
# Test: Time Range Parsing (AC#3)
# =============================================================================


class TestTimeRangeParsing:
    """Tests for time range parsing functionality."""

    def test_parse_yesterday(self, oee_query_tool):
        """AC#3: Default is yesterday (T-1)."""
        start, end = oee_query_tool._parse_time_range("yesterday")
        expected = date.today() - timedelta(days=1)
        assert start == expected
        assert end == expected

    def test_parse_empty_defaults_to_yesterday(self, oee_query_tool):
        """AC#3: Empty string defaults to yesterday."""
        start, end = oee_query_tool._parse_time_range("")
        expected = date.today() - timedelta(days=1)
        assert start == expected
        assert end == expected

    def test_parse_today(self, oee_query_tool):
        """AC#3: 'today' returns today's date."""
        start, end = oee_query_tool._parse_time_range("today")
        assert start == date.today()
        assert end == date.today()

    def test_parse_last_week(self, oee_query_tool):
        """AC#3: 'last week' returns 7 days ending yesterday."""
        start, end = oee_query_tool._parse_time_range("last week")
        yesterday = date.today() - timedelta(days=1)
        assert end == yesterday
        assert start == yesterday - timedelta(days=6)
        assert (end - start).days == 6

    def test_parse_last_7_days(self, oee_query_tool):
        """AC#3: 'last 7 days' same as 'last week'."""
        start, end = oee_query_tool._parse_time_range("last 7 days")
        yesterday = date.today() - timedelta(days=1)
        assert end == yesterday
        assert start == yesterday - timedelta(days=6)

    def test_parse_last_month(self, oee_query_tool):
        """AC#3: 'last month' returns 30 days."""
        start, end = oee_query_tool._parse_time_range("last month")
        yesterday = date.today() - timedelta(days=1)
        assert end == yesterday
        assert start == yesterday - timedelta(days=29)

    def test_parse_this_week(self, oee_query_tool):
        """AC#3: 'this week' returns Monday to yesterday."""
        start, end = oee_query_tool._parse_time_range("this week")
        today = date.today()
        yesterday = today - timedelta(days=1)
        monday = today - timedelta(days=today.weekday())
        assert start == monday
        assert end == yesterday

    def test_parse_unrecognized_defaults_to_yesterday(self, oee_query_tool):
        """AC#3: Unrecognized time range defaults to yesterday."""
        start, end = oee_query_tool._parse_time_range("some random text")
        expected = date.today() - timedelta(days=1)
        assert start == expected
        assert end == expected


# =============================================================================
# Test: Asset-Level OEE Query (AC#1, AC#4)
# =============================================================================


class TestAssetLevelOEEQuery:
    """Tests for asset-level OEE queries."""

    @pytest.mark.asyncio
    async def test_asset_oee_returns_success(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#1: Successful asset OEE query returns all expected data."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.success is True
            assert result.data is not None
            assert result.data["scope_type"] == "asset"
            assert result.data["scope_name"] == "Grinder 5"

    @pytest.mark.asyncio
    async def test_asset_oee_includes_components(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#1: Response includes OEE components (A, P, Q)."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            components = result.data["components"]
            assert "availability" in components
            assert "performance" in components
            assert "quality" in components
            assert 0 <= components["availability"] <= 100
            assert 0 <= components["performance"] <= 100
            assert 0 <= components["quality"] <= 100

    @pytest.mark.asyncio
    async def test_asset_oee_includes_target_comparison(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#4: Response includes target comparison when target exists."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.data["target_oee"] == 85.0
            assert result.data["variance_from_target"] is not None
            assert result.data["target_status"] in ["above_target", "below_target"]

    @pytest.mark.asyncio
    async def test_asset_oee_no_target_configured(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target_no_oee,
    ):
        """AC#4: Handles case when no target OEE is configured."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target_no_oee, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.data["target_oee"] is None
            assert result.data["variance_from_target"] is None
            assert result.data["target_status"] == "no_target"

    @pytest.mark.asyncio
    async def test_asset_oee_includes_date_range(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#3: Response includes correct date range."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(
                scope="Grinder 5", time_range="last week"
            )

            assert result.data["date_range"] is not None
            assert result.data["start_date"] is not None
            assert result.data["end_date"] is not None


# =============================================================================
# Test: Area-Level OEE Query (AC#2)
# =============================================================================


class TestAreaLevelOEEQuery:
    """Tests for area-level OEE queries."""

    @pytest.mark.asyncio
    async def test_area_oee_returns_aggregated_data(
        self,
        oee_query_tool,
        mock_assets_in_area,
        mock_oee_metrics_area,
    ):
        """AC#2: Returns aggregated OEE across all assets in area."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_assets_by_area.return_value = create_data_result(
                mock_assets_in_area, "assets"
            )
            mock_ds.get_oee_by_area.return_value = create_data_result(
                mock_oee_metrics_area, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinding area")

            assert result.success is True
            assert result.data["scope_type"] == "area"
            assert result.data["overall_oee"] is not None

    @pytest.mark.asyncio
    async def test_area_oee_includes_asset_breakdown(
        self,
        oee_query_tool,
        mock_assets_in_area,
        mock_oee_metrics_area,
    ):
        """AC#2: Lists individual asset OEE values ranked by performance."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_assets_by_area.return_value = create_data_result(
                mock_assets_in_area, "assets"
            )
            mock_ds.get_oee_by_area.return_value = create_data_result(
                mock_oee_metrics_area, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinding area")

            breakdown = result.data["asset_breakdown"]
            assert breakdown is not None
            assert len(breakdown) > 0
            # Should be sorted by OEE descending
            oee_values = [asset["oee"] for asset in breakdown]
            assert oee_values == sorted(oee_values, reverse=True)

    @pytest.mark.asyncio
    async def test_area_oee_identifies_bottom_performers(
        self,
        oee_query_tool,
        mock_assets_in_area,
        mock_oee_metrics_area,
    ):
        """AC#2: Highlights which assets are pulling down the average."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_assets_by_area.return_value = create_data_result(
                mock_assets_in_area, "assets"
            )
            mock_ds.get_oee_by_area.return_value = create_data_result(
                mock_oee_metrics_area, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                None, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinding area")

            bottom_performers = result.data["bottom_performers"]
            assert bottom_performers is not None
            assert len(bottom_performers) > 0
            # Should include low performers
            assert "Grinder 5" in bottom_performers or "Grinder 3" in bottom_performers


# =============================================================================
# Test: No Data Handling (AC#5)
# =============================================================================


class TestNoDataHandling:
    """Tests for no data handling."""

    @pytest.mark.asyncio
    async def test_asset_not_found(self, oee_query_tool):
        """AC#5: Returns helpful message when asset not found."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                None, "assets"
            )

            result = await oee_query_tool._arun(scope="NonExistentAsset")

            assert result.success is True
            assert result.data["no_data"] is True
            assert "NonExistentAsset" in result.data["message"]

    @pytest.mark.asyncio
    async def test_no_oee_data_for_time_range(
        self, oee_query_tool, mock_asset
    ):
        """AC#5: Returns helpful message when no OEE data exists."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.success is True
            assert result.data["no_data"] is True
            assert "No OEE data available" in result.data["message"]

    @pytest.mark.asyncio
    async def test_no_data_does_not_fabricate_values(
        self, oee_query_tool, mock_asset
    ):
        """AC#5: Response does NOT fabricate any values."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            # Should not have fabricated OEE values
            assert result.data.get("overall_oee") is None
            assert result.data.get("components") is None

    @pytest.mark.asyncio
    async def test_no_data_includes_citation(self, oee_query_tool, mock_asset):
        """AC#5: Includes citation for query that returned no results."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert len(result.citations) > 0


# =============================================================================
# Test: OEE Component Breakdown (AC#6)
# =============================================================================


class TestOEEComponentBreakdown:
    """Tests for OEE component analysis."""

    @pytest.mark.asyncio
    async def test_includes_oee_formula(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#6: Response shows the OEE formula."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert "oee_formula" in result.data
            assert "Availability" in result.data["oee_formula"]
            assert "Performance" in result.data["oee_formula"]
            assert "Quality" in result.data["oee_formula"]

    @pytest.mark.asyncio
    async def test_identifies_biggest_opportunity(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#6: Explains which component is the biggest opportunity."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.data["biggest_opportunity"] in [
                "availability", "performance", "quality"
            ]

    @pytest.mark.asyncio
    async def test_provides_actionable_insight(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#6: Provides actionable insight on where to focus."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            insight = result.data["opportunity_insight"]
            assert insight is not None
            assert len(insight) > 20  # Should be a meaningful message

    def test_analyze_opportunity_availability(self, oee_query_tool):
        """AC#6: Correctly identifies availability as opportunity."""
        components = OEEComponentBreakdown(
            availability=70.0,  # Lowest
            performance=95.0,
            quality=99.0,
        )
        opportunity, insight, potential = oee_query_tool._analyze_opportunity(
            components, "Test Asset"
        )
        assert opportunity == "availability"
        assert potential == 30.0
        assert "Availability" in insight

    def test_analyze_opportunity_performance(self, oee_query_tool):
        """AC#6: Correctly identifies performance as opportunity."""
        components = OEEComponentBreakdown(
            availability=95.0,
            performance=70.0,  # Lowest
            quality=99.0,
        )
        opportunity, insight, potential = oee_query_tool._analyze_opportunity(
            components, "Test Asset"
        )
        assert opportunity == "performance"
        assert potential == 30.0
        assert "Performance" in insight

    def test_analyze_opportunity_quality(self, oee_query_tool):
        """AC#6: Correctly identifies quality as opportunity."""
        components = OEEComponentBreakdown(
            availability=95.0,
            performance=95.0,
            quality=80.0,  # Lowest
        )
        opportunity, insight, potential = oee_query_tool._analyze_opportunity(
            components, "Test Asset"
        )
        assert opportunity == "quality"
        assert potential == 20.0
        assert "Quality" in insight


# =============================================================================
# Test: Citation Compliance (AC#1, AC#2)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation and compliance."""

    @pytest.mark.asyncio
    async def test_asset_query_includes_citations(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#1: All values include citations with date range."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert len(result.citations) >= 3  # assets, daily_summaries, shift_targets

    @pytest.mark.asyncio
    async def test_citation_format(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """Citations follow format with source, table, timestamp."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

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
    async def test_cache_tier_is_daily(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#8: Cache tier is 'daily' for historical data."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.metadata["cache_tier"] == "daily"

    @pytest.mark.asyncio
    async def test_ttl_is_15_minutes(
        self,
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """AC#8: TTL is 900 seconds (15 minutes)."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.metadata["ttl_seconds"] == CACHE_TTL_DAILY
            assert result.metadata["ttl_seconds"] == 900

    @pytest.mark.asyncio
    async def test_cache_metadata_on_no_data(self, oee_query_tool, mock_asset):
        """AC#8: Cache metadata included even on no data response."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.metadata["cache_tier"] == "daily"
            assert result.metadata["ttl_seconds"] == 900


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_data_source_error_returns_friendly_message(
        self, oee_query_tool
    ):
        """Returns user-friendly error message for data source errors."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="assets",
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert result.success is False
            assert result.error_message is not None
            assert "Unable to retrieve" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(self, oee_query_tool):
        """Unexpected errors are caught and logged."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.side_effect = RuntimeError(
                "Unexpected failure"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

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
        oee_query_tool,
        mock_asset,
        mock_oee_metrics,
        mock_shift_target,
    ):
        """Follow-up questions are generated in metadata."""
        with patch(
            "app.services.agent.tools.oee_query.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics, "daily_summaries"
            )
            mock_ds.get_shift_target.return_value = create_data_result(
                mock_shift_target, "shift_targets"
            )

            result = await oee_query_tool._arun(scope="Grinder 5")

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3

    def test_follow_up_questions_below_target(self, oee_query_tool):
        """Follow-up questions include target-related questions when below target."""
        output = OEEQueryOutput(
            scope_type="asset",
            scope_name="Grinder 5",
            date_range="Jan 8, 2026",
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() - timedelta(days=1),
            overall_oee=78.0,
            components=OEEComponentBreakdown(
                availability=85.0,
                performance=92.0,
                quality=99.5,
            ),
            target_oee=85.0,
            variance_from_target=-7.0,
            target_status="below_target",
            biggest_opportunity="availability",
            opportunity_insight="Focus on availability",
            potential_improvement=15.0,
            data_points=1,
        )

        questions = oee_query_tool._generate_follow_ups(output)

        # Should include question about being below target
        assert any("below" in q.lower() or "target" in q.lower() for q in questions)


# =============================================================================
# Test: Tool Registration (Integration)
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = OEEQueryTool()
        assert tool is not None
        assert tool.name == "oee_query"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = OEEQueryTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)
