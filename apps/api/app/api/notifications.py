"""
Notifications API endpoints.

Story: 18.2 - Teams Webhook Configuration
AC#2: POST /teams/test endpoint for testing webhook connectivity

References:
- [Source: apps/api/app/api/followups.py] - Authentication pattern
- [Source: apps/api/app/services/notifications/teams.py] - TeamsWebhookClient
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.models.user import CurrentUser
from app.services.notifications.teams import TeamsWebhookClient

router = APIRouter()


@router.post("/teams/test")
async def test_teams_webhook(current_user: CurrentUser = Depends(get_current_user)):
    """Test the Teams webhook configuration by sending a test Adaptive Card."""
    client = TeamsWebhookClient()
    if not client.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Teams webhook URL is not configured. Set TEAMS_WEBHOOK_URL environment variable.",
        )
    result = await client.send_test_message()
    return result
