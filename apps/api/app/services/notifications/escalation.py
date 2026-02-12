"""
Escalation Nudge Notifications Service (Story 18.5)

Checks for unacknowledged safety events and stale follow-ups,
sending Teams notifications to prompt action. Runs as a periodic
background task via the APScheduler.

AC#1: Safety item unacknowledged 2+ hours → Teams nudge with link
AC#2: Follow-up in "assigned" status 24+ hours → Teams nudge
AC#3: Recently updated follow-up → no nudge (DB query filter)
AC#4: Teams not configured → skip with INFO log
AC#5: Rate limiting — max once per 4 hours per item via escalation_nudge_log

References:
- [Source: apps/api/app/services/notifications/teams.py] - TeamsWebhookClient, card builders
- [Source: apps/api/app/core/config.py] - Settings.teams_configured
- [Source: supabase/migrations/0036_escalation_nudge_log.sql] - escalation_nudge_log table
"""

import logging
from datetime import date, datetime, timedelta, timezone

from supabase import create_client

from app.core.config import get_settings
from app.services.notifications.teams import TeamsWebhookClient

logger = logging.getLogger(__name__)


def get_teams_client() -> TeamsWebhookClient:
    """Get a TeamsWebhookClient instance."""
    return TeamsWebhookClient()


# ---------------------------------------------------------------------------
# Card Builders (pure functions returning Adaptive Card v1.4 dicts)
# ---------------------------------------------------------------------------


def build_safety_escalation_card(
    asset_name: str,
    hours_elapsed: float,
    severity: str,
    report_date: date,
    base_url: str,
) -> dict:
    """Build an Adaptive Card for an unacknowledged safety event escalation.

    Story 18.5 AC#1: Card includes title, message body with asset name and hours,
    severity info, and an "Open Report" action button.
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
                "text": "Escalation: Safety Alert Unacknowledged",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": (
                    f"Safety alert on {asset_name} has been unacknowledged "
                    f"for {hours_elapsed} hours. Please review."
                ),
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": f"Severity: {severity}",
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


def build_followup_escalation_card(
    asset_name: str,
    assignee_name: str,
    hours_since_update: int,
    report_date: date,
    base_url: str,
) -> dict:
    """Build an Adaptive Card for a stale follow-up escalation.

    Story 18.5 AC#2: Card includes title, message body with asset name,
    assignee name, hours since update, and an "Open Report" action button.
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
                "text": "Escalation: Follow-Up Stale",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": (
                    f"Follow-up for {asset_name} assigned to {assignee_name} "
                    f"has had no update for {hours_since_update} hours."
                ),
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


# ---------------------------------------------------------------------------
# Database Query Helpers
# ---------------------------------------------------------------------------


async def check_unacknowledged_safety_items(supabase_client, settings) -> list:
    """Query safety_events for items unacknowledged beyond the threshold.

    Returns list of dicts with id, asset_name, severity, status, created_at.
    Story 18.5: uses created_at as proxy for "on the report" time.
    AC#1: status != 'resolved' AND created_at < cutoff (2+ hours old).
    """
    threshold_hours = settings.escalation_safety_threshold_hours
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=threshold_hours)).isoformat()

    try:
        response = (
            supabase_client.table("safety_events")
            .select("id,asset_name,severity,status,created_at")
            .neq("status", "resolved")
            .lt("created_at", cutoff)
            .execute()
        )
        data = response.data
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


async def check_stale_followups(supabase_client, settings) -> list:
    """Query action_followups for items stale beyond the threshold.

    Returns list of dicts with id, asset_name, assigned_to, assignee_name,
    status, updated_at.
    AC#2: status = 'assigned' AND updated_at < cutoff (24+ hours old).
    AC#3: Recently updated follow-ups are excluded by the updated_at filter.
    """
    threshold_hours = settings.escalation_followup_threshold_hours
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=threshold_hours)).isoformat()

    try:
        response = (
            supabase_client.table("action_followups")
            .select("id,asset_name,assigned_to,assignee_name,status,updated_at")
            .eq("status", "assigned")
            .lt("updated_at", cutoff)
            .execute()
        )
        data = response.data
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Rate Limiting Helpers
# ---------------------------------------------------------------------------


async def _was_recently_nudged(
    supabase_client,
    item_type: str,
    item_id: str,
    cooldown_hours: int = 4,
) -> bool:
    """Check if a nudge was sent for this item within the cooldown window.

    Queries escalation_nudge_log for any entry within the last cooldown_hours.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=cooldown_hours)).isoformat()

    try:
        response = (
            supabase_client.table("escalation_nudge_log")
            .select("id")
            .eq("item_type", item_type)
            .eq("item_id", item_id)
            .gte("nudge_sent_at", cutoff)
            .limit(1)
            .execute()
        )
        data = response.data
        if isinstance(data, list):
            return len(data) > 0
        return False
    except Exception as e:
        logger.error(f"Failed to check nudge log for {item_type}:{item_id}: {e}")
        return False


async def _record_nudge(
    supabase_client,
    item_type: str,
    item_id: str,
) -> None:
    """Record that a nudge was sent for this item.

    Inserts a row into escalation_nudge_log for rate-limit tracking.
    """
    supabase_client.table("escalation_nudge_log").insert({
        "item_type": item_type,
        "item_id": item_id,
        "channel": "teams",
    }).execute()


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------


async def run_escalation_check() -> None:
    """Run the escalation check cycle. Fire-and-forget — never raises.

    Story 18.5 AC#4: If Teams is not configured, logs INFO and returns.
    Story 18.5 AC#1-3: Checks safety events and stale follow-ups.
    Story 18.5 AC#5: Applies per-item rate limiting via escalation_nudge_log.
    """
    try:
        settings = get_settings()

        # AC#4: Early return if Teams is not configured
        if not settings.teams_configured:
            logger.info("Teams webhook not configured, skipping escalation check")
            return

        # Create Supabase service-role client for database access
        supabase = create_client(settings.supabase_url, settings.supabase_key)

        teams_client = get_teams_client()
        now = datetime.now(timezone.utc)
        today = date.today()
        base_url = settings.app_base_url

        # AC#1: Check unacknowledged safety events (filtered by helper)
        safety_items = await check_unacknowledged_safety_items(supabase, settings)

        for item in safety_items:
            item_id = str(item.get("id", ""))
            try:
                # AC#5: Rate limiting
                if await _was_recently_nudged(
                    supabase, "safety_event", item_id,
                    cooldown_hours=settings.escalation_cooldown_hours,
                ):
                    logger.info(f"Skipping safety escalation for {item_id} (rate-limited)")
                    continue

                # Build and send card
                created_at_str = item.get("created_at", "")
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    hours_elapsed = round((now - created_at).total_seconds() / 3600, 1)
                except (ValueError, AttributeError):
                    hours_elapsed = settings.escalation_safety_threshold_hours

                card = build_safety_escalation_card(
                    asset_name=item.get("asset_name", "Unknown"),
                    hours_elapsed=hours_elapsed,
                    severity=item.get("severity", "unknown"),
                    report_date=today,
                    base_url=base_url,
                )

                result = await teams_client.send_card(card)
                if result.get("success"):
                    logger.info(f"Sent safety escalation for {item_id}")
                else:
                    logger.warning(
                        f"Failed to send safety escalation for {item_id}: "
                        f"{result.get('message', 'unknown error')}"
                    )

                # Record nudge (after send, so notification is delivered even if record fails)
                try:
                    await _record_nudge(supabase, "safety_event", item_id)
                except Exception as e:
                    logger.error(f"Failed to record nudge for safety_event:{item_id}: {e}")

            except Exception as e:
                logger.error(f"Error processing safety escalation for {item_id}: {e}")
                continue

        # AC#2: Check stale follow-ups (filtered by helper)
        stale_followups = await check_stale_followups(supabase, settings)

        for item in stale_followups:
            item_id = str(item.get("id", ""))
            try:
                # AC#5: Rate limiting
                if await _was_recently_nudged(
                    supabase, "followup", item_id,
                    cooldown_hours=settings.escalation_cooldown_hours,
                ):
                    logger.info(f"Skipping followup escalation for {item_id} (rate-limited)")
                    continue

                # Calculate hours since update
                updated_at_str = item.get("updated_at", "")
                try:
                    updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                    hours_since_update = int((now - updated_at).total_seconds() / 3600)
                except (ValueError, AttributeError):
                    hours_since_update = settings.escalation_followup_threshold_hours

                # Resolve assignee name
                assignee_name = item.get("assignee_name", "Unknown")

                card = build_followup_escalation_card(
                    asset_name=item.get("asset_name", "Unknown"),
                    assignee_name=assignee_name,
                    hours_since_update=hours_since_update,
                    report_date=today,
                    base_url=base_url,
                )

                result = await teams_client.send_card(card)
                if result.get("success"):
                    logger.info(f"Sent followup escalation for {item_id}")
                else:
                    logger.warning(
                        f"Failed to send followup escalation for {item_id}: "
                        f"{result.get('message', 'unknown error')}"
                    )

                # Record nudge
                try:
                    await _record_nudge(supabase, "followup", item_id)
                except Exception as e:
                    logger.error(f"Failed to record nudge for followup:{item_id}: {e}")

            except Exception as e:
                logger.error(f"Error processing followup escalation for {item_id}: {e}")
                continue

    except Exception as e:
        logger.error(f"Escalation check failed: {e}")
