"""
Data Transformation Service

Handles cleansing, normalization, and transformation of raw MSSQL data
to prepare for OEE and financial calculations.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #3 - Data Cleansing and Transformation
"""

import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set
from uuid import UUID

import pytz
from supabase import create_client, Client

from app.core.config import get_settings
from app.models.pipeline import (
    ExtractedData,
    RawDowntimeRecord,
    RawProductionRecord,
    RawQualityRecord,
    CleanedProductionData,
)

logger = logging.getLogger(__name__)


class TransformationError(Exception):
    """Raised when data transformation fails."""
    pass


class AssetMappingError(TransformationError):
    """Raised when asset mapping cannot be resolved."""
    pass


class DataTransformer:
    """
    Transforms raw MSSQL data into clean, validated formats.

    Handles:
    - NULL value handling (default to 0 or exclude)
    - Zero value validation (distinguish 0 output vs missing)
    - Timestamp normalization to plant local timezone
    - Asset mapping (MSSQL source_id -> Supabase assets.id)
    """

    def __init__(self, timezone: str = None):
        """
        Initialize the transformer.

        Args:
            timezone: Plant local timezone. Defaults to PIPELINE_TIMEZONE env var
                     or "America/Chicago".
        """
        self.timezone = timezone or os.getenv("PIPELINE_TIMEZONE", "America/Chicago")
        self._supabase_client: Optional[Client] = None
        self._asset_cache: Dict[str, UUID] = {}  # source_id -> asset.id

    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client."""
        if self._supabase_client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise TransformationError("Supabase not configured")
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._supabase_client

    def clear_asset_cache(self) -> None:
        """Clear the cached asset mappings."""
        self._asset_cache.clear()

    def load_asset_mappings(self) -> Dict[str, UUID]:
        """
        Load all asset source_id -> id mappings from Supabase.

        Returns:
            Dictionary mapping source_id to asset UUID

        Raises:
            TransformationError: If asset loading fails
        """
        try:
            client = self._get_supabase_client()
            response = client.table("assets").select("id, source_id").execute()

            self._asset_cache = {}
            for asset in response.data:
                source_id = asset.get("source_id")
                asset_id = asset.get("id")
                if source_id and asset_id:
                    self._asset_cache[source_id] = UUID(asset_id)

            logger.info(f"Loaded {len(self._asset_cache)} asset mappings")
            return self._asset_cache

        except Exception as e:
            logger.error(f"Failed to load asset mappings: {e}")
            raise TransformationError(f"Failed to load asset mappings: {e}") from e

    def get_asset_id(self, source_id: str) -> Optional[UUID]:
        """
        Get asset UUID for a given source_id.

        Args:
            source_id: MSSQL locationName value

        Returns:
            Asset UUID if found, None otherwise
        """
        if not self._asset_cache:
            self.load_asset_mappings()

        return self._asset_cache.get(source_id)

    def normalize_timestamp(self, dt: datetime) -> datetime:
        """
        Normalize a timestamp to the plant local timezone.

        Args:
            dt: Input datetime (may be naive or have different timezone)

        Returns:
            Datetime normalized to plant local timezone
        """
        try:
            local_tz = pytz.timezone(self.timezone)

            if dt.tzinfo is None:
                # Assume naive datetime is already in local time
                return local_tz.localize(dt)
            else:
                # Convert to local timezone
                return dt.astimezone(local_tz)

        except Exception as e:
            logger.warning(f"Timestamp normalization failed for {dt}: {e}")
            return dt

    def cleanse_integer(self, value: any, default: int = 0) -> int:
        """
        Cleanse an integer value, handling NULL and invalid values.

        Args:
            value: Raw value to cleanse
            default: Default value for NULL/invalid (default: 0)

        Returns:
            Cleansed integer value
        """
        if value is None:
            return default
        try:
            result = int(value)
            return max(0, result)  # Ensure non-negative
        except (ValueError, TypeError):
            return default

    def cleanse_decimal(self, value: any, default: Decimal = Decimal("0")) -> Decimal:
        """
        Cleanse a decimal value, handling NULL and invalid values.

        Args:
            value: Raw value to cleanse
            default: Default value for NULL/invalid

        Returns:
            Cleansed Decimal value
        """
        if value is None:
            return default
        try:
            result = Decimal(str(value))
            return max(Decimal("0"), result)  # Ensure non-negative
        except Exception:
            return default

    def aggregate_production_by_asset(
        self,
        production_records: List[RawProductionRecord],
        target_date: date
    ) -> Dict[str, Dict]:
        """
        Aggregate production records by source_id.

        Args:
            production_records: List of raw production records
            target_date: Date being processed

        Returns:
            Dictionary keyed by source_id with aggregated production data
        """
        aggregated: Dict[str, Dict] = {}

        for record in production_records:
            source_id = record.source_id
            if not source_id:
                continue

            if source_id not in aggregated:
                aggregated[source_id] = {
                    "source_id": source_id,
                    "production_date": target_date,
                    "units_produced": 0,
                    "units_scrapped": 0,
                    "planned_units": 0,
                    "has_production_data": False,
                }

            agg = aggregated[source_id]
            agg["units_produced"] += self.cleanse_integer(record.units_produced)
            agg["units_scrapped"] += self.cleanse_integer(record.units_scrapped)
            agg["planned_units"] += self.cleanse_integer(record.planned_units)

            # Mark as having data if any non-zero value exists
            if record.units_produced is not None or record.planned_units is not None:
                agg["has_production_data"] = True

        return aggregated

    def aggregate_downtime_by_asset(
        self,
        downtime_records: List[RawDowntimeRecord]
    ) -> Dict[str, int]:
        """
        Aggregate total downtime minutes by source_id.

        Args:
            downtime_records: List of raw downtime records

        Returns:
            Dictionary mapping source_id to total downtime minutes
        """
        downtime_by_asset: Dict[str, int] = {}

        for record in downtime_records:
            source_id = record.source_id
            if not source_id:
                continue

            duration = self.cleanse_integer(record.duration_minutes)
            downtime_by_asset[source_id] = downtime_by_asset.get(source_id, 0) + duration

        return downtime_by_asset

    def aggregate_quality_by_asset(
        self,
        quality_records: List[RawQualityRecord]
    ) -> Dict[str, Dict]:
        """
        Aggregate quality metrics by source_id.

        Args:
            quality_records: List of raw quality records

        Returns:
            Dictionary mapping source_id to quality aggregates
        """
        quality_by_asset: Dict[str, Dict] = {}

        for record in quality_records:
            source_id = record.source_id
            if not source_id:
                continue

            if source_id not in quality_by_asset:
                quality_by_asset[source_id] = {
                    "good_units": 0,
                    "total_units": 0,
                    "scrap_units": 0,
                }

            qba = quality_by_asset[source_id]
            qba["good_units"] += self.cleanse_integer(record.good_units)
            qba["total_units"] += self.cleanse_integer(record.total_units)
            qba["scrap_units"] += self.cleanse_integer(record.scrap_units)

        return quality_by_asset

    def transform(self, extracted_data: ExtractedData) -> List[CleanedProductionData]:
        """
        Transform raw extracted data into cleaned production data.

        This is the main transformation entry point that:
        1. Loads asset mappings from Supabase
        2. Aggregates data by asset
        3. Merges production, downtime, and quality data
        4. Maps source_ids to asset UUIDs
        5. Creates validated CleanedProductionData objects

        Args:
            extracted_data: Raw data from MSSQL extraction

        Returns:
            List of CleanedProductionData objects ready for calculations

        Raises:
            TransformationError: If transformation fails
        """
        target_date = extracted_data.target_date
        logger.info(f"Starting transformation for {target_date}")

        # Load asset mappings
        self.load_asset_mappings()

        # Aggregate raw data by source_id
        production_agg = self.aggregate_production_by_asset(
            extracted_data.production_records,
            target_date
        )
        downtime_agg = self.aggregate_downtime_by_asset(extracted_data.downtime_records)
        quality_agg = self.aggregate_quality_by_asset(extracted_data.quality_records)

        # Get all unique source_ids
        all_source_ids: Set[str] = set()
        all_source_ids.update(production_agg.keys())
        all_source_ids.update(downtime_agg.keys())
        all_source_ids.update(quality_agg.keys())

        # Transform to CleanedProductionData
        cleaned_data: List[CleanedProductionData] = []
        unmapped_sources: Set[str] = set()

        for source_id in all_source_ids:
            # Get asset UUID
            asset_id = self.get_asset_id(source_id)
            if asset_id is None:
                unmapped_sources.add(source_id)
                continue

            # Get aggregated data for this source
            prod = production_agg.get(source_id, {})
            downtime_minutes = downtime_agg.get(source_id, 0)
            quality = quality_agg.get(source_id, {})

            # Build cleaned data
            units_produced = prod.get("units_produced", 0)
            units_scrapped = prod.get("units_scrapped", 0)

            # For quality: use quality records if available, else derive from production
            good_units = quality.get("good_units", 0)
            total_units = quality.get("total_units", 0)

            # If no quality records, derive from production
            if total_units == 0 and units_produced > 0:
                total_units = units_produced
                good_units = units_produced - units_scrapped

            cleaned = CleanedProductionData(
                asset_id=asset_id,
                source_id=source_id,
                production_date=target_date,
                units_produced=units_produced,
                units_scrapped=units_scrapped,
                planned_units=prod.get("planned_units", 0),
                good_units=good_units,
                total_units=total_units,
                total_downtime_minutes=downtime_minutes,
                has_production_data=prod.get("has_production_data", False),
            )
            cleaned_data.append(cleaned)

        if unmapped_sources:
            logger.warning(
                f"Could not map {len(unmapped_sources)} source_ids to assets: "
                f"{list(unmapped_sources)[:5]}..."
            )

        logger.info(
            f"Transformation complete: {len(cleaned_data)} assets, "
            f"{len(unmapped_sources)} unmapped"
        )
        return cleaned_data

    def detect_safety_events(
        self,
        downtime_records: List[RawDowntimeRecord],
        safety_pattern: str = None
    ) -> List[RawDowntimeRecord]:
        """
        Detect safety-related downtime events based on reason_code pattern.

        Args:
            downtime_records: List of all downtime records
            safety_pattern: Pattern to match for safety events.
                           Defaults to SAFETY_REASON_CODE env var or "Safety Issue".

        Returns:
            List of downtime records identified as safety events
        """
        if safety_pattern is None:
            safety_pattern = os.getenv("SAFETY_REASON_CODE", "Safety Issue")

        safety_pattern_lower = safety_pattern.lower()

        safety_events = []
        for record in downtime_records:
            reason = record.reason_code or ""
            if safety_pattern_lower in reason.lower():
                safety_events.append(record)

        logger.info(f"Detected {len(safety_events)} safety events")
        return safety_events


# Module-level singleton
data_transformer = DataTransformer()
