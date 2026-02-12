"""
Notifications Services Package (Story 18.2)

Provides notification services for posting messages to external channels.

Components:
- TeamsWebhookClient: Posts Adaptive Cards to Microsoft Teams via Incoming Webhooks
"""

from app.services.notifications.teams import TeamsWebhookClient


def get_teams_client() -> TeamsWebhookClient:
    """Get a TeamsWebhookClient instance."""
    return TeamsWebhookClient()


__all__ = [
    "TeamsWebhookClient",
    "get_teams_client",
]
