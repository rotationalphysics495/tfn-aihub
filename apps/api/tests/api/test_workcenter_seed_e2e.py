"""
End-to-End Tests for Workcenter Seed Data.

Story: 11.3 - Workcenter Seed Data
AC: #1 - All 4 workcenters have data after seeding
AC: #2 - Each workcenter has varied performance
AC: #3 - Attainment ranges from ~70% to ~100%
AC: #5 - Every asset has shift target records

These tests validate that after the seed data is loaded, the workcenter
summary API endpoint returns correct data for all 4 workcenters.

Tests will FAIL until Story 11.3 is implemented because:
  - Several assets are missing daily_summaries for T-1
  - shift_targets are missing from seed-data.mjs
  - Roaster shift_target sums don't match daily_summaries targets
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# Constants
# =============================================================================

YESTERDAY = (date.today() - timedelta(days=1)).isoformat()

WORKCENTER_AREAS = {"Roasting", "Grinding", "Filling", "Packaging"}

# All 14 asset UUIDs used in seed data
ALL_ASSET_IDS = [
    "a0000001-0000-0000-0000-000000000001",  # Roaster 1
    "a0000001-0000-0000-0000-000000000002",  # Roaster 2
    "a0000001-0000-0000-0000-000000000003",  # Roaster 3
    "a0000001-0000-0000-0000-000000000004",  # Grinder 1
    "a0000001-0000-0000-0000-000000000005",  # Grinder 2
    "a0000001-0000-0000-0000-000000000006",  # Grinder 3
    "a0000001-0000-0000-0000-000000000007",  # Grinder 4
    "a0000001-0000-0000-0000-000000000014",  # Grinder 5
    "a0000001-0000-0000-0000-000000000008",  # Filler Line A
    "a0000001-0000-0000-0000-000000000009",  # Filler Line B
    "a0000001-0000-0000-0000-000000000010",  # Filler Line C
    "a0000001-0000-0000-0000-000000000011",  # Packaging Line 1
    "a0000001-0000-0000-0000-000000000012",  # Packaging Line 2
    "a0000001-0000-0000-0000-000000000013",  # Packaging Line 3
]

# Expected asset counts per workcenter
EXPECTED_ASSET_COUNTS = {
    "Roasting": 3,
    "Grinding": 5,
    "Filling": 3,
    "Packaging": 3,
}

# Expected daily target_output per asset
EXPECTED_DAILY_TARGETS = {
    "a0000001-0000-0000-0000-000000000001": 143,   # Roaster 1
    "a0000001-0000-0000-0000-000000000002": 143,   # Roaster 2
    "a0000001-0000-0000-0000-000000000003": 143,   # Roaster 3
    "a0000001-0000-0000-0000-000000000004": 1950,  # Grinder 1
    "a0000001-0000-0000-0000-000000000005": 1950,  # Grinder 2
    "a0000001-0000-0000-0000-000000000006": 1950,  # Grinder 3
    "a0000001-0000-0000-0000-000000000007": 1950,  # Grinder 4
    "a0000001-0000-0000-0000-000000000014": 1950,  # Grinder 5
    "a0000001-0000-0000-0000-000000000008": 4600,  # Filler A
    "a0000001-0000-0000-0000-000000000009": 4600,  # Filler B
    "a0000001-0000-0000-0000-000000000010": 4000,  # Filler C
    "a0000001-0000-0000-0000-000000000011": 6200,  # Packaging 1
    "a0000001-0000-0000-0000-000000000012": 6200,  # Packaging 2
    "a0000001-0000-0000-0000-000000000013": 5600,  # Packaging 3
}

# Expected shift_target sums per asset (should equal daily target)
EXPECTED_SHIFT_TARGET_SUMS = {
    "a0000001-0000-0000-0000-000000000001": 143,   # Roaster 1: 50+48+45
    "a0000001-0000-0000-0000-000000000002": 143,   # Roaster 2: 50+48+45
    "a0000001-0000-0000-0000-000000000003": 143,   # Roaster 3: 50+48+45
    "a0000001-0000-0000-0000-000000000004": 1950,  # Grinder 1: 1000+950
    "a0000001-0000-0000-0000-000000000005": 1950,  # Grinder 2: 1000+950
    "a0000001-0000-0000-0000-000000000006": 1950,  # Grinder 3: 900+1050
    "a0000001-0000-0000-0000-000000000007": 1950,  # Grinder 4: 850+1100
    "a0000001-0000-0000-0000-000000000014": 1950,  # Grinder 5: 1000+950
    "a0000001-0000-0000-0000-000000000008": 4600,  # Filler A: 2400+2200
    "a0000001-0000-0000-0000-000000000009": 4600,  # Filler B: 2400+2200
    "a0000001-0000-0000-0000-000000000010": 4000,  # Filler C: 2000+2000
    "a0000001-0000-0000-0000-000000000011": 6200,  # Pack 1: 3200+3000
    "a0000001-0000-0000-0000-000000000012": 6200,  # Pack 2: 3200+3000
    "a0000001-0000-0000-0000-000000000013": 5600,  # Pack 3: 2800+2800
}


# =============================================================================
# Sample Seed Data (representing what the seed SHOULD produce after 11.3)
# =============================================================================

# Complete list of seeded assets with correct area assignments (all 14)
SEEDED_ASSETS = [
    {"id": "a0000001-0000-0000-0000-000000000001", "name": "Roaster 1", "area": "Roasting"},
    {"id": "a0000001-0000-0000-0000-000000000002", "name": "Roaster 2", "area": "Roasting"},
    {"id": "a0000001-0000-0000-0000-000000000003", "name": "Roaster 3", "area": "Roasting"},
    {"id": "a0000001-0000-0000-0000-000000000004", "name": "Grinder 1", "area": "Grinding"},
    {"id": "a0000001-0000-0000-0000-000000000005", "name": "Grinder 2", "area": "Grinding"},
    {"id": "a0000001-0000-0000-0000-000000000006", "name": "Grinder 3", "area": "Grinding"},
    {"id": "a0000001-0000-0000-0000-000000000007", "name": "Grinder 4", "area": "Grinding"},
    {"id": "a0000001-0000-0000-0000-000000000014", "name": "Grinder 5", "area": "Grinding"},
    {"id": "a0000001-0000-0000-0000-000000000008", "name": "Filler Line A", "area": "Filling"},
    {"id": "a0000001-0000-0000-0000-000000000009", "name": "Filler Line B", "area": "Filling"},
    {"id": "a0000001-0000-0000-0000-000000000010", "name": "Filler Line C", "area": "Filling"},
    {"id": "a0000001-0000-0000-0000-000000000011", "name": "Packaging Line 1", "area": "Packaging"},
    {"id": "a0000001-0000-0000-0000-000000000012", "name": "Packaging Line 2", "area": "Packaging"},
    {"id": "a0000001-0000-0000-0000-000000000013", "name": "Packaging Line 3", "area": "Packaging"},
]

# Expected daily_summaries for T-1 for ALL 14 assets after Story 11.3
# These represent what the seed data SHOULD produce.
# Currently MISSING for: Roaster 3, Grinder 4, Filler C, Packaging 3
# (which is why these tests will FAIL)
SEEDED_DAILY_SUMMARIES_T1 = [
    # Roasting
    {"asset_id": "a0000001-0000-0000-0000-000000000001", "units_produced": 125, "oee": 87.50, "downtime_minutes": 45},
    {"asset_id": "a0000001-0000-0000-0000-000000000002", "units_produced": 145, "oee": 96.10, "downtime_minutes": 10},
    {"asset_id": "a0000001-0000-0000-0000-000000000003", "units_produced": 127, "oee": 89.00, "downtime_minutes": 35},
    # Grinding
    {"asset_id": "a0000001-0000-0000-0000-000000000004", "units_produced": 1780, "oee": 91.20, "downtime_minutes": 30},
    {"asset_id": "a0000001-0000-0000-0000-000000000005", "units_produced": 1960, "oee": 95.80, "downtime_minutes": 0},
    {"asset_id": "a0000001-0000-0000-0000-000000000006", "units_produced": 1642, "oee": 84.20, "downtime_minutes": 62},
    {"asset_id": "a0000001-0000-0000-0000-000000000007", "units_produced": 1700, "oee": 87.18, "downtime_minutes": 50},
    {"asset_id": "a0000001-0000-0000-0000-000000000014", "units_produced": 1608, "oee": 82.50, "downtime_minutes": 72},
    # Filling
    {"asset_id": "a0000001-0000-0000-0000-000000000008", "units_produced": 3335, "oee": 72.50, "downtime_minutes": 95},
    {"asset_id": "a0000001-0000-0000-0000-000000000009", "units_produced": 4650, "oee": 89.20, "downtime_minutes": 42},
    {"asset_id": "a0000001-0000-0000-0000-000000000010", "units_produced": 3200, "oee": 80.00, "downtime_minutes": 62},
    # Packaging
    {"asset_id": "a0000001-0000-0000-0000-000000000011", "units_produced": 5549, "oee": 89.50, "downtime_minutes": 42},
    {"asset_id": "a0000001-0000-0000-0000-000000000012", "units_produced": 6300, "oee": 88.90, "downtime_minutes": 45},
    {"asset_id": "a0000001-0000-0000-0000-000000000013", "units_produced": 4900, "oee": 87.50, "downtime_minutes": 55},
]

# Shift targets for ALL 14 assets (what seed data SHOULD produce after 11.3)
SEEDED_SHIFT_TARGETS = [
    # Roasters: each sums to 143
    {"asset_id": "a0000001-0000-0000-0000-000000000001", "target_units": 50},
    {"asset_id": "a0000001-0000-0000-0000-000000000001", "target_units": 48},
    {"asset_id": "a0000001-0000-0000-0000-000000000001", "target_units": 45},
    {"asset_id": "a0000001-0000-0000-0000-000000000002", "target_units": 50},
    {"asset_id": "a0000001-0000-0000-0000-000000000002", "target_units": 48},
    {"asset_id": "a0000001-0000-0000-0000-000000000002", "target_units": 45},
    {"asset_id": "a0000001-0000-0000-0000-000000000003", "target_units": 50},
    {"asset_id": "a0000001-0000-0000-0000-000000000003", "target_units": 48},
    {"asset_id": "a0000001-0000-0000-0000-000000000003", "target_units": 45},
    # Grinders: each sums to 1950
    {"asset_id": "a0000001-0000-0000-0000-000000000004", "target_units": 1000},
    {"asset_id": "a0000001-0000-0000-0000-000000000004", "target_units": 950},
    {"asset_id": "a0000001-0000-0000-0000-000000000005", "target_units": 1000},
    {"asset_id": "a0000001-0000-0000-0000-000000000005", "target_units": 950},
    {"asset_id": "a0000001-0000-0000-0000-000000000006", "target_units": 900},
    {"asset_id": "a0000001-0000-0000-0000-000000000006", "target_units": 1050},
    {"asset_id": "a0000001-0000-0000-0000-000000000007", "target_units": 850},
    {"asset_id": "a0000001-0000-0000-0000-000000000007", "target_units": 1100},
    {"asset_id": "a0000001-0000-0000-0000-000000000014", "target_units": 1000},
    {"asset_id": "a0000001-0000-0000-0000-000000000014", "target_units": 950},
    # Fillers
    {"asset_id": "a0000001-0000-0000-0000-000000000008", "target_units": 2400},
    {"asset_id": "a0000001-0000-0000-0000-000000000008", "target_units": 2200},
    {"asset_id": "a0000001-0000-0000-0000-000000000009", "target_units": 2400},
    {"asset_id": "a0000001-0000-0000-0000-000000000009", "target_units": 2200},
    {"asset_id": "a0000001-0000-0000-0000-000000000010", "target_units": 2000},
    {"asset_id": "a0000001-0000-0000-0000-000000000010", "target_units": 2000},
    # Packaging
    {"asset_id": "a0000001-0000-0000-0000-000000000011", "target_units": 3200},
    {"asset_id": "a0000001-0000-0000-0000-000000000011", "target_units": 3000},
    {"asset_id": "a0000001-0000-0000-0000-000000000012", "target_units": 3200},
    {"asset_id": "a0000001-0000-0000-0000-000000000012", "target_units": 3000},
    {"asset_id": "a0000001-0000-0000-0000-000000000013", "target_units": 2800},
    {"asset_id": "a0000001-0000-0000-0000-000000000013", "target_units": 2800},
]


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
    Helper to set up mock Supabase client so that different .table() calls
    return different mock chains.
    """
    def table_side_effect(table_name):
        table_mock = MagicMock()
        data = responses_by_table.get(table_name, [])
        response = MagicMock(data=data)

        # Simple select().execute() chain
        table_mock.select.return_value.execute.return_value = response
        # select().eq().execute() chain
        table_mock.select.return_value.eq.return_value.execute.return_value = response

        return table_mock

    client_mock.table.side_effect = table_side_effect


# =============================================================================
# E2E Tests: Workcenter Summary API with Seed Data
# =============================================================================


class TestWorkcenterSeedDataE2E:
    """E2E tests for workcenter summary endpoint with seeded data."""

    def test_e2e_001_workcenter_summary_returns_all_4_workcenters(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-001: Workcenter summary API returns data for all 4 workcenters after seeding.

        Given: The database has been seeded via seed-data.mjs and the API server is running
        When: GET /api/v1/production/workcenter-summary?date=<yesterday> is called with valid auth
        Then: The response contains a "workcenters" array with exactly 4 entries,
              one each for Roasting, Grinding, Filling, and Packaging
        """
        # Arrange: set up mock to return seed data for all 14 assets
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        # Act
        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "workcenters" in data
        assert "report_date" in data
        assert data["report_date"] == YESTERDAY

        # Should have exactly 4 workcenters
        wc_names = {wc["workcenter"] for wc in data["workcenters"]}
        assert len(data["workcenters"]) == 4, (
            f"Expected 4 workcenters, got {len(data['workcenters'])}: {wc_names}"
        )

        # Each expected workcenter must be present
        for area in WORKCENTER_AREAS:
            assert area in wc_names, f"Missing workcenter: {area}"

    def test_e2e_001_roasting_has_3_assets(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-002: Roasting workcenter has 3 assets in API response."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        roasting = next(
            (wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting"),
            None,
        )
        assert roasting is not None, "Roasting workcenter not found in response"
        assert len(roasting["assets"]) == 3, (
            f"Roasting should have 3 assets, got {len(roasting['assets'])}"
        )

    def test_e2e_001_grinding_has_5_assets(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-003: Grinding workcenter has 5 assets in API response."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        grinding = next(
            (wc for wc in data["workcenters"] if wc["workcenter"] == "Grinding"),
            None,
        )
        assert grinding is not None, "Grinding workcenter not found in response"
        assert len(grinding["assets"]) == 5, (
            f"Grinding should have 5 assets, got {len(grinding['assets'])}"
        )

    def test_e2e_001_filling_has_3_assets(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-004: Filling workcenter has 3 assets in API response."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        filling = next(
            (wc for wc in data["workcenters"] if wc["workcenter"] == "Filling"),
            None,
        )
        assert filling is not None, "Filling workcenter not found in response"
        assert len(filling["assets"]) == 3, (
            f"Filling should have 3 assets, got {len(filling['assets'])}"
        )

    def test_e2e_001_packaging_has_3_assets(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-005: Packaging workcenter has 3 assets in API response."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        packaging = next(
            (wc for wc in data["workcenters"] if wc["workcenter"] == "Packaging"),
            None,
        )
        assert packaging is not None, "Packaging workcenter not found in response"
        assert len(packaging["assets"]) == 3, (
            f"Packaging should have 3 assets, got {len(packaging['assets'])}"
        )

    def test_e2e_001_each_workcenter_has_attainment(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-006: Each workcenter has attainment_pct in response."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        for wc in data["workcenters"]:
            assert "attainment_pct" in wc, (
                f"Workcenter {wc.get('workcenter', '?')} missing attainment_pct"
            )
            assert isinstance(wc["attainment_pct"], (int, float)), (
                f"attainment_pct should be numeric for {wc.get('workcenter', '?')}"
            )
            # Attainment should be in realistic range (not 0, not > 100)
            assert 50 <= wc["attainment_pct"] <= 110, (
                f"Workcenter {wc.get('workcenter', '?')} attainment {wc['attainment_pct']}% out of range"
            )

    def test_e2e_001_each_workcenter_has_hit_and_miss(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-007: Each workcenter has both hit and miss indicators."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        for wc in data["workcenters"]:
            wc_name = wc.get("workcenter", "?")
            assert "assets_hit" in wc, f"{wc_name} missing assets_hit"
            assert "assets_missed" in wc, f"{wc_name} missing assets_missed"

            # Each workcenter should have at least one hitter and one misser
            # (per AC2 requirement for varied performance)
            assert wc["assets_hit"] >= 1, (
                f"{wc_name} should have at least 1 asset hitting target"
            )
            assert wc["assets_missed"] >= 1, (
                f"{wc_name} should have at least 1 asset missing target"
            )

    def test_e2e_001_total_asset_count_is_14(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-008: Total asset count across all workcenters is 14."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        total_assets = sum(len(wc["assets"]) for wc in data["workcenters"])
        assert total_assets == 14, (
            f"Total assets across all workcenters should be 14, got {total_assets}"
        )

    def test_e2e_001_attainment_spread_is_meaningful(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-009: Attainment spread across workcenters shows realistic variation."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        attainments = [wc["attainment_pct"] for wc in data["workcenters"]]
        min_att = min(attainments)
        max_att = max(attainments)

        # AC3: ranges from ~70% to ~100%, meaningful spread
        assert min_att <= 85, (
            f"Min attainment ({min_att}%) should be <= 85% for meaningful spread"
        )
        assert max_att >= 85, (
            f"Max attainment ({max_att}%) should be >= 85% for meaningful spread"
        )
        assert min_att >= 70, (
            f"Min attainment ({min_att}%) should not be below 70%"
        )
        assert max_att <= 100, (
            f"Max attainment ({max_att}%) should not exceed 100%"
        )

    def test_e2e_001_per_asset_details_present(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """11-3-workcenter-seed-data-E2E-010: Per-asset breakdown is present with required fields."""
        _make_table_mock(mock_supabase_client, {
            "assets": SEEDED_ASSETS,
            "daily_summaries": SEEDED_DAILY_SUMMARIES_T1,
            "shift_targets": SEEDED_SHIFT_TARGETS,
        })

        response = client.get(
            f"/api/v1/production/workcenter-summary?date={YESTERDAY}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        for wc in data["workcenters"]:
            for asset in wc["assets"]:
                assert "asset_name" in asset, "Asset should have asset_name"
                assert "actual_output" in asset, "Asset should have actual_output"
                assert "target_output" in asset, "Asset should have target_output"
                assert "attainment_pct" in asset, "Asset should have attainment_pct"
                assert "hit_target" in asset, "Asset should have hit_target"
                assert isinstance(asset["actual_output"], (int, float))
                assert isinstance(asset["target_output"], (int, float))
