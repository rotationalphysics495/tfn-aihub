"""
Morning Report Pipeline Orchestrator

Main entry point for the daily batch pipeline (Pipeline A).
Orchestrates data extraction, transformation, calculation, and storage.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #1 - Railway Cron Job Configuration
AC: #6 - Daily Summary Storage
AC: #7 - Safety Event Detection
AC: #8 - Pipeline Execution Logging
AC: #9 - Idempotency and Re-run Safety
"""

import logging
import os
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from uuid import UUID

from supabase import create_client, Client

from app.core.config import get_settings
from app.models.pipeline import (
    CleanedProductionData,
    DailySummaryCreate,
    ExtractedData,
    FinancialMetrics,
    OEEMetrics,
    PipelineExecutionLog,
    PipelineResult,
    PipelineStatus,
    RawDowntimeRecord,
    SafetyEventCreate,
    SeverityLevel,
)
from app.services.pipelines.data_extractor import DataExtractor, DataExtractionError
from app.services.pipelines.transformer import DataTransformer, TransformationError
from app.services.pipelines.calculator import Calculator, CalculationError

logger = logging.getLogger(__name__)


class MorningReportPipelineError(Exception):
    """Raised when the morning report pipeline fails."""
    pass


class MorningReportPipeline:
    """
    Orchestrates the Morning Report batch pipeline.

    Pipeline Flow:
        1. Extract T-1 data from MSSQL
        2. Transform and cleanse data
        3. Calculate OEE and financial metrics
        4. Detect safety events
        5. Store results in Supabase (daily_summaries, safety_events)
        6. Log execution details

    Features:
        - Idempotent execution (upsert pattern)
        - Graceful error handling with partial completion
        - Detailed execution logging
        - Re-run safety (no duplicate records)
    """

    def __init__(
        self,
        extractor: Optional[DataExtractor] = None,
        transformer: Optional[DataTransformer] = None,
        calculator_instance: Optional[Calculator] = None,
    ):
        """
        Initialize the pipeline with optional dependency injection.

        Args:
            extractor: DataExtractor instance (creates new if None)
            transformer: DataTransformer instance (creates new if None)
            calculator_instance: Calculator instance (creates new if None)
        """
        self.extractor = extractor or DataExtractor()
        self.transformer = transformer or DataTransformer()
        self.calculator = calculator_instance or Calculator()
        self._supabase_client: Optional[Client] = None
        self._execution_logs: List[PipelineExecutionLog] = []

    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client."""
        if self._supabase_client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise MorningReportPipelineError("Supabase not configured")
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._supabase_client

    def _create_execution_log(
        self,
        target_date: date,
        status: PipelineStatus = PipelineStatus.PENDING
    ) -> PipelineExecutionLog:
        """Create a new execution log entry."""
        return PipelineExecutionLog(
            pipeline_name="morning_report",
            target_date=target_date,
            status=status,
            started_at=datetime.utcnow(),
        )

    def _finalize_execution_log(
        self,
        log: PipelineExecutionLog,
        status: PipelineStatus,
        error_message: Optional[str] = None
    ) -> PipelineExecutionLog:
        """Finalize execution log with end time and duration."""
        log.status = status
        log.completed_at = datetime.utcnow()
        log.duration_seconds = (log.completed_at - log.started_at).total_seconds()
        if error_message:
            log.errors.append(error_message)
        return log

    def upsert_daily_summary(
        self,
        data: CleanedProductionData,
        oee: OEEMetrics,
        financial: FinancialMetrics
    ) -> bool:
        """
        Upsert a daily summary record to Supabase.

        Uses ON CONFLICT UPDATE pattern for idempotency.

        Args:
            data: Cleaned production data
            oee: Calculated OEE metrics
            financial: Calculated financial metrics

        Returns:
            True if upsert succeeded, False otherwise
        """
        try:
            client = self._get_supabase_client()

            # Convert OEE decimal to percentage (0-100)
            oee_percentage = (oee.oee_overall * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Build summary data
            # Note: Column names aligned with existing summaries.py model
            summary_data = {
                "asset_id": str(data.asset_id),
                "date": data.production_date.isoformat(),
                "oee": float(oee_percentage),
                "waste": float(data.units_scrapped),
                "financial_loss": float(financial.total_financial_loss_dollars),
                "actual_output": data.units_produced,
                "target_output": data.planned_units,
                "downtime_minutes": data.total_downtime_minutes,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Upsert: insert or update on conflict (asset_id, date)
            response = client.table("daily_summaries").upsert(
                summary_data,
                on_conflict="asset_id,date"
            ).execute()

            logger.debug(f"Upserted daily summary for asset {data.asset_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert daily summary: {e}")
            return False

    def create_safety_event(
        self,
        downtime: RawDowntimeRecord,
        asset_id: UUID
    ) -> bool:
        """
        Create a safety event record in Supabase.

        Args:
            downtime: Downtime record with safety issue
            asset_id: UUID of the asset

        Returns:
            True if creation succeeded, False otherwise
        """
        try:
            client = self._get_supabase_client()

            # Build safety event data per AC#7: includes duration_minutes, severity='critical'
            event_data = {
                "asset_id": str(asset_id),
                "occurred_at": downtime.event_timestamp.isoformat(),
                "duration_minutes": downtime.duration_minutes,
                "reason_code": downtime.reason_code or "Safety Issue",
                "severity": SeverityLevel.CRITICAL.value,
                "description": downtime.description,
            }

            # Check if event already exists (idempotency)
            existing = client.table("safety_events").select("id").eq(
                "asset_id", str(asset_id)
            ).eq(
                "occurred_at", downtime.event_timestamp.isoformat()
            ).execute()

            if existing.data:
                logger.debug(f"Safety event already exists for asset {asset_id}")
                return True

            # Insert new event
            response = client.table("safety_events").insert(event_data).execute()

            logger.info(
                f"Created safety event for asset {asset_id}: {downtime.reason_code}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create safety event: {e}")
            return False

    async def run(
        self,
        target_date: Optional[date] = None,
        force: bool = False
    ) -> PipelineResult:
        """
        Execute the morning report pipeline.

        Args:
            target_date: Date to process. Defaults to yesterday (T-1).
            force: If True, re-run even if data already exists.

        Returns:
            PipelineResult with execution details

        Raises:
            MorningReportPipelineError: If pipeline fails completely
        """
        # Default to yesterday (T-1)
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        logger.info(f"Starting Morning Report pipeline for {target_date}")

        # Create execution log
        execution_log = self._create_execution_log(target_date, PipelineStatus.RUNNING)

        summaries_created = 0
        summaries_updated = 0
        safety_events_created = 0

        try:
            # Step 1: Extract data from MSSQL
            logger.info("Step 1: Extracting data from MSSQL")
            extracted_data = self.extractor.extract_all(target_date)

            total_extracted = (
                len(extracted_data.production_records) +
                len(extracted_data.downtime_records) +
                len(extracted_data.quality_records) +
                len(extracted_data.labor_records)
            )
            execution_log.records_processed = total_extracted

            if total_extracted == 0:
                logger.warning(f"No data extracted for {target_date}")
                execution_log = self._finalize_execution_log(
                    execution_log,
                    PipelineStatus.SUCCESS,
                    "No data to process"
                )
                return PipelineResult(
                    status=PipelineStatus.SUCCESS,
                    execution_log=execution_log,
                    summaries_created=0,
                    summaries_updated=0,
                    safety_events_created=0,
                )

            # Step 2: Transform data
            logger.info("Step 2: Transforming and cleansing data")
            cleaned_data = self.transformer.transform(extracted_data)

            # Step 3: Detect safety events
            logger.info("Step 3: Detecting safety events")
            safety_downtime = self.transformer.detect_safety_events(
                extracted_data.downtime_records
            )

            # Step 4: Calculate metrics
            logger.info("Step 4: Calculating OEE and financial metrics")
            calculated = self.calculator.calculate_all(cleaned_data)

            # Step 5: Store daily summaries
            logger.info("Step 5: Storing daily summaries")
            for data, oee, financial in calculated:
                success = self.upsert_daily_summary(data, oee, financial)
                if success:
                    summaries_updated += 1  # Upsert counts as update
                    execution_log.assets_processed.append(str(data.asset_id))
                else:
                    execution_log.records_failed += 1

            # Step 6: Create safety events
            logger.info("Step 6: Creating safety events")
            for downtime in safety_downtime:
                # Get asset_id for this source_id
                asset_id = self.transformer.get_asset_id(downtime.source_id)
                if asset_id:
                    success = self.create_safety_event(downtime, asset_id)
                    if success:
                        safety_events_created += 1
                else:
                    logger.warning(
                        f"Cannot create safety event: no asset for {downtime.source_id}"
                    )

            # Finalize
            execution_log = self._finalize_execution_log(
                execution_log,
                PipelineStatus.SUCCESS
            )

            self._execution_logs.append(execution_log)

            logger.info(
                f"Morning Report pipeline completed: "
                f"{summaries_updated} summaries, {safety_events_created} safety events"
            )

            return PipelineResult(
                status=PipelineStatus.SUCCESS,
                execution_log=execution_log,
                summaries_created=0,  # Using upsert, so all are "updated"
                summaries_updated=summaries_updated,
                safety_events_created=safety_events_created,
            )

        except DataExtractionError as e:
            error_msg = f"Data extraction failed: {e}"
            logger.error(error_msg)
            execution_log = self._finalize_execution_log(
                execution_log,
                PipelineStatus.FAILED,
                error_msg
            )
            self._execution_logs.append(execution_log)
            return PipelineResult(
                status=PipelineStatus.FAILED,
                execution_log=execution_log,
                error_message=error_msg,
            )

        except TransformationError as e:
            error_msg = f"Data transformation failed: {e}"
            logger.error(error_msg)
            execution_log = self._finalize_execution_log(
                execution_log,
                PipelineStatus.FAILED,
                error_msg
            )
            self._execution_logs.append(execution_log)
            return PipelineResult(
                status=PipelineStatus.FAILED,
                execution_log=execution_log,
                error_message=error_msg,
            )

        except CalculationError as e:
            error_msg = f"Calculation failed: {e}"
            logger.error(error_msg)
            execution_log = self._finalize_execution_log(
                execution_log,
                PipelineStatus.PARTIAL,
                error_msg
            )
            self._execution_logs.append(execution_log)
            return PipelineResult(
                status=PipelineStatus.PARTIAL,
                execution_log=execution_log,
                summaries_updated=summaries_updated,
                safety_events_created=safety_events_created,
                error_message=error_msg,
            )

        except Exception as e:
            error_msg = f"Pipeline failed unexpectedly: {e}"
            logger.exception(error_msg)
            execution_log = self._finalize_execution_log(
                execution_log,
                PipelineStatus.FAILED,
                error_msg
            )
            self._execution_logs.append(execution_log)
            return PipelineResult(
                status=PipelineStatus.FAILED,
                execution_log=execution_log,
                error_message=error_msg,
            )

    def get_last_execution(self) -> Optional[PipelineExecutionLog]:
        """Get the most recent execution log."""
        if self._execution_logs:
            return self._execution_logs[-1]
        return None

    def get_execution_logs(self, limit: int = 10) -> List[PipelineExecutionLog]:
        """Get recent execution logs."""
        return self._execution_logs[-limit:]


# Module-level singleton
_pipeline_instance: Optional[MorningReportPipeline] = None


def get_pipeline() -> MorningReportPipeline:
    """Get or create the singleton pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MorningReportPipeline()
    return _pipeline_instance


async def run_morning_report(
    target_date: Optional[date] = None,
    force: bool = False,
    generate_smart_summary: bool = True,
) -> PipelineResult:
    """
    Convenience function to run the morning report pipeline.

    Story 3.5 AC#9: Triggers Smart Summary generation after pipeline success.

    Args:
        target_date: Date to process. Defaults to yesterday (T-1).
        force: If True, re-run even if data already exists.
        generate_smart_summary: If True, trigger smart summary after pipeline.

    Returns:
        PipelineResult with execution details
    """
    pipeline = get_pipeline()
    result = await pipeline.run(target_date, force)

    # AC#9: Trigger Smart Summary generation after pipeline success
    if generate_smart_summary and result.status in (
        PipelineStatus.SUCCESS,
        PipelineStatus.PARTIAL
    ):
        await _trigger_smart_summary_generation(
            target_date or (date.today() - timedelta(days=1))
        )

    return result


async def _trigger_smart_summary_generation(target_date: date) -> None:
    """
    Trigger Smart Summary generation after pipeline completion.

    Story 3.5 AC#9:
    - Smart Summary generation is triggered automatically after pipeline success
    - Handle pipeline failures gracefully (don't block on summary)
    - Summary is available before 06:30 AM

    Args:
        target_date: Date to generate summary for
    """
    try:
        from app.services.ai.smart_summary import get_smart_summary_service

        logger.info(f"Triggering Smart Summary generation for {target_date}")

        service = get_smart_summary_service()

        # Invalidate any existing cache to ensure fresh data is used
        await service.invalidate_cache(target_date)

        # Generate new summary
        summary = await service.generate_smart_summary(
            target_date=target_date,
            regenerate=True,  # Force fresh generation with new pipeline data
        )

        if summary.is_fallback:
            logger.warning(
                f"Smart Summary generated with fallback for {target_date}"
            )
        else:
            logger.info(
                f"Smart Summary generated successfully for {target_date} "
                f"in {summary.generation_duration_ms}ms"
            )

    except Exception as e:
        # AC#9: Handle failures gracefully - don't block pipeline on summary errors
        logger.error(
            f"Smart Summary generation failed for {target_date}: {e}. "
            f"Pipeline result is not affected."
        )


# CLI entry point for Railway Cron
if __name__ == "__main__":
    import asyncio
    import sys

    # Configure logging
    logging.basicConfig(
        level=os.getenv("PIPELINE_LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def main():
        """CLI entry point for cron job."""
        logger.info("Morning Report Pipeline - Cron Entry Point")

        # Parse optional date argument
        target_date = None
        if len(sys.argv) > 1:
            try:
                target_date = date.fromisoformat(sys.argv[1])
                logger.info(f"Using provided date: {target_date}")
            except ValueError:
                logger.error(f"Invalid date format: {sys.argv[1]}")
                sys.exit(1)

        # Run pipeline
        result = await run_morning_report(target_date)

        # Log result
        if result.status == PipelineStatus.SUCCESS:
            logger.info(
                f"Pipeline completed successfully: "
                f"{result.summaries_updated} summaries, "
                f"{result.safety_events_created} safety events"
            )
            sys.exit(0)
        elif result.status == PipelineStatus.PARTIAL:
            logger.warning(f"Pipeline completed with errors: {result.error_message}")
            sys.exit(0)  # Partial success is still success
        else:
            logger.error(f"Pipeline failed: {result.error_message}")
            sys.exit(1)

    asyncio.run(main())
