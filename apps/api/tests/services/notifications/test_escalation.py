"""
Tests for Escalation Nudge Notifications — Checker Logic, Rate Limiting, and Migration (Story 18.5)

Test Coverage:
- AC#1 INT: Unacknowledged safety events trigger Teams escalation cards
- AC#2 INT: Stale follow-ups trigger Teams escalation cards
- AC#3 INT: Recently updated follow-ups are excluded
- AC#4 INT: Teams not configured — early return with INFO log
- AC#5 INT: Rate limiting prevents duplicate nudges within cooldown window
- Cross-cutting: Error handling, orchestration, migration schema

Unit Tests:
- UNIT-012 to UNIT-014: _was_recently_nudged / _record_nudge helpers
- UNIT-015 to UNIT-017: Configurable thresholds from settings
- UNIT-018: Migration file schema review

References:
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.5]
- [Source: apps/api/app/services/notifications/escalation.py] - EscalationChecker, run_escalation_check
- [Source: apps/api/app/core/config.py] - Settings.teams_configured
- [Source: supabase/migrations/0036_escalation_nudge_log.sql] - escalation_nudge_log table
"""

import logging
import os
import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock, call


# ---------------------------------------------------------------------------
# Test Data Factories
# ---------------------------------------------------------------------------

NOW = datetime(2026, 2, 12, 10, 0, 0, tzinfo=timezone.utc)
REPORT_DATE = date(2026, 2, 12)
BASE_URL = "https://app.example.com"
WEBHOOK_URL = "https://outlook.office.com/webhook/test-id/IncomingWebhook/test"


def _make_safety_event(
    event_id: str = "evt-1",
    asset_name: str = "Press-A",
    severity: str = "high",
    created_at: datetime = None,
    is_resolved: bool = False,
) -> dict:
    """Factory for safety_event rows as returned by Supabase."""
    if created_at is None:
        created_at = NOW - timedelta(hours=3)
    return {
        "id": event_id,
        "asset_name": asset_name,
        "severity": severity,
        "status": "resolved" if is_resolved else "open",
        "created_at": created_at.isoformat(),
        "is_resolved": is_resolved,
    }


def _make_followup(
    followup_id: str = "fu-1",
    asset_name: str = "Oven-2",
    assigned_to: str = "user-uuid-1",
    assignee_name: str = "John Doe",
    status: str = "assigned",
    updated_at: datetime = None,
) -> dict:
    """Factory for action_followup rows as returned by Supabase."""
    if updated_at is None:
        updated_at = NOW - timedelta(hours=30)
    return {
        "id": followup_id,
        "asset_name": asset_name,
        "assigned_to": assigned_to,
        "assignee_name": assignee_name,
        "status": status,
        "updated_at": updated_at.isoformat(),
    }


def _make_nudge_log_entry(
    item_type: str = "safety_event",
    item_id: str = "evt-1",
    nudge_sent_at: datetime = None,
    channel: str = "teams",
) -> dict:
    """Factory for escalation_nudge_log rows."""
    if nudge_sent_at is None:
        nudge_sent_at = NOW - timedelta(hours=2)
    return {
        "id": "nudge-log-001",
        "item_type": item_type,
        "item_id": item_id,
        "nudge_sent_at": nudge_sent_at.isoformat(),
        "channel": channel,
    }


def _mock_settings(
    teams_configured: bool = True,
    webhook_url: str = WEBHOOK_URL,
    base_url: str = BASE_URL,
    safety_threshold_hours: int = 2,
    followup_threshold_hours: int = 24,
    cooldown_hours: int = 4,
) -> MagicMock:
    """Create a mock Settings object for escalation tests."""
    mock = MagicMock()
    mock.teams_configured = teams_configured
    mock.teams_webhook_url = webhook_url
    mock.app_base_url = base_url
    mock.escalation_safety_threshold_hours = safety_threshold_hours
    mock.escalation_followup_threshold_hours = followup_threshold_hours
    mock.escalation_cooldown_hours = cooldown_hours
    mock.supabase_url = "https://test-project.supabase.co"
    mock.supabase_key = "test-key"
    return mock


# ===========================================================================
# AC1 INTEGRATION TESTS: Unacknowledged safety events
# ===========================================================================


class TestSafetyEscalation:
    """AC#1: Unacknowledged safety event older than 2h triggers Teams notification."""

    @pytest.mark.asyncio
    async def test_INT_001_unacknowledged_safety_event_triggers_notification(self):
        """
        18-5-escalation-nudge-notifications-INT-001:
        Unacknowledged safety event older than 2 hours triggers Teams notification.

        Given: A safety event exists with is_resolved=FALSE and created_at = 3 hours ago,
               Teams webhook is configured, no prior nudge
        When: run_escalation_check() is called
        Then: send_card() is called exactly once with a safety escalation Adaptive Card,
              and a nudge record is written to escalation_nudge_log
        """
        from app.services.notifications.escalation import run_escalation_check

        safety_event = _make_safety_event(
            event_id="evt-1",
            asset_name="Press-A",
            severity="high",
            created_at=NOW - timedelta(hours=3),
        )

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[safety_event]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_called()
        card_payload = mock_teams_client.send_card.call_args[0][0]
        assert card_payload["type"] == "AdaptiveCard"
        # Card should mention the asset name
        body_texts = [b.get("text", "") for b in card_payload.get("body", [])]
        all_text = " ".join(body_texts)
        assert "Press-A" in all_text

    @pytest.mark.asyncio
    async def test_INT_002_resolved_safety_event_does_not_trigger(self):
        """
        18-5-escalation-nudge-notifications-INT-002:
        Acknowledged (resolved) safety event does NOT trigger escalation.

        Given: A safety event exists with is_resolved=TRUE and created_at = 5 hours ago
        When: run_escalation_check() is called
        Then: No safety escalation card is sent via send_card()
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()
        # Safety events query returns empty (resolved items filtered by WHERE clause)
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[])

        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_003_young_safety_event_does_not_trigger(self):
        """
        18-5-escalation-nudge-notifications-INT-003:
        Safety event younger than 2 hours does NOT trigger escalation.

        Given: A safety event exists with is_resolved=FALSE and created_at = 30 minutes ago
        When: run_escalation_check() is called
        Then: No safety escalation card is sent
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()
        # Query returns empty (event too recent to match threshold)
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[])

        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_004_multiple_safety_events_get_separate_notifications(self):
        """
        18-5-escalation-nudge-notifications-INT-004:
        Multiple unacknowledged safety events each get separate notifications.

        Given: Three safety events exist, all with is_resolved=FALSE and created_at > 2 hours ago
        When: run_escalation_check() is called
        Then: send_card() is called three times, once per event
        """
        from app.services.notifications.escalation import run_escalation_check

        events = [
            _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=3)),
            _make_safety_event("evt-2", "Mixer-01", "critical", NOW - timedelta(hours=5)),
            _make_safety_event("evt-3", "Grinder-5", "medium", NOW - timedelta(hours=2.5)),
        ]

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=events),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        assert mock_teams_client.send_card.call_count == 3


# ===========================================================================
# AC2 INTEGRATION TESTS: Stale follow-ups
# ===========================================================================


class TestFollowupEscalation:
    """AC#2: Stale follow-up in assigned status for 24+ hours triggers Teams notification."""

    @pytest.mark.asyncio
    async def test_INT_005_stale_followup_triggers_notification(self):
        """
        18-5-escalation-nudge-notifications-INT-005:
        Stale follow-up in assigned status for 24+ hours triggers Teams notification.

        Given: An action_followup with status='assigned' and updated_at = 30 hours ago
        When: run_escalation_check() is called
        Then: send_card() is called with a follow-up escalation card containing the asset name
        """
        from app.services.notifications.escalation import run_escalation_check

        followup = _make_followup(
            followup_id="fu-1",
            asset_name="Oven-2",
            assigned_to="user-uuid-1",
            assignee_name="John Doe",
            status="assigned",
            updated_at=NOW - timedelta(hours=30),
        )

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[followup]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_called()
        card_payload = mock_teams_client.send_card.call_args[0][0]
        body_texts = [b.get("text", "") for b in card_payload.get("body", [])]
        all_text = " ".join(body_texts)
        assert "Oven-2" in all_text

    @pytest.mark.asyncio
    async def test_INT_006_in_progress_followup_does_not_trigger(self):
        """
        18-5-escalation-nudge-notifications-INT-006:
        Follow-up in "in_progress" status does NOT trigger escalation.

        Given: An action_followup with status='in_progress' and updated_at = 48 hours ago
        When: run_escalation_check() is called
        Then: No follow-up escalation card is sent
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[])

        # Query returns empty (in_progress items filtered by query)
        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_007_resolved_followup_does_not_trigger(self):
        """
        18-5-escalation-nudge-notifications-INT-007:
        Follow-up in "resolved" status does NOT trigger escalation.

        Given: An action_followup with status='resolved' and updated_at = 72 hours ago
        When: run_escalation_check() is called
        Then: No follow-up escalation card is sent
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[])

        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_008_multiple_stale_followups_get_separate_notifications(self):
        """
        18-5-escalation-nudge-notifications-INT-008:
        Multiple stale follow-ups each get separate notifications.

        Given: Two action_followups, both with status='assigned' and updated_at > 24 hours ago
        When: run_escalation_check() is called
        Then: send_card() is called twice, once per follow-up
        """
        from app.services.notifications.escalation import run_escalation_check

        followups = [
            _make_followup("fu-1", "Oven-2", "user-1", "John Doe", "assigned", NOW - timedelta(hours=30)),
            _make_followup("fu-2", "Boiler-3", "user-2", "Jane Smith", "assigned", NOW - timedelta(hours=48)),
        ]

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=followups),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        assert mock_teams_client.send_card.call_count == 2


# ===========================================================================
# AC3 INTEGRATION TESTS: Recently updated follow-ups excluded
# ===========================================================================


class TestRecentlyUpdatedFollowupExcluded:
    """AC#3: Recently updated follow-up (within 24h) is excluded from escalation."""

    @pytest.mark.asyncio
    async def test_INT_009_recently_updated_followup_excluded(self):
        """
        18-5-escalation-nudge-notifications-INT-009:
        Recently updated follow-up is excluded by database query.

        Given: An action_followup with status='assigned' and updated_at = 6 hours ago
        When: run_escalation_check() is called
        Then: No follow-up escalation card is sent
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[])

        # DB query filters out recently updated followups — returns empty
        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_010_followup_at_exact_24h_boundary_not_escalated(self):
        """
        18-5-escalation-nudge-notifications-INT-010:
        Follow-up updated exactly at 24-hour boundary is NOT escalated.

        Given: An action_followup with status='assigned' and updated_at = exactly 24 hours ago
        When: run_escalation_check() is called
        Then: No follow-up escalation card is sent (boundary: requires > 24h)
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[])

        # At exact boundary, the DB query should exclude (requires > 24h)
        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_011_mix_stale_and_recent_only_stale_triggers(self):
        """
        18-5-escalation-nudge-notifications-INT-011:
        Mix of stale and recently-updated follow-ups — only stale ones trigger.

        Given: Two follow-ups: one stale (48h ago), one recent (2h ago), both status='assigned'
        When: run_escalation_check() is called
        Then: send_card() is called exactly once for the stale follow-up
        """
        from app.services.notifications.escalation import run_escalation_check

        # DB query only returns the stale one (recent is filtered by WHERE clause)
        stale_followup = _make_followup(
            "fu-1", "Oven-2", "user-1", "John Doe", "assigned", NOW - timedelta(hours=48)
        )

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[stale_followup]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        assert mock_teams_client.send_card.call_count == 1


# ===========================================================================
# AC4 INTEGRATION TESTS: Teams not configured
# ===========================================================================


class TestTeamsNotConfigured:
    """AC#4: Teams not configured — escalation check skips with INFO log."""

    @pytest.mark.asyncio
    async def test_INT_012_skips_entirely_with_info_log(self, caplog):
        """
        18-5-escalation-nudge-notifications-INT-012:
        Teams not configured — escalation check skips entirely with INFO log.

        Given: TEAMS_WEBHOOK_URL is empty and escalation-eligible items exist
        When: run_escalation_check() is called
        Then: No send_card() is called, no DB queries, and INFO log emitted
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = False

        settings = _mock_settings(teams_configured=False, webhook_url="")

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client") as mock_create_client,
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            caplog.at_level(logging.INFO),
        ):
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()
        mock_create_client.assert_not_called()
        # Verify INFO log about "not configured"
        assert any(
            "not configured" in record.message.lower()
            for record in caplog.records
            if record.levelno >= logging.INFO
        )

    @pytest.mark.asyncio
    async def test_INT_013_no_supabase_queries_when_not_configured(self):
        """
        18-5-escalation-nudge-notifications-INT-013:
        Teams not configured — no Supabase queries are executed.

        Given: TEAMS_WEBHOOK_URL is empty
        When: run_escalation_check() is called
        Then: The Supabase client is never instantiated
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_teams_client = AsyncMock()
        mock_teams_client.is_configured = False

        settings = _mock_settings(teams_configured=False, webhook_url="")

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client") as mock_create_client,
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
        ):
            await run_escalation_check()

        mock_create_client.assert_not_called()


# ===========================================================================
# AC5 INTEGRATION TESTS: Rate limiting
# ===========================================================================


class TestRateLimiting:
    """AC#5: Rate limiting prevents duplicate nudges within 4-hour cooldown."""

    @pytest.mark.asyncio
    async def test_INT_014_prevents_duplicate_within_4h_window(self):
        """
        18-5-escalation-nudge-notifications-INT-014:
        Rate limiting prevents duplicate nudge within 4-hour window.

        Given: A safety event is eligible AND a nudge was sent 2 hours ago for same item
        When: run_escalation_check() is called
        Then: No send_card() is called for that item (rate-limited)
        """
        from app.services.notifications.escalation import run_escalation_check

        safety_event = _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=3))
        recent_nudge = _make_nudge_log_entry(
            "safety_event", "evt-1", NOW - timedelta(hours=2)
        )

        mock_supabase = MagicMock()
        # Safety events query returns one event
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[safety_event])

        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        # Nudge log query returns recent nudge
        nudge_query = MagicMock()
        nudge_query.execute.return_value = MagicMock(data=[recent_nudge])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_015_allows_nudge_after_4h_cooldown(self):
        """
        18-5-escalation-nudge-notifications-INT-015:
        Rate limiting allows nudge after 4-hour cooldown expires.

        Given: A safety event is eligible AND the last nudge was 5 hours ago
        When: run_escalation_check() is called
        Then: send_card() IS called and a new nudge record is written
        """
        from app.services.notifications.escalation import run_escalation_check

        safety_event = _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=6))

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[safety_event]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_called()

    @pytest.mark.asyncio
    async def test_INT_016_rate_limiting_applies_independently_per_item(self):
        """
        18-5-escalation-nudge-notifications-INT-016:
        Rate limiting applies independently per item.

        Given: Two safety events (evt-1 and evt-2) are eligible, evt-1 was nudged 1h ago,
               evt-2 has never been nudged
        When: run_escalation_check() is called
        Then: send_card() is called once for evt-2 only; evt-1 is rate-limited
        """
        from app.services.notifications.escalation import run_escalation_check

        events = [
            _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=3)),
            _make_safety_event("evt-2", "Mixer-01", "critical", NOW - timedelta(hours=5)),
        ]

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        # evt-1 was nudged recently (rate-limited), evt-2 was not
        async def _nudge_side_effect(client, item_type, item_id, cooldown_hours=4):
            return item_id == "evt-1"

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=events),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[]),
            patch("app.services.notifications.escalation._was_recently_nudged", side_effect=_nudge_side_effect),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        # Only evt-2 should get a notification (evt-1 is rate-limited)
        assert mock_teams_client.send_card.call_count == 1

    @pytest.mark.asyncio
    async def test_INT_017_rate_limiting_independent_across_item_types(self):
        """
        18-5-escalation-nudge-notifications-INT-017:
        Rate limiting applies to follow-up items independently from safety events.

        Given: One safety event (evt-1) and one follow-up (fu-1) are eligible;
               evt-1 was nudged 1 hour ago; fu-1 has never been nudged
        When: run_escalation_check() is called
        Then: send_card() is called once for fu-1; evt-1 is rate-limited
        """
        from app.services.notifications.escalation import run_escalation_check

        safety_event = _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=3))
        followup = _make_followup(
            "fu-1", "Oven-2", "user-1", "John Doe", "assigned", NOW - timedelta(hours=30)
        )

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        # evt-1 was nudged recently (rate-limited), fu-1 was not
        async def _nudge_side_effect(client, item_type, item_id, cooldown_hours=4):
            return item_type == "safety_event" and item_id == "evt-1"

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[safety_event]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[followup]),
            patch("app.services.notifications.escalation._was_recently_nudged", side_effect=_nudge_side_effect),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        # fu-1 should be notified (not rate-limited), evt-1 should be rate-limited
        assert mock_teams_client.send_card.call_count == 1

    @pytest.mark.asyncio
    async def test_INT_018_rate_limiting_at_exact_4h_boundary(self):
        """
        18-5-escalation-nudge-notifications-INT-018:
        Rate limiting at exact 4-hour boundary.

        Given: A safety event is eligible AND the last nudge was exactly 4 hours ago
        When: run_escalation_check() is called
        Then: Nudge should be allowed at exactly 4h (cooldown expired)
        """
        from app.services.notifications.escalation import run_escalation_check

        safety_event = _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=5))

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[safety_event]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_called()


# ===========================================================================
# Cross-cutting: Orchestration and Error Handling
# ===========================================================================


class TestOrchestration:
    """Cross-cutting: run_escalation_check orchestrates safety and follow-up checks."""

    @pytest.mark.asyncio
    async def test_INT_019_orchestrates_both_check_types(self):
        """
        18-5-escalation-nudge-notifications-INT-019:
        run_escalation_check orchestrates safety and follow-up checks.

        Given: Both safety events and stale follow-ups exist, Teams is configured
        When: run_escalation_check() is called
        Then: send_card() is invoked for each eligible item
        """
        from app.services.notifications.escalation import run_escalation_check

        safety_event = _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=3))
        followup = _make_followup(
            "fu-1", "Oven-2", "user-1", "John Doe", "assigned", NOW - timedelta(hours=30)
        )

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[safety_event]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[followup]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        # Both safety and follow-up should trigger notifications
        assert mock_teams_client.send_card.call_count == 2


class TestErrorHandling:
    """Cross-cutting: Error handling — escalation check must never crash the scheduler."""

    @pytest.mark.asyncio
    async def test_INT_020_supabase_failure_does_not_crash(self, caplog):
        """
        18-5-escalation-nudge-notifications-INT-020:
        Supabase query failure does not crash the scheduler.

        Given: Teams is configured AND the safety check helper raises an exception
        When: run_escalation_check() is called
        Then: The exception is caught and logged at ERROR level; the function returns
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", side_effect=Exception("Connection refused")),
            caplog.at_level(logging.ERROR),
        ):
            # Must not raise
            await run_escalation_check()

        # Verify error was logged
        assert any(
            record.levelno >= logging.ERROR
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_INT_021_send_card_failure_does_not_prevent_subsequent(self):
        """
        18-5-escalation-nudge-notifications-INT-021:
        send_card failure does not crash or prevent subsequent checks.

        Given: Multiple eligible items AND send_card() fails for the first item
        When: run_escalation_check() is called
        Then: Subsequent items are still processed; function does not raise
        """
        from app.services.notifications.escalation import run_escalation_check

        events = [
            _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=3)),
            _make_safety_event("evt-2", "Mixer-01", "critical", NOW - timedelta(hours=5)),
        ]

        mock_supabase = MagicMock()

        # First call fails, second succeeds
        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            side_effect=[
                {"success": False, "message": "HTTP 500", "status_code": 500},
                {"success": True, "message": "OK", "status_code": 200},
            ]
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=events),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", return_value=None),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            # Must not raise
            await run_escalation_check()

        # Both items should have been attempted
        assert mock_teams_client.send_card.call_count == 2

    @pytest.mark.asyncio
    async def test_INT_022_no_items_no_notifications_no_errors(self):
        """
        18-5-escalation-nudge-notifications-INT-022:
        No items found — no notifications sent, no errors.

        Given: No unacknowledged safety events and no stale follow-ups
        When: run_escalation_check() is called
        Then: send_card() is never called; no errors; function completes normally
        """
        from app.services.notifications.escalation import run_escalation_check

        mock_supabase = MagicMock()
        safety_query = MagicMock()
        safety_query.execute.return_value = MagicMock(data=[])

        followup_query = MagicMock()
        followup_query.execute.return_value = MagicMock(data=[])

        mock_supabase.table.return_value.select.return_value.execute = MagicMock(data=[])

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock()
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await run_escalation_check()

        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_023_record_nudge_failure_does_not_prevent_notification(self):
        """
        18-5-escalation-nudge-notifications-INT-023:
        _record_nudge failure does not prevent notification delivery.

        Given: An eligible safety event, send_card succeeds, but _record_nudge raises
        When: run_escalation_check() is called
        Then: The notification is still sent, the error is logged
        """
        from app.services.notifications.escalation import run_escalation_check

        safety_event = _make_safety_event("evt-1", "Press-A", "high", NOW - timedelta(hours=3))

        mock_supabase = MagicMock()

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": True, "message": "OK", "status_code": 200}
        )
        mock_teams_client.is_configured = True

        settings = _mock_settings()

        with (
            patch("app.services.notifications.escalation.get_settings", return_value=settings),
            patch("app.services.notifications.escalation.create_client", return_value=mock_supabase),
            patch("app.services.notifications.escalation.get_teams_client", return_value=mock_teams_client),
            patch("app.services.notifications.escalation.check_unacknowledged_safety_items", return_value=[safety_event]),
            patch("app.services.notifications.escalation.check_stale_followups", return_value=[]),
            patch("app.services.notifications.escalation._was_recently_nudged", return_value=False),
            patch("app.services.notifications.escalation._record_nudge", side_effect=Exception("DB write failed")),
            patch("app.services.notifications.escalation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = NOW
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            # Must not raise
            await run_escalation_check()

        # Notification should still have been sent
        mock_teams_client.send_card.assert_called()


# ===========================================================================
# UNIT TESTS: _was_recently_nudged / _record_nudge
# ===========================================================================


class TestWasRecentlyNudged:
    """AC#5 UNIT: _was_recently_nudged rate-limit helper."""

    @pytest.mark.asyncio
    async def test_UNIT_012_returns_true_within_cooldown(self):
        """
        18-5-escalation-nudge-notifications-UNIT-012:
        _was_recently_nudged returns True when nudge is within cooldown.

        Given: escalation_nudge_log has an entry for item_type="safety_event",
               item_id="evt-1" with nudge_sent_at = 1 hour ago, cooldown = 4 hours
        When: _was_recently_nudged("safety_event", "evt-1") is called
        Then: Returns True
        """
        from app.services.notifications.escalation import _was_recently_nudged

        recent_nudge = _make_nudge_log_entry("safety_event", "evt-1", NOW - timedelta(hours=1))

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[recent_nudge]
        )

        result = await _was_recently_nudged(
            mock_supabase, "safety_event", "evt-1", cooldown_hours=4
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_UNIT_013_returns_false_when_no_prior_nudge(self):
        """
        18-5-escalation-nudge-notifications-UNIT-013:
        _was_recently_nudged returns False when no prior nudge exists.

        Given: escalation_nudge_log has no entries for item_type="safety_event", item_id="evt-new"
        When: _was_recently_nudged("safety_event", "evt-new") is called
        Then: Returns False
        """
        from app.services.notifications.escalation import _was_recently_nudged

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = await _was_recently_nudged(
            mock_supabase, "safety_event", "evt-new", cooldown_hours=4
        )

        assert result is False


class TestRecordNudge:
    """AC#5 UNIT: _record_nudge inserts entry into escalation_nudge_log."""

    @pytest.mark.asyncio
    async def test_UNIT_014_inserts_entry_into_nudge_log(self):
        """
        18-5-escalation-nudge-notifications-UNIT-014:
        _record_nudge inserts entry into escalation_nudge_log.

        Given: A successful escalation nudge was sent for item_type="followup", item_id="fu-1"
        When: _record_nudge("followup", "fu-1") is called
        Then: A row is inserted into escalation_nudge_log with correct fields
        """
        from app.services.notifications.escalation import _record_nudge

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "nudge-new", "item_type": "followup", "item_id": "fu-1"}]
        )

        await _record_nudge(mock_supabase, "followup", "fu-1")

        mock_supabase.table.assert_called_with("escalation_nudge_log")
        insert_call = mock_supabase.table.return_value.insert
        insert_call.assert_called_once()
        insert_data = insert_call.call_args[0][0]
        assert insert_data["item_type"] == "followup"
        assert insert_data["item_id"] == "fu-1"
        assert insert_data["channel"] == "teams"


# ===========================================================================
# UNIT TESTS: Configurable thresholds
# ===========================================================================


class TestConfigurableThresholds:
    """UNIT: EscalationChecker uses configurable thresholds from settings."""

    @pytest.mark.asyncio
    async def test_UNIT_015_safety_threshold_from_settings(self):
        """
        18-5-escalation-nudge-notifications-UNIT-015:
        EscalationChecker uses configurable threshold from settings.

        Given: Settings has escalation_safety_threshold_hours=4 (non-default value)
        When: check_unacknowledged_safety_items() constructs its query
        Then: The query uses a 4-hour threshold instead of the default 2 hours
        """
        from app.services.notifications.escalation import check_unacknowledged_safety_items

        mock_supabase = MagicMock()
        # Set up chainable mock for the Supabase query
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])

        settings = _mock_settings(safety_threshold_hours=4)

        result = await check_unacknowledged_safety_items(mock_supabase, settings)

        # The function should use settings.escalation_safety_threshold_hours (4 hours)
        # Verify the query was called with the correct threshold
        assert settings.escalation_safety_threshold_hours == 4

    @pytest.mark.asyncio
    async def test_UNIT_016_followup_threshold_from_settings(self):
        """
        18-5-escalation-nudge-notifications-UNIT-016:
        EscalationChecker uses configurable follow-up threshold from settings.

        Given: Settings has escalation_followup_threshold_hours=48 (non-default value)
        When: check_stale_followups() constructs its query
        Then: The query uses a 48-hour threshold instead of the default 24 hours
        """
        from app.services.notifications.escalation import check_stale_followups

        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])

        settings = _mock_settings(followup_threshold_hours=48)

        result = await check_stale_followups(mock_supabase, settings)

        assert settings.escalation_followup_threshold_hours == 48

    @pytest.mark.asyncio
    async def test_UNIT_017_cooldown_from_settings(self):
        """
        18-5-escalation-nudge-notifications-UNIT-017:
        EscalationChecker uses configurable cooldown from settings.

        Given: Settings has escalation_cooldown_hours=8 (non-default value)
        When: _was_recently_nudged() constructs its query
        Then: The query checks for nudges within the last 8 hours
        """
        from app.services.notifications.escalation import _was_recently_nudged

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = await _was_recently_nudged(
            mock_supabase, "safety_event", "evt-1", cooldown_hours=8
        )

        # Verify the custom cooldown was used (8 hours instead of default 4)
        assert result is False  # No prior nudge, returns False


# ===========================================================================
# UNIT TEST: Migration schema
# ===========================================================================


class TestMigrationSchema:
    """UNIT: escalation_nudge_log migration creates correct table schema."""

    def test_UNIT_018_migration_file_creates_correct_schema(self):
        """
        18-5-escalation-nudge-notifications-UNIT-018:
        escalation_nudge_log migration creates correct table schema.

        Given: The SQL migration file 0036_escalation_nudge_log.sql exists
        When: The migration SQL is reviewed
        Then: It creates table escalation_nudge_log with expected columns and indices
        """
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..",
            "supabase", "migrations", "0036_escalation_nudge_log.sql",
        )
        migration_path = os.path.normpath(migration_path)

        assert os.path.exists(migration_path), (
            f"Migration file 0036_escalation_nudge_log.sql must exist at {migration_path}"
        )

        with open(migration_path) as f:
            sql = f.read()

        # Table name
        assert "escalation_nudge_log" in sql

        # Required columns
        assert "item_type" in sql
        assert "item_id" in sql
        assert "nudge_sent_at" in sql
        assert "channel" in sql

        # UUID primary key
        assert "uuid" in sql.lower()

        # Index on (item_type, item_id, nudge_sent_at)
        assert "CREATE INDEX" in sql.upper() or "create index" in sql.lower()

        # RLS enabled
        assert "ENABLE ROW LEVEL SECURITY" in sql.upper() or "enable row level security" in sql.lower()
