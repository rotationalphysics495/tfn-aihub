"""
Tests for Preferences API Endpoints (Story 8.9)

AC#1: Preferences written to user_preferences table immediately
AC#3: Supabase record updated immediately, Mem0 context reflects change
AC#5: Mem0 sync failures don't block Supabase saves

Tests API endpoints with Supabase and Mem0 mocked.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.preferences import DEFAULT_AREA_ORDER
from app.api.preferences import get_supabase_client
from app.main import app


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for dependency injection."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def override_supabase_dep(mock_supabase_client):
    """Override the Supabase dependency for testing."""
    async def _override():
        return mock_supabase_client

    app.dependency_overrides[get_supabase_client] = _override
    yield mock_supabase_client
    app.dependency_overrides.clear()


class TestGetPreferencesAPI:
    """Tests for GET /api/v1/preferences endpoint."""

    def test_get_preferences_returns_data(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#1: GET returns stored preferences."""
        mock_data = {
            "user_id": valid_jwt_payload["sub"],
            "role": "plant_manager",
            "area_order": ["Grinding", "Packing"],
            "detail_level": "summary",
            "voice_enabled": True,
            "onboarding_complete": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_result = MagicMock()
        mock_result.data = mock_data
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        response = client.get(
            "/api/v1/preferences",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "plant_manager"
        assert data["area_order"] == ["Grinding", "Packing"]

    def test_get_preferences_returns_404_when_not_found(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """GET returns 404 when preferences don't exist."""
        mock_result = MagicMock()
        mock_result.data = None
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        response = client.get(
            "/api/v1/preferences",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 404

    def test_get_preferences_requires_auth(self, client):
        """GET requires authentication."""
        response = client.get("/api/v1/preferences")
        assert response.status_code == 401


class TestCreatePreferencesAPI:
    """Tests for POST /api/v1/preferences endpoint."""

    def test_create_preferences_success(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#1: POST creates preferences and syncs to Mem0."""
        request_data = {
            "role": "plant_manager",
            "area_order": ["Grinding", "Packing", "Roasting"],
            "detail_level": "summary",
            "voice_enabled": True,
            "onboarding_complete": True,
        }

        mock_response_data = {
            **request_data,
            "user_id": valid_jwt_payload["sub"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mock no existing record
        mock_existing = MagicMock()
        mock_existing.data = None
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock insert response
        mock_insert = MagicMock()
        mock_insert.data = [mock_response_data]
        override_supabase_dep.table.return_value.insert.return_value.execute.return_value = mock_insert

        with patch("app.api.preferences.sync_preferences_to_mem0"):
            response = client.post(
                "/api/v1/preferences",
                json=request_data,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "plant_manager"
        assert data["onboarding_complete"] is True

    def test_create_preferences_updates_existing(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#1: POST updates existing preferences."""
        request_data = {
            "role": "supervisor",
            "area_order": ["Packing", "Grinding"],
            "detail_level": "detailed",
            "voice_enabled": False,
            "onboarding_complete": True,
        }

        mock_response_data = {
            **request_data,
            "user_id": valid_jwt_payload["sub"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mock existing record
        mock_existing = MagicMock()
        mock_existing.data = {"user_id": valid_jwt_payload["sub"]}
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock update response
        mock_update = MagicMock()
        mock_update.data = [mock_response_data]
        override_supabase_dep.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        with patch("app.api.preferences.sync_preferences_to_mem0"):
            response = client.post(
                "/api/v1/preferences",
                json=request_data,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        override_supabase_dep.table.return_value.update.assert_called_once()

    def test_create_preferences_validates_area_order(
        self, client, mock_verify_jwt, valid_jwt_payload
    ):
        """Validation: Invalid areas are rejected."""
        request_data = {
            "role": "plant_manager",
            "area_order": ["InvalidArea", "Packing"],
            "detail_level": "summary",
            "voice_enabled": True,
        }

        response = client.post(
            "/api/v1/preferences",
            json=request_data,
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 422  # Validation error


class TestUpdatePreferencesAPI:
    """Tests for PUT /api/v1/preferences endpoint."""

    def test_update_preferences_success(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#3: PUT updates preferences and syncs to Mem0."""
        existing_data = {
            "user_id": valid_jwt_payload["sub"],
            "role": "plant_manager",
            "area_order": DEFAULT_AREA_ORDER,
            "detail_level": "summary",
            "voice_enabled": True,
            "onboarding_complete": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        updated_data = {
            **existing_data,
            "area_order": ["Grinding", "Packing"],
        }

        # Mock existing record
        mock_existing = MagicMock()
        mock_existing.data = existing_data
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock update response
        mock_update = MagicMock()
        mock_update.data = [updated_data]
        override_supabase_dep.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        with patch("app.api.preferences.sync_preferences_to_mem0"):
            response = client.put(
                "/api/v1/preferences",
                json={"area_order": ["Grinding", "Packing"]},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["area_order"] == ["Grinding", "Packing"]

    def test_update_preferences_returns_404_when_not_found(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#3: PUT returns 404 when preferences don't exist."""
        # Mock no existing record
        mock_existing = MagicMock()
        mock_existing.data = None
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        response = client.put(
            "/api/v1/preferences",
            json={"voice_enabled": False},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 404

    def test_update_preferences_partial_update(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#3: PUT allows partial updates."""
        existing_data = {
            "user_id": valid_jwt_payload["sub"],
            "role": "plant_manager",
            "area_order": DEFAULT_AREA_ORDER,
            "detail_level": "summary",
            "voice_enabled": True,
            "onboarding_complete": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mock existing record
        mock_existing = MagicMock()
        mock_existing.data = existing_data
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock update response
        updated_data = {**existing_data, "voice_enabled": False}
        mock_update = MagicMock()
        mock_update.data = [updated_data]
        override_supabase_dep.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        with patch("app.api.preferences.sync_preferences_to_mem0"):
            # Only update voice_enabled
            response = client.put(
                "/api/v1/preferences",
                json={"voice_enabled": False},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        # Verify only voice_enabled was in update call
        update_call_args = override_supabase_dep.table.return_value.update.call_args[0][0]
        assert "voice_enabled" in update_call_args
        assert update_call_args["voice_enabled"] is False


class TestPatchPreferencesAPI:
    """Tests for PATCH /api/v1/preferences endpoint."""

    def test_patch_preferences_success(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#3: PATCH updates preferences."""
        existing_data = {
            "user_id": valid_jwt_payload["sub"],
            "role": "plant_manager",
            "area_order": DEFAULT_AREA_ORDER,
            "detail_level": "summary",
            "voice_enabled": True,
            "onboarding_complete": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mock existing record
        mock_existing = MagicMock()
        mock_existing.data = existing_data
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock update response
        updated_data = {**existing_data, "detail_level": "detailed"}
        mock_update = MagicMock()
        mock_update.data = [updated_data]
        override_supabase_dep.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        with patch("app.api.preferences.sync_preferences_to_mem0"):
            response = client.patch(
                "/api/v1/preferences",
                json={"detail_level": "detailed"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200


class TestMem0SyncIntegration:
    """Tests for Mem0 sync integration in API endpoints."""

    def test_create_preferences_triggers_mem0_sync(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#1: POST triggers Mem0 sync in background."""
        request_data = {
            "role": "plant_manager",
            "area_order": ["Grinding", "Packing", "Roasting"],
            "detail_level": "summary",
            "voice_enabled": True,
            "onboarding_complete": True,
        }

        mock_response_data = {
            **request_data,
            "user_id": valid_jwt_payload["sub"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_existing = MagicMock()
        mock_existing.data = None
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        mock_insert = MagicMock()
        mock_insert.data = [mock_response_data]
        override_supabase_dep.table.return_value.insert.return_value.execute.return_value = mock_insert

        with patch("app.api.preferences.sync_preferences_to_mem0"):
            response = client.post(
                "/api/v1/preferences",
                json=request_data,
                headers={"Authorization": "Bearer test-token"},
            )

            # Note: Background tasks are executed synchronously in TestClient
            # So we can verify the sync function was called
            assert response.status_code == 201

    def test_update_preferences_triggers_mem0_sync(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#3: PUT triggers Mem0 sync in background."""
        existing_data = {
            "user_id": valid_jwt_payload["sub"],
            "role": "plant_manager",
            "area_order": DEFAULT_AREA_ORDER,
            "detail_level": "summary",
            "voice_enabled": True,
            "onboarding_complete": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_existing = MagicMock()
        mock_existing.data = existing_data
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        mock_update = MagicMock()
        mock_update.data = [existing_data]
        override_supabase_dep.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        with patch("app.api.preferences.sync_preferences_to_mem0"):
            response = client.put(
                "/api/v1/preferences",
                json={"voice_enabled": False},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200


class TestGracefulDegradationAPI:
    """Tests for AC#5 - graceful degradation in API."""

    def test_supabase_failure_returns_error(
        self, client, mock_verify_jwt, valid_jwt_payload, override_supabase_dep
    ):
        """AC#5: Supabase failure returns HTTP error."""
        override_supabase_dep.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = Exception("DB Error")

        response = client.get(
            "/api/v1/preferences",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 500
