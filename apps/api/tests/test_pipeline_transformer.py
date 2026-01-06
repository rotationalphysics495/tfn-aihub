"""
Tests for Data Transformation Service.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #3 - Data Cleansing and Transformation
AC: #7 - Safety Event Detection
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, MagicMock

import pytz

from app.services.pipelines.transformer import (
    DataTransformer,
    TransformationError,
    AssetMappingError,
)
from app.models.pipeline import (
    ExtractedData,
    RawProductionRecord,
    RawDowntimeRecord,
    RawQualityRecord,
    CleanedProductionData,
)


@pytest.fixture
def transformer():
    """Create a fresh transformer instance."""
    return DataTransformer(timezone="America/Chicago")


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
            RawProductionRecord(
                source_id="GRINDER_02",
                production_date=date(2026, 1, 5),
                units_produced=1200,
                units_scrapped=10,
                planned_units=1500,
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


class TestNullHandling:
    """Tests for NULL value handling."""

    def test_cleanse_integer_null_returns_default(self, transformer):
        """AC#3: NULL integers default to 0."""
        assert transformer.cleanse_integer(None) == 0
        assert transformer.cleanse_integer(None, default=100) == 100

    def test_cleanse_integer_valid_value(self, transformer):
        """AC#3: Valid integers are preserved."""
        assert transformer.cleanse_integer(42) == 42
        assert transformer.cleanse_integer("100") == 100

    def test_cleanse_integer_negative_becomes_zero(self, transformer):
        """AC#3: Negative values become 0 (non-negative constraint)."""
        assert transformer.cleanse_integer(-5) == 0

    def test_cleanse_decimal_null_returns_default(self, transformer):
        """AC#3: NULL decimals default to 0."""
        assert transformer.cleanse_decimal(None) == Decimal("0")
        assert transformer.cleanse_decimal(None, default=Decimal("10.5")) == Decimal("10.5")

    def test_cleanse_decimal_valid_value(self, transformer):
        """AC#3: Valid decimals are preserved."""
        assert transformer.cleanse_decimal(42.5) == Decimal("42.5")
        assert transformer.cleanse_decimal("100.25") == Decimal("100.25")


class TestZeroValueValidation:
    """Tests for distinguishing 0 output vs missing data."""

    def test_production_with_zero_output(self, transformer):
        """AC#3: Zero output is valid and distinct from missing."""
        records = [
            RawProductionRecord(
                source_id="ASSET_01",
                production_date=date(2026, 1, 5),
                units_produced=0,  # Actual zero output
                units_scrapped=0,
                planned_units=1000,
            )
        ]

        aggregated = transformer.aggregate_production_by_asset(
            records, date(2026, 1, 5)
        )

        assert "ASSET_01" in aggregated
        assert aggregated["ASSET_01"]["units_produced"] == 0
        assert aggregated["ASSET_01"]["has_production_data"] is True  # Data exists

    def test_production_with_null_output(self, transformer):
        """AC#3: NULL output indicates missing data."""
        records = [
            RawProductionRecord(
                source_id="ASSET_01",
                production_date=date(2026, 1, 5),
                units_produced=None,  # Missing data
                units_scrapped=None,
                planned_units=None,
            )
        ]

        aggregated = transformer.aggregate_production_by_asset(
            records, date(2026, 1, 5)
        )

        assert "ASSET_01" in aggregated
        assert aggregated["ASSET_01"]["units_produced"] == 0
        assert aggregated["ASSET_01"]["has_production_data"] is False  # No real data


class TestTimestampNormalization:
    """Tests for timestamp normalization to plant local timezone."""

    def test_normalize_naive_datetime(self, transformer):
        """AC#3: Naive datetime is localized to plant timezone."""
        naive_dt = datetime(2026, 1, 5, 14, 30, 0)
        normalized = transformer.normalize_timestamp(naive_dt)

        assert normalized.tzinfo is not None
        assert normalized.hour == 14  # Hour preserved
        assert normalized.minute == 30

    def test_normalize_utc_datetime(self, transformer):
        """AC#3: UTC datetime is converted to plant timezone."""
        utc_dt = datetime(2026, 1, 5, 20, 0, 0, tzinfo=pytz.UTC)
        normalized = transformer.normalize_timestamp(utc_dt)

        # Chicago is UTC-6, so 20:00 UTC = 14:00 CST
        assert normalized.hour == 14

    def test_normalize_handles_invalid(self, transformer):
        """AC#3: Invalid timestamps are returned as-is."""
        dt = datetime(2026, 1, 5, 14, 30, 0)

        with patch("pytz.timezone", side_effect=Exception("Invalid timezone")):
            result = transformer.normalize_timestamp(dt)
            assert result == dt  # Original returned on error


class TestAssetMapping:
    """Tests for asset mapping (source_id -> Supabase asset.id)."""

    def test_load_asset_mappings_success(self, transformer):
        """AC#3: Load asset mappings from Supabase."""
        mock_data = [
            {"id": str(uuid4()), "source_id": "GRINDER_01"},
            {"id": str(uuid4()), "source_id": "GRINDER_02"},
        ]

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.return_value.data = mock_data

        with patch.object(transformer, "_get_supabase_client", return_value=mock_client):
            mappings = transformer.load_asset_mappings()

            assert len(mappings) == 2
            assert "GRINDER_01" in mappings
            assert "GRINDER_02" in mappings

    def test_get_asset_id_returns_uuid(self, transformer):
        """AC#3: Get asset UUID for source_id."""
        asset_uuid = uuid4()
        transformer._asset_cache = {"GRINDER_01": asset_uuid}

        result = transformer.get_asset_id("GRINDER_01")
        assert result == asset_uuid

    def test_get_asset_id_unknown_returns_none(self, transformer):
        """AC#3: Unknown source_id returns None."""
        transformer._asset_cache = {"GRINDER_01": uuid4()}

        result = transformer.get_asset_id("UNKNOWN_ASSET")
        assert result is None

    def test_clear_asset_cache(self, transformer):
        """AC#3: Cache can be cleared."""
        transformer._asset_cache = {"GRINDER_01": uuid4()}
        transformer.clear_asset_cache()
        assert transformer._asset_cache == {}


class TestDataAggregation:
    """Tests for data aggregation by asset."""

    def test_aggregate_production_multiple_records(self, transformer):
        """AC#3: Multiple records for same asset are summed."""
        records = [
            RawProductionRecord(
                source_id="ASSET_01",
                production_date=date(2026, 1, 5),
                units_produced=500,
                units_scrapped=5,
                planned_units=600,
            ),
            RawProductionRecord(
                source_id="ASSET_01",
                production_date=date(2026, 1, 5),
                units_produced=500,
                units_scrapped=5,
                planned_units=600,
            ),
        ]

        aggregated = transformer.aggregate_production_by_asset(
            records, date(2026, 1, 5)
        )

        assert aggregated["ASSET_01"]["units_produced"] == 1000
        assert aggregated["ASSET_01"]["units_scrapped"] == 10
        assert aggregated["ASSET_01"]["planned_units"] == 1200

    def test_aggregate_downtime_by_asset(self, transformer):
        """AC#3: Downtime minutes are summed per asset."""
        records = [
            RawDowntimeRecord(
                source_id="ASSET_01",
                event_timestamp=datetime(2026, 1, 5, 10, 0, 0),
                duration_minutes=30,
            ),
            RawDowntimeRecord(
                source_id="ASSET_01",
                event_timestamp=datetime(2026, 1, 5, 14, 0, 0),
                duration_minutes=15,
            ),
        ]

        downtime = transformer.aggregate_downtime_by_asset(records)

        assert downtime["ASSET_01"] == 45

    def test_aggregate_quality_by_asset(self, transformer):
        """AC#3: Quality metrics are summed per asset."""
        records = [
            RawQualityRecord(
                source_id="ASSET_01",
                production_date=date(2026, 1, 5),
                good_units=450,
                total_units=500,
                scrap_units=50,
            ),
            RawQualityRecord(
                source_id="ASSET_01",
                production_date=date(2026, 1, 5),
                good_units=480,
                total_units=500,
                scrap_units=20,
            ),
        ]

        quality = transformer.aggregate_quality_by_asset(records)

        assert quality["ASSET_01"]["good_units"] == 930
        assert quality["ASSET_01"]["total_units"] == 1000
        assert quality["ASSET_01"]["scrap_units"] == 70


class TestTransform:
    """Tests for main transform function."""

    def test_transform_creates_cleaned_data(self, transformer, sample_extracted_data):
        """AC#3: Transform creates CleanedProductionData objects."""
        # Mock asset mappings
        asset1 = uuid4()
        asset2 = uuid4()
        transformer._asset_cache = {
            "GRINDER_01": asset1,
            "GRINDER_02": asset2,
        }

        with patch.object(transformer, "load_asset_mappings", return_value=transformer._asset_cache):
            cleaned = transformer.transform(sample_extracted_data)

            assert len(cleaned) == 2
            assert all(isinstance(c, CleanedProductionData) for c in cleaned)

    def test_transform_skips_unmapped_assets(self, transformer, sample_extracted_data):
        """AC#3: Assets without mapping are skipped."""
        # Only map one asset
        transformer._asset_cache = {"GRINDER_01": uuid4()}

        with patch.object(transformer, "load_asset_mappings", return_value=transformer._asset_cache):
            cleaned = transformer.transform(sample_extracted_data)

            # Only GRINDER_01 should be included
            assert len(cleaned) == 1
            assert cleaned[0].source_id == "GRINDER_01"


class TestSafetyEventDetection:
    """Tests for safety event detection."""

    def test_detect_safety_events_by_pattern(self, transformer):
        """AC#7: Detect safety events by reason_code pattern."""
        records = [
            RawDowntimeRecord(
                source_id="ASSET_01",
                event_timestamp=datetime(2026, 1, 5, 10, 0, 0),
                duration_minutes=30,
                reason_code="Safety Issue",  # Matches
            ),
            RawDowntimeRecord(
                source_id="ASSET_02",
                event_timestamp=datetime(2026, 1, 5, 11, 0, 0),
                duration_minutes=15,
                reason_code="Mechanical Failure",  # Doesn't match
            ),
            RawDowntimeRecord(
                source_id="ASSET_03",
                event_timestamp=datetime(2026, 1, 5, 12, 0, 0),
                duration_minutes=45,
                reason_code="safety issue - employee injury",  # Case insensitive
            ),
        ]

        safety = transformer.detect_safety_events(records)

        assert len(safety) == 2
        assert safety[0].source_id == "ASSET_01"
        assert safety[1].source_id == "ASSET_03"

    def test_detect_safety_events_custom_pattern(self, transformer):
        """AC#7: Custom safety pattern via parameter."""
        records = [
            RawDowntimeRecord(
                source_id="ASSET_01",
                event_timestamp=datetime(2026, 1, 5, 10, 0, 0),
                duration_minutes=30,
                reason_code="Emergency Stop",
            ),
        ]

        safety = transformer.detect_safety_events(
            records, safety_pattern="Emergency"
        )

        assert len(safety) == 1

    def test_detect_safety_events_no_matches(self, transformer):
        """AC#7: Return empty list when no safety events."""
        records = [
            RawDowntimeRecord(
                source_id="ASSET_01",
                event_timestamp=datetime(2026, 1, 5, 10, 0, 0),
                duration_minutes=30,
                reason_code="Scheduled Maintenance",
            ),
        ]

        safety = transformer.detect_safety_events(records)

        assert safety == []

    def test_detect_safety_events_handles_null_reason(self, transformer):
        """AC#7: Handle NULL reason_code."""
        records = [
            RawDowntimeRecord(
                source_id="ASSET_01",
                event_timestamp=datetime(2026, 1, 5, 10, 0, 0),
                duration_minutes=30,
                reason_code=None,  # NULL
            ),
        ]

        safety = transformer.detect_safety_events(records)

        assert safety == []


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_transform_empty_data(self, transformer):
        """AC#3: Handle empty extracted data."""
        empty_data = ExtractedData(
            target_date=date(2026, 1, 5),
            production_records=[],
            downtime_records=[],
            quality_records=[],
            labor_records=[],
        )

        transformer._asset_cache = {}

        with patch.object(transformer, "load_asset_mappings", return_value={}):
            cleaned = transformer.transform(empty_data)
            assert cleaned == []

    def test_transform_handles_empty_source_id(self, transformer):
        """AC#3: Skip records with empty source_id."""
        records = [
            RawProductionRecord(
                source_id="",  # Empty
                production_date=date(2026, 1, 5),
                units_produced=1000,
            ),
            RawProductionRecord(
                source_id="GOOD_ASSET",
                production_date=date(2026, 1, 5),
                units_produced=500,
            ),
        ]

        aggregated = transformer.aggregate_production_by_asset(
            records, date(2026, 1, 5)
        )

        assert "" not in aggregated
        assert "GOOD_ASSET" in aggregated
