"""
Integration Tests for _trigger_teams_notification and run_morning_report Teams Integration (Story 18.3)

Test Coverage:
- AC#1 INT: _trigger_teams_notification sends summary card after pipeline success
- AC#1 INT: run_morning_report calls _trigger_teams_notification after smart summary
- AC#2 INT: All-clear card path when zero action items
- AC#3 INT: Fire-and-forget error handling (teams failures don't block pipeline)

References:
- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.3]
- [Source: apps/api/app/services/pipelines/morning_report.py] - run_morning_report, _trigger_teams_notification
- [Source: apps/api/app/services/notifications/teams.py] - TeamsWebhookClient
- [Source: apps/api/app/schemas/action.py] - ActionListResponse, ActionItem
"""

import logging
import pytest
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
from unittest.mock import patch, MagicMock, AsyncMock, call

from app.models.pipeline import PipelineExecutionLog, PipelineResult, PipelineStatus
from app.schemas.action import (
    ActionCategory,
    ActionItem,
    ActionListResponse,
    PriorityLevel,
)


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


def _make_pipeline_result(status: PipelineStatus = PipelineStatus.SUCCESS) -> PipelineResult:
    """Create a PipelineResult for testing."""
    log = PipelineExecutionLog(
        pipeline_name="morning_report",
        target_date=date(2026, 2, 10),
        status=status,
        started_at=datetime(2026, 2, 10, 6, 0, 0),
    )
    log.completed_at = datetime(2026, 2, 10, 6, 10, 0)
    log.duration_seconds = 600.0
    return PipelineResult(
        status=status,
        execution_log=log,
        summaries_updated=5,
        safety_events_created=1,
    )


# Shared constants --------------------------------------------------------

TARGET_DATE = date(2026, 2, 10)


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
        report_date=TARGET_DATE,
        counts_by_category={"safety": 1, "oee": 2, "financial": 2},
    )


@pytest.fixture
def empty_action_response() -> ActionListResponse:
    return _make_action_list_response(
        [],
        report_date=TARGET_DATE,
        counts_by_category={"safety": 0, "oee": 0, "financial": 0},
    )


# ===========================================================================
# AC1 INTEGRATION TESTS: _trigger_teams_notification with action items
# ===========================================================================

class TestTriggerTeamsNotification:
    """AC#1: _trigger_teams_notification sends summary card after pipeline success."""

    @pytest.mark.asyncio
    async def test_INT_001_sends_summary_card(self, five_item_response):
        """
        18-3-morning-summary-teams-card-INT-001:
        _trigger_teams_notification sends summary card after pipeline success.

        Given: teams_configured=True, action engine returns 5 action items, TeamsWebhookClient mocked
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: send_card() is called once with an Adaptive Card payload built by build_morning_summary_card()
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(return_value=five_item_response)

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(return_value={"success": True, "message": "OK", "status_code": 200})

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://app.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
        ):
            await _trigger_teams_notification(TARGET_DATE)

        mock_teams_client.send_card.assert_called_once()
        card_payload = mock_teams_client.send_card.call_args[0][0]
        assert card_payload["type"] == "AdaptiveCard"
        assert "Morning Report -- 2026-02-10" in card_payload["body"][0]["text"]

    @pytest.mark.asyncio
    async def test_INT_002_run_morning_report_calls_trigger(self, five_item_response):
        """
        18-3-morning-summary-teams-card-INT-002:
        run_morning_report calls _trigger_teams_notification after smart summary.

        Given: Pipeline SUCCESS, smart summary succeeds, teams_configured=True
        When: run_morning_report(target_date=date(2026, 2, 10), generate_smart_summary=True) is called
        Then: _trigger_teams_notification is called after _trigger_smart_summary_generation
        """
        from app.services.pipelines.morning_report import run_morning_report

        mock_pipeline = AsyncMock()
        mock_pipeline.run = AsyncMock(return_value=_make_pipeline_result(PipelineStatus.SUCCESS))

        call_order = []

        async def mock_smart_summary(target_date):
            call_order.append("smart_summary")

        async def mock_teams_notification(target_date):
            call_order.append("teams_notification")

        with (
            patch("app.services.pipelines.morning_report.get_pipeline", return_value=mock_pipeline),
            patch(
                "app.services.pipelines.morning_report._trigger_smart_summary_generation",
                side_effect=mock_smart_summary,
            ),
            patch(
                "app.services.pipelines.morning_report._trigger_teams_notification",
                side_effect=mock_teams_notification,
            ),
        ):
            result = await run_morning_report(target_date=TARGET_DATE, generate_smart_summary=True)

        assert result.status == PipelineStatus.SUCCESS
        assert "smart_summary" in call_order
        assert "teams_notification" in call_order
        assert call_order.index("smart_summary") < call_order.index("teams_notification")

    @pytest.mark.asyncio
    async def test_INT_003_queries_action_engine_with_correct_date(self):
        """
        18-3-morning-summary-teams-card-INT-003:
        _trigger_teams_notification queries action engine with correct date.

        Given: settings.teams_configured=True
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: generate_action_list() is called with report_date=date(2026, 2, 10)
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        items = [_make_action_item(1, "Asset", "Rec", ActionCategory.SAFETY, PriorityLevel.CRITICAL)]
        response = _make_action_list_response(items, TARGET_DATE)

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(return_value=response)

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(return_value={"success": True, "message": "OK", "status_code": 200})

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://app.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
        ):
            await _trigger_teams_notification(TARGET_DATE)

        mock_engine.generate_action_list.assert_called_once()
        call_kwargs = mock_engine.generate_action_list.call_args
        # Check that report_date was passed correctly (positional or keyword)
        assert TARGET_DATE in call_kwargs.args or call_kwargs.kwargs.get("report_date") == TARGET_DATE

    @pytest.mark.asyncio
    async def test_INT_004_uses_app_base_url_from_settings(self):
        """
        18-3-morning-summary-teams-card-INT-004:
        _trigger_teams_notification uses app_base_url from settings for Open Report link.

        Given: settings.app_base_url="https://prod.example.com", teams_configured=True
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: Card actions[0] URL is "https://prod.example.com/morning-report?date=2026-02-10"
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        items = [_make_action_item(1, "Asset A", "Rec A", ActionCategory.OEE, PriorityLevel.HIGH)]
        response = _make_action_list_response(items, TARGET_DATE)

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(return_value=response)

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(return_value={"success": True, "message": "OK", "status_code": 200})

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://prod.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
        ):
            await _trigger_teams_notification(TARGET_DATE)

        mock_teams_client.send_card.assert_called_once()
        card_payload = mock_teams_client.send_card.call_args[0][0]
        open_url = card_payload["actions"][0]["url"]
        assert open_url == "https://prod.example.com/morning-report?date=2026-02-10"


# ===========================================================================
# AC2 INTEGRATION TESTS: All-clear card path
# ===========================================================================

class TestTriggerTeamsNotificationAllClear:
    """AC#2: All-clear card when zero action items."""

    @pytest.mark.asyncio
    async def test_INT_005_sends_all_clear_card_when_zero_items(self, empty_action_response):
        """
        18-3-morning-summary-teams-card-INT-005:
        _trigger_teams_notification sends all-clear card when zero action items.

        Given: teams_configured=True, action engine returns total_count=0
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: send_card() receives the all-clear card payload with "All clear. No action items today."
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(return_value=empty_action_response)

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(return_value={"success": True, "message": "OK", "status_code": 200})

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://app.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
        ):
            await _trigger_teams_notification(TARGET_DATE)

        mock_teams_client.send_card.assert_called_once()
        card_payload = mock_teams_client.send_card.call_args[0][0]
        # All-clear card should have the combined title+message
        body_text = card_payload["body"][0]["text"]
        assert "All clear" in body_text
        assert "No action items today" in body_text

    @pytest.mark.asyncio
    async def test_INT_006_run_morning_report_posts_all_clear(self, empty_action_response):
        """
        18-3-morning-summary-teams-card-INT-006:
        run_morning_report posts all-clear card when pipeline succeeds with no action items.

        Given: Pipeline SUCCESS, action engine returns 0 items, teams_configured=True
        When: run_morning_report(target_date=date(2026, 2, 10)) is called
        Then: send_card() receives all-clear card, PipelineResult with SUCCESS returned
        """
        from app.services.pipelines.morning_report import run_morning_report

        mock_pipeline = AsyncMock()
        mock_pipeline.run = AsyncMock(return_value=_make_pipeline_result(PipelineStatus.SUCCESS))

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(return_value=empty_action_response)

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(return_value={"success": True, "message": "OK", "status_code": 200})

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://app.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_pipeline", return_value=mock_pipeline),
            patch(
                "app.services.pipelines.morning_report._trigger_smart_summary_generation",
                new_callable=AsyncMock,
            ),
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
        ):
            result = await run_morning_report(target_date=TARGET_DATE)

        assert result.status == PipelineStatus.SUCCESS
        mock_teams_client.send_card.assert_called_once()
        card_payload = mock_teams_client.send_card.call_args[0][0]
        body_text = card_payload["body"][0]["text"]
        assert "All clear" in body_text


# ===========================================================================
# AC3 INTEGRATION TESTS: Fire-and-forget error handling
# ===========================================================================

class TestTriggerTeamsNotificationErrorHandling:
    """AC#3: Fire-and-forget -- failures logged, pipeline unaffected."""

    @pytest.mark.asyncio
    async def test_INT_007_skips_silently_when_not_configured(self):
        """
        18-3-morning-summary-teams-card-INT-007:
        _trigger_teams_notification skips silently when teams_configured is False.

        Given: settings.teams_configured returns False
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: No call to get_action_engine() or send_card(), returns None
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        mock_engine = AsyncMock()
        mock_teams_client = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.teams_configured = False

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine) as mock_get_engine,
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client) as mock_get_teams,
        ):
            result = await _trigger_teams_notification(TARGET_DATE)

        assert result is None
        mock_get_engine.assert_not_called()
        mock_get_teams.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_008_catches_and_logs_send_card_failure(self, five_item_response, caplog):
        """
        18-3-morning-summary-teams-card-INT-008:
        _trigger_teams_notification catches and logs send_card failure.

        Given: teams_configured=True, action engine returns items, send_card returns failure
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: Failure logged at ERROR level, function returns None (no raise)
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(return_value=five_item_response)

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(
            return_value={"success": False, "message": "Connection refused", "status_code": None}
        )

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://app.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
            caplog.at_level(logging.ERROR),
        ):
            result = await _trigger_teams_notification(TARGET_DATE)

        assert result is None
        # Verify error was logged
        assert any("error" in record.message.lower() or "fail" in record.message.lower()
                    for record in caplog.records if record.levelno >= logging.ERROR)

    @pytest.mark.asyncio
    async def test_INT_009_catches_exception_from_send_card(self, five_item_response, caplog):
        """
        18-3-morning-summary-teams-card-INT-009:
        _trigger_teams_notification catches exception from send_card if it raises.

        Given: teams_configured=True, send_card() raises RuntimeError
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: Exception caught, logged at ERROR level, function returns None
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(return_value=five_item_response)

        mock_teams_client = AsyncMock()
        mock_teams_client.send_card = AsyncMock(side_effect=RuntimeError("unexpected failure"))

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://app.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
            caplog.at_level(logging.ERROR),
        ):
            result = await _trigger_teams_notification(TARGET_DATE)

        # Must not raise -- fire and forget
        assert result is None

    @pytest.mark.asyncio
    async def test_INT_010_catches_exception_from_generate_action_list(self, caplog):
        """
        18-3-morning-summary-teams-card-INT-010:
        _trigger_teams_notification catches exception from generate_action_list.

        Given: teams_configured=True, generate_action_list() raises Exception
        When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
        Then: Exception caught, logged at ERROR, returns None, send_card() NOT called
        """
        from app.services.pipelines.morning_report import _trigger_teams_notification

        mock_engine = AsyncMock()
        mock_engine.generate_action_list = AsyncMock(side_effect=Exception("database error"))

        mock_teams_client = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.teams_configured = True
        mock_settings.app_base_url = "https://app.example.com"

        with (
            patch("app.services.pipelines.morning_report.get_settings", return_value=mock_settings),
            patch("app.services.pipelines.morning_report.get_action_engine", return_value=mock_engine),
            patch("app.services.pipelines.morning_report.get_teams_client", return_value=mock_teams_client),
            caplog.at_level(logging.ERROR),
        ):
            result = await _trigger_teams_notification(TARGET_DATE)

        assert result is None
        mock_teams_client.send_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_INT_011_run_morning_report_returns_result_when_teams_fails(self):
        """
        18-3-morning-summary-teams-card-INT-011:
        run_morning_report returns PipelineResult even when Teams notification fails.

        Given: Pipeline SUCCESS, _trigger_teams_notification raises Exception
        When: run_morning_report(target_date=date(2026, 2, 10)) is called
        Then: PipelineResult with SUCCESS returned, no exception propagates
        """
        from app.services.pipelines.morning_report import run_morning_report

        mock_pipeline = AsyncMock()
        mock_pipeline.run = AsyncMock(return_value=_make_pipeline_result(PipelineStatus.SUCCESS))

        with (
            patch("app.services.pipelines.morning_report.get_pipeline", return_value=mock_pipeline),
            patch(
                "app.services.pipelines.morning_report._trigger_smart_summary_generation",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.pipelines.morning_report._trigger_teams_notification",
                new_callable=AsyncMock,
                side_effect=Exception("catastrophic teams failure"),
            ),
        ):
            result = await run_morning_report(target_date=TARGET_DATE)

        assert result.status == PipelineStatus.SUCCESS
        assert result.summaries_updated == 5

    @pytest.mark.asyncio
    async def test_INT_012_run_morning_report_returns_partial_when_notification_fails(self):
        """
        18-3-morning-summary-teams-card-INT-012:
        run_morning_report returns PipelineResult when PARTIAL status and notification fails.

        Given: Pipeline PARTIAL, smart summary succeeds, Teams notification fails
        When: run_morning_report(target_date=date(2026, 2, 10)) is called
        Then: PipelineResult with PARTIAL status returned correctly
        """
        from app.services.pipelines.morning_report import run_morning_report

        mock_pipeline = AsyncMock()
        mock_pipeline.run = AsyncMock(return_value=_make_pipeline_result(PipelineStatus.PARTIAL))

        with (
            patch("app.services.pipelines.morning_report.get_pipeline", return_value=mock_pipeline),
            patch(
                "app.services.pipelines.morning_report._trigger_smart_summary_generation",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.pipelines.morning_report._trigger_teams_notification",
                new_callable=AsyncMock,
                side_effect=Exception("teams notification failure"),
            ),
        ):
            result = await run_morning_report(target_date=TARGET_DATE)

        assert result.status == PipelineStatus.PARTIAL
