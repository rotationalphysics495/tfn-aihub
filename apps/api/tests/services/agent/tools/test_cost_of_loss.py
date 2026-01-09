"""
Tests for Cost of Loss Tool (Story 6.3)

Comprehensive test coverage for all acceptance criteria:
AC#1: Basic Cost of Loss Query - Ranked list with category, amount, root cause, percentage
AC#2: Top N Cost Drivers Query - Limit to top N items with trend comparison
AC#3: Area-Filtered Query - Filter by area and compare to plant-wide average
AC#4: Category Grouping - Group by downtime, waste, quality with subtotals
AC#5: Citation Compliance - All responses include citations with source tables
AC#6: Performance Requirements - <2s response time, 15-minute cache TTL
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List
from unittest.mock import AsyncMock, patch

from app.models.agent import (
    AreaComparison,
    CategorySummary,
    CostOfLossInput,
    CostOfLossOutput,
    LossItem,
    TrendComparison,
)
from app.services.agent.base import Citation, ToolResult
from app.services.agent.data_source.protocol import DataResult, FinancialMetrics
from app.services.agent.tools.cost_of_loss import (
    CostOfLossTool,
    CACHE_TTL_DAILY,
    calculate_downtime_cost,
    calculate_waste_cost,
    determine_trend_direction,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def cost_of_loss_tool():
    """Create an instance of CostOfLossTool."""
    return CostOfLossTool()


@pytest.fixture
def mock_metrics_with_downtime_reasons():
    """Create mock FinancialMetrics with downtime_reasons JSONB."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-grd-005",
            asset_name="Grinder 5",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=78,
            waste_count=23,
            downtime_reasons={
                "Material Jam": 32,
                "Safety Stop": 8,
                "Blade Change": 15,
                "Maintenance": 23,
            },
            standard_hourly_rate=Decimal("2400.00"),
            cost_per_unit=Decimal("20.00"),
        ),
        FinancialMetrics(
            id="rec-002",
            asset_id="asset-pkg-002",
            asset_name="Packaging Line 2",
            area="Packaging",
            report_date=yesterday,
            downtime_minutes=45,
            waste_count=15,
            downtime_reasons={
                "Safety Stop": 25,
                "Material Jam": 20,
            },
            standard_hourly_rate=Decimal("2000.00"),
            cost_per_unit=Decimal("15.00"),
        ),
    ]


@pytest.fixture
def mock_metrics_multiple_areas():
    """Create mock FinancialMetrics for multiple areas."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-grd-005",
            asset_name="Grinder 5",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=60,
            waste_count=20,
            downtime_reasons={"Material Jam": 60},
            standard_hourly_rate=Decimal("2400.00"),
            cost_per_unit=Decimal("20.00"),
        ),
        FinancialMetrics(
            id="rec-002",
            asset_id="asset-grd-006",
            asset_name="Grinder 6",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=30,
            waste_count=10,
            downtime_reasons={"Blade Change": 30},
            standard_hourly_rate=Decimal("2400.00"),
            cost_per_unit=Decimal("20.00"),
        ),
        FinancialMetrics(
            id="rec-003",
            asset_id="asset-pkg-001",
            asset_name="Packaging Line 1",
            area="Packaging",
            report_date=yesterday,
            downtime_minutes=20,
            waste_count=5,
            downtime_reasons={"Safety Stop": 20},
            standard_hourly_rate=Decimal("2000.00"),
            cost_per_unit=Decimal("15.00"),
        ),
    ]


@pytest.fixture
def mock_metrics_no_cost_data():
    """Create mock FinancialMetrics WITHOUT cost center data."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-001",
            asset_name="Asset Without Cost Center",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=60,
            waste_count=20,
            downtime_reasons=None,
            standard_hourly_rate=None,
            cost_per_unit=None,
        ),
    ]


@pytest.fixture
def mock_metrics_no_downtime_reasons():
    """Create mock FinancialMetrics without downtime_reasons breakdown."""
    yesterday = date.today() - timedelta(days=1)
    return [
        FinancialMetrics(
            id="rec-001",
            asset_id="asset-grd-005",
            asset_name="Grinder 5",
            area="Grinding",
            report_date=yesterday,
            downtime_minutes=60,
            waste_count=20,
            downtime_reasons=None,  # No breakdown available
            standard_hourly_rate=Decimal("2400.00"),
            cost_per_unit=Decimal("20.00"),
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


class TestCostOfLossToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, cost_of_loss_tool):
        """Tool name is 'cost_of_loss'."""
        assert cost_of_loss_tool.name == "cost_of_loss"

    def test_tool_description_for_intent_matching(self, cost_of_loss_tool):
        """Tool description enables correct intent matching."""
        description = cost_of_loss_tool.description.lower()
        assert "cost" in description
        assert "loss" in description
        assert "rank" in description
        assert "driver" in description

    def test_tool_args_schema(self, cost_of_loss_tool):
        """Args schema is CostOfLossInput."""
        assert cost_of_loss_tool.args_schema == CostOfLossInput

    def test_tool_citations_required(self, cost_of_loss_tool):
        """Citations are required."""
        assert cost_of_loss_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestCostOfLossInput:
    """Tests for CostOfLossInput validation."""

    def test_valid_input_defaults(self):
        """Test valid input with defaults."""
        input_model = CostOfLossInput()
        assert input_model.time_range == "yesterday"
        assert input_model.area is None
        assert input_model.limit == 10
        assert input_model.include_trends is False

    def test_valid_input_with_all_params(self):
        """Test valid input with all parameters."""
        input_model = CostOfLossInput(
            time_range="this week",
            area="Grinding",
            limit=3,
            include_trends=True
        )
        assert input_model.time_range == "this week"
        assert input_model.area == "Grinding"
        assert input_model.limit == 3
        assert input_model.include_trends is True

    def test_limit_validation(self):
        """Test limit parameter validation."""
        # Valid limits
        input_model = CostOfLossInput(limit=1)
        assert input_model.limit == 1

        input_model = CostOfLossInput(limit=100)
        assert input_model.limit == 100


# =============================================================================
# Test: Trend Direction Logic
# =============================================================================


class TestTrendDirectionLogic:
    """Tests for trend direction calculation."""

    def test_trend_up_when_increase_above_threshold(self):
        """Trend is 'up' when current > previous by more than 5%."""
        result = determine_trend_direction(1100.0, 1000.0)
        assert result == "up"

    def test_trend_down_when_decrease_above_threshold(self):
        """Trend is 'down' when current < previous by more than 5%."""
        result = determine_trend_direction(900.0, 1000.0)
        assert result == "down"

    def test_trend_stable_within_threshold(self):
        """Trend is 'stable' when change within 5% threshold."""
        result = determine_trend_direction(1040.0, 1000.0)  # 4% increase
        assert result == "stable"

        result = determine_trend_direction(960.0, 1000.0)  # 4% decrease
        assert result == "stable"

    def test_trend_up_from_zero_previous(self):
        """Trend is 'up' when previous was zero and current > 0."""
        result = determine_trend_direction(100.0, 0.0)
        assert result == "up"

    def test_trend_stable_when_both_zero(self):
        """Trend is 'stable' when both are zero."""
        result = determine_trend_direction(0.0, 0.0)
        assert result == "stable"


# =============================================================================
# Test: Calculation Functions
# =============================================================================


class TestCalculationFunctions:
    """Tests for cost calculation functions."""

    def test_calculate_downtime_cost(self):
        """Downtime cost calculation with formula."""
        cost, formula = calculate_downtime_cost(60, 2400.00)

        # 60 * 2400 / 60 = 2400.00
        assert cost == pytest.approx(2400.00, rel=0.01)
        assert "60 min" in formula
        assert "$2400.00/hr" in formula

    def test_calculate_waste_cost(self):
        """Waste cost calculation with formula."""
        cost, formula = calculate_waste_cost(20, 20.00)

        # 20 * 20 = 400.00
        assert cost == pytest.approx(400.00, rel=0.01)
        assert "20 units" in formula
        assert "$20.00/unit" in formula


# =============================================================================
# Test: Basic Cost of Loss Query (AC#1)
# =============================================================================


class TestBasicCostOfLossQuery:
    """Tests for basic cost of loss query functionality."""

    @pytest.mark.asyncio
    async def test_returns_success(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#1: Successful query returns success."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            assert result.success is True
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_returns_ranked_list(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#1: Response includes ranked list (highest first)."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            ranked_items = result.data["ranked_items"]
            assert len(ranked_items) > 0

            # Verify sorted by amount descending
            amounts = [item["amount"] for item in ranked_items]
            assert amounts == sorted(amounts, reverse=True)

    @pytest.mark.asyncio
    async def test_each_item_has_required_fields(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#1: Each loss item has asset, category, amount, root cause."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            for item in result.data["ranked_items"]:
                assert "asset_id" in item
                assert "asset_name" in item
                assert "category" in item
                assert "amount" in item
                assert "root_cause" in item  # May be None
                assert "percentage_of_total" in item

    @pytest.mark.asyncio
    async def test_includes_total_loss(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#1: Response includes total loss across all items."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            assert "total_loss" in result.data
            assert result.data["total_loss"] > 0


# =============================================================================
# Test: Percentage Calculations (AC#1)
# =============================================================================


class TestPercentageCalculations:
    """Tests for percentage of total calculation."""

    @pytest.mark.asyncio
    async def test_percentages_calculated(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#1: Each item has percentage of total."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            for item in result.data["ranked_items"]:
                assert item["percentage_of_total"] >= 0
                assert item["percentage_of_total"] <= 100


# =============================================================================
# Test: Top N Cost Drivers Query (AC#2)
# =============================================================================


class TestTopNCostDriversQuery:
    """Tests for top N cost drivers functionality."""

    @pytest.mark.asyncio
    async def test_limit_parameter_applied(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#2: Response limits to top N items."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday",
                limit=3
            )

            assert len(result.data["ranked_items"]) <= 3

    @pytest.mark.asyncio
    async def test_trend_comparison_included_when_requested(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#2: Includes trend vs previous period when include_trends=True."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Return same data for both current and previous period queries
            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday",
                include_trends=True
            )

            # Trend comparison should be present (may be None if not enough data)
            assert "trend_comparison" in result.data
            # If we have data, it should have required fields
            if result.data["trend_comparison"] is not None:
                trend = result.data["trend_comparison"]
                assert "previous_period_total" in trend
                assert "current_period_total" in trend
                assert "change_amount" in trend
                assert "change_percent" in trend
                assert "trend_direction" in trend
                assert trend["trend_direction"] in ["up", "down", "stable"]


# =============================================================================
# Test: Area-Filtered Query (AC#3)
# =============================================================================


class TestAreaFilteredQuery:
    """Tests for area-filtered cost of loss queries."""

    @pytest.mark.asyncio
    async def test_area_filter_applied(
        self,
        cost_of_loss_tool,
        mock_metrics_multiple_areas,
    ):
        """AC#3: Response filters to specified area."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Filter mock data to Grinding area only
            grinding_metrics = [
                m for m in mock_metrics_multiple_areas if m.area == "Grinding"
            ]

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                grinding_metrics, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday",
                area="Grinding"
            )

            assert result.success is True
            assert "Grinding" in result.data["scope"]

    @pytest.mark.asyncio
    async def test_area_comparison_included(
        self,
        cost_of_loss_tool,
        mock_metrics_multiple_areas,
    ):
        """AC#3: Compares area loss to plant-wide average."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # For area query, return Grinding metrics
            # For plant-wide query, return all metrics
            def mock_get_cost_of_loss(start_date, end_date, area=None):
                if area:
                    data = [m for m in mock_metrics_multiple_areas if m.area == area]
                else:
                    data = mock_metrics_multiple_areas
                return create_data_result(data, "daily_summaries")

            mock_ds.get_cost_of_loss.side_effect = mock_get_cost_of_loss

            result = await cost_of_loss_tool._arun(
                time_range="yesterday",
                area="Grinding"
            )

            # Area comparison should be present
            assert "area_comparison" in result.data
            if result.data["area_comparison"] is not None:
                comparison = result.data["area_comparison"]
                assert "area_loss" in comparison
                assert "plant_wide_average" in comparison
                assert "variance" in comparison
                assert "variance_percent" in comparison
                assert "comparison_text" in comparison


# =============================================================================
# Test: Category Grouping (AC#4)
# =============================================================================


class TestCategoryGrouping:
    """Tests for category grouping functionality."""

    @pytest.mark.asyncio
    async def test_losses_grouped_by_category(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#4: Losses are grouped by category."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            category_summaries = result.data["category_summaries"]
            assert len(category_summaries) > 0

            categories = [s["category"] for s in category_summaries]
            # Should have downtime and waste based on mock data
            assert "downtime" in categories
            assert "waste" in categories

    @pytest.mark.asyncio
    async def test_category_subtotals_calculated(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#4: Each category shows subtotal and percentage."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            for summary in result.data["category_summaries"]:
                assert "total_amount" in summary
                assert "item_count" in summary
                assert "percentage_of_total" in summary
                assert summary["total_amount"] >= 0
                assert summary["percentage_of_total"] >= 0
                assert summary["percentage_of_total"] <= 100

    @pytest.mark.asyncio
    async def test_category_totals_sum_to_total_loss(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#4: Category subtotals should sum to total loss."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            category_sum = sum(
                s["total_amount"] for s in result.data["category_summaries"]
            )
            total_loss = result.data["total_loss"]

            assert category_sum == pytest.approx(total_loss, rel=0.01)

    @pytest.mark.asyncio
    async def test_top_contributors_included(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#4: Top contributors per category are included."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            for summary in result.data["category_summaries"]:
                assert "top_contributors" in summary


# =============================================================================
# Test: Root Cause Extraction (AC#4)
# =============================================================================


class TestRootCauseExtraction:
    """Tests for root cause extraction from downtime_reasons."""

    @pytest.mark.asyncio
    async def test_root_causes_extracted(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#4: Root causes extracted from downtime_reasons JSONB."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            # Find downtime items
            downtime_items = [
                item for item in result.data["ranked_items"]
                if item["category"] == "downtime"
            ]

            # Should have root causes
            items_with_root_cause = [
                item for item in downtime_items if item["root_cause"] is not None
            ]
            assert len(items_with_root_cause) > 0

            # Check for expected root causes from mock data
            root_causes = [item["root_cause"] for item in items_with_root_cause]
            assert "Material Jam" in root_causes or "Safety Stop" in root_causes

    @pytest.mark.asyncio
    async def test_downtime_without_reasons_handled(
        self,
        cost_of_loss_tool,
        mock_metrics_no_downtime_reasons,
    ):
        """Downtime without breakdown still produces loss items."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_no_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="last 30 days",  # Unique time range to avoid cache
                force_refresh=True,
            )

            # Should still have downtime loss item
            downtime_items = [
                item for item in result.data["ranked_items"]
                if item["category"] == "downtime"
            ]
            assert len(downtime_items) > 0

            # Root cause should be None when no breakdown
            assert downtime_items[0]["root_cause"] is None


# =============================================================================
# Test: Citation Compliance (AC#5)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation and compliance."""

    @pytest.mark.asyncio
    async def test_response_includes_citations(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#5: All responses include citations."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            assert len(result.citations) >= 1

    @pytest.mark.asyncio
    async def test_citation_includes_source_table(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#5: Citations include source table."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
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
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#5: Citations reference calculation basis."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            # Should have citation for calculation
            calc_citation = next(
                (c for c in result.citations if c.source == "calculation"),
                None
            )
            assert calc_citation is not None
            assert calc_citation.table == "cost_centers"

    @pytest.mark.asyncio
    async def test_response_includes_data_freshness(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#5: Response includes data freshness indicator."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
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
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#6: Cache tier is 'daily' for cost of loss data."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            assert result.metadata["cache_tier"] == "daily"

    @pytest.mark.asyncio
    async def test_ttl_is_15_minutes(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """AC#6: TTL is 15 minutes (900 seconds)."""
        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday"
            )

            assert result.metadata["ttl_seconds"] == CACHE_TTL_DAILY
            assert result.metadata["ttl_seconds"] == 900


# =============================================================================
# Test: Time Range Parsing
# =============================================================================


class TestTimeRangeParsing:
    """Tests for time range parsing."""

    def test_parse_yesterday_default(self, cost_of_loss_tool):
        """Default time range is 'yesterday' for T-1 data."""
        result = cost_of_loss_tool._parse_time_range("yesterday")
        yesterday = date.today() - timedelta(days=1)
        assert result.start == yesterday
        assert result.end == yesterday
        assert result.description == "yesterday"

    def test_parse_today(self, cost_of_loss_tool):
        """Parse 'today' time range."""
        result = cost_of_loss_tool._parse_time_range("today")
        today = date.today()
        assert result.start == today
        assert result.end == today
        assert result.description == "today"

    def test_parse_this_week(self, cost_of_loss_tool):
        """Parse 'this week' time range."""
        result = cost_of_loss_tool._parse_time_range("this week")
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        assert result.start == monday
        assert result.end == today
        assert result.description == "this week"

    def test_parse_last_n_days(self, cost_of_loss_tool):
        """Parse 'last 7 days' time range."""
        result = cost_of_loss_tool._parse_time_range("last 7 days")
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        assert result.start == seven_days_ago
        assert result.end == today
        assert result.description == "last 7 days"

    def test_parse_date_range(self, cost_of_loss_tool):
        """Parse explicit date range."""
        result = cost_of_loss_tool._parse_time_range("2026-01-01 to 2026-01-09")
        assert result.start == date(2026, 1, 1)
        assert result.end == date(2026, 1, 9)

    def test_parse_unknown_defaults_to_yesterday(self, cost_of_loss_tool):
        """Unknown time range defaults to yesterday."""
        result = cost_of_loss_tool._parse_time_range("unknown value")
        yesterday = date.today() - timedelta(days=1)
        assert result.start == yesterday
        assert result.end == yesterday


# =============================================================================
# Test: Missing Cost Center Data Handling
# =============================================================================


class TestMissingCostCenterHandling:
    """Tests for missing cost center data handling."""

    @pytest.mark.asyncio
    async def test_missing_cost_center_returns_message(
        self,
        cost_of_loss_tool,
        mock_metrics_no_cost_data,
    ):
        """Returns message when cost center data is missing."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_no_cost_data, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="last 45 days",  # Unique time range to avoid cache
                force_refresh=True,
            )

            assert result.success is True
            assert result.data["total_loss"] == 0.0
            assert "Unable to calculate cost of loss" in result.data["message"]
            assert "no cost center data" in result.data["message"].lower()


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_data_source_error_returns_friendly_message(
        self, cost_of_loss_tool
    ):
        """Returns user-friendly error message for data source errors."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results from other tests
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="daily_summaries",
            )

            result = await cost_of_loss_tool._arun(
                time_range="yesterday",
                force_refresh=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "Unable to retrieve" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(self, cost_of_loss_tool):
        """Unexpected errors are caught and logged."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results from other tests
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.side_effect = RuntimeError("Unexpected failure")

            result = await cost_of_loss_tool._arun(
                time_range="yesterday",
                force_refresh=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "unexpected error" in result.error_message.lower()


# =============================================================================
# Test: No Data Response
# =============================================================================


class TestNoDataResponse:
    """Tests for no data handling."""

    @pytest.mark.asyncio
    async def test_no_data_returns_zero_loss(self, cost_of_loss_tool):
        """Returns zero loss when no data found."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                [], "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="last 60 days",  # Unique time range to avoid cache
                force_refresh=True,
            )

            assert result.success is True
            assert result.data["total_loss"] == 0.0
            assert "No data found" in result.data["message"]


# =============================================================================
# Test: Follow-up Question Generation
# =============================================================================


class TestFollowUpQuestions:
    """Tests for follow-up question generation."""

    @pytest.mark.asyncio
    async def test_follow_up_questions_generated(
        self,
        cost_of_loss_tool,
        mock_metrics_with_downtime_reasons,
    ):
        """Follow-up questions are generated in metadata."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to avoid cached results
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.cost_of_loss.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_cost_of_loss.return_value = create_data_result(
                mock_metrics_with_downtime_reasons, "daily_summaries"
            )

            result = await cost_of_loss_tool._arun(
                time_range="last 90 days",  # Unique time range to avoid cache
                force_refresh=True,
            )

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3


# =============================================================================
# Test: Tool Registration
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = CostOfLossTool()
        assert tool is not None
        assert tool.name == "cost_of_loss"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = CostOfLossTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)
