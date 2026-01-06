"""
Integration Tests for Morning Report Pipeline.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #6 - Daily Summary Storage
AC: #8 - Pipeline Execution Logging
AC: #9 - Idempotency and Re-run Safety
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.pipelines.morning_report import (
    MorningReportPipeline,
    run_morning_report,
    get_pipeline,
)
from app.services.pipelines.data_extractor import DataExtractor
from app.services.pipelines.transformer import DataTransformer
from app.services.pipelines.calculator import Calculator
from app.models.pipeline import (
    ExtractedData,
    RawProductionRecord,
    RawDowntimeRecord,
    RawQualityRecord,
    PipelineStatus,
    CleanedProductionData,
    OEEMetrics,
    FinancialMetrics,
)


@pytest.fixture
def mock_extractor():
    """Create mock extractor."""
    extractor = MagicMock(spec=DataExtractor)
    return extractor


@pytest.fixture
def mock_transformer():
    """Create mock transformer."""
    transformer = MagicMock(spec=DataTransformer)
    return transformer


@pytest.fixture
def mock_calculator():
    """Create mock calculator."""
    calc = MagicMock(spec=Calculator)
    return calc


@pytest.fixture
def sample_extracted_data():
    """Create sample extracted data."""
    return ExtractedData(
        target_date=date(2026, 1, 5),
        production_records=[
            RawProductionRecord(
                source_id="GRINDER_01",
                production_date=date(2026, 1, 5),
                units_produced=1500,
                units_scrapped=25,
                planned_units=1800,
            ),
        ],
        downtime_records=[
            RawDowntimeRecord(
                source_id="GRINDER_01",
                event_timestamp=datetime(2026, 1, 5, 14, 30, 0),
                duration_minutes=45,
                reason_code="Mechanical Failure",
            ),
        ],
        quality_records=[
            RawQualityRecord(
                source_id="GRINDER_01",
                production_date=date(2026, 1, 5),
                good_units=1475,
                total_units=1500,
                scrap_units=25,
            ),
        ],
        labor_records=[],
    )


@pytest.fixture
def sample_cleaned_data():
    """Create sample cleaned data."""
    return [
        CleanedProductionData(
            asset_id=uuid4(),
            source_id="GRINDER_01",
            production_date=date(2026, 1, 5),
            units_produced=1500,
            units_scrapped=25,
            planned_units=1800,
            good_units=1475,
            total_units=1500,
            total_downtime_minutes=45,
            has_production_data=True,
        ),
    ]


class TestPipelineOrchestration:
    """Tests for pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_pipeline_full_execution(
        self,
        mock_extractor,
        mock_transformer,
        mock_calculator,
        sample_extracted_data,
        sample_cleaned_data,
    ):
        """AC#6, AC#8: Full pipeline execution flow."""
        # Setup mocks
        mock_extractor.extract_all.return_value = sample_extracted_data
        mock_transformer.transform.return_value = sample_cleaned_data
        mock_transformer.detect_safety_events.return_value = []
        mock_transformer.get_asset_id.return_value = sample_cleaned_data[0].asset_id

        oee = OEEMetrics(
            availability=Decimal("0.9"),
            performance=Decimal("0.85"),
            quality=Decimal("0.98"),
            oee_overall=Decimal("0.75"),
        )
        financial = FinancialMetrics(
            downtime_cost_dollars=Decimal("225.00"),
            waste_cost_dollars=Decimal("125.00"),
            total_financial_loss_dollars=Decimal("350.00"),
        )
        mock_calculator.calculate_all.return_value = [
            (sample_cleaned_data[0], oee, financial)
        ]

        # Create pipeline with mocks
        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
            calculator_instance=mock_calculator,
        )

        # Mock Supabase upsert
        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        pipeline._supabase_client = mock_client

        # Execute pipeline
        result = await pipeline.run(date(2026, 1, 5))

        # Verify
        assert result.status == PipelineStatus.SUCCESS
        assert result.summaries_updated == 1
        assert result.execution_log.records_processed > 0
        mock_extractor.extract_all.assert_called_once()
        mock_transformer.transform.assert_called_once()
        mock_calculator.calculate_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_default_date_is_yesterday(
        self,
        mock_extractor,
        mock_transformer,
        mock_calculator,
    ):
        """AC#1: Pipeline defaults to T-1 (yesterday)."""
        mock_extractor.extract_all.return_value = ExtractedData(
            target_date=date.today() - timedelta(days=1),
            production_records=[],
            downtime_records=[],
            quality_records=[],
            labor_records=[],
        )
        mock_transformer.transform.return_value = []
        mock_transformer.detect_safety_events.return_value = []

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
            calculator_instance=mock_calculator,
        )

        result = await pipeline.run()  # No date specified

        yesterday = date.today() - timedelta(days=1)
        mock_extractor.extract_all.assert_called_once_with(yesterday)
        assert result.execution_log.target_date == yesterday


class TestIdempotency:
    """Tests for idempotent execution (AC#9)."""

    @pytest.mark.asyncio
    async def test_upsert_pattern_no_duplicates(
        self,
        mock_extractor,
        mock_transformer,
        mock_calculator,
        sample_extracted_data,
        sample_cleaned_data,
    ):
        """AC#9: Upsert pattern prevents duplicate records."""
        mock_extractor.extract_all.return_value = sample_extracted_data
        mock_transformer.transform.return_value = sample_cleaned_data
        mock_transformer.detect_safety_events.return_value = []

        oee = OEEMetrics()
        financial = FinancialMetrics()
        mock_calculator.calculate_all.return_value = [
            (sample_cleaned_data[0], oee, financial)
        ]

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
            calculator_instance=mock_calculator,
        )

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        pipeline._supabase_client = mock_client

        # Run twice for same date
        await pipeline.run(date(2026, 1, 5))
        await pipeline.run(date(2026, 1, 5))

        # Verify upsert was called with on_conflict parameter
        upsert_calls = mock_client.table.return_value.upsert.call_args_list
        assert len(upsert_calls) == 2  # Called twice
        # Each call should use on_conflict for idempotency
        for call in upsert_calls:
            assert "on_conflict" in call.kwargs

    @pytest.mark.asyncio
    async def test_rerun_produces_same_result(
        self,
        mock_extractor,
        mock_transformer,
        mock_calculator,
        sample_extracted_data,
        sample_cleaned_data,
    ):
        """AC#9: Re-running produces identical results."""
        mock_extractor.extract_all.return_value = sample_extracted_data
        mock_transformer.transform.return_value = sample_cleaned_data
        mock_transformer.detect_safety_events.return_value = []

        oee = OEEMetrics(oee_overall=Decimal("0.75"))
        financial = FinancialMetrics(total_financial_loss_dollars=Decimal("350"))
        mock_calculator.calculate_all.return_value = [
            (sample_cleaned_data[0], oee, financial)
        ]

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
            calculator_instance=mock_calculator,
        )

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        pipeline._supabase_client = mock_client

        result1 = await pipeline.run(date(2026, 1, 5))
        result2 = await pipeline.run(date(2026, 1, 5))

        # Same results on re-run
        assert result1.summaries_updated == result2.summaries_updated


class TestExecutionLogging:
    """Tests for pipeline execution logging (AC#8)."""

    @pytest.mark.asyncio
    async def test_execution_log_recorded(
        self,
        mock_extractor,
        mock_transformer,
        mock_calculator,
        sample_extracted_data,
        sample_cleaned_data,
    ):
        """AC#8: Execution log is recorded with details."""
        mock_extractor.extract_all.return_value = sample_extracted_data
        mock_transformer.transform.return_value = sample_cleaned_data
        mock_transformer.detect_safety_events.return_value = []
        mock_calculator.calculate_all.return_value = []

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
            calculator_instance=mock_calculator,
        )

        result = await pipeline.run(date(2026, 1, 5))

        log = result.execution_log
        assert log.pipeline_name == "morning_report"
        assert log.target_date == date(2026, 1, 5)
        assert log.started_at is not None
        assert log.completed_at is not None
        assert log.duration_seconds is not None
        assert log.records_processed >= 0

    @pytest.mark.asyncio
    async def test_execution_log_accessible_via_api(
        self,
        mock_extractor,
        mock_transformer,
        mock_calculator,
        sample_extracted_data,
    ):
        """AC#8: Logs accessible via API."""
        mock_extractor.extract_all.return_value = sample_extracted_data
        mock_transformer.transform.return_value = []
        mock_transformer.detect_safety_events.return_value = []

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
            calculator_instance=mock_calculator,
        )

        await pipeline.run(date(2026, 1, 5))

        # Verify logs can be retrieved
        last_run = pipeline.get_last_execution()
        all_logs = pipeline.get_execution_logs(limit=10)

        assert last_run is not None
        assert len(all_logs) >= 1


class TestSafetyEventCreation:
    """Tests for safety event creation (AC#7)."""

    @pytest.mark.asyncio
    async def test_safety_event_created(
        self,
        mock_extractor,
        mock_transformer,
        mock_calculator,
    ):
        """AC#7: Safety events are created for safety-related downtime."""
        asset_id = uuid4()

        # Safety downtime record
        safety_downtime = RawDowntimeRecord(
            source_id="GRINDER_01",
            event_timestamp=datetime(2026, 1, 5, 10, 0, 0),
            duration_minutes=30,
            reason_code="Safety Issue",
            description="Emergency stop activated",
        )

        mock_extractor.extract_all.return_value = ExtractedData(
            target_date=date(2026, 1, 5),
            production_records=[],
            downtime_records=[safety_downtime],
            quality_records=[],
            labor_records=[],
        )
        mock_transformer.transform.return_value = []
        mock_transformer.detect_safety_events.return_value = [safety_downtime]
        mock_transformer.get_asset_id.return_value = asset_id

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
            calculator_instance=mock_calculator,
        )

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
        pipeline._supabase_client = mock_client

        result = await pipeline.run(date(2026, 1, 5))

        # Verify safety event was created
        assert result.safety_events_created == 1


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_extraction_failure_handled(self, mock_extractor):
        """AC#8: Extraction failure is logged and pipeline returns failed status."""
        from app.services.pipelines.data_extractor import DataExtractionError

        mock_extractor.extract_all.side_effect = DataExtractionError("DB connection failed")

        pipeline = MorningReportPipeline(extractor=mock_extractor)

        result = await pipeline.run(date(2026, 1, 5))

        assert result.status == PipelineStatus.FAILED
        assert "extraction" in result.error_message.lower()
        assert len(result.execution_log.errors) > 0

    @pytest.mark.asyncio
    async def test_transformation_failure_handled(
        self,
        mock_extractor,
        mock_transformer,
        sample_extracted_data,
    ):
        """AC#8: Transformation failure is logged and handled."""
        from app.services.pipelines.transformer import TransformationError

        mock_extractor.extract_all.return_value = sample_extracted_data
        mock_transformer.transform.side_effect = TransformationError("Asset mapping failed")

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
        )

        result = await pipeline.run(date(2026, 1, 5))

        assert result.status == PipelineStatus.FAILED
        assert "transformation" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_no_data_succeeds(self, mock_extractor, mock_transformer):
        """Handle case where no data exists for target date."""
        mock_extractor.extract_all.return_value = ExtractedData(
            target_date=date(2026, 1, 5),
            production_records=[],
            downtime_records=[],
            quality_records=[],
            labor_records=[],
        )

        pipeline = MorningReportPipeline(
            extractor=mock_extractor,
            transformer=mock_transformer,
        )

        result = await pipeline.run(date(2026, 1, 5))

        # Should succeed with 0 records
        assert result.status == PipelineStatus.SUCCESS
        assert result.summaries_updated == 0


class TestDailySummaryStorage:
    """Tests for daily summary storage (AC#6)."""

    def test_upsert_daily_summary(self, sample_cleaned_data):
        """AC#6: Daily summary is upserted correctly."""
        pipeline = MorningReportPipeline()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        pipeline._supabase_client = mock_client

        oee = OEEMetrics(
            availability=Decimal("0.9"),
            performance=Decimal("0.85"),
            quality=Decimal("0.98"),
            oee_overall=Decimal("0.75"),
        )
        financial = FinancialMetrics(
            downtime_cost_dollars=Decimal("225.00"),
            waste_cost_dollars=Decimal("125.00"),
            total_financial_loss_dollars=Decimal("350.00"),
            downtime_minutes=45,
        )

        result = pipeline.upsert_daily_summary(sample_cleaned_data[0], oee, financial)

        assert result is True
        # Verify upsert was called with correct data
        mock_client.table.assert_called_with("daily_summaries")
        upsert_call = mock_client.table.return_value.upsert.call_args
        data = upsert_call[0][0]  # First positional arg

        # Note: Column names aligned with existing summaries.py model
        assert data["oee"] == 75.0  # 0.75 * 100
        assert data["actual_output"] == 1500
        assert data["downtime_minutes"] == 45
        assert data["financial_loss"] == 350.0


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_pipeline_singleton(self):
        """Verify get_pipeline returns singleton."""
        pipeline1 = get_pipeline()
        pipeline2 = get_pipeline()

        assert pipeline1 is pipeline2

    @pytest.mark.asyncio
    async def test_run_morning_report_convenience(self):
        """Test convenience function."""
        with patch("app.services.pipelines.morning_report.get_pipeline") as mock_get:
            mock_pipeline = MagicMock()
            mock_pipeline.run = AsyncMock()
            mock_get.return_value = mock_pipeline

            await run_morning_report(date(2026, 1, 5), force=True)

            mock_pipeline.run.assert_called_once_with(date(2026, 1, 5), True)
