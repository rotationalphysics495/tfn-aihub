"""
Tests for authentication endpoints and JWT validation.

Test Coverage for Story 1.2 Acceptance Criteria:
- AC#3: JWT tokens are validated in FastAPI backend for all protected API endpoints
- AC#4: Unauthenticated requests are rejected with appropriate 401 response
- AC#7: Error handling provides clear feedback for invalid credentials
"""
import pytest
from fastapi import HTTPException, status


class TestHealthEndpoint:
    """Tests for the public health endpoint."""

    def test_health_check_no_auth_required(self, client):
        """Health check should be accessible without authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuthEndpoints:
    """Tests for auth-related endpoints."""

    def test_get_current_user_without_token(self, client):
        """AC#4: Should return 401 when no token provided."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_current_user_with_valid_token(self, client, mock_verify_jwt):
        """AC#3: Should return user info when valid token provided."""
        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert data["email"] == "test@example.com"
        assert data["role"] == "authenticated"

    def test_verify_auth_with_valid_token(self, client, mock_verify_jwt):
        """AC#3: Should verify authentication successfully."""
        response = client.get(
            "/api/auth/verify", headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user_id"] == "123e4567-e89b-12d3-a456-426614174000"

    def test_verify_auth_with_expired_token(self, client, mock_verify_jwt_expired):
        """AC#7: Should return 401 with clear message for expired token."""
        response = client.get(
            "/api/auth/verify", headers={"Authorization": "Bearer expired-token"}
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_verify_auth_with_invalid_token(self, client, mock_verify_jwt_invalid):
        """AC#7: Should return 401 with clear message for invalid token."""
        response = client.get(
            "/api/auth/verify", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


class TestProtectedAssetEndpoints:
    """Tests for protected asset endpoints."""

    def test_list_assets_without_token(self, client):
        """AC#4: Should reject unauthenticated requests to assets with 401."""
        response = client.get("/api/assets/")
        assert response.status_code == 401

    def test_list_assets_with_valid_token(self, client, mock_verify_jwt):
        """AC#3: Should allow access with valid token."""
        response = client.get(
            "/api/assets/", headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200

    def test_get_asset_without_token(self, client):
        """AC#4: Should reject unauthenticated requests with 401."""
        response = client.get("/api/assets/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 401


class TestProtectedSummaryEndpoints:
    """Tests for protected summary endpoints."""

    def test_list_summaries_without_token(self, client):
        """AC#4: Should reject unauthenticated requests to summaries with 401."""
        response = client.get("/api/summaries/daily")
        assert response.status_code == 401

    def test_list_summaries_with_valid_token(self, client, mock_verify_jwt):
        """AC#3: Should allow access with valid token."""
        response = client.get(
            "/api/summaries/daily", headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200


class TestProtectedActionEndpoints:
    """Tests for protected action endpoints."""

    def test_list_actions_without_token(self, client):
        """AC#4: Should reject unauthenticated requests to actions with 401."""
        response = client.get("/api/actions/daily")
        assert response.status_code == 401

    def test_list_actions_with_valid_token(self, client, mock_verify_jwt, mock_action_engine):
        """AC#3: Should allow access with valid token."""
        from unittest.mock import AsyncMock, MagicMock
        from datetime import date, datetime, timedelta
        from app.schemas.action import ActionListResponse

        # Mock the action engine response
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=ActionListResponse(
                actions=[],
                generated_at=datetime.utcnow(),
                report_date=date.today() - timedelta(days=1),
                total_count=0,
                counts_by_category={"safety": 0, "oee": 0, "financial": 0}
            )
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily", headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200

    def test_list_safety_actions_without_token(self, client):
        """AC#4: Should reject unauthenticated requests to safety actions with 401."""
        response = client.get("/api/actions/safety")
        assert response.status_code == 401

    def test_list_safety_actions_with_valid_token(self, client, mock_verify_jwt):
        """AC#3: Should allow access with valid token."""
        response = client.get(
            "/api/actions/safety", headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_no_auth_required(self, client):
        """Root endpoint should be accessible without authentication."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Manufacturing Performance Assistant" in response.json()["message"]
