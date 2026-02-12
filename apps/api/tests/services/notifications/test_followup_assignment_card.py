"""
Tests for Follow-Up Assignment Teams Card Builder & Webhook Error Handling (Story 18.4)

Test Coverage:
- AC#1: build_followup_assignment_card() produces valid Adaptive Card with header, FactSet, button
- AC#2: TeamsWebhookClient.send_card() returns not-configured result when webhook URL is empty
- AC#3: send_card() handles timeout, HTTP error, connection error, and unexpected exceptions

References:
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.4]
- [Source: apps/api/app/services/notifications/teams.py] - TeamsWebhookClient
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import httpx

from app.services.notifications.teams import TeamsWebhookClient


# ---------------------------------------------------------------------------
# Test Data Factories
# ---------------------------------------------------------------------------

BASE_URL = "https://app.example.com"
SAMPLE_WEBHOOK_URL = "https://outlook.office.com/webhook/test-id/IncomingWebhook/test"


def _make_followup_data(**overrides):
    """Factory for followup_data dicts used by build_followup_assignment_card."""
    data = {
        "action_summary": "Inspect belt tension",
        "asset_name": "Grinder 5",
        "category": "safety",
        "assigner_name": "john.doe",
        "note": "Check by EOD",
        "report_date": "2026-02-10",
    }
    data.update(overrides)
    return data


# ===========================================================================
# AC1 UNIT TESTS: build_followup_assignment_card
# ===========================================================================


class TestBuildFollowupAssignmentCard:
    """AC#1: build_followup_assignment_card() produces valid Adaptive Card JSON."""

    def test_UNIT_001_valid_adaptive_card_structure(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-001:
        build_followup_assignment_card produces valid Adaptive Card structure.

        Given: A followup_data dict with all fields populated and base_url
        When: build_followup_assignment_card(followup_data, base_url) is called
        Then: The returned dict contains $schema, type, version, body array, actions array
        """
        from app.services.notifications.teams import build_followup_assignment_card

        followup_data = _make_followup_data()
        card = build_followup_assignment_card(followup_data, BASE_URL)

        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert isinstance(card["body"], list)
        assert isinstance(card["actions"], list)

    def test_UNIT_002_card_header_text_block(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-002:
        Card header TextBlock displays "Follow-Up Assigned".

        Given: A followup_data dict with all required fields
        When: build_followup_assignment_card(followup_data, base_url) is called
        Then: The first element in body is a TextBlock with text="Follow-Up Assigned",
              weight="Bolder", size="Medium"
        """
        from app.services.notifications.teams import build_followup_assignment_card

        followup_data = _make_followup_data()
        card = build_followup_assignment_card(followup_data, BASE_URL)

        header = card["body"][0]
        assert header["type"] == "TextBlock"
        assert header["text"] == "Follow-Up Assigned"
        assert header["weight"] == "Bolder"
        assert header["size"] == "Medium"

    def test_UNIT_003_factset_contains_all_required_fields(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-003:
        Card FactSet contains all required fields.

        Given: followup_data with action_summary, asset_name, category, assigner_name, note
        When: build_followup_assignment_card(followup_data, base_url) is called
        Then: The card body contains a FactSet with facts for Action, Asset, Category,
              Assigned by, and Note with correct values
        """
        from app.services.notifications.teams import build_followup_assignment_card

        followup_data = _make_followup_data(
            action_summary="Inspect belt tension",
            asset_name="Grinder 5",
            category="safety",
            assigner_name="john.doe",
            note="Check by EOD",
        )
        card = build_followup_assignment_card(followup_data, BASE_URL)

        # Find the FactSet element in the body
        factset = None
        for element in card["body"]:
            if element.get("type") == "FactSet":
                factset = element
                break

        assert factset is not None, "Card body must contain a FactSet element"

        facts = {f["title"]: f["value"] for f in factset["facts"]}
        assert facts["Action:"] == "Inspect belt tension"
        assert facts["Asset:"] == "Grinder 5"
        assert facts["Category:"] == "safety"
        assert facts["Assigned by:"] == "john.doe"
        assert facts["Note:"] == "Check by EOD"

    def test_UNIT_004_note_omitted_when_none(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-004:
        Note fact is omitted when note is None.

        Given: A followup_data dict with note=None
        When: build_followup_assignment_card(followup_data, base_url) is called
        Then: The FactSet does not contain a fact with title "Note:", and the
              remaining facts (Action, Asset, Category, Assigned by) are still present
        """
        from app.services.notifications.teams import build_followup_assignment_card

        followup_data = _make_followup_data(note=None)
        card = build_followup_assignment_card(followup_data, BASE_URL)

        factset = None
        for element in card["body"]:
            if element.get("type") == "FactSet":
                factset = element
                break

        assert factset is not None, "Card body must contain a FactSet element"

        fact_titles = [f["title"] for f in factset["facts"]]
        assert "Note:" not in fact_titles
        assert "Action:" in fact_titles
        assert "Asset:" in fact_titles
        assert "Category:" in fact_titles
        assert "Assigned by:" in fact_titles

    def test_UNIT_005_note_omitted_when_empty_string(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-005:
        Note fact is omitted when note is empty string.

        Given: A followup_data dict with note=""
        When: build_followup_assignment_card(followup_data, base_url) is called
        Then: The FactSet does not contain a fact with title "Note:", and the
              remaining facts are still present
        """
        from app.services.notifications.teams import build_followup_assignment_card

        followup_data = _make_followup_data(note="")
        card = build_followup_assignment_card(followup_data, BASE_URL)

        factset = None
        for element in card["body"]:
            if element.get("type") == "FactSet":
                factset = element
                break

        assert factset is not None, "Card body must contain a FactSet element"

        fact_titles = [f["title"] for f in factset["facts"]]
        assert "Note:" not in fact_titles
        assert "Action:" in fact_titles
        assert "Asset:" in fact_titles
        assert "Category:" in fact_titles
        assert "Assigned by:" in fact_titles

    def test_UNIT_006_view_in_app_button_url(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-006:
        View in App button has correct URL with report_date.

        Given: followup_data with report_date="2026-02-10" and base_url="https://app.example.com"
        When: build_followup_assignment_card(followup_data, base_url) is called
        Then: The actions array contains one Action.OpenUrl with title="View in App"
              and url="https://app.example.com/morning-report?date=2026-02-10"
        """
        from app.services.notifications.teams import build_followup_assignment_card

        followup_data = _make_followup_data(report_date="2026-02-10")
        card = build_followup_assignment_card(followup_data, "https://app.example.com")

        assert len(card["actions"]) == 1
        action = card["actions"][0]
        assert action["type"] == "Action.OpenUrl"
        assert action["title"] == "View in App"
        assert action["url"] == "https://app.example.com/morning-report?date=2026-02-10"

    def test_UNIT_007_base_url_trailing_slash_stripped(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-007:
        base_url trailing slash is stripped before URL construction.

        Given: followup_data with report_date="2026-02-10" and base_url with trailing slash
        When: build_followup_assignment_card(followup_data, base_url) is called
        Then: The "View in App" button URL is correctly formed (no double slash)
        """
        from app.services.notifications.teams import build_followup_assignment_card

        followup_data = _make_followup_data(report_date="2026-02-10")
        card = build_followup_assignment_card(followup_data, "https://app.example.com/")

        action = card["actions"][0]
        assert action["url"] == "https://app.example.com/morning-report?date=2026-02-10"


# ===========================================================================
# AC2 UNIT TESTS: send_card not-configured result
# ===========================================================================


class TestSendCardNotConfigured:
    """AC#2: send_card() returns not-configured result when webhook URL is empty."""

    @pytest.mark.asyncio
    async def test_UNIT_008_returns_not_configured_when_empty_url(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-008:
        TeamsWebhookClient.send_card returns not-configured result when webhook URL is empty.

        Given: TeamsWebhookClient instantiated with webhook_url="" (is_configured=False)
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": "Teams webhook URL not configured",
              "status_code": None} without making any HTTP request
        """
        client = TeamsWebhookClient(webhook_url="")
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            result = await client.send_card(card_payload)

            # No HTTP request should have been made
            mock_client_cls.assert_not_called()

        assert result["success"] is False
        assert result["message"] == "Teams webhook URL not configured"
        assert result["status_code"] is None


# ===========================================================================
# AC3 UNIT TESTS: send_card error handling
# ===========================================================================


class TestSendCardWebhookErrors:
    """AC#3: send_card() handles webhook errors gracefully without propagation."""

    @pytest.mark.asyncio
    async def test_UNIT_009_timeout_logged_no_propagation(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-009:
        Webhook timeout is logged and does not propagate.

        Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post raises TimeoutException
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": "Request timed out", "status_code": None},
              an error is logged, and no exception propagates
        """
        client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.post.side_effect = httpx.TimeoutException("Connection timed out")

            result = await client.send_card(card_payload)

        assert result["success"] is False
        assert result["message"] == "Request timed out"
        assert result["status_code"] is None

    @pytest.mark.asyncio
    async def test_UNIT_010_http_error_logged_no_propagation(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-010:
        Webhook HTTP error (non-2xx) is logged and does not propagate.

        Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post returns
               a 400 response that raises HTTPStatusError on raise_for_status()
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": containing "HTTP 400", "status_code": 400},
              an error is logged, and no exception propagates
        """
        client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.post.return_value = mock_response

            result = await client.send_card(card_payload)

        assert result["success"] is False
        assert "HTTP 400" in result["message"]
        assert result["status_code"] == 400

    @pytest.mark.asyncio
    async def test_UNIT_011_connect_error_logged_no_propagation(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-011:
        Webhook connection error is logged and does not propagate.

        Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post raises ConnectError
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": containing "Connection failed", "status_code": None},
              an error is logged, and no exception propagates
        """
        client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.post.side_effect = httpx.ConnectError("DNS resolution failed")

            result = await client.send_card(card_payload)

        assert result["success"] is False
        assert "Connection failed" in result["message"]
        assert result["status_code"] is None

    @pytest.mark.asyncio
    async def test_UNIT_012_unexpected_exception_caught_and_logged(self):
        """
        18-4-followup-assignment-teams-notification-UNIT-012:
        Unexpected exception is caught and logged.

        Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post raises RuntimeError
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": containing "Unexpected error: RuntimeError",
              "status_code": None}, an error is logged, and no exception propagates
        """
        client = TeamsWebhookClient(webhook_url=SAMPLE_WEBHOOK_URL)
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.post.side_effect = RuntimeError("something broke")

            result = await client.send_card(card_payload)

        assert result["success"] is False
        assert "Unexpected error: RuntimeError" in result["message"]
        assert result["status_code"] is None
