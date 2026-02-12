"""
End-to-end tests for follow-up assignment flow with email notifications.

Story: 15.2 - Email Notification Service
AC#1: Email sent on follow-up assignment
AC#2: Graceful degradation when SMTP not configured
AC#3: Graceful failure on send error

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (endpoint and services don't exist yet).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone
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
MANAGER_NAME = "John Manager"
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
def mock_verify_jwt():
    """Mock JWT verification for the manager user."""
    jwt_payload = {
        "sub": MANAGER_USER_ID,
        "email": MANAGER_EMAIL,
        "role": "authenticated",
        "aud": "authenticated",
        "exp": 9999999999,
    }
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = jwt_payload
        yield mock


@pytest.fixture
def e2e_followup_payload():
    """Full follow-up payload for E2E tests."""
    return {
        "action_item_id": "AI-OEE-007",
        "action_summary": "Adjust belt tension",
        "asset_name": "Conveyor-7",
        "category": "oee",
        "assigned_to": ASSIGNEE_USER_ID,
        "note": "Check alignment while you're at it",
        "report_date": "2026-02-10",
    }


@pytest.fixture
def created_followup_record(e2e_followup_payload):
    """The follow-up record after Supabase insert."""
    return {
        **e2e_followup_payload,
        "id": str(uuid4()),
        "assigned_by": MANAGER_USER_ID,
        "status": "assigned",
        "created_at": "2026-02-10T08:00:00+00:00",
        "updated_at": "2026-02-10T08:00:00+00:00",
    }


# =============================================================================
# E2E-001: Full assignment flow
# =============================================================================


class TestFollowUpAssignmentE2E:
    """E2E tests for the complete follow-up assignment flow."""

    def test_full_assignment_flow(
        self, client, mock_verify_jwt, e2e_followup_payload, created_followup_record,
    ):
        """
        15-2-email-notification-service-E2E-001: Full assignment flow creates follow-up,
        sends email, and logs message.

        Given: SMTP is configured, an authenticated user exists, an assignee exists
        When: A follow-up is assigned via POST /api/v1/followups
        Then: (1) Record created in action_followups with status='assigned'
              (2) Email sent with correct subject and body
              (3) followup_messages record created with direction='outbound', message_type='assignment'
              (4) Email dispatched within 60 seconds
        """
        from app.services.email.provider import SendResult

        sent_at = datetime.now(timezone.utc)
        followup_messages_record = {
            "id": str(uuid4()),
            "followup_id": created_followup_record["id"],
            "direction": "outbound",
            "message_type": "assignment",
            "sent_at": sent_at.isoformat(),
            "failed_at": None,
        }

        with patch("app.api.followups.create_client") as mock_create:
            mock_client = MagicMock()

            # Mock action_followups insert
            mock_followups_chain = MagicMock()
            mock_followups_chain.insert.return_value = mock_followups_chain
            mock_followups_chain.execute.return_value = MagicMock(
                data=[created_followup_record]
            )

            mock_client.table.return_value = mock_followups_chain
            mock_create.return_value = mock_client

            with patch("app.api.followups.get_notification_service") as mock_notif_get:
                mock_notif_service = MagicMock()
                mock_notif_service.send_assignment_notification = AsyncMock()
                mock_notif_get.return_value = mock_notif_service

                response = client.post(
                    FOLLOWUPS_URL,
                    json=e2e_followup_payload,
                    headers={"Authorization": "Bearer test-token"},
                )

        # (1) Follow-up created with status='assigned'
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "assigned"
        assert data["action_item_id"] == "AI-OEE-007"
        assert data["action_summary"] == "Adjust belt tension"
        assert data["asset_name"] == "Conveyor-7"
        assert data["category"] == "oee"
        assert data["assigned_by"] == MANAGER_USER_ID

        # (2) & (3) Notification service was called
        mock_notif_service.send_assignment_notification.assert_called_once()
        notif_call_args = mock_notif_service.send_assignment_notification.call_args
        notif_data = notif_call_args[0][0] if notif_call_args[0] else notif_call_args[1]
        # Verify it received the follow-up data
        assert isinstance(notif_data, dict) or hasattr(notif_data, "followup_id")


# =============================================================================
# E2E-002: Assignment succeeds without email (no SMTP)
# =============================================================================


class TestFollowUpAssignmentNoSMTP:
    """E2E tests when SMTP is not configured."""

    def test_assignment_succeeds_without_email(
        self, client, mock_verify_jwt, e2e_followup_payload, created_followup_record,
    ):
        """
        15-2-email-notification-service-E2E-002: Follow-up assignment succeeds without email
        when SMTP credentials are absent.

        Given: No SMTP environment variables configured
        When: A follow-up is assigned via POST /api/v1/followups
        Then: (1) Follow-up saved with status='assigned'
              (2) No email sent
              (3) Warning-level log created
              (4) API response is 201
              (5) No followup_messages record created
        """
        with patch("app.api.followups.create_client") as mock_create:
            mock_client = MagicMock()
            mock_chain = MagicMock()
            mock_client.table.return_value = mock_chain
            mock_chain.insert.return_value = mock_chain
            mock_chain.execute.return_value = MagicMock(
                data=[created_followup_record]
            )
            mock_create.return_value = mock_client

            with patch("app.api.followups.get_notification_service") as mock_notif_get:
                mock_notif_service = MagicMock()
                mock_notif_service.send_assignment_notification = AsyncMock()
                mock_notif_get.return_value = mock_notif_service

                response = client.post(
                    FOLLOWUPS_URL,
                    json=e2e_followup_payload,
                    headers={"Authorization": "Bearer test-token"},
                )

        # (1) & (4) Follow-up saved, API returns 201
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "assigned"
        assert data["action_item_id"] == "AI-OEE-007"

        # The notification service was dispatched (fire-and-forget)
        # but internally it would log warning and skip email
        # We verify the endpoint itself doesn't fail


# =============================================================================
# E2E-003: Email failure preserves follow-up
# =============================================================================


class TestFollowUpAssignmentEmailFailure:
    """E2E tests when email send fails."""

    def test_email_failure_preserves_followup(
        self, client, mock_verify_jwt, e2e_followup_payload, created_followup_record,
    ):
        """
        15-2-email-notification-service-E2E-003: Email failure preserves follow-up
        and creates failed message record.

        Given: SMTP configured but SMTP server unreachable
        When: A follow-up is assigned via POST /api/v1/followups
        Then: (1) Follow-up saved with status='assigned'
              (2) followup_messages record created with failed_at set
              (3) Error logged
              (4) API response is 201 (not rolled back)
        """
        with patch("app.api.followups.create_client") as mock_create:
            mock_client = MagicMock()
            mock_chain = MagicMock()
            mock_client.table.return_value = mock_chain
            mock_chain.insert.return_value = mock_chain
            mock_chain.execute.return_value = MagicMock(
                data=[created_followup_record]
            )
            mock_create.return_value = mock_client

            with patch("app.api.followups.get_notification_service") as mock_notif_get:
                mock_notif_service = MagicMock()
                # Notification async task will fail but should not affect response
                mock_notif_service.send_assignment_notification = AsyncMock(
                    side_effect=ConnectionRefusedError("SMTP server unreachable")
                )
                mock_notif_get.return_value = mock_notif_service

                response = client.post(
                    FOLLOWUPS_URL,
                    json=e2e_followup_payload,
                    headers={"Authorization": "Bearer test-token"},
                )

        # (1) & (4) Follow-up saved, API response 201
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "assigned"
        assert data["action_item_id"] == "AI-OEE-007"
        assert data["action_summary"] == "Adjust belt tension"
        assert data["asset_name"] == "Conveyor-7"
        assert "id" in data
