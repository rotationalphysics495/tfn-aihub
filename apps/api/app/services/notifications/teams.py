"""
Teams Webhook Client for posting Adaptive Cards to Microsoft Teams.

Story: 18.2 - Teams Webhook Configuration
AC#2: Post test message to configured Teams channel
AC#3: Graceful degradation when webhook URL not configured

Story: 18.3 - Morning Summary Teams Card
AC#1: build_morning_summary_card() produces Adaptive Card with title, summary, bullets, button
AC#2: build_all_clear_card() produces card for zero-action-item days

References:
- [Source: docs/architecture-api.md#Technology Stack] - httpx >=0.26.0
- [Source: apps/api/app/core/config.py] - Settings.teams_webhook_url
- [Source: apps/api/app/schemas/action.py] - ActionListResponse, ActionItem
"""

import logging
from datetime import date
from typing import Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MAX_BULLET_TEXT_LEN = 100


def build_morning_summary_card(
    action_list: "ActionListResponse",
    report_date: date,
    base_url: str,
) -> dict:
    """Build an Adaptive Card for the morning summary with action items.

    Story 18.3 AC#1: Card includes title, category counts, top 3 bullets, Open Report button.
    """
    from app.schemas.action import ActionListResponse  # noqa: F811

    counts = action_list.counts_by_category
    safety_count = counts.get("safety", 0)
    oee_count = counts.get("oee", 0)
    financial_count = counts.get("financial", 0)

    item_word = "item" if action_list.total_count == 1 else "items"
    summary_text = (
        f"{action_list.total_count} action {item_word}: "
        f"{safety_count} safety, {oee_count} OEE misses, {financial_count} financial"
    )

    top_items = action_list.actions[:3]
    bullet_lines = []
    for item in top_items:
        rec = item.recommendation_text
        if len(rec) > MAX_BULLET_TEXT_LEN:
            rec = rec[:MAX_BULLET_TEXT_LEN] + "..."
        bullet_lines.append(f"- {item.asset_name}: {rec}")
    bullets_text = "\n".join(bullet_lines)

    base_url = base_url.rstrip("/")
    report_url = f"{base_url}/morning-report?date={report_date.isoformat()}"

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"Morning Report -- {report_date.isoformat()}",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": summary_text,
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": bullets_text,
                "wrap": True,
            },
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "Open Report",
                "url": report_url,
            }
        ],
    }


def build_all_clear_card(report_date: date, base_url: str) -> dict:
    """Build an Adaptive Card for the all-clear (zero action items) case.

    Story 18.3 AC#2: Card with "All clear. No action items today." and Open Report button.
    """
    base_url = base_url.rstrip("/")
    report_url = f"{base_url}/morning-report?date={report_date.isoformat()}"

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"Morning Report -- {report_date.isoformat()}: All clear. No action items today.",
                "weight": "Bolder",
                "size": "Medium",
            },
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "Open Report",
                "url": report_url,
            }
        ],
    }


def build_followup_assignment_card(followup_data: dict, base_url: str) -> dict:
    """Build an Adaptive Card for a follow-up assignment notification.

    Story 18.4 AC#1: Card includes header, FactSet with action/asset/category/assigner/note,
    and a "View in App" button linking to the morning report page.
    """
    base_url = base_url.rstrip("/")
    report_date = str(followup_data.get("report_date", ""))
    report_url = f"{base_url}/morning-report?date={report_date}"

    assigner_name = followup_data.get("assigner_name", "Someone")
    action_summary = followup_data.get("action_summary", "")
    asset_name = followup_data.get("asset_name", "")
    summary_message = f"{assigner_name} assigned you a follow-up: {action_summary} on {asset_name}"

    facts = [
        {"title": "Action:", "value": action_summary},
        {"title": "Asset:", "value": asset_name},
        {"title": "Category:", "value": followup_data.get("category", "")},
        {"title": "Assigned by:", "value": assigner_name},
    ]

    note = followup_data.get("note")
    if note:
        facts.append({"title": "Note:", "value": note})

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Follow-Up Assigned",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": summary_message,
                "wrap": True,
            },
            {
                "type": "FactSet",
                "facts": facts,
            },
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "View in App",
                "url": report_url,
            }
        ],
    }


class TeamsWebhookClient:
    """Client for posting Adaptive Cards to Microsoft Teams via Incoming Webhooks."""

    def __init__(self, webhook_url: Optional[str] = None):
        settings = get_settings()
        self.webhook_url = webhook_url or settings.teams_webhook_url
        self.timeout = 10  # seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def send_card(self, card_payload: dict) -> dict:
        """Post an Adaptive Card to Teams. Returns {"success": bool, "message": str, "status_code": int | None}."""
        if not self.is_configured:
            return {"success": False, "message": "Teams webhook URL not configured", "status_code": None}

        message = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": card_payload
            }]
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.webhook_url, json=message)
                resp.raise_for_status()
                logger.info(f"Teams webhook POST succeeded: {resp.status_code}")
                return {"success": True, "message": "Message posted to Teams", "status_code": resp.status_code}
        except httpx.TimeoutException:
            logger.error("Teams webhook POST timed out")
            return {"success": False, "message": "Request timed out", "status_code": None}
        except httpx.HTTPStatusError as e:
            logger.error(f"Teams webhook POST failed: {e.response.status_code}")
            return {"success": False, "message": f"HTTP {e.response.status_code}: {e.response.text[:200]}", "status_code": e.response.status_code}
        except httpx.ConnectError as e:
            logger.error(f"Teams webhook connection failed: {e}")
            return {"success": False, "message": f"Connection failed: {str(e)[:200]}", "status_code": None}
        except Exception as e:
            logger.error(f"Teams webhook unexpected error: {e}")
            return {"success": False, "message": f"Unexpected error: {type(e).__name__}", "status_code": None}

    async def send_test_message(self) -> dict:
        """Send a test Adaptive Card to verify webhook connectivity."""
        test_card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {"type": "TextBlock", "text": "TFN AI Hub - Connection Test", "weight": "Bolder", "size": "Medium"},
                {"type": "TextBlock", "text": "Teams webhook integration is working correctly.", "wrap": True}
            ]
        }
        return await self.send_card(test_card)
