"""
MSSQL Data Extraction Service

Handles extraction of T-1 (previous day) production data from MSSQL.
Uses read-only queries with retry logic for resilience.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #2 - MSSQL Data Extraction
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.core.database import mssql_db, DatabaseError, DatabaseNotConfiguredError
from app.models.pipeline import (
    ExtractedData,
    RawProductionRecord,
    RawDowntimeRecord,
    RawQualityRecord,
    RawLaborRecord,
)

logger = logging.getLogger(__name__)


class DataExtractionError(Exception):
    """Raised when data extraction fails after retries."""
    pass


class DataExtractor:
    """
    Extracts production data from MSSQL for the Morning Report pipeline.

    All queries are SELECT-only (read-only) per NFR3 compliance.
    Implements retry logic with exponential backoff for transient failures.
    """

    def __init__(self, retry_count: int = 3):
        """
        Initialize the data extractor.

        Args:
            retry_count: Maximum number of retry attempts (default: 3)
        """
        self.retry_count = retry_count

    def get_target_date_range(self, target_date: date) -> tuple[datetime, datetime]:
        """
        Get the full 24-hour window for a target date.

        Args:
            target_date: The date to get range for

        Returns:
            Tuple of (start_datetime, end_datetime) covering full day
        """
        start_datetime = datetime.combine(target_date, time.min)  # 00:00:00
        end_datetime = datetime.combine(target_date, time.max)    # 23:59:59.999999
        return start_datetime, end_datetime

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((SQLAlchemyError, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _execute_query(self, query: str, params: dict) -> List[dict]:
        """
        Execute a SQL query with retry logic.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows as dictionaries

        Raises:
            DataExtractionError: If query fails after retries
        """
        if not mssql_db.is_initialized:
            raise DatabaseNotConfiguredError("MSSQL database not initialized")

        try:
            with mssql_db.session_scope() as session:
                result = session.execute(text(query), params)
                # Convert rows to dictionaries
                rows = []
                for row in result:
                    rows.append(dict(row._mapping))
                return rows
        except SQLAlchemyError as e:
            logger.error(f"SQL query failed: {e}")
            raise

    def extract_production_data(self, target_date: date) -> List[RawProductionRecord]:
        """
        Extract production output data for the target date.

        Args:
            target_date: Date to extract data for (T-1)

        Returns:
            List of raw production records
        """
        start_dt, end_dt = self.get_target_date_range(target_date)

        # NOTE: This query structure assumes a typical manufacturing MSSQL schema.
        # Adjust column/table names to match actual source database structure.
        query = """
            SELECT
                locationName AS source_id,
                CAST(production_date AS DATE) AS production_date,
                COALESCE(units_produced, 0) AS units_produced,
                COALESCE(units_scrapped, 0) AS units_scrapped,
                COALESCE(planned_units, 0) AS planned_units
            FROM production_output
            WHERE production_date >= :start_date
              AND production_date <= :end_date
        """

        params = {"start_date": start_dt, "end_date": end_dt}

        try:
            rows = self._execute_query(query, params)
            records = []
            for row in rows:
                try:
                    record = RawProductionRecord(
                        source_id=str(row.get("source_id", "")),
                        production_date=row.get("production_date") or target_date,
                        units_produced=row.get("units_produced"),
                        units_scrapped=row.get("units_scrapped"),
                        planned_units=row.get("planned_units"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to parse production record: {e}, row: {row}")
                    continue

            logger.info(f"Extracted {len(records)} production records for {target_date}")
            return records

        except DatabaseNotConfiguredError:
            logger.warning("MSSQL not configured, returning empty production data")
            return []
        except Exception as e:
            logger.error(f"Failed to extract production data: {e}")
            raise DataExtractionError(f"Production data extraction failed: {e}") from e

    def extract_downtime_data(self, target_date: date) -> List[RawDowntimeRecord]:
        """
        Extract downtime events for the target date.

        Args:
            target_date: Date to extract data for (T-1)

        Returns:
            List of raw downtime records
        """
        start_dt, end_dt = self.get_target_date_range(target_date)

        query = """
            SELECT
                locationName AS source_id,
                event_timestamp,
                COALESCE(duration_minutes, 0) AS duration_minutes,
                reason_code,
                description
            FROM downtime_events
            WHERE event_timestamp >= :start_date
              AND event_timestamp <= :end_date
        """

        params = {"start_date": start_dt, "end_date": end_dt}

        try:
            rows = self._execute_query(query, params)
            records = []
            for row in rows:
                try:
                    record = RawDowntimeRecord(
                        source_id=str(row.get("source_id", "")),
                        event_timestamp=row.get("event_timestamp") or start_dt,
                        duration_minutes=int(row.get("duration_minutes", 0)),
                        reason_code=row.get("reason_code"),
                        description=row.get("description"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to parse downtime record: {e}, row: {row}")
                    continue

            logger.info(f"Extracted {len(records)} downtime records for {target_date}")
            return records

        except DatabaseNotConfiguredError:
            logger.warning("MSSQL not configured, returning empty downtime data")
            return []
        except Exception as e:
            logger.error(f"Failed to extract downtime data: {e}")
            raise DataExtractionError(f"Downtime data extraction failed: {e}") from e

    def extract_quality_data(self, target_date: date) -> List[RawQualityRecord]:
        """
        Extract quality/scrap data for the target date.

        Args:
            target_date: Date to extract data for (T-1)

        Returns:
            List of raw quality records
        """
        start_dt, end_dt = self.get_target_date_range(target_date)

        query = """
            SELECT
                locationName AS source_id,
                CAST(production_date AS DATE) AS production_date,
                COALESCE(good_units, 0) AS good_units,
                COALESCE(total_units, 0) AS total_units,
                COALESCE(scrap_units, 0) AS scrap_units,
                COALESCE(rework_units, 0) AS rework_units
            FROM quality_records
            WHERE production_date >= :start_date
              AND production_date <= :end_date
        """

        params = {"start_date": start_dt, "end_date": end_dt}

        try:
            rows = self._execute_query(query, params)
            records = []
            for row in rows:
                try:
                    record = RawQualityRecord(
                        source_id=str(row.get("source_id", "")),
                        production_date=row.get("production_date") or target_date,
                        good_units=row.get("good_units"),
                        total_units=row.get("total_units"),
                        scrap_units=row.get("scrap_units"),
                        rework_units=row.get("rework_units"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to parse quality record: {e}, row: {row}")
                    continue

            logger.info(f"Extracted {len(records)} quality records for {target_date}")
            return records

        except DatabaseNotConfiguredError:
            logger.warning("MSSQL not configured, returning empty quality data")
            return []
        except Exception as e:
            logger.error(f"Failed to extract quality data: {e}")
            raise DataExtractionError(f"Quality data extraction failed: {e}") from e

    def extract_labor_data(self, target_date: date) -> List[RawLaborRecord]:
        """
        Extract labor/shift data for the target date.

        Args:
            target_date: Date to extract data for (T-1)

        Returns:
            List of raw labor records
        """
        start_dt, end_dt = self.get_target_date_range(target_date)

        query = """
            SELECT
                locationName AS source_id,
                CAST(production_date AS DATE) AS production_date,
                planned_hours,
                actual_hours,
                headcount
            FROM labor_records
            WHERE production_date >= :start_date
              AND production_date <= :end_date
        """

        params = {"start_date": start_dt, "end_date": end_dt}

        try:
            rows = self._execute_query(query, params)
            records = []
            for row in rows:
                try:
                    record = RawLaborRecord(
                        source_id=str(row.get("source_id", "")),
                        production_date=row.get("production_date") or target_date,
                        planned_hours=row.get("planned_hours"),
                        actual_hours=row.get("actual_hours"),
                        headcount=row.get("headcount"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to parse labor record: {e}, row: {row}")
                    continue

            logger.info(f"Extracted {len(records)} labor records for {target_date}")
            return records

        except DatabaseNotConfiguredError:
            logger.warning("MSSQL not configured, returning empty labor data")
            return []
        except Exception as e:
            logger.error(f"Failed to extract labor data: {e}")
            raise DataExtractionError(f"Labor data extraction failed: {e}") from e

    def extract_all(self, target_date: Optional[date] = None) -> ExtractedData:
        """
        Extract all data types for the target date (T-1 by default).

        Args:
            target_date: Date to extract data for. Defaults to yesterday.

        Returns:
            ExtractedData containing all raw records

        Raises:
            DataExtractionError: If any extraction fails after retries
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        logger.info(f"Starting data extraction for {target_date}")

        extracted = ExtractedData(
            target_date=target_date,
            production_records=self.extract_production_data(target_date),
            downtime_records=self.extract_downtime_data(target_date),
            quality_records=self.extract_quality_data(target_date),
            labor_records=self.extract_labor_data(target_date),
        )

        total_records = (
            len(extracted.production_records) +
            len(extracted.downtime_records) +
            len(extracted.quality_records) +
            len(extracted.labor_records)
        )
        logger.info(f"Completed extraction: {total_records} total records for {target_date}")

        return extracted


# Module-level singleton for convenience
data_extractor = DataExtractor()
