"""
Tests for Live Pulse Ticker API Endpoint.

Story: 2.9 - Live Pulse Ticker
Tests cover:
AC#2 - Production Status Display
AC#3 - Financial Context Integration
AC#4 - Safety Alert Integration
AC#5 - Data Source Integration
AC#6 - Performance Requirements
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# =============================================================================
# Test Data
# =============================================================================


SAMPLE_ASSETS = [
    {
        "id": "asset-001",
        "name": "Grinder 01",
        "area": "Machining",
        "source_id": "GRINDER_01",
    },
    {
        "id": "asset-002",
        "name": "Grinder 02",
        "area": "Machining",
        "source_id": "GRINDER_02",
    },
    {
        "id": "asset-003",
        "name": "Press 01",
        "area": "Forming",
        "source_id": "PRESS_01",
    },
]

SAMPLE_COST_CENTERS = [
    {
        "asset_id": "asset-001",
        "standard_hourly_rate": 500.00,
        "cost_per_unit": 2.50,
    },
    {
        "asset_id": "asset-002",
        "standard_hourly_rate": 450.00,
        "cost_per_unit": 2.25,
    },
]

SAMPLE_LIVE_SNAPSHOTS = [
    {
        "id": "snap-001",
        "asset_id": "asset-001",
        "snapshot_timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
        "current_output": 1500,
        "target_output": 1800,
        "oee_percentage": 85.5,
        "status": "below_target",
        "financial_loss_dollars": 250.00,
        "downtime_reason": None,
    },
    {
        "id": "snap-002",
        "asset_id": "asset-002",
        "snapshot_timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
        "current_output": 2000,
        "target_output": 1800,
        "oee_percentage": 92.0,
        "status": "above_target",
        "financial_loss_dollars": 0.00,
        "downtime_reason": None,
    },
    {
        "id": "snap-003",
        "asset_id": "asset-003",
        "snapshot_timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
        "current_output": 800,
        "target_output": 1000,
        "oee_percentage": 75.0,
        "status": "below_target",
        "financial_loss_dollars": 150.00,
        "downtime_reason": "Mechanical Failure",
    },
]

SAMPLE_SAFETY_EVENTS = [
    {
        "id": "safety-001",
        "asset_id": "asset-001",
        "event_timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        "reason_code": "Safety Issue",
        "severity": "high",
        "acknowledged": False,
    },
]


# =============================================================================
# API Tests
# =============================================================================


class TestLivePulseEndpoint:
    """Tests for GET /api/live-pulse endpoint."""

    def test_endpoint_requires_authentication(self, client):
        """Endpoint requires valid JWT token."""
        response = client.get("/api/live-pulse")
        assert response.status_code == 401  # HTTPBearer returns 401 for missing auth

    def test_returns_live_pulse_data(self, client, mock_verify_jwt):
        """AC#5: Returns aggregated live pulse data from multiple sources."""
        mock_supabase = MagicMock()

        # Mock assets table
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = SAMPLE_ASSETS

        # Use side_effect to return different data for different tables
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_COST_CENTERS
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "timestamp" in data
        assert "production" in data
        assert "financial" in data
        assert "safety" in data
        assert "meta" in data

    def test_production_data_structure(self, client, mock_verify_jwt):
        """AC#2: Production data includes throughput, OEE, machine status."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_COST_CENTERS
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        production = response.json()["production"]

        # AC#2: Throughput vs target
        assert "current_output" in production
        assert "target_output" in production
        assert "output_percentage" in production

        # AC#2: OEE metric
        assert "oee_percentage" in production

        # AC#2: Machine status breakdown
        assert "machine_status" in production
        assert "running" in production["machine_status"]
        assert "idle" in production["machine_status"]
        assert "down" in production["machine_status"]
        assert "total" in production["machine_status"]

        # AC#2: Active downtime events
        assert "active_downtime" in production

    def test_financial_data_structure(self, client, mock_verify_jwt):
        """AC#3: Financial data includes shift-to-date and rolling 15-min loss."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_COST_CENTERS
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        financial = response.json()["financial"]

        # AC#3: Financial context
        assert "shift_to_date_loss" in financial
        assert "rolling_15_min_loss" in financial
        assert "currency" in financial
        assert financial["currency"] == "USD"

    def test_safety_data_with_active_incidents(self, client, mock_verify_jwt):
        """AC#4: Safety data includes active incidents."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_COST_CENTERS
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = SAMPLE_SAFETY_EVENTS
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        safety = response.json()["safety"]

        # AC#4: Safety alert data
        assert "has_active_incident" in safety
        assert safety["has_active_incident"] is True
        assert "active_incidents" in safety
        assert len(safety["active_incidents"]) == 1
        assert safety["active_incidents"][0]["severity"] == "high"

    def test_safety_data_no_incidents(self, client, mock_verify_jwt):
        """AC#4: Safety data correctly indicates no active incidents."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = []
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        safety = response.json()["safety"]

        assert safety["has_active_incident"] is False
        assert safety["active_incidents"] == []

    def test_meta_data_freshness(self, client, mock_verify_jwt):
        """AC#5: Meta data includes data age and staleness flag."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = []
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        meta = response.json()["meta"]

        # AC#5: Data freshness metadata
        assert "data_age" in meta
        assert "is_stale" in meta
        assert isinstance(meta["data_age"], int)
        assert isinstance(meta["is_stale"], bool)

    def test_stale_data_detection(self, client, mock_verify_jwt):
        """AC#5: Data older than 20 minutes is marked as stale."""
        mock_supabase = MagicMock()

        # Create snapshots that are > 20 minutes old
        stale_snapshots = [
            {
                "id": "snap-001",
                "asset_id": "asset-001",
                "snapshot_timestamp": (datetime.utcnow() - timedelta(minutes=25)).isoformat() + "Z",
                "current_output": 1500,
                "target_output": 1800,
                "oee_percentage": 85.5,
                "status": "below_target",
                "financial_loss_dollars": 250.00,
                "downtime_reason": None,
            },
        ]

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = []
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = stale_snapshots
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        meta = response.json()["meta"]

        # Data > 20 min old should be marked stale
        assert meta["is_stale"] is True
        assert meta["data_age"] >= 1200  # 20 minutes in seconds

    def test_handles_empty_snapshots(self, client, mock_verify_jwt):
        """AC#6: Handles case with no live snapshot data gracefully."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = []
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = []
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        # Should still return 200 with zero values
        assert response.status_code == 200
        data = response.json()

        assert data["production"]["current_output"] == 0
        assert data["production"]["target_output"] == 0
        assert data["financial"]["shift_to_date_loss"] == 0

    def test_handles_database_error(self, client, mock_verify_jwt):
        """AC#6: Returns 500 on database error."""
        with patch("app.api.live_pulse.get_supabase_client", side_effect=Exception("DB Error")):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 500
        assert "Failed to fetch live pulse data" in response.json()["detail"]


# =============================================================================
# Data Calculation Tests
# =============================================================================


class TestDataCalculations:
    """Tests for data aggregation and calculation logic."""

    def test_output_percentage_calculation(self, client, mock_verify_jwt):
        """AC#2: Output percentage calculated correctly."""
        mock_supabase = MagicMock()

        # Snapshots with known values for calculation check
        test_snapshots = [
            {
                "id": "snap-001",
                "asset_id": "asset-001",
                "snapshot_timestamp": datetime.utcnow().isoformat() + "Z",
                "current_output": 750,
                "target_output": 1000,
                "oee_percentage": 80.0,
                "status": "below_target",
                "financial_loss_dollars": 0,
                "downtime_reason": None,
            },
        ]

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = [SAMPLE_ASSETS[0]]
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = []
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = test_snapshots
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        production = response.json()["production"]

        # 750 / 1000 * 100 = 75%
        assert production["output_percentage"] == 75.0

    def test_financial_loss_aggregation(self, client, mock_verify_jwt):
        """AC#3: Financial loss aggregated correctly across assets."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_COST_CENTERS
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        financial = response.json()["financial"]

        # Total loss from sample data: 250 + 0 + 150 = 400
        assert financial["shift_to_date_loss"] == 400.00

    def test_machine_status_counting(self, client, mock_verify_jwt):
        """AC#2: Machine status breakdown counted correctly."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = []
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        machine_status = response.json()["production"]["machine_status"]

        # Total from SAMPLE_ASSETS
        assert machine_status["total"] == 3

    def test_oee_average_calculation(self, client, mock_verify_jwt):
        """AC#2: OEE averaged across assets with data."""
        mock_supabase = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assets":
                mock_table.select.return_value.execute.return_value.data = SAMPLE_ASSETS
            elif table_name == "cost_centers":
                mock_table.select.return_value.execute.return_value.data = []
            elif table_name == "live_snapshots":
                mock_chain = MagicMock()
                mock_chain.order.return_value.execute.return_value.data = SAMPLE_LIVE_SNAPSHOTS
                mock_table.select.return_value = mock_chain
            elif table_name == "safety_events":
                mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("app.api.live_pulse.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/live-pulse",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        production = response.json()["production"]

        # Average OEE: (85.5 + 92.0 + 75.0) / 3 = 84.17
        assert 80 < production["oee_percentage"] < 90


# =============================================================================
# Data Age Calculation Tests
# =============================================================================


class TestDataAgeCalculation:
    """Tests for data age and staleness calculation logic."""

    def test_calculate_data_age_with_recent_data(self):
        """Data age calculated correctly for recent timestamps."""
        from app.api.live_pulse import calculate_data_age

        recent_timestamp = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"
        age, is_stale = calculate_data_age(recent_timestamp)

        # Should be around 300 seconds (5 minutes)
        assert 280 <= age <= 320
        assert is_stale is False

    def test_calculate_data_age_with_stale_data(self):
        """Data age calculated correctly for stale timestamps."""
        from app.api.live_pulse import calculate_data_age

        stale_timestamp = (datetime.utcnow() - timedelta(minutes=25)).isoformat() + "Z"
        age, is_stale = calculate_data_age(stale_timestamp)

        # Should be around 1500 seconds (25 minutes)
        assert age >= 1200  # > 20 minutes
        assert is_stale is True

    def test_calculate_data_age_with_none(self):
        """Data age returns 0 and stale for None timestamp."""
        from app.api.live_pulse import calculate_data_age

        age, is_stale = calculate_data_age(None)

        assert age == 0
        assert is_stale is True

    def test_calculate_data_age_with_invalid_format(self):
        """Data age handles invalid timestamp format gracefully."""
        from app.api.live_pulse import calculate_data_age

        age, is_stale = calculate_data_age("not-a-timestamp")

        assert age == 0
        assert is_stale is True
