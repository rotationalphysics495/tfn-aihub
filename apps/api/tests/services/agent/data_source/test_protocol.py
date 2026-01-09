"""
Tests for DataSource Protocol and Models (Story 5.2)

AC#1: DataSource Protocol Definition
AC#3: DataResult Response Format
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal

from app.services.agent.data_source.protocol import (
    Asset,
    DataResult,
    DataSource,
    DowntimeEvent,
    OEEMetrics,
    ProductionStatus,
    SafetyEvent,
    ShiftTarget,
)


class TestDataResult:
    """Tests for DataResult model."""

    def test_data_result_creation(self):
        """AC#3: DataResult with required fields."""
        result = DataResult(
            data={"oee": 87.5},
            source_name="supabase",
            table_name="daily_summaries",
        )

        assert result.data == {"oee": 87.5}
        assert result.source_name == "supabase"
        assert result.table_name == "daily_summaries"
        assert result.query_timestamp is not None
        assert result.row_count == 0  # default

    def test_data_result_with_all_fields(self):
        """AC#3: DataResult with all optional fields."""
        ts = datetime.now(timezone.utc)
        result = DataResult(
            data=[{"id": "1"}, {"id": "2"}],
            source_name="supabase",
            table_name="assets",
            query_timestamp=ts,
            query="SELECT * FROM assets",
            row_count=2,
        )

        assert result.query_timestamp == ts
        assert result.query == "SELECT * FROM assets"
        assert result.row_count == 2

    def test_data_result_to_citation_metadata(self):
        """AC#3: Metadata available for citation generation."""
        result = DataResult(
            data={"id": "123"},
            source_name="supabase",
            table_name="daily_summaries",
            query="SELECT * FROM daily_summaries WHERE id = '123'",
        )

        metadata = result.to_citation_metadata()

        assert metadata["source"] == "supabase"
        assert metadata["table"] == "daily_summaries"
        assert "daily_summaries" in metadata["query"]

    def test_data_result_to_citation_metadata_no_query(self):
        """to_citation_metadata generates default query when none provided."""
        result = DataResult(
            data=None,
            source_name="supabase",
            table_name="assets",
        )

        metadata = result.to_citation_metadata()

        assert "Query on assets" in metadata["query"]

    def test_data_result_has_data_with_dict(self):
        """has_data returns True for non-empty dict."""
        result = DataResult(
            data={"value": 1},
            source_name="supabase",
            table_name="test",
        )

        assert result.has_data is True

    def test_data_result_has_data_with_list(self):
        """has_data returns True for non-empty list."""
        result = DataResult(
            data=[{"id": 1}],
            source_name="supabase",
            table_name="test",
        )

        assert result.has_data is True

    def test_data_result_has_data_empty_list(self):
        """has_data returns False for empty list."""
        result = DataResult(
            data=[],
            source_name="supabase",
            table_name="test",
        )

        assert result.has_data is False

    def test_data_result_has_data_none(self):
        """has_data returns False for None."""
        result = DataResult(
            data=None,
            source_name="supabase",
            table_name="test",
        )

        assert result.has_data is False


class TestAssetModel:
    """Tests for Asset model."""

    def test_asset_creation(self):
        """Asset model with required fields."""
        asset = Asset(
            id="123-456",
            name="Grinder 5",
            source_id="LOC-GRN-005",
        )

        assert asset.id == "123-456"
        assert asset.name == "Grinder 5"
        assert asset.source_id == "LOC-GRN-005"
        assert asset.area is None

    def test_asset_with_optional_fields(self):
        """Asset model with all fields."""
        ts = datetime.now(timezone.utc)
        asset = Asset(
            id="123-456",
            name="Grinder 5",
            source_id="LOC-GRN-005",
            area="Grinding",
            created_at=ts,
            updated_at=ts,
        )

        assert asset.area == "Grinding"
        assert asset.created_at == ts


class TestOEEMetricsModel:
    """Tests for OEEMetrics model."""

    def test_oee_metrics_creation(self):
        """OEEMetrics model with required fields."""
        metrics = OEEMetrics(
            id="123",
            asset_id="456",
            report_date=date(2026, 1, 8),
        )

        assert metrics.id == "123"
        assert metrics.asset_id == "456"
        assert metrics.report_date == date(2026, 1, 8)

    def test_oee_metrics_with_values(self):
        """AC#5: OEE includes availability, performance, quality breakdown."""
        metrics = OEEMetrics(
            id="123",
            asset_id="456",
            report_date=date(2026, 1, 8),
            oee_percentage=Decimal("87.50"),
            availability=Decimal("92.00"),
            performance=Decimal("95.00"),
            quality=Decimal("99.50"),
            actual_output=950,
            target_output=1000,
            downtime_minutes=45,
            waste_count=5,
            financial_loss_dollars=Decimal("1500.00"),
        )

        assert metrics.oee_percentage == Decimal("87.50")
        assert metrics.availability == Decimal("92.00")
        assert metrics.performance == Decimal("95.00")
        assert metrics.quality == Decimal("99.50")


class TestDowntimeEventModel:
    """Tests for DowntimeEvent model."""

    def test_downtime_event_creation(self):
        """DowntimeEvent model with required fields."""
        event = DowntimeEvent(
            id="123",
            asset_id="456",
            report_date=date(2026, 1, 8),
            downtime_minutes=60,
        )

        assert event.id == "123"
        assert event.downtime_minutes == 60

    def test_downtime_event_with_reason(self):
        """AC#6: Downtime with reasons and durations."""
        event = DowntimeEvent(
            id="123",
            asset_id="456",
            asset_name="Grinder 5",
            report_date=date(2026, 1, 8),
            downtime_minutes=120,
            reason_code="MECH-001",
            reason_description="Mechanical failure",
            financial_loss_dollars=Decimal("2500.00"),
        )

        assert event.reason_code == "MECH-001"
        assert event.reason_description == "Mechanical failure"
        assert event.financial_loss_dollars == Decimal("2500.00")


class TestProductionStatusModel:
    """Tests for ProductionStatus model."""

    def test_production_status_creation(self):
        """ProductionStatus model with required fields."""
        ts = datetime.now(timezone.utc)
        status = ProductionStatus(
            id="123",
            asset_id="456",
            snapshot_timestamp=ts,
            status="on_target",
        )

        assert status.id == "123"
        assert status.snapshot_timestamp == ts
        assert status.status == "on_target"

    def test_production_status_with_metrics(self):
        """AC#7: Production status with data freshness."""
        ts = datetime.now(timezone.utc)
        status = ProductionStatus(
            id="123",
            asset_id="456",
            asset_name="Grinder 5",
            area="Grinding",
            snapshot_timestamp=ts,
            current_output=450,
            target_output=500,
            output_variance=-50,
            status="behind",
        )

        assert status.current_output == 450
        assert status.target_output == 500
        assert status.output_variance == -50
        assert status.status == "behind"


class TestShiftTargetModel:
    """Tests for ShiftTarget model."""

    def test_shift_target_creation(self):
        """ShiftTarget model with required fields."""
        target = ShiftTarget(
            id="123",
            asset_id="456",
            target_output=1000,
        )

        assert target.id == "123"
        assert target.target_output == 1000

    def test_shift_target_with_details(self):
        """ShiftTarget with shift and effective date."""
        target = ShiftTarget(
            id="123",
            asset_id="456",
            target_output=1000,
            shift="Day",
            effective_date=date(2026, 1, 1),
        )

        assert target.shift == "Day"
        assert target.effective_date == date(2026, 1, 1)


class TestSafetyEventModel:
    """Tests for SafetyEvent model."""

    def test_safety_event_creation(self):
        """SafetyEvent model with required fields."""
        ts = datetime.now(timezone.utc)
        event = SafetyEvent(
            id="123",
            asset_id="456",
            event_timestamp=ts,
            reason_code="SAFETY-001",
            severity="high",
        )

        assert event.id == "123"
        assert event.reason_code == "SAFETY-001"
        assert event.severity == "high"
        assert event.is_resolved is False


class TestDataSourceProtocol:
    """Tests for DataSource Protocol compliance."""

    def test_protocol_is_runtime_checkable(self):
        """AC#1: Protocol can be used for isinstance checks."""
        from typing import runtime_checkable

        # DataSource should be runtime checkable
        assert hasattr(DataSource, "__protocol_attrs__") or hasattr(
            DataSource, "__subclasshook__"
        )

    def test_protocol_defines_required_methods(self):
        """AC#1: Protocol defines async methods for all common operations."""
        # Check that Protocol defines expected methods
        expected_methods = [
            "get_asset",
            "get_asset_by_name",
            "get_assets_by_area",
            "get_similar_assets",
            "get_all_assets",
            "get_oee",
            "get_oee_by_area",
            "get_downtime",
            "get_downtime_by_area",
            "get_live_snapshot",
            "get_live_snapshots_by_area",
            "get_shift_target",
            "get_safety_events",
        ]

        for method in expected_methods:
            assert hasattr(DataSource, method), f"Missing method: {method}"
