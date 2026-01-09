"""
Tests for Financial Impact Tool (Story 6.2)

Comprehensive test coverage for all acceptance criteria:
AC#1: Asset-Level Financial Impact Query - Returns total loss, breakdown, hourly rate, average comparison
AC#2: Area-Level Financial Impact Query - Aggregates across assets, shows per-asset breakdown, highest-cost asset
AC#3: Missing Cost Center Data Handling - Honest response with available non-financial metrics
AC#4: Transparent Calculations - All responses show calculation formulas
AC#5: Citation Compliance - All responses include citations with source tables
AC#6: Performance Requirements - <2s response time, 15-minute cache TTL
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List
from unittest.mock import AsyncMock, patch

from app.models.agent import (
    AssetFinancialSummary,
    AverageComparison,
    CostBreakdown,
    FinancialImpactInput,
    FinancialImpactOutput,
    HighestCostAsset,
    NonFinancialMetric,
)
from app.services.agent.base import Citation, ToolResult
from app.services.agent.data_source.protocol import DataResult, FinancialMetrics
from app.services.agent.tools.financial_impact import (
    FinancialImpactTool,
    CACHE_TTL_DAILY,
    calculate_downtime_cost,
    calculate_waste_cost,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def financial_impact_tool():
    """Create an instance of FinancialImpactTool."""
    return FinancialImpactTool()


@pytest.fixture
def mock_financial_metrics_with_cost():
    """Create mock FinancialMetrics objects WITH cost center data."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-grd-005",
            asset_name="Grinder 5",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=47,
            waste_count=23,
            standard_hourly_rate=Decimal("2393.62"),
            cost_per_unit=Decimal("20.24"),
        ),
    ]


@pytest.fixture
def mock_financial_metrics_area():
    """Create mock FinancialMetrics for multiple assets in an area."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-grd-005",
            asset_name="Grinder 5",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=47,
            waste_count=23,
            standard_hourly_rate=Decimal("2393.62"),
            cost_per_unit=Decimal("20.24"),
        ),
        FinancialMetrics(
            id="rec-002",
            asset_id="asset-grd-006",
            asset_name="Grinder 6",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=30,
            waste_count=15,
            standard_hourly_rate=Decimal("2400.00"),
            cost_per_unit=Decimal("18.50"),
        ),
        FinancialMetrics(
            id="rec-003",
            asset_id="asset-grd-007",
            asset_name="Grinder 7",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=60,
            waste_count=10,
            standard_hourly_rate=Decimal("2500.00"),
            cost_per_unit=Decimal("22.00"),
        ),
    ]


@pytest.fixture
def mock_financial_metrics_no_cost():
    """Create mock FinancialMetrics objects WITHOUT cost center data."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-001",
            asset_name="Asset Without Cost Center",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=47,
            waste_count=23,
            standard_hourly_rate=None,
            cost_per_unit=None,
        ),
    ]


@pytest.fixture
def mock_financial_metrics_partial_cost():
    """Create mock FinancialMetrics with only downtime rate (no waste cost)."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-001",
            asset_name="Asset Partial Cost",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=60,
            waste_count=10,
            standard_hourly_rate=Decimal("2000.00"),
            cost_per_unit=None,  # No waste cost configured
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
# Test: Tool Properties
# =============================================================================


class TestFinancialImpactToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, financial_impact_tool):
        """Tool name is 'financial_impact'."""
        assert financial_impact_tool.name == "financial_impact"

    def test_tool_description_for_intent_matching(self, financial_impact_tool):
        """Tool description enables correct intent matching."""
        description = financial_impact_tool.description.lower()
        assert "financial" in description
        assert "cost" in description
        assert "downtime" in description
        assert "waste" in description

    def test_tool_args_schema(self, financial_impact_tool):
        """Args schema is FinancialImpactInput."""
        assert financial_impact_tool.args_schema == FinancialImpactInput

    def test_tool_citations_required(self, financial_impact_tool):
        """Citations are required."""
        assert financial_impact_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestFinancialImpactInput:
    """Tests for FinancialImpactInput validation."""

    def test_valid_input_defaults(self):
        """Test valid input with defaults."""
        input_model = FinancialImpactInput()
        assert input_model.time_range == "yesterday"
        assert input_model.asset_id is None
        assert input_model.area is None
        assert input_model.include_breakdown is True

    def test_valid_input_with_all_params(self):
        """Test valid input with all parameters."""
        input_model = FinancialImpactInput(
            time_range="this week",
            asset_id="asset-123",
            area="Grinding",
            include_breakdown=False
        )
        assert input_model.time_range == "this week"
        assert input_model.asset_id == "asset-123"
        assert input_model.area == "Grinding"
        assert input_model.include_breakdown is False


# =============================================================================
# Test: Calculation Functions (AC#4)
# =============================================================================


class TestCalculationFunctions:
    """Tests for financial calculation functions."""

    def test_calculate_downtime_cost(self):
        """AC#4: Downtime cost calculation with formula."""
        cost, formula = calculate_downtime_cost(47, 2393.62)

        # 47 * 2393.62 / 60 = 1875.00 (rounded)
        assert cost == pytest.approx(1875.00, rel=0.01)
        assert "47 min" in formula
        assert "$2393.62/hr" in formula
        assert "/ 60" in formula
        assert "$" in formula

    def test_calculate_waste_cost(self):
        """AC#4: Waste cost calculation with formula."""
        cost, formula = calculate_waste_cost(23, 20.24)

        # 23 * 20.24 = 465.52
        assert cost == pytest.approx(465.52, rel=0.01)
        assert "23 units" in formula
        assert "$20.24/unit" in formula
        assert "$" in formula

    def test_calculate_downtime_cost_zero_minutes(self):
        """Downtime cost is zero when no downtime."""
        cost, formula = calculate_downtime_cost(0, 2000.00)
        assert cost == 0.0
        assert "0 min" in formula

    def test_calculate_waste_cost_zero_count(self):
        """Waste cost is zero when no waste."""
        cost, formula = calculate_waste_cost(0, 20.00)
        assert cost == 0.0
        assert "0 units" in formula


# =============================================================================
# Test: Asset-Level Financial Impact Query (AC#1)
# =============================================================================


class TestAssetLevelFinancialImpact:
    """Tests for asset-level financial impact queries."""

    @pytest.mark.asyncio
    async def test_asset_query_returns_success(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#1: Successful asset query returns all expected data."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            assert result.success is True
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_asset_query_returns_total_loss(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#1: Response includes total financial loss."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            assert result.data["total_loss"] is not None
            assert result.data["total_loss"] > 0
            # Expected: 1875.00 (downtime) + 465.52 (waste) = ~2340.52
            assert result.data["total_loss"] == pytest.approx(2340.52, rel=0.01)

    @pytest.mark.asyncio
    async def test_asset_query_returns_breakdown(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#1: Response includes breakdown by category."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            breakdown = result.data["breakdown"]
            assert len(breakdown) == 2

            categories = {b["category"] for b in breakdown}
            assert "downtime" in categories
            assert "waste" in categories

    @pytest.mark.asyncio
    async def test_asset_query_includes_hourly_rate(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#1: Response includes hourly rate used for calculation."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            # Find downtime breakdown
            downtime_breakdown = next(
                (b for b in result.data["breakdown"] if b["category"] == "downtime"),
                None
            )

            assert downtime_breakdown is not None
            assert "standard_hourly_rate" in downtime_breakdown["calculation_basis"]
            assert downtime_breakdown["calculation_basis"]["standard_hourly_rate"] == pytest.approx(2393.62, rel=0.01)


# =============================================================================
# Test: Area-Level Financial Impact Query (AC#2)
# =============================================================================


class TestAreaLevelFinancialImpact:
    """Tests for area-level financial impact queries."""

    @pytest.mark.asyncio
    async def test_area_query_aggregates_across_assets(
        self,
        financial_impact_tool,
        mock_financial_metrics_area,
    ):
        """AC#2: Area query aggregates across all assets in the area."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_area, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                area="Grinding"
            )

            assert result.success is True
            assert result.data["total_loss"] > 0
            assert result.data["scope"] == "the Grinding area"

    @pytest.mark.asyncio
    async def test_area_query_shows_per_asset_breakdown(
        self,
        financial_impact_tool,
        mock_financial_metrics_area,
    ):
        """AC#2: Shows per-asset breakdown for area queries."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_area, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                area="Grinding"
            )

            per_asset = result.data["per_asset_breakdown"]
            assert per_asset is not None
            assert len(per_asset) == 3  # 3 assets in mock data

            # Check that each asset has required fields
            for asset_summary in per_asset:
                assert "asset_id" in asset_summary
                assert "asset_name" in asset_summary
                assert "total_loss" in asset_summary
                assert "downtime_cost" in asset_summary
                assert "waste_cost" in asset_summary

    @pytest.mark.asyncio
    async def test_area_query_identifies_highest_cost_asset(
        self,
        financial_impact_tool,
        mock_financial_metrics_area,
    ):
        """AC#2: Identifies the highest-cost asset in area queries."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_area, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                area="Grinding"
            )

            highest = result.data["highest_cost_asset"]
            assert highest is not None
            assert "asset_id" in highest
            assert "asset_name" in highest
            assert "total_loss" in highest
            assert highest["total_loss"] > 0


# =============================================================================
# Test: Missing Cost Center Data Handling (AC#3)
# =============================================================================


class TestMissingCostCenterHandling:
    """Tests for missing cost center data handling."""

    @pytest.mark.asyncio
    async def test_missing_cost_center_returns_honest_message(
        self,
        financial_impact_tool,
        mock_financial_metrics_no_cost,
    ):
        """AC#3: Returns honest response when cost center data is missing."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_no_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-001"
            )

            assert result.success is True
            assert result.data["total_loss"] is None
            assert "Unable to calculate financial impact" in result.data["message"]
            assert "no cost center data" in result.data["message"].lower()

    @pytest.mark.asyncio
    async def test_missing_cost_center_returns_non_financial_metrics(
        self,
        financial_impact_tool,
        mock_financial_metrics_no_cost,
    ):
        """AC#3: Returns available non-financial metrics when cost data unavailable."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_no_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-001"
            )

            non_financial = result.data["non_financial_metrics"]
            assert non_financial is not None
            assert len(non_financial) > 0

            metric = non_financial[0]
            assert metric["downtime_minutes"] == 47
            assert metric["waste_count"] == 23

    @pytest.mark.asyncio
    async def test_partial_cost_data_calculates_available(
        self,
        financial_impact_tool,
        mock_financial_metrics_partial_cost,
    ):
        """AC#3: With partial cost data, calculates what's available."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results from other tests
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_partial_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-partial-001",  # Unique ID to avoid cache
                force_refresh=True,  # Force refresh to bypass cache
            )

            assert result.success is True
            # Should have total_loss (even if only from downtime)
            assert result.data["total_loss"] is not None
            assert result.data["total_loss"] > 0

            # Should have downtime cost in breakdown
            breakdown = result.data["breakdown"]
            assert len(breakdown) >= 1  # At least downtime

            downtime_breakdown = next(
                (b for b in breakdown if b["category"] == "downtime"),
                None
            )
            assert downtime_breakdown is not None
            assert downtime_breakdown["amount"] > 0

            # Waste should not be present (no cost_per_unit)
            waste_breakdown = next(
                (b for b in breakdown if b["category"] == "waste"),
                None
            )
            assert waste_breakdown is None


# =============================================================================
# Test: Transparent Calculations (AC#4)
# =============================================================================


class TestTransparentCalculations:
    """Tests for calculation formula transparency."""

    @pytest.mark.asyncio
    async def test_breakdown_includes_formula(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#4: All calculations include formulas."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            for breakdown in result.data["breakdown"]:
                assert "formula_used" in breakdown
                assert breakdown["formula_used"] is not None
                # Formula should contain dollar amounts
                assert "$" in breakdown["formula_used"]

    @pytest.mark.asyncio
    async def test_breakdown_includes_calculation_basis(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#4: Breakdown includes calculation basis values."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            for breakdown in result.data["breakdown"]:
                assert "calculation_basis" in breakdown
                assert breakdown["calculation_basis"] is not None
                # Should have relevant values
                if breakdown["category"] == "downtime":
                    assert "downtime_minutes" in breakdown["calculation_basis"]
                    assert "standard_hourly_rate" in breakdown["calculation_basis"]
                elif breakdown["category"] == "waste":
                    assert "waste_count" in breakdown["calculation_basis"]
                    assert "cost_per_unit" in breakdown["calculation_basis"]


# =============================================================================
# Test: Citation Compliance (AC#5)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation and compliance."""

    @pytest.mark.asyncio
    async def test_response_includes_citations(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#5: All responses include citations."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            assert len(result.citations) >= 1

    @pytest.mark.asyncio
    async def test_citation_includes_source_table(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#5: Citations include source table."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            # Should have citation from daily_summaries
            ds_citation = next(
                (c for c in result.citations if c.table == "daily_summaries"),
                None
            )
            assert ds_citation is not None

    @pytest.mark.asyncio
    async def test_citation_includes_calculation_evidence(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#5: Citations reference calculation basis."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            # Should have citation for calculation
            calc_citation = next(
                (c for c in result.citations if c.source == "calculation"),
                None
            )
            assert calc_citation is not None
            assert calc_citation.table == "cost_centers"

    @pytest.mark.asyncio
    async def test_citation_includes_timestamp(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#5: Citations include timestamp."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            for citation in result.citations:
                assert citation.timestamp is not None

    @pytest.mark.asyncio
    async def test_response_includes_data_freshness(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#5: Response includes data freshness indicator."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            assert "data_freshness" in result.data
            assert result.data["data_freshness"] is not None


# =============================================================================
# Test: Caching Support (AC#6)
# =============================================================================


class TestCachingSupport:
    """Tests for cache metadata."""

    @pytest.mark.asyncio
    async def test_cache_tier_is_daily(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#6: Cache tier is 'daily' for financial data."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            assert result.metadata["cache_tier"] == "daily"

    @pytest.mark.asyncio
    async def test_ttl_is_15_minutes(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#6: TTL is 15 minutes (900 seconds)."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            assert result.metadata["ttl_seconds"] == CACHE_TTL_DAILY
            assert result.metadata["ttl_seconds"] == 900


# =============================================================================
# Test: Time Range Parsing
# =============================================================================


class TestTimeRangeParsing:
    """Tests for time range parsing."""

    def test_parse_yesterday_default(self, financial_impact_tool):
        """Default time range is 'yesterday' for T-1 data."""
        result = financial_impact_tool._parse_time_range("yesterday")
        yesterday = date.today() - timedelta(days=1)
        assert result.start == yesterday
        assert result.end == yesterday
        assert result.description == "yesterday"

    def test_parse_today(self, financial_impact_tool):
        """Parse 'today' time range."""
        result = financial_impact_tool._parse_time_range("today")
        today = date.today()
        assert result.start == today
        assert result.end == today
        assert result.description == "today"

    def test_parse_this_week(self, financial_impact_tool):
        """Parse 'this week' time range."""
        result = financial_impact_tool._parse_time_range("this week")
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        assert result.start == monday
        assert result.end == today
        assert result.description == "this week"

    def test_parse_last_n_days(self, financial_impact_tool):
        """Parse 'last 7 days' time range."""
        result = financial_impact_tool._parse_time_range("last 7 days")
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        assert result.start == seven_days_ago
        assert result.end == today
        assert result.description == "last 7 days"

    def test_parse_date_range(self, financial_impact_tool):
        """Parse explicit date range."""
        result = financial_impact_tool._parse_time_range("2026-01-01 to 2026-01-09")
        assert result.start == date(2026, 1, 1)
        assert result.end == date(2026, 1, 9)

    def test_parse_unknown_defaults_to_yesterday(self, financial_impact_tool):
        """Unknown time range defaults to yesterday."""
        result = financial_impact_tool._parse_time_range("unknown value")
        yesterday = date.today() - timedelta(days=1)
        assert result.start == yesterday
        assert result.end == yesterday


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_data_source_error_returns_friendly_message(
        self, financial_impact_tool
    ):
        """Returns user-friendly error message for data source errors."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results from other tests
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="daily_summaries",
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-error-test-1",  # Unique asset ID to avoid cache hits
                force_refresh=True,  # Force refresh to bypass cache
            )

            assert result.success is False
            assert result.error_message is not None
            assert "Unable to retrieve" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(self, financial_impact_tool):
        """Unexpected errors are caught and logged."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results from other tests
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.side_effect = RuntimeError("Unexpected failure")

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-error-test-2",  # Unique asset ID to avoid cache hits
                force_refresh=True,  # Force refresh to bypass cache
            )

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
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """Follow-up questions are generated in metadata."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3


# =============================================================================
# Test: Tool Registration (Integration)
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = FinancialImpactTool()
        assert tool is not None
        assert tool.name == "financial_impact"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = FinancialImpactTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)


# =============================================================================
# Test: Average Comparison (AC#1)
# =============================================================================


class TestAverageComparison:
    """Tests for average loss comparison calculation."""

    @pytest.mark.asyncio
    async def test_average_comparison_included(
        self,
        financial_impact_tool,
        mock_financial_metrics_with_cost,
    ):
        """AC#1: Response includes comparison to average loss."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Return same data for both current and historical queries
            mock_ds.get_financial_metrics.return_value = create_data_result(
                mock_financial_metrics_with_cost, "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-grd-005"
            )

            # Average comparison may be None if not enough historical data
            # but the field should exist
            assert "average_comparison" in result.data


# =============================================================================
# Test: No Data Response
# =============================================================================


class TestNoDataResponse:
    """Tests for no data handling."""

    @pytest.mark.asyncio
    async def test_no_data_returns_zero_loss(
        self, financial_impact_tool
    ):
        """Returns zero loss when no data found."""
        with patch(
            "app.services.agent.tools.financial_impact.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_financial_metrics.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await financial_impact_tool._arun(
                time_range="yesterday",
                asset_id="asset-nonexistent"
            )

            assert result.success is True
            assert result.data["total_loss"] == 0.0
            assert "No data found" in result.data["message"]
