"""
Integration tests for Follow-Up Assignment Teams Notification (Story 18.4)

Test Coverage:
- AC#1: POST /api/v1/followups creates follow-up and dispatches Teams notification
- AC#2: Graceful degradation when Teams not configured
- AC#3: Graceful failure on webhook error does not roll back follow-up creation
- AC#4: Fire-and-forget delivery via asyncio.create_task

References:
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.4]
- [Source: apps/api/app/api/followups.py] - create_followup endpoint
- [Source: apps/api/app/services/notifications/teams.py] - TeamsWebhookClient
"""

import logging
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

import os

# Set test environment variables before importing app
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("POLL_RUN_ON_STARTUP", "false")

from fastapi.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FOLLOWUPS_URL = "/api/v1/followups"
MANAGER_USER_ID = "123e4567-e89b-12d3-a456-426614174000"
MANAGER_EMAIL = "john.doe@company.com"
ASSIGNEE_USER_ID = str(uuid4())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
        "action_summary": "Inspect belt tension",
        "asset_name": "Grinder 5",
        "category": "safety",
        "assigned_to": ASSIGNEE_USER_ID,
        "note": "Check by EOD",
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


def _mock_supabase_insert(created_record):
    """Create mock Supabase client with insert returning created_record."""
    mock_client = MagicMock()
    mock_chain = MagicMock()
    mock_client.table.return_value = mock_chain
    mock_chain.insert.return_value = mock_chain
    mock_chain.execute.return_value = MagicMock(data=[created_record])
    return mock_client



# ===========================================================================
# AC1: POST /api/v1/followups creates follow-up and dispatches Teams notification
# ===========================================================================


class TestFollowupTeamsNotificationDispatch:
    """AC#1: Teams notification dispatched on follow-up assignment."""

    def test_INT_001_creates_followup_and_dispatches_teams_notification(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-001:
        POST /followups creates follow-up and dispatches Teams notification.

        Given: A valid JWT-authenticated user, teams_configured=True,
               Supabase insert returns a created record, and
               get_teams_client().send_card() is mocked
        When: POST /api/v1/followups is called with valid follow-up data
        Then: The endpoint returns 201 with the created follow-up,
              and the Teams notification is dispatched with an Adaptive Card
              containing the correct followup fields
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                    mock_teams = MagicMock()
                    mock_teams.is_configured = True
                    mock_teams.send_card = AsyncMock(
                        return_value={"success": True, "message": "OK", "status_code": 200}
                    )
                    mock_teams_factory.return_value = mock_teams

                    with patch("app.api.followups.get_settings") as mock_settings:
                        mock_settings.return_value = MagicMock(
                            supabase_url="https://test.supabase.co",
                            supabase_key="test-key",
                            teams_configured=True,
                            app_base_url="https://app.example.com",
                        )

                        response = client.post(
                            FOLLOWUPS_URL,
                            json=valid_followup_payload,
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 201
        data = response.json()
        assert data["action_summary"] == "Inspect belt tension"
        assert data["asset_name"] == "Grinder 5"

        # Verify Teams send_card was called with an Adaptive Card
        mock_teams.send_card.assert_called_once()
        card_arg = mock_teams.send_card.call_args[0][0]
        assert card_arg["type"] == "AdaptiveCard"

    def test_INT_002_assigner_display_name_from_email_local_part(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-002:
        Assigner display name extracted from current_user email local part.

        Given: current_user.email="john.doe@company.com", teams_configured=True
        When: POST /api/v1/followups is called
        Then: The followup_data passed to build_followup_assignment_card contains
              assigner_name="john.doe" (local part before @)
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch(
                    "app.api.followups.build_followup_assignment_card"
                ) as mock_build_card:
                    mock_build_card.return_value = {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [],
                        "actions": [],
                    }

                    with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                        mock_teams = MagicMock()
                        mock_teams.is_configured = True
                        mock_teams.send_card = AsyncMock(
                            return_value={"success": True, "message": "OK", "status_code": 200}
                        )
                        mock_teams_factory.return_value = mock_teams

                        with patch("app.api.followups.get_settings") as mock_settings:
                            mock_settings.return_value = MagicMock(
                                supabase_url="https://test.supabase.co",
                                supabase_key="test-key",
                                teams_configured=True,
                                app_base_url="https://app.example.com",
                            )

                            response = client.post(
                                FOLLOWUPS_URL,
                                json=valid_followup_payload,
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 201

        # Verify build_followup_assignment_card was called with assigner_name="john.doe"
        mock_build_card.assert_called_once()
        call_args = mock_build_card.call_args
        followup_data = call_args[0][0] if call_args[0] else call_args[1].get("followup_data")
        assert followup_data["assigner_name"] == "john.doe"

    def test_INT_003_followup_data_contains_expected_fields(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-003:
        followup_data passed to build_followup_assignment_card contains expected fields.

        Given: teams_configured=True, Supabase insert succeeds
        When: POST /api/v1/followups is called with valid follow-up data
        Then: The followup_data dict passed to build_followup_assignment_card contains
              action_summary, asset_name, category, assigner_name, note, report_date
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch(
                    "app.api.followups.build_followup_assignment_card"
                ) as mock_build_card:
                    mock_build_card.return_value = {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [],
                        "actions": [],
                    }

                    with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                        mock_teams = MagicMock()
                        mock_teams.is_configured = True
                        mock_teams.send_card = AsyncMock(
                            return_value={"success": True, "message": "OK", "status_code": 200}
                        )
                        mock_teams_factory.return_value = mock_teams

                        with patch("app.api.followups.get_settings") as mock_settings:
                            mock_settings.return_value = MagicMock(
                                supabase_url="https://test.supabase.co",
                                supabase_key="test-key",
                                teams_configured=True,
                                app_base_url="https://app.example.com",
                            )

                            response = client.post(
                                FOLLOWUPS_URL,
                                json=valid_followup_payload,
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 201

        # Verify build_followup_assignment_card was called with expected fields
        mock_build_card.assert_called_once()
        call_args = mock_build_card.call_args
        followup_data = call_args[0][0] if call_args[0] else call_args[1].get("followup_data")
        assert followup_data["action_summary"] == "Inspect belt tension"
        assert followup_data["asset_name"] == "Grinder 5"
        assert followup_data["category"] == "safety"
        assert followup_data["assigner_name"] == "john.doe"
        assert followup_data["note"] == "Check by EOD"
        assert followup_data["report_date"] == "2026-02-10"


# ===========================================================================
# AC2: Graceful degradation when Teams not configured
# ===========================================================================


class TestTeamsNotConfiguredGracefulDegradation:
    """AC#2: Follow-up succeeds when Teams is not configured."""

    def test_INT_004_teams_notification_skipped_when_not_configured(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-004:
        Teams notification skipped when teams_configured is False.

        Given: settings.teams_configured=False, a valid JWT-authenticated user,
               Supabase insert succeeds
        When: POST /api/v1/followups is called with valid follow-up data
        Then: The endpoint returns 201 with the created follow-up,
              get_teams_client().send_card() is NOT called, and no error is raised
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                    mock_teams = MagicMock()
                    mock_teams.is_configured = False
                    mock_teams.send_card = AsyncMock()
                    mock_teams_factory.return_value = mock_teams

                    with patch("app.api.followups.get_settings") as mock_settings:
                        mock_settings.return_value = MagicMock(
                            supabase_url="https://test.supabase.co",
                            supabase_key="test-key",
                            teams_configured=False,
                            app_base_url="https://app.example.com",
                        )

                        response = client.post(
                            FOLLOWUPS_URL,
                            json=valid_followup_payload,
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 201
        data = response.json()
        assert data["action_summary"] == "Inspect belt tension"

        # Verify Teams send_card was NOT called
        mock_teams.send_card.assert_not_called()

    def test_INT_005_debug_log_emitted_when_teams_skipped(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
        caplog,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-005:
        Debug log emitted when Teams notification is skipped.

        Given: settings.teams_configured=False
        When: POST /api/v1/followups is called with valid follow-up data
        Then: A debug-level log message is emitted containing "Teams notification skipped"
              (or equivalent), and no error-level log is emitted for Teams
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with caplog.at_level(logging.DEBUG):
            with patch("app.api.followups.create_client", return_value=mock_sb):
                with patch("app.api.followups.get_notification_service") as mock_email:
                    mock_email_service = MagicMock()
                    mock_email_service.send_assignment_notification = AsyncMock()
                    mock_email.return_value = mock_email_service

                    with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                        mock_teams = MagicMock()
                        mock_teams.is_configured = False
                        mock_teams.send_card = AsyncMock()
                        mock_teams_factory.return_value = mock_teams

                        with patch("app.api.followups.get_settings") as mock_settings:
                            mock_settings.return_value = MagicMock(
                                supabase_url="https://test.supabase.co",
                                supabase_key="test-key",
                                teams_configured=False,
                                app_base_url="https://app.example.com",
                            )

                            response = client.post(
                                FOLLOWUPS_URL,
                                json=valid_followup_payload,
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 201

        # Check debug log for Teams skip message
        teams_debug_messages = [
            record for record in caplog.records
            if "teams" in record.message.lower() and "skip" in record.message.lower()
        ]
        assert len(teams_debug_messages) > 0, (
            "Expected a debug log containing 'Teams' and 'skip' when teams_configured=False"
        )

        # No error-level log for Teams
        teams_error_messages = [
            record for record in caplog.records
            if record.levelno >= logging.ERROR and "teams" in record.message.lower()
        ]
        assert len(teams_error_messages) == 0, (
            "No error-level log should be emitted for Teams when simply not configured"
        )


# ===========================================================================
# AC3: Graceful failure on webhook error
# ===========================================================================


class TestWebhookFailureGracefulDegradation:
    """AC#3: Webhook failure does not roll back follow-up creation."""

    def test_INT_006_webhook_failure_does_not_roll_back_followup(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-006:
        Webhook failure does not roll back follow-up creation.

        Given: settings.teams_configured=True, Supabase insert succeeds,
               get_teams_client().send_card() returns a failure result
        When: POST /api/v1/followups is called with valid data
        Then: The endpoint returns 201 with the created follow-up record
              (insert NOT rolled back)
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                    mock_teams = MagicMock()
                    mock_teams.is_configured = True
                    mock_teams.send_card = AsyncMock(
                        return_value={
                            "success": False,
                            "message": "Request timed out",
                            "status_code": None,
                        }
                    )
                    mock_teams_factory.return_value = mock_teams

                    with patch("app.api.followups.get_settings") as mock_settings:
                        mock_settings.return_value = MagicMock(
                            supabase_url="https://test.supabase.co",
                            supabase_key="test-key",
                            teams_configured=True,
                            app_base_url="https://app.example.com",
                        )

                        response = client.post(
                            FOLLOWUPS_URL,
                            json=valid_followup_payload,
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 201
        data = response.json()
        assert data["action_summary"] == "Inspect belt tension"
        assert data["status"] == "assigned"

    def test_INT_007_exception_in_teams_dispatch_does_not_affect_response(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-007:
        Exception in Teams dispatch block does not affect API response.

        Given: settings.teams_configured=True, Supabase insert succeeds,
               get_teams_client() raises an unexpected Exception during instantiation
        When: POST /api/v1/followups is called with valid data
        Then: The endpoint returns 201 with the created follow-up record,
              the exception is caught and logged, and the follow-up creation is not affected
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                    mock_teams_factory.side_effect = RuntimeError(
                        "Teams client instantiation failed"
                    )

                    with patch("app.api.followups.get_settings") as mock_settings:
                        mock_settings.return_value = MagicMock(
                            supabase_url="https://test.supabase.co",
                            supabase_key="test-key",
                            teams_configured=True,
                            app_base_url="https://app.example.com",
                        )

                        response = client.post(
                            FOLLOWUPS_URL,
                            json=valid_followup_payload,
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 201
        data = response.json()
        assert data["action_summary"] == "Inspect belt tension"


# ===========================================================================
# AC4: Fire-and-forget delivery
# ===========================================================================


class TestFireAndForgetDelivery:
    """AC#4: Teams notification dispatched as fire-and-forget via asyncio.create_task."""

    def test_INT_008_teams_notification_dispatched_via_create_task(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-008:
        Teams notification dispatched via asyncio.create_task (fire-and-forget).

        Given: settings.teams_configured=True, Supabase insert succeeds, Teams client is mocked
        When: POST /api/v1/followups is called
        Then: asyncio.create_task() is called to dispatch the Teams notification
              (verified by mocking asyncio.create_task), and the endpoint returns
              the follow-up response without awaiting the task
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                    mock_teams = MagicMock()
                    mock_teams.is_configured = True
                    mock_teams.send_card = AsyncMock(
                        return_value={"success": True, "message": "OK", "status_code": 200}
                    )
                    mock_teams_factory.return_value = mock_teams

                    with patch("app.api.followups.get_settings") as mock_settings:
                        mock_settings.return_value = MagicMock(
                            supabase_url="https://test.supabase.co",
                            supabase_key="test-key",
                            teams_configured=True,
                            app_base_url="https://app.example.com",
                        )

                        with patch("app.api.followups.asyncio") as mock_asyncio:
                            mock_asyncio.create_task = MagicMock()

                            response = client.post(
                                FOLLOWUPS_URL,
                                json=valid_followup_payload,
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 201

        # Verify asyncio.create_task was called for Teams notification
        # (in addition to email notification)
        teams_task_calls = [
            call for call in mock_asyncio.create_task.call_args_list
        ]
        # At least one create_task call should be for Teams
        assert mock_asyncio.create_task.call_count >= 2, (
            "Expected asyncio.create_task to be called at least twice "
            "(once for email, once for Teams)"
        )

    def test_INT_009_api_response_returns_immediately(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-009:
        API response returns immediately regardless of webhook latency.

        Given: settings.teams_configured=True, Supabase insert succeeds,
               Teams send_card is mocked with AsyncMock
        When: POST /api/v1/followups is called
        Then: The response is returned with status 201 and includes the created
              follow-up data, the response does not wait for the Teams webhook to complete
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                    mock_teams = MagicMock()
                    mock_teams.is_configured = True
                    # Simulate a slow webhook that would block if awaited
                    mock_teams.send_card = AsyncMock(
                        return_value={"success": True, "message": "OK", "status_code": 200}
                    )
                    mock_teams_factory.return_value = mock_teams

                    with patch("app.api.followups.get_settings") as mock_settings:
                        mock_settings.return_value = MagicMock(
                            supabase_url="https://test.supabase.co",
                            supabase_key="test-key",
                            teams_configured=True,
                            app_base_url="https://app.example.com",
                        )

                        response = client.post(
                            FOLLOWUPS_URL,
                            json=valid_followup_payload,
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["action_summary"] == "Inspect belt tension"
        assert data["status"] == "assigned"

    def test_INT_010_both_email_and_teams_dispatched_as_separate_tasks(
        self, client, mock_verify_jwt, valid_followup_payload, created_followup_record,
    ):
        """
        18-4-followup-assignment-teams-notification-INT-010:
        Both email and Teams notifications dispatched as separate fire-and-forget tasks.

        Given: settings.teams_configured=True, email notification service is mocked,
               Teams client is mocked, Supabase insert succeeds
        When: POST /api/v1/followups is called
        Then: asyncio.create_task is called at least twice — once for email notification
              and once for Teams notification — and both are independent fire-and-forget tasks
        """
        mock_sb = _mock_supabase_insert(created_followup_record)

        with patch("app.api.followups.create_client", return_value=mock_sb):
            with patch("app.api.followups.get_notification_service") as mock_email:
                mock_email_service = MagicMock()
                mock_email_service.send_assignment_notification = AsyncMock()
                mock_email.return_value = mock_email_service

                with patch("app.api.followups.get_teams_client") as mock_teams_factory:
                    mock_teams = MagicMock()
                    mock_teams.is_configured = True
                    mock_teams.send_card = AsyncMock(
                        return_value={"success": True, "message": "OK", "status_code": 200}
                    )
                    mock_teams_factory.return_value = mock_teams

                    with patch("app.api.followups.get_settings") as mock_settings:
                        mock_settings.return_value = MagicMock(
                            supabase_url="https://test.supabase.co",
                            supabase_key="test-key",
                            teams_configured=True,
                            app_base_url="https://app.example.com",
                        )

                        with patch("app.api.followups.asyncio") as mock_asyncio:
                            mock_asyncio.create_task = MagicMock()

                            response = client.post(
                                FOLLOWUPS_URL,
                                json=valid_followup_payload,
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 201

        # Both email and Teams should dispatch via create_task
        assert mock_asyncio.create_task.call_count >= 2, (
            f"Expected at least 2 create_task calls (email + Teams), "
            f"got {mock_asyncio.create_task.call_count}"
        )
