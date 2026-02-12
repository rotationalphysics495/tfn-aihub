"""
Notifications Services Package (Story 18.2, 18.3)

Provides notification services for posting messages to external channels.

Components:
- TeamsWebhookClient: Posts Adaptive Cards to Microsoft Teams via Incoming Webhooks
- build_morning_summary_card: Builds Adaptive Card for morning summary with action items
- build_all_clear_card: Builds Adaptive Card for zero-action-item days
"""

from app.services.notifications.teams import (
    TeamsWebhookClient,
    build_all_clear_card,
    build_followup_assignment_card,
    build_morning_summary_card,
)


def get_teams_client() -> TeamsWebhookClient:
    """Get a TeamsWebhookClient instance."""
    return TeamsWebhookClient()


__all__ = [
    "TeamsWebhookClient",
    "build_all_clear_card",
    "build_followup_assignment_card",
    "build_morning_summary_card",
    "get_teams_client",
]
