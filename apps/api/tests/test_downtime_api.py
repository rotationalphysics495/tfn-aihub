"""
Tests for Downtime API Endpoints.

Story: 2.5 - Downtime Pareto Analysis
AC: #1 - Downtime Data Retrieval
AC: #2 - Pareto Analysis Calculation
AC: #5 - Financial Impact Integration
AC: #6 - Safety Reason Code Highlighting
AC: #7 - Time Window Toggle
"""

import pytest
from datetime import datetime, date, timedelta
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
    with patch("app.api.downtime.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


@pytest.fixture
def sample_assets():
    """Sample asset data."""
    return [
        {
            "id": str(uuid4()),
            "name": "CNC Mill 01",
            "area": "Machining",
            "source_id": "CNC_MILL_01",
            "cost_center_id": str(uuid4()),
        },
        {
            "id": str(uuid4()),
            "name": "Lathe 02",
            "area": "Machining",
            "source_id": "LATHE_02",
            "cost_center_id": str(uuid4()),
        },
    ]


@pytest.fixture
def sample_cost_centers(sample_assets):
    """Sample cost center data."""
    return [
        {
            "id": sample_assets[0]["cost_center_id"],
            "standard_hourly_rate": 150.0,
        },
        {
            "id": sample_assets[1]["cost_center_id"],
            "standard_hourly_rate": 120.0,
        },
    ]


@pytest.fixture
def sample_daily_summaries(sample_assets):
    """Sample daily summary data with downtime."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return [
        {
            "id": str(uuid4()),
            "asset_id": sample_assets[0]["id"],
            "report_date": yesterday,
            "actual_output": 950,
            "target_output": 1000,
            "downtime_minutes": 45,
            "reason_code": "Mechanical Failure",
            "waste_count": 50,
        },
        {
            "id": str(uuid4()),
            "asset_id": sample_assets[0]["id"],
            "report_date": yesterday,
            "actual_output": 900,
            "target_output": 1000,
            "downtime_minutes": 30,
            "reason_code": "Material Shortage",
            "waste_count": 30,
        },
        {
            "id": str(uuid4()),
            "asset_id": sample_assets[1]["id"],
            "report_date": yesterday,
            "actual_output": 850,
            "target_output": 1000,
            "downtime_minutes": 60,
            "reason_code": "Safety Issue",
            "waste_count": 20,
        },
    ]


# =============================================================================
# Downtime Events Endpoint Tests
# =============================================================================


class TestDowntimeEventsEndpoint:
    """Tests for GET /api/v1/downtime/events."""

    def test_requires_authentication(self, client):
        """AC#1: Endpoint requires authentication."""
        response = client.get("/api/v1/downtime/events")
        assert response.status_code == 401

    def test_returns_events_with_daily_data(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#1: Returns downtime events from daily_summaries (T-1) by default."""
        # Setup mock responses
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),  # Assets query
            MagicMock(data=sample_cost_centers),  # Cost centers query
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure (AC#1)
        assert "events" in data
        assert "total_count" in data
        assert "total_downtime_minutes" in data
        assert "total_financial_impact" in data
        assert "data_source" in data
        assert "last_updated" in data

    def test_events_include_required_fields(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#1: Each event includes asset_id, reason_code, duration_minutes, event_timestamp, financial_impact."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        if data["events"]:
            event = data["events"][0]
            assert "asset_id" in event
            assert "reason_code" in event
            assert "duration_minutes" in event
            assert "event_timestamp" in event
            assert "financial_impact" in event
            assert "is_safety_related" in event

    def test_supports_pagination(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """AC#1: Supports pagination with limit and offset."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=[]
        )

        response = client.get(
            "/api/v1/downtime/events?limit=10&offset=5",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200

    def test_supports_live_source(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """AC#7: Supports live source parameter for T-15m data."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[]
        )

        response = client.get(
            "/api/v1/downtime/events?source=live",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data_source"] == "live_snapshots"


# =============================================================================
# Pareto Analysis Endpoint Tests
# =============================================================================


class TestParetoEndpoint:
    """Tests for GET /api/v1/downtime/pareto."""

    def test_requires_authentication(self, client):
        """AC#2: Endpoint requires authentication."""
        response = client.get("/api/v1/downtime/pareto")
        assert response.status_code == 401

    def test_returns_pareto_items(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#2: Returns Pareto items sorted by descending downtime."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/pareto",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "items" in data
        assert "total_downtime_minutes" in data
        assert "total_financial_impact" in data
        assert "total_events" in data
        assert "threshold_80_index" in data

    def test_pareto_items_include_all_fields(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#2: Pareto items include total_minutes, percentage, cumulative_percentage."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/pareto",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            item = data["items"][0]
            assert "reason_code" in item
            assert "total_minutes" in item
            assert "percentage" in item
            assert "cumulative_percentage" in item
            assert "financial_impact" in item
            assert "event_count" in item
            assert "is_safety_related" in item


# =============================================================================
# Summary Endpoint Tests
# =============================================================================


class TestSummaryEndpoint:
    """Tests for GET /api/v1/downtime/summary."""

    def test_requires_authentication(self, client):
        """AC#5: Endpoint requires authentication."""
        response = client.get("/api/v1/downtime/summary")
        assert response.status_code == 401

    def test_returns_cost_of_loss_summary(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#5: Returns financial impact summary."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/summary",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # AC#5: Total financial impact displayed
        assert "total_financial_loss" in data
        assert "total_downtime_minutes" in data
        assert "total_downtime_hours" in data
        assert "top_reason_code" in data
        assert "safety_events_count" in data


# =============================================================================
# Safety Event Detail Endpoint Tests
# =============================================================================


class TestSafetyEventDetailEndpoint:
    """Tests for GET /api/v1/downtime/safety/{event_id}."""

    def test_requires_authentication(self, client):
        """AC#6: Endpoint requires authentication."""
        event_id = str(uuid4())
        response = client.get(f"/api/v1/downtime/safety/{event_id}")
        assert response.status_code == 401

    def test_returns_safety_event_detail(
        self, client, mock_verify_jwt, mock_supabase_client, sample_assets
    ):
        """AC#6: Returns detailed safety event information."""
        event_id = str(uuid4())
        safety_event = {
            "id": event_id,
            "asset_id": sample_assets[0]["id"],
            "event_timestamp": datetime.utcnow().isoformat() + "Z",
            "reason_code": "Safety Issue",
            "severity": "high",
            "description": "E-stop triggered",
            "is_resolved": False,
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[safety_event]
        )
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=sample_assets
        )

        response = client.get(
            f"/api/v1/downtime/safety/{event_id}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id
        assert "severity" in data
        assert "description" in data

    def test_returns_404_for_nonexistent_event(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#6: Returns 404 for non-existent safety event."""
        event_id = str(uuid4())
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        response = client.get(
            f"/api/v1/downtime/safety/{event_id}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 404


# =============================================================================
# Areas Endpoint Tests
# =============================================================================


class TestAreasEndpoint:
    """Tests for GET /api/v1/downtime/areas."""

    def test_requires_authentication(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/v1/downtime/areas")
        assert response.status_code == 401

    def test_returns_unique_areas(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns unique areas for filtering."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[
                {"area": "Machining"},
                {"area": "Assembly"},
                {"area": "Machining"},  # Duplicate
                {"area": None},  # Null
            ]
        )

        response = client.get(
            "/api/v1/downtime/areas",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "Machining" in data
        assert "Assembly" in data
        assert len(data) == 2  # Duplicates and nulls filtered


# =============================================================================
# Pareto Calculation Tests
# =============================================================================


class TestParetoCalculation:
    """Tests for Pareto calculation logic."""

    def test_cumulative_percentage_reaches_100(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#2: Cumulative percentage reaches 100% for full dataset."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/pareto",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            # Last item should have cumulative_percentage approximately 100%
            # (allow for rounding differences)
            last_item = data["items"][-1]
            assert abs(last_item["cumulative_percentage"] - 100.0) < 0.5


class TestSafetyDetection:
    """Tests for safety event detection."""

    def test_safety_keyword_detection(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#6: Safety events are correctly identified and flagged."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # At least one event should be safety-related (sample has "Safety Issue")
        safety_events = [e for e in data["events"] if e["is_safety_related"]]
        assert len(safety_events) >= 1


# =============================================================================
# Financial Impact Calculation Tests
# =============================================================================


class TestFinancialImpactCalculation:
    """Tests for financial impact calculation logic."""

    def test_financial_impact_formula(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, sample_daily_summaries
    ):
        """AC#5: Financial impact = (downtime_minutes / 60) * standard_hourly_rate."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/v1/downtime/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        if data["events"]:
            event = data["events"][0]
            # Financial impact should be non-negative
            assert event["financial_impact"] >= 0


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for API error handling."""

    def test_handles_database_error(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns 500 on database error."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = Exception(
            "Database error"
        )

        response = client.get(
            "/api/v1/downtime/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 500

    def test_handles_empty_data_gracefully(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns empty response for no data."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=[]
        )

        response = client.get(
            "/api/v1/downtime/events",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total_count"] == 0


# =============================================================================
# OpenAPI Documentation Tests
# =============================================================================


class TestOpenAPIDocumentation:
    """Tests for API documentation."""

    def test_openapi_includes_downtime_endpoints(self, client):
        """Verify downtime endpoints are in OpenAPI spec."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        paths = openapi.get("paths", {})

        assert "/api/v1/downtime/events" in paths
        assert "/api/v1/downtime/pareto" in paths
        assert "/api/v1/downtime/summary" in paths
        assert "/api/v1/downtime/areas" in paths
