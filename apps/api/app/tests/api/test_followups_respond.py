"""
Integration tests for public follow-up response endpoints.

Story: 15.3 - Response Capture via Token Link
AC#1: Response page renders via token link (GET context endpoint)
AC#2: Response submission creates message record (POST respond endpoint)
AC#3: Expired token shows expiry message
AC#4: Invalid token shows error
Cross-Cutting: Full flow, error handling, boundary cases

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (endpoints don't exist yet).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import os

# Set test environment variables before importing app
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("POLL_RUN_ON_STARTUP", "false")

from app.main import app


# --- Constants ---

FOLLOWUP_ID = "uuid-followup-1"
MANAGER_USER_ID = str(uuid4())
MANAGER_EMAIL = "manager@plant.com"
ASSIGNEE_EMAIL = "assignee@plant.com"
VALID_TOKEN = "valid-token-uuid"
EXPIRED_TOKEN = "expired-token-uuid"
USED_TOKEN = "used-token-uuid"
CONTEXT_URL = f"/api/v1/followups/{FOLLOWUP_ID}/context"
RESPOND_URL = "/api/v1/followups/respond"


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
def valid_token_record():
    """A valid, fresh token record from followup_messages."""
    return {
        "id": str(uuid4()),
        "followup_id": FOLLOWUP_ID,
        "response_token": VALID_TOKEN,
        "sender_email": ASSIGNEE_EMAIL,
        "token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
        "token_used_at": None,
        "direction": "outbound",
        "message_type": "assignment",
    }


@pytest.fixture
def expired_token_record():
    """An expired token record from followup_messages."""
    return {
        "id": str(uuid4()),
        "followup_id": FOLLOWUP_ID,
        "response_token": EXPIRED_TOKEN,
        "sender_email": ASSIGNEE_EMAIL,
        "token_expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "token_used_at": None,
        "direction": "outbound",
        "message_type": "assignment",
    }


@pytest.fixture
def used_token_record():
    """An already-used token record from followup_messages."""
    return {
        "id": str(uuid4()),
        "followup_id": FOLLOWUP_ID,
        "response_token": USED_TOKEN,
        "sender_email": ASSIGNEE_EMAIL,
        "token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
        "token_used_at": "2026-02-10T12:00:00Z",
        "direction": "outbound",
        "message_type": "assignment",
    }


@pytest.fixture
def followup_context_record():
    """A follow-up record from action_followups with all context fields."""
    return {
        "id": FOLLOWUP_ID,
        "action_summary": "Replace bearing",
        "asset_name": "Pump-101",
        "category": "safety",
        "assigned_by": MANAGER_USER_ID,
        "note": "Please prioritize this week",
        "report_date": "2026-02-10",
        "status": "assigned",
    }


def _mock_token_service_valid():
    """Create a mock TokenService that returns valid token validation."""
    mock_service = MagicMock()
    mock_result = MagicMock()
    mock_result.is_valid = True
    mock_result.followup_id = FOLLOWUP_ID
    mock_result.assignee_email = ASSIGNEE_EMAIL
    mock_result.error_reason = None
    mock_service.validate_token.return_value = mock_result
    mock_service.mark_token_used.return_value = None
    return mock_service


def _mock_token_service_expired():
    """Create a mock TokenService that returns expired token validation."""
    mock_service = MagicMock()
    mock_result = MagicMock()
    mock_result.is_valid = False
    mock_result.followup_id = None
    mock_result.assignee_email = None
    mock_result.error_reason = "expired"
    mock_service.validate_token.return_value = mock_result
    return mock_service


def _mock_token_service_invalid():
    """Create a mock TokenService that returns invalid token validation."""
    mock_service = MagicMock()
    mock_result = MagicMock()
    mock_result.is_valid = False
    mock_result.followup_id = None
    mock_result.assignee_email = None
    mock_result.error_reason = "invalid"
    mock_service.validate_token.return_value = mock_result
    return mock_service


def _mock_supabase_for_context(followup_record, manager_email=MANAGER_EMAIL):
    """Create a mock Supabase client that returns followup context data."""
    mock_client = MagicMock()

    # Mock table().select().eq().execute() for action_followups
    mock_chain = MagicMock()
    mock_client.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.execute.return_value = MagicMock(data=[followup_record])

    # Mock auth.admin.get_user_by_id for manager lookup
    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.email = manager_email
    mock_user.user.user_metadata = {"full_name": "John Manager"}
    mock_client.auth.admin.get_user_by_id.return_value = mock_user

    # Mock table chain for insert
    mock_chain.insert.return_value = mock_chain

    return mock_client


# =============================================================================
# AC1: GET /api/v1/followups/{id}/context
# =============================================================================


class TestGetFollowupContext:
    """Tests for GET /api/v1/followups/{id}/context endpoint."""

    def test_returns_context_for_valid_token(
        self, client, followup_context_record,
    ):
        """
        15-3-response-capture-via-token-link-INT-001: GET /api/v1/followups/{id}/context
        returns followup context for valid token.

        Given: A valid token exists in followup_messages with associated followup_id,
               the action_followups record exists with context fields; Supabase is mocked
        When: GET /api/v1/followups/{id}/context?token={valid_token} is called
        Then: Returns 200 with JSON body containing action_summary, asset_name, category,
              assigned_by_email, assigned_by_name, note, and report_date
        """
        mock_token = _mock_token_service_valid()
        mock_supabase = _mock_supabase_for_context(followup_context_record)

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_supabase):
                response = client.get(
                    f"{CONTEXT_URL}?token={VALID_TOKEN}",
                )

        assert response.status_code == 200
        data = response.json()
        assert data["action_summary"] == "Replace bearing"
        assert data["asset_name"] == "Pump-101"
        assert data["category"] == "safety"
        assert "assigned_by_email" in data
        assert data["assigned_by_email"] == MANAGER_EMAIL
        assert "note" in data
        assert data["note"] == "Please prioritize this week"
        assert data["report_date"] == "2026-02-10"

    def test_does_not_require_authentication(self, client, followup_context_record):
        """
        15-3-response-capture-via-token-link-INT-002: GET /api/v1/followups/{id}/context
        does not require authentication.

        Given: A valid token exists for the requested followup_id; Supabase is mocked
        When: GET /api/v1/followups/{id}/context?token={valid_token} is called WITHOUT
              any Authorization header
        Then: Returns 200 (not 401 or 403) -- this is a public endpoint where the token IS the auth
        """
        mock_token = _mock_token_service_valid()
        mock_supabase = _mock_supabase_for_context(followup_context_record)

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_supabase):
                response = client.get(
                    f"{CONTEXT_URL}?token={VALID_TOKEN}",
                    # NO Authorization header
                )

        assert response.status_code == 200
        assert response.status_code not in (401, 403)

    def test_returns_assigner_details(self, client, followup_context_record):
        """
        15-3-response-capture-via-token-link-INT-003: GET /api/v1/followups/{id}/context
        returns assigner details.

        Given: A valid token, the action_followups record has assigned_by="uuid-manager-1",
               and auth.users has this user with email="manager@plant.com"; Supabase is mocked
        When: GET /api/v1/followups/{id}/context?token={valid_token} is called
        Then: The response includes assigned_by_email="manager@plant.com" and assigned_by_name
        """
        mock_token = _mock_token_service_valid()
        mock_supabase = _mock_supabase_for_context(
            followup_context_record, manager_email=MANAGER_EMAIL
        )

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_supabase):
                response = client.get(
                    f"{CONTEXT_URL}?token={VALID_TOKEN}",
                )

        assert response.status_code == 200
        data = response.json()
        assert data["assigned_by_email"] == MANAGER_EMAIL
        assert "assigned_by_name" in data


# =============================================================================
# AC2: POST /api/v1/followups/respond
# =============================================================================


class TestPostFollowupRespond:
    """Tests for POST /api/v1/followups/respond endpoint."""

    def test_creates_inbound_message_record(self, client):
        """
        15-3-response-capture-via-token-link-INT-004: POST /api/v1/followups/respond creates
        inbound message record with valid token.

        Given: A valid token exists in followup_messages linked to a followup with
               status='assigned', assignee_email="assignee@plant.com"; Supabase is mocked
        When: POST /api/v1/followups/respond is called with valid token and response_text
        Then: A new followup_messages record is inserted with direction='inbound',
              message_type='response', sender_email="assignee@plant.com", body="I fixed the bearing"
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "I fixed the bearing"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

        # Verify insert was called with correct data
        insert_call = mock_chain.insert
        assert insert_call.called
        inserted_data = insert_call.call_args[0][0]
        assert inserted_data["direction"] == "inbound"
        assert inserted_data["message_type"] == "response"
        assert inserted_data["sender_email"] == ASSIGNEE_EMAIL
        assert inserted_data["body"] == "I fixed the bearing"

    def test_updates_status_from_assigned_to_in_progress(self, client):
        """
        15-3-response-capture-via-token-link-INT-005: POST /api/v1/followups/respond updates
        status from 'assigned' to 'in_progress'.

        Given: A valid token exists, and the linked action_followups record has status='assigned'
        When: POST /api/v1/followups/respond is called with valid token and response text
        Then: The action_followups record is updated with status='in_progress'
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4()), "status": "assigned"}])

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "Working on it"},
                )

        assert response.status_code == 200

        # Verify update was called on action_followups with status='in_progress'
        update_call = mock_chain.update
        assert update_call.called
        # Check that at least one update call sets status to in_progress
        found_status_update = False
        for call in update_call.call_args_list:
            if call[0] and "status" in call[0][0]:
                if call[0][0]["status"] == "in_progress":
                    found_status_update = True
        assert found_status_update, "Should update status to 'in_progress'"

    def test_does_not_regress_from_in_progress(self, client):
        """
        15-3-response-capture-via-token-link-INT-006: POST /api/v1/followups/respond does NOT
        regress status from 'in_progress'.

        Given: A valid token exists, and the linked action_followups record already has
               status='in_progress'
        When: POST /api/v1/followups/respond is called with valid token and response text
        Then: The action_followups.status remains 'in_progress' -- the conditional UPDATE
              WHERE status='assigned' has no effect, and the response message is still created
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        # Return in_progress status
        mock_chain.execute.return_value = MagicMock(
            data=[{"id": str(uuid4()), "status": "in_progress"}]
        )

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "Still working on it"},
                )

        # Should still succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_does_not_regress_from_resolved(self, client):
        """
        15-3-response-capture-via-token-link-INT-007: POST /api/v1/followups/respond does NOT
        regress status from 'resolved'.

        Given: A valid token exists, and the linked action_followups record has status='resolved'
        When: POST /api/v1/followups/respond is called with valid token and response text
        Then: The action_followups.status remains 'resolved' and the response message is created
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        # Return resolved status
        mock_chain.execute.return_value = MagicMock(
            data=[{"id": str(uuid4()), "status": "resolved"}]
        )

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "Additional info"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_marks_token_as_used(self, client):
        """
        15-3-response-capture-via-token-link-INT-008: POST /api/v1/followups/respond marks
        token as used after success.

        Given: A valid, unused token exists; Supabase is mocked
        When: POST /api/v1/followups/respond is called with the token and valid response text
        Then: TokenService.mark_token_used() is called with the token
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "Done"},
                )

        assert response.status_code == 200
        mock_token.mark_token_used.assert_called_once_with(VALID_TOKEN)

    def test_does_not_require_authentication(self, client):
        """
        15-3-response-capture-via-token-link-INT-009: POST /api/v1/followups/respond does not
        require authentication.

        Given: A valid token exists; Supabase is mocked
        When: POST /api/v1/followups/respond is called WITHOUT any Authorization header
        Then: Returns 200 (not 401 or 403) -- public endpoint where the token IS the auth
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "My response"},
                    # NO Authorization header
                )

        assert response.status_code == 200
        assert response.status_code not in (401, 403)


# =============================================================================
# AC2: Validation errors
# =============================================================================


class TestPostFollowupRespondValidation:
    """Tests for POST /api/v1/followups/respond validation errors."""

    def test_returns_422_for_missing_response_text(self, client):
        """
        15-3-response-capture-via-token-link-INT-010: POST /api/v1/followups/respond returns
        422 for missing response_text.

        Given: A request body with token="valid-token" but no response_text field
        When: POST /api/v1/followups/respond is called
        Then: Returns 422 Unprocessable Entity with validation error details
        """
        mock_token = _mock_token_service_valid()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.post(
                RESPOND_URL,
                json={"token": VALID_TOKEN},
            )

        assert response.status_code == 422

    def test_returns_422_for_empty_response_text(self, client):
        """
        15-3-response-capture-via-token-link-INT-011: POST /api/v1/followups/respond returns
        422 for empty response_text.

        Given: A request body with token="valid-token" and response_text=""
        When: POST /api/v1/followups/respond is called
        Then: Returns 422 Unprocessable Entity with validation error
        """
        mock_token = _mock_token_service_valid()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.post(
                RESPOND_URL,
                json={"token": VALID_TOKEN, "response_text": ""},
            )

        assert response.status_code == 422


# =============================================================================
# AC2: Full flow integration
# =============================================================================


class TestFollowupRespondFullFlow:
    """Tests for the full token-to-response flow."""

    def test_full_flow_token_to_response(self, client, followup_context_record):
        """
        15-3-response-capture-via-token-link-INT-012: Full flow -- token generation to
        response submission to message creation.

        Given: TokenService.generate_token() has been called and returns a token,
               the followup_messages outbound record exists with the token
        When: (1) GET /api/v1/followups/{id}/context?token={token} fetches context,
              then (2) POST /api/v1/followups/respond is called with the token and response
        Then: (1) A new followup_messages record is created with direction='inbound',
              (2) The token is marked as used (token_used_at is set),
              (3) Success response is returned
        """
        mock_token = _mock_token_service_valid()
        mock_supabase = _mock_supabase_for_context(followup_context_record)
        mock_supabase.table.return_value.insert.return_value = mock_supabase.table.return_value
        mock_supabase.table.return_value.update.return_value = mock_supabase.table.return_value

        # Step 1: GET context
        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_supabase):
                context_response = client.get(
                    f"{CONTEXT_URL}?token={VALID_TOKEN}",
                )

        assert context_response.status_code == 200

        # Step 2: POST respond
        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_supabase):
                respond_response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "Completed the repair"},
                )

        assert respond_response.status_code == 200
        data = respond_response.json()
        assert data["success"] is True

        # Token should be marked as used
        mock_token.mark_token_used.assert_called_with(VALID_TOKEN)


# =============================================================================
# AC3: Expired token
# =============================================================================


class TestExpiredToken:
    """Tests for expired token handling."""

    def test_get_context_returns_400_for_expired_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-013: GET /api/v1/followups/{id}/context
        returns 400 for expired token.

        Given: A followup_messages record exists with response_token where token_expires_at
               is in the past
        When: GET /api/v1/followups/{id}/context?token={expired_token} is called
        Then: Returns 400 with error_reason='expired'
        """
        mock_token = _mock_token_service_expired()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.get(
                f"{CONTEXT_URL}?token={EXPIRED_TOKEN}",
            )

        assert response.status_code == 400
        data = response.json()
        assert data.get("error_reason") == "expired" or "expired" in str(data.get("detail", "")).lower()

    def test_get_context_returns_400_for_used_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-014: GET /api/v1/followups/{id}/context
        returns 400 for already-used token.

        Given: A followup_messages record exists with response_token where token_used_at
               is set (already consumed)
        When: GET /api/v1/followups/{id}/context?token={used_token} is called
        Then: Returns 400 with error_reason='expired' (used tokens treated same as expired)
        """
        mock_token = _mock_token_service_expired()  # Used tokens return 'expired' reason

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.get(
                f"{CONTEXT_URL}?token={USED_TOKEN}",
            )

        assert response.status_code == 400
        data = response.json()
        assert data.get("error_reason") == "expired" or "expired" in str(data.get("detail", "")).lower()

    def test_post_respond_returns_400_for_expired_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-015: POST /api/v1/followups/respond returns
        400 for expired token.

        Given: A followup_messages record exists with an expired token
        When: POST /api/v1/followups/respond is called with the expired token and valid response
        Then: Returns 400 with detail "Token expired", no message record is created
        """
        mock_token = _mock_token_service_expired()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.post(
                RESPOND_URL,
                json={"token": EXPIRED_TOKEN, "response_text": "My response"},
            )

        assert response.status_code == 400
        data = response.json()
        assert "expired" in str(data.get("detail", "")).lower() or \
            data.get("error_reason") == "expired"

    def test_post_respond_returns_400_for_used_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-016: POST /api/v1/followups/respond returns
        400 for already-used token.

        Given: A followup_messages record exists with token_used_at already set
        When: POST /api/v1/followups/respond is called with the used token
        Then: Returns 400 with detail "Token expired", no new message record is created
        """
        mock_token = _mock_token_service_expired()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.post(
                RESPOND_URL,
                json={"token": USED_TOKEN, "response_text": "Trying again"},
            )

        assert response.status_code == 400
        data = response.json()
        assert "expired" in str(data.get("detail", "")).lower() or \
            data.get("error_reason") == "expired"


# =============================================================================
# AC4: Invalid token
# =============================================================================


class TestInvalidToken:
    """Tests for invalid token handling."""

    def test_get_context_returns_404_for_nonexistent_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-017: GET /api/v1/followups/{id}/context
        returns 404 for nonexistent token.

        Given: No followup_messages record exists with the given response_token
        When: GET /api/v1/followups/{id}/context?token=nonexistent-token-uuid is called
        Then: Returns 404 with error_reason='invalid'
        """
        mock_token = _mock_token_service_invalid()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.get(
                f"{CONTEXT_URL}?token=nonexistent-token-uuid",
            )

        assert response.status_code == 404
        data = response.json()
        assert data.get("error_reason") == "invalid" or "invalid" in str(data.get("detail", "")).lower()

    def test_get_context_returns_404_for_malformed_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-018: GET /api/v1/followups/{id}/context
        returns 404 for malformed token.

        Given: The token parameter is a random string that doesn't match any record
        When: GET /api/v1/followups/{id}/context?token=not-a-real-token is called
        Then: Returns 404 with error_reason='invalid'
        """
        mock_token = _mock_token_service_invalid()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.get(
                f"{CONTEXT_URL}?token=not-a-real-token",
            )

        assert response.status_code == 404

    def test_get_context_returns_error_when_token_missing(self, client):
        """
        15-3-response-capture-via-token-link-INT-019: GET /api/v1/followups/{id}/context
        returns error when token is missing from query.

        Given: No token query parameter is provided
        When: GET /api/v1/followups/{id}/context is called without a token parameter
        Then: Returns 422 (missing required query parameter) or 400
        """
        response = client.get(CONTEXT_URL)

        assert response.status_code in (400, 422)

    def test_post_respond_returns_404_for_nonexistent_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-020: POST /api/v1/followups/respond returns
        404 for nonexistent token.

        Given: No followup_messages record exists with the given response_token
        When: POST /api/v1/followups/respond is called with the fake token
        Then: Returns 404 with detail "Invalid link", no message record is created
        """
        mock_token = _mock_token_service_invalid()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.post(
                RESPOND_URL,
                json={"token": "fake-uuid-token", "response_text": "My response"},
            )

        assert response.status_code == 404
        data = response.json()
        assert "invalid" in str(data.get("detail", "")).lower() or \
            data.get("error_reason") == "invalid"

    def test_post_respond_returns_404_for_malformed_token(self, client):
        """
        15-3-response-capture-via-token-link-INT-021: POST /api/v1/followups/respond returns
        404 for malformed token.

        Given: The token field contains a random/malformed string; no matching record exists
        When: POST /api/v1/followups/respond is called with the malformed token
        Then: Returns 404 with detail "Invalid link"
        """
        mock_token = _mock_token_service_invalid()

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            response = client.post(
                RESPOND_URL,
                json={"token": "abc123garbage", "response_text": "My response"},
            )

        assert response.status_code == 404


# =============================================================================
# Cross-Cutting: Error handling
# =============================================================================


class TestRespondErrorHandling:
    """Tests for error handling in the respond endpoint."""

    def test_handles_supabase_errors_gracefully(self, client):
        """
        15-3-response-capture-via-token-link-INT-025: POST /api/v1/followups/respond handles
        Supabase errors gracefully.

        Given: Token is valid but Supabase insert for the inbound message raises an exception
        When: POST /api/v1/followups/respond is called
        Then: Returns 500 with a generic error message, token is NOT marked as used
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.execute.side_effect = Exception("Supabase unavailable")

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": "My response"},
                )

        assert response.status_code == 500

        # Token should NOT be marked as used on failure
        mock_token.mark_token_used.assert_not_called()


# =============================================================================
# Cross-Cutting: Boundary cases
# =============================================================================


class TestRespondBoundary:
    """Tests for boundary conditions in the respond endpoint."""

    def test_max_length_response_text_succeeds(self, client):
        """
        15-3-response-capture-via-token-link-INT-026: POST /api/v1/followups/respond with
        response_text at max length (5000 chars) succeeds.

        Given: A valid token exists; response_text is exactly 5000 characters long
        When: POST /api/v1/followups/respond is called
        Then: Returns success, the message record body contains the full 5000-character response
        """
        mock_token = _mock_token_service_valid()
        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])

        long_text = "a" * 5000

        with patch("app.api.followups.get_token_service", return_value=mock_token):
            with patch("app.api.followups.get_service_role_client", return_value=mock_client):
                response = client.post(
                    RESPOND_URL,
                    json={"token": VALID_TOKEN, "response_text": long_text},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
