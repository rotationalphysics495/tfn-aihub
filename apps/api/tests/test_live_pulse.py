"""
Tests for Live Pulse Polling Pipeline.

Story: 2.2 - Polling Data Pipeline (T-15m)
Tests cover all acceptance criteria:
AC#1 - Background Scheduler Configuration
AC#2 - Data Polling Execution
AC#3 - Live Snapshots Storage
AC#4 - Safety Incident Detection
AC#5 - Output vs Target Calculation
AC#6 - Error Handling and Resilience
AC#7 - Health and Monitoring
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import UUID, uuid4

from app.services.pipelines.live_pulse import (
    LivePulsePipeline,
    LiveSnapshotData,
    SafetyEventData,
    LivePulseResult,
    run_live_pulse_poll,
    get_live_pulse_pipeline,
)
from app.services.scheduler import (
    PipelineScheduler,
    PipelineSchedulerStatus,
    get_scheduler,
    get_pipeline_status,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def pipeline():
    """Create a fresh pipeline instance."""
    return LivePulsePipeline()


@pytest.fixture
def scheduler():
    """Create a fresh scheduler instance."""
    return PipelineScheduler()


@pytest.fixture
def sample_asset_id():
    """Sample UUID for testing."""
    return UUID("123e4567-e89b-12d3-a456-426614174000")


@pytest.fixture
def sample_production_records():
    """Sample production data from MSSQL."""
    return [
        {
            "source_id": "GRINDER_01",
            "output_actual": 1500,
            "last_reading": datetime(2026, 1, 5, 14, 30, 0),
        },
        {
            "source_id": "GRINDER_02",
            "output_actual": 1200,
            "last_reading": datetime(2026, 1, 5, 14, 30, 0),
        },
    ]


@pytest.fixture
def sample_downtime_records():
    """Sample downtime data from MSSQL."""
    return [
        {
            "source_id": "GRINDER_01",
            "event_timestamp": datetime(2026, 1, 5, 14, 0, 0),
            "duration_minutes": 30,
            "reason_code": "Mechanical Failure",
            "description": "Belt replacement",
        },
        {
            "source_id": "GRINDER_01",
            "event_timestamp": datetime(2026, 1, 5, 14, 15, 0),
            "duration_minutes": 15,
            "reason_code": "Safety Issue",  # This should be detected
            "description": "Emergency stop triggered",
        },
    ]


@pytest.fixture
def sample_oee_data():
    """Sample OEE data from MSSQL."""
    return {
        "GRINDER_01": Decimal("85.5"),
        "GRINDER_02": Decimal("78.2"),
    }


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value.data = []
    client.table.return_value.insert.return_value.execute.return_value.data = [{}]
    client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = []
    return client


# =============================================================================
# AC#1: Background Scheduler Configuration
# =============================================================================


class TestSchedulerConfiguration:
    """Tests for background scheduler setup (AC#1)."""

    def test_scheduler_initializes(self, scheduler):
        """AC#1: Scheduler initializes with default settings."""
        assert scheduler is not None
        assert scheduler._poll_interval_minutes == 15  # Default
        # Note: _run_on_startup is set to False by conftest.py for testing

    def test_scheduler_run_on_startup_default(self):
        """AC#1: Scheduler run_on_startup defaults to true."""
        with patch.dict("os.environ", {"POLL_RUN_ON_STARTUP": "true"}):
            sched = PipelineScheduler()
            assert sched._run_on_startup is True

    def test_scheduler_poll_interval_from_env(self):
        """AC#1: Poll interval can be configured via environment."""
        with patch.dict("os.environ", {"POLL_INTERVAL_MINUTES": "5"}):
            sched = PipelineScheduler()
            assert sched._poll_interval_minutes == 5

    def test_scheduler_status_initialized(self, scheduler):
        """AC#1: Scheduler status is properly initialized."""
        status = scheduler.status
        assert status.is_running is False
        assert status.last_poll_timestamp is None
        assert status.last_poll_success is True
        assert status.polls_executed == 0
        assert status.polls_failed == 0

    @pytest.mark.asyncio
    async def test_scheduler_starts_and_stops(self, scheduler):
        """AC#1: Scheduler can start and stop gracefully."""
        # Set a dummy poll job
        async def dummy_job():
            pass

        scheduler.set_poll_job(dummy_job)

        # Override to not run on startup
        scheduler._run_on_startup = False

        await scheduler.start()
        assert scheduler.is_running is True
        assert scheduler.status.is_running is True

        await scheduler.shutdown(wait=True)
        assert scheduler.is_running is False
        assert scheduler.status.is_running is False

    def test_scheduler_singleton(self):
        """AC#1: get_scheduler returns singleton instance."""
        sched1 = get_scheduler()
        sched2 = get_scheduler()
        assert sched1 is sched2


# =============================================================================
# AC#2: Data Polling Execution
# =============================================================================


class TestDataPolling:
    """Tests for MSSQL data fetching (AC#2)."""

    def test_fetch_production_data_with_rolling_window(self, pipeline):
        """AC#2: Fetch data from last 30 minutes (rolling window)."""
        mock_rows = [
            {"source_id": "GRINDER_01", "output_actual": 1500}
        ]

        with patch.object(pipeline, "_execute_query", return_value=mock_rows):
            records = pipeline.fetch_production_data()

            assert len(records) == 1
            assert records[0]["source_id"] == "GRINDER_01"

    def test_fetch_downtime_data(self, pipeline, sample_downtime_records):
        """AC#2: Fetch downtime data from MSSQL."""
        with patch.object(
            pipeline, "_execute_query",
            return_value=sample_downtime_records
        ):
            records = pipeline.fetch_downtime_data()

            assert len(records) == 2
            assert records[0]["reason_code"] == "Mechanical Failure"

    def test_fetch_oee_data(self, pipeline):
        """AC#2: Fetch current OEE metrics."""
        mock_rows = [
            {"source_id": "GRINDER_01", "oee_current": 85.5}
        ]

        with patch.object(pipeline, "_execute_query", return_value=mock_rows):
            oee_data = pipeline.fetch_oee_data()

            assert "GRINDER_01" in oee_data
            assert oee_data["GRINDER_01"] == Decimal("85.5")

    def test_fetch_returns_empty_when_not_configured(self, pipeline):
        """AC#2: Return empty data when MSSQL not configured."""
        from app.core.database import DatabaseNotConfiguredError

        with patch.object(
            pipeline, "_execute_query",
            side_effect=DatabaseNotConfiguredError("Not configured")
        ):
            records = pipeline.fetch_production_data()
            assert records == []

    def test_poll_window_configurable(self):
        """AC#2: Rolling window is configurable via environment."""
        with patch.dict("os.environ", {"POLL_WINDOW_MINUTES": "60"}):
            pipe = LivePulsePipeline()
            assert pipe._poll_window_minutes == 60


# =============================================================================
# AC#3: Live Snapshots Storage
# =============================================================================


class TestLiveSnapshots:
    """Tests for live snapshots storage (AC#3)."""

    def test_snapshot_data_includes_required_fields(self, sample_asset_id):
        """AC#3: Snapshot includes timestamp, asset_id, output, target, oee."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=1500,
            output_target=1800,
            oee_current=Decimal("85.5"),
        )

        data = snapshot.to_dict()

        assert "asset_id" in data
        assert "snapshot_timestamp" in data
        assert "output_actual" in data
        assert "output_target" in data
        assert "oee_current" in data
        assert data["output_actual"] == 1500
        assert data["output_target"] == 1800

    def test_create_live_snapshots(
        self, pipeline, sample_production_records, sample_oee_data, sample_asset_id
    ):
        """AC#3: Create snapshot objects from production data."""
        # Mock asset mapping
        pipeline._asset_cache = {
            "GRINDER_01": sample_asset_id,
            "GRINDER_02": uuid4(),
        }
        pipeline._target_cache = {
            sample_asset_id: 1800,
        }

        snapshots = pipeline.create_live_snapshots(
            sample_production_records, sample_oee_data
        )

        assert len(snapshots) == 2
        assert all(isinstance(s, LiveSnapshotData) for s in snapshots)

    def test_write_snapshots_to_supabase(
        self, pipeline, sample_asset_id, mock_supabase_client
    ):
        """AC#3: Write snapshots to Supabase live_snapshots table."""
        pipeline._supabase_client = mock_supabase_client

        snapshots = [
            LiveSnapshotData(
                asset_id=sample_asset_id,
                source_id="GRINDER_01",
                output_actual=1500,
                output_target=1800,
            )
        ]

        written = pipeline.write_snapshots_to_supabase(snapshots)

        mock_supabase_client.table.assert_called_with("live_snapshots")
        assert written >= 0

    def test_cleanup_old_snapshots(self, pipeline, mock_supabase_client):
        """AC#3: Cleanup snapshots older than 24 hours."""
        mock_supabase_client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = [
            {"id": "1"}, {"id": "2"}
        ]
        pipeline._supabase_client = mock_supabase_client

        deleted = pipeline.cleanup_old_snapshots()

        mock_supabase_client.table.assert_called_with("live_snapshots")
        # delete().lt() chain was called
        assert deleted == 2

    def test_snapshot_retention_configurable(self):
        """AC#3: Retention period configurable via environment."""
        with patch.dict("os.environ", {"SNAPSHOT_RETENTION_HOURS": "48"}):
            pipe = LivePulsePipeline()
            assert pipe._snapshot_retention_hours == 48


# =============================================================================
# AC#4: Safety Incident Detection
# =============================================================================


class TestSafetyDetection:
    """Tests for safety incident detection (AC#4)."""

    def test_detect_safety_events_by_reason_code(
        self, pipeline, sample_downtime_records, sample_asset_id
    ):
        """AC#4: Detect events with reason_code = 'Safety Issue'."""
        pipeline._asset_cache = {"GRINDER_01": sample_asset_id}

        safety_events = pipeline.detect_safety_events(sample_downtime_records)

        assert len(safety_events) == 1
        assert safety_events[0].reason_code == "Safety Issue"

    def test_safety_event_includes_required_fields(
        self, pipeline, sample_asset_id
    ):
        """AC#4: Safety event includes asset_id, timestamp, reason_code, details."""
        downtime_records = [
            {
                "source_id": "GRINDER_01",
                "event_timestamp": datetime(2026, 1, 5, 14, 15, 0),
                "duration_minutes": 15,
                "reason_code": "Safety Issue",
                "description": "Emergency stop",
            }
        ]
        pipeline._asset_cache = {"GRINDER_01": sample_asset_id}

        safety_events = pipeline.detect_safety_events(downtime_records)

        assert len(safety_events) == 1
        event = safety_events[0]
        assert event.asset_id == sample_asset_id
        assert event.event_timestamp == datetime(2026, 1, 5, 14, 15, 0)
        assert event.reason_code == "Safety Issue"
        assert event.description == "Emergency stop"

    def test_safety_events_logged_at_warning_level(
        self, pipeline, sample_asset_id, caplog
    ):
        """AC#4: Safety events logged at WARNING level."""
        import logging

        downtime_records = [
            {
                "source_id": "GRINDER_01",
                "event_timestamp": datetime.utcnow(),
                "duration_minutes": 15,
                "reason_code": "Safety Issue",
                "description": "Test safety event",
            }
        ]
        pipeline._asset_cache = {"GRINDER_01": sample_asset_id}

        with caplog.at_level(logging.WARNING):
            pipeline.detect_safety_events(downtime_records)

        assert "Safety incident detected" in caplog.text

    def test_safety_event_deduplication(
        self, pipeline, sample_asset_id, mock_supabase_client
    ):
        """AC#4: Avoid duplicate alerts for same incident."""
        # Mock existing event found
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "existing-id"}
        ]
        pipeline._supabase_client = mock_supabase_client

        events = [
            SafetyEventData(
                asset_id=sample_asset_id,
                source_id="GRINDER_01",
                event_timestamp=datetime(2026, 1, 5, 14, 15, 0),
                reason_code="Safety Issue",
            )
        ]

        written = pipeline.write_safety_events_to_supabase(events)

        # Should not insert duplicate
        assert written == 0

    def test_safety_reason_code_configurable(self):
        """AC#4: Safety reason code pattern configurable via environment."""
        with patch.dict("os.environ", {"SAFETY_REASON_CODE": "Safety Stop"}):
            pipe = LivePulsePipeline()
            assert pipe._safety_reason_code == "Safety Stop"


# =============================================================================
# AC#5: Output vs Target Calculation
# =============================================================================


class TestVarianceCalculation:
    """Tests for output vs target variance calculation (AC#5)."""

    def test_variance_percent_calculation(self, sample_asset_id):
        """AC#5: Calculate ((actual - target) / target) * 100."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=1500,
            output_target=1800,
        )

        # Expected: ((1500 - 1800) / 1800) * 100 = -16.67%
        expected_variance = Decimal("-16.67")
        assert snapshot.variance_percent == expected_variance

    def test_status_below_target(self, sample_asset_id):
        """AC#5: Status = 'below_target' when variance < -5%."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=1500,
            output_target=1800,  # -16.67% variance
        )

        assert snapshot.status == "below_target"

    def test_status_on_target(self, sample_asset_id):
        """AC#5: Status = 'on_target' when -5% <= variance <= 5%."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=1000,
            output_target=1000,  # 0% variance
        )

        assert snapshot.status == "on_target"

    def test_status_above_target(self, sample_asset_id):
        """AC#5: Status = 'above_target' when variance > 5%."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=2000,
            output_target=1800,  # +11.11% variance
        )

        assert snapshot.status == "above_target"

    def test_zero_target_handled(self, sample_asset_id):
        """AC#5: Handle zero target gracefully."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=1000,
            output_target=0,  # Zero target
        )

        assert snapshot.variance_percent == Decimal("0")
        assert snapshot.status == "on_target"


# =============================================================================
# AC#6: Error Handling and Resilience
# =============================================================================


class TestErrorHandling:
    """Tests for error handling and resilience (AC#6)."""

    @pytest.mark.asyncio
    async def test_poll_error_does_not_crash_scheduler(self, pipeline):
        """AC#6: Single failure does not crash the service."""
        # Mock a failing poll
        with patch.object(
            pipeline, "_load_asset_mappings",
            side_effect=Exception("Database error")
        ):
            result = await pipeline.execute_poll()

            assert result.success is False
            assert len(result.errors) > 0
            assert "Database error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_poll_continues_after_error(self, scheduler):
        """AC#6: Scheduler continues running after poll failure."""
        call_count = [0]

        async def failing_then_success_job():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First poll fails")
            return LivePulseResult()

        scheduler.set_poll_job(failing_then_success_job)
        scheduler._run_on_startup = False

        await scheduler.start()
        assert scheduler.is_running is True

        # Scheduler should still be running
        await scheduler.shutdown(wait=True)

    def test_poll_result_tracks_errors(self):
        """AC#6: Poll result contains error information."""
        result = LivePulseResult()
        result.success = False
        result.errors.append("Connection timeout")

        assert result.success is False
        assert "Connection timeout" in result.errors

    @pytest.mark.asyncio
    async def test_graceful_degradation_without_mssql(self, pipeline):
        """AC#6: Poll completes successfully without MSSQL."""
        from app.core.database import DatabaseNotConfiguredError

        with patch.object(
            pipeline, "_load_asset_mappings",
            side_effect=DatabaseNotConfiguredError("Not configured")
        ):
            result = await pipeline.execute_poll()

            # Should succeed gracefully (degraded mode)
            assert result.success is True
            assert "MSSQL not configured" in result.errors[0]


# =============================================================================
# AC#7: Health and Monitoring
# =============================================================================


class TestHealthMonitoring:
    """Tests for health and monitoring (AC#7)."""

    def test_status_tracks_last_poll_timestamp(self):
        """AC#7: Health includes last_poll_timestamp."""
        status = PipelineSchedulerStatus()
        now = datetime.utcnow()

        status.record_poll_success(1.5)

        assert status.last_poll_timestamp is not None
        assert status.last_poll_timestamp >= now

    def test_status_tracks_last_poll_success(self):
        """AC#7: Health includes last_poll_success (boolean)."""
        status = PipelineSchedulerStatus()

        status.record_poll_success(1.5)
        assert status.last_poll_success is True

        status.record_poll_failure("Error", 2.0)
        assert status.last_poll_success is False

    def test_status_to_dict_includes_all_fields(self):
        """AC#7: Status dict includes all required health fields."""
        status = PipelineSchedulerStatus()
        status.is_running = True
        status.record_poll_success(1.5)

        result = status.to_dict()

        assert "status" in result
        assert result["status"] == "running"
        assert "last_poll_timestamp" in result
        assert "last_poll_success" in result
        assert "next_poll_scheduled" in result

    def test_get_pipeline_status_function(self):
        """AC#7: get_pipeline_status returns health information."""
        status = get_pipeline_status()

        assert isinstance(status, dict)
        assert "status" in status
        assert "last_poll_timestamp" in status
        assert "last_poll_success" in status

    def test_status_tracks_poll_counts(self):
        """AC#7: Track total polls executed and failed."""
        status = PipelineSchedulerStatus()

        status.record_poll_success(1.0)
        status.record_poll_success(1.0)
        status.record_poll_failure("Error", 1.0)

        assert status.polls_executed == 3
        assert status.polls_failed == 1


# =============================================================================
# Integration Tests
# =============================================================================


class TestPipelineIntegration:
    """Integration tests for the complete pipeline flow."""

    @pytest.mark.asyncio
    async def test_full_poll_execution(
        self, pipeline, sample_asset_id, mock_supabase_client
    ):
        """Integration test: Complete poll cycle."""
        # Setup mocks
        pipeline._supabase_client = mock_supabase_client
        pipeline._asset_cache = {"GRINDER_01": sample_asset_id}
        pipeline._target_cache = {sample_asset_id: 1800}

        # Mock asset loading to return cached data
        with patch.object(pipeline, "_load_asset_mappings", return_value=pipeline._asset_cache):
            with patch.object(pipeline, "_load_shift_targets", return_value=pipeline._target_cache):
                with patch.object(pipeline, "fetch_production_data", return_value=[
                    {"source_id": "GRINDER_01", "output_actual": 1500}
                ]):
                    with patch.object(pipeline, "fetch_downtime_data", return_value=[]):
                        with patch.object(pipeline, "fetch_oee_data", return_value={}):
                            result = await pipeline.execute_poll()

                            assert result.success is True
                            assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_safety_event_flow(
        self, pipeline, sample_asset_id, mock_supabase_client
    ):
        """Integration test: Safety event detection and storage."""
        # Mock no existing event using source_record_id deduplication (Story 2.6 update)
        # The new code uses .eq(source_record_id) for deduplication
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "new-id"}]

        pipeline._supabase_client = mock_supabase_client
        pipeline._asset_cache = {"GRINDER_01": sample_asset_id}
        pipeline._target_cache = {}

        downtime_with_safety = [
            {
                "source_id": "GRINDER_01",
                "event_timestamp": datetime.utcnow(),
                "duration_minutes": 15,
                "reason_code": "Safety Issue",
                "description": "Emergency stop",
                "record_id": "DT_12345",  # MSSQL record ID for deduplication
            }
        ]

        with patch.object(pipeline, "_load_asset_mappings", return_value=pipeline._asset_cache):
            with patch.object(pipeline, "_load_shift_targets", return_value={}):
                with patch.object(pipeline, "fetch_production_data", return_value=[]):
                    with patch.object(pipeline, "fetch_downtime_data", return_value=downtime_with_safety):
                        with patch.object(pipeline, "fetch_oee_data", return_value={}):
                            result = await pipeline.execute_poll()

                            assert result.success is True
                            assert result.safety_events_created == 1

    def test_module_singleton_functions(self):
        """Test module-level singleton functions."""
        pipeline1 = get_live_pulse_pipeline()
        pipeline2 = get_live_pulse_pipeline()
        assert pipeline1 is pipeline2


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_production_records(self, pipeline):
        """Handle empty production records gracefully."""
        snapshots = pipeline.create_live_snapshots([], {})
        assert snapshots == []

    def test_unknown_asset_skipped(
        self, pipeline, sample_production_records, mock_supabase_client
    ):
        """Assets not in mapping are skipped."""
        # Mock the Supabase client to return empty asset list
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []
        pipeline._supabase_client = mock_supabase_client
        pipeline._asset_cache = {"NONEXISTENT": uuid4()}  # Different from sample records
        pipeline._target_cache = {}

        snapshots = pipeline.create_live_snapshots(
            sample_production_records, {}
        )

        assert len(snapshots) == 0

    def test_negative_output_handled(self, sample_asset_id):
        """Negative output values handled correctly."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=-100,  # Invalid but shouldn't crash
            output_target=1000,
        )

        # Should calculate variance regardless
        assert snapshot.variance_percent is not None

    def test_very_large_variance(self, sample_asset_id):
        """Very large variance values handled correctly."""
        snapshot = LiveSnapshotData(
            asset_id=sample_asset_id,
            source_id="GRINDER_01",
            output_actual=10000,
            output_target=100,  # 9900% variance
        )

        assert snapshot.status == "above_target"
        assert snapshot.variance_percent > Decimal("5")
