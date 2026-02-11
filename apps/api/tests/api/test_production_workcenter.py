"""
Tests for Production Workcenter Summary API Endpoint.

Story: 11.1 - Workcenter Summary API Endpoint
AC: #1 - Workcenter-grouped response with aggregations
AC: #2 - Empty data returns 200 with message
AC: #3 - Date defaults to T-1
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# =============================================================================
# Fixtures
# =============================================================================

# Note: mock_verify_jwt fixture is provided by conftest.py


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for production endpoint."""
    with patch("app.api.production.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


def _make_table_mock(client_mock, responses_by_table):
    """
    Helper to set up mock Supabase client so that different .table() calls
    return different mock chains.

    responses_by_table: dict mapping table name -> mock response data
    """
    def table_side_effect(table_name):
        table_mock = MagicMock()
        data = responses_by_table.get(table_name, [])
        response = MagicMock(data=data)

        # Simple select().execute() chain (assets, shift_targets)
        table_mock.select.return_value.execute.return_value = response
        # select().eq().execute() chain (daily_summaries)
        table_mock.select.return_value.eq.return_value.execute.return_value = response

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
    {"asset_id": ASSET_1_ID, "units_produced": 100, "oee": 85.5, "downtime_minutes": 30},
    {"asset_id": ASSET_2_ID, "units_produced": 80, "oee": 72.0, "downtime_minutes": 45},
    {"asset_id": ASSET_3_ID, "units_produced": 200, "oee": 92.0, "downtime_minutes": 10},
]

SAMPLE_TARGETS = [
    {"asset_id": ASSET_1_ID, "target_units": 50},
    {"asset_id": ASSET_1_ID, "target_units": 50},  # Two shifts = 100 total
    {"asset_id": ASSET_2_ID, "target_units": 60},
    {"asset_id": ASSET_2_ID, "target_units": 60},  # Two shifts = 120 total
    {"asset_id": ASSET_3_ID, "target_units": 100},
    {"asset_id": ASSET_3_ID, "target_units": 100},  # Two shifts = 200 total
]


# =============================================================================
# Tests: Authentication
# =============================================================================


class TestWorkcenterSummaryAuth:
    """Tests for authentication on workcenter-summary endpoint."""

    def test_requires_authentication(self, client):
        """11-1-UNIT-001: AC#1: Endpoint requires JWT authentication."""
        response = client.get("/api/v1/production/workcenter-summary")
        assert response.status_code == 401

    def test_requires_authentication_legacy_path(self, client):
        """11-1-UNIT-002: Endpoint requires JWT authentication on legacy path too."""
        response = client.get("/api/production/workcenter-summary")
        assert response.status_code == 401


# =============================================================================
# Tests: Normal Response (AC#1)
# =============================================================================


class TestWorkcenterSummaryNormal:
    """Tests for normal workcenter summary responses."""

    def test_returns_grouped_workcenters(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-003: AC#1: Response includes one entry per workcenter grouped by area."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "workcenters" in data
        assert "report_date" in data
        assert data["report_date"] == "2026-02-10"

        # Should have 2 workcenters: Filling and Grinding
        wc_names = [wc["workcenter"] for wc in data["workcenters"]]
        assert "Grinding" in wc_names
        assert "Filling" in wc_names
        assert len(data["workcenters"]) == 2

    def test_workcenter_aggregations(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-004: AC#1: Workcenter entry has correct totals and attainment."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Find Grinding workcenter
        grinding = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Grinding")
        # Grinder 1: actual=100, target=100; Grinder 2: actual=80, target=120
        assert grinding["total_actual"] == 180
        assert grinding["total_target"] == 220
        # 180/220 * 100 = 81.8%
        assert grinding["attainment_pct"] == 81.8
        # Grinder 1 hit (100 >= 100), Grinder 2 missed (80 < 120)
        assert grinding["assets_hit"] == 1
        assert grinding["assets_missed"] == 1

        # Find Filling workcenter
        filling = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Filling")
        assert filling["total_actual"] == 200
        assert filling["total_target"] == 200
        assert filling["attainment_pct"] == 100.0
        assert filling["assets_hit"] == 1
        assert filling["assets_missed"] == 0

    def test_per_asset_breakdown(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-005: AC#1: Per-asset breakdown includes name, actual, target, OEE, downtime."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        grinding = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Grinding")
        assert len(grinding["assets"]) == 2

        # Check one asset detail
        grinder1 = next(a for a in grinding["assets"] if a["asset_name"] == "Grinder 1")
        assert grinder1["actual_output"] == 100
        assert grinder1["target_output"] == 100
        assert grinder1["attainment_pct"] == 100.0
        assert grinder1["oee"] == 85.5
        assert grinder1["downtime_minutes"] == 30
        assert grinder1["hit_target"] is True

        grinder2 = next(a for a in grinding["assets"] if a["asset_name"] == "Grinder 2")
        assert grinder2["actual_output"] == 80
        assert grinder2["target_output"] == 120
        assert grinder2["hit_target"] is False

    def test_legacy_path_works(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-006: Endpoint is accessible on legacy /api/production path too."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": SAMPLE_SUMMARIES,
            "shift_targets": SAMPLE_TARGETS,
        })

        response = client.get(
            "/api/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["workcenters"]) == 2


# =============================================================================
# Tests: Empty Data (AC#2)
# =============================================================================


class TestWorkcenterSummaryEmpty:
    """Tests for empty data scenario."""

    def test_empty_data_returns_200_with_message(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-007: AC#2: No daily summary data returns 200 with empty array and message."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": [],
            "shift_targets": SAMPLE_TARGETS,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["workcenters"] == []
        assert data["report_date"] == "2026-02-10"
        assert "No data available" in data["message"]
        assert "2026-02-10" in data["message"]


# =============================================================================
# Tests: Date Defaulting (AC#3)
# =============================================================================


class TestWorkcenterSummaryDateDefault:
    """Tests for date parameter handling."""

    def test_date_defaults_to_yesterday(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-008: AC#3: When no date param, defaults to T-1."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": [],
            "shift_targets": SAMPLE_TARGETS,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        expected_date = (date.today() - timedelta(days=1)).isoformat()
        assert data["report_date"] == expected_date

    def test_explicit_date_param_is_respected(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-009: AC#3: Explicit date parameter is used when provided."""
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "daily_summaries": [],
            "shift_targets": SAMPLE_TARGETS,
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-01-15",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["report_date"] == "2026-01-15"


# =============================================================================
# Tests: Edge Cases
# =============================================================================


class TestWorkcenterSummaryEdgeCases:
    """Tests for edge cases."""

    def test_zero_target_attainment(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-010: Edge case: Zero target returns 100.0 attainment (no division by zero)."""
        asset_id = str(uuid4())
        _make_table_mock(mock_supabase_client, {
            "assets": [{"id": asset_id, "name": "Asset X", "area": "Testing"}],
            "daily_summaries": [{"asset_id": asset_id, "units_produced": 50, "oee": 80.0, "downtime_minutes": 10}],
            "shift_targets": [],  # No targets at all
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["workcenters"]) == 1
        wc = data["workcenters"][0]
        assert wc["attainment_pct"] == 100.0
        assert wc["assets"][0]["attainment_pct"] == 100.0
        assert wc["assets"][0]["hit_target"] is True

    def test_null_area_assets_excluded(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-011: Edge case: Assets with NULL area are excluded from response."""
        asset_with_area = str(uuid4())
        asset_no_area = str(uuid4())
        _make_table_mock(mock_supabase_client, {
            "assets": [
                {"id": asset_with_area, "name": "Good Asset", "area": "Grinding"},
                {"id": asset_no_area, "name": "No Area Asset", "area": None},
            ],
            "daily_summaries": [
                {"asset_id": asset_with_area, "units_produced": 100, "oee": 90.0, "downtime_minutes": 5},
                {"asset_id": asset_no_area, "units_produced": 50, "oee": 70.0, "downtime_minutes": 20},
            ],
            "shift_targets": [
                {"asset_id": asset_with_area, "target_units": 100},
                {"asset_id": asset_no_area, "target_units": 50},
            ],
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        # Only the asset with an area should appear
        assert len(data["workcenters"]) == 1
        assert data["workcenters"][0]["workcenter"] == "Grinding"
        assert len(data["workcenters"][0]["assets"]) == 1

    def test_partial_data_asset_with_summary_but_no_target(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-012: Edge case: Asset has daily summary but no shift_target entry."""
        asset_id = str(uuid4())
        _make_table_mock(mock_supabase_client, {
            "assets": [{"id": asset_id, "name": "Partial Asset", "area": "Packaging"}],
            "daily_summaries": [{"asset_id": asset_id, "units_produced": 75, "oee": 80.0, "downtime_minutes": 15}],
            "shift_targets": [],  # No target for this asset
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["workcenters"]) == 1
        asset = data["workcenters"][0]["assets"][0]
        assert asset["actual_output"] == 75
        assert asset["target_output"] == 0
        assert asset["hit_target"] is True  # 75 >= 0

    def test_asset_with_target_but_no_summary_excluded(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-013: Edge case: Asset has shift_target but no daily_summary - not in response."""
        asset_with_summary = str(uuid4())
        asset_no_summary = str(uuid4())
        _make_table_mock(mock_supabase_client, {
            "assets": [
                {"id": asset_with_summary, "name": "Has Data", "area": "Grinding"},
                {"id": asset_no_summary, "name": "No Data", "area": "Grinding"},
            ],
            "daily_summaries": [
                {"asset_id": asset_with_summary, "units_produced": 100, "oee": 90.0, "downtime_minutes": 5},
            ],
            "shift_targets": [
                {"asset_id": asset_with_summary, "target_units": 100},
                {"asset_id": asset_no_summary, "target_units": 100},
            ],
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        grinding = data["workcenters"][0]
        # Only the asset with a summary should appear
        assert len(grinding["assets"]) == 1
        assert grinding["assets"][0]["asset_name"] == "Has Data"

    def test_null_oee_and_downtime_returned_as_null(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-014: Edge case: Null OEE and downtime are returned as null in response."""
        asset_id = str(uuid4())
        _make_table_mock(mock_supabase_client, {
            "assets": [{"id": asset_id, "name": "Sparse Asset", "area": "Roasting"}],
            "daily_summaries": [{"asset_id": asset_id, "units_produced": 50, "oee": None, "downtime_minutes": None}],
            "shift_targets": [{"asset_id": asset_id, "target_units": 100}],
        })

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        asset = data["workcenters"][0]["assets"][0]
        assert asset["oee"] is None
        assert asset["downtime_minutes"] is None

    def test_supabase_error_returns_500(self, client, mock_verify_jwt, mock_supabase_client):
        """11-1-UNIT-015: Error handling: Supabase query failure returns 500 with generic message."""
        mock_supabase_client.table.side_effect = Exception("Connection refused")

        response = client.get(
            "/api/v1/production/workcenter-summary?date=2026-02-10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch workcenter summary data"
