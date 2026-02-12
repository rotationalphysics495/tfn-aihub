"""
Tests for Shift Breakdown on Workcenter Summary API Endpoint.

Story: 17.4 - Shift Breakdown API & UI
AC: #1 - shift_breakdown array with per-shift metrics
AC: #2 - Optional shift filter parameter
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for production endpoint."""
    with patch("app.api.production.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


def _make_table_mock(client_mock, responses_by_table):
    """
    Helper to set up mock Supabase client supporting the shift_summaries
    chained query pattern: .select().eq().eq().execute() and .select().eq().execute()
    """
    def table_side_effect(table_name):
        table_mock = MagicMock()
        data = responses_by_table.get(table_name, [])
        response = MagicMock(data=data)

        # Simple select().execute() chain (assets, shift_targets)
        table_mock.select.return_value.execute.return_value = response
        # select().eq().execute() chain (daily_summaries, shift_summaries no shift filter)
        table_mock.select.return_value.eq.return_value.execute.return_value = response
        # select().eq().eq().execute() chain (shift_summaries with shift filter)
        table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = response

        return table_mock

    client_mock.table.side_effect = table_side_effect


# =============================================================================
# Sample Data
# =============================================================================


ASSET_1_ID = str(uuid4())
ASSET_2_ID = str(uuid4())
ASSET_3_ID = str(uuid4())

SAMPLE_ASSETS = [
    {"id": ASSET_1_ID, "name": "Grinder 1", "area": "Grinding"},
    {"id": ASSET_2_ID, "name": "Grinder 2", "area": "Grinding"},
    {"id": ASSET_3_ID, "name": "Filler 1", "area": "Filling"},
]

SAMPLE_SUMMARIES = [
    {"asset_id": ASSET_1_ID, "units_produced": 300, "oee": 85.0, "downtime_minutes": 60},
    {"asset_id": ASSET_2_ID, "units_produced": 240, "oee": 72.0, "downtime_minutes": 90},
    {"asset_id": ASSET_3_ID, "units_produced": 600, "oee": 92.0, "downtime_minutes": 30},
]

SAMPLE_TARGETS = [
    {"asset_id": ASSET_1_ID, "target_units": 100},
    {"asset_id": ASSET_1_ID, "target_units": 100},
    {"asset_id": ASSET_1_ID, "target_units": 100},  # 3 shifts = 300 total
    {"asset_id": ASSET_2_ID, "target_units": 100},
    {"asset_id": ASSET_2_ID, "target_units": 100},
    {"asset_id": ASSET_2_ID, "target_units": 100},  # 3 shifts = 300 total
    {"asset_id": ASSET_3_ID, "target_units": 200},
    {"asset_id": ASSET_3_ID, "target_units": 200},
    {"asset_id": ASSET_3_ID, "target_units": 200},  # 3 shifts = 600 total
]

SAMPLE_SHIFT_SUMMARIES = [
    # Grinder 1 shifts
    {"asset_id": ASSET_1_ID, "shift": "morning", "oee": 88.0, "downtime_minutes": 15, "units_produced": 120},
    {"asset_id": ASSET_1_ID, "shift": "afternoon", "oee": 84.0, "downtime_minutes": 25, "units_produced": 100},
    {"asset_id": ASSET_1_ID, "shift": "night", "oee": 83.0, "downtime_minutes": 20, "units_produced": 80},
    # Grinder 2 shifts
    {"asset_id": ASSET_2_ID, "shift": "morning", "oee": 78.0, "downtime_minutes": 20, "units_produced": 100},
    {"asset_id": ASSET_2_ID, "shift": "afternoon", "oee": 65.0, "downtime_minutes": 45, "units_produced": 70},
    {"asset_id": ASSET_2_ID, "shift": "night", "oee": 73.0, "downtime_minutes": 25, "units_produced": 70},
    # Filler 1 shifts
    {"asset_id": ASSET_3_ID, "shift": "morning", "oee": 94.0, "downtime_minutes": 8, "units_produced": 220},
    {"asset_id": ASSET_3_ID, "shift": "afternoon", "oee": 91.0, "downtime_minutes": 12, "units_produced": 200},
    {"asset_id": ASSET_3_ID, "shift": "night", "oee": 91.0, "downtime_minutes": 10, "units_produced": 180},
]

SAMPLE_SHIFT_MORNING_ONLY = [
    {"asset_id": ASSET_1_ID, "shift": "morning", "oee": 88.0, "downtime_minutes": 15, "units_produced": 120},
    {"asset_id": ASSET_2_ID, "shift": "morning", "oee": 78.0, "downtime_minutes": 20, "units_produced": 100},
    {"asset_id": ASSET_3_ID, "shift": "morning", "oee": 94.0, "downtime_minutes": 8, "units_produced": 220},
]


# =============================================================================
# Tests: Shift Breakdown Array (AC#1)
# =============================================================================


class TestShiftBreakdown:
    """Tests for shift_breakdown array on workcenter entries."""

    def test_shift_breakdown_populated(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-001: AC#1: shift_breakdown array is populated when shift data exists."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": SAMPLE_SHIFT_SUMMARIES,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Each workcenter should have shift_breakdown
        for wc in data["workcenters"]:
            assert "shift_breakdown" in wc
            assert wc["shift_breakdown"] is not None
            assert len(wc["shift_breakdown"]) == 3  # morning, afternoon, night

            # Each shift should have required fields
            for sb in wc["shift_breakdown"]:
                assert "shift" in sb
                assert "actual_output" in sb
                assert "target_output" in sb
                assert "attainment_pct" in sb
                assert "oee" in sb
                assert "downtime_minutes" in sb
                assert sb["shift"] in ("morning", "afternoon", "night")

    def test_shift_breakdown_empty_when_no_shift_data(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-002: AC#1: shift_breakdown is null when no shift data exists."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": [],  # No shift data
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        for wc in data["workcenters"]:
            assert wc["shift_breakdown"] is None

    def test_shift_breakdown_ordered_morning_afternoon_night(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-003: AC#1: shift_breakdown items appear in morning/afternoon/night order."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": SAMPLE_SHIFT_SUMMARIES,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        for wc in data["workcenters"]:
            shifts = [sb["shift"] for sb in wc["shift_breakdown"]]
            assert shifts == ["morning", "afternoon", "night"]

    def test_shift_breakdown_aggregates_across_assets(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-004: AC#1: shift_breakdown aggregates actual_output across all assets in workcenter."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": SAMPLE_SHIFT_SUMMARIES,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        grinding = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Grinding")
        morning = next(sb for sb in grinding["shift_breakdown"] if sb["shift"] == "morning")

        # Grinder 1 morning: 120, Grinder 2 morning: 100
        assert morning["actual_output"] == 220

    def test_daily_aggregate_unchanged(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-005: AC#1: Overall workcenter figures remain from daily aggregation."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": SAMPLE_SHIFT_SUMMARIES,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        grinding = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Grinding")
        # Grinder 1: 300 actual, Grinder 2: 240 actual
        assert grinding["total_actual"] == 540
        # Grinder 1: 300 target, Grinder 2: 300 target
        assert grinding["total_target"] == 600


# =============================================================================
# Tests: Shift Filter Parameter (AC#2)
# =============================================================================


class TestShiftFilter:
    """Tests for shift query parameter filtering."""

    def test_shift_filter_returns_shift_data(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-006: AC#2: shift parameter filters to show only that shift's data."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": SAMPLE_SHIFT_MORNING_ONLY,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10&shift=morning",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["workcenters"]) > 0

        # When shift is filtered, shift_breakdown should be null (not applicable)
        for wc in data["workcenters"]:
            assert wc["shift_breakdown"] is None

    def test_shift_filter_overrides_primary_metrics(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-007: AC#2: shift filter uses shift data as primary metrics."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": SAMPLE_SHIFT_MORNING_ONLY,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10&shift=morning",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        grinding = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Grinding")
        # Morning shift: Grinder 1 = 120, Grinder 2 = 100
        assert grinding["total_actual"] == 220

    def test_invalid_shift_returns_400(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-008: Invalid shift parameter returns 400 error."""
        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10&shift=invalid",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid shift value" in data["detail"]

    def test_no_shift_param_returns_all_with_breakdown(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-009: No shift param returns aggregate with shift_breakdown populated."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": SAMPLE_SHIFT_SUMMARIES,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        for wc in data["workcenters"]:
            assert wc["shift_breakdown"] is not None


# =============================================================================
# Tests: Backward Compatibility
# =============================================================================


class TestShiftBreakdownBackwardCompat:
    """Tests for backward compatibility when no shift data exists."""

    def test_existing_response_unchanged_without_shift_data(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-010: Existing response structure preserved when shift_summaries is empty."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": [],
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["workcenters"]) == 2
        grinding = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Grinding")
        assert grinding["total_actual"] == 540
        assert grinding["total_target"] == 600
        assert grinding["shift_breakdown"] is None

    def test_date_defaults_to_yesterday(self, client, mock_verify_jwt, mock_supabase_client):
        """17-4-UNIT-011: Date still defaults to T-1 when not provided."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
            "shift_summaries": [],
        })

        response = client.get(
            "/api/v1/production/workcenter-summary",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        assert data["report_date"] == yesterday
