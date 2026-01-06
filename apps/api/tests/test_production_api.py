"""
Tests for Production API Endpoints.

Story: 2.3 - Throughput Dashboard
AC: #2 - Actual vs Target Visualization
AC: #5 - Real-time Data Binding
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.api.production import (
    calculate_status,
    calculate_percentage,
    ThroughputStatus,
)


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
    with patch("app.api.production.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


# =============================================================================
# Unit Tests for Helper Functions
# =============================================================================


class TestCalculateStatus:
    """Tests for status calculation logic."""

    def test_on_target_when_actual_equals_target(self):
        """AC#3: On target when actual >= target."""
        assert calculate_status(100, 100) == ThroughputStatus.ON_TARGET

    def test_on_target_when_actual_exceeds_target(self):
        """AC#3: On target when actual > target."""
        assert calculate_status(110, 100) == ThroughputStatus.ON_TARGET

    def test_behind_when_between_90_and_100_percent(self):
        """AC#3: Behind when actual < target by < 10%."""
        assert calculate_status(95, 100) == ThroughputStatus.BEHIND
        assert calculate_status(90, 100) == ThroughputStatus.BEHIND

    def test_critical_when_below_90_percent(self):
        """AC#3: Critical when actual < target by >= 10%."""
        assert calculate_status(89, 100) == ThroughputStatus.CRITICAL
        assert calculate_status(50, 100) == ThroughputStatus.CRITICAL
        assert calculate_status(0, 100) == ThroughputStatus.CRITICAL

    def test_on_target_when_target_is_zero(self):
        """AC#3: Avoid division by zero - return on_target."""
        assert calculate_status(50, 0) == ThroughputStatus.ON_TARGET
        assert calculate_status(0, 0) == ThroughputStatus.ON_TARGET


class TestCalculatePercentage:
    """Tests for percentage calculation logic."""

    def test_100_percent_when_actual_equals_target(self):
        """100% when actual equals target."""
        assert calculate_percentage(100, 100) == 100.0

    def test_percentage_above_100(self):
        """Above 100% when exceeding target."""
        assert calculate_percentage(150, 100) == 150.0

    def test_percentage_below_100(self):
        """Below 100% when behind target."""
        assert calculate_percentage(75, 100) == 75.0

    def test_percentage_with_zero_target(self):
        """Return 100% when target is zero (avoid division by zero)."""
        assert calculate_percentage(50, 0) == 100.0

    def test_percentage_rounding(self):
        """Percentage should be rounded to 1 decimal place."""
        assert calculate_percentage(33, 100) == 33.0
        assert calculate_percentage(333, 1000) == 33.3


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestThroughputEndpoint:
    """Tests for GET /api/production/throughput."""

    def test_requires_authentication(self, client):
        """AC#1: Endpoint requires authentication."""
        response = client.get("/api/production/throughput")
        assert response.status_code == 401

    def test_returns_throughput_data(self, client, mock_verify_jwt, mock_supabase_client):
        """AC#2: Returns throughput data with all required fields."""
        # Setup mock data
        asset_id = str(uuid4())
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            # First call: assets
            MagicMock(data=[{
                "id": asset_id,
                "name": "Grinder 5",
                "area": "Grinding",
                "source_id": "GRINDER_05",
            }]),
            # Second call: live_snapshots
            MagicMock(data=[{
                "id": str(uuid4()),
                "asset_id": asset_id,
                "snapshot_timestamp": datetime.utcnow().isoformat(),
                "current_output": 90,
                "target_output": 100,
                "output_variance": -10,
                "status": "behind",
            }]),
        ]
        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[{
            "id": str(uuid4()),
            "asset_id": asset_id,
            "snapshot_timestamp": datetime.utcnow().isoformat(),
            "current_output": 90,
            "target_output": 100,
            "output_variance": -10,
            "status": "behind",
        }])

        response = client.get(
            "/api/production/throughput",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert "last_updated" in data
        assert "total_assets" in data
        assert "on_target_count" in data
        assert "behind_count" in data
        assert "critical_count" in data

    def test_returns_empty_when_no_data(self, client, mock_verify_jwt, mock_supabase_client):
        """AC#7: Returns empty state when no data available."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/production/throughput",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assets"] == []
        assert data["total_assets"] == 0

    def test_filter_by_area(self, client, mock_verify_jwt, mock_supabase_client):
        """AC#8: Can filter by asset area."""
        asset_id = str(uuid4())
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{
                "id": asset_id,
                "name": "Grinder 5",
                "area": "Grinding",
                "source_id": "GRINDER_05",
            }]),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/production/throughput?area=Grinding",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200

    def test_filter_by_status(self, client, mock_verify_jwt, mock_supabase_client):
        """AC#8: Can filter by status."""
        asset_id = str(uuid4())
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{
                "id": asset_id,
                "name": "Grinder 5",
                "area": "Grinding",
                "source_id": "GRINDER_05",
            }]),
            MagicMock(data=[{
                "id": str(uuid4()),
                "asset_id": asset_id,
                "snapshot_timestamp": datetime.utcnow().isoformat(),
                "current_output": 90,
                "target_output": 100,
                "output_variance": -10,
                "status": "behind",
            }]),
        ]
        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[{
            "id": str(uuid4()),
            "asset_id": asset_id,
            "snapshot_timestamp": datetime.utcnow().isoformat(),
            "current_output": 90,
            "target_output": 100,
            "output_variance": -10,
            "status": "behind",
        }])

        response = client.get(
            "/api/production/throughput?status=behind",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200


class TestAreasEndpoint:
    """Tests for GET /api/production/throughput/areas."""

    def test_requires_authentication(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/production/throughput/areas")
        assert response.status_code == 401

    def test_returns_unique_areas(self, client, mock_verify_jwt, mock_supabase_client):
        """AC#8: Returns unique areas for filtering."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[
            {"area": "Grinding"},
            {"area": "Assembly"},
            {"area": "Grinding"},  # Duplicate
            {"area": None},  # Null area
        ])

        response = client.get(
            "/api/production/throughput/areas",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "Grinding" in data
        assert "Assembly" in data
        assert len(data) == 2  # Duplicates and nulls filtered

    def test_returns_empty_when_no_areas(self, client, mock_verify_jwt, mock_supabase_client):
        """Returns empty list when no areas defined."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/production/throughput/areas",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        assert response.json() == []


class TestThroughputResponseSchema:
    """Tests for API response structure."""

    def test_asset_throughput_contains_required_fields(self, client, mock_verify_jwt, mock_supabase_client):
        """AC#2: Each asset has required fields."""
        asset_id = str(uuid4())
        snapshot_time = datetime.utcnow().isoformat() + "Z"

        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=[{
                "id": asset_id,
                "name": "Test Asset",
                "area": "Test Area",
                "source_id": "TEST_01",
            }]),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[{
            "id": str(uuid4()),
            "asset_id": asset_id,
            "snapshot_timestamp": snapshot_time,
            "current_output": 100,
            "target_output": 100,
            "output_variance": 0,
            "status": "on_target",
        }])

        response = client.get(
            "/api/production/throughput",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        if data["assets"]:
            asset = data["assets"][0]
            assert "id" in asset
            assert "name" in asset
            assert "actual_output" in asset
            assert "target_output" in asset
            assert "variance" in asset
            assert "percentage" in asset
            assert "status" in asset
            assert "snapshot_timestamp" in asset


class TestEndpointDocumentation:
    """Tests for API documentation."""

    def test_openapi_includes_production_endpoints(self, client):
        """Verify production endpoints are in OpenAPI spec."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        paths = openapi.get("paths", {})

        assert "/api/production/throughput" in paths
        assert "/api/production/throughput/areas" in paths
