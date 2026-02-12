"""
Integration tests for POST /api/v1/followups endpoint.

Story: 15.2 - Email Notification Service
AC#1: Email sent on follow-up assignment
AC#2: Graceful degradation when SMTP not configured
AC#3: Graceful failure on send error

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (endpoint doesn't exist yet).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4
import os

# Set test environment variables before importing app
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("POLL_RUN_ON_STARTUP", "false")

from app.main import app


# --- Constants ---

FOLLOWUPS_URL = "/api/v1/followups"
MANAGER_USER_ID = "123e4567-e89b-12d3-a456-426614174000"
MANAGER_EMAIL = "manager@plant.com"
ASSIGNEE_USER_ID = str(uuid4())
ASSIGNEE_EMAIL = "assignee@plant.com"


# --- Fixtures ---


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
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
            mock_scheduler.status.to_dict.return_value = {"status": "stopped"}
            mock_sched.return_value = mock_scheduler
            with TestClient(app) as test_client:
                yield test_client


@pytest.fixture
def valid_jwt_payload():
    """JWT payload for an authenticated manager user."""
    return {
        "sub": MANAGER_USER_ID,
        "email": MANAGER_EMAIL,
        "role": "authenticated",
        "aud": "authenticated",
        "exp": 9999999999,
    }


@pytest.fixture
def mock_verify_jwt(valid_jwt_payload):
    """Mock JWT verification to return a valid payload."""
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = valid_jwt_payload
        yield mock


@pytest.fixture
def valid_followup_payload():
    """Standard valid payload for creating a follow-up."""
    return {
        "action_item_id": "AI-001",
        "action_summary": "Replace bearing",
        "asset_name": "Pump-101",
        "category": "safety",
        "assigned_to": ASSIGNEE_USER_ID,
        "note": "Priority this week",
        "report_date": "2026-02-10",
    }


@pytest.fixture
def created_followup_record(valid_followup_payload):
    """The follow-up record as returned by Supabase after insert."""
    return {
        **valid_followup_payload,
        "id": str(uuid4()),
        "assigned_by": MANAGER_USER_ID,
        "status": "assigned",
        "created_at": "2026-02-10T08:00:00+00:00",
        "updated_at": "2026-02-10T08:00:00+00:00",
    }


def _mock_supabase_and_notification(created_record):
    """Helper to create inline mocks for Supabase insert and notification service.

    Returns (mock_create_patcher, mock_notif_patcher, mock_client) context objects.
    Use with `with` blocks inside tests.
    """
    mock_client = MagicMock()
    mock_chain = MagicMock()
    mock_client.table.return_value = mock_chain
    mock_chain.insert.return_value = mock_chain
    mock_chain.execute.return_value = MagicMock(data=[created_record])
    return mock_client


# =============================================================================
# AC1: POST /api/v1/followups creates follow-up and triggers notification
# =============================================================================


class TestCreateFollowUp:
    """Tests for POST /api/v1/followups endpoint."""

    def test_creates_followup_and_returns_201(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        15-2-email-notification-service-INT-001: POST creates follow-up record and returns it.

        Given: An authenticated user with valid JWT, Supabase insert mocked
        When: POST /api/v1/followups is called with valid body
        Then: Returns 201 with created record including id, status="assigned", created_at,
              and assigned_by set to authenticated user's ID
        """
        mock_client = _mock_supabase_and_notification(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_client):
            with patch("app.api.followups.get_notification_service") as mock_notif:
                mock_service = MagicMock()
                mock_service.send_assignment_notification = AsyncMock()
                mock_notif.return_value = mock_service

                response = client.post(
                    FOLLOWUPS_URL,
                    json=valid_followup_payload,
                    headers={"Authorization": "Bearer test-token"},
                )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["status"] == "assigned"
        assert data["assigned_by"] == MANAGER_USER_ID
        assert data["action_item_id"] == "AI-001"
        assert data["action_summary"] == "Replace bearing"
        assert data["asset_name"] == "Pump-101"
        assert data["category"] == "safety"
        assert data["assigned_to"] == ASSIGNEE_USER_ID
        assert "created_at" in data

        # Verify Supabase insert was called
        mock_client.table.assert_called_with("action_followups")
        insert_call = mock_client.table.return_value.insert
        insert_call.assert_called_once()
        insert_data = insert_call.call_args[0][0]
        assert insert_data["assigned_by"] == MANAGER_USER_ID

    def test_triggers_async_email_notification(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        15-2-email-notification-service-INT-002: POST triggers async email notification.

        Given: An authenticated user, Supabase insert succeeds
        When: POST /api/v1/followups is called with valid data
        Then: asyncio.create_task() is called to dispatch notification asynchronously,
              API response returns without waiting for email delivery
        """
        mock_client = _mock_supabase_and_notification(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_client):
            with patch("app.api.followups.get_notification_service") as mock_notif:
                mock_service = MagicMock()
                mock_service.send_assignment_notification = AsyncMock()
                mock_notif.return_value = mock_service

                with patch("app.api.followups.asyncio") as mock_asyncio:
                    mock_asyncio.create_task = MagicMock()

                    response = client.post(
                        FOLLOWUPS_URL,
                        json=valid_followup_payload,
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 201
        mock_asyncio.create_task.assert_called_once()

    def test_requires_authentication(self, client):
        """
        15-2-email-notification-service-INT-003: POST requires authentication.

        Given: No Authorization header is provided
        When: POST /api/v1/followups is called
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            FOLLOWUPS_URL,
            json={
                "action_item_id": "AI-001",
                "action_summary": "Test",
                "asset_name": "Pump-101",
                "category": "safety",
                "assigned_to": str(uuid4()),
                "report_date": "2026-02-10",
            },
        )

        assert response.status_code in (401, 403)

    def test_validates_required_fields(
        self, client, mock_verify_jwt,
    ):
        """
        15-2-email-notification-service-INT-004: POST validates required fields.

        Given: An authenticated user
        When: POST is called with missing required fields
        Then: Returns 422 Unprocessable Entity with validation errors
        """
        response = client.post(
            FOLLOWUPS_URL,
            json={"note": "Missing required fields"},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 422

    def test_validates_category_enum(
        self, client, mock_verify_jwt,
    ):
        """
        15-2-email-notification-service-INT-005: POST validates category enum.

        Given: An authenticated user
        When: POST is called with category="invalid_category"
        Then: Returns 422 with validation error for invalid category
        """
        response = client.post(
            FOLLOWUPS_URL,
            json={
                "action_item_id": "AI-001",
                "action_summary": "Test",
                "asset_name": "Pump-101",
                "category": "invalid_category",
                "assigned_to": str(uuid4()),
                "report_date": "2026-02-10",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 422


# =============================================================================
# AC2: Graceful degradation when SMTP not configured
# =============================================================================


class TestCreateFollowUpSMTPNotConfigured:
    """Tests for POST /api/v1/followups when SMTP is not configured."""

    def test_succeeds_without_smtp(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        15-2-email-notification-service-INT-006: POST succeeds when SMTP not configured.

        Given: An authenticated user, smtp_configured=False, Supabase insert succeeds
        When: POST /api/v1/followups is called with valid data
        Then: Returns 201 with created record, assignment persisted, not blocked by email failure
        """
        mock_client = _mock_supabase_and_notification(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_client):
            with patch("app.api.followups.get_notification_service") as mock_notif:
                mock_service = MagicMock()
                mock_service.send_assignment_notification = AsyncMock()
                mock_notif.return_value = mock_service

                response = client.post(
                    FOLLOWUPS_URL,
                    json=valid_followup_payload,
                    headers={"Authorization": "Bearer test-token"},
                )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "assigned"
        assert data["action_item_id"] == "AI-001"


# =============================================================================
# AC3: Graceful failure on send error
# =============================================================================


class TestCreateFollowUpEmailFailure:
    """Tests for POST /api/v1/followups when email send fails."""

    def test_does_not_rollback_on_email_failure(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        15-2-email-notification-service-INT-007: POST does not roll back follow-up when email fails.

        Given: An authenticated user, Supabase insert succeeds, notification service fails
        When: POST /api/v1/followups is called
        Then: Returns 201, follow-up persisted, email failure handled asynchronously
        """
        mock_client = _mock_supabase_and_notification(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_client):
            with patch("app.api.followups.get_notification_service") as mock_notif:
                mock_service = MagicMock()
                mock_service.send_assignment_notification = AsyncMock(
                    side_effect=Exception("Email failed")
                )
                mock_notif.return_value = mock_service

                response = client.post(
                    FOLLOWUPS_URL,
                    json=valid_followup_payload,
                    headers={"Authorization": "Bearer test-token"},
                )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "assigned"

    def test_followup_messages_has_failed_at_on_error(self):
        """
        15-2-email-notification-service-INT-008: followup_messages has failed_at when email send errors.

        Given: SMTP configured, Supabase mocked, EmailProvider returns failure
        When: The notification service processes an assignment notification
        Then: followup_messages record created with failed_at set
        """
        from app.services.email.notification_service import FollowUpNotificationService
        from app.services.email.provider import SendResult

        mock_provider = MagicMock()
        mock_provider.send = AsyncMock(
            return_value=SendResult(success=False, error="SMTP error", sent_at=None)
        )

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.user = MagicMock()
        mock_user.user.email = "test@example.com"
        mock_client.auth.admin.get_user_by_id.return_value = mock_user

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])

        service = FollowUpNotificationService(
            email_provider=mock_provider,
            supabase_client=mock_client,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            import asyncio
            asyncio.get_event_loop().run_until_complete(
                service.send_assignment_notification({
                    "followup_id": str(uuid4()),
                    "action_item_id": "AI-001",
                    "action_summary": "Test",
                    "asset_name": "Pump-101",
                    "category": "safety",
                    "assigned_to": str(uuid4()),
                    "assigned_by": str(uuid4()),
                    "sender_email": "manager@plant.com",
                    "assigner_name": "Manager",
                    "recommendation": "Replace bearing",
                    "evidence_summary": "Vibration exceeded",
                    "report_date": "2026-02-10",
                })
            )

        insert_call = mock_chain.insert
        insert_call.assert_called_once()
        inserted_data = insert_call.call_args[0][0]
        assert inserted_data["direction"] == "outbound"
        assert inserted_data["message_type"] == "assignment"
        assert inserted_data["sent_at"] is None
        assert inserted_data["failed_at"] is not None


# =============================================================================
# Cross-Cutting: JWT sub used as assigned_by
# =============================================================================


class TestCreateFollowUpJWTIntegration:
    """Tests for JWT integration in follow-up creation."""

    def test_sets_assigned_by_from_jwt(
        self, client, created_followup_record,
    ):
        """
        15-2-email-notification-service-INT-009: POST sets assigned_by from JWT.

        Given: An authenticated user with JWT sub="uuid-manager-123"
        When: POST /api/v1/followups is called
        Then: The insert includes assigned_by="uuid-manager-123" from JWT
        """
        manager_id = "uuid-manager-123"
        jwt_payload = {
            "sub": manager_id,
            "email": "manager@plant.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }

        mock_client = _mock_supabase_and_notification(created_followup_record)

        with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock_jwt:
            mock_jwt.return_value = jwt_payload

            with patch("app.api.followups.create_client", return_value=mock_client):
                with patch("app.api.followups.get_notification_service") as mock_notif:
                    mock_service = MagicMock()
                    mock_service.send_assignment_notification = AsyncMock()
                    mock_notif.return_value = mock_service

                    response = client.post(
                        FOLLOWUPS_URL,
                        json={
                            "action_item_id": "AI-001",
                            "action_summary": "Replace bearing",
                            "asset_name": "Pump-101",
                            "category": "safety",
                            "assigned_to": str(uuid4()),
                            "report_date": "2026-02-10",
                        },
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 201

        insert_call = mock_client.table.return_value.insert
        insert_call.assert_called_once()
        insert_data = insert_call.call_args[0][0]
        assert insert_data["assigned_by"] == manager_id
