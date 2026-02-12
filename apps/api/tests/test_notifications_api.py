"""
Tests for Notifications API endpoints.

Story: 18.2 - Teams Webhook Configuration
AC#2: Test message posting to configured Teams channel via API endpoint
AC#3: Graceful degradation when webhook not configured

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (notifications router
doesn't exist yet).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# =============================================================================
# AC2: POST /api/v1/notifications/teams/test — success and error cases
# =============================================================================


class TestTeamsTestEndpointSuccess:
    """Tests for successful teams test endpoint invocation."""

    def test_teams_test_returns_success_when_webhook_configured(
        self, client, mock_verify_jwt
    ):
        """
        18-2-teams-webhook-configuration-INT-001: POST /api/v1/notifications/teams/test
        returns success when webhook configured.

        Given: An authenticated user and TEAMS_WEBHOOK_URL is configured
        When: POST request is sent to /api/v1/notifications/teams/test
        Then: Response status code is 200
        And: Response JSON contains {"success": true, "message": "Message posted to Teams", "status_code": 200}
        """
        mock_result = {
            "success": True,
            "message": "Message posted to Teams",
            "status_code": 200,
        }

        with patch(
            "app.api.notifications.TeamsWebhookClient"
        ) as mock_client_cls:
            mock_instance = MagicMock()
            mock_instance.is_configured = True
            mock_instance.send_test_message = AsyncMock(return_value=mock_result)
            mock_client_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/notifications/teams/test",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Message posted to Teams"
        assert data["status_code"] == 200

    def test_teams_test_returns_failure_when_webhook_rejects(
        self, client, mock_verify_jwt
    ):
        """
        18-2-teams-webhook-configuration-INT-005: POST /api/v1/notifications/teams/test
        returns failure result when Teams webhook rejects.

        Given: An authenticated user and webhook configured, but Teams returns HTTP 403
        When: POST request is sent to /api/v1/notifications/teams/test
        Then: Response status code is 200 (endpoint itself succeeds)
        And: Response JSON contains {"success": false, "status_code": 403} with message including "HTTP 403"
        """
        mock_result = {
            "success": False,
            "message": "HTTP 403: Forbidden",
            "status_code": 403,
        }

        with patch(
            "app.api.notifications.TeamsWebhookClient"
        ) as mock_client_cls:
            mock_instance = MagicMock()
            mock_instance.is_configured = True
            mock_instance.send_test_message = AsyncMock(return_value=mock_result)
            mock_client_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/notifications/teams/test",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status_code"] == 403
        assert "HTTP 403" in data["message"]

    def test_teams_test_returns_failure_on_timeout(
        self, client, mock_verify_jwt
    ):
        """
        18-2-teams-webhook-configuration-INT-006: POST /api/v1/notifications/teams/test
        returns failure result on timeout.

        Given: An authenticated user and webhook configured, but Teams endpoint times out
        When: POST request is sent to /api/v1/notifications/teams/test
        Then: Response status code is 200 (endpoint itself succeeds)
        And: Response JSON contains {"success": false, "message": "Request timed out", "status_code": null}
        """
        mock_result = {
            "success": False,
            "message": "Request timed out",
            "status_code": None,
        }

        with patch(
            "app.api.notifications.TeamsWebhookClient"
        ) as mock_client_cls:
            mock_instance = MagicMock()
            mock_instance.is_configured = True
            mock_instance.send_test_message = AsyncMock(return_value=mock_result)
            mock_client_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/notifications/teams/test",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Request timed out"
        assert data["status_code"] is None


# =============================================================================
# AC2: POST /api/v1/notifications/teams/test — not configured
# =============================================================================


class TestTeamsTestEndpointNotConfigured:
    """Tests for teams test endpoint when webhook is not configured."""

    def test_teams_test_returns_400_when_webhook_not_configured(
        self, client, mock_verify_jwt
    ):
        """
        18-2-teams-webhook-configuration-INT-002: POST /api/v1/notifications/teams/test
        returns 400 when webhook not configured.

        Given: An authenticated user and TEAMS_WEBHOOK_URL is empty/not set
        When: POST request is sent to /api/v1/notifications/teams/test
        Then: Response status code is 400
        And: Response JSON detail contains "not configured"
        """
        with patch(
            "app.api.notifications.TeamsWebhookClient"
        ) as mock_client_cls:
            mock_instance = MagicMock()
            mock_instance.is_configured = False
            mock_client_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/notifications/teams/test",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 400
        data = response.json()
        assert "not configured" in data["detail"].lower()


# =============================================================================
# AC2: POST /api/v1/notifications/teams/test — authentication
# =============================================================================


class TestTeamsTestEndpointAuth:
    """Tests for authentication on teams test endpoint."""

    def test_teams_test_returns_401_when_unauthenticated(self, client):
        """
        18-2-teams-webhook-configuration-INT-003: POST /api/v1/notifications/teams/test
        returns 401 when unauthenticated.

        Given: No authentication token is provided
        When: POST request is sent to /api/v1/notifications/teams/test
        Then: Response status code is 401
        """
        response = client.post("/api/v1/notifications/teams/test")

        assert response.status_code == 401

    def test_teams_test_returns_401_with_expired_token(
        self, client, mock_verify_jwt_expired
    ):
        """
        18-2-teams-webhook-configuration-INT-004: POST /api/v1/notifications/teams/test
        returns 401 with expired token.

        Given: An expired JWT token is provided
        When: POST request is sent to /api/v1/notifications/teams/test
        Then: Response status code is 401
        And: Response JSON detail contains "expired"
        """
        response = client.post(
            "/api/v1/notifications/teams/test",
            headers={"Authorization": "Bearer expired-token"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()


# =============================================================================
# AC2: Notifications router registration
# =============================================================================


class TestNotificationsRouterRegistration:
    """Tests for notifications router registration in main.py."""

    def test_notifications_router_is_registered(self, client):
        """
        18-2-teams-webhook-configuration-INT-007: Notifications router is registered
        in main.py at correct prefix.

        Given: The FastAPI application is loaded
        When: The registered routes are inspected
        Then: A route exists at /api/v1/notifications/teams/test with POST method
        """
        from app.main import app

        # Collect all registered route paths and methods
        routes = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                routes.append((route.path, route.methods))

        # Check that the notifications teams test endpoint is registered
        teams_test_route = None
        for path, methods in routes:
            if path == "/api/v1/notifications/teams/test":
                teams_test_route = (path, methods)
                break

        assert teams_test_route is not None, (
            "Route /api/v1/notifications/teams/test must be registered in the app. "
            f"Available routes: {[path for path, _ in routes]}"
        )
        assert "POST" in teams_test_route[1], (
            "Route /api/v1/notifications/teams/test must accept POST method"
        )
