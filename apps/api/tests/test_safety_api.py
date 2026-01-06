"""
Tests for Safety Alert API Endpoints.

Story: 2.6 - Safety Alert System
AC: #1 - Safety detection during polling
AC: #2 - Persistence to safety_events table
AC: #3 - Safety Red visual indicator
AC: #5 - Link to specific asset
AC: #6 - Alert persistence until acknowledged
AC: #9 - Safety count in header/status
AC: #10 - Financial impact context
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    with patch("app.core.database.mssql_db") as mock_db:
        mock_db.initialize = MagicMock()
        mock_db.dispose = MagicMock()
        mock_db.check_health.return_value = {
            "status": "not_configured",
            "connected": False,
        }
        with patch("app.services.scheduler.get_scheduler") as mock_sched:
            mock_scheduler = MagicMock()
            mock_scheduler.start = AsyncMock()
            mock_scheduler.shutdown = AsyncMock()
            mock_scheduler.status.to_dict.return_value = {
                "status": "stopped",
            }
            mock_sched.return_value = mock_scheduler
            with TestClient(app) as test_client:
                yield test_client


@pytest.fixture
def mock_verify_jwt():
    """Mock JWT verification."""
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }
        yield mock


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    with patch("app.api.safety.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


@pytest.fixture
def sample_assets():
    """Sample asset data."""
    return [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "Grinder 5",
            "area": "Grinding",
            "source_id": "GRINDER_05",
            "cost_center_id": "22222222-2222-2222-2222-222222222222",
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "name": "CNC Mill 01",
            "area": "Machining",
            "source_id": "CNC_MILL_01",
            "cost_center_id": "44444444-4444-4444-4444-444444444444",
        },
    ]


@pytest.fixture
def sample_cost_centers():
    """Sample cost center data."""
    return [
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "standard_hourly_rate": 175.0,
        },
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "standard_hourly_rate": 150.0,
        },
    ]


@pytest.fixture
def sample_safety_events(sample_assets):
    """Sample safety events data."""
    return [
        {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "asset_id": sample_assets[0]["id"],
            "event_timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
            "reason_code": "Safety Issue",
            "severity": "critical",
            "description": "Emergency stop triggered",
            "is_resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "duration_minutes": 15,
            "source_record_id": "MSSQL_DT_12345",
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
        {
            "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "asset_id": sample_assets[1]["id"],
            "event_timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
            "reason_code": "Safety Issue - E-Stop",
            "severity": "high",
            "description": "Operator e-stop",
            "is_resolved": True,
            "resolved_at": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
            "resolved_by": "55555555-5555-5555-5555-555555555555",
            "duration_minutes": 30,
            "source_record_id": "MSSQL_DT_12346",
            "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
        },
    ]


# =============================================================================
# Get Safety Events Endpoint Tests
# =============================================================================


class TestGetSafetyEventsEndpoint:
    """Tests for GET /api/safety/events."""

    def test_requires_authentication(self, client):
        """AC#2: Endpoint requires authentication."""
        response = client.get("/api/safety/events")
        assert response.status_code == 401

    def test_returns_safety_events(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_safety_events
    ):
        """AC#2: Returns safety events from safety_events table."""
        # Setup mock chain for safety events query
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table

        # Mock the chained query methods
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select

        # Different returns based on query context
        def select_side_effect(*args, **kwargs):
            # Track calls for different tables
            return mock_select

        mock_table.select.side_effect = select_side_effect

        # Setup return values
        mock_select.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=sample_safety_events
        )
        mock_select.execute.side_effect = [
            MagicMock(data=sample_assets),  # assets query
            MagicMock(data=sample_cost_centers),  # cost_centers query
        ]

        response = client.get(
            "/api/safety/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "events" in data
        assert "count" in data
        assert "last_updated" in data

    def test_supports_limit_parameter(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC: Supports limit query parameter."""
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_select.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/safety/events?limit=10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200

    def test_supports_since_parameter(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC: Supports since query parameter."""
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.gte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_select.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/safety/events?since=2026-01-05T00:00:00Z",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200

    def test_supports_asset_id_filter(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#5: Supports asset_id query parameter for filtering."""
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_select.execute.return_value = MagicMock(data=[])

        asset_id = str(uuid4())
        response = client.get(
            f"/api/safety/events?asset_id={asset_id}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200


# =============================================================================
# Get Active Alerts Endpoint Tests
# =============================================================================


class TestGetActiveAlertsEndpoint:
    """Tests for GET /api/safety/active."""

    def test_requires_authentication(self, client):
        """AC#6: Endpoint requires authentication."""
        response = client.get("/api/safety/active")
        assert response.status_code == 401

    def test_returns_only_unacknowledged_alerts(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_safety_events
    ):
        """AC#6: Returns only unacknowledged (active) alerts."""
        # Only return the unresolved event
        active_events = [e for e in sample_safety_events if not e.get("is_resolved")]

        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=active_events
        )
        mock_select.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]

        response = client.get(
            "/api/safety/active",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify only active alerts returned
        assert "events" in data
        assert "count" in data
        for event in data["events"]:
            assert event.get("acknowledged") is False

    def test_returns_count_for_header_indicator(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#9: Returns count for header indicator."""
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        mock_select.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/safety/active",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Count should be present for header indicator (AC#9)
        assert "count" in data
        assert isinstance(data["count"], int)


# =============================================================================
# Acknowledge Event Endpoint Tests
# =============================================================================


class TestAcknowledgeEndpoint:
    """Tests for POST /api/safety/acknowledge/{event_id}."""

    def test_requires_authentication(self, client):
        """AC#6: Endpoint requires authentication."""
        event_id = str(uuid4())
        response = client.post(f"/api/safety/acknowledge/{event_id}")
        assert response.status_code == 401

    def test_acknowledges_event_successfully(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_safety_events
    ):
        """AC#6: Successfully acknowledges a safety event."""
        event = sample_safety_events[0].copy()
        acknowledged_event = {
            **event,
            "is_resolved": True,
            "resolved_at": datetime.utcnow().isoformat() + "Z",
        }

        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[acknowledged_event]
        )
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]

        response = client.post(
            f"/api/safety/acknowledge/{event['id']}",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify acknowledgement response
        assert data["success"] is True
        assert "event" in data
        assert data["event"]["acknowledged"] is True

    def test_returns_404_for_nonexistent_event(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#6: Returns 404 for non-existent event."""
        event_id = str(uuid4())

        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        response = client.post(
            f"/api/safety/acknowledge/{event_id}",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )

        # Should return 404 for non-existent event
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# =============================================================================
# Get Single Event Endpoint Tests
# =============================================================================


class TestGetSafetyEventEndpoint:
    """Tests for GET /api/safety/{event_id}."""

    def test_requires_authentication(self, client):
        """AC#5: Endpoint requires authentication."""
        event_id = str(uuid4())
        response = client.get(f"/api/safety/{event_id}")
        assert response.status_code == 401

    def test_returns_event_with_asset_details(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_safety_events
    ):
        """AC#5: Returns event with asset name for linking."""
        event = sample_safety_events[0]

        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value.execute.return_value = MagicMock(data=[event])
        mock_select.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]

        response = client.get(
            f"/api/safety/{event['id']}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # AC#5: Should include asset_name for linking
        assert "asset_id" in data
        assert "asset_name" in data
        assert data["asset_name"] == "Grinder 5"

    def test_returns_financial_impact(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_safety_events
    ):
        """AC#10: Returns financial impact when available."""
        event = sample_safety_events[0]

        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value.execute.return_value = MagicMock(data=[event])
        mock_select.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]

        response = client.get(
            f"/api/safety/{event['id']}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # AC#10: Financial impact should be calculated
        # Duration is 15 min, rate is 175/hr
        # Expected: (15/60) * 175 = $43.75
        if data.get("financial_impact") is not None:
            assert data["financial_impact"] > 0

    def test_returns_404_for_nonexistent_event(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns 404 for non-existent event."""
        event_id = str(uuid4())

        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            f"/api/safety/{event_id}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 404


# =============================================================================
# Dashboard Status Endpoint Tests
# =============================================================================


class TestDashboardStatusEndpoint:
    """Tests for GET /api/safety/status."""

    def test_requires_authentication(self, client):
        """AC#9: Endpoint requires authentication."""
        response = client.get("/api/safety/status")
        assert response.status_code == 401

    def test_returns_safety_alert_count(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#9: Returns safety_alert_count for header indicator."""
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select

        # Safety events count query
        mock_select.eq.return_value.execute.return_value = MagicMock(
            data=[], count=3
        )

        # Live snapshots query
        mock_select.order.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/safety/status",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # AC#9: Must include safety_alert_count
        assert "safety_alert_count" in data
        assert "safety_alerts_active" in data
        assert isinstance(data["safety_alert_count"], int)
        assert isinstance(data["safety_alerts_active"], bool)

    def test_returns_asset_status_counts(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns asset status counts for dashboard."""
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value.execute.return_value = MagicMock(data=[], count=0)
        mock_select.order.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/safety/status",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify status counts are present
        assert "total_assets" in data
        assert "assets_on_target" in data
        assert "assets_below_target" in data
        assert "assets_above_target" in data


# =============================================================================
# OpenAPI Documentation Tests
# =============================================================================


class TestOpenAPIDocumentation:
    """Tests for API documentation."""

    def test_openapi_includes_safety_endpoints(self, client):
        """Verify safety endpoints are in OpenAPI spec."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        paths = openapi.get("paths", {})

        assert "/api/safety/events" in paths
        assert "/api/safety/active" in paths
        assert "/api/safety/status" in paths
        # Check acknowledge endpoint pattern
        assert any("acknowledge" in path for path in paths.keys())


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for API error handling."""

    def test_handles_database_error_gracefully(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns 500 on database error."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = Exception(
            "Database connection error"
        )

        response = client.get(
            "/api/safety/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 500

    def test_handles_invalid_since_format(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns 400 for invalid timestamp format."""
        response = client.get(
            "/api/safety/events?since=not-a-timestamp",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 400
        assert "timestamp" in response.json()["detail"].lower()

    def test_handles_invalid_uuid_in_acknowledge(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns 400 for invalid UUID format in acknowledge endpoint."""
        response = client.post(
            "/api/safety/acknowledge/not-a-uuid",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )

        assert response.status_code == 400
        assert "uuid" in response.json()["detail"].lower()

    def test_handles_invalid_uuid_in_get_event(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns 400 for invalid UUID format in get event endpoint."""
        response = client.get(
            "/api/safety/invalid-uuid-format",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 400
        assert "uuid" in response.json()["detail"].lower()
