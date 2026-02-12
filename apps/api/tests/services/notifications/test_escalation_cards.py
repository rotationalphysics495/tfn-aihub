"""
Tests for Escalation Nudge Notification Card Builders & Settings (Story 18.5)

Test Coverage:
- AC#1 UNIT: build_safety_escalation_card() produces valid Adaptive Card with title, body, action button
- AC#2 UNIT: build_followup_escalation_card() produces valid Adaptive Card with title, body, action button
- AC#4 UNIT: Settings.teams_configured returns False for empty/whitespace-only webhook URL

References:
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.5]
- [Source: apps/api/app/services/notifications/escalation.py] - build_safety_escalation_card, build_followup_escalation_card
- [Source: apps/api/app/core/config.py] - Settings.teams_configured
"""

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

REPORT_DATE = date(2026, 2, 12)
BASE_URL = "https://app.example.com"


# ===========================================================================
# AC1 UNIT TESTS: build_safety_escalation_card
# ===========================================================================


class TestBuildSafetyEscalationCard:
    """AC#1: build_safety_escalation_card() produces valid Adaptive Card for safety escalation."""

    def test_UNIT_001_correct_title_and_message_body(self):
        """
        18-5-escalation-nudge-notifications-UNIT-001:
        Safety escalation card contains correct title and message body.

        Given: A safety event with asset_name="Mixer-01", hours_elapsed=3.5, severity="high",
               report_date=2026-02-12
        When: build_safety_escalation_card() is called with those parameters and
              base_url="https://app.example.com"
        Then: The returned card contains title "Escalation: Safety Alert Unacknowledged"
              and body text "Safety alert on Mixer-01 has been unacknowledged for 3.5 hours.
              Please review."
        """
        from app.services.notifications.escalation import build_safety_escalation_card

        card = build_safety_escalation_card(
            asset_name="Mixer-01",
            hours_elapsed=3.5,
            severity="high",
            report_date=REPORT_DATE,
            base_url=BASE_URL,
        )

        # Verify title
        title_block = card["body"][0]
        assert title_block["text"] == "Escalation: Safety Alert Unacknowledged"

        # Verify body text
        body_texts = [b["text"] for b in card["body"] if b["type"] == "TextBlock"]
        expected_msg = "Safety alert on Mixer-01 has been unacknowledged for 3.5 hours. Please review."
        assert any(expected_msg in t for t in body_texts)

    def test_UNIT_002_open_report_action_button_url(self):
        """
        18-5-escalation-nudge-notifications-UNIT-002:
        Safety escalation card contains Open Report action button with correct URL.

        Given: A safety event with report_date=2026-02-12 and base_url="https://app.example.com"
        When: build_safety_escalation_card() is called
        Then: The card has an actions array with one Action.OpenUrl titled "Open Report"
              pointing to "https://app.example.com/morning-report?date=2026-02-12"
        """
        from app.services.notifications.escalation import build_safety_escalation_card

        card = build_safety_escalation_card(
            asset_name="Mixer-01",
            hours_elapsed=3.5,
            severity="high",
            report_date=REPORT_DATE,
            base_url=BASE_URL,
        )

        assert len(card["actions"]) >= 1
        action = card["actions"][0]
        assert action["type"] == "Action.OpenUrl"
        assert action["title"] == "Open Report"
        assert action["url"] == "https://app.example.com/morning-report?date=2026-02-12"

    def test_UNIT_003_valid_adaptive_card_v14_structure(self):
        """
        18-5-escalation-nudge-notifications-UNIT-003:
        Safety escalation card has valid Adaptive Card v1.4 structure.

        Given: Valid input parameters for a safety escalation card
        When: build_safety_escalation_card() is called
        Then: The returned dict contains "$schema", "type"="AdaptiveCard", "version"="1.4",
              a non-empty "body" array, and a non-empty "actions" array
        """
        from app.services.notifications.escalation import build_safety_escalation_card

        card = build_safety_escalation_card(
            asset_name="Mixer-01",
            hours_elapsed=2.5,
            severity="medium",
            report_date=REPORT_DATE,
            base_url=BASE_URL,
        )

        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert isinstance(card["body"], list)
        assert len(card["body"]) > 0
        assert isinstance(card["actions"], list)
        assert len(card["actions"]) > 0

    def test_UNIT_004_includes_severity_information(self):
        """
        18-5-escalation-nudge-notifications-UNIT-004:
        Safety escalation card includes severity information.

        Given: A safety event with severity="critical"
        When: build_safety_escalation_card() is called
        Then: The card body contains the severity value "critical" in one of the TextBlock elements
        """
        from app.services.notifications.escalation import build_safety_escalation_card

        card = build_safety_escalation_card(
            asset_name="Mixer-01",
            hours_elapsed=5.0,
            severity="critical",
            report_date=REPORT_DATE,
            base_url=BASE_URL,
        )

        body_texts = [b["text"] for b in card["body"] if b.get("type") == "TextBlock"]
        all_text = " ".join(body_texts).lower()
        assert "critical" in all_text

    def test_UNIT_005_handles_trailing_slash_in_base_url(self):
        """
        18-5-escalation-nudge-notifications-UNIT-005:
        Safety escalation card handles trailing slash in base_url.

        Given: base_url="https://app.example.com/" (with trailing slash)
        When: build_safety_escalation_card() is called
        Then: The "Open Report" URL is "https://app.example.com/morning-report?date=2026-02-12"
              (no double slash)
        """
        from app.services.notifications.escalation import build_safety_escalation_card

        card = build_safety_escalation_card(
            asset_name="Mixer-01",
            hours_elapsed=3.0,
            severity="high",
            report_date=REPORT_DATE,
            base_url="https://app.example.com/",
        )

        action = card["actions"][0]
        assert action["url"] == "https://app.example.com/morning-report?date=2026-02-12"


# ===========================================================================
# AC2 UNIT TESTS: build_followup_escalation_card
# ===========================================================================


class TestBuildFollowupEscalationCard:
    """AC#2: build_followup_escalation_card() produces valid Adaptive Card for stale follow-ups."""

    def test_UNIT_006_correct_title_and_message_body(self):
        """
        18-5-escalation-nudge-notifications-UNIT-006:
        Follow-up escalation card contains correct title and message body.

        Given: A stale follow-up with asset_name="Boiler-3", assignee_name="John Doe",
               hours_since_update=36
        When: build_followup_escalation_card() is called with base_url and report_date
        Then: The returned card contains title "Escalation: Follow-Up Stale" and body text
              "Follow-up for Boiler-3 assigned to John Doe has had no update for 36 hours."
        """
        from app.services.notifications.escalation import build_followup_escalation_card

        card = build_followup_escalation_card(
            asset_name="Boiler-3",
            assignee_name="John Doe",
            hours_since_update=36,
            report_date=REPORT_DATE,
            base_url=BASE_URL,
        )

        # Verify title
        title_block = card["body"][0]
        assert title_block["text"] == "Escalation: Follow-Up Stale"

        # Verify body text
        body_texts = [b["text"] for b in card["body"] if b["type"] == "TextBlock"]
        expected_msg = "Follow-up for Boiler-3 assigned to John Doe has had no update for 36 hours."
        assert any(expected_msg in t for t in body_texts)

    def test_UNIT_007_open_report_action_button(self):
        """
        18-5-escalation-nudge-notifications-UNIT-007:
        Follow-up escalation card contains Open Report action button.

        Given: A follow-up escalation card with report_date=2026-02-10 and
               base_url="https://app.example.com"
        When: build_followup_escalation_card() is called
        Then: The card has an Action.OpenUrl titled "Open Report" with URL
              "https://app.example.com/morning-report?date=2026-02-10"
        """
        from app.services.notifications.escalation import build_followup_escalation_card

        card = build_followup_escalation_card(
            asset_name="Boiler-3",
            assignee_name="John Doe",
            hours_since_update=36,
            report_date=date(2026, 2, 10),
            base_url=BASE_URL,
        )

        assert len(card["actions"]) >= 1
        action = card["actions"][0]
        assert action["type"] == "Action.OpenUrl"
        assert action["title"] == "Open Report"
        assert action["url"] == "https://app.example.com/morning-report?date=2026-02-10"

    def test_UNIT_008_valid_adaptive_card_v14_structure(self):
        """
        18-5-escalation-nudge-notifications-UNIT-008:
        Follow-up escalation card has valid Adaptive Card v1.4 structure.

        Given: Valid input parameters for a follow-up escalation card
        When: build_followup_escalation_card() is called
        Then: The returned dict contains "$schema", "type"="AdaptiveCard", "version"="1.4",
              non-empty "body" and "actions" arrays
        """
        from app.services.notifications.escalation import build_followup_escalation_card

        card = build_followup_escalation_card(
            asset_name="Oven-2",
            assignee_name="Jane Smith",
            hours_since_update=48,
            report_date=REPORT_DATE,
            base_url=BASE_URL,
        )

        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert isinstance(card["body"], list)
        assert len(card["body"]) > 0
        assert isinstance(card["actions"], list)
        assert len(card["actions"]) > 0

    def test_UNIT_009_handles_unknown_assignee_gracefully(self):
        """
        18-5-escalation-nudge-notifications-UNIT-009:
        Follow-up escalation card handles unknown assignee gracefully.

        Given: Assignee name resolution fails and falls back to "Unknown"
        When: build_followup_escalation_card() is called with assignee_name="Unknown"
        Then: The card body text reads "Follow-up for {asset_name} assigned to Unknown
              has had no update for {hours} hours."
        """
        from app.services.notifications.escalation import build_followup_escalation_card

        card = build_followup_escalation_card(
            asset_name="Press-B",
            assignee_name="Unknown",
            hours_since_update=30,
            report_date=REPORT_DATE,
            base_url=BASE_URL,
        )

        body_texts = [b["text"] for b in card["body"] if b["type"] == "TextBlock"]
        expected_msg = "Follow-up for Press-B assigned to Unknown has had no update for 30 hours."
        assert any(expected_msg in t for t in body_texts)


# ===========================================================================
# AC4 UNIT TESTS: Settings.teams_configured
# ===========================================================================


class TestSettingsTeamsConfigured:
    """AC#4: Settings.teams_configured returns False for empty/whitespace-only webhook URL."""

    def test_UNIT_010_returns_false_for_empty_string(self):
        """
        18-5-escalation-nudge-notifications-UNIT-010:
        Settings.teams_configured returns False for empty string.

        Given: teams_webhook_url="" in Settings
        When: teams_configured property is accessed
        Then: Returns False
        """
        from app.core.config import Settings

        settings = Settings(teams_webhook_url="")
        assert settings.teams_configured is False

    def test_UNIT_011_returns_false_for_whitespace_only_string(self):
        """
        18-5-escalation-nudge-notifications-UNIT-011:
        Settings.teams_configured returns False for whitespace-only string.

        Given: teams_webhook_url="   " in Settings
        When: teams_configured property is accessed
        Then: Returns False
        """
        from app.core.config import Settings

        settings = Settings(teams_webhook_url="   ")
        assert settings.teams_configured is False
