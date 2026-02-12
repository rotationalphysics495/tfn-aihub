"""
Integration tests for follow-up messages API endpoints.

Story: 15.4 - Message Thread UI
AC#1: Chronological message thread display
AC#2: Unread indicator on follow-up entry
AC#3: Empty state when no responses
AC#4: Messages API returns chronological messages with correct fields
AC#5: RLS enforcement for unauthorized access

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (endpoints don't exist yet).
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

FOLLOWUP_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
MANAGER_USER_ID = "123e4567-e89b-12d3-a456-426614174000"
MANAGER_EMAIL = "manager@plant.com"
ASSIGNEE_USER_ID = str(uuid4())
ASSIGNEE_EMAIL = "assignee@plant.com"
TECHNICIAN_USER_ID = str(uuid4())
OUTSIDER_USER_ID = str(uuid4())

MESSAGES_URL = f"/api/v1/followups/{FOLLOWUP_ID}/messages"
VIEWED_URL = f"/api/v1/followups/{FOLLOWUP_ID}/viewed"


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
    with patch(
        "app.core.security.verify_supabase_jwt", new_callable=AsyncMock
    ) as mock:
        mock.return_value = valid_jwt_payload
        yield mock


@pytest.fixture
def followup_record():
    """A follow-up record from action_followups."""
    return {
        "id": FOLLOWUP_ID,
        "action_item_id": "AI-001",
        "action_summary": "Replace bearing",
        "asset_name": "Pump-101",
        "category": "safety",
        "assigned_to": TECHNICIAN_USER_ID,
        "assigned_to_email": ASSIGNEE_EMAIL,
        "assigned_by": MANAGER_USER_ID,
        "note": "Priority this week",
        "status": "in_progress",
        "report_date": "2026-02-10",
        "created_at": "2026-02-10T08:00:00+00:00",
        "updated_at": "2026-02-10T14:30:00+00:00",
        "last_viewed_at": "2026-02-10T12:00:00+00:00",
    }


@pytest.fixture
def followup_record_null_viewed():
    """A follow-up record with last_viewed_at=None."""
    return {
        "id": FOLLOWUP_ID,
        "action_item_id": "AI-001",
        "action_summary": "Replace bearing",
        "asset_name": "Pump-101",
        "category": "safety",
        "assigned_to": TECHNICIAN_USER_ID,
        "assigned_to_email": ASSIGNEE_EMAIL,
        "assigned_by": MANAGER_USER_ID,
        "note": "Priority this week",
        "status": "assigned",
        "report_date": "2026-02-10",
        "created_at": "2026-02-10T08:00:00+00:00",
        "updated_at": "2026-02-10T08:00:00+00:00",
        "last_viewed_at": None,
    }


@pytest.fixture
def sample_messages():
    """Sample followup_messages records sorted by sent_at."""
    return [
        {
            "id": str(uuid4()),
            "followup_id": FOLLOWUP_ID,
            "direction": "outbound",
            "message_type": "assignment",
            "sender_email": MANAGER_EMAIL,
            "subject": "Follow-up: Replace bearing",
            "body": "Please inspect the bearing on Pump-101",
            "sent_at": "2026-02-10T08:00:00+00:00",
        },
        {
            "id": str(uuid4()),
            "followup_id": FOLLOWUP_ID,
            "direction": "outbound",
            "message_type": "status_update",
            "sender_email": ASSIGNEE_EMAIL,
            "subject": None,
            "body": "in_progress",
            "sent_at": "2026-02-10T10:00:00+00:00",
        },
        {
            "id": str(uuid4()),
            "followup_id": FOLLOWUP_ID,
            "direction": "inbound",
            "message_type": "response",
            "sender_email": ASSIGNEE_EMAIL,
            "subject": None,
            "body": "Bearing replaced and tested",
            "sent_at": "2026-02-10T14:30:00+00:00",
        },
    ]


def _mock_supabase_for_messages(followup_record, messages, user_id=MANAGER_USER_ID):
    """Create a mock Supabase client for messages endpoint.

    Mocks:
    - table('action_followups').select().eq().execute() → followup_record
    - table('followup_messages').select().eq().order().execute() → messages
    """
    mock_client = MagicMock()

    # We need to handle multiple table() calls returning different chains
    followup_chain = MagicMock()
    followup_chain.select.return_value = followup_chain
    followup_chain.eq.return_value = followup_chain

    if followup_record:
        followup_chain.execute.return_value = MagicMock(data=[followup_record])
    else:
        followup_chain.execute.return_value = MagicMock(data=[])

    messages_chain = MagicMock()
    messages_chain.select.return_value = messages_chain
    messages_chain.eq.return_value = messages_chain
    messages_chain.order.return_value = messages_chain
    messages_chain.execute.return_value = MagicMock(data=messages)

    def table_side_effect(table_name):
        if table_name == "action_followups":
            return followup_chain
        elif table_name == "followup_messages":
            return messages_chain
        return MagicMock()

    mock_client.table.side_effect = table_side_effect
    return mock_client


def _mock_supabase_for_viewed(followup_record):
    """Create a mock Supabase client for viewed endpoint."""
    mock_client = MagicMock()
    mock_chain = MagicMock()
    mock_client.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.update.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain

    if followup_record:
        mock_chain.execute.return_value = MagicMock(data=[followup_record])
    else:
        mock_chain.execute.return_value = MagicMock(data=[])

    return mock_client


# =============================================================================
# AC2: Unread indicator — PATCH /viewed
# =============================================================================


class TestPatchFollowUpViewed:
    """Tests for PATCH /api/v1/followups/{id}/viewed endpoint."""

    def test_updates_last_viewed_at(
        self, client, mock_verify_jwt, followup_record,
    ):
        """
        15-4-message-thread-ui-INT-004: PATCH /api/v1/followups/{id}/viewed updates
        last_viewed_at server-side.

        Given: An authenticated manager user, a follow-up "fu-123" assigned to or by
               the user, last_viewed_at is null
        When: PATCH /api/v1/followups/fu-123/viewed is called with valid Bearer token
        Then: Response 200 with { "success": true, "last_viewed_at": "<current ISO datetime>" },
              and the action_followups row is updated with last_viewed_at = NOW()
        """
        updated_record = {
            **followup_record,
            "last_viewed_at": "2026-02-11T12:00:00+00:00",
        }
        mock_client = _mock_supabase_for_viewed(updated_record)

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.patch(
                VIEWED_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "last_viewed_at" in data
        assert data["last_viewed_at"] is not None

    def test_returns_401_without_auth(self, client):
        """
        15-4-message-thread-ui-INT-015: PATCH /viewed requires authentication.

        Given: No Authorization header is provided
        When: PATCH /api/v1/followups/fu-123/viewed is called
        Then: Response is 401 Unauthorized
        """
        response = client.patch(VIEWED_URL)

        assert response.status_code in (401, 403)


# =============================================================================
# AC2: GET /api/v1/actions/followups returns has_unread per follow-up
# =============================================================================


class TestFollowUpsListHasUnread:
    """Tests for has_unread field in followups list endpoint."""

    def test_returns_has_unread_per_followup(
        self, client, mock_verify_jwt,
    ):
        """
        15-4-message-thread-ui-INT-005: GET /api/v1/actions/followups returns
        has_unread per follow-up item.

        Given: An authenticated user with two follow-ups: one with inbound messages
               newer than last_viewed_at, one with no inbound messages
        When: GET /api/v1/actions/followups is called
        Then: The response includes has_unread=true for the first follow-up
              and has_unread=false for the second
        """
        followups_with_unread = [
            {
                "id": "fu-unread",
                "action_item_id": "AI-001",
                "action_summary": "Replace bearing",
                "asset_name": "Pump-101",
                "category": "safety",
                "assigned_to": TECHNICIAN_USER_ID,
                "assigned_to_email": ASSIGNEE_EMAIL,
                "assigned_by": MANAGER_USER_ID,
                "status": "in_progress",
                "report_date": "2026-02-10",
                "created_at": "2026-02-10T08:00:00+00:00",
                "updated_at": "2026-02-10T14:30:00+00:00",
                "has_unread": True,
            },
            {
                "id": "fu-read",
                "action_item_id": "AI-002",
                "action_summary": "Check valve",
                "asset_name": "Valve-201",
                "category": "maintenance",
                "assigned_to": TECHNICIAN_USER_ID,
                "assigned_to_email": ASSIGNEE_EMAIL,
                "assigned_by": MANAGER_USER_ID,
                "status": "assigned",
                "report_date": "2026-02-10",
                "created_at": "2026-02-10T08:00:00+00:00",
                "updated_at": "2026-02-10T08:00:00+00:00",
                "has_unread": False,
            },
        ]

        mock_client = MagicMock()
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.order.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=followups_with_unread)

        with patch("app.api.actions.create_client", return_value=mock_client):
            response = client.get(
                "/api/v1/actions/followups?assigned_by=me&status=all",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        followups = data.get("followups", data.get("items", []))
        assert len(followups) >= 2

        unread_fu = next((f for f in followups if f["id"] == "fu-unread"), None)
        read_fu = next((f for f in followups if f["id"] == "fu-read"), None)

        assert unread_fu is not None
        assert unread_fu.get("has_unread") is True

        assert read_fu is not None
        assert read_fu.get("has_unread") is False


# =============================================================================
# AC3: Empty state — GET /messages for follow-up with assignee_name
# =============================================================================


class TestGetMessagesEmptyState:
    """Tests for GET /messages when follow-up has no responses."""

    def test_returns_assignee_name_for_empty_state(
        self, client, mock_verify_jwt, followup_record,
    ):
        """
        15-4-message-thread-ui-INT-007: GET /api/v1/followups/{id}/messages returns
        assignee_name in response for empty state label.

        Given: An authenticated user, follow-up "fu-xyz" exists with
               assignee_name="Jane Doe" and only one outbound message
        When: GET /api/v1/followups/fu-xyz/messages is called
        Then: Response includes assignee_name="Jane Doe" in the wrapper
              and the messages array contains only the outbound message
        """
        fu_record_with_name = {
            **followup_record,
            "assignee_name": "Jane Doe",
        }
        outbound_only = [
            {
                "id": str(uuid4()),
                "followup_id": FOLLOWUP_ID,
                "direction": "outbound",
                "message_type": "assignment",
                "sender_email": MANAGER_EMAIL,
                "subject": "Follow-up: Replace bearing",
                "body": "Please inspect the bearing",
                "sent_at": "2026-02-10T08:00:00+00:00",
            },
        ]

        mock_client = _mock_supabase_for_messages(fu_record_with_name, outbound_only)

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "assignee_name" in data
        assert data["messages"] is not None
        assert len(data["messages"]) == 1
        assert data["messages"][0]["direction"] == "outbound"


# =============================================================================
# AC4: Messages API returns chronological messages with correct fields
# =============================================================================


class TestGetFollowUpMessages:
    """Tests for GET /api/v1/followups/{id}/messages endpoint."""

    def test_returns_messages_in_chronological_order(
        self, client, mock_verify_jwt, followup_record, sample_messages,
    ):
        """
        15-4-message-thread-ui-INT-008: GET /messages returns messages in
        chronological order (sent_at ascending).

        Given: An authenticated manager user, follow-up "fu-123" has 3 messages
               at sent_at 08:00, 10:00, 14:30
        When: GET /api/v1/followups/fu-123/messages is called with valid auth
        Then: Response 200 with messages array sorted by sent_at ascending,
              message at index 0 has the earliest timestamp,
              message at index 2 has the latest
        """
        mock_client = _mock_supabase_for_messages(followup_record, sample_messages)

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        messages = data["messages"]
        assert len(messages) == 3

        # Verify chronological order
        assert messages[0]["sent_at"] <= messages[1]["sent_at"]
        assert messages[1]["sent_at"] <= messages[2]["sent_at"]

    def test_returns_all_required_fields_per_message(
        self, client, mock_verify_jwt, followup_record, sample_messages,
    ):
        """
        15-4-message-thread-ui-INT-009: GET /messages returns all required fields
        per message.

        Given: An authenticated user, follow-up "fu-123" has messages
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Each message contains: id, direction, message_type, sender_email,
              subject, body, sent_at
        """
        mock_client = _mock_supabase_for_messages(followup_record, sample_messages)

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        messages = data["messages"]
        assert len(messages) > 0

        required_fields = ["id", "direction", "message_type", "sender_email",
                           "subject", "body", "sent_at"]
        for msg in messages:
            for field in required_fields:
                assert field in msg, f"Message missing required field: {field}"

        # Verify direction enum values
        valid_directions = {"outbound", "inbound"}
        for msg in messages:
            assert msg["direction"] in valid_directions

        # Verify message_type enum values
        valid_types = {"assignment", "response", "escalation", "status_update"}
        for msg in messages:
            assert msg["message_type"] in valid_types

    def test_returns_followup_context_in_wrapper(
        self, client, mock_verify_jwt, followup_record, sample_messages,
    ):
        """
        15-4-message-thread-ui-INT-010: GET /messages returns follow-up context
        in wrapper.

        Given: An authenticated user, follow-up "fu-123" exists with
               action_summary, assignee_name, assignee_email, status
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response includes wrapper fields: followup_id, action_summary,
              assignee_name, assignee_email, status, has_unread, last_viewed_at
        """
        mock_client = _mock_supabase_for_messages(followup_record, sample_messages)

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify wrapper fields
        assert "followup_id" in data or "id" in data
        assert "action_summary" in data
        assert "status" in data
        assert "has_unread" in data
        assert "last_viewed_at" in data

    def test_computes_has_unread_correctly(
        self, client, mock_verify_jwt, followup_record, sample_messages,
    ):
        """
        15-4-message-thread-ui-INT-011: GET /messages computes has_unread correctly
        (inbound newer than last_viewed_at).

        Given: An authenticated user, follow-up "fu-123" has
               last_viewed_at="2026-02-10T12:00:00Z" and an inbound message
               with sent_at="2026-02-10T14:30:00Z"
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response has has_unread=true because inbound sent_at > last_viewed_at
        """
        mock_client = _mock_supabase_for_messages(followup_record, sample_messages)

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        # The inbound message at 14:30 is after last_viewed_at at 12:00
        assert data["has_unread"] is True

    def test_has_unread_false_when_no_inbound_messages(
        self, client, mock_verify_jwt, followup_record,
    ):
        """
        15-4-message-thread-ui-INT-012: GET /messages returns has_unread=false
        when no inbound messages exist.

        Given: An authenticated user, follow-up "fu-123" has only outbound messages
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response has has_unread=false
        """
        outbound_only = [
            {
                "id": str(uuid4()),
                "followup_id": FOLLOWUP_ID,
                "direction": "outbound",
                "message_type": "assignment",
                "sender_email": MANAGER_EMAIL,
                "subject": "Follow-up: Replace bearing",
                "body": "Please inspect the bearing",
                "sent_at": "2026-02-10T08:00:00+00:00",
            },
        ]
        mock_client = _mock_supabase_for_messages(followup_record, outbound_only)

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["has_unread"] is False

    def test_has_unread_true_when_last_viewed_at_null(
        self, client, mock_verify_jwt, followup_record_null_viewed,
    ):
        """
        15-4-message-thread-ui-INT-013: GET /messages returns has_unread=true
        when last_viewed_at is null and inbound exists.

        Given: An authenticated user, follow-up "fu-123" has last_viewed_at=null
               and an inbound message exists
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response has has_unread=true (null treated as epoch via COALESCE)
        """
        messages_with_inbound = [
            {
                "id": str(uuid4()),
                "followup_id": FOLLOWUP_ID,
                "direction": "outbound",
                "message_type": "assignment",
                "sender_email": MANAGER_EMAIL,
                "subject": "Follow-up",
                "body": "Please inspect",
                "sent_at": "2026-02-10T08:00:00+00:00",
            },
            {
                "id": str(uuid4()),
                "followup_id": FOLLOWUP_ID,
                "direction": "inbound",
                "message_type": "response",
                "sender_email": ASSIGNEE_EMAIL,
                "subject": None,
                "body": "Done",
                "sent_at": "2026-02-10T14:30:00+00:00",
            },
        ]
        mock_client = _mock_supabase_for_messages(
            followup_record_null_viewed, messages_with_inbound
        )

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["has_unread"] is True

    def test_requires_authentication(self, client):
        """
        15-4-message-thread-ui-INT-014: GET /messages requires authentication.

        Given: No Authorization header is provided
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response is 401 Unauthorized
        """
        response = client.get(MESSAGES_URL)

        assert response.status_code in (401, 403)

    def test_returns_404_for_nonexistent_followup(
        self, client, mock_verify_jwt,
    ):
        """
        15-4-message-thread-ui-INT-016: GET /messages returns 404 for
        non-existent follow-up ID.

        Given: An authenticated user, no follow-up with id="00000000-0000-0000-0000-000000000000"
        When: GET /api/v1/followups/00000000-0000-0000-0000-000000000000/messages is called
        Then: Response is 404 Not Found
        """
        mock_client = _mock_supabase_for_messages(None, [])

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                "/api/v1/followups/00000000-0000-0000-0000-000000000000/messages",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 404

    def test_returns_empty_messages_for_followup_with_no_messages(
        self, client, mock_verify_jwt, followup_record,
    ):
        """
        15-4-message-thread-ui-INT-017: GET /messages returns empty messages array
        for follow-up with no messages.

        Given: An authenticated user, follow-up "fu-123" exists but
               followup_messages table has no records for this ID
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response 200 with messages=[] (empty array), wrapper still includes
              followup context (assignee_name, status, etc.)
        """
        mock_client = _mock_supabase_for_messages(followup_record, [])

        with patch("app.api.followups.create_client", return_value=mock_client):
            response = client.get(
                MESSAGES_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []
        # Wrapper should still contain context
        assert "action_summary" in data or "status" in data


# =============================================================================
# AC5: RLS enforcement for unauthorized access
# =============================================================================


class TestFollowUpMessagesRLS:
    """Tests for RLS enforcement on messages endpoint."""

    def test_returns_404_when_user_is_neither_assigner_nor_assignee(
        self, client,
    ):
        """
        15-4-message-thread-ui-INT-018: GET /messages returns 404 when user is
        neither assigner nor assignee.

        Given: An authenticated user with id="user-outsider", follow-up "fu-123"
               has assigned_by="user-manager" and assigned_to="user-technician"
        When: GET /api/v1/followups/fu-123/messages is called with outsider's token
        Then: Response is 404 (application-level defense-in-depth)
        """
        outsider_jwt = {
            "sub": OUTSIDER_USER_ID,
            "email": "outsider@plant.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }

        followup = {
            "id": FOLLOWUP_ID,
            "action_summary": "Replace bearing",
            "asset_name": "Pump-101",
            "category": "safety",
            "assigned_to": TECHNICIAN_USER_ID,
            "assigned_by": MANAGER_USER_ID,
            "status": "in_progress",
            "last_viewed_at": None,
        }

        mock_client = _mock_supabase_for_messages(followup, [])

        with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock_jwt:
            mock_jwt.return_value = outsider_jwt
            with patch("app.api.followups.create_client", return_value=mock_client):
                response = client.get(
                    MESSAGES_URL,
                    headers={"Authorization": "Bearer outsider-token"},
                )

        assert response.status_code == 404

    def test_succeeds_when_user_is_assigner(
        self, client, followup_record, sample_messages,
    ):
        """
        15-4-message-thread-ui-INT-019: GET /messages succeeds when user is
        the assigner.

        Given: An authenticated user with id="user-manager", follow-up "fu-123"
               has assigned_by="user-manager"
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response is 200 with the messages array
        """
        manager_jwt = {
            "sub": MANAGER_USER_ID,
            "email": MANAGER_EMAIL,
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }

        mock_client = _mock_supabase_for_messages(followup_record, sample_messages)

        with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock_jwt:
            mock_jwt.return_value = manager_jwt
            with patch("app.api.followups.create_client", return_value=mock_client):
                response = client.get(
                    MESSAGES_URL,
                    headers={"Authorization": "Bearer manager-token"},
                )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 3

    def test_succeeds_when_user_is_assignee(
        self, client, followup_record, sample_messages,
    ):
        """
        15-4-message-thread-ui-INT-020: GET /messages succeeds when user is
        the assignee.

        Given: An authenticated user with id="user-technician", follow-up "fu-123"
               has assigned_to="user-technician"
        When: GET /api/v1/followups/fu-123/messages is called
        Then: Response is 200 with the messages array
        """
        # Update followup to match assignee
        fu_as_assignee = {
            **followup_record,
            "assigned_to": TECHNICIAN_USER_ID,
        }

        technician_jwt = {
            "sub": TECHNICIAN_USER_ID,
            "email": ASSIGNEE_EMAIL,
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }

        mock_client = _mock_supabase_for_messages(fu_as_assignee, sample_messages)

        with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock_jwt:
            mock_jwt.return_value = technician_jwt
            with patch("app.api.followups.create_client", return_value=mock_client):
                response = client.get(
                    MESSAGES_URL,
                    headers={"Authorization": "Bearer technician-token"},
                )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 3

    def test_patch_viewed_returns_404_when_user_is_outsider(
        self, client,
    ):
        """
        15-4-message-thread-ui-INT-021: PATCH /viewed returns 404 when user is
        neither assigner nor assignee.

        Given: An authenticated user with id="user-outsider", follow-up "fu-123"
               has assigned_by="user-manager" and assigned_to="user-technician"
        When: PATCH /api/v1/followups/fu-123/viewed is called with outsider's token
        Then: Response is 404
        """
        outsider_jwt = {
            "sub": OUTSIDER_USER_ID,
            "email": "outsider@plant.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }

        followup = {
            "id": FOLLOWUP_ID,
            "action_summary": "Replace bearing",
            "assigned_to": TECHNICIAN_USER_ID,
            "assigned_by": MANAGER_USER_ID,
            "status": "in_progress",
            "last_viewed_at": None,
        }

        mock_client = _mock_supabase_for_viewed(followup)

        with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock_jwt:
            mock_jwt.return_value = outsider_jwt
            with patch("app.api.followups.create_client", return_value=mock_client):
                response = client.patch(
                    VIEWED_URL,
                    headers={"Authorization": "Bearer outsider-token"},
                )

        assert response.status_code == 404
