"""
Tests for Morning Summary Teams Card Builder Functions (Story 18.3)

Test Coverage:
- AC#1: build_morning_summary_card() produces valid Adaptive Card with title, summary, bullets, button
- AC#2: build_all_clear_card() produces correct zero-action-item card
- AC#3: send_card() handles network errors, HTTP errors, and unconfigured webhook gracefully

References:
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.3]
- [Source: apps/api/app/services/notifications/teams.py] - TeamsWebhookClient
- [Source: apps/api/app/schemas/action.py] - ActionListResponse, ActionItem
"""

import pytest
from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from unittest.mock import patch, MagicMock, AsyncMock

import httpx

from app.schemas.action import (
    ActionCategory,
    ActionItem,
    ActionListResponse,
    PriorityLevel,
)
from app.services.notifications.teams import TeamsWebhookClient


# ---------------------------------------------------------------------------
# Test Data Factories
# ---------------------------------------------------------------------------

def _make_action_item(
    index: int,
    asset_name: str,
    recommendation_text: str,
    category: ActionCategory = ActionCategory.OEE,
    priority_level: PriorityLevel = PriorityLevel.MEDIUM,
) -> ActionItem:
    """Create an ActionItem with sensible defaults for testing."""
    return ActionItem(
        id=f"action-{index:03d}",
        asset_id=f"asset-{index:03d}",
        asset_name=asset_name,
        priority_level=priority_level,
        category=category,
        primary_metric_value=f"Metric {index}",
        recommendation_text=recommendation_text,
        evidence_summary=f"Evidence for action {index}",
        evidence_refs=[],
        created_at=datetime(2026, 2, 10, 6, 0, 0, tzinfo=timezone.utc),
    )


def _make_action_list_response(
    actions: List[ActionItem],
    report_date: date = date(2026, 2, 10),
    counts_by_category: Optional[Dict[str, int]] = None,
) -> ActionListResponse:
    """Create an ActionListResponse from a list of ActionItem objects."""
    if counts_by_category is None:
        counts = {"safety": 0, "oee": 0, "financial": 0}
        for a in actions:
            counts[a.category.value] = counts.get(a.category.value, 0) + 1
    else:
        counts = counts_by_category
    return ActionListResponse(
        actions=actions,
        generated_at=datetime(2026, 2, 10, 6, 15, 0, tzinfo=timezone.utc),
        report_date=report_date,
        total_count=len(actions),
        counts_by_category=counts,
    )


# Shared fixtures --------------------------------------------------------

REPORT_DATE = date(2026, 2, 10)
BASE_URL = "https://app.example.com"


@pytest.fixture
def five_action_items() -> List[ActionItem]:
    """5 action items: 1 safety, 2 OEE, 2 financial."""
    return [
        _make_action_item(1, "Grinder 5", "Safety event detected", ActionCategory.SAFETY, PriorityLevel.CRITICAL),
        _make_action_item(2, "CAMA 2400", "OEE at 72%", ActionCategory.OEE, PriorityLevel.HIGH),
        _make_action_item(3, "Rychiger 101", "$1,200 financial loss", ActionCategory.FINANCIAL, PriorityLevel.MEDIUM),
        _make_action_item(4, "Filler 300", "OEE below target", ActionCategory.OEE, PriorityLevel.MEDIUM),
        _make_action_item(5, "Wrapper 200", "$800 waste cost", ActionCategory.FINANCIAL, PriorityLevel.LOW),
    ]


@pytest.fixture
def five_item_response(five_action_items) -> ActionListResponse:
    return _make_action_list_response(
        five_action_items,
        report_date=REPORT_DATE,
        counts_by_category={"safety": 1, "oee": 2, "financial": 2},
    )


# ===========================================================================
# AC1 UNIT TESTS: build_morning_summary_card
# ===========================================================================

class TestBuildMorningSummaryCard:
    """AC#1: build_morning_summary_card() produces valid Adaptive Card JSON."""

    def test_UNIT_001_valid_adaptive_card_structure(self, five_item_response):
        """
        18-3-morning-summary-teams-card-UNIT-001:
        build_morning_summary_card produces valid Adaptive Card JSON structure.

        Given: An ActionListResponse with 5 action items (1 safety, 2 OEE, 2 financial)
        When: build_morning_summary_card(action_list, report_date, base_url) is called
        Then: The returned dict contains $schema, type, version, body (3 TextBlocks), actions (1 Action.OpenUrl)
        """
        from app.services.notifications.teams import build_morning_summary_card

        card = build_morning_summary_card(five_item_response, REPORT_DATE, BASE_URL)

        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert isinstance(card["body"], list)
        assert len(card["body"]) == 3
        for block in card["body"]:
            assert block["type"] == "TextBlock"
        assert isinstance(card["actions"], list)
        assert len(card["actions"]) == 1
        assert card["actions"][0]["type"] == "Action.OpenUrl"

    def test_UNIT_002_title_format(self, five_item_response):
        """
        18-3-morning-summary-teams-card-UNIT-002:
        Card title uses correct format "Morning Report -- {date}".

        Given: A report_date of 2026-02-10
        When: build_morning_summary_card() is called
        Then: The first TextBlock has text "Morning Report -- 2026-02-10", weight "Bolder", size "Medium"
        """
        from app.services.notifications.teams import build_morning_summary_card

        card = build_morning_summary_card(five_item_response, REPORT_DATE, BASE_URL)

        title_block = card["body"][0]
        assert title_block["text"] == "Morning Report -- 2026-02-10"
        assert title_block["weight"] == "Bolder"
        assert title_block["size"] == "Medium"

    def test_UNIT_003_summary_line_category_counts(self, five_item_response):
        """
        18-3-morning-summary-teams-card-UNIT-003:
        Summary line shows correct category counts.

        Given: ActionListResponse with total_count=5, counts_by_category={"safety": 1, "oee": 2, "financial": 2}
        When: build_morning_summary_card() is called
        Then: Second TextBlock has text "5 action items: 1 safety, 2 OEE misses, 2 financial" and wrap=true
        """
        from app.services.notifications.teams import build_morning_summary_card

        card = build_morning_summary_card(five_item_response, REPORT_DATE, BASE_URL)

        summary_block = card["body"][1]
        assert summary_block["text"] == "5 action items: 1 safety, 2 OEE misses, 2 financial"
        assert summary_block["wrap"] is True

    def test_UNIT_004_top_3_bullet_points(self, five_item_response):
        """
        18-3-morning-summary-teams-card-UNIT-004:
        Top 3 action items rendered as bullet points with asset name and headline.

        Given: 5 actions, first 3: (Grinder 5, Safety event detected), (CAMA 2400, OEE at 72%), (Rychiger 101, $1,200 financial loss)
        When: build_morning_summary_card() is called
        Then: Third TextBlock contains the 3 bullet lines and wrap=true
        """
        from app.services.notifications.teams import build_morning_summary_card

        card = build_morning_summary_card(five_item_response, REPORT_DATE, BASE_URL)

        bullets_block = card["body"][2]
        expected = (
            "- Grinder 5: Safety event detected\n"
            "- CAMA 2400: OEE at 72%\n"
            "- Rychiger 101: $1,200 financial loss"
        )
        assert bullets_block["text"] == expected
        assert bullets_block["wrap"] is True

    def test_UNIT_005_open_report_button_url(self, five_item_response):
        """
        18-3-morning-summary-teams-card-UNIT-005:
        Open Report button uses correct URL with date parameter.

        Given: base_url="https://app.example.com" and report_date=2026-02-10
        When: build_morning_summary_card() is called
        Then: actions[0] is Action.OpenUrl with title "Open Report" and correct URL
        """
        from app.services.notifications.teams import build_morning_summary_card

        card = build_morning_summary_card(five_item_response, REPORT_DATE, BASE_URL)

        action = card["actions"][0]
        assert action["type"] == "Action.OpenUrl"
        assert action["title"] == "Open Report"
        assert action["url"] == "https://app.example.com/morning-report?date=2026-02-10"

    def test_UNIT_006_exactly_3_items_no_truncation(self):
        """
        18-3-morning-summary-teams-card-UNIT-006:
        Card with exactly 3 action items shows all 3 in bullets (no truncation).

        Given: An ActionListResponse with exactly 3 action items
        When: build_morning_summary_card() is called
        Then: The bullet point TextBlock contains exactly 3 lines
        """
        from app.services.notifications.teams import build_morning_summary_card

        items = [
            _make_action_item(1, "Asset A", "Recommendation A", ActionCategory.SAFETY, PriorityLevel.CRITICAL),
            _make_action_item(2, "Asset B", "Recommendation B", ActionCategory.OEE, PriorityLevel.HIGH),
            _make_action_item(3, "Asset C", "Recommendation C", ActionCategory.FINANCIAL, PriorityLevel.MEDIUM),
        ]
        response = _make_action_list_response(items, REPORT_DATE)
        card = build_morning_summary_card(response, REPORT_DATE, BASE_URL)

        bullets_block = card["body"][2]
        lines = bullets_block["text"].split("\n")
        assert len(lines) == 3
        assert lines[0] == "- Asset A: Recommendation A"
        assert lines[1] == "- Asset B: Recommendation B"
        assert lines[2] == "- Asset C: Recommendation C"

    def test_UNIT_007_fewer_than_3_items(self):
        """
        18-3-morning-summary-teams-card-UNIT-007:
        Card with fewer than 3 action items shows only available items.

        Given: ActionListResponse with 1 action item (1 safety, 0 OEE, 0 financial)
        When: build_morning_summary_card() is called
        Then: Summary reads "1 action item: 1 safety, 0 OEE misses, 0 financial", bullet has 1 line
        """
        from app.services.notifications.teams import build_morning_summary_card

        items = [
            _make_action_item(1, "Grinder 5", "Safety event detected", ActionCategory.SAFETY, PriorityLevel.CRITICAL),
        ]
        response = _make_action_list_response(
            items, REPORT_DATE,
            counts_by_category={"safety": 1, "oee": 0, "financial": 0},
        )
        card = build_morning_summary_card(response, REPORT_DATE, BASE_URL)

        summary_block = card["body"][1]
        assert summary_block["text"] == "1 action item: 1 safety, 0 OEE misses, 0 financial"

        bullets_block = card["body"][2]
        lines = bullets_block["text"].split("\n")
        assert len(lines) == 1

    def test_UNIT_008_long_recommendation_truncated(self):
        """
        18-3-morning-summary-teams-card-UNIT-008:
        Long recommendation text is truncated in bullet points.

        Given: An ActionListResponse where the first action has recommendation_text >100 chars
        When: build_morning_summary_card() is called
        Then: The bullet text for that item is truncated to ~100 characters with "..." suffix
        """
        from app.services.notifications.teams import build_morning_summary_card

        long_text = "A" * 150
        items = [
            _make_action_item(1, "Grinder 5", long_text, ActionCategory.SAFETY, PriorityLevel.CRITICAL),
            _make_action_item(2, "CAMA 2400", "Short text", ActionCategory.OEE, PriorityLevel.HIGH),
        ]
        response = _make_action_list_response(items, REPORT_DATE)
        card = build_morning_summary_card(response, REPORT_DATE, BASE_URL)

        bullets_block = card["body"][2]
        first_line = bullets_block["text"].split("\n")[0]
        # The first bullet should have the asset name prefix plus truncated text
        # "- Grinder 5: " (14 chars) + truncated text + "..."
        assert first_line.endswith("...")
        # The recommendation portion should be roughly 100 chars (excluding "- AssetName: " prefix)
        recommendation_part = first_line.split(": ", 1)[1]
        assert len(recommendation_part) <= 104  # ~100 + "..."

    def test_UNIT_009_zero_counts_some_categories(self):
        """
        18-3-morning-summary-teams-card-UNIT-009:
        Summary line handles zero counts for some categories.

        Given: counts_by_category={"safety": 0, "oee": 3, "financial": 0}
        When: build_morning_summary_card() is called
        Then: Summary reads "3 action items: 0 safety, 3 OEE misses, 0 financial"
        """
        from app.services.notifications.teams import build_morning_summary_card

        items = [
            _make_action_item(1, "Asset A", "Below target", ActionCategory.OEE),
            _make_action_item(2, "Asset B", "Below target", ActionCategory.OEE),
            _make_action_item(3, "Asset C", "Below target", ActionCategory.OEE),
        ]
        response = _make_action_list_response(
            items, REPORT_DATE,
            counts_by_category={"safety": 0, "oee": 3, "financial": 0},
        )
        card = build_morning_summary_card(response, REPORT_DATE, BASE_URL)

        summary_block = card["body"][1]
        assert summary_block["text"] == "3 action items: 0 safety, 3 OEE misses, 0 financial"


# ===========================================================================
# AC2 UNIT TESTS: build_all_clear_card
# ===========================================================================

class TestBuildAllClearCard:
    """AC#2: build_all_clear_card() for zero-action-item days."""

    def test_UNIT_010_all_clear_message(self):
        """
        18-3-morning-summary-teams-card-UNIT-010:
        build_all_clear_card produces correct all-clear message.

        Given: report_date=2026-02-10 and base_url="https://app.example.com"
        When: build_all_clear_card(report_date, base_url) is called
        Then: Body contains TextBlock with "Morning Report -- 2026-02-10: All clear. No action items today."
        """
        from app.services.notifications.teams import build_all_clear_card

        card = build_all_clear_card(REPORT_DATE, BASE_URL)

        assert card["body"][0]["text"] == "Morning Report -- 2026-02-10: All clear. No action items today."
        assert card["body"][0]["weight"] == "Bolder"
        assert card["body"][0]["size"] == "Medium"

    def test_UNIT_011_all_clear_open_report_button(self):
        """
        18-3-morning-summary-teams-card-UNIT-011:
        All-clear card includes Open Report button.

        Given: report_date=2026-02-10 and base_url="https://app.example.com"
        When: build_all_clear_card() is called
        Then: actions[0] is Action.OpenUrl with title "Open Report" and correct URL
        """
        from app.services.notifications.teams import build_all_clear_card

        card = build_all_clear_card(REPORT_DATE, BASE_URL)

        assert len(card["actions"]) == 1
        action = card["actions"][0]
        assert action["type"] == "Action.OpenUrl"
        assert action["title"] == "Open Report"
        assert action["url"] == "https://app.example.com/morning-report?date=2026-02-10"

    def test_UNIT_012_all_clear_valid_adaptive_card_structure(self):
        """
        18-3-morning-summary-teams-card-UNIT-012:
        All-clear card has valid Adaptive Card structure.

        Given: report_date=2026-02-10 and base_url="https://app.example.com"
        When: build_all_clear_card() is called
        Then: The dict contains $schema, type AdaptiveCard, version 1.4, body array, actions array
        """
        from app.services.notifications.teams import build_all_clear_card

        card = build_all_clear_card(REPORT_DATE, BASE_URL)

        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert isinstance(card["body"], list)
        assert isinstance(card["actions"], list)


# ===========================================================================
# AC3 UNIT TESTS: send_card error handling
# ===========================================================================

class TestSendCardErrorHandling:
    """AC#3: send_card() handles network errors, HTTP errors, and unconfigured webhook."""

    @pytest.mark.asyncio
    async def test_UNIT_013_handles_timeout_exception(self):
        """
        18-3-morning-summary-teams-card-UNIT-013:
        send_card handles httpx.TimeoutException gracefully.

        Given: httpx.AsyncClient.post raises httpx.TimeoutException
        When: send_card(card_payload) is called
        Then: Returns {"success": False, ...} without raising, error is logged
        """
        client = TeamsWebhookClient(webhook_url="https://webhook.example.com/test")
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.post.side_effect = httpx.TimeoutException("Connection timed out")

            result = await client.send_card(card_payload)

        assert result["success"] is False
        assert "status_code" in result

    @pytest.mark.asyncio
    async def test_UNIT_014_handles_connect_error(self):
        """
        18-3-morning-summary-teams-card-UNIT-014:
        send_card handles httpx.ConnectError gracefully.

        Given: httpx.AsyncClient.post raises httpx.ConnectError
        When: send_card(card_payload) is called
        Then: Returns {"success": False, ...} without raising, error is logged
        """
        client = TeamsWebhookClient(webhook_url="https://webhook.example.com/test")
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.post.side_effect = httpx.ConnectError("DNS resolution failed")

            result = await client.send_card(card_payload)

        assert result["success"] is False
        assert "status_code" in result

    @pytest.mark.asyncio
    async def test_UNIT_015_handles_http_error_responses(self):
        """
        18-3-morning-summary-teams-card-UNIT-015:
        send_card handles HTTP 4xx/5xx responses gracefully.

        Given: Webhook returns HTTP 400 Bad Request
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "status_code": 400, ...} without raising
        """
        client = TeamsWebhookClient(webhook_url="https://webhook.example.com/test")
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
        assert result["status_code"] == 400

    @pytest.mark.asyncio
    async def test_UNIT_016_returns_early_when_not_configured(self):
        """
        18-3-morning-summary-teams-card-UNIT-016:
        send_card returns early when webhook not configured.

        Given: TeamsWebhookClient instantiated with empty webhook_url=""
        When: send_card(card_payload) is called
        Then: Returns {"success": False, "message": contains "not configured"} without HTTP request
        """
        client = TeamsWebhookClient(webhook_url="")
        card_payload = {"type": "AdaptiveCard", "version": "1.4", "body": []}

        with patch("app.services.notifications.teams.httpx.AsyncClient") as mock_client_cls:
            result = await client.send_card(card_payload)

            # No HTTP request should have been made
            mock_client_cls.assert_not_called()

        assert result["success"] is False
        assert "not configured" in result["message"].lower()
