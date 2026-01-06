"""
Tests for OEE API Endpoints.

Story: 2.4 - OEE Metrics View
AC: #2 - OEE metrics computed from daily_summaries and live_snapshots
AC: #5 - OEE values update within 60 seconds (via API response)
AC: #7 - OEE targets shown alongside actual values
AC: #10 - API endpoint returns OEE data with proper error handling
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
    with patch("app.api.oee.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


@pytest.fixture
def sample_assets():
    """Sample asset data."""
    return [
        {
            "id": str(uuid4()),
            "name": "Grinder 5",
            "area": "Grinding",
            "source_id": "GRINDER_05",
        },
        {
            "id": str(uuid4()),
            "name": "Lathe 2",
            "area": "Machining",
            "source_id": "LATHE_02",
        },
    ]


@pytest.fixture
def sample_daily_summaries(sample_assets):
    """Sample daily summary data."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return [
        {
            "id": str(uuid4()),
            "asset_id": sample_assets[0]["id"],
            "report_date": yesterday,
            "actual_output": 950,
            "target_output": 1000,
            "downtime_minutes": 48,
            "waste_count": 50,
            "oee_percentage": 83.5,
        },
        {
            "id": str(uuid4()),
            "asset_id": sample_assets[1]["id"],
            "report_date": yesterday,
            "actual_output": 900,
            "target_output": 1000,
            "downtime_minutes": 96,
            "waste_count": 30,
            "oee_percentage": 78.2,
        },
    ]


@pytest.fixture
def sample_shift_targets(sample_assets):
    """Sample shift target data."""
    return [
        {
            "asset_id": sample_assets[0]["id"],
            "target_output": 1000,
            "shift": "Day",
            "effective_date": date.today().isoformat(),
        },
        {
            "asset_id": sample_assets[1]["id"],
            "target_output": 1000,
            "shift": "Day",
            "effective_date": date.today().isoformat(),
        },
    ]


# =============================================================================
# Plant OEE Endpoint Tests
# =============================================================================


class TestPlantOEEEndpoint:
    """Tests for GET /api/oee/plant."""

    def test_requires_authentication(self, client):
        """AC#10: Endpoint requires authentication."""
        response = client.get("/api/oee/plant")
        assert response.status_code == 401

    def test_returns_plant_oee_with_daily_data(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_daily_summaries, sample_shift_targets
    ):
        """AC#2: Returns plant OEE from daily_summaries (T-1) by default."""
        # Setup mock responses
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            # Assets query
            MagicMock(data=sample_assets),
            # Shift targets query
            MagicMock(data=sample_shift_targets),
        ]

        # Daily summaries query with date filter
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/oee/plant",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "plant_oee" in data
        assert "assets" in data
        assert "data_source" in data
        assert "last_updated" in data

        # Verify plant_oee structure
        plant_oee = data["plant_oee"]
        assert "overall" in plant_oee
        assert "availability" in plant_oee
        assert "performance" in plant_oee
        assert "quality" in plant_oee
        assert "target" in plant_oee
        assert "status" in plant_oee

        # AC#7: Target is shown
        assert plant_oee["target"] == 85.0

    def test_returns_live_data_when_requested(
        self, client, mock_verify_jwt, mock_supabase_client, sample_assets
    ):
        """AC#2: Returns OEE from live_snapshots when source=live."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=[]),  # No shift targets
        ]

        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{
                "id": str(uuid4()),
                "asset_id": sample_assets[0]["id"],
                "snapshot_timestamp": datetime.utcnow().isoformat() + "Z",
                "current_output": 90,
                "target_output": 100,
            }]
        )

        response = client.get(
            "/api/oee/plant?source=live",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data_source"] == "live_snapshots"

    def test_returns_empty_when_no_assets(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#10: Handles empty asset list gracefully."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/oee/plant",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assets"] == []
        assert data["plant_oee"]["status"] == "unknown"

    def test_includes_last_updated_timestamp(
        self, client, mock_verify_jwt, mock_supabase_client, sample_assets
    ):
        """AC#5: Response includes last_updated for freshness tracking."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/oee/plant",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "last_updated" in data
        assert data["last_updated"] is not None


# =============================================================================
# Assets OEE Endpoint Tests
# =============================================================================


class TestAssetsOEEEndpoint:
    """Tests for GET /api/oee/assets."""

    def test_requires_authentication(self, client):
        """AC#10: Endpoint requires authentication."""
        response = client.get("/api/oee/assets")
        assert response.status_code == 401

    def test_returns_assets_oee_list(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_daily_summaries, sample_shift_targets
    ):
        """AC#4: Returns per-asset OEE breakdown."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_shift_targets),
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/oee/assets",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_asset_contains_all_oee_components(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_daily_summaries, sample_shift_targets
    ):
        """AC#1: Each asset shows all three OEE components."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_shift_targets),
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        response = client.get(
            "/api/oee/assets",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        if data:
            asset = data[0]
            assert "oee" in asset
            assert "availability" in asset
            assert "performance" in asset
            assert "quality" in asset
            assert "target" in asset
            assert "status" in asset

    def test_filter_by_area(
        self, client, mock_verify_jwt, mock_supabase_client, sample_assets
    ):
        """Assets can be filtered by area."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/oee/assets?area=Grinding",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200

    def test_filter_by_status(
        self, client, mock_verify_jwt, mock_supabase_client, sample_assets
    ):
        """AC#8: Assets can be filtered by OEE status."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/oee/assets?status=yellow",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200


# =============================================================================
# Single Asset OEE Endpoint Tests
# =============================================================================


class TestAssetOEEDetailEndpoint:
    """Tests for GET /api/oee/assets/{asset_id}."""

    def test_requires_authentication(self, client):
        """AC#10: Endpoint requires authentication."""
        asset_id = str(uuid4())
        response = client.get(f"/api/oee/assets/{asset_id}")
        assert response.status_code == 401

    def test_returns_single_asset_oee(
        self, client, mock_verify_jwt, mock_supabase_client, sample_assets
    ):
        """Returns detailed OEE for a single asset (with no data returns null OEE).

        Note: Full integration testing recommended for complex query chains.
        This test verifies the endpoint structure with minimal mock complexity.
        """
        asset_id = sample_assets[0]["id"]

        # The query chain for this endpoint is complex:
        # 1. assets.select().eq(asset_id) -> asset info
        # 2. shift_targets.select().eq(asset_id) -> target info
        # 3. daily_summaries.select().eq(report_date).eq(asset_id) -> summary data
        #
        # Mock the entire chain uniformly
        mock_chain = MagicMock()
        mock_chain.execute.return_value = MagicMock(data=[sample_assets[0]])
        mock_supabase_client.table.return_value.select.return_value.eq.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain  # For chained .eq() calls

        response = client.get(
            f"/api/oee/assets/{asset_id}",
            headers={"Authorization": "Bearer valid-token"},
        )

        # Endpoint should return 200 or handle gracefully
        # Due to mock complexity, we verify the endpoint is reachable and
        # returns the expected response structure (even if data is minimal)
        assert response.status_code == 200
        data = response.json()

        # Verify response contains expected fields
        assert "asset_id" in data
        assert "oee" in data
        assert "data_source" in data
        assert "last_updated" in data

    def test_returns_404_for_nonexistent_asset(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#10: Returns 404 for non-existent asset."""
        asset_id = str(uuid4())

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            f"/api/oee/assets/{asset_id}",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 404


# =============================================================================
# Areas Endpoint Tests
# =============================================================================


class TestOEEAreasEndpoint:
    """Tests for GET /api/oee/areas."""

    def test_requires_authentication(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/oee/areas")
        assert response.status_code == 401

    def test_returns_unique_areas(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """Returns unique areas for filtering."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[
            {"area": "Grinding"},
            {"area": "Machining"},
            {"area": "Grinding"},  # Duplicate
            {"area": None},  # Null
        ])

        response = client.get(
            "/api/oee/areas",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "Grinding" in data
        assert "Machining" in data
        assert len(data) == 2  # Duplicates and nulls filtered


# =============================================================================
# Response Schema Tests
# =============================================================================


class TestOEEResponseSchema:
    """Tests for API response structure."""

    def test_plant_oee_response_structure(
        self, client, mock_verify_jwt, mock_supabase_client, sample_assets
    ):
        """Verify response matches expected JSON structure."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=[]),
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        response = client.get(
            "/api/oee/plant",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        required_fields = ["plant_oee", "assets", "data_source", "last_updated"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify plant_oee structure
        plant_oee_fields = ["overall", "availability", "performance", "quality", "target", "status"]
        for field in plant_oee_fields:
            assert field in data["plant_oee"], f"Missing plant_oee field: {field}"


class TestOpenAPIDocumentation:
    """Tests for API documentation."""

    def test_openapi_includes_oee_endpoints(self, client):
        """Verify OEE endpoints are in OpenAPI spec."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        paths = openapi.get("paths", {})

        assert "/api/oee/plant" in paths
        assert "/api/oee/assets" in paths
        assert "/api/oee/areas" in paths


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestOEEErrorHandling:
    """Tests for API error handling."""

    def test_handles_database_error_gracefully(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """AC#10: Returns 500 on database error."""
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = Exception(
            "Database connection failed"
        )

        response = client.get(
            "/api/oee/plant",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 500
        assert "Failed to fetch OEE data" in response.json()["detail"]
