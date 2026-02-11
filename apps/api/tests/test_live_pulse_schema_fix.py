"""
Tests for Story 10.2: Live Pulse Schema Fix

Verifies that the live_pulse.py endpoint queries only columns that exist
in the live_snapshots table, handles missing OEE data gracefully, and
returns correct aggregated production/financial data.

Test IDs: 10-2-live-pulse-schema-fix-UNIT-001 through UNIT-005
          10-2-live-pulse-schema-fix-INT-001 through INT-020

These tests are written TDD-style and should FAIL until the feature code
is corrected to remove non-existent columns from the Supabase select query.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# =============================================================================
# Valid live_snapshots columns (from migrations 0003 + 0022)
# =============================================================================

VALID_LIVE_SNAPSHOT_COLUMNS = {
    "id",
    "asset_id",
    "snapshot_timestamp",
    "current_output",
    "target_output",
    "output_variance",
    "status",
    "created_at",
    "financial_loss_dollars",
}

# Columns that should NOT appear in the select query
INVALID_COLUMNS = {"oee_percentage", "downtime_reason", "downtime_minutes"}


# =============================================================================
# Test Data Factories
# =============================================================================


def make_snapshot(
    snap_id="snap-001",
    asset_id="asset-001",
    minutes_ago=5,
    current_output=1500,
    target_output=1800,
    status="below_target",
    financial_loss_dollars=250.00,
    include_oee=False,
    oee_value=None,
    include_downtime=False,
    downtime_reason=None,
    downtime_minutes=None,
):
    """Factory for creating mock snapshot dicts with only valid columns."""
    snapshot = {
        "id": snap_id,
        "asset_id": asset_id,
        "snapshot_timestamp": (
            datetime.utcnow() - timedelta(minutes=minutes_ago)
        ).isoformat() + "Z",
        "current_output": current_output,
        "target_output": target_output,
        "status": status,
        "financial_loss_dollars": financial_loss_dollars,
    }
    if include_oee:
        snapshot["oee_percentage"] = oee_value
    if include_downtime:
        snapshot["downtime_reason"] = downtime_reason
        snapshot["downtime_minutes"] = downtime_minutes
    return snapshot


def make_assets(count=3):
    """Factory for creating mock asset records."""
    assets = [
        {"id": "asset-001", "name": "Grinder 01", "area": "Machining", "source_id": "GRINDER_01"},
        {"id": "asset-002", "name": "Grinder 02", "area": "Machining", "source_id": "GRINDER_02"},
        {"id": "asset-003", "name": "Press 01", "area": "Forming", "source_id": "PRESS_01"},
    ]
    return assets[:count]


def make_cost_centers():
    """Factory for creating mock cost center records."""
    return [
        {"asset_id": "asset-001", "standard_hourly_rate": 500.00, "cost_per_unit": 2.50},
        {"asset_id": "asset-002", "standard_hourly_rate": 450.00, "cost_per_unit": 2.25},
    ]


def build_mock_supabase(snapshots, assets=None, cost_centers=None, safety_events=None):
    """Build a mock Supabase client with table side_effect routing.

    The returned mock has a `_captured_select_args` dict that records the
    positional arguments passed to `.select()` for each table name, so that
    unit tests can inspect which columns were queried.
    """
    if assets is None:
        assets = make_assets()
    if cost_centers is None:
        cost_centers = make_cost_centers()
    if safety_events is None:
        safety_events = []

    mock_supabase = MagicMock()
    # Store captured select() call args keyed by table name
    mock_supabase._captured_select_args = {}

    def table_side_effect(table_name):
        mock_table = MagicMock()

        if table_name == "assets":
            # Build the return chain first
            select_return = MagicMock()
            select_return.execute.return_value.data = assets

            def assets_select(*args, **kwargs):
                mock_supabase._captured_select_args[table_name] = args[0] if args else ""
                return select_return

            mock_table.select = MagicMock(side_effect=assets_select)
        elif table_name == "cost_centers":
            select_return = MagicMock()
            select_return.execute.return_value.data = cost_centers

            def cc_select(*args, **kwargs):
                mock_supabase._captured_select_args[table_name] = args[0] if args else ""
                return select_return

            mock_table.select = MagicMock(side_effect=cc_select)
        elif table_name == "live_snapshots":
            mock_chain = MagicMock()
            mock_chain.order.return_value.execute.return_value.data = snapshots

            def ls_select(*args, **kwargs):
                mock_supabase._captured_select_args[table_name] = args[0] if args else ""
                return mock_chain

            mock_table.select = MagicMock(side_effect=ls_select)
        elif table_name == "safety_events":
            select_return = MagicMock()
            select_return.eq.return_value.execute.return_value.data = safety_events

            def se_select(*args, **kwargs):
                mock_supabase._captured_select_args[table_name] = args[0] if args else ""
                return select_return

            mock_table.select = MagicMock(side_effect=se_select)
        return mock_table

    mock_supabase.table.side_effect = table_side_effect
    return mock_supabase


def get_select_string(mock_supabase, table_name="live_snapshots"):
    """Extract the captured select() string for the given table."""
    return mock_supabase._captured_select_args.get(table_name)


# =============================================================================
# AC1: Successful API Response
# =============================================================================


class TestSuccessfulApiResponse:
    """AC1: Endpoint returns 200 with corrected query columns."""

    def test_INT_001_endpoint_returns_200_with_corrected_query_columns(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-001:
        Given: Authenticated user, snapshots with only valid columns
        When: GET /api/live-pulse
        Then: 200 with timestamp, production, financial, safety, meta keys
        """
        # Given: 3 snapshots with only columns that exist in live_snapshots
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001", current_output=1500,
                          target_output=1800, status="below_target", financial_loss_dollars=250.00),
            make_snapshot(snap_id="snap-002", asset_id="asset-002", current_output=2000,
                          target_output=1800, status="above_target", financial_loss_dollars=0.00),
            make_snapshot(snap_id="snap-003", asset_id="asset-003", current_output=800,
                          target_output=1000, status="on_target", financial_loss_dollars=150.00),
        ]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "production" in data
        assert "financial" in data
        assert "safety" in data
        assert "meta" in data

    def test_INT_002_no_500_when_oee_percentage_absent(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-002:
        Given: Snapshots do NOT include oee_percentage key
        When: GET /api/live-pulse
        Then: 200 (not 500), production.oee_percentage defaults to 0.0
        """
        # Given: snapshots without oee_percentage
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001"),
            make_snapshot(snap_id="snap-002", asset_id="asset-002"),
            make_snapshot(snap_id="snap-003", asset_id="asset-003"),
        ]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then: Must be 200, not 500
        assert response.status_code == 200
        data = response.json()
        assert data["production"]["oee_percentage"] == 0.0

    def test_INT_003_production_data_structure_on_success(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-003:
        Given: 2 assets with known output values
        When: GET /api/live-pulse
        Then: production contains current_output, target_output, output_percentage,
              oee_percentage, machine_status, active_downtime
        """
        # Given: 2 snapshots with known values
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          current_output=1500, target_output=1800,
                          status="below_target", financial_loss_dollars=250.00),
            make_snapshot(snap_id="snap-002", asset_id="asset-002",
                          current_output=2000, target_output=1800,
                          status="above_target", financial_loss_dollars=0.00),
        ]
        mock_supabase = build_mock_supabase(snapshots, assets=make_assets(2))

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        production = response.json()["production"]
        assert "current_output" in production
        assert "target_output" in production
        assert "output_percentage" in production
        assert "oee_percentage" in production
        assert "machine_status" in production
        assert "active_downtime" in production


# =============================================================================
# AC2: Correct Column References
# =============================================================================


class TestCorrectColumnReferences:
    """AC2: All column references match actual live_snapshots schema."""

    def test_UNIT_001_select_query_excludes_invalid_columns(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-UNIT-001:
        Given: get_live_pulse_data() is invoked
        When: .table("live_snapshots").select(...) is called
        Then: select string does NOT contain oee_percentage, downtime_reason, downtime_minutes
        And: contains only valid live_snapshots columns
        """
        # Given
        snapshots = [make_snapshot()]
        mock_supabase = build_mock_supabase(snapshots)

        # When: call the endpoint to trigger the select
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then: inspect what was passed to select()
        select_str = get_select_string(mock_supabase)
        assert select_str is not None, "live_snapshots select was not called"

        # The select string must NOT contain invalid columns
        assert "oee_percentage" not in select_str, (
            f"oee_percentage found in select string: {select_str}"
        )
        assert "downtime_reason" not in select_str, (
            f"downtime_reason found in select string: {select_str}"
        )
        assert "downtime_minutes" not in select_str, (
            f"downtime_minutes found in select string: {select_str}"
        )

    def test_UNIT_002_select_query_only_valid_columns(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-UNIT-002:
        Given: The corrected live_pulse.py source
        When: select string is examined
        Then: Every column in the select string is from the valid set
        """
        # Given
        snapshots = [make_snapshot()]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then: parse the select string and validate each column
        select_str = get_select_string(mock_supabase)
        assert select_str is not None, "live_snapshots select was not called"

        # Parse comma-separated column names
        columns_in_query = {col.strip() for col in select_str.split(",")}

        # Every column must be in the valid set
        invalid_found = columns_in_query - VALID_LIVE_SNAPSHOT_COLUMNS
        assert not invalid_found, (
            f"Invalid columns in select query: {invalid_found}. "
            f"Full select string: {select_str}"
        )

    def test_UNIT_003_downtime_columns_not_in_select(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-UNIT-003:
        Given: The corrected get_live_pulse_data() function
        When: .table("live_snapshots").select() is inspected
        Then: downtime_reason and downtime_minutes are NOT in the select string
        """
        # Given
        snapshots = [make_snapshot()]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        select_str = get_select_string(mock_supabase)
        assert select_str is not None
        assert "downtime_reason" not in select_str
        assert "downtime_minutes" not in select_str

    def test_INT_004_response_includes_correct_status_per_asset(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-004:
        Given: 3 assets with different status values
        When: GET /api/live-pulse
        Then: machine_status.total == 3, all statuses map to running
        """
        # Given
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          status="below_target", financial_loss_dollars=250.00),
            make_snapshot(snap_id="snap-002", asset_id="asset-002",
                          status="above_target", financial_loss_dollars=0.00),
            make_snapshot(snap_id="snap-003", asset_id="asset-003",
                          status="on_target", financial_loss_dollars=150.00),
        ]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        machine_status = response.json()["production"]["machine_status"]
        assert machine_status["total"] == 3
        # All three statuses (below_target, above_target, on_target) map to running
        assert machine_status["running"] == 3

    def test_INT_005_correct_output_aggregation(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-005:
        Given: 2 assets: asset-001 (750/1000), asset-002 (1250/1000)
        When: GET /api/live-pulse
        Then: current_output=2000, target_output=2000, output_percentage=100.0
        """
        # Given
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          current_output=750, target_output=1000,
                          status="below_target", financial_loss_dollars=0.00),
            make_snapshot(snap_id="snap-002", asset_id="asset-002",
                          current_output=1250, target_output=1000,
                          status="above_target", financial_loss_dollars=0.00),
        ]
        mock_supabase = build_mock_supabase(snapshots, assets=make_assets(2))

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        production = response.json()["production"]
        assert production["current_output"] == 2000
        assert production["target_output"] == 2000
        assert production["output_percentage"] == 100.0

    def test_INT_006_correct_financial_loss_aggregation(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-006:
        Given: 3 assets with financial_loss_dollars of 250, 0, 150
        When: GET /api/live-pulse
        Then: financial.shift_to_date_loss == 400.00
        """
        # Given
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          financial_loss_dollars=250.00),
            make_snapshot(snap_id="snap-002", asset_id="asset-002",
                          financial_loss_dollars=0.00),
            make_snapshot(snap_id="snap-003", asset_id="asset-003",
                          financial_loss_dollars=150.00),
        ]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        assert response.json()["financial"]["shift_to_date_loss"] == 400.00


# =============================================================================
# AC3: OEE Calculation Graceful Handling
# =============================================================================


class TestOeeGracefulHandling:
    """AC3: OEE defaults to 0.0 when live_snapshots lacks oee_percentage column."""

    def test_UNIT_004_oee_percentage_not_in_select_string(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-UNIT-004:
        Given: The corrected get_live_pulse_data() function
        When: .table("live_snapshots").select() argument is inspected
        Then: 'oee_percentage' does not appear in the select argument
        """
        # Given
        snapshots = [make_snapshot()]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        select_str = get_select_string(mock_supabase)
        assert select_str is not None
        assert "oee_percentage" not in select_str, (
            f"oee_percentage should not be in the select query: {select_str}"
        )

    def test_INT_007_oee_defaults_to_zero_when_absent(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-007:
        Given: 3 snapshots WITHOUT oee_percentage key
        When: GET /api/live-pulse
        Then: 200, production.oee_percentage == 0.0
        """
        # Given: snapshots that simulate the real corrected query response
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001"),
            make_snapshot(snap_id="snap-002", asset_id="asset-002"),
            make_snapshot(snap_id="snap-003", asset_id="asset-003"),
        ]
        # None of these have oee_percentage key
        for s in snapshots:
            assert "oee_percentage" not in s

        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        assert response.json()["production"]["oee_percentage"] == 0.0

    def test_INT_008_oee_computed_when_present_backward_compat(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-008:
        Given: 3 snapshots WITH oee_percentage values (85.5, 92.0, 75.0)
        When: GET /api/live-pulse
        Then: production.oee_percentage ~= 84.2 (average)
        """
        # Given: snapshots that include oee_percentage (backward compat mock data)
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          include_oee=True, oee_value=85.5),
            make_snapshot(snap_id="snap-002", asset_id="asset-002",
                          include_oee=True, oee_value=92.0),
            make_snapshot(snap_id="snap-003", asset_id="asset-003",
                          include_oee=True, oee_value=75.0),
        ]
        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then: average of 85.5, 92.0, 75.0 = 84.17
        assert response.status_code == 200
        oee = response.json()["production"]["oee_percentage"]
        assert 80.0 < oee < 90.0, f"Expected OEE ~84.2, got {oee}"

    def test_INT_009_oee_defaults_when_all_none(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-009:
        Given: 2 snapshots with oee_percentage key present but value is None
        When: GET /api/live-pulse
        Then: production.oee_percentage == 0.0
        """
        # Given
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          include_oee=True, oee_value=None),
            make_snapshot(snap_id="snap-002", asset_id="asset-002",
                          include_oee=True, oee_value=None),
        ]
        mock_supabase = build_mock_supabase(snapshots, assets=make_assets(2))

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        assert response.json()["production"]["oee_percentage"] == 0.0

    def test_INT_010_oee_field_exists_as_float_with_empty_snapshots(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-010:
        Given: Empty snapshots (no data at all)
        When: GET /api/live-pulse
        Then: production.oee_percentage present and equals 0.0
        """
        # Given
        mock_supabase = build_mock_supabase(snapshots=[])

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        production = response.json()["production"]
        assert "oee_percentage" in production
        assert production["oee_percentage"] == 0.0
        assert isinstance(production["oee_percentage"], float)


# =============================================================================
# Edge Cases and Error Scenarios
# =============================================================================


class TestEdgeCasesAndErrors:
    """Edge cases and error scenarios for the schema fix."""

    def test_INT_016_empty_snapshots_returns_valid_defaults(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-016:
        Given: Empty live_snapshots table
        When: GET /api/live-pulse
        Then: 200 with zero/default values for all fields
        """
        # Given
        mock_supabase = build_mock_supabase(snapshots=[], assets=make_assets())

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["production"]["current_output"] == 0
        assert data["production"]["target_output"] == 0
        assert data["production"]["oee_percentage"] == 0.0
        assert data["production"]["active_downtime"] == []
        assert data["financial"]["shift_to_date_loss"] == 0

    def test_INT_017_active_downtime_empty_when_columns_absent(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-017:
        Given: 3 snapshots WITHOUT downtime_reason or downtime_minutes keys
        When: GET /api/live-pulse
        Then: production.active_downtime is empty list, no error raised
        """
        # Given: snapshots without downtime columns (reflecting corrected query)
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001"),
            make_snapshot(snap_id="snap-002", asset_id="asset-002"),
            make_snapshot(snap_id="snap-003", asset_id="asset-003"),
        ]
        # Verify no downtime keys present
        for s in snapshots:
            assert "downtime_reason" not in s
            assert "downtime_minutes" not in s

        mock_supabase = build_mock_supabase(snapshots)

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        assert response.json()["production"]["active_downtime"] == []

    def test_INT_018_active_downtime_populated_when_present_backward_compat(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-018:
        Given: A snapshot WITH downtime_reason="Mechanical Failure" and downtime_minutes=30
        When: GET /api/live-pulse
        Then: active_downtime contains entry with reason_code and duration_minutes
        """
        # Given: snapshot with downtime data (even though columns don't exist in real table)
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          include_downtime=True,
                          downtime_reason="Mechanical Failure",
                          downtime_minutes=30,
                          status="below_target"),
        ]
        mock_supabase = build_mock_supabase(snapshots, assets=make_assets(1))

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 200
        downtime = response.json()["production"]["active_downtime"]
        assert len(downtime) >= 1
        assert downtime[0]["reason_code"] == "Mechanical Failure"
        assert downtime[0]["duration_minutes"] == 30

    def test_INT_019_database_exception_returns_500(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-019:
        Given: get_supabase_client() raises Exception
        When: GET /api/live-pulse
        Then: 500 with "Failed to fetch live pulse data"
        """
        # Given
        with patch(
            "app.api.live_pulse.get_supabase_client",
            side_effect=Exception("DB connection failed"),
        ):
            # When
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then
        assert response.status_code == 500
        assert "Failed to fetch live pulse data" in response.json()["detail"]

    def test_INT_020_multiple_snapshots_per_asset_uses_latest(
        self, client, mock_verify_jwt
    ):
        """
        10-2-live-pulse-schema-fix-INT-020:
        Given: 4 snapshots for 2 assets (2 each), ordered by timestamp desc
        When: GET /api/live-pulse
        Then: Only latest snapshot per asset is used; total = 500 + 700 = 1200
        """
        # Given: snapshots ordered desc by timestamp (newer first)
        snapshots = [
            make_snapshot(snap_id="snap-001", asset_id="asset-001",
                          minutes_ago=2, current_output=500, target_output=600,
                          financial_loss_dollars=0.00),
            make_snapshot(snap_id="snap-003", asset_id="asset-002",
                          minutes_ago=2, current_output=700, target_output=800,
                          financial_loss_dollars=0.00),
            make_snapshot(snap_id="snap-002", asset_id="asset-001",
                          minutes_ago=10, current_output=300, target_output=600,
                          financial_loss_dollars=0.00),
            make_snapshot(snap_id="snap-004", asset_id="asset-002",
                          minutes_ago=10, current_output=400, target_output=800,
                          financial_loss_dollars=0.00),
        ]
        mock_supabase = build_mock_supabase(snapshots, assets=make_assets(2))

        # When
        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"},
            )

        # Then: only latest per asset: 500 + 700 = 1200
        assert response.status_code == 200
        production = response.json()["production"]
        assert production["current_output"] == 1200

    def test_UNIT_005_snapshot_get_safely_handles_missing_keys(self):
        """
        10-2-live-pulse-schema-fix-UNIT-005:
        Given: A snapshot dict with only valid corrected-query columns
        When: .get("oee_percentage"), .get("downtime_reason"), .get("downtime_minutes") called
        Then: All return None without KeyError
        """
        # Given: dict with only the 7 corrected columns
        snapshot = {
            "id": "snap-001",
            "asset_id": "asset-001",
            "snapshot_timestamp": datetime.utcnow().isoformat() + "Z",
            "current_output": 1500,
            "target_output": 1800,
            "status": "below_target",
            "financial_loss_dollars": 250.00,
        }

        # When / Then: .get() returns None, no KeyError
        assert snapshot.get("oee_percentage") is None
        assert snapshot.get("downtime_reason") is None
        assert snapshot.get("downtime_minutes") is None
