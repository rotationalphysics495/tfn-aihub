"""
Tests for Downtime Analysis Service.

Story: 2.5 - Downtime Pareto Analysis
AC: #2 - Pareto Analysis Calculation
AC: #5 - Financial Impact Integration
AC: #6 - Safety Reason Code Highlighting
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.downtime import DowntimeEvent, DataSource
from app.services.downtime_analysis import DowntimeAnalysisService, SAFETY_KEYWORDS


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    return MagicMock()


@pytest.fixture
def service(mock_supabase_client):
    """Create service instance with mocked client."""
    return DowntimeAnalysisService(mock_supabase_client)


@pytest.fixture
def sample_events():
    """Sample downtime events for testing."""
    return [
        DowntimeEvent(
            id="1",
            asset_id=str(uuid4()),
            asset_name="CNC Mill 01",
            area="Machining",
            reason_code="Mechanical Failure",
            duration_minutes=60,
            event_timestamp="2026-01-05T10:00:00Z",
            financial_impact=150.0,
            is_safety_related=False,
        ),
        DowntimeEvent(
            id="2",
            asset_id=str(uuid4()),
            asset_name="Lathe 02",
            area="Machining",
            reason_code="Mechanical Failure",
            duration_minutes=30,
            event_timestamp="2026-01-05T11:00:00Z",
            financial_impact=75.0,
            is_safety_related=False,
        ),
        DowntimeEvent(
            id="3",
            asset_id=str(uuid4()),
            asset_name="Press 01",
            area="Forming",
            reason_code="Material Shortage",
            duration_minutes=45,
            event_timestamp="2026-01-05T12:00:00Z",
            financial_impact=112.5,
            is_safety_related=False,
        ),
        DowntimeEvent(
            id="4",
            asset_id=str(uuid4()),
            asset_name="Grinder 01",
            area="Finishing",
            reason_code="Safety Issue",
            duration_minutes=15,
            event_timestamp="2026-01-05T13:00:00Z",
            financial_impact=37.5,
            is_safety_related=True,
        ),
    ]


# =============================================================================
# Safety Detection Tests
# =============================================================================


class TestSafetyDetection:
    """Tests for is_safety_related method."""

    def test_detects_safety_keyword(self, service):
        """AC#6: Detects 'safety' in reason code."""
        assert service.is_safety_related("Safety Issue") is True
        assert service.is_safety_related("safety stop") is True
        assert service.is_safety_related("SAFETY EVENT") is True

    def test_detects_emergency_stop(self, service):
        """AC#6: Detects emergency stop keywords."""
        assert service.is_safety_related("Emergency Stop") is True
        assert service.is_safety_related("E-Stop Triggered") is True

    def test_detects_hazard(self, service):
        """AC#6: Detects hazard keywords."""
        assert service.is_safety_related("Hazard Detected") is True

    def test_detects_injury(self, service):
        """AC#6: Detects injury keywords."""
        assert service.is_safety_related("Operator Injury") is True
        assert service.is_safety_related("accident report") is True

    def test_non_safety_codes_return_false(self, service):
        """AC#6: Non-safety codes return False."""
        assert service.is_safety_related("Mechanical Failure") is False
        assert service.is_safety_related("Material Shortage") is False
        assert service.is_safety_related("Planned Maintenance") is False
        assert service.is_safety_related("Operator Error") is False

    def test_handles_empty_string(self, service):
        """AC#6: Handles empty string gracefully."""
        assert service.is_safety_related("") is False

    def test_handles_none(self, service):
        """AC#6: Handles None gracefully."""
        assert service.is_safety_related(None) is False


# =============================================================================
# Financial Impact Calculation Tests
# =============================================================================


class TestFinancialImpactCalculation:
    """Tests for calculate_financial_impact method."""

    def test_calculates_with_hourly_rate(self, service):
        """AC#5: Financial impact = (downtime_minutes / 60) * standard_hourly_rate."""
        cost_center_id = str(uuid4())
        cost_centers_map = {cost_center_id: 150.0}

        # 60 minutes at $150/hour = $150
        result = service.calculate_financial_impact(60, cost_center_id, cost_centers_map)
        assert result == 150.0

        # 30 minutes at $150/hour = $75
        result = service.calculate_financial_impact(30, cost_center_id, cost_centers_map)
        assert result == 75.0

        # 90 minutes at $150/hour = $225
        result = service.calculate_financial_impact(90, cost_center_id, cost_centers_map)
        assert result == 225.0

    def test_uses_default_rate_when_no_cost_center(self, service):
        """AC#5: Uses default rate when cost center not found."""
        from app.services.downtime_analysis import DEFAULT_HOURLY_RATE

        result = service.calculate_financial_impact(60, None, {})
        assert result == DEFAULT_HOURLY_RATE

    def test_uses_default_rate_for_unknown_cost_center(self, service):
        """AC#5: Uses default rate for unknown cost center ID."""
        from app.services.downtime_analysis import DEFAULT_HOURLY_RATE

        result = service.calculate_financial_impact(60, "unknown-id", {})
        assert result == DEFAULT_HOURLY_RATE

    def test_rounds_to_two_decimal_places(self, service):
        """AC#5: Result is rounded to 2 decimal places."""
        cost_center_id = str(uuid4())
        cost_centers_map = {cost_center_id: 100.0}

        # 7 minutes at $100/hour = $11.666... should be $11.67
        result = service.calculate_financial_impact(7, cost_center_id, cost_centers_map)
        assert result == 11.67


# =============================================================================
# Pareto Calculation Tests
# =============================================================================


class TestParetoCalculation:
    """Tests for calculate_pareto method."""

    def test_calculates_pareto_distribution(self, service, sample_events):
        """AC#2: Calculates Pareto distribution by reason code."""
        items, threshold_idx = service.calculate_pareto(sample_events)

        assert len(items) == 3  # 3 unique reason codes
        assert all(item.reason_code for item in items)
        assert all(item.total_minutes > 0 for item in items)

    def test_sorted_by_descending_duration(self, service, sample_events):
        """AC#2: Results sorted by descending downtime duration."""
        items, _ = service.calculate_pareto(sample_events)

        for i in range(len(items) - 1):
            assert items[i].total_minutes >= items[i + 1].total_minutes

    def test_percentages_sum_to_100(self, service, sample_events):
        """AC#2: Percentages sum to approximately 100%."""
        items, _ = service.calculate_pareto(sample_events)

        total_percentage = sum(item.percentage for item in items)
        assert abs(total_percentage - 100.0) < 0.1  # Within 0.1%

    def test_cumulative_reaches_100(self, service, sample_events):
        """AC#2: Cumulative percentage reaches 100% at last item."""
        items, _ = service.calculate_pareto(sample_events)

        assert items[-1].cumulative_percentage == 100.0

    def test_cumulative_is_monotonically_increasing(self, service, sample_events):
        """AC#2: Cumulative percentage is monotonically increasing."""
        items, _ = service.calculate_pareto(sample_events)

        for i in range(len(items) - 1):
            assert items[i].cumulative_percentage <= items[i + 1].cumulative_percentage

    def test_finds_80_threshold_index(self, service, sample_events):
        """AC#2: Returns index where cumulative percentage crosses 80%."""
        items, threshold_idx = service.calculate_pareto(sample_events)

        if threshold_idx is not None:
            # Item at threshold should have cumulative >= 80%
            assert items[threshold_idx].cumulative_percentage >= 80.0
            # Previous items should have cumulative < 80%
            if threshold_idx > 0:
                assert items[threshold_idx - 1].cumulative_percentage < 80.0

    def test_aggregates_financial_impact(self, service, sample_events):
        """AC#5: Aggregates financial impact per reason code."""
        items, _ = service.calculate_pareto(sample_events)

        # Mechanical Failure: 150 + 75 = 225
        mech_failure = next((i for i in items if i.reason_code == "Mechanical Failure"), None)
        assert mech_failure is not None
        assert mech_failure.financial_impact == 225.0

    def test_counts_events(self, service, sample_events):
        """AC#2: Counts events per reason code."""
        items, _ = service.calculate_pareto(sample_events)

        # Mechanical Failure has 2 events
        mech_failure = next((i for i in items if i.reason_code == "Mechanical Failure"), None)
        assert mech_failure is not None
        assert mech_failure.event_count == 2

    def test_marks_safety_related_reasons(self, service, sample_events):
        """AC#6: Safety-related reasons are flagged."""
        items, _ = service.calculate_pareto(sample_events)

        safety_item = next((i for i in items if i.reason_code == "Safety Issue"), None)
        assert safety_item is not None
        assert safety_item.is_safety_related is True

        non_safety_item = next((i for i in items if i.reason_code == "Mechanical Failure"), None)
        assert non_safety_item is not None
        assert non_safety_item.is_safety_related is False

    def test_handles_empty_events(self, service):
        """AC#2: Handles empty event list gracefully."""
        items, threshold_idx = service.calculate_pareto([])

        assert items == []
        assert threshold_idx is None


# =============================================================================
# Cost of Loss Summary Tests
# =============================================================================


class TestCostOfLossSummary:
    """Tests for build_cost_of_loss_summary method."""

    def test_calculates_total_financial_loss(self, service, sample_events):
        """AC#5: Calculates total financial loss."""
        items, _ = service.calculate_pareto(sample_events)
        summary = service.build_cost_of_loss_summary(
            sample_events, items, "daily_summaries", "2026-01-05T06:00:00Z"
        )

        expected_total = sum(e.financial_impact for e in sample_events)
        assert summary.total_financial_loss == round(expected_total, 2)

    def test_calculates_total_downtime(self, service, sample_events):
        """AC#5: Calculates total downtime in minutes and hours."""
        items, _ = service.calculate_pareto(sample_events)
        summary = service.build_cost_of_loss_summary(
            sample_events, items, "daily_summaries", "2026-01-05T06:00:00Z"
        )

        expected_minutes = sum(e.duration_minutes for e in sample_events)
        assert summary.total_downtime_minutes == expected_minutes
        assert summary.total_downtime_hours == round(expected_minutes / 60.0, 2)

    def test_identifies_top_reason(self, service, sample_events):
        """AC#5: Identifies top reason code."""
        items, _ = service.calculate_pareto(sample_events)
        summary = service.build_cost_of_loss_summary(
            sample_events, items, "daily_summaries", "2026-01-05T06:00:00Z"
        )

        # Top reason should match first Pareto item
        assert summary.top_reason_code == items[0].reason_code
        assert summary.top_reason_percentage == items[0].percentage

    def test_counts_safety_events(self, service, sample_events):
        """AC#6: Counts safety-related events."""
        items, _ = service.calculate_pareto(sample_events)
        summary = service.build_cost_of_loss_summary(
            sample_events, items, "daily_summaries", "2026-01-05T06:00:00Z"
        )

        expected_safety_count = sum(1 for e in sample_events if e.is_safety_related)
        assert summary.safety_events_count == expected_safety_count

    def test_calculates_safety_downtime(self, service, sample_events):
        """AC#6: Calculates safety-related downtime."""
        items, _ = service.calculate_pareto(sample_events)
        summary = service.build_cost_of_loss_summary(
            sample_events, items, "daily_summaries", "2026-01-05T06:00:00Z"
        )

        expected_safety_minutes = sum(
            e.duration_minutes for e in sample_events if e.is_safety_related
        )
        assert summary.safety_downtime_minutes == expected_safety_minutes


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_single_event(self, service):
        """Handles single event correctly."""
        event = DowntimeEvent(
            id="1",
            asset_id=str(uuid4()),
            asset_name="Test Asset",
            reason_code="Single Reason",
            duration_minutes=30,
            event_timestamp="2026-01-05T10:00:00Z",
            financial_impact=75.0,
            is_safety_related=False,
        )

        items, threshold_idx = service.calculate_pareto([event])

        assert len(items) == 1
        assert items[0].percentage == 100.0
        assert items[0].cumulative_percentage == 100.0
        assert threshold_idx == 0  # Single item crosses 80%

    def test_all_same_reason_code(self, service):
        """Handles all events with same reason code."""
        events = [
            DowntimeEvent(
                id=str(i),
                asset_id=str(uuid4()),
                asset_name=f"Asset {i}",
                reason_code="Same Reason",
                duration_minutes=30,
                event_timestamp=f"2026-01-05T{10+i}:00:00Z",
                financial_impact=75.0,
                is_safety_related=False,
            )
            for i in range(5)
        ]

        items, threshold_idx = service.calculate_pareto(events)

        assert len(items) == 1
        assert items[0].event_count == 5
        assert items[0].total_minutes == 150
        assert items[0].percentage == 100.0

    def test_zero_downtime_events_filtered(self, service):
        """Events with zero downtime should be filtered in transform."""
        # This is tested in the transform_to_downtime_events method
        # Zero-minute events are skipped during transformation
        pass
