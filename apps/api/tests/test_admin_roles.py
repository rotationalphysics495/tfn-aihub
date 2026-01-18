"""
Tests for Admin Role Management API (Story 9.14)

Test Coverage:
- AC#1: List users with current roles
- AC#2: Update user role with audit logging
- AC#3: Prevent removing last admin
- AC#4: Default Supervisor role for new users (tested via migration)

References:
- [Source: architecture/voice-briefing.md#Admin UI Architecture]
- [Source: prd/prd-functional-requirements.md#FR47, FR56]
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.models.admin import UserRole, UserWithRole, UserListResponse, RoleUpdateResponse


@pytest.fixture(autouse=True)
def reset_mock_user_roles():
    """Reset mock user roles before and after each test to prevent state leaks."""
    from app.api.admin import _mock_user_roles
    _mock_user_roles.clear()
    yield
    _mock_user_roles.clear()


class TestAdminRoleEndpoints:
    """Tests for admin role management endpoints."""

    @pytest.fixture
    def admin_user_id(self):
        """Admin user ID for tests."""
        return "dddddddd-dddd-dddd-dddd-dddddddddddd"

    @pytest.fixture
    def mock_jwt_verify_admin(self, admin_user_id):
        """Mock JWT verification to return admin payload."""
        with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "sub": admin_user_id,
                "email": "admin@example.com",
                "role": "service_role",
                "aud": "authenticated",
                "exp": 9999999999,
            }
            yield mock

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client to return None (use mock data)."""
        with patch("app.api.admin._get_supabase_client", return_value=None):
            yield

    def test_list_users_returns_all_users(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """
        AC#1: Admins see a list of users with current roles.
        """
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert "total_count" in data
        assert data["total_count"] == len(data["users"])
        assert data["total_count"] > 0

        # Verify user structure
        for user in data["users"]:
            assert "user_id" in user
            assert "email" in user
            assert "role" in user
            assert user["role"] in ["supervisor", "plant_manager", "admin"]

    def test_list_users_unauthorized(self, client):
        """Unauthenticated requests should be rejected."""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    def test_get_single_user(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """Get a specific user by ID."""
        # Use a known mock user ID
        user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

        response = client.get(
            f"/api/v1/admin/users/{user_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == user_id
        assert "email" in data
        assert "role" in data

    def test_get_user_not_found(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """Should return 404 for unknown user."""
        unknown_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/admin/users/{unknown_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_user_role_supervisor_to_manager(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """
        AC#2: Admin changes a user's role, role is updated.
        """
        # Use a known supervisor user ID
        user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

        # Mock audit at the import location in admin.py
        with patch("app.api.admin.log_role_change") as mock_audit:
            response = client.put(
                f"/api/v1/admin/users/{user_id}/role",
                headers={"Authorization": "Bearer test-token"},
                json={"role": "plant_manager"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["user"]["role"] == "plant_manager"
        assert "updated" in data["message"].lower()

        # Verify audit was called
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args.kwargs["target_user_id"] == user_id
        assert call_args.kwargs["old_role"] == "supervisor"
        assert call_args.kwargs["new_role"] == "plant_manager"

    def test_update_user_role_manager_to_admin(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """Can promote user to admin."""
        user_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"  # Plant manager

        with patch("app.api.admin.log_role_change"):
            response = client.put(
                f"/api/v1/admin/users/{user_id}/role",
                headers={"Authorization": "Bearer test-token"},
                json={"role": "admin"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "admin"

    def test_prevent_removing_last_admin(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """
        AC#3: System prevents removing the last admin.
        """
        # Set up mock data with exactly one admin (autouse fixture already cleared)
        from app.api.admin import _mock_user_roles

        now = datetime.now(timezone.utc).isoformat()
        admin_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        _mock_user_roles[admin_id] = {
            "user_id": admin_id,
            "email": "admin@example.com",
            "role": "admin",
            "created_at": now,
            "updated_at": now,
        }
        # Add a non-admin user
        _mock_user_roles["eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"] = {
            "user_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "email": "supervisor@example.com",
            "role": "supervisor",
            "created_at": now,
            "updated_at": now,
        }

        # Attempt to demote the only admin
        response = client.put(
            f"/api/v1/admin/users/{admin_id}/role",
            headers={"Authorization": "Bearer test-token"},
            json={"role": "supervisor"}
        )

        assert response.status_code == 400
        assert "last admin" in response.json()["detail"].lower()

    def test_update_role_user_not_found(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """Should return 404 for unknown user."""
        unknown_id = "00000000-0000-0000-0000-000000000000"

        response = client.put(
            f"/api/v1/admin/users/{unknown_id}/role",
            headers={"Authorization": "Bearer test-token"},
            json={"role": "admin"}
        )

        assert response.status_code == 404

    def test_update_role_invalid_role(
        self, client, mock_jwt_verify_admin, mock_supabase_client
    ):
        """Should reject invalid role values."""
        user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

        response = client.put(
            f"/api/v1/admin/users/{user_id}/role",
            headers={"Authorization": "Bearer test-token"},
            json={"role": "invalid_role"}
        )

        assert response.status_code == 422  # Validation error


class TestAuditLogging:
    """Tests for audit logging of role changes."""

    def test_log_role_change_creates_entry(self):
        """
        AC#2: Audit log entry is created for role changes.
        """
        from app.services.audit import AuditLogger

        logger = AuditLogger()  # Uses in-memory storage without Supabase

        admin_id = str(uuid4())
        target_id = str(uuid4())

        log_id = logger.log_role_change(
            admin_user_id=admin_id,
            target_user_id=target_id,
            old_role="supervisor",
            new_role="plant_manager",
            metadata={"source": "test"},
        )

        assert log_id is not None

        # Verify log was stored in memory
        assert len(logger._in_memory_logs) > 0
        log_entry = logger._in_memory_logs[-1]

        assert log_entry["admin_user_id"] == admin_id
        assert log_entry["target_user_id"] == target_id
        assert log_entry["action_type"] == "role_change"
        assert log_entry["before_value"]["role"] == "supervisor"
        assert log_entry["after_value"]["role"] == "plant_manager"


class TestUserRoleModels:
    """Tests for role management Pydantic models."""

    def test_user_with_role_model(self):
        """UserWithRole model validates correctly."""
        user = UserWithRole(
            user_id=uuid4(),
            email="test@example.com",
            role=UserRole.SUPERVISOR,
        )

        assert user.email == "test@example.com"
        assert user.role == UserRole.SUPERVISOR

    def test_user_role_enum_values(self):
        """UserRole enum has correct values."""
        assert UserRole.PLANT_MANAGER.value == "plant_manager"
        assert UserRole.SUPERVISOR.value == "supervisor"
        assert UserRole.ADMIN.value == "admin"

    def test_user_list_response_model(self):
        """UserListResponse model works correctly."""
        users = [
            UserWithRole(
                user_id=uuid4(),
                email="user1@example.com",
                role=UserRole.SUPERVISOR,
            ),
            UserWithRole(
                user_id=uuid4(),
                email="user2@example.com",
                role=UserRole.ADMIN,
            ),
        ]

        response = UserListResponse(users=users, total_count=2)
        assert response.total_count == 2
        assert len(response.users) == 2

    def test_role_update_response_model(self):
        """RoleUpdateResponse model works correctly."""
        user = UserWithRole(
            user_id=uuid4(),
            email="test@example.com",
            role=UserRole.PLANT_MANAGER,
        )

        response = RoleUpdateResponse(
            success=True,
            user=user,
            message="Role updated successfully",
        )

        assert response.success is True
        assert response.user.role == UserRole.PLANT_MANAGER
