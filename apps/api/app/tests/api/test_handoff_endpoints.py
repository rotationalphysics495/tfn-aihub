"""
Handoff API Endpoint Tests (Story 9.1, Task 8)

Tests for handoff API endpoints including:
- GET /api/v1/handoff/initiate (AC#1, AC#3, AC#4)
- POST /api/v1/handoff/ (AC#1, AC#2)
- GET /api/v1/handoff/ (list handoffs)
- GET /api/v1/handoff/{id} (get details)
- PATCH /api/v1/handoff/{id} (update draft)
- POST /api/v1/handoff/{id}/submit (submit handoff)

References:
- [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
- [Source: prd-functional-requirements.md#FR21-FR30]
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timezone
from uuid import UUID
from fastapi.testclient import TestClient

from app.main import app
from app.models.handoff import ShiftType, HandoffStatus, ShiftTimeRange, SupervisorAsset
from app.models.user import CurrentUser
from app.core.security import get_current_user
from app.api import handoff as handoff_module


# Test user ID
TEST_USER_ID = "test-user-123"


def get_test_user(user_id: str = TEST_USER_ID) -> CurrentUser:
    """Create a test user with the given ID."""
    return CurrentUser(id=user_id, email=f"{user_id}@test.com", role="authenticated")


@pytest.fixture(autouse=True)
def reset_handoffs_store():
    """Reset the in-memory handoffs store before each test."""
    handoff_module._handoffs.clear()
    yield
    handoff_module._handoffs.clear()


@pytest.fixture
def authenticated_client():
    """Create a test client with mocked authentication."""
    def _create_client(user_id: str = TEST_USER_ID):
        test_user = get_test_user(user_id)
        app.dependency_overrides[get_current_user] = lambda: test_user
        client = TestClient(app)
        return client, test_user

    yield _create_client

    # Cleanup
    app.dependency_overrides.clear()


class TestInitiateHandoffEndpoint:
    """Tests for GET /api/v1/handoff/initiate endpoint."""

    def test_initiate_returns_shift_info(self, authenticated_client):
        """Test initiate endpoint returns shift information (AC#1)."""
        client, _ = authenticated_client()
        response = client.get("/api/v1/handoff/initiate")

        assert response.status_code == 200
        data = response.json()

        assert "shift_info" in data
        assert "shift_type" in data["shift_info"]
        assert data["shift_info"]["shift_type"] in ["morning", "afternoon", "night"]
        assert "start_time" in data["shift_info"]
        assert "end_time" in data["shift_info"]
        assert "shift_date" in data["shift_info"]

    def test_initiate_returns_assigned_assets(self, authenticated_client):
        """Test initiate endpoint returns assigned assets (AC#1)."""
        client, _ = authenticated_client()
        response = client.get("/api/v1/handoff/initiate")

        assert response.status_code == 200
        data = response.json()

        assert "assigned_assets" in data
        assert isinstance(data["assigned_assets"], list)

        # With mock data, should have assets
        if len(data["assigned_assets"]) > 0:
            asset = data["assigned_assets"][0]
            assert "asset_id" in asset
            assert "asset_name" in asset

    def test_initiate_with_no_assets_returns_error(self, authenticated_client):
        """Test initiate shows error when no assets assigned (AC#3)."""
        client, _ = authenticated_client()
        with patch('app.api.handoff._get_supervisor_assignments', return_value=[]):
            response = client.get("/api/v1/handoff/initiate")

            assert response.status_code == 200
            data = response.json()

            assert data["can_create"] is False
            assert "No assets assigned" in data["message"]
            assert len(data["assigned_assets"]) == 0

    def test_initiate_with_existing_draft_handoff(self, authenticated_client):
        """Test initiate returns existing handoff info (AC#4)."""
        client, _ = authenticated_client()

        # First create a handoff
        create_response = client.post("/api/v1/handoff/", json={})
        assert create_response.status_code == 201

        # Now initiate again - should see existing handoff
        response = client.get("/api/v1/handoff/initiate")

        assert response.status_code == 200
        data = response.json()

        # Existing handoff should be flagged
        assert data["existing_handoff"] is not None
        assert data["existing_handoff"]["exists"] is True
        assert data["existing_handoff"]["can_edit"] is True


class TestCreateHandoffEndpoint:
    """Tests for POST /api/v1/handoff/ endpoint."""

    def test_create_handoff_success(self, authenticated_client):
        """Test successful handoff creation (AC#1, AC#2)."""
        client, _ = authenticated_client("test-create-user-001")

        response = client.post(
            "/api/v1/handoff/",
            json={"text_notes": "Test notes for handoff"}
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["status"] == "draft"
        assert data["text_notes"] == "Test notes for handoff"
        assert "shift_date" in data
        assert "shift_type" in data

    def test_create_handoff_with_selected_assets(self, authenticated_client):
        """Test handoff creation with specific assets."""
        client, _ = authenticated_client("test-create-user-002")

        # First get assigned assets
        initiate_response = client.get("/api/v1/handoff/initiate")
        assets = initiate_response.json()["assigned_assets"]

        if len(assets) > 0:
            # Create with first asset only
            response = client.post(
                "/api/v1/handoff/",
                json={"assets_covered": [assets[0]["asset_id"]]}
            )

            assert response.status_code == 201

    def test_create_handoff_no_assets_fails(self, authenticated_client):
        """Test handoff creation fails when no assets assigned (AC#3)."""
        client, _ = authenticated_client()
        with patch('app.api.handoff._get_supervisor_assignments', return_value=[]):
            response = client.post("/api/v1/handoff/", json={})

            assert response.status_code == 400
            assert "No assets assigned" in response.json()["detail"]

    def test_create_duplicate_handoff_fails(self, authenticated_client):
        """Test duplicate handoff creation returns 409 (AC#4)."""
        client, _ = authenticated_client("test-duplicate-user")

        # Create first handoff
        first_response = client.post("/api/v1/handoff/", json={})
        assert first_response.status_code == 201

        # Try to create another
        second_response = client.post("/api/v1/handoff/", json={})

        assert second_response.status_code == 409
        detail = second_response.json()["detail"]
        assert "already exists" in detail["message"]
        assert detail["action"] == "edit"


class TestListHandoffsEndpoint:
    """Tests for GET /api/v1/handoff/ endpoint."""

    def test_list_handoffs_returns_user_handoffs(self, authenticated_client):
        """Test listing returns user's handoffs."""
        client, _ = authenticated_client("test-list-user")

        # Create a handoff first
        client.post("/api/v1/handoff/", json={})

        response = client.get("/api/v1/handoff/")

        assert response.status_code == 200
        data = response.json()

        assert "handoffs" in data
        assert "total_count" in data
        assert data["total_count"] >= 1

    def test_list_handoffs_pagination(self, authenticated_client):
        """Test list endpoint supports pagination."""
        client, _ = authenticated_client("test-pagination-user")

        # Create a handoff
        client.post("/api/v1/handoff/", json={})

        response = client.get("/api/v1/handoff/?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["handoffs"], list)
        assert len(data["handoffs"]) <= 5

    def test_list_handoffs_empty_for_new_user(self, authenticated_client):
        """Test list returns empty for new user."""
        client, _ = authenticated_client("brand-new-user")
        response = client.get("/api/v1/handoff/")

        assert response.status_code == 200
        data = response.json()

        assert data["handoffs"] == []
        assert data["total_count"] == 0


class TestGetHandoffEndpoint:
    """Tests for GET /api/v1/handoff/{id} endpoint."""

    def test_get_handoff_success(self, authenticated_client):
        """Test getting handoff details."""
        client, _ = authenticated_client("test-get-user")

        # Create a handoff
        create_response = client.post(
            "/api/v1/handoff/",
            json={"text_notes": "Get test notes"}
        )
        handoff_id = create_response.json()["id"]

        # Get it
        response = client.get(f"/api/v1/handoff/{handoff_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == handoff_id
        assert data["text_notes"] == "Get test notes"
        assert "assets_covered" in data

    def test_get_handoff_not_found(self, authenticated_client):
        """Test 404 for non-existent handoff."""
        client, _ = authenticated_client()
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/handoff/{fake_id}")

        assert response.status_code == 404

    def test_get_handoff_access_denied(self, authenticated_client):
        """Test access denied for other user's handoff."""
        # Create handoff as owner
        owner_client, _ = authenticated_client("test-owner-user")
        create_response = owner_client.post("/api/v1/handoff/", json={})
        handoff_id = create_response.json()["id"]

        # Clear override and try to access as different user
        app.dependency_overrides.clear()
        other_client, _ = authenticated_client("test-other-user")
        response = other_client.get(f"/api/v1/handoff/{handoff_id}")

        assert response.status_code == 403


class TestUpdateHandoffEndpoint:
    """Tests for PATCH /api/v1/handoff/{id} endpoint."""

    def test_update_draft_handoff_success(self, authenticated_client):
        """Test updating a draft handoff."""
        client, _ = authenticated_client("test-update-user")

        # Create a handoff
        create_response = client.post(
            "/api/v1/handoff/",
            json={"text_notes": "Original notes"}
        )
        handoff_id = create_response.json()["id"]

        # Update it
        response = client.patch(
            f"/api/v1/handoff/{handoff_id}",
            json={"text_notes": "Updated notes"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["text_notes"] == "Updated notes"

    def test_update_non_draft_handoff_fails(self, authenticated_client):
        """Test updating submitted handoff fails."""
        client, _ = authenticated_client("test-update-submitted-user")

        # Create and submit a handoff
        create_response = client.post("/api/v1/handoff/", json={})
        handoff_id = create_response.json()["id"]

        # Submit it
        client.post(f"/api/v1/handoff/{handoff_id}/submit")

        # Try to update
        response = client.patch(
            f"/api/v1/handoff/{handoff_id}",
            json={"text_notes": "Attempted update"}
        )

        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()


class TestSubmitHandoffEndpoint:
    """Tests for POST /api/v1/handoff/{id}/submit endpoint."""

    def test_submit_handoff_success(self, authenticated_client):
        """Test successful handoff submission."""
        client, _ = authenticated_client("test-submit-user")

        # Create a handoff
        create_response = client.post("/api/v1/handoff/", json={})
        handoff_id = create_response.json()["id"]

        # Submit it
        response = client.post(f"/api/v1/handoff/{handoff_id}/submit")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "pending_acknowledgment"

    def test_submit_already_submitted_fails(self, authenticated_client):
        """Test submitting already submitted handoff fails."""
        client, _ = authenticated_client("test-double-submit-user")

        # Create and submit
        create_response = client.post("/api/v1/handoff/", json={})
        handoff_id = create_response.json()["id"]
        client.post(f"/api/v1/handoff/{handoff_id}/submit")

        # Try to submit again
        response = client.post(f"/api/v1/handoff/{handoff_id}/submit")

        assert response.status_code == 400


class TestShiftDetection:
    """Tests for shift detection utilities used by endpoints."""

    def test_shift_detection_returns_valid_type(self, authenticated_client):
        """Test shift detection returns a valid shift type."""
        client, _ = authenticated_client()
        response = client.get("/api/v1/handoff/initiate")
        data = response.json()

        shift_type = data["shift_info"]["shift_type"]
        assert shift_type in ["morning", "afternoon", "night"]

    def test_shift_info_has_8_hour_range(self, authenticated_client):
        """Test shift time range is 8 hours."""
        client, _ = authenticated_client()
        response = client.get("/api/v1/handoff/initiate")
        data = response.json()

        start = datetime.fromisoformat(data["shift_info"]["start_time"].replace('Z', '+00:00'))
        end = datetime.fromisoformat(data["shift_info"]["end_time"].replace('Z', '+00:00'))

        duration = (end - start).total_seconds() / 3600
        assert duration == 8.0
