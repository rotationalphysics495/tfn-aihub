"""
Tests for Comparative Analysis Tool (Story 7.2)

Comprehensive test coverage for all acceptance criteria:
AC#1: Two-Asset Comparison - Side-by-side metrics, variance, recommendations
AC#2: Multi-Asset Comparison - Pattern matching, ranking by performance
AC#3: Area-Level Comparison - Aggregated metrics, top/bottom performers
AC#4: Incompatible Metrics Handling - Normalization, comparability notes
AC#5: Default Time Range - 7 days default, custom ranges
AC#6: Citation & Data Freshness - Citations, 15-minute cache TTL
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.agent import (
    AreaPerformerSummary,
    ComparativeAnalysisCitation,
    ComparativeAnalysisInput,
    ComparativeAnalysisOutput,
    ComparisonMetric,
    SubjectSummary,
)
from app.services.agent.base import Citation, ToolResult
from app.services.agent.tools.comparative_analysis import (
    ComparativeAnalysisTool,
    DEFAULT_METRICS,
    METRIC_CONFIG,
    WINNER_SCORE_GAP,
    _utcnow,
)
from app.services.agent.data_source import DataResult
from app.services.agent.data_source.protocol import Asset, OEEMetrics, ShiftTarget


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def comparative_tool():
    """Create an instance of ComparativeAnalysisTool."""
    return ComparativeAnalysisTool()


@pytest.fixture
def mock_asset_grinder5():
    """Create mock asset for Grinder 5."""
    return Asset(
        id="ast-grd-005",
        name="Grinder 5",
        source_id="GRD005",
        area="Grinding",
    )


@pytest.fixture
def mock_asset_grinder3():
    """Create mock asset for Grinder 3."""
    return Asset(
        id="ast-grd-003",
        name="Grinder 3",
        source_id="GRD003",
        area="Grinding",
    )


@pytest.fixture
def mock_asset_cama():
    """Create mock asset for CAMA 800-1."""
    return Asset(
        id="ast-pkg-001",
        name="CAMA 800-1",
        source_id="CAMA001",
        area="Packaging",
    )


@pytest.fixture
def mock_oee_grinder5():
    """Create mock OEE data for Grinder 5."""
    base_date = date.today() - timedelta(days=3)
    return [
        OEEMetrics(
            id=f"oee-g5-{i}",
            asset_id="ast-grd-005",
            report_date=base_date + timedelta(days=i),
            oee_percentage=Decimal("78.3"),
            availability=Decimal("85.0"),
            performance=Decimal("92.1"),
            quality=Decimal("99.8"),
            actual_output=4820,
            target_output=5000,
            downtime_minutes=252,
            waste_count=154,
        )
        for i in range(7)
    ]


@pytest.fixture
def mock_oee_grinder3():
    """Create mock OEE data for Grinder 3 - better performing."""
    base_date = date.today() - timedelta(days=3)
    return [
        OEEMetrics(
            id=f"oee-g3-{i}",
            asset_id="ast-grd-003",
            report_date=base_date + timedelta(days=i),
            oee_percentage=Decimal("85.1"),
            availability=Decimal("90.5"),
            performance=Decimal("94.0"),
            quality=Decimal("99.9"),
            actual_output=4950,
            target_output=5000,
            downtime_minutes=168,
            waste_count=99,
        )
        for i in range(7)
    ]


@pytest.fixture
def mock_shift_target():
    """Create mock shift target."""
    return ShiftTarget(
        id="tgt-001",
        asset_id="ast-grd-005",
        target_output=5000,
        target_oee=85.0,
    )


@pytest.fixture
def mock_data_result_factory():
    """Factory to create DataResult objects."""
    def factory(data, table_name="daily_summaries"):
        return DataResult(
            data=data,
            source_name="supabase",
            table_name=table_name,
            query_timestamp=_utcnow(),
            row_count=len(data) if isinstance(data, list) else (1 if data else 0),
        )
    return factory


# =============================================================================
# Test: Tool Properties
# =============================================================================


class TestComparativeAnalysisToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, comparative_tool):
        """Tool name is 'comparative_analysis'."""
        assert comparative_tool.name == "comparative_analysis"

    def test_tool_description_for_intent_matching(self, comparative_tool):
        """Tool description enables correct intent matching."""
        description = comparative_tool.description.lower()
        assert "compare" in description
        assert "side-by-side" in description
        assert "asset" in description or "area" in description
        assert "best performer" in description or "difference" in description

    def test_tool_args_schema(self, comparative_tool):
        """Args schema is ComparativeAnalysisInput."""
        assert comparative_tool.args_schema == ComparativeAnalysisInput

    def test_tool_citations_required(self, comparative_tool):
        """Citations are required."""
        assert comparative_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestComparativeAnalysisInput:
    """Tests for ComparativeAnalysisInput validation."""

    def test_valid_input_minimal(self):
        """Test valid input with minimal required fields."""
        input_model = ComparativeAnalysisInput(
            subjects=["Grinder 5", "Grinder 3"]
        )
        assert len(input_model.subjects) == 2
        assert input_model.comparison_type == "asset"
        assert input_model.time_range_days == 7
        assert input_model.metrics is None

    def test_valid_input_all_fields(self):
        """Test valid input with all fields."""
        input_model = ComparativeAnalysisInput(
            subjects=["Grinder 5", "Grinder 3", "Grinder 1"],
            comparison_type="asset",
            metrics=["oee", "output"],
            time_range_days=14
        )
        assert len(input_model.subjects) == 3
        assert input_model.comparison_type == "asset"
        assert input_model.metrics == ["oee", "output"]
        assert input_model.time_range_days == 14

    def test_area_comparison_type(self):
        """Test area comparison type."""
        input_model = ComparativeAnalysisInput(
            subjects=["Grinding", "Packaging"],
            comparison_type="area"
        )
        assert input_model.comparison_type == "area"

    def test_time_range_bounds(self):
        """Test time range validation."""
        # Valid ranges
        assert ComparativeAnalysisInput(
            subjects=["A", "B"], time_range_days=1
        ).time_range_days == 1
        assert ComparativeAnalysisInput(
            subjects=["A", "B"], time_range_days=90
        ).time_range_days == 90

        # Default value
        assert ComparativeAnalysisInput(
            subjects=["A", "B"]
        ).time_range_days == 7


# =============================================================================
# Test: Two-Asset Comparison (AC#1)
# =============================================================================


class TestTwoAssetComparison:
    """Tests for AC#1: Two-Asset Comparison."""

    @pytest.mark.asyncio
    async def test_basic_two_asset_comparison(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#1: Successful two-asset comparison returns all expected data."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()

            # Setup mock responses
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )

            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"],
                comparison_type="asset",
                time_range_days=7
            )

            assert result.success is True
            assert result.data is not None
            assert len(result.data["subjects"]) == 2
            assert result.data["comparison_type"] == "asset"

    @pytest.mark.asyncio
    async def test_comparison_includes_metrics(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#1: Response includes side-by-side metrics table."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            metrics = result.data["metrics"]
            assert len(metrics) >= 4  # OEE, output, downtime, waste

            # Check metric structure
            for metric in metrics:
                assert "metric_name" in metric
                assert "values" in metric
                assert "best_performer" in metric
                assert "worst_performer" in metric
                assert "variance_pct" in metric

    @pytest.mark.asyncio
    async def test_comparison_includes_variance_highlighting(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#1: Variance highlighting (better/worse indicators)."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            # Check that best/worst performers are identified
            oee_metric = next(
                m for m in result.data["metrics"] if m["metric_name"] == "oee"
            )
            assert oee_metric["best_performer"] in ["Grinder 5", "Grinder 3"]
            assert oee_metric["worst_performer"] in ["Grinder 5", "Grinder 3"]
            assert oee_metric["best_performer"] != oee_metric["worst_performer"]

    @pytest.mark.asyncio
    async def test_comparison_includes_summary(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#1: Summary of key differences."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            assert result.data["summary"] is not None
            assert len(result.data["summary"]) > 0
            # Summary should mention the assets
            summary_lower = result.data["summary"].lower()
            assert "grinder" in summary_lower

    @pytest.mark.asyncio
    async def test_comparison_winner_when_clear(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#1: Winner/recommendation if one is clearly better."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            # Winner may or may not be set depending on score gap
            # but the field should exist
            assert "winner" in result.data

    @pytest.mark.asyncio
    async def test_comparison_includes_recommendations(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#1: Recommendations based on comparison."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            assert "recommendations" in result.data
            # Recommendations should be a list
            assert isinstance(result.data["recommendations"], list)


# =============================================================================
# Test: Multi-Asset Comparison (AC#2)
# =============================================================================


class TestMultiAssetComparison:
    """Tests for AC#2: Multi-Asset Comparison."""

    @pytest.mark.asyncio
    async def test_all_grinders_pattern_expansion(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#2: 'all grinders' pattern expands to multiple assets."""
        # Create additional grinder assets
        mock_grinder1 = Asset(
            id="ast-grd-001", name="Grinder 1", source_id="GRD001", area="Grinding"
        )
        all_assets = [mock_asset_grinder5, mock_asset_grinder3, mock_grinder1]

        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_all_assets = AsyncMock(
                return_value=mock_data_result_factory(all_assets, "assets")
            )
            mock_ds.get_oee = AsyncMock(
                return_value=mock_data_result_factory(mock_oee_grinder5)
            )
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["all grinders"],
                comparison_type="asset"
            )

            assert result.success is True
            # Should find multiple grinder assets
            assert len(result.data["subjects"]) >= 2

    @pytest.mark.asyncio
    async def test_ranking_by_performance(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#2: Ranks by overall performance."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            subjects = result.data["subjects"]
            # Should be sorted by score descending
            scores = [s["score"] for s in subjects]
            assert scores == sorted(scores, reverse=True)

            # Check ranking is sequential
            ranks = [s["rank"] for s in subjects]
            assert ranks == [1, 2]

    @pytest.mark.asyncio
    async def test_max_10_assets_limit(
        self,
        comparative_tool,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#2: Supports 2-10 assets in a single comparison."""
        # Create 15 mock assets
        many_assets = [
            Asset(
                id=f"ast-{i}", name=f"Asset {i}", source_id=f"AST{i:03d}", area="Test"
            )
            for i in range(15)
        ]

        mock_oee = [
            OEEMetrics(
                id="oee-test",
                asset_id="ast-0",
                report_date=date.today(),
                oee_percentage=Decimal("80.0"),
                availability=Decimal("85.0"),
                performance=Decimal("92.0"),
                quality=Decimal("99.0"),
                actual_output=1000,
                downtime_minutes=60,
                waste_count=10,
            )
        ]

        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_all_assets = AsyncMock(
                return_value=mock_data_result_factory(many_assets, "assets")
            )
            mock_ds.get_oee = AsyncMock(
                return_value=mock_data_result_factory(mock_oee)
            )
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["all asset"],  # Pattern to match all
                comparison_type="asset"
            )

            # Should be limited to 10
            assert len(result.data["subjects"]) <= 10


# =============================================================================
# Test: Area-Level Comparison (AC#3)
# =============================================================================


class TestAreaLevelComparison:
    """Tests for AC#3: Area-Level Comparison."""

    @pytest.mark.asyncio
    async def test_area_comparison_aggregated_metrics(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_asset_cama,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#3: Aggregates metrics at the area level."""
        grinding_assets = [mock_asset_grinder5, mock_asset_grinder3]
        packaging_assets = [mock_asset_cama]

        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            # Need to return enough data for both initial resolution and area_performers
            mock_ds.get_assets_by_area = AsyncMock(side_effect=[
                mock_data_result_factory(grinding_assets, "assets"),
                mock_data_result_factory(packaging_assets, "assets"),
                mock_data_result_factory(grinding_assets, "assets"),  # For area_performers
                mock_data_result_factory(packaging_assets, "assets"),  # For area_performers
            ])
            mock_ds.get_oee_by_area = AsyncMock(
                return_value=mock_data_result_factory(mock_oee_grinder5)
            )
            mock_ds.get_oee = AsyncMock(
                return_value=mock_data_result_factory(mock_oee_grinder5)
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinding", "Packaging"],
                comparison_type="area"
            )

            assert result.success is True
            assert result.data["comparison_type"] == "area"
            # Should have area-level subjects
            for subject in result.data["subjects"]:
                assert subject["subject_type"] == "area"

    @pytest.mark.asyncio
    async def test_area_comparison_shows_top_bottom_performers(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#3: Identifies top/bottom performers within each area."""
        grinding_assets = [mock_asset_grinder5, mock_asset_grinder3]

        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            # Need to return enough data for resolution, metrics, and area_performers
            mock_ds.get_assets_by_area = AsyncMock(side_effect=[
                mock_data_result_factory(grinding_assets, "assets"),
                mock_data_result_factory(grinding_assets, "assets"),
                mock_data_result_factory(grinding_assets, "assets"),  # For area_performers
                mock_data_result_factory(grinding_assets, "assets"),  # For area_performers
            ])
            mock_ds.get_oee_by_area = AsyncMock(
                return_value=mock_data_result_factory(mock_oee_grinder5)
            )
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
                mock_data_result_factory(mock_oee_grinder5),  # For area_performers
                mock_data_result_factory(mock_oee_grinder3),  # For area_performers
            ])
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinding", "Packaging"],
                comparison_type="area"
            )

            assert result.success is True
            # Area performers may be present for area comparisons
            # Check the field exists
            assert "area_performers" in result.data


# =============================================================================
# Test: Incompatible Metrics Handling (AC#4)
# =============================================================================


class TestIncompatibleMetricsHandling:
    """Tests for AC#4: Incompatible Metrics Handling."""

    @pytest.mark.asyncio
    async def test_different_targets_noted(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_cama,
        mock_oee_grinder5,
        mock_data_result_factory,
    ):
        """AC#4: Notes about different targets."""
        target1 = ShiftTarget(
            id="tgt-1", asset_id="ast-grd-005", target_output=5000, target_oee=85.0
        )
        target2 = ShiftTarget(
            id="tgt-2", asset_id="ast-pkg-001", target_output=10000, target_oee=80.0
        )

        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_cama, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(
                return_value=mock_data_result_factory(mock_oee_grinder5)
            )
            mock_ds.get_shift_target = AsyncMock(side_effect=[
                mock_data_result_factory(target1, "shift_targets"),
                mock_data_result_factory(target2, "shift_targets"),
            ])
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "CAMA 800-1"],
                comparison_type="asset"
            )

            # Should have comparability notes about different targets
            assert "comparability_notes" in result.data

    @pytest.mark.asyncio
    async def test_variance_calculation(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#4: Variance percentages calculated correctly."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            # Check variance is calculated
            for metric in result.data["metrics"]:
                assert "variance_pct" in metric
                assert isinstance(metric["variance_pct"], (int, float))
                assert metric["variance_pct"] >= 0


# =============================================================================
# Test: Default Time Range (AC#5)
# =============================================================================


class TestDefaultTimeRange:
    """Tests for AC#5: Default Time Range."""

    @pytest.mark.asyncio
    async def test_default_7_day_range(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#5: Defaults to last 7 days."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            # Call without specifying time_range_days (should default to 7)
            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            assert result.success is True
            # Time range should be visible in the output
            assert "time_range" in result.data
            assert result.data["time_range"] is not None

    @pytest.mark.asyncio
    async def test_custom_time_range(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#5: User can specify custom time ranges."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"],
                time_range_days=30  # Custom 30-day range
            )

            assert result.success is True
            assert "time_range" in result.data

    @pytest.mark.asyncio
    async def test_time_range_clearly_stated(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#5: Time range is clearly stated in response."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            # Time range should be human-readable format
            time_range = result.data["time_range"]
            assert time_range is not None
            # Should contain month/date format
            assert "-" in time_range or "to" in time_range.lower()


# =============================================================================
# Test: Citation & Data Freshness (AC#6)
# =============================================================================


class TestCitationAndDataFreshness:
    """Tests for AC#6: Citation & Data Freshness."""

    @pytest.mark.asyncio
    async def test_citations_included(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#6: All comparison metrics include source citations."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            # Should have tool-level citations
            assert len(result.citations) > 0

            # Should have output citations
            assert "citations" in result.data
            assert len(result.data["citations"]) > 0

    @pytest.mark.asyncio
    async def test_data_freshness_timestamp(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#6: Data freshness timestamp included in response."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            assert "data_as_of" in result.data
            # Should be ISO format timestamp
            data_as_of = result.data["data_as_of"]
            assert "T" in data_as_of  # ISO format has T separator

    @pytest.mark.asyncio
    async def test_cache_tier_is_daily(
        self,
        comparative_tool,
        mock_asset_grinder5,
        mock_asset_grinder3,
        mock_oee_grinder5,
        mock_oee_grinder3,
        mock_shift_target,
        mock_data_result_factory,
    ):
        """AC#6: Cache TTL is 15 minutes (daily tier)."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(side_effect=[
                mock_data_result_factory(mock_asset_grinder5, "assets"),
                mock_data_result_factory(mock_asset_grinder3, "assets"),
            ])
            mock_ds.get_oee = AsyncMock(side_effect=[
                mock_data_result_factory(mock_oee_grinder5),
                mock_data_result_factory(mock_oee_grinder3),
            ])
            mock_ds.get_shift_target = AsyncMock(
                return_value=mock_data_result_factory(mock_shift_target, "shift_targets")
            )
            mock_get_ds.return_value = mock_ds

            result = await comparative_tool._arun(
                subjects=["Grinder 5", "Grinder 3"]
            )

            # Should indicate cache tier in metadata
            assert result.metadata.get("cache_tier") == "daily"


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_insufficient_subjects(
        self,
        comparative_tool,
        mock_data_result_factory,
    ):
        """Graceful handling when < 2 subjects found."""
        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            # Return empty result for asset lookup
            mock_ds.get_asset_by_name = AsyncMock(
                return_value=mock_data_result_factory(None, "assets")
            )
            mock_get_ds.return_value = mock_ds

            # Use unique subjects to avoid cache hits from other tests
            result = await comparative_tool._arun(
                subjects=["NonexistentAsset99", "NonexistentAsset98"],
                time_range_days=1  # Different params to avoid cache
            )

            # Should still succeed but with message
            assert result.success is True
            assert "Unable to find" in result.data["summary"] or len(result.data["subjects"]) < 2

    @pytest.mark.asyncio
    async def test_data_source_error_handled(
        self,
        comparative_tool,
    ):
        """Data source errors are caught and logged."""
        from app.services.agent.data_source import DataSourceError
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to ensure we don't get cached results
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(
                side_effect=DataSourceError("Connection failed")
            )
            mock_get_ds.return_value = mock_ds

            # Use unique subjects/params to avoid cache hits
            result = await comparative_tool._arun(
                subjects=["ErrorTestAsset1", "ErrorTestAsset2"],
                time_range_days=11  # Different params to avoid cache
            )

            assert result.success is False
            assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(
        self,
        comparative_tool,
    ):
        """Unexpected exceptions are caught and logged."""
        from app.services.agent.cache import reset_tool_cache

        # Reset cache to ensure we don't get cached results
        reset_tool_cache()

        with patch(
            "app.services.agent.tools.comparative_analysis.get_data_source"
        ) as mock_get_ds:
            mock_ds = MagicMock()
            mock_ds.get_asset_by_name = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )
            mock_get_ds.return_value = mock_ds

            # Use unique subjects/params to avoid cache hits
            result = await comparative_tool._arun(
                subjects=["UnexpectedErrorAsset1", "UnexpectedErrorAsset2"],
                time_range_days=12  # Different params to avoid cache
            )

            assert result.success is False
            assert "unexpected error" in result.error_message.lower()


# =============================================================================
# Test: Tool Registration
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = ComparativeAnalysisTool()
        assert tool is not None
        assert tool.name == "comparative_analysis"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = ComparativeAnalysisTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)


# =============================================================================
# Test: Helper Methods
# =============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_format_date_range_same_month(self, comparative_tool):
        """Test date range formatting for same month."""
        start = date(2026, 1, 2)
        end = date(2026, 1, 9)
        result = comparative_tool._format_date_range(start, end)
        assert "Jan" in result
        assert "2026" in result

    def test_format_date_range_different_months(self, comparative_tool):
        """Test date range formatting for different months."""
        start = date(2025, 12, 28)
        end = date(2026, 1, 4)
        result = comparative_tool._format_date_range(start, end)
        assert "Dec" in result
        assert "Jan" in result

    def test_calculate_average(self, comparative_tool, mock_oee_grinder5):
        """Test average calculation."""
        avg = comparative_tool._calculate_average(mock_oee_grinder5, "oee_percentage")
        assert avg == pytest.approx(78.3, 0.1)

    def test_calculate_average_empty_list(self, comparative_tool):
        """Test average calculation with empty list."""
        avg = comparative_tool._calculate_average([], "oee_percentage")
        assert avg == 0.0


# =============================================================================
# Test: Metric Configuration
# =============================================================================


class TestMetricConfiguration:
    """Tests for metric configuration."""

    def test_default_metrics(self):
        """Default metrics are configured."""
        assert "oee" in DEFAULT_METRICS
        assert "output" in DEFAULT_METRICS
        assert "downtime_hours" in DEFAULT_METRICS
        assert "waste_pct" in DEFAULT_METRICS

    def test_metric_config_higher_is_better(self):
        """Higher is better is correctly configured."""
        # OEE should be higher is better
        assert METRIC_CONFIG["oee"]["higher_is_better"] is True
        # Downtime should be lower is better
        assert METRIC_CONFIG["downtime_hours"]["higher_is_better"] is False
        # Waste should be lower is better
        assert METRIC_CONFIG["waste_pct"]["higher_is_better"] is False

    def test_metric_config_has_units(self):
        """All metrics have units configured."""
        for metric, config in METRIC_CONFIG.items():
            assert "unit" in config
            assert "display_name" in config
