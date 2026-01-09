"""
Tests for Downtime Analysis Tool (Story 5.5)

Comprehensive test coverage for all acceptance criteria:
AC#1: Asset-Level Downtime Query - Returns total downtime, reasons ranked by duration
AC#2: Area-Level Downtime Query - Aggregates across all assets in area
AC#3: No Downtime Handling - Honest messaging when no downtime recorded
AC#4: Time Range Support - Parses natural language time ranges
AC#5: Pareto Analysis - 80/20 rule, cumulative percentages, vital few identification
AC#6: Safety Event Highlighting - Safety-related reasons flagged and shown first
AC#7: Tool Registration - Auto-discovered by agent framework
AC#8: Caching Support - Returns cache metadata (daily tier, 15 min TTL)
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional
from unittest.mock import AsyncMock, patch

from app.services.agent.base import Citation, ToolResult
from app.services.agent.data_source.protocol import (
    Asset,
    DataResult,
    OEEMetrics,
)
from app.services.agent.tools.downtime_analysis import (
    DowntimeAnalysisTool,
    DowntimeAnalysisInput,
    DowntimeAnalysisOutput,
    DowntimeReason,
    AssetDowntimeBreakdown,
    CACHE_TTL_DAILY,
    SAFETY_KEYWORDS,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def downtime_analysis_tool():
    """Create an instance of DowntimeAnalysisTool."""
    return DowntimeAnalysisTool()


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
def mock_oee_metrics_with_downtime():
    """Create mock OEE metrics with downtime_reasons."""
    base_date = date.today() - timedelta(days=1)
    return [
        OEEMetrics(
            id="oee-1",
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            report_date=base_date,
            oee_percentage=Decimal("78.0"),
            availability=Decimal("85.0"),
            performance=Decimal("92.0"),
            quality=Decimal("99.5"),
            actual_output=1800,
            target_output=2000,
            downtime_minutes=127,
            downtime_reasons={
                "Material Jam": 48,
                "Blade Change": 35,
                "Operator Break": 25,
                "Safety Stop": 19,
            },
            waste_count=10,
        ),
    ]


@pytest.fixture
def mock_oee_metrics_no_downtime():
    """Create mock OEE metrics with no downtime."""
    base_date = date.today() - timedelta(days=1)
    return [
        OEEMetrics(
            id="oee-1",
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            report_date=base_date,
            oee_percentage=Decimal("95.0"),
            availability=Decimal("98.0"),
            performance=Decimal("97.0"),
            quality=Decimal("99.9"),
            actual_output=1950,
            target_output=2000,
            downtime_minutes=0,
            downtime_reasons=None,
            waste_count=2,
        ),
    ]


@pytest.fixture
def mock_oee_metrics_area():
    """Create mock OEE metrics for multiple assets in an area."""
    base_date = date.today() - timedelta(days=1)
    return [
        # Asset 1: High downtime
        OEEMetrics(
            id="oee-a1-1",
            asset_id="asset-1",
            report_date=base_date,
            oee_percentage=Decimal("65.0"),
            availability=Decimal("75.0"),
            performance=Decimal("88.0"),
            quality=Decimal("98.5"),
            actual_output=1400,
            target_output=2000,
            downtime_minutes=120,
            downtime_reasons={
                "Material Jam": 60,
                "Blade Change": 40,
                "Calibration": 20,
            },
        ),
        # Asset 2: Medium downtime
        OEEMetrics(
            id="oee-a2-1",
            asset_id="asset-2",
            report_date=base_date,
            oee_percentage=Decimal("78.0"),
            availability=Decimal("85.0"),
            performance=Decimal("92.0"),
            quality=Decimal("99.0"),
            actual_output=1750,
            target_output=2000,
            downtime_minutes=60,
            downtime_reasons={
                "Material Jam": 35,
                "Operator Break": 25,
            },
        ),
        # Asset 3: Low downtime with safety event
        OEEMetrics(
            id="oee-a3-1",
            asset_id="asset-3",
            report_date=base_date,
            oee_percentage=Decimal("85.0"),
            availability=Decimal("90.0"),
            performance=Decimal("95.0"),
            quality=Decimal("99.5"),
            actual_output=1900,
            target_output=2000,
            downtime_minutes=30,
            downtime_reasons={
                "Safety Issue": 15,
                "Blade Change": 15,
            },
        ),
        # Asset 4: No downtime
        OEEMetrics(
            id="oee-a4-1",
            asset_id="asset-4",
            report_date=base_date,
            oee_percentage=Decimal("95.0"),
            availability=Decimal("98.0"),
            performance=Decimal("97.0"),
            quality=Decimal("99.9"),
            actual_output=1950,
            target_output=2000,
            downtime_minutes=0,
            downtime_reasons=None,
        ),
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


class TestDowntimeAnalysisToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, downtime_analysis_tool):
        """AC#7: Tool name is 'downtime_analysis'."""
        assert downtime_analysis_tool.name == "downtime_analysis"

    def test_tool_description_for_intent_matching(self, downtime_analysis_tool):
        """AC#7: Tool description enables correct intent matching for downtime questions."""
        description = downtime_analysis_tool.description.lower()
        assert "downtime" in description
        assert "pareto" in description
        assert "asset" in description or "area" in description

    def test_tool_args_schema(self, downtime_analysis_tool):
        """AC#7: Args schema is DowntimeAnalysisInput."""
        assert downtime_analysis_tool.args_schema == DowntimeAnalysisInput

    def test_tool_citations_required(self, downtime_analysis_tool):
        """AC#7: Citations are required."""
        assert downtime_analysis_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestDowntimeAnalysisInput:
    """Tests for DowntimeAnalysisInput validation."""

    def test_valid_input_minimal(self):
        """Test valid input with just scope."""
        input_model = DowntimeAnalysisInput(scope="Grinder 5")
        assert input_model.scope == "Grinder 5"
        assert input_model.time_range == "yesterday"

    def test_valid_input_with_time_range(self):
        """Test valid input with custom time range."""
        input_model = DowntimeAnalysisInput(scope="Grinding", time_range="last week")
        assert input_model.scope == "Grinding"
        assert input_model.time_range == "last week"

    def test_scope_required(self):
        """Test that scope is required."""
        with pytest.raises(ValueError):
            DowntimeAnalysisInput()


# =============================================================================
# Test: Time Range Parsing (AC#4)
# =============================================================================


class TestTimeRangeParsing:
    """Tests for time range parsing functionality."""

    def test_parse_yesterday(self, downtime_analysis_tool):
        """AC#4: Default is yesterday (T-1)."""
        start, end = downtime_analysis_tool._parse_time_range("yesterday")
        expected = date.today() - timedelta(days=1)
        assert start == expected
        assert end == expected

    def test_parse_empty_defaults_to_yesterday(self, downtime_analysis_tool):
        """AC#4: Empty string defaults to yesterday."""
        start, end = downtime_analysis_tool._parse_time_range("")
        expected = date.today() - timedelta(days=1)
        assert start == expected
        assert end == expected

    def test_parse_today(self, downtime_analysis_tool):
        """AC#4: 'today' returns today's date."""
        start, end = downtime_analysis_tool._parse_time_range("today")
        assert start == date.today()
        assert end == date.today()

    def test_parse_last_week(self, downtime_analysis_tool):
        """AC#4: 'last week' returns 7 days ending yesterday."""
        start, end = downtime_analysis_tool._parse_time_range("last week")
        yesterday = date.today() - timedelta(days=1)
        assert end == yesterday
        assert start == yesterday - timedelta(days=6)
        assert (end - start).days == 6

    def test_parse_last_7_days(self, downtime_analysis_tool):
        """AC#4: 'last 7 days' same as 'last week'."""
        start, end = downtime_analysis_tool._parse_time_range("last 7 days")
        yesterday = date.today() - timedelta(days=1)
        assert end == yesterday
        assert start == yesterday - timedelta(days=6)

    def test_parse_this_week(self, downtime_analysis_tool):
        """AC#4: 'this week' returns Monday to yesterday."""
        start, end = downtime_analysis_tool._parse_time_range("this week")
        today = date.today()
        yesterday = today - timedelta(days=1)
        monday = today - timedelta(days=today.weekday())
        assert start == monday
        assert end == yesterday

    def test_parse_unrecognized_defaults_to_yesterday(self, downtime_analysis_tool):
        """AC#4: Unrecognized time range defaults to yesterday."""
        start, end = downtime_analysis_tool._parse_time_range("some random text")
        expected = date.today() - timedelta(days=1)
        assert start == expected
        assert end == expected


# =============================================================================
# Test: Asset-Level Downtime Query (AC#1)
# =============================================================================


class TestAssetLevelDowntimeQuery:
    """Tests for asset-level downtime queries."""

    @pytest.mark.asyncio
    async def test_asset_downtime_returns_success(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """AC#1: Successful asset downtime query returns all expected data."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            assert result.success is True
            assert result.data is not None
            assert result.data["scope_type"] == "asset"
            assert result.data["scope_name"] == "Grinder 5"

    @pytest.mark.asyncio
    async def test_asset_downtime_includes_pareto_analysis(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """AC#1: Response includes Pareto analysis with reasons ranked by duration."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            reasons = result.data["reasons"]
            assert len(reasons) > 0
            # Reasons should be sorted by duration (Safety first, then by minutes)
            # Verify total downtime
            assert result.data["total_downtime_minutes"] == 127

    @pytest.mark.asyncio
    async def test_asset_downtime_includes_percentages(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """AC#1: Response includes percentage of total downtime per reason."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            reasons = result.data["reasons"]
            for reason in reasons:
                assert 0 <= reason["percentage"] <= 100
                assert 0 <= reason["cumulative_percentage"] <= 100


# =============================================================================
# Test: Area-Level Downtime Query (AC#2)
# =============================================================================


class TestAreaLevelDowntimeQuery:
    """Tests for area-level downtime queries."""

    @pytest.mark.asyncio
    async def test_area_downtime_aggregates_assets(
        self,
        downtime_analysis_tool,
        mock_assets_in_area,
        mock_oee_metrics_area,
    ):
        """AC#2: Returns aggregated downtime across all assets in area."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_assets_by_area.return_value = create_data_result(
                mock_assets_in_area, "assets"
            )

            # Return different metrics for each asset
            def get_oee_for_asset(asset_id, start, end):
                for m in mock_oee_metrics_area:
                    if m.asset_id == asset_id:
                        return create_data_result([m], "daily_summaries")
                return create_data_result([], "daily_summaries")

            mock_ds.get_oee.side_effect = get_oee_for_asset

            result = await downtime_analysis_tool._arun(scope="Grinding area")

            assert result.success is True
            assert result.data["scope_type"] == "area"
            assert result.data["total_downtime_minutes"] > 0

    @pytest.mark.asyncio
    async def test_area_downtime_includes_asset_breakdown(
        self,
        downtime_analysis_tool,
        mock_assets_in_area,
        mock_oee_metrics_area,
    ):
        """AC#2: Shows which assets contributed most to each reason."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_assets_by_area.return_value = create_data_result(
                mock_assets_in_area, "assets"
            )

            def get_oee_for_asset(asset_id, start, end):
                for m in mock_oee_metrics_area:
                    if m.asset_id == asset_id:
                        return create_data_result([m], "daily_summaries")
                return create_data_result([], "daily_summaries")

            mock_ds.get_oee.side_effect = get_oee_for_asset

            result = await downtime_analysis_tool._arun(scope="Grinding area")

            assert result.data["asset_breakdown"] is not None
            assert len(result.data["asset_breakdown"]) > 0
            # Should be sorted by downtime
            breakdown = result.data["asset_breakdown"]
            downtime_values = [a["total_minutes"] for a in breakdown]
            assert downtime_values == sorted(downtime_values, reverse=True)

    @pytest.mark.asyncio
    async def test_area_downtime_identifies_worst_asset(
        self,
        downtime_analysis_tool,
        mock_assets_in_area,
        mock_oee_metrics_area,
    ):
        """AC#2: Identifies the worst performing asset in the area."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_assets_by_area.return_value = create_data_result(
                mock_assets_in_area, "assets"
            )

            def get_oee_for_asset(asset_id, start, end):
                for m in mock_oee_metrics_area:
                    if m.asset_id == asset_id:
                        return create_data_result([m], "daily_summaries")
                return create_data_result([], "daily_summaries")

            mock_ds.get_oee.side_effect = get_oee_for_asset

            result = await downtime_analysis_tool._arun(scope="Grinding area")

            assert result.data["worst_asset"] is not None
            assert result.data["worst_asset"] == "Grinder 1"  # Has most downtime


# =============================================================================
# Test: No Downtime Handling (AC#3)
# =============================================================================


class TestNoDowntimeHandling:
    """Tests for no downtime handling."""

    @pytest.mark.asyncio
    async def test_no_downtime_returns_success_message(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_no_downtime,
    ):
        """AC#3: Returns success message when no downtime recorded."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_no_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            assert result.success is True
            assert result.data["no_downtime"] is True
            assert result.data["uptime_percentage"] == 100.0
            assert "congratulations" in result.data

    @pytest.mark.asyncio
    async def test_no_downtime_includes_message(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_no_downtime,
    ):
        """AC#3: Response states '[Asset] had no recorded downtime in [time range]'."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_no_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            message = result.data.get("message", "")
            assert "no recorded downtime" in message.lower()

    @pytest.mark.asyncio
    async def test_asset_not_found(self, downtime_analysis_tool):
        """AC#3: Returns helpful message when asset not found."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                None, "assets"
            )

            result = await downtime_analysis_tool._arun(scope="NonExistentAsset")

            assert result.success is True
            assert result.data["no_data"] is True
            assert "not found" in result.data["message"].lower()


# =============================================================================
# Test: Pareto Analysis (AC#5)
# =============================================================================


class TestParetoAnalysis:
    """Tests for Pareto analysis functionality."""

    def test_calculate_pareto_sorts_by_duration(self, downtime_analysis_tool):
        """AC#5: Reasons are sorted by descending duration."""
        reasons = {
            "Reason A": 20,
            "Reason B": 50,
            "Reason C": 30,
        }

        pareto_list, threshold_idx = downtime_analysis_tool._calculate_pareto(reasons)

        minutes = [r.total_minutes for r in pareto_list]
        assert minutes == sorted(minutes, reverse=True)

    def test_calculate_pareto_calculates_percentages(self, downtime_analysis_tool):
        """AC#5: Calculates percentage of total for each reason."""
        reasons = {
            "Reason A": 25,
            "Reason B": 50,
            "Reason C": 25,
        }

        pareto_list, threshold_idx = downtime_analysis_tool._calculate_pareto(reasons)

        # Reason B should be 50%
        reason_b = next(r for r in pareto_list if r.reason_code == "Reason B")
        assert reason_b.percentage == 50.0

    def test_calculate_pareto_calculates_cumulative(self, downtime_analysis_tool):
        """AC#5: Calculates cumulative percentage."""
        reasons = {
            "Reason A": 50,
            "Reason B": 30,
            "Reason C": 20,
        }

        pareto_list, threshold_idx = downtime_analysis_tool._calculate_pareto(reasons)

        # First reason should be 50% cumulative
        assert pareto_list[0].cumulative_percentage == 50.0
        # Second reason should be 80% cumulative
        assert pareto_list[1].cumulative_percentage == 80.0
        # Third reason should be 100% cumulative
        assert pareto_list[2].cumulative_percentage == 100.0

    def test_calculate_pareto_identifies_80_threshold(self, downtime_analysis_tool):
        """AC#5: Identifies the 80% threshold index."""
        reasons = {
            "Reason A": 50,
            "Reason B": 30,
            "Reason C": 20,
        }

        pareto_list, threshold_idx = downtime_analysis_tool._calculate_pareto(reasons)

        # 80% threshold is at index 1 (50 + 30 = 80)
        assert threshold_idx == 1

    def test_calculate_pareto_marks_vital_few(self, downtime_analysis_tool):
        """AC#5: Marks reasons in the vital few (up to 80%)."""
        reasons = {
            "Reason A": 50,
            "Reason B": 30,
            "Reason C": 20,
        }

        pareto_list, threshold_idx = downtime_analysis_tool._calculate_pareto(reasons)

        # Reasons A and B should be vital few
        assert pareto_list[0].is_vital_few is True
        assert pareto_list[1].is_vital_few is True
        # Reason C should not be vital few
        assert pareto_list[2].is_vital_few is False

    def test_calculate_pareto_empty_returns_empty(self, downtime_analysis_tool):
        """AC#5: Empty reasons returns empty list."""
        pareto_list, threshold_idx = downtime_analysis_tool._calculate_pareto({})

        assert pareto_list == []
        assert threshold_idx is None


# =============================================================================
# Test: Safety Event Highlighting (AC#6)
# =============================================================================


class TestSafetyEventHighlighting:
    """Tests for safety event highlighting."""

    def test_is_safety_related_detects_safety_keywords(self, downtime_analysis_tool):
        """AC#6: Detects safety-related reason codes."""
        assert downtime_analysis_tool._is_safety_related("Safety Stop") is True
        assert downtime_analysis_tool._is_safety_related("emergency stop") is True
        assert downtime_analysis_tool._is_safety_related("e-stop triggered") is True
        assert downtime_analysis_tool._is_safety_related("lockout procedure") is True
        assert downtime_analysis_tool._is_safety_related("Safety Issue") is True

    def test_is_safety_related_returns_false_for_non_safety(self, downtime_analysis_tool):
        """AC#6: Returns False for non-safety reasons."""
        assert downtime_analysis_tool._is_safety_related("Material Jam") is False
        assert downtime_analysis_tool._is_safety_related("Blade Change") is False
        assert downtime_analysis_tool._is_safety_related("Operator Break") is False
        assert downtime_analysis_tool._is_safety_related("Calibration") is False

    def test_safety_events_appear_first(self, downtime_analysis_tool):
        """AC#6: Safety events appear first regardless of duration."""
        reasons = {
            "Material Jam": 60,
            "Safety Stop": 10,
            "Blade Change": 40,
        }

        pareto_list, threshold_idx = downtime_analysis_tool._calculate_pareto(reasons)

        # Safety Stop should be first even though it has less duration
        assert pareto_list[0].reason_code == "Safety Stop"
        assert pareto_list[0].is_safety_related is True

    @pytest.mark.asyncio
    async def test_safety_downtime_extracted(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """AC#6: Safety-related downtime is extracted and summarized."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            # Should have safety downtime from "Safety Stop"
            assert result.data["safety_downtime_minutes"] == 19
            assert "Safety Stop" in result.data["safety_reasons"]


# =============================================================================
# Test: Citation Compliance (AC#1, AC#2)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation and compliance."""

    @pytest.mark.asyncio
    async def test_asset_query_includes_citations(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """AC#1: All values include citations."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            # Should have citations for assets and daily_summaries
            assert len(result.citations) >= 2

    @pytest.mark.asyncio
    async def test_citation_format(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """Citations follow format with source, table, timestamp."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

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
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """AC#8: Cache tier is 'daily' for historical data."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            assert result.metadata["cache_tier"] == "daily"

    @pytest.mark.asyncio
    async def test_ttl_is_15_minutes(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """AC#8: TTL is 900 seconds (15 minutes)."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            assert result.metadata["ttl_seconds"] == CACHE_TTL_DAILY
            assert result.metadata["ttl_seconds"] == 900

    @pytest.mark.asyncio
    async def test_cache_metadata_on_no_downtime(
        self,
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_no_downtime,
    ):
        """AC#8: Cache metadata included even on no downtime response."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_no_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            assert result.metadata["cache_tier"] == "daily"
            assert result.metadata["ttl_seconds"] == 900


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_data_source_error_returns_friendly_message(
        self, downtime_analysis_tool
    ):
        """Returns user-friendly error message for data source errors."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="assets",
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            assert result.success is False
            assert result.error_message is not None
            assert "Unable to retrieve" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(self, downtime_analysis_tool):
        """Unexpected errors are caught and logged."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.side_effect = RuntimeError(
                "Unexpected failure"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

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
        downtime_analysis_tool,
        mock_asset,
        mock_oee_metrics_with_downtime,
    ):
        """Follow-up questions are generated in metadata."""
        with patch(
            "app.services.agent.tools.downtime_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_asset_by_name.return_value = create_data_result(
                mock_asset, "assets"
            )
            mock_ds.get_downtime.return_value = create_data_result(
                [], "daily_summaries"
            )
            mock_ds.get_oee.return_value = create_data_result(
                mock_oee_metrics_with_downtime, "daily_summaries"
            )

            result = await downtime_analysis_tool._arun(scope="Grinder 5")

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3


# =============================================================================
# Test: Tool Registration (Integration)
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = DowntimeAnalysisTool()
        assert tool is not None
        assert tool.name == "downtime_analysis"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = DowntimeAnalysisTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)
