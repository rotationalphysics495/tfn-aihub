"""
Tests for SMTPEmailProvider and SendResult.

Story: 15.2 - Email Notification Service
AC#1: Email sent on follow-up assignment
AC#3: Graceful failure on send error

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (imports will fail).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone


# =============================================================================
# AC1: SMTPEmailProvider sends email correctly
# =============================================================================


class TestSMTPEmailProviderSend:
    """Tests for SMTPEmailProvider.send() method."""

    def test_send_email_successfully(self):
        """
        15-2-email-notification-service-UNIT-001: SMTPEmailProvider sends email successfully via aiosmtplib.

        Given: SMTP credentials are configured and aiosmtplib connection is mocked to succeed
        When: SMTPEmailProvider.send() is called with a valid recipient, subject, HTML body, and plain text body
        Then: aiosmtplib.send() is called with correctly constructed EmailMessage,
              and SendResult is returned with success=True, error=None, sent_at populated
        """
        from app.services.email.provider import SMTPEmailProvider, SendResult

        provider = SMTPEmailProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=True,
        )

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=({}, "OK"))

            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="assignee@example.com",
                    subject="[Action Required] safety - Pump-101: Replace bearing",
                    html_body="<html><body>Test</body></html>",
                    text_body="Plain text version",
                )
            )

        assert isinstance(result, SendResult)
        assert result.success is True
        assert result.error is None
        assert result.sent_at is not None
        assert isinstance(result.sent_at, datetime)

        # Verify aiosmtplib.send was called
        mock_smtp.send.assert_called_once()
        # Verify the email message was constructed correctly
        call_args = mock_smtp.send.call_args
        msg = call_args[0][0] if call_args[0] else call_args[1].get("message")
        assert msg["To"] == "assignee@example.com"
        assert msg["Subject"] == "[Action Required] safety - Pump-101: Replace bearing"
        assert msg["From"] == "noreply@plant.com"

    def test_email_headers_and_from_address(self):
        """
        15-2-email-notification-service-UNIT-002: SMTPEmailProvider sets correct email headers and From address.

        Given: SMTP is configured with smtp_from="noreply@plant.com"
        When: SMTPEmailProvider.send() is called
        Then: EmailMessage has From=smtp_from, To=recipient, Subject=provided subject,
              MIME type is multipart/alternative
        """
        from app.services.email.provider import SMTPEmailProvider

        provider = SMTPEmailProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=True,
        )

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=({}, "OK"))

            import asyncio
            asyncio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="user@example.com",
                    subject="Test Subject",
                    html_body="<html>Test</html>",
                    text_body="Test",
                )
            )

        call_args = mock_smtp.send.call_args
        msg = call_args[0][0] if call_args[0] else call_args[1].get("message")
        assert msg["From"] == "noreply@plant.com"
        assert msg["To"] == "user@example.com"
        assert msg["Subject"] == "Test Subject"
        assert msg.get_content_type() == "multipart/alternative"

    def test_connects_with_tls_when_enabled(self):
        """
        15-2-email-notification-service-UNIT-003: SMTPEmailProvider connects with TLS when smtp_use_tls is True.

        Given: smtp_use_tls=True in settings and aiosmtplib is mocked
        When: SMTPEmailProvider.send() is called
        Then: aiosmtplib SMTP connection uses TLS/STARTTLS with configured host and port
        """
        from app.services.email.provider import SMTPEmailProvider

        provider = SMTPEmailProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=True,
        )

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=({}, "OK"))

            import asyncio
            asyncio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="user@example.com",
                    subject="Test",
                    html_body="<html>Test</html>",
                    text_body="Test",
                )
            )

        # Verify TLS was used in the send call
        call_kwargs = mock_smtp.send.call_args[1] if mock_smtp.send.call_args[1] else {}
        # The provider should pass use_tls=True or start_tls=True
        assert call_kwargs.get("use_tls", False) or call_kwargs.get("start_tls", False), \
            "TLS should be enabled when smtp_use_tls=True"
        assert call_kwargs.get("hostname") == "smtp.office365.com"
        assert call_kwargs.get("port") == 587

    def test_connects_without_tls_when_disabled(self):
        """
        15-2-email-notification-service-UNIT-004: SMTPEmailProvider connects without TLS when smtp_use_tls is False.

        Given: smtp_use_tls=False in settings and aiosmtplib is mocked
        When: SMTPEmailProvider.send() is called
        Then: aiosmtplib SMTP connection is created without TLS/STARTTLS
        """
        from app.services.email.provider import SMTPEmailProvider

        provider = SMTPEmailProvider(
            smtp_host="localhost",
            smtp_port=25,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=False,
        )

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=({}, "OK"))

            import asyncio
            asyncio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="user@example.com",
                    subject="Test",
                    html_body="<html>Test</html>",
                    text_body="Test",
                )
            )

        call_kwargs = mock_smtp.send.call_args[1] if mock_smtp.send.call_args[1] else {}
        # TLS should NOT be enabled
        assert not call_kwargs.get("use_tls", False), \
            "TLS should not be enabled when smtp_use_tls=False"
        assert not call_kwargs.get("start_tls", False), \
            "STARTTLS should not be enabled when smtp_use_tls=False"

    def test_respects_connection_timeout(self):
        """
        15-2-email-notification-service-UNIT-005: SMTPEmailProvider respects connection timeout.

        Given: aiosmtplib is mocked and configured with a 10s default timeout
        When: SMTPEmailProvider.send() is called
        Then: The SMTP connection is opened with timeout=10
        """
        from app.services.email.provider import SMTPEmailProvider

        provider = SMTPEmailProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=True,
            timeout=10,
        )

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=({}, "OK"))

            import asyncio
            asyncio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="user@example.com",
                    subject="Test",
                    html_body="<html>Test</html>",
                    text_body="Test",
                )
            )

        call_kwargs = mock_smtp.send.call_args[1] if mock_smtp.send.call_args[1] else {}
        assert call_kwargs.get("timeout") == 10

    def test_returns_failure_on_smtp_error(self):
        """
        15-2-email-notification-service-UNIT-006: SMTPEmailProvider returns failure SendResult on SMTP error.

        Given: aiosmtplib.send() is mocked to raise an SMTPException("Connection refused")
        When: SMTPEmailProvider.send() is called
        Then: SendResult with success=False, error containing "Connection refused", sent_at=None;
              no exception propagated
        """
        from app.services.email.provider import SMTPEmailProvider, SendResult

        provider = SMTPEmailProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=True,
        )

        import aiosmtplib

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(
                side_effect=aiosmtplib.SMTPException("Connection refused")
            )
            mock_smtp.SMTPException = aiosmtplib.SMTPException

            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="user@example.com",
                    subject="Test",
                    html_body="<html>Test</html>",
                    text_body="Test",
                )
            )

        assert isinstance(result, SendResult)
        assert result.success is False
        assert "Connection refused" in result.error
        assert result.sent_at is None

    def test_returns_failure_on_network_timeout(self):
        """
        15-2-email-notification-service-UNIT-007: SMTPEmailProvider returns failure SendResult on network timeout.

        Given: aiosmtplib connection is mocked to raise asyncio.TimeoutError
        When: SMTPEmailProvider.send() is called
        Then: SendResult with success=False, error describing timeout, sent_at=None
        """
        import asyncio as aio
        from app.services.email.provider import SMTPEmailProvider, SendResult

        provider = SMTPEmailProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=True,
        )

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(side_effect=aio.TimeoutError())

            result = aio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="user@example.com",
                    subject="Test",
                    html_body="<html>Test</html>",
                    text_body="Test",
                )
            )

        assert isinstance(result, SendResult)
        assert result.success is False
        assert result.error is not None
        assert "timeout" in result.error.lower()
        assert result.sent_at is None

    def test_authenticates_with_username_password(self):
        """
        15-2-email-notification-service-UNIT-031: SMTPEmailProvider handles authentication with username/password.

        Given: SMTP is configured with smtp_user and smtp_password, aiosmtplib is mocked
        When: SMTPEmailProvider.send() is called
        Then: The SMTP connection authenticates with configured username and password
        """
        from app.services.email.provider import SMTPEmailProvider

        provider = SMTPEmailProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
            smtp_use_tls=True,
        )

        with patch("app.services.email.provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=({}, "OK"))

            import asyncio
            asyncio.get_event_loop().run_until_complete(
                provider.send(
                    recipient="user@example.com",
                    subject="Test",
                    html_body="<html>Test</html>",
                    text_body="Test",
                )
            )

        call_kwargs = mock_smtp.send.call_args[1] if mock_smtp.send.call_args[1] else {}
        assert call_kwargs.get("username") == "user@plant.com"
        assert call_kwargs.get("password") == "secret"


# =============================================================================
# Cross-Cutting: SendResult dataclass
# =============================================================================


class TestSendResult:
    """Tests for SendResult dataclass."""

    def test_send_result_success(self):
        """
        15-2-email-notification-service-UNIT-025: SendResult correctly represents success.

        Given: A successful email send scenario
        When: SendResult is constructed with success=True, error=None, sent_at=datetime
        Then: success is True, error is None, sent_at is a valid datetime
        """
        from app.services.email.provider import SendResult

        now = datetime.now(timezone.utc)
        result = SendResult(success=True, error=None, sent_at=now)

        assert result.success is True
        assert result.error is None
        assert result.sent_at == now
        assert isinstance(result.sent_at, datetime)

    def test_send_result_failure(self):
        """
        15-2-email-notification-service-UNIT-026: SendResult correctly represents failure.

        Given: A failed email send scenario
        When: SendResult is constructed with success=False, error="Connection timeout", sent_at=None
        Then: success is False, error is "Connection timeout", sent_at is None
        """
        from app.services.email.provider import SendResult

        result = SendResult(success=False, error="Connection timeout", sent_at=None)

        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.sent_at is None


# =============================================================================
# Cross-Cutting: Singleton pattern
# =============================================================================


class TestEmailServiceFactory:
    """Tests for get_email_service factory function."""

    def test_get_email_service_returns_singleton(self):
        """
        15-2-email-notification-service-UNIT-027: get_email_service factory returns singleton.

        Given: The email service module is initialized
        When: get_email_service() is called multiple times
        Then: The same SMTPEmailProvider instance is returned each time
        """
        from app.services.email import get_email_service

        service_1 = get_email_service()
        service_2 = get_email_service()

        assert service_1 is service_2
