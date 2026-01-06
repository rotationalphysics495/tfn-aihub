"""
Live Pulse Pipeline

Pipeline B: Real-time polling pipeline that fetches live production data
every 15 minutes from MSSQL and writes snapshots to Supabase.

Story: 2.2 - Polling Data Pipeline (T-15m)
AC: #2 - Data Polling Execution
AC: #3 - Live Snapshots Storage
AC: #4 - Safety Incident Detection
AC: #5 - Output vs Target Calculation
AC: #6 - Error Handling and Resilience
"""

import logging
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from supabase import create_client, Client
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.core.config import get_settings
from app.core.database import mssql_db, DatabaseError, DatabaseNotConfiguredError
from app.services.scheduler import get_scheduler

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models for Live Pulse
# =============================================================================


class LiveSnapshotData:
    """Container for live snapshot data to write to Supabase."""

    def __init__(
        self,
        asset_id: UUID,
        source_id: str,
        output_actual: int,
        output_target: int,
        oee_current: Optional[Decimal] = None,
    ):
        self.asset_id = asset_id
        self.source_id = source_id
        self.output_actual = output_actual
        self.output_target = output_target
        self.oee_current = oee_current
        self.snapshot_timestamp = datetime.utcnow()

        # Calculate variance
        if output_target > 0:
            variance = ((output_actual - output_target) / output_target) * 100
            self.variance_percent = Decimal(str(variance)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            self.variance_percent = Decimal("0")

        # Determine status based on variance threshold (+/- 5%)
        if self.variance_percent >= Decimal("5"):
            self.status = "above_target"
        elif self.variance_percent <= Decimal("-5"):
            self.status = "below_target"
        else:
            self.status = "on_target"

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase insertion."""
        return {
            "asset_id": str(self.asset_id),
            "snapshot_timestamp": self.snapshot_timestamp.isoformat(),
            "output_actual": self.output_actual,
            "output_target": self.output_target,
            "variance_percent": float(self.variance_percent),
            "status": self.status,
            "oee_current": float(self.oee_current) if self.oee_current else None,
        }


class SafetyEventData:
    """Container for safety event data to write to Supabase."""

    def __init__(
        self,
        asset_id: UUID,
        source_id: str,
        event_timestamp: datetime,
        reason_code: str,
        description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        source_record_id: Optional[str] = None,
    ):
        self.asset_id = asset_id
        self.source_id = source_id
        self.event_timestamp = event_timestamp
        self.reason_code = reason_code
        self.description = description
        self.duration_minutes = duration_minutes
        self.source_record_id = source_record_id

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase insertion."""
        data = {
            "asset_id": str(self.asset_id),
            "event_timestamp": self.event_timestamp.isoformat(),
            "occurred_at": self.event_timestamp.isoformat(),
            "reason_code": self.reason_code,
            "severity": "critical",  # Safety issues are always critical
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "is_resolved": False,  # New safety events start unacknowledged
        }
        if self.source_record_id:
            data["source_record_id"] = self.source_record_id
        return data


class LivePulseResult:
    """Result of a live pulse poll execution."""

    def __init__(self):
        self.success: bool = True
        self.snapshots_created: int = 0
        self.safety_events_created: int = 0
        self.errors: List[str] = []
        self.duration_seconds: float = 0.0
        self.poll_timestamp: datetime = datetime.utcnow()


# =============================================================================
# Live Pulse Pipeline
# =============================================================================


class LivePulsePipeline:
    """
    Live Pulse polling pipeline.

    Fetches production data from MSSQL every 15 minutes, detects safety
    incidents, calculates output vs target variance, and stores snapshots
    in Supabase.

    Pipeline Flow:
        1. Fetch 30-minute rolling window data from MSSQL
        2. Detect safety events (reason_code = 'Safety Issue')
        3. Calculate output vs target variance
        4. Write live snapshots to Supabase
        5. Cleanup old snapshots (24h retention)
    """

    def __init__(self):
        self._supabase_client: Optional[Client] = None
        self._asset_cache: Dict[str, UUID] = {}
        self._target_cache: Dict[UUID, int] = {}

        # Configuration from environment
        self._poll_window_minutes: int = int(
            os.getenv("POLL_WINDOW_MINUTES", "30")
        )
        self._snapshot_retention_hours: int = int(
            os.getenv("SNAPSHOT_RETENTION_HOURS", "24")
        )
        self._poll_timeout_seconds: int = int(
            os.getenv("POLL_TIMEOUT_SECONDS", "60")
        )
        self._safety_reason_code: str = os.getenv(
            "SAFETY_REASON_CODE", "Safety Issue"
        )

    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client."""
        if self._supabase_client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError("Supabase not configured")
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._supabase_client

    def _load_asset_mappings(self) -> Dict[str, UUID]:
        """Load asset source_id -> id mappings from Supabase."""
        try:
            client = self._get_supabase_client()
            response = client.table("assets").select("id, source_id").execute()

            self._asset_cache = {}
            for asset in response.data:
                source_id = asset.get("source_id")
                asset_id = asset.get("id")
                if source_id and asset_id:
                    self._asset_cache[source_id] = UUID(asset_id)

            logger.debug(f"Loaded {len(self._asset_cache)} asset mappings")
            return self._asset_cache

        except Exception as e:
            logger.error(f"Failed to load asset mappings: {e}")
            raise

    def _load_shift_targets(self) -> Dict[UUID, int]:
        """Load current shift targets from Supabase."""
        try:
            client = self._get_supabase_client()

            # Get current shift targets
            # We fetch targets that are currently active based on shift timing
            now = datetime.utcnow()
            today = now.date().isoformat()

            response = client.table("shift_targets").select(
                "asset_id, target_output"
            ).eq("date", today).execute()

            self._target_cache = {}
            for target in response.data:
                asset_id = target.get("asset_id")
                target_output = target.get("target_output", 0)
                if asset_id:
                    self._target_cache[UUID(asset_id)] = target_output

            logger.debug(f"Loaded {len(self._target_cache)} shift targets")
            return self._target_cache

        except Exception as e:
            logger.warning(f"Failed to load shift targets: {e}")
            # Return empty cache - targets will default to 0
            return {}

    def _get_asset_id(self, source_id: str) -> Optional[UUID]:
        """Get asset UUID for a given source_id."""
        if not self._asset_cache:
            self._load_asset_mappings()
        return self._asset_cache.get(source_id)

    def _get_target_output(self, asset_id: UUID) -> int:
        """Get target output for an asset."""
        return self._target_cache.get(asset_id, 0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((SQLAlchemyError, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _execute_query(self, query: str, params: dict) -> List[dict]:
        """Execute a SQL query with retry logic."""
        if not mssql_db.is_initialized:
            raise DatabaseNotConfiguredError("MSSQL database not initialized")

        try:
            with mssql_db.session_scope() as session:
                result = session.execute(text(query), params)
                rows = []
                for row in result:
                    rows.append(dict(row._mapping))
                return rows
        except SQLAlchemyError as e:
            logger.error(f"SQL query failed: {e}")
            raise

    def fetch_production_data(self) -> List[dict]:
        """
        Fetch production output data for the rolling window.

        Returns:
            List of production records from MSSQL
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self._poll_window_minutes)

        # Query for production data in the rolling window
        # NOTE: Adapt column/table names to match actual MSSQL schema
        query = """
            SELECT
                locationName AS source_id,
                COALESCE(SUM(units_produced), 0) AS output_actual,
                MAX(production_timestamp) AS last_reading
            FROM production_output
            WHERE production_timestamp >= :cutoff_time
            GROUP BY locationName
        """

        params = {"cutoff_time": cutoff_time}

        try:
            rows = self._execute_query(query, params)
            logger.info(f"Fetched {len(rows)} production records")
            return rows
        except DatabaseNotConfiguredError:
            logger.warning("MSSQL not configured, returning empty production data")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch production data: {e}")
            raise

    def fetch_downtime_data(self) -> List[dict]:
        """
        Fetch downtime events for the rolling window.

        Returns:
            List of downtime records from MSSQL
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self._poll_window_minutes)

        query = """
            SELECT
                locationName AS source_id,
                event_timestamp,
                COALESCE(duration_minutes, 0) AS duration_minutes,
                reason_code,
                description
            FROM downtime_events
            WHERE event_timestamp >= :cutoff_time
        """

        params = {"cutoff_time": cutoff_time}

        try:
            rows = self._execute_query(query, params)
            logger.info(f"Fetched {len(rows)} downtime records")
            return rows
        except DatabaseNotConfiguredError:
            logger.warning("MSSQL not configured, returning empty downtime data")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch downtime data: {e}")
            raise

    def fetch_oee_data(self) -> Dict[str, Decimal]:
        """
        Fetch current OEE metrics for assets.

        Returns:
            Dictionary mapping source_id to OEE percentage
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self._poll_window_minutes)

        query = """
            SELECT
                locationName AS source_id,
                AVG(oee_percentage) AS oee_current
            FROM oee_readings
            WHERE reading_timestamp >= :cutoff_time
            GROUP BY locationName
        """

        params = {"cutoff_time": cutoff_time}

        try:
            rows = self._execute_query(query, params)
            oee_map = {}
            for row in rows:
                source_id = row.get("source_id")
                oee_value = row.get("oee_current")
                if source_id and oee_value is not None:
                    oee_map[source_id] = Decimal(str(oee_value))
            logger.debug(f"Fetched OEE data for {len(oee_map)} assets")
            return oee_map
        except DatabaseNotConfiguredError:
            logger.warning("MSSQL not configured, returning empty OEE data")
            return {}
        except Exception as e:
            logger.warning(f"Failed to fetch OEE data: {e}")
            return {}

    def detect_safety_events(
        self,
        downtime_records: List[dict]
    ) -> List[SafetyEventData]:
        """
        Detect safety incidents from downtime records.

        Args:
            downtime_records: List of downtime records from MSSQL

        Returns:
            List of safety events to create
        """
        safety_pattern = self._safety_reason_code.lower()
        safety_events = []

        for record in downtime_records:
            reason_code = record.get("reason_code") or ""
            if safety_pattern in reason_code.lower():
                source_id = record.get("source_id")
                asset_id = self._get_asset_id(source_id)

                if asset_id:
                    # Generate source_record_id for deduplication (AC #6 - anti-pattern #6)
                    # Combine source_id and timestamp to create unique identifier
                    event_timestamp = record.get("event_timestamp", datetime.utcnow())
                    record_id = record.get("record_id")  # MSSQL record ID if available
                    if record_id:
                        source_record_id = f"MSSQL_{record_id}"
                    else:
                        # Fallback: use source_id + timestamp
                        source_record_id = f"{source_id}_{event_timestamp.isoformat()}"

                    event = SafetyEventData(
                        asset_id=asset_id,
                        source_id=source_id,
                        event_timestamp=event_timestamp,
                        reason_code=reason_code,
                        description=record.get("description"),
                        duration_minutes=record.get("duration_minutes", 0),
                        source_record_id=source_record_id,
                    )
                    safety_events.append(event)

                    # Log at WARNING level per AC#4
                    logger.warning(
                        f"Safety incident detected: asset={source_id}, "
                        f"reason={reason_code}, duration={event.duration_minutes}min"
                    )
                else:
                    logger.warning(
                        f"Safety incident for unknown asset: {source_id}"
                    )

        logger.info(f"Detected {len(safety_events)} safety events")
        return safety_events

    def create_live_snapshots(
        self,
        production_records: List[dict],
        oee_data: Dict[str, Decimal]
    ) -> List[LiveSnapshotData]:
        """
        Create live snapshot objects from production data.

        Args:
            production_records: Production data from MSSQL
            oee_data: Current OEE values by source_id

        Returns:
            List of snapshot objects to write
        """
        snapshots = []

        for record in production_records:
            source_id = record.get("source_id")
            asset_id = self._get_asset_id(source_id)

            if asset_id is None:
                logger.debug(f"No asset mapping for source_id: {source_id}")
                continue

            output_actual = int(record.get("output_actual", 0))
            output_target = self._get_target_output(asset_id)
            oee_current = oee_data.get(source_id)

            snapshot = LiveSnapshotData(
                asset_id=asset_id,
                source_id=source_id,
                output_actual=output_actual,
                output_target=output_target,
                oee_current=oee_current,
            )
            snapshots.append(snapshot)

        logger.debug(f"Created {len(snapshots)} snapshot objects")
        return snapshots

    def write_snapshots_to_supabase(
        self,
        snapshots: List[LiveSnapshotData]
    ) -> int:
        """
        Write live snapshots to Supabase.

        Args:
            snapshots: List of snapshot objects to write

        Returns:
            Number of snapshots successfully written
        """
        if not snapshots:
            return 0

        try:
            client = self._get_supabase_client()
            written = 0

            # Batch insert for efficiency
            snapshot_data = [s.to_dict() for s in snapshots]
            response = client.table("live_snapshots").insert(snapshot_data).execute()

            written = len(response.data) if response.data else 0
            logger.info(f"Wrote {written} live snapshots to Supabase")
            return written

        except Exception as e:
            logger.error(f"Failed to write snapshots: {e}")
            raise

    def write_safety_events_to_supabase(
        self,
        safety_events: List[SafetyEventData]
    ) -> int:
        """
        Write safety events to Supabase with deduplication.

        Uses source_record_id for deduplication per AC#6 anti-pattern #6.

        Args:
            safety_events: List of safety events to write

        Returns:
            Number of events successfully written
        """
        if not safety_events:
            return 0

        try:
            client = self._get_supabase_client()
            written = 0

            for event in safety_events:
                # Check for existing event using source_record_id (preferred)
                # or fall back to asset_id + timestamp for deduplication
                if event.source_record_id:
                    existing = client.table("safety_events").select("id").eq(
                        "source_record_id", event.source_record_id
                    ).execute()
                else:
                    existing = client.table("safety_events").select("id").eq(
                        "asset_id", str(event.asset_id)
                    ).eq(
                        "event_timestamp", event.event_timestamp.isoformat()
                    ).execute()

                if existing.data:
                    logger.debug(
                        f"Safety event already exists for asset {event.asset_id} "
                        f"(source_record_id: {event.source_record_id})"
                    )
                    continue

                # Insert new event
                response = client.table("safety_events").insert(
                    event.to_dict()
                ).execute()

                if response.data:
                    written += 1
                    logger.info(
                        f"Created safety event for asset {event.source_id}: "
                        f"{event.reason_code}"
                    )

            logger.info(f"Created {written} safety events in Supabase")
            return written

        except Exception as e:
            logger.error(f"Failed to write safety events: {e}")
            raise

    def cleanup_old_snapshots(self) -> int:
        """
        Remove snapshots older than retention period.

        Returns:
            Number of snapshots deleted
        """
        try:
            client = self._get_supabase_client()

            cutoff_time = datetime.utcnow() - timedelta(
                hours=self._snapshot_retention_hours
            )

            response = client.table("live_snapshots").delete().lt(
                "snapshot_timestamp", cutoff_time.isoformat()
            ).execute()

            deleted = len(response.data) if response.data else 0
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old snapshots")
            return deleted

        except Exception as e:
            logger.warning(f"Failed to cleanup old snapshots: {e}")
            return 0

    async def execute_poll(self) -> LivePulseResult:
        """
        Execute a single poll cycle.

        This is the main entry point called by the scheduler.

        Returns:
            LivePulseResult with execution details
        """
        result = LivePulseResult()
        start_time = time.time()
        scheduler = get_scheduler()

        logger.info("Starting Live Pulse poll execution")

        try:
            # Load asset mappings and targets
            self._load_asset_mappings()
            self._load_shift_targets()

            # Step 1: Fetch data from MSSQL
            logger.debug("Fetching production data")
            production_records = self.fetch_production_data()

            logger.debug("Fetching downtime data")
            downtime_records = self.fetch_downtime_data()

            logger.debug("Fetching OEE data")
            oee_data = self.fetch_oee_data()

            # Check execution time
            elapsed = time.time() - start_time
            if elapsed > 45:  # Warning threshold
                logger.warning(
                    f"Poll execution taking longer than expected: {elapsed:.2f}s"
                )

            # Step 2: Detect safety events
            logger.debug("Detecting safety events")
            safety_events = self.detect_safety_events(downtime_records)

            # Step 3: Create live snapshots
            logger.debug("Creating live snapshots")
            snapshots = self.create_live_snapshots(production_records, oee_data)

            # Step 4: Write to Supabase
            logger.debug("Writing safety events to Supabase")
            result.safety_events_created = self.write_safety_events_to_supabase(
                safety_events
            )

            logger.debug("Writing snapshots to Supabase")
            result.snapshots_created = self.write_snapshots_to_supabase(snapshots)

            # Step 5: Cleanup old snapshots
            logger.debug("Cleaning up old snapshots")
            self.cleanup_old_snapshots()

            result.success = True
            result.duration_seconds = time.time() - start_time

            # Update scheduler status
            scheduler.status.record_poll_success(result.duration_seconds)

            logger.info(
                f"Live Pulse poll completed: "
                f"{result.snapshots_created} snapshots, "
                f"{result.safety_events_created} safety events "
                f"(duration: {result.duration_seconds:.2f}s)"
            )

        except DatabaseNotConfiguredError as e:
            result.success = True  # Graceful degradation
            result.duration_seconds = time.time() - start_time
            result.errors.append(f"MSSQL not configured: {e}")
            scheduler.status.record_poll_success(result.duration_seconds)
            logger.warning("Live Pulse poll skipped - MSSQL not configured")

        except Exception as e:
            result.success = False
            result.duration_seconds = time.time() - start_time
            result.errors.append(str(e))
            scheduler.status.record_poll_failure(str(e), result.duration_seconds)
            logger.error(f"Live Pulse poll failed: {e}")
            # Don't re-raise - let scheduler continue running

        return result


# =============================================================================
# Module-level functions
# =============================================================================


# Global pipeline instance
_pipeline_instance: Optional[LivePulsePipeline] = None


def get_live_pulse_pipeline() -> LivePulsePipeline:
    """Get or create the singleton pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = LivePulsePipeline()
    return _pipeline_instance


async def run_live_pulse_poll() -> LivePulseResult:
    """
    Execute a live pulse poll.

    This function is called by the scheduler on each poll interval.

    Returns:
        LivePulseResult with execution details
    """
    pipeline = get_live_pulse_pipeline()
    return await pipeline.execute_poll()
