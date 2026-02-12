"""
Tests for TeamsWebhookClient service.

Story: 18.2 - Teams Webhook Configuration
AC#2: Test message posting to configured Teams channel
AC#3: Graceful degradation when no webhook URL configured

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (TeamsWebhookClient module
doesn't exist yet).
"""

import pytest
import logging
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
import httpx


# =============================================================================
# Test Data
# =============================================================================

SAMPLE_WEBHOOK_URL = "https://outlook.office.com/webhook/abc123"
SAMPLE_SETTINGS_URL = "https://outlook.office.com/webhook/from-settings"
SAMPLE_OVERRIDE_URL = "https://outlook.office.com/webhook/override"

SAMPLE_CARD_PAYLOAD = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.4",
    "body": [{"type": "TextBlock", "text": "Test"}],
}

EXPECTED_ENVELOPE = {
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": None,
            "content": SAMPLE_CARD_PAYLOAD,
        }
    ],
}


# =============================================================================
# AC2: TeamsWebhookClient is_configured property
# =============================================================================


class TestTeamsWebhookClientIsConfigured:
    """Tests for TeamsWebhookClient.is_configured property."""

    def test_is_configured_true_when_webhook_url_set(self):
        """
        18-2-teams-webhook-configuration-UNIT-006: TeamsWebhookClient.is_configured
        returns True when webhook URL is set.

        Given: A TeamsWebhookClient initialized with a non-empty webhook_url
        When: The is_configured property is accessed
        Then: It returns True
        """
        from app.services.notifications.teams import TeamsWebhookClient

        client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)

        assert client.is_configured is True

    def test_is_configured_false_when_webhook_url_empty(self):
        """
        18-2-teams-webhook-configuration-UNIT-007: TeamsWebhookClient.is_configured
        returns False when webhook URL is empty.

        Given: A TeamsWebhookClient initialized with empty webhook_url
        When: The is_configured property is accessed
        Then: It returns False
        """
        with patch("app.services.notifications.teams.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(teams_webhook_url="")

            from app.services.notifications.teams import TeamsWebhookClient

            client = TeamsWebhookClient(webhook_url="")

            assert client.is_configured is False

    def test_is_configured_false_when_url_is_none(self):
        """
        18-2-teams-webhook-configuration-UNIT-018: TeamsWebhookClient.is_configured
        returns False when URL is None.

        Given: A TeamsWebhookClient initialized with webhook_url=None and settings
               also has empty teams_webhook_url
        When: The is_configured property is accessed
        Then: It returns False
        """
        with patch("app.services.notifications.teams.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(teams_webhook_url="")

            from app.services.notifications.teams import TeamsWebhookClient

            client = TeamsWebhookClient(webhook_url=None)

            assert client.is_configured is False


# =============================================================================
# AC2: TeamsWebhookClient.send_card — success case
# =============================================================================


class TestTeamsWebhookClientSendCardSuccess:
    """Tests for successful send_card operations."""

    @pytest.mark.asyncio
    async def test_send_card_posts_correct_adaptive_card_envelope(self):
        """
        18-2-teams-webhook-configuration-UNIT-008: TeamsWebhookClient.send_card posts
        correct Adaptive Card envelope to webhook URL.

        Given: A TeamsWebhookClient with configured webhook URL and mocked httpx returning 200
        When: send_card(card_payload) is called
        Then: httpx POSTs to the webhook URL with the correct envelope structure
        And: Returns {"success": True, "message": "Message posted to Teams", "status_code": 200}
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
            result = await client.send_card(SAMPLE_CARD_PAYLOAD)

        # Verify the POST was called with the correct URL and envelope
        mock_async_client.post.assert_called_once()
        call_args = mock_async_client.post.call_args
        assert call_args[0][0] == SAMPLE_WEBHOOK_URL or call_args.kwargs.get("url") == SAMPLE_WEBHOOK_URL

        # Verify the JSON body contains the correct envelope
        posted_json = call_args.kwargs.get("json") or call_args[1].get("json")
        assert posted_json["type"] == "message"
        assert len(posted_json["attachments"]) == 1
        attachment = posted_json["attachments"][0]
        assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"
        assert attachment["contentUrl"] is None
        assert attachment["content"] == SAMPLE_CARD_PAYLOAD

        # Verify the result
        assert result["success"] is True
        assert result["message"] == "Message posted to Teams"
        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_send_card_logs_success_on_http_200(self, caplog):
        """
        18-2-teams-webhook-configuration-UNIT-015: TeamsWebhookClient.send_card logs
        success on HTTP 200.

        Given: A TeamsWebhookClient with configured webhook URL and mocked httpx returning 200
        When: send_card(card_payload) is called
        Then: A log message at INFO level is emitted containing "succeeded" and the status code
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)

            with caplog.at_level(logging.INFO):
                await client.send_card(SAMPLE_CARD_PAYLOAD)

        assert any("succeeded" in record.message.lower() for record in caplog.records), (
            "Expected INFO log message containing 'succeeded'"
        )


# =============================================================================
# AC2: TeamsWebhookClient.send_card — error handling
# =============================================================================


class TestTeamsWebhookClientSendCardErrors:
    """Tests for send_card error handling."""

    @pytest.mark.asyncio
    async def test_send_card_handles_timeout_exception(self):
        """
        18-2-teams-webhook-configuration-UNIT-009: TeamsWebhookClient.send_card
        handles httpx.TimeoutException.

        Given: A TeamsWebhookClient with configured webhook URL and mocked httpx
               that raises TimeoutException
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": "Request timed out", "status_code": None}
        And: No unhandled exception is raised
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_async_client = AsyncMock()
        mock_async_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
            result = await client.send_card(SAMPLE_CARD_PAYLOAD)

        assert result["success"] is False
        assert result["message"] == "Request timed out"
        assert result["status_code"] is None

    @pytest.mark.asyncio
    async def test_send_card_handles_http_status_error_4xx(self):
        """
        18-2-teams-webhook-configuration-UNIT-010: TeamsWebhookClient.send_card
        handles httpx.HTTPStatusError (4xx).

        Given: A TeamsWebhookClient with mocked httpx returning HTTP 400
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": "HTTP 400: Bad Request", "status_code": 400}
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Bad Request",
            request=MagicMock(),
            response=mock_response,
        )
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
            result = await client.send_card(SAMPLE_CARD_PAYLOAD)

        assert result["success"] is False
        assert "HTTP 400" in result["message"]
        assert "Bad Request" in result["message"]
        assert result["status_code"] == 400

    @pytest.mark.asyncio
    async def test_send_card_handles_http_status_error_5xx(self):
        """
        18-2-teams-webhook-configuration-UNIT-011: TeamsWebhookClient.send_card
        handles httpx.HTTPStatusError (5xx).

        Given: A TeamsWebhookClient with mocked httpx returning HTTP 502
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": "HTTP 502: Bad Gateway", "status_code": 502}
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"

        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Bad Gateway",
            request=MagicMock(),
            response=mock_response,
        )
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
            result = await client.send_card(SAMPLE_CARD_PAYLOAD)

        assert result["success"] is False
        assert "HTTP 502" in result["message"]
        assert "Bad Gateway" in result["message"]
        assert result["status_code"] == 502

    @pytest.mark.asyncio
    async def test_send_card_handles_connect_error(self):
        """
        18-2-teams-webhook-configuration-UNIT-012: TeamsWebhookClient.send_card
        handles httpx.ConnectError.

        Given: A TeamsWebhookClient with mocked httpx that raises ConnectError
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": "Connection failed: ...", "status_code": None}
        And: No unhandled exception is raised
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_async_client = AsyncMock()
        mock_async_client.post.side_effect = httpx.ConnectError("Connection refused")
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
            result = await client.send_card(SAMPLE_CARD_PAYLOAD)

        assert result["success"] is False
        assert "Connection failed" in result["message"]
        assert result["status_code"] is None

    @pytest.mark.asyncio
    async def test_send_card_logs_failure_on_error(self, caplog):
        """
        18-2-teams-webhook-configuration-UNIT-016: TeamsWebhookClient.send_card logs
        failure on error.

        Given: A TeamsWebhookClient with mocked httpx that raises TimeoutException
        When: send_card(card_payload) is called
        Then: A log message at ERROR level is emitted containing "timed out"
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_async_client = AsyncMock()
        mock_async_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)

            with caplog.at_level(logging.ERROR):
                await client.send_card(SAMPLE_CARD_PAYLOAD)

        assert any("timed out" in record.message.lower() for record in caplog.records), (
            "Expected ERROR log message containing 'timed out'"
        )


# =============================================================================
# AC3: TeamsWebhookClient.send_card — not configured (early return)
# =============================================================================


class TestTeamsWebhookClientSendCardNotConfigured:
    """Tests for send_card when webhook is not configured."""

    @pytest.mark.asyncio
    async def test_send_card_returns_early_when_not_configured(self):
        """
        18-2-teams-webhook-configuration-UNIT-013: TeamsWebhookClient.send_card
        returns early when not configured.

        Given: A TeamsWebhookClient with no webhook URL configured (empty string)
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": "Teams webhook URL not configured", "status_code": None}
        And: No HTTP request is attempted
        """
        with patch("app.services.notifications.teams.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(teams_webhook_url="")

            from app.services.notifications.teams import TeamsWebhookClient

            with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_httpx:
                client = TeamsWebhookClient(webhook_url="")
                result = await client.send_card(SAMPLE_CARD_PAYLOAD)

                # Verify httpx was never called
                mock_httpx.assert_not_called()

        assert result["success"] is False
        assert result["message"] == "Teams webhook URL not configured"
        assert result["status_code"] is None

    @pytest.mark.asyncio
    async def test_send_card_does_not_make_http_request_when_not_configured(self):
        """
        18-2-teams-webhook-configuration-UNIT-017: TeamsWebhookClient.send_card does
        not make HTTP request when not configured.

        Given: A TeamsWebhookClient with empty/unset webhook URL
        When: send_card(card_payload) is called
        Then: No HTTP POST request is attempted (httpx.AsyncClient never instantiated)
        And: Returns failure dict
        """
        with patch("app.services.notifications.teams.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(teams_webhook_url="")

            from app.services.notifications.teams import TeamsWebhookClient

            with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_httpx_cls:
                client = TeamsWebhookClient(webhook_url="")
                result = await client.send_card(
                    {"type": "AdaptiveCard", "body": [{"type": "TextBlock", "text": "Test"}]}
                )

                # Spy: httpx.AsyncClient should NOT have been instantiated
                mock_httpx_cls.assert_not_called()

        assert result["success"] is False
        assert result["status_code"] is None


# =============================================================================
# AC2: TeamsWebhookClient.send_test_message
# =============================================================================


class TestTeamsWebhookClientSendTestMessage:
    """Tests for send_test_message method."""

    @pytest.mark.asyncio
    async def test_send_test_message_sends_correct_adaptive_card_structure(self):
        """
        18-2-teams-webhook-configuration-UNIT-014: TeamsWebhookClient.send_test_message
        sends correct Adaptive Card structure.

        Given: A TeamsWebhookClient with configured webhook URL and mocked httpx returning 200
        When: send_test_message() is called
        Then: The card payload contains correct schema, type, version
        And: The card body contains a TextBlock with "TFN AI Hub - Connection Test"
        And: The card body contains a TextBlock with "Teams webhook integration is working correctly."
        """
        from app.services.notifications.teams import TeamsWebhookClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notifications.teams.httpx.AsyncClient", return_value=mock_async_client):
            client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
            result = await client.send_test_message()

        # Capture the posted JSON
        call_args = mock_async_client.post.call_args
        posted_json = call_args.kwargs.get("json") or call_args[1].get("json")

        # Navigate to the card content
        card_content = posted_json["attachments"][0]["content"]

        # Verify Adaptive Card structure
        assert card_content["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card_content["type"] == "AdaptiveCard"
        assert card_content["version"] == "1.4"

        # Verify body content
        body = card_content["body"]
        assert len(body) >= 2

        # First TextBlock: title
        title_block = body[0]
        assert title_block["type"] == "TextBlock"
        assert title_block["text"] == "TFN AI Hub - Connection Test"
        assert title_block["weight"] == "Bolder"
        assert title_block["size"] == "Medium"

        # Second TextBlock: description
        desc_block = body[1]
        assert desc_block["type"] == "TextBlock"
        assert desc_block["text"] == "Teams webhook integration is working correctly."
        assert desc_block["wrap"] is True

        # Verify successful result
        assert result["success"] is True


# =============================================================================
# AC3: TeamsWebhookClient construction — settings integration
# =============================================================================


class TestTeamsWebhookClientConstruction:
    """Tests for TeamsWebhookClient constructor and settings integration."""

    def test_client_constructed_from_settings_when_no_explicit_url(self):
        """
        18-2-teams-webhook-configuration-UNIT-020: TeamsWebhookClient constructed
        from settings when no explicit URL provided.

        Given: Settings has teams_webhook_url="https://outlook.office.com/webhook/from-settings"
        When: A TeamsWebhookClient is instantiated with no webhook_url parameter
        Then: client.webhook_url equals the URL from settings
        """
        with patch("app.services.notifications.teams.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                teams_webhook_url=SAMPLE_SETTINGS_URL
            )

            from app.services.notifications.teams import TeamsWebhookClient

            client = TeamsWebhookClient()

            assert client.webhook_url == SAMPLE_SETTINGS_URL

    def test_explicit_webhook_url_overrides_settings(self):
        """
        18-2-teams-webhook-configuration-UNIT-021: TeamsWebhookClient explicit
        webhook_url overrides settings.

        Given: Settings has teams_webhook_url="https://outlook.office.com/webhook/from-settings"
        When: A TeamsWebhookClient is instantiated with an explicit webhook_url
        Then: client.webhook_url equals the explicit URL (overrides settings)
        """
        with patch("app.services.notifications.teams.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                teams_webhook_url=SAMPLE_SETTINGS_URL
            )

            from app.services.notifications.teams import TeamsWebhookClient

            client = TeamsWebhookClient(webhook_url=SAMPLE_OVERRIDE_URL)

            assert client.webhook_url == SAMPLE_OVERRIDE_URL
