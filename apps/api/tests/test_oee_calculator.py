"""
Tests for OEE Calculator Service.

Story: 2.4 - OEE Metrics View
AC: #2 - OEE metrics computed from daily_summaries and live_snapshots
AC: #10 - Proper error handling and data validation
"""

import pytest
from app.services.oee_calculator import (
    calculate_availability,
    calculate_performance,
    calculate_quality,
    calculate_overall_oee,
    calculate_oee_from_daily_summary,
    calculate_oee_from_live_snapshot,
    calculate_plant_wide_oee,
    get_oee_status,
    get_default_oee_target,
    AssetOEE,
    OEEComponents,
    OEE_GREEN_THRESHOLD,
    OEE_YELLOW_THRESHOLD,
)


# =============================================================================
# Unit Tests for OEE Status Classification
# =============================================================================


class TestGetOEEStatus:
    """Tests for OEE status classification per AC #8."""

    def test_green_status_at_threshold(self):
        """AC#8: Green status when OEE >= 85%."""
        assert get_oee_status(85.0) == "green"

    def test_green_status_above_threshold(self):
        """AC#8: Green status when OEE > 85%."""
        assert get_oee_status(95.0) == "green"
        assert get_oee_status(100.0) == "green"

    def test_yellow_status_at_lower_threshold(self):
        """AC#8: Yellow status when OEE = 70%."""
        assert get_oee_status(70.0) == "yellow"

    def test_yellow_status_in_range(self):
        """AC#8: Yellow status when OEE 70-84%."""
        assert get_oee_status(75.0) == "yellow"
        assert get_oee_status(84.9) == "yellow"

    def test_red_status_below_threshold(self):
        """AC#8: Red status when OEE < 70%."""
        assert get_oee_status(69.9) == "red"
        assert get_oee_status(50.0) == "red"
        assert get_oee_status(0.0) == "red"

    def test_unknown_status_when_null(self):
        """AC#10: Unknown status when OEE is null."""
        assert get_oee_status(None) == "unknown"


# =============================================================================
# Unit Tests for Individual OEE Component Calculations
# =============================================================================


class TestCalculateAvailability:
    """Tests for Availability calculation.

    Formula: (Run Time / Planned Production Time) x 100
    AC: #1 - OEE displays Availability component
    """

    def test_perfect_availability(self):
        """100% availability when no downtime."""
        assert calculate_availability(480, 480) == 100.0

    def test_partial_availability(self):
        """Correct availability with some downtime."""
        # 400 minutes run time out of 480 planned
        result = calculate_availability(400, 480)
        assert result == pytest.approx(83.3, rel=0.1)

    def test_zero_run_time(self):
        """0% availability when no run time."""
        assert calculate_availability(0, 480) == 0.0

    def test_capped_at_100(self):
        """Availability capped at 100% (handles data anomalies)."""
        # Run time exceeds planned time (data anomaly)
        assert calculate_availability(500, 480) == 100.0

    def test_null_run_time(self):
        """AC#10: Returns None when run_time is null."""
        assert calculate_availability(None, 480) is None

    def test_null_planned_time(self):
        """AC#10: Returns None when planned_time is null."""
        assert calculate_availability(480, None) is None

    def test_zero_planned_time(self):
        """AC#10: Returns None when planned_time is zero (avoid div by zero)."""
        assert calculate_availability(480, 0) is None

    def test_negative_planned_time(self):
        """AC#10: Returns None when planned_time is negative."""
        assert calculate_availability(480, -100) is None


class TestCalculatePerformance:
    """Tests for Performance calculation.

    Formula: (Actual Output / Target Output) x 100
    AC: #1 - OEE displays Performance component
    """

    def test_perfect_performance(self):
        """100% performance when actual equals target."""
        assert calculate_performance(1000, 1000) == 100.0

    def test_above_target_performance(self):
        """Above 100% when exceeding target (not capped)."""
        result = calculate_performance(1100, 1000)
        assert result == 110.0

    def test_below_target_performance(self):
        """Below 100% when under target."""
        result = calculate_performance(800, 1000)
        assert result == 80.0

    def test_zero_actual_output(self):
        """0% when no actual output."""
        assert calculate_performance(0, 1000) == 0.0

    def test_null_actual_output(self):
        """AC#10: Returns None when actual_output is null."""
        assert calculate_performance(None, 1000) is None

    def test_null_target_output(self):
        """AC#10: Returns None when target_output is null."""
        assert calculate_performance(1000, None) is None

    def test_zero_target_output(self):
        """AC#10: Returns None when target_output is zero (avoid div by zero)."""
        assert calculate_performance(1000, 0) is None


class TestCalculateQuality:
    """Tests for Quality calculation.

    Formula: (Good Units / Total Units) x 100
    AC: #1 - OEE displays Quality component
    """

    def test_perfect_quality(self):
        """100% quality when all units are good."""
        assert calculate_quality(1000, 1000) == 100.0

    def test_partial_quality(self):
        """Correct quality with some waste."""
        result = calculate_quality(950, 1000)
        assert result == 95.0

    def test_zero_good_units(self):
        """0% quality when no good units."""
        assert calculate_quality(0, 1000) == 0.0

    def test_capped_at_100(self):
        """Quality capped at 100% (handles data anomalies)."""
        # Good units exceeds total (data anomaly)
        assert calculate_quality(1100, 1000) == 100.0

    def test_null_good_output(self):
        """AC#10: Returns None when good_output is null."""
        assert calculate_quality(None, 1000) is None

    def test_null_total_output(self):
        """AC#10: Returns None when total_output is null."""
        assert calculate_quality(1000, None) is None

    def test_zero_total_output(self):
        """AC#10: Returns None when total_output is zero (avoid div by zero)."""
        assert calculate_quality(0, 0) is None


class TestCalculateOverallOEE:
    """Tests for Overall OEE calculation.

    Formula: (Availability x Performance x Quality) / 10000
    AC: #1 - OEE displays overall percentage
    """

    def test_perfect_oee(self):
        """100% OEE with perfect components."""
        result = calculate_overall_oee(100.0, 100.0, 100.0)
        assert result == 100.0

    def test_typical_oee(self):
        """Typical OEE calculation."""
        # A=90%, P=95%, Q=98%
        result = calculate_overall_oee(90.0, 95.0, 98.0)
        expected = (90.0 * 95.0 * 98.0) / 10000
        assert result == pytest.approx(expected, rel=0.1)

    def test_world_class_oee(self):
        """World-class OEE benchmark (~85%)."""
        # A=90%, P=95%, Q=99.9%
        result = calculate_overall_oee(90.0, 95.0, 99.9)
        assert result >= 85.0

    def test_null_availability(self):
        """AC#10: Returns None when availability is null."""
        assert calculate_overall_oee(None, 95.0, 98.0) is None

    def test_null_performance(self):
        """AC#10: Returns None when performance is null."""
        assert calculate_overall_oee(90.0, None, 98.0) is None

    def test_null_quality(self):
        """AC#10: Returns None when quality is null."""
        assert calculate_overall_oee(90.0, 95.0, None) is None

    def test_all_null_components(self):
        """AC#10: Returns None when all components are null."""
        assert calculate_overall_oee(None, None, None) is None


# =============================================================================
# Tests for OEE Calculation from Data Records
# =============================================================================


class TestCalculateOEEFromDailySummary:
    """Tests for calculating OEE from daily_summaries table data.

    AC: #2 - OEE metrics computed from daily_summaries (T-1)
    """

    def test_complete_data(self):
        """Calculates all OEE components with complete data."""
        daily_summary = {
            "asset_id": "test-uuid",
            "actual_output": 950,
            "target_output": 1000,
            "waste_count": 50,
            "downtime_minutes": 48,  # 10% downtime of 480-min shift
        }
        shift_target = {"planned_time": 480}

        result = calculate_oee_from_daily_summary(daily_summary, shift_target)

        assert isinstance(result, OEEComponents)
        assert result.availability is not None
        assert result.performance is not None
        assert result.quality is not None
        assert result.overall is not None
        assert result.status in ["green", "yellow", "red", "unknown"]

    def test_handles_missing_waste_count(self):
        """Defaults waste_count to 0 when missing."""
        daily_summary = {
            "asset_id": "test-uuid",
            "actual_output": 1000,
            "target_output": 1000,
            "downtime_minutes": 0,
        }

        result = calculate_oee_from_daily_summary(daily_summary)

        # With no waste and no downtime, should be close to 100%
        assert result.quality is not None
        assert result.quality >= 95.0

    def test_handles_null_actual_output(self):
        """AC#10: Handles null actual_output gracefully."""
        daily_summary = {
            "asset_id": "test-uuid",
            "actual_output": None,
            "target_output": 1000,
        }

        result = calculate_oee_from_daily_summary(daily_summary)

        # Performance and quality should be None
        assert result.performance is None
        assert result.quality is None


class TestCalculateOEEFromLiveSnapshot:
    """Tests for calculating OEE from live_snapshots table data.

    AC: #2 - OEE metrics computed from live_snapshots (T-15m)
    """

    def test_calculates_performance_from_live_data(self):
        """Calculates performance from live snapshot data."""
        live_snapshot = {
            "asset_id": "test-uuid",
            "current_output": 950,
            "target_output": 1000,
        }

        result = calculate_oee_from_live_snapshot(live_snapshot)

        assert isinstance(result, OEEComponents)
        assert result.performance == 95.0  # 950/1000 * 100

    def test_estimates_oee_from_performance(self):
        """Estimates overall OEE using performance with assumed values."""
        live_snapshot = {
            "asset_id": "test-uuid",
            "current_output": 900,
            "target_output": 1000,
        }

        result = calculate_oee_from_live_snapshot(live_snapshot)

        # Overall should be calculated with assumed availability/quality
        assert result.overall is not None
        assert result.status in ["green", "yellow", "red", "unknown"]

    def test_handles_zero_target_output(self):
        """AC#10: Handles zero target_output gracefully."""
        live_snapshot = {
            "asset_id": "test-uuid",
            "current_output": 100,
            "target_output": 0,
        }

        result = calculate_oee_from_live_snapshot(live_snapshot)

        assert result.performance is None


# =============================================================================
# Tests for Plant-Wide OEE Calculation
# =============================================================================


class TestCalculatePlantWideOEE:
    """Tests for plant-wide OEE aggregation.

    AC: #3 - Plant-wide OEE percentage prominently displayed
    """

    def test_averages_multiple_assets(self):
        """Calculates average OEE across multiple assets."""
        asset_oee_list = [
            AssetOEE(
                asset_id="1", name="Asset 1", area="A",
                oee=80.0, availability=90.0, performance=90.0, quality=98.0,
                target=85.0, status="yellow"
            ),
            AssetOEE(
                asset_id="2", name="Asset 2", area="A",
                oee=90.0, availability=95.0, performance=95.0, quality=99.0,
                target=85.0, status="green"
            ),
        ]

        result = calculate_plant_wide_oee(asset_oee_list)

        assert result.overall == 85.0  # Average of 80 and 90
        assert result.availability == pytest.approx(92.5, rel=0.1)

    def test_handles_empty_list(self):
        """AC#10: Handles empty asset list gracefully."""
        result = calculate_plant_wide_oee([])

        assert result.overall is None
        assert result.status == "unknown"

    def test_handles_assets_with_null_values(self):
        """AC#10: Filters out null values in average calculation."""
        asset_oee_list = [
            AssetOEE(
                asset_id="1", name="Asset 1", area="A",
                oee=80.0, availability=90.0, performance=90.0, quality=98.0,
                target=85.0, status="yellow"
            ),
            AssetOEE(
                asset_id="2", name="Asset 2", area="A",
                oee=None, availability=None, performance=None, quality=None,
                target=85.0, status="unknown"
            ),
        ]

        result = calculate_plant_wide_oee(asset_oee_list)

        # Should only average the one asset with data
        assert result.overall == 80.0


# =============================================================================
# Tests for Default Values
# =============================================================================


class TestGetDefaultOEETarget:
    """Tests for default OEE target value."""

    def test_default_target_is_85(self):
        """AC#7: Default OEE target is 85% (world-class benchmark)."""
        assert get_default_oee_target() == 85.0


# =============================================================================
# Tests for Data Classes
# =============================================================================


class TestOEEComponents:
    """Tests for OEEComponents dataclass."""

    def test_to_dict(self):
        """OEEComponents can be converted to dictionary."""
        components = OEEComponents(
            availability=90.0,
            performance=95.0,
            quality=98.0,
            overall=83.7,
            status="yellow",
        )

        result = components.to_dict()

        assert result["availability"] == 90.0
        assert result["performance"] == 95.0
        assert result["quality"] == 98.0
        assert result["overall"] == 83.7
        assert result["status"] == "yellow"


class TestAssetOEE:
    """Tests for AssetOEE dataclass."""

    def test_to_dict(self):
        """AssetOEE can be converted to dictionary."""
        asset_oee = AssetOEE(
            asset_id="test-uuid",
            name="Grinder 5",
            area="Grinding",
            oee=82.3,
            availability=90.0,
            performance=95.0,
            quality=96.2,
            target=85.0,
            status="yellow",
        )

        result = asset_oee.to_dict()

        assert result["asset_id"] == "test-uuid"
        assert result["name"] == "Grinder 5"
        assert result["area"] == "Grinding"
        assert result["oee"] == 82.3
        assert result["status"] == "yellow"
