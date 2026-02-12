"""
Teams Webhook Client for posting Adaptive Cards to Microsoft Teams.

Story: 18.2 - Teams Webhook Configuration
AC#2: Post test message to configured Teams channel
AC#3: Graceful degradation when webhook URL not configured

References:
- [Source: docs/architecture-api.md#Technology Stack] - httpx >=0.26.0
- [Source: apps/api/app/core/config.py] - Settings.teams_webhook_url
"""

import logging
from typing import Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


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
