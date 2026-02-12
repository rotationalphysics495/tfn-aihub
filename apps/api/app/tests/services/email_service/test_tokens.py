"""
Tests for TokenService — token generation, validation, and usage.

Story: 15.3 - Response Capture via Token Link
AC#1: Response page renders via token link (token generation & validation)
AC#3: Expired token shows expiry message
AC#4: Invalid token shows error
Cross-Cutting: Token service factory and error handling

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (imports will fail).
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from uuid import uuid4


# --- Constants ---

FOLLOWUP_ID = str(uuid4())
ASSIGNEE_EMAIL = "assignee@plant.com"


# --- Fixtures ---


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase service_role client for token operations."""
    client = MagicMock()
    mock_chain = MagicMock()
    client.table.return_value = mock_chain
    mock_chain.insert.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.update.return_value = mock_chain
    mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
    return client


@pytest.fixture
def mock_supabase_empty():
    """Mock Supabase client that returns empty result set."""
    client = MagicMock()
    mock_chain = MagicMock()
    client.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.execute.return_value = MagicMock(data=[])
    return client


@pytest.fixture
def mock_supabase_error():
    """Mock Supabase client that raises an exception."""
    client = MagicMock()
    mock_chain = MagicMock()
    client.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.execute.side_effect = Exception("Supabase unavailable")
    return client


# =============================================================================
# AC1: Token generation
# =============================================================================


class TestTokenServiceGenerate:
    """Tests for TokenService.generate_token() method."""

    def test_generate_token_returns_uuid_and_stores_record(self, mock_supabase_client):
        """
        15-3-response-capture-via-token-link-UNIT-001: TokenService.generate_token produces UUID
        and stores in followup_messages.

        Given: A valid followup_id (UUID) and assignee_email="assignee@plant.com" exist,
               and the Supabase client is mocked
        When: TokenService.generate_token(followup_id, assignee_email) is called
        Then: A UUID v4 string is returned, and a followup_messages record is inserted
              with response_token set to the generated UUID, token_expires_at set to
              approximately now + 72 hours, token_used_at=None, direction='outbound',
              message_type='assignment', and sender_email=assignee_email
        """
        from app.services.email.tokens import TokenService

        service = TokenService(supabase_client=mock_supabase_client)
        token = service.generate_token(FOLLOWUP_ID, ASSIGNEE_EMAIL)

        # Token should be a non-empty string (UUID format)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify Supabase insert was called on followup_messages
        mock_supabase_client.table.assert_called_with("followup_messages")
        insert_call = mock_supabase_client.table.return_value.insert
        insert_call.assert_called_once()

        inserted_data = insert_call.call_args[0][0]
        assert inserted_data["response_token"] == token
        assert inserted_data["followup_id"] == FOLLOWUP_ID
        assert inserted_data["sender_email"] == ASSIGNEE_EMAIL
        assert inserted_data["direction"] == "outbound"
        assert inserted_data["message_type"] == "assignment"
        assert inserted_data.get("token_used_at") is None
        assert "token_expires_at" in inserted_data

    def test_generate_token_sets_72_hour_expiry(self, mock_supabase_client):
        """
        15-3-response-capture-via-token-link-UNIT-002: TokenService.generate_token sets
        token_expires_at to 72 hours from now.

        Given: The current time is known (mocked via datetime), and Supabase client is mocked
        When: TokenService.generate_token() is called
        Then: The token_expires_at value in the inserted record is exactly 72 hours after
              the current time (within a small tolerance)
        """
        from app.services.email.tokens import TokenService

        frozen_now = datetime(2026, 2, 11, 10, 0, 0, tzinfo=timezone.utc)
        expected_expiry = frozen_now + timedelta(hours=72)

        with patch("app.services.email.tokens.datetime") as mock_dt:
            mock_dt.now.return_value = frozen_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            service = TokenService(supabase_client=mock_supabase_client)
            service.generate_token(FOLLOWUP_ID, ASSIGNEE_EMAIL)

        insert_call = mock_supabase_client.table.return_value.insert
        inserted_data = insert_call.call_args[0][0]

        # token_expires_at should be ~72 hours from now
        expires_at = inserted_data["token_expires_at"]
        # Handle both string and datetime formats
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        diff = abs((expires_at - expected_expiry).total_seconds())
        assert diff < 5, f"Expiry should be 72h from now, diff was {diff}s"


# =============================================================================
# AC1 / AC3 / AC4: Token validation
# =============================================================================


class TestTokenServiceValidate:
    """Tests for TokenService.validate_token() method."""

    def test_validate_token_returns_valid_for_fresh_token(self, mock_supabase_client):
        """
        15-3-response-capture-via-token-link-UNIT-003: TokenService.validate_token returns
        valid result for fresh token.

        Given: A followup_messages record exists with response_token="valid-uuid-token",
               token_expires_at in the future, and token_used_at=None; Supabase client is
               mocked to return this record
        When: TokenService.validate_token("valid-uuid-token") is called
        Then: A TokenValidationResult is returned with is_valid=True, followup_id matching
              the record, assignee_email matching the record's sender_email, and error_reason=None
        """
        from app.services.email.tokens import TokenService

        future_expiry = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        mock_record = {
            "response_token": "valid-uuid-token",
            "followup_id": FOLLOWUP_ID,
            "sender_email": ASSIGNEE_EMAIL,
            "token_expires_at": future_expiry,
            "token_used_at": None,
        }

        mock_chain = MagicMock()
        mock_supabase_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[mock_record])

        service = TokenService(supabase_client=mock_supabase_client)
        result = service.validate_token("valid-uuid-token")

        assert result.is_valid is True
        assert result.followup_id == FOLLOWUP_ID
        assert result.assignee_email == ASSIGNEE_EMAIL
        assert result.error_reason is None

    def test_validate_token_returns_expired_for_past_expiry(self, mock_supabase_client):
        """
        15-3-response-capture-via-token-link-UNIT-004: TokenService.validate_token returns
        expired for token past 72h.

        Given: A followup_messages record exists with response_token="expired-token",
               token_expires_at in the past (e.g., 73 hours ago), and token_used_at=None;
               Supabase is mocked
        When: TokenService.validate_token("expired-token") is called
        Then: A TokenValidationResult is returned with is_valid=False and error_reason='expired'
        """
        from app.services.email.tokens import TokenService

        past_expiry = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mock_record = {
            "response_token": "expired-token",
            "followup_id": FOLLOWUP_ID,
            "sender_email": ASSIGNEE_EMAIL,
            "token_expires_at": past_expiry,
            "token_used_at": None,
        }

        mock_chain = MagicMock()
        mock_supabase_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[mock_record])

        service = TokenService(supabase_client=mock_supabase_client)
        result = service.validate_token("expired-token")

        assert result.is_valid is False
        assert result.error_reason == "expired"

    def test_validate_token_returns_expired_for_used_token(self, mock_supabase_client):
        """
        15-3-response-capture-via-token-link-UNIT-005: TokenService.validate_token returns
        used for already-consumed token.

        Given: A followup_messages record exists with response_token="used-token",
               token_expires_at in the future, and token_used_at set to a past timestamp;
               Supabase is mocked
        When: TokenService.validate_token("used-token") is called
        Then: A TokenValidationResult is returned with is_valid=False and
              error_reason='expired' (used tokens show same message as expired)
        """
        from app.services.email.tokens import TokenService

        future_expiry = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        mock_record = {
            "response_token": "used-token",
            "followup_id": FOLLOWUP_ID,
            "sender_email": ASSIGNEE_EMAIL,
            "token_expires_at": future_expiry,
            "token_used_at": "2026-02-10T12:00:00Z",
        }

        mock_chain = MagicMock()
        mock_supabase_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[mock_record])

        service = TokenService(supabase_client=mock_supabase_client)
        result = service.validate_token("used-token")

        assert result.is_valid is False
        assert result.error_reason == "expired"

    def test_validate_token_returns_invalid_for_nonexistent_token(self, mock_supabase_empty):
        """
        15-3-response-capture-via-token-link-UNIT-006: TokenService.validate_token returns
        invalid for nonexistent token.

        Given: No followup_messages record exists with response_token="nonexistent-token";
               Supabase query returns empty data
        When: TokenService.validate_token("nonexistent-token") is called
        Then: A TokenValidationResult is returned with is_valid=False and error_reason='invalid'
        """
        from app.services.email.tokens import TokenService

        service = TokenService(supabase_client=mock_supabase_empty)
        result = service.validate_token("nonexistent-token")

        assert result.is_valid is False
        assert result.error_reason == "invalid"


# =============================================================================
# AC2: Token mark as used
# =============================================================================


class TestTokenServiceMarkUsed:
    """Tests for TokenService.mark_token_used() method."""

    def test_mark_token_used_sets_timestamp(self, mock_supabase_client):
        """
        15-3-response-capture-via-token-link-UNIT-007: TokenService.mark_token_used sets
        token_used_at timestamp.

        Given: A followup_messages record exists with response_token="token-to-use"
               and token_used_at=None; Supabase is mocked
        When: TokenService.mark_token_used("token-to-use") is called
        Then: The Supabase update is called on the followup_messages record setting
              token_used_at to the current timestamp (not None)
        """
        from app.services.email.tokens import TokenService

        service = TokenService(supabase_client=mock_supabase_client)
        service.mark_token_used("token-to-use")

        # Verify update was called on followup_messages
        mock_supabase_client.table.assert_called_with("followup_messages")
        update_call = mock_supabase_client.table.return_value.update
        update_call.assert_called_once()

        update_data = update_call.call_args[0][0]
        assert "token_used_at" in update_data
        assert update_data["token_used_at"] is not None

        # Verify eq was called with the token
        eq_call = mock_supabase_client.table.return_value.update.return_value.eq
        eq_call.assert_called_with("response_token", "token-to-use")


# =============================================================================
# Cross-Cutting: Singleton factory
# =============================================================================


class TestTokenServiceFactory:
    """Tests for get_token_service factory function."""

    def test_get_token_service_returns_singleton(self):
        """
        15-3-response-capture-via-token-link-UNIT-013: get_token_service factory returns singleton.

        Given: The email service module is initialized
        When: get_token_service() is called multiple times
        Then: The same TokenService instance is returned each time
        """
        from app.services.email import get_token_service

        service_1 = get_token_service()
        service_2 = get_token_service()

        assert service_1 is service_2


# =============================================================================
# Cross-Cutting: Service role client
# =============================================================================


class TestTokenServiceClient:
    """Tests for TokenService Supabase client configuration."""

    def test_token_service_uses_service_role_client(self):
        """
        15-3-response-capture-via-token-link-UNIT-014: TokenService uses service_role Supabase client.

        Given: TokenService is instantiated with a Supabase client
        When: Any token operation is performed (generate, validate, mark_used)
        Then: The Supabase service_role client is used (not a user-scoped JWT client),
              ensuring RLS is bypassed since the public endpoints have no authenticated user
        """
        from app.services.email.tokens import TokenService

        mock_service_role_client = MagicMock()
        mock_chain = MagicMock()
        mock_service_role_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value = MagicMock(data=[])

        service = TokenService(supabase_client=mock_service_role_client)
        service.validate_token("some-token")

        # The service_role client should be used for the query
        mock_service_role_client.table.assert_called_with("followup_messages")


# =============================================================================
# Cross-Cutting: Error handling
# =============================================================================


class TestTokenServiceErrorHandling:
    """Tests for TokenService error handling."""

    def test_validate_token_propagates_database_errors(self, mock_supabase_error):
        """
        15-3-response-capture-via-token-link-UNIT-015: TokenService handles database errors
        in validate_token gracefully.

        Given: Supabase client raises an exception during the token lookup query
        When: TokenService.validate_token() is called
        Then: The error is propagated as an appropriate exception (not silently swallowed),
              allowing the API endpoint to return a 500 error
        """
        from app.services.email.tokens import TokenService

        service = TokenService(supabase_client=mock_supabase_error)

        with pytest.raises(Exception):
            service.validate_token("any-token")
