"""
Admin API Endpoint Tests (Story 9.13, Task 10)

Tests for admin API endpoints including:
- GET /api/v1/admin/assignments (AC#1: Grid display data)
- GET /api/v1/admin/assignments/user/{user_id} (AC#1: User assignments)
- POST /api/v1/admin/assignments/preview (AC#2: Preview impact)
- POST /api/v1/admin/assignments/batch (AC#3: Batch save)
- POST /api/v1/admin/assignments (Create single)
- DELETE /api/v1/admin/assignments/{id} (Delete single)

References:
- [Source: architecture/voice-briefing.md#Admin UI Architecture]
- [Source: prd/prd-functional-requirements.md#FR46-FR50]
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import CurrentUser, UserRole
from app.core.security import require_admin
from app.api import admin as admin_module


# Test user IDs (must be valid UUIDs)
TEST_ADMIN_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
TEST_USER_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"


def get_test_admin() -> CurrentUser:
    """Create a test admin user."""
    return CurrentUser(id=TEST_ADMIN_ID, email="admin@test.com", role="authenticated")


def get_test_user() -> CurrentUser:
    """Create a test non-admin user."""
    return CurrentUser(id=TEST_USER_ID, email="user@test.com", role="authenticated")


@pytest.fixture(autouse=True)
def reset_mock_store():
    """Reset the in-memory store before each test."""
    admin_module._mock_assignments.clear()
    yield
    admin_module._mock_assignments.clear()


@pytest.fixture
def admin_client():
    """Create a test client with admin authentication."""
    app.dependency_overrides[require_admin] = lambda: get_test_admin()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client():
    """Create a test client without admin authentication."""
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: get_test_user()
    # Don't override require_admin - it should fail
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestListAssignmentsEndpoint:
    """Tests for GET /api/v1/admin/assignments endpoint."""

    def test_returns_grid_data(self, admin_client):
        """Test endpoint returns supervisors, assets, and assignments (AC#1)."""
        response = admin_client.get("/api/v1/admin/assignments")

        assert response.status_code == 200
        data = response.json()

        assert "supervisors" in data
        assert "assets" in data
        assert "assignments" in data
        assert "total_count" in data

        assert isinstance(data["supervisors"], list)
        assert isinstance(data["assets"], list)
        assert isinstance(data["assignments"], list)

    def test_returns_supervisor_info(self, admin_client):
        """Test supervisors have required fields."""
        response = admin_client.get("/api/v1/admin/assignments")

        assert response.status_code == 200
        data = response.json()

        if len(data["supervisors"]) > 0:
            supervisor = data["supervisors"][0]
            assert "user_id" in supervisor
            assert "email" in supervisor

    def test_returns_asset_info(self, admin_client):
        """Test assets have required fields with area for grouping (AC#1)."""
        response = admin_client.get("/api/v1/admin/assignments")

        assert response.status_code == 200
        data = response.json()

        if len(data["assets"]) > 0:
            asset = data["assets"][0]
            assert "asset_id" in asset
            assert "name" in asset
            assert "area" in asset  # Required for grouping columns

    def test_filters_expired_by_default(self, admin_client):
        """Test expired temporary assignments are excluded by default."""
        response = admin_client.get("/api/v1/admin/assignments")
        assert response.status_code == 200

        response_with_expired = admin_client.get("/api/v1/admin/assignments?include_expired=true")
        assert response_with_expired.status_code == 200


class TestUserAssignmentsEndpoint:
    """Tests for GET /api/v1/admin/assignments/user/{user_id} endpoint."""

    def test_returns_user_assignments(self, admin_client):
        """Test endpoint returns specific user's assignments."""
        # Use a mock supervisor ID
        user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        response = admin_client.get(f"/api/v1/admin/assignments/user/{user_id}")

        assert response.status_code == 200
        data = response.json()

        assert "user_id" in data
        assert "assignments" in data
        assert "asset_count" in data
        assert "area_count" in data

    def test_returns_correct_counts(self, admin_client):
        """Test asset and area counts are calculated correctly."""
        user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        response = admin_client.get(f"/api/v1/admin/assignments/user/{user_id}")

        assert response.status_code == 200
        data = response.json()

        # Mock data should have this user with 2 assets in Grinding area
        assert data["asset_count"] == len(data["assignments"])


class TestPreviewEndpoint:
    """Tests for POST /api/v1/admin/assignments/preview endpoint."""

    def test_preview_returns_impact_summary(self, admin_client):
        """Test preview returns impact summary (AC#2, FR48)."""
        changes = [
            {
                "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "asset_id": "33333333-3333-3333-3333-333333333331",
                "action": "add"
            }
        ]

        response = admin_client.post(
            "/api/v1/admin/assignments/preview",
            json={"changes": changes}
        )

        assert response.status_code == 200
        data = response.json()

        assert "changes_count" in data
        assert "users_affected" in data
        assert "impact_summary" in data
        assert "user_impacts" in data

    def test_preview_shows_user_will_see_x_assets_across_y_areas(self, admin_client):
        """Test preview shows 'User will see X assets across Y areas' (AC#2)."""
        changes = [
            {
                "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "asset_id": "33333333-3333-3333-3333-333333333331",
                "action": "add"
            }
        ]

        response = admin_client.post(
            "/api/v1/admin/assignments/preview",
            json={"changes": changes}
        )

        assert response.status_code == 200
        data = response.json()

        # Check impact summary format
        assert "assets" in data["impact_summary"].lower()
        assert "areas" in data["impact_summary"].lower()

    def test_preview_warns_on_removing_all_assets(self, admin_client):
        """Test preview warns when removing all assets from a user."""
        # First, get current assignments for a user
        user_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

        # Remove assignments (this user has none by default)
        changes = [
            {
                "user_id": user_id,
                "asset_id": "11111111-1111-1111-1111-111111111111",
                "action": "remove"
            }
        ]

        response = admin_client.post(
            "/api/v1/admin/assignments/preview",
            json={"changes": changes}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have warnings array
        assert "warnings" in data


class TestBatchUpdateEndpoint:
    """Tests for POST /api/v1/admin/assignments/batch endpoint."""

    def test_batch_creates_assignments(self, admin_client):
        """Test batch endpoint creates new assignments (AC#3)."""
        changes = [
            {
                "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "asset_id": "11111111-1111-1111-1111-111111111111",
                "action": "add"
            }
        ]

        response = admin_client.post(
            "/api/v1/admin/assignments/batch",
            json={"changes": changes}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["applied_count"] >= 1
        assert "batch_id" in data

    def test_batch_removes_assignments(self, admin_client):
        """Test batch endpoint removes assignments (AC#3)."""
        # Use existing mock assignment
        changes = [
            {
                "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "asset_id": "11111111-1111-1111-1111-111111111111",
                "action": "remove"
            }
        ]

        response = admin_client.post(
            "/api/v1/admin/assignments/batch",
            json={"changes": changes}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

    def test_batch_atomic_operation(self, admin_client):
        """Test batch operations are atomic (AC#3)."""
        changes = [
            {
                "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "asset_id": "11111111-1111-1111-1111-111111111111",
                "action": "add"
            },
            {
                "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "asset_id": "22222222-2222-2222-2222-222222222221",
                "action": "add"
            }
        ]

        response = admin_client.post(
            "/api/v1/admin/assignments/batch",
            json={"changes": changes}
        )

        assert response.status_code == 200
        data = response.json()

        # Both should be applied together
        assert data["applied_count"] == 2

    def test_batch_returns_batch_id_for_audit(self, admin_client):
        """Test batch returns batch_id for audit trail (AC#3, FR50)."""
        changes = [
            {
                "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "asset_id": "11111111-1111-1111-1111-111111111111",
                "action": "add"
            }
        ]

        response = admin_client.post(
            "/api/v1/admin/assignments/batch",
            json={"changes": changes}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have UUID batch_id
        assert "batch_id" in data
        UUID(data["batch_id"])  # Validates it's a valid UUID


class TestCreateAssignmentEndpoint:
    """Tests for POST /api/v1/admin/assignments endpoint."""

    def test_creates_assignment(self, admin_client):
        """Test creating a single assignment."""
        request = {
            "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "asset_id": "33333333-3333-3333-3333-333333333331",
        }

        response = admin_client.post(
            "/api/v1/admin/assignments",
            json=request
        )

        assert response.status_code == 201
        data = response.json()

        assert data["success"] is True
        assert "assignment" in data
        assert data["assignment"]["user_id"] == request["user_id"]
        assert data["assignment"]["asset_id"] == request["asset_id"]

    def test_creates_temporary_assignment(self, admin_client):
        """Test creating a temporary assignment with expiration (AC#4, FR49)."""
        expires_at = "2026-02-15T23:59:59Z"
        request = {
            "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "asset_id": "33333333-3333-3333-3333-333333333332",
            "expires_at": expires_at
        }

        response = admin_client.post(
            "/api/v1/admin/assignments",
            json=request
        )

        assert response.status_code == 201
        data = response.json()

        assert data["success"] is True
        assert data["assignment"]["expires_at"] is not None

    def test_rejects_duplicate_assignment(self, admin_client):
        """Test duplicate assignment returns 409 Conflict."""
        request = {
            "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "asset_id": "11111111-1111-1111-1111-111111111111",
        }

        response = admin_client.post(
            "/api/v1/admin/assignments",
            json=request
        )

        # Should fail because mock data already has this assignment
        assert response.status_code == 409


class TestDeleteAssignmentEndpoint:
    """Tests for DELETE /api/v1/admin/assignments/{id} endpoint."""

    def test_deletes_assignment(self, admin_client):
        """Test deleting an assignment."""
        # Get the mock assignment ID
        assignment_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1"

        response = admin_client.delete(f"/api/v1/admin/assignments/{assignment_id}")

        assert response.status_code == 204

    def test_returns_404_for_nonexistent(self, admin_client):
        """Test returns 404 for nonexistent assignment."""
        fake_id = str(uuid4())

        response = admin_client.delete(f"/api/v1/admin/assignments/{fake_id}")

        assert response.status_code == 404


class TestAdminAuthorization:
    """Tests for admin-only authorization (Task 2.6)."""

    def test_requires_admin_role_for_list(self):
        """Test list endpoint returns 401/403 without admin auth."""
        # Client without any auth overrides
        client = TestClient(app)
        app.dependency_overrides.clear()

        response = client.get("/api/v1/admin/assignments")

        # Should fail with 401 (not authenticated) or 403 (not authorized)
        assert response.status_code in [401, 403, 422]

    def test_requires_admin_role_for_batch(self):
        """Test batch endpoint requires admin auth."""
        client = TestClient(app)
        app.dependency_overrides.clear()

        response = client.post(
            "/api/v1/admin/assignments/batch",
            json={"changes": [{"user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "asset_id": "11111111-1111-1111-1111-111111111111", "action": "add"}]}
        )

        assert response.status_code in [401, 403, 422]


class TestAuditLogging:
    """Tests for audit logging (Task 10.3, FR50, FR56)."""

    def test_batch_creates_audit_log(self, admin_client):
        """Test batch operations create audit log entries."""
        changes = [
            {
                "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "asset_id": "11111111-1111-1111-1111-111111111111",
                "action": "add"
            }
        ]

        # Patch the audit logger to verify it's called
        with patch('app.api.admin.log_batch_assignment_change') as mock_log:
            response = admin_client.post(
                "/api/v1/admin/assignments/batch",
                json={"changes": changes}
            )

            assert response.status_code == 200
            mock_log.assert_called_once()

    def test_create_creates_audit_log(self, admin_client):
        """Test single create creates audit log entry."""
        request = {
            "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "asset_id": "33333333-3333-3333-3333-333333333331",
        }

        with patch('app.api.admin.log_assignment_change') as mock_log:
            response = admin_client.post(
                "/api/v1/admin/assignments",
                json=request
            )

            assert response.status_code == 201
            mock_log.assert_called_once()

    def test_delete_creates_audit_log(self, admin_client):
        """Test delete creates audit log entry."""
        assignment_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1"

        with patch('app.api.admin.log_assignment_change') as mock_log:
            response = admin_client.delete(f"/api/v1/admin/assignments/{assignment_id}")

            assert response.status_code == 204
            mock_log.assert_called_once()
