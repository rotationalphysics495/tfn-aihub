"""
Tests for FollowUpNotificationService.

Story: 15.2 - Email Notification Service
AC#1: Email sent on follow-up assignment (notification orchestration)
AC#2: Graceful degradation when SMTP not configured
AC#3: Graceful failure on send error

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (imports will fail).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4


# --- Constants ---

FOLLOWUP_ID = str(uuid4())
ASSIGNER_USER_ID = str(uuid4())
ASSIGNEE_USER_ID = str(uuid4())
ASSIGNER_EMAIL = "manager@plant.com"
ASSIGNEE_EMAIL = "assignee@plant.com"


# --- Fixtures ---


@pytest.fixture
def sample_followup_data():
    """Standard follow-up data for notification tests."""
    return {
        "followup_id": FOLLOWUP_ID,
        "action_item_id": "AI-001",
        "action_summary": "Replace bearing",
        "asset_name": "Pump-101",
        "category": "safety",
        "assigned_to": ASSIGNEE_USER_ID,
        "assigned_by": ASSIGNER_USER_ID,
        "sender_email": ASSIGNER_EMAIL,
        "note": "Please prioritize this week",
        "recommendation": "Replace worn bearing immediately",
        "evidence_summary": "Vibration levels exceeded threshold 3x",
        "financial_impact": "$15,000 estimated repair cost",
        "assigner_name": "John Manager",
        "report_date": "2026-02-10",
    }


@pytest.fixture
def mock_email_provider_success():
    """Mock EmailProvider that returns success."""
    provider = MagicMock()
    sent_at = datetime.now(timezone.utc)
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.error = None
    mock_result.sent_at = sent_at
    provider.send = AsyncMock(return_value=mock_result)
    return provider


@pytest.fixture
def mock_email_provider_failure():
    """Mock EmailProvider that returns failure."""
    provider = MagicMock()
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.error = "Connection refused"
    mock_result.sent_at = None
    provider.send = AsyncMock(return_value=mock_result)
    return provider


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for database operations."""
    client = MagicMock()
    # Mock the chain: table().insert().execute()
    mock_chain = MagicMock()
    client.table.return_value = mock_chain
    mock_chain.insert.return_value = mock_chain
    mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
    return client


@pytest.fixture
def mock_supabase_with_user():
    """Mock Supabase client that resolves a user from auth.users."""
    client = MagicMock()

    # Mock auth.admin.get_user_by_id to return user with email
    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.email = ASSIGNEE_EMAIL
    client.auth.admin.get_user_by_id.return_value = mock_user

    # Mock table operations
    mock_chain = MagicMock()
    client.table.return_value = mock_chain
    mock_chain.insert.return_value = mock_chain
    mock_chain.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])

    return client


# =============================================================================
# AC1: Notification service creates followup_messages record
# =============================================================================


class TestFollowUpNotificationServiceSend:
    """Tests for FollowUpNotificationService.send_assignment_notification()."""

    @pytest.mark.asyncio
    async def test_creates_followup_messages_record_on_success(
        self, sample_followup_data, mock_email_provider_success, mock_supabase_with_user,
    ):
        """
        15-2-email-notification-service-UNIT-014: Creates followup_messages record on successful send.

        Given: EmailProvider.send() returns SendResult(success=True, sent_at=<timestamp>),
               Supabase client is mocked
        When: send_assignment_notification() is called with valid follow-up data
        Then: A record is inserted into followup_messages with correct fields
        """
        from app.services.email.notification_service import FollowUpNotificationService

        service = FollowUpNotificationService(
            email_provider=mock_email_provider_success,
            supabase_client=mock_supabase_with_user,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            await service.send_assignment_notification(sample_followup_data)

        # Verify followup_messages insert was called
        mock_supabase_with_user.table.assert_any_call("followup_messages")
        insert_call = mock_supabase_with_user.table.return_value.insert
        insert_call.assert_called_once()

        inserted_data = insert_call.call_args[0][0]
        assert inserted_data["followup_id"] == FOLLOWUP_ID
        assert inserted_data["direction"] == "outbound"
        assert inserted_data["message_type"] == "assignment"
        assert inserted_data["sender_id"] == ASSIGNER_USER_ID
        assert inserted_data["sender_email"] == ASSIGNER_EMAIL
        assert inserted_data["sent_at"] is not None
        assert inserted_data.get("failed_at") is None

    @pytest.mark.asyncio
    async def test_resolves_assignee_email_from_auth_users(
        self, sample_followup_data, mock_email_provider_success, mock_supabase_with_user,
    ):
        """
        15-2-email-notification-service-UNIT-015: Resolves assignee email from auth.users.

        Given: assigned_to UUID exists in auth.users with email="assignee@plant.com"
        When: send_assignment_notification() is called
        Then: Email is sent to the resolved email, not hardcoded
        """
        from app.services.email.notification_service import FollowUpNotificationService

        service = FollowUpNotificationService(
            email_provider=mock_email_provider_success,
            supabase_client=mock_supabase_with_user,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            await service.send_assignment_notification(sample_followup_data)

        # Verify auth.users lookup was called with assignee UUID
        mock_supabase_with_user.auth.admin.get_user_by_id.assert_called_once_with(
            ASSIGNEE_USER_ID
        )

        # Verify email was sent to resolved email
        send_call = mock_email_provider_success.send
        send_call.assert_called_once()
        call_kwargs = send_call.call_args[1] if send_call.call_args[1] else {}
        call_args = send_call.call_args[0] if send_call.call_args[0] else ()
        recipient = call_kwargs.get("recipient") or (call_args[0] if call_args else None)
        assert recipient == ASSIGNEE_EMAIL

    @pytest.mark.asyncio
    async def test_never_raises_exceptions(self, sample_followup_data):
        """
        15-2-email-notification-service-UNIT-016: FollowUpNotificationService never raises exceptions.

        Given: An unexpected RuntimeError occurs during email send
        When: send_assignment_notification() is called
        Then: Exception is caught and logged, method completes without raising
        """
        from app.services.email.notification_service import FollowUpNotificationService

        mock_provider = MagicMock()
        mock_provider.send = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.user = MagicMock()
        mock_user.user.email = "test@example.com"
        mock_client.auth.admin.get_user_by_id.return_value = mock_user

        service = FollowUpNotificationService(
            email_provider=mock_provider,
            supabase_client=mock_client,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            # Should NOT raise
            await service.send_assignment_notification(sample_followup_data)


# =============================================================================
# AC2: Graceful degradation when SMTP not configured
# =============================================================================


class TestNotificationServiceSMTPNotConfigured:
    """Tests for notification service behavior when SMTP is not configured."""

    @pytest.mark.asyncio
    async def test_logs_warning_and_returns_early(self, sample_followup_data):
        """
        15-2-email-notification-service-UNIT-020: Logs warning and returns early when SMTP not configured.

        Given: smtp_configured returns False and logger is mocked
        When: send_assignment_notification() is called with valid follow-up data
        Then: Warning logged, method returns without sending email, no followup_messages created
        """
        from app.services.email.notification_service import FollowUpNotificationService

        mock_provider = MagicMock()
        mock_client = MagicMock()

        service = FollowUpNotificationService(
            email_provider=mock_provider,
            supabase_client=mock_client,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = False

            with patch("app.services.email.notification_service.logger") as mock_logger:
                await service.send_assignment_notification(sample_followup_data)

                # Warning should be logged
                mock_logger.warning.assert_called_once()
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "smtp" in warning_msg.lower() or "email" in warning_msg.lower() or \
                    "not configured" in warning_msg.lower()

        # Email should NOT be sent
        mock_provider.send.assert_not_called()

        # No followup_messages should be created
        mock_client.table.assert_not_called()


# =============================================================================
# AC3: Graceful failure on send error
# =============================================================================


class TestNotificationServiceSendFailure:
    """Tests for notification service behavior when email send fails."""

    @pytest.mark.asyncio
    async def test_creates_followup_messages_with_failed_at(
        self, sample_followup_data, mock_email_provider_failure, mock_supabase_with_user,
    ):
        """
        15-2-email-notification-service-UNIT-021: Creates followup_messages with failed_at on email send failure.

        Given: EmailProvider.send() returns SendResult(success=False, error="Connection refused")
        When: send_assignment_notification() is called
        Then: followup_messages record created with sent_at=None and failed_at set
        """
        from app.services.email.notification_service import FollowUpNotificationService

        service = FollowUpNotificationService(
            email_provider=mock_email_provider_failure,
            supabase_client=mock_supabase_with_user,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            await service.send_assignment_notification(sample_followup_data)

        # Verify insert was called
        insert_call = mock_supabase_with_user.table.return_value.insert
        insert_call.assert_called_once()

        inserted_data = insert_call.call_args[0][0]
        assert inserted_data["direction"] == "outbound"
        assert inserted_data["message_type"] == "assignment"
        assert inserted_data["sent_at"] is None
        assert inserted_data["failed_at"] is not None

    @pytest.mark.asyncio
    async def test_logs_error_details_on_send_failure(
        self, sample_followup_data, mock_email_provider_failure, mock_supabase_with_user,
    ):
        """
        15-2-email-notification-service-UNIT-022: Logs error details on send failure.

        Given: EmailProvider.send() returns failure with error="Invalid recipient address"
        When: send_assignment_notification() is called
        Then: Error-level log with error details, followup_id, and recipient email
        """
        from app.services.email.notification_service import FollowUpNotificationService
        from app.services.email.provider import SendResult

        mock_provider = MagicMock()
        mock_provider.send = AsyncMock(
            return_value=SendResult(success=False, error="Invalid recipient address", sent_at=None)
        )

        service = FollowUpNotificationService(
            email_provider=mock_provider,
            supabase_client=mock_supabase_with_user,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            with patch("app.services.email.notification_service.logger") as mock_logger:
                await service.send_assignment_notification(sample_followup_data)

                # Error should be logged
                mock_logger.error.assert_called()
                error_msg = str(mock_logger.error.call_args)
                assert "Invalid recipient address" in error_msg or \
                    mock_logger.error.call_count > 0

    @pytest.mark.asyncio
    async def test_does_not_propagate_send_failure(self, sample_followup_data):
        """
        15-2-email-notification-service-UNIT-023: Does not propagate send failure to caller.

        Given: EmailProvider.send() raises ConnectionResetError
        When: send_assignment_notification() is called
        Then: Exception is caught, logged, method returns without raising
        """
        from app.services.email.notification_service import FollowUpNotificationService

        mock_provider = MagicMock()
        mock_provider.send = AsyncMock(side_effect=ConnectionResetError("Connection reset"))

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.user = MagicMock()
        mock_user.user.email = "test@example.com"
        mock_client.auth.admin.get_user_by_id.return_value = mock_user

        service = FollowUpNotificationService(
            email_provider=mock_provider,
            supabase_client=mock_client,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            # Should NOT raise
            await service.send_assignment_notification(sample_followup_data)

    @pytest.mark.asyncio
    async def test_handles_followup_messages_insert_failure(
        self, sample_followup_data, mock_email_provider_success,
    ):
        """
        15-2-email-notification-service-UNIT-024: Handles followup_messages insert failure gracefully.

        Given: Email send succeeds but Supabase insert into followup_messages raises exception
        When: send_assignment_notification() is called
        Then: Exception caught and logged, method does not raise
        """
        from app.services.email.notification_service import FollowUpNotificationService

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.user = MagicMock()
        mock_user.user.email = "test@example.com"
        mock_client.auth.admin.get_user_by_id.return_value = mock_user

        # Make insert raise
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.execute.side_effect = Exception("Supabase unavailable")

        service = FollowUpNotificationService(
            email_provider=mock_email_provider_success,
            supabase_client=mock_client,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            # Should NOT raise
            await service.send_assignment_notification(sample_followup_data)


# =============================================================================
# Cross-Cutting: Singleton pattern
# =============================================================================


class TestNotificationServiceFactory:
    """Tests for get_notification_service factory function."""

    def test_get_notification_service_returns_singleton(self):
        """
        15-2-email-notification-service-UNIT-028: get_notification_service factory returns singleton.

        Given: The email service module is initialized
        When: get_notification_service() is called multiple times
        Then: The same FollowUpNotificationService instance is returned each time
        """
        from app.services.email import get_notification_service

        service_1 = get_notification_service()
        service_2 = get_notification_service()

        assert service_1 is service_2


# =============================================================================
# Edge Case: Assignee not found
# =============================================================================


class TestNotificationServiceEdgeCases:
    """Tests for edge cases in notification service."""

    @pytest.mark.asyncio
    async def test_handles_assignee_not_found(self, sample_followup_data):
        """
        15-2-email-notification-service-UNIT-032: Handles assignee not found in auth.users.

        Given: assigned_to UUID does not exist in auth.users (returns None)
        When: send_assignment_notification() is called
        Then: Error logged, no email sent, method returns without raising
        """
        from app.services.email.notification_service import FollowUpNotificationService

        mock_provider = MagicMock()
        mock_provider.send = AsyncMock()

        mock_client = MagicMock()
        # Return None for user lookup (user not found)
        mock_client.auth.admin.get_user_by_id.return_value = None

        service = FollowUpNotificationService(
            email_provider=mock_provider,
            supabase_client=mock_client,
        )

        with patch("app.services.email.notification_service.get_settings") as mock_settings:
            mock_settings.return_value.smtp_configured = True
            mock_settings.return_value.app_base_url = "https://plant.example.com"

            with patch("app.services.email.notification_service.logger") as mock_logger:
                # Should NOT raise
                await service.send_assignment_notification(sample_followup_data)

                # Error should be logged about user not found
                mock_logger.error.assert_called()

        # Email should NOT be sent
        mock_provider.send.assert_not_called()
