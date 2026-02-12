"""
Tests for Story 16.6: AI Summary with Action Plan Context

Test-first development: these tests define the expected behavior for
action plan context features added to the Smart Summary generation pipeline.

Story: 16.6 - AI Summary with Action Plan Context
AC: #1 - Active action plan mention in summary
AC: #2 - Recently verified plan correlation
AC: #3 - Context builder fetches action plans
AC: #4 - Prompt template updated
AC: #5 - Fallback summary includes action plan badges
AC: #6 - No action plan data graceful handling
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai.smart_summary import (
    SmartSummaryService,
    SmartSummary,
)
from app.services.ai.context_builder import (
    ContextBuilder,
    SummaryContext,
)
from app.services.ai.prompts import (
    format_action_plans,
    render_data_prompt,
    get_system_prompt,
    SYSTEM_PROMPT_DEFAULT,
)


# =============================================================================
# Fixtures
# =============================================================================

TARGET_DATE = date(2026, 2, 12)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    return MagicMock()


@pytest.fixture
def sample_action_plans():
    """Sample active action plans."""
    return [
        {
            "id": "plan-1",
            "title": "Bearing replacement on Grinder 5",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "category": "oee",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2026-02-14",
            "corrective_action": "Replace worn bearings",
            "root_cause": "Bearing wear from extended operation",
        },
        {
            "id": "plan-2",
            "title": "Calibration review for Mill 3",
            "asset_id": "asset-2",
            "asset_name": "Mill 3",
            "category": "quality",
            "status": "open",
            "priority": "medium",
            "due_date": "2026-02-18",
            "corrective_action": "Recalibrate measurement systems",
            "root_cause": "Drift in measurement calibration",
        },
    ]


@pytest.fixture
def sample_recently_verified_plans():
    """Sample recently verified action plans."""
    return [
        {
            "id": "plan-3",
            "title": "Motor replacement on CAMA 2400",
            "asset_id": "asset-3",
            "asset_name": "CAMA 2400",
            "corrective_action": "Replaced main drive motor",
            "verified_at": "2026-02-10T14:00:00Z",
            "completed_at": "2026-02-09T10:00:00Z",
            "status": "verified",
        },
    ]


@pytest.fixture
def sample_daily_summaries():
    """Sample daily summaries with below-target OEE."""
    return [
        {
            "id": "sum-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "report_date": "2026-02-12",
            "oee_percentage": 72.5,
            "actual_output": 850,
            "target_output": 1000,
            "financial_loss_dollars": 2500.00,
            "downtime_minutes": 45,
            "waste_count": 15,
        },
        {
            "id": "sum-2",
            "asset_id": "asset-2",
            "asset_name": "Mill 3",
            "report_date": "2026-02-12",
            "oee_percentage": 88.0,
            "actual_output": 950,
            "target_output": 1000,
            "financial_loss_dollars": 500.00,
            "downtime_minutes": 10,
            "waste_count": 5,
        },
    ]


@pytest.fixture
def sample_safety_events():
    """Sample safety events."""
    return [
        {
            "id": "safety-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "event_timestamp": "2026-02-12T10:30:00Z",
            "duration_minutes": 15,
            "reason_code": "Emergency Stop",
            "severity": "critical",
            "description": "Operator triggered e-stop",
            "is_resolved": False,
        },
    ]


@pytest.fixture
def sample_action_items():
    """Sample action items from Action Engine."""
    return [
        {
            "id": "action-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "category": "oee",
            "priority_level": "high",
            "primary_metric_value": "OEE: 72.5%",
            "recommendation_text": "Review performance on Grinder 5",
            "evidence_summary": "OEE 12.5% below target",
            "financial_impact_usd": 2500.00,
        },
    ]


@pytest.fixture
def context_with_action_plans(
    sample_daily_summaries,
    sample_safety_events,
    sample_action_items,
    sample_action_plans,
    sample_recently_verified_plans,
):
    """SummaryContext with action plan data populated."""
    return SummaryContext(
        target_date=TARGET_DATE,
        daily_summaries=sample_daily_summaries,
        safety_events=sample_safety_events,
        action_items=sample_action_items,
        assets={
            "asset-1": {"name": "Grinder 5"},
            "asset-2": {"name": "Mill 3"},
            "asset-3": {"name": "CAMA 2400"},
        },
        target_oee=85.0,
        action_plans=sample_action_plans,
        recently_verified_plans=sample_recently_verified_plans,
    )


@pytest.fixture
def context_without_action_plans(
    sample_daily_summaries,
    sample_safety_events,
    sample_action_items,
):
    """SummaryContext with no action plan data."""
    return SummaryContext(
        target_date=TARGET_DATE,
        daily_summaries=sample_daily_summaries,
        safety_events=sample_safety_events,
        action_items=sample_action_items,
        assets={
            "asset-1": {"name": "Grinder 5"},
            "asset-2": {"name": "Mill 3"},
        },
        target_oee=85.0,
        action_plans=[],
        recently_verified_plans=[],
    )


# =============================================================================
# AC#3: Context Builder Fetches Action Plans
# =============================================================================

class TestSummaryContextActionPlanFields:
    """Tests for action plan fields on SummaryContext (AC#3)."""

    def test_action_plans_defaults_to_empty(self):
        """16-6-UNIT-001: SummaryContext action_plans field defaults to empty list."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[],
        )
        assert context.action_plans == []

    def test_recently_verified_plans_defaults_to_empty(self):
        """16-6-UNIT-002: SummaryContext recently_verified_plans field defaults to empty list."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[],
        )
        assert context.recently_verified_plans == []

    def test_action_plans_populated(self, sample_action_plans):
        """16-6-UNIT-003: SummaryContext stores action_plans when provided."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[],
            action_plans=sample_action_plans,
        )
        assert len(context.action_plans) == 2
        assert context.action_plans[0]["title"] == "Bearing replacement on Grinder 5"

    def test_recently_verified_plans_populated(self, sample_recently_verified_plans):
        """16-6-UNIT-004: SummaryContext stores recently_verified_plans when provided."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[],
            recently_verified_plans=sample_recently_verified_plans,
        )
        assert len(context.recently_verified_plans) == 1
        assert context.recently_verified_plans[0]["title"] == "Motor replacement on CAMA 2400"


class TestFetchActiveActionPlans:
    """Tests for fetch_active_action_plans() on ContextBuilder (AC#3)."""

    @pytest.mark.asyncio
    async def test_returns_active_plans_for_matching_asset_ids(
        self, mock_supabase_client
    ):
        """16-6-UNIT-005: fetch_active_action_plans returns active plans for matching asset_ids."""
        active_data = [
            {"id": "plan-1", "title": "Fix bearing", "asset_id": "asset-1",
             "status": "in_progress", "due_date": "2026-02-14"},
        ]
        verified_data = [
            {"id": "plan-3", "title": "Motor replacement", "asset_id": "asset-1",
             "status": "verified", "verified_at": "2026-02-10T14:00:00Z"},
        ]

        # Mock the chain for active plans
        mock_active_chain = MagicMock()
        mock_active_chain.execute.return_value = MagicMock(data=active_data)

        mock_verified_chain = MagicMock()
        mock_verified_chain.execute.return_value = MagicMock(data=verified_data)

        call_count = [0]

        def mock_in_(field, values):
            """Track calls to in_ method."""
            result = MagicMock()
            if field == "status" and "open" in values:
                result.execute.return_value = MagicMock(data=active_data)
                return result
            elif field == "status" and values == ["verified"]:
                # This is actually .eq(), not .in_()
                pass
            # Return chained mock
            result.in_ = mock_in_
            result.eq = lambda f, v: MagicMock(
                gte=lambda f2, v2: MagicMock(
                    execute=MagicMock(return_value=MagicMock(data=verified_data))
                )
            )
            return result

        mock_supabase_client.table.return_value.select.return_value.in_ = mock_in_

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        active, verified = await builder.fetch_active_action_plans(
            target_date=TARGET_DATE,
            asset_ids=["asset-1"],
        )

        assert len(active) >= 1
        assert active[0]["title"] == "Fix bearing"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_asset_ids(self, mock_supabase_client):
        """16-6-UNIT-006: fetch_active_action_plans returns empty when no asset_ids provided."""
        builder = ContextBuilder(supabase_client=mock_supabase_client)
        active, verified = await builder.fetch_active_action_plans(
            target_date=TARGET_DATE,
            asset_ids=[],
        )
        assert active == []
        assert verified == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self, mock_supabase_client):
        """16-6-UNIT-007: fetch_active_action_plans returns empty lists on exception (AC#6)."""
        mock_supabase_client.table.side_effect = Exception(
            "relation \"action_plans\" does not exist"
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        active, verified = await builder.fetch_active_action_plans(
            target_date=TARGET_DATE,
            asset_ids=["asset-1"],
        )

        assert active == []
        assert verified == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_generic_error(self, mock_supabase_client):
        """16-6-UNIT-008: fetch_active_action_plans returns empty on generic error (AC#6)."""
        mock_supabase_client.table.side_effect = Exception("connection timeout")

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        active, verified = await builder.fetch_active_action_plans(
            target_date=TARGET_DATE,
            asset_ids=["asset-1", "asset-2"],
        )

        assert active == []
        assert verified == []


class TestBuildContextActionPlans:
    """Tests for build_context populating action plan fields (AC#3)."""

    @pytest.mark.asyncio
    async def test_build_context_populates_action_plans(self, mock_supabase_client):
        """16-6-UNIT-009: build_context populates action_plans when data exists."""
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 78.0, "asset_id": "asset-1", "report_date": "2026-02-12",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        active_plans = [
            {"id": "plan-1", "title": "Fix bearing", "asset_id": "asset-1",
             "status": "in_progress", "due_date": "2026-02-14"},
        ]
        verified_plans = [
            {"id": "plan-3", "title": "Motor replacement", "asset_id": "asset-1",
             "status": "verified", "verified_at": "2026-02-10"},
        ]

        with patch.object(builder, 'fetch_action_items', new_callable=AsyncMock,
                         return_value=[{"asset_id": "asset-1"}]), \
             patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock, return_value=None), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_active_action_plans', new_callable=AsyncMock,
                         return_value=(active_plans, verified_plans)), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        assert len(context.action_plans) == 1
        assert context.action_plans[0]["title"] == "Fix bearing"
        assert len(context.recently_verified_plans) == 1
        assert context.recently_verified_plans[0]["title"] == "Motor replacement"

    @pytest.mark.asyncio
    async def test_build_context_action_plans_enriched_with_asset_names(
        self, mock_supabase_client
    ):
        """16-6-UNIT-010: build_context enriches action plans with asset names."""
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 78.0, "asset_id": "asset-1", "report_date": "2026-02-12",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "asset-1", "name": "Grinder 5"}]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        active_plans = [
            {"id": "plan-1", "title": "Fix bearing", "asset_id": "asset-1"},
        ]

        with patch.object(builder, 'fetch_action_items', new_callable=AsyncMock,
                         return_value=[{"asset_id": "asset-1"}]), \
             patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock, return_value=None), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_active_action_plans', new_callable=AsyncMock,
                         return_value=(active_plans, [])), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        assert len(context.action_plans) == 1
        assert context.action_plans[0]["asset_name"] == "Grinder 5"

    @pytest.mark.asyncio
    async def test_build_context_action_plans_failure_isolated(
        self, mock_supabase_client
    ):
        """16-6-UNIT-011: build_context succeeds even when action plans fetch fails (AC#6)."""
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 78.0, "asset_id": "asset-1", "report_date": "2026-02-12",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        with patch.object(builder, 'fetch_action_items', new_callable=AsyncMock,
                         return_value=[{"asset_id": "asset-1"}]), \
             patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock, return_value=None), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_active_action_plans', new_callable=AsyncMock,
                         side_effect=Exception("action_plans table missing")), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        # Context should still be valid
        assert context.target_date == TARGET_DATE
        assert context.action_plans == []
        assert context.recently_verified_plans == []


# =============================================================================
# AC#4: Prompt Template Updated
# =============================================================================

class TestFormatActionPlans:
    """Tests for format_action_plans() in prompts.py (AC#4)."""

    def test_format_active_plans(self, sample_action_plans):
        """16-6-UNIT-012: format_action_plans formats active plans correctly."""
        result = format_action_plans(action_plans=sample_action_plans)

        assert "Active action plans" in result
        assert "Grinder 5" in result
        assert "Bearing replacement on Grinder 5" in result
        assert "in_progress" in result
        assert "due 2026-02-14" in result
        assert "Mill 3" in result
        assert "Calibration review" in result

    def test_format_verified_plans(self, sample_recently_verified_plans):
        """16-6-UNIT-013: format_action_plans formats verified plans correctly."""
        result = format_action_plans(
            recently_verified_plans=sample_recently_verified_plans
        )

        assert "Recently completed action plans" in result
        assert "CAMA 2400" in result
        assert "Motor replacement" in result
        assert "Replaced main drive motor" in result

    def test_format_both_active_and_verified(
        self, sample_action_plans, sample_recently_verified_plans
    ):
        """16-6-UNIT-014: format_action_plans includes both active and verified sections."""
        result = format_action_plans(
            action_plans=sample_action_plans,
            recently_verified_plans=sample_recently_verified_plans,
        )

        assert "Active action plans" in result
        assert "Recently completed action plans" in result
        assert "Grinder 5" in result
        assert "CAMA 2400" in result

    def test_format_empty_returns_no_plans_message(self):
        """16-6-UNIT-015: format_action_plans returns 'no plans' message when both empty."""
        result = format_action_plans(action_plans=[], recently_verified_plans=[])
        assert "No active action plans" in result

    def test_format_none_returns_no_plans_message(self):
        """16-6-UNIT-016: format_action_plans handles None inputs gracefully."""
        result = format_action_plans()
        assert "No active action plans" in result


class TestRenderDataPromptActionPlans:
    """Tests for render_data_prompt with action plan data (AC#4)."""

    def test_includes_action_plan_section_when_plans_exist(
        self, sample_action_plans
    ):
        """16-6-UNIT-017: render_data_prompt includes ACTION PLAN STATUS section when plans exist."""
        result = render_data_prompt(
            target_date=TARGET_DATE,
            safety_events=[],
            daily_summaries=[],
            action_items=[],
            action_plans=sample_action_plans,
        )

        assert "ACTION PLAN STATUS" in result
        assert "Bearing replacement" in result
        assert "Grinder 5" in result

    def test_includes_action_plan_section_when_no_plans(self):
        """16-6-UNIT-018: render_data_prompt includes graceful 'no plans' text when empty."""
        result = render_data_prompt(
            target_date=TARGET_DATE,
            safety_events=[],
            daily_summaries=[],
            action_items=[],
            action_plans=[],
            recently_verified_plans=[],
        )

        assert "ACTION PLAN STATUS" in result
        assert "No active action plans" in result

    def test_backward_compatible_without_action_plan_args(self):
        """16-6-UNIT-019: render_data_prompt works without action plan kwargs (backward compatible)."""
        result = render_data_prompt(
            target_date=TARGET_DATE,
            safety_events=[],
            daily_summaries=[],
            action_items=[],
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain ACTION PLAN STATUS section with graceful message
        assert "ACTION PLAN STATUS" in result


class TestSystemPromptActionPlans:
    """Tests for system prompt containing action plan instructions (AC#1, AC#2)."""

    def test_system_prompt_includes_action_plan_instructions(self):
        """16-6-UNIT-020: SYSTEM_PROMPT_DEFAULT includes action plan context instructions."""
        prompt = get_system_prompt()

        # Should contain instructions about action plans
        assert "action plan" in prompt.lower()

    def test_system_prompt_includes_active_plan_mention_instruction(self):
        """16-6-UNIT-021: SYSTEM_PROMPT_DEFAULT includes instruction to mention active plans."""
        assert "active action plan" in SYSTEM_PROMPT_DEFAULT.lower()
        assert "in progress" in SYSTEM_PROMPT_DEFAULT.lower()

    def test_system_prompt_includes_verified_plan_correlation_instruction(self):
        """16-6-UNIT-022: SYSTEM_PROMPT_DEFAULT includes instruction to correlate verified plans."""
        assert "recently verified" in SYSTEM_PROMPT_DEFAULT.lower() or \
               "verified action plan" in SYSTEM_PROMPT_DEFAULT.lower()


# =============================================================================
# AC#5: Fallback Summary Includes Action Plan Badges
# =============================================================================

class TestFallbackSummaryActionPlans:
    """Tests for fallback summary including action plan notes (AC#5)."""

    def test_fallback_includes_action_plan_note_for_below_target_asset(
        self, context_with_action_plans
    ):
        """16-6-UNIT-023: Fallback summary includes action plan note for below-target assets."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_with_action_plans)

        # Grinder 5 is below target and has an active plan
        assert "Action plan:" in summary.summary_text
        assert "Bearing replacement" in summary.summary_text

    def test_fallback_includes_due_date_in_action_plan_note(
        self, context_with_action_plans
    ):
        """16-6-UNIT-024: Fallback action plan note includes due date."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_with_action_plans)

        assert "due 2026-02-14" in summary.summary_text

    def test_fallback_no_action_plan_note_for_on_target_asset(
        self, context_with_action_plans
    ):
        """16-6-UNIT-025: Fallback does not add action plan note for on-target assets."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_with_action_plans)

        # Mill 3 is above target (88%), so its plan shouldn't appear in productivity
        text = summary.summary_text
        # The calibration plan for Mill 3 should not appear since Mill 3 is not below target
        productivity_section = text.split("**Productivity**")[-1] if "**Productivity**" in text else ""
        assert "Calibration review" not in productivity_section

    def test_fallback_without_action_plans_unchanged(
        self, context_without_action_plans
    ):
        """16-6-UNIT-026: Fallback summary without action plans is unchanged from baseline."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_without_action_plans)

        assert "Action plan:" not in summary.summary_text

    def test_fallback_still_includes_standard_sections(
        self, context_with_action_plans
    ):
        """16-6-UNIT-027: Fallback with action plans still includes standard sections."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_with_action_plans)

        text = summary.summary_text
        assert "**Safety**" in text
        assert "**Productivity**" in text
        assert summary.is_fallback is True
        assert summary.model_used == "fallback_template"


# =============================================================================
# AC#6: No Action Plan Data Graceful Handling
# =============================================================================

class TestGracefulHandling:
    """Tests for graceful handling when no action plans exist (AC#6)."""

    def test_summary_generates_normally_without_action_plans(
        self, context_without_action_plans
    ):
        """16-6-UNIT-028: Summary generates normally without action plan references."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_without_action_plans)

        assert summary.summary_text is not None
        assert len(summary.summary_text) > 0
        assert "Action plan:" not in summary.summary_text

    def test_format_action_plans_empty_is_graceful(self):
        """16-6-UNIT-029: format_action_plans produces graceful message for empty data."""
        result = format_action_plans(action_plans=[], recently_verified_plans=[])
        assert "No active action plans" in result
        assert isinstance(result, str)

    def test_render_data_prompt_with_no_plans_is_valid(self):
        """16-6-UNIT-030: render_data_prompt with no action plans produces valid prompt."""
        result = render_data_prompt(
            target_date=TARGET_DATE,
            safety_events=[],
            daily_summaries=[],
            action_items=[],
        )

        assert isinstance(result, str)
        assert "ACTION PLAN STATUS" in result
        assert "No active action plans" in result

    @pytest.mark.asyncio
    async def test_context_builder_handles_missing_table_gracefully(
        self, mock_supabase_client
    ):
        """16-6-UNIT-031: ContextBuilder handles missing action_plans table gracefully."""
        mock_supabase_client.table.side_effect = Exception(
            "relation \"action_plans\" does not exist"
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        active, verified = await builder.fetch_active_action_plans(
            target_date=TARGET_DATE,
            asset_ids=["asset-1"],
        )

        assert active == []
        assert verified == []


# =============================================================================
# AC#1 & AC#2: LLM Integration Tests
# =============================================================================

class TestGenerateWithLLMActionPlans:
    """Tests for _generate_with_llm passing action plan data (AC#1, AC#2)."""

    @pytest.mark.asyncio
    async def test_generate_with_llm_passes_action_plans(
        self, sample_action_plans, sample_recently_verified_plans
    ):
        """16-6-INT-001: _generate_with_llm passes action plan data from context to render_data_prompt."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[{"oee_percentage": 80.0, "asset_id": "a1", "asset_name": "Test"}],
            safety_events=[],
            action_items=[],
            action_plans=sample_action_plans,
            recently_verified_plans=sample_recently_verified_plans,
        )

        service = SmartSummaryService()

        mock_response = MagicMock()
        mock_response.content = "Test summary with action plan context"
        mock_response.response_metadata = {
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }

        with patch('app.services.ai.smart_summary.render_data_prompt') as mock_render, \
             patch('app.services.ai.smart_summary.get_system_prompt', return_value="system"), \
             patch('app.services.ai.smart_summary.get_llm_config') as mock_config, \
             patch('app.services.ai.smart_summary.get_llm_client') as mock_client, \
             patch('app.services.ai.smart_summary.estimate_tokens', return_value=100):

            mock_render.return_value = "rendered prompt"
            config_mock = MagicMock()
            config_mock.provider = "openai"
            config_mock.get_model_name.return_value = "gpt-4"
            config_mock.is_configured = True
            mock_config.return_value = config_mock

            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_llm

            await service._generate_with_llm(context)

            # Verify render_data_prompt was called with action plans
            mock_render.assert_called_once()
            call_kwargs = mock_render.call_args.kwargs
            assert call_kwargs.get("action_plans") == sample_action_plans
            assert call_kwargs.get("recently_verified_plans") == sample_recently_verified_plans


# =============================================================================
# Integration Tests
# =============================================================================

class TestSmartSummaryActionPlanIntegration:
    """Integration tests for end-to-end action plan context in summary generation."""

    @pytest.mark.asyncio
    async def test_e2e_summary_includes_action_plan_in_prompt(
        self, mock_supabase_client, sample_action_plans
    ):
        """16-6-E2E-001: End-to-end summary generation includes action plan data in LLM prompt."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 72.5, "asset_id": "asset-1", "asset_name": "Grinder 5",
                 "financial_loss_dollars": 2500, "downtime_minutes": 45, "waste_count": 15,
                 "actual_output": 850, "target_output": 1000},
            ],
            safety_events=[],
            action_items=[],
            assets={"asset-1": {"name": "Grinder 5"}},
            target_oee=85.0,
            action_plans=sample_action_plans,
            recently_verified_plans=[],
        )

        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_context_builder.build_context = AsyncMock(return_value=context)

        # Capture what prompt was sent to LLM
        captured_prompts = []

        mock_response = MagicMock()
        mock_response.content = (
            "Grinder 5 OEE is still below target — note that a corrective action plan "
            "is in progress (bearing replacement, due Friday). "
            "[Asset: Grinder 5, OEE: 72.5%]"
        )
        mock_response.response_metadata = {
            "usage": {"prompt_tokens": 500, "completion_tokens": 200}
        }

        async def capture_ainvoke(messages):
            for msg in messages:
                captured_prompts.append(msg.content)
            return mock_response

        # Mock cache miss + storage
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(
            supabase_client=mock_supabase_client,
            context_builder=mock_context_builder,
        )

        with patch('app.services.ai.smart_summary.get_llm_config') as mock_config:
            config_mock = MagicMock()
            config_mock.provider = "openai"
            config_mock.get_model_name.return_value = "gpt-4"
            config_mock.is_configured = True
            config_mock.token_usage_alert_threshold = 100000
            mock_config.return_value = config_mock

            with patch('app.services.ai.smart_summary.get_llm_client') as mock_client:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=capture_ainvoke)
                mock_client.return_value = mock_llm

                summary = await service.generate_smart_summary(target_date=TARGET_DATE)

        assert summary.is_fallback is False
        assert len(summary.summary_text) > 0

        # The data prompt should contain action plan section
        data_prompt = captured_prompts[-1] if captured_prompts else ""
        assert "ACTION PLAN STATUS" in data_prompt
        assert "Bearing replacement" in data_prompt

    @pytest.mark.asyncio
    async def test_e2e_summary_without_action_plans_succeeds(
        self, mock_supabase_client
    ):
        """16-6-E2E-002: Full summary generation succeeds with no action plan data."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 80.0, "asset_id": "a1", "asset_name": "Test Asset",
                 "financial_loss_dollars": 500, "downtime_minutes": 15, "waste_count": 3,
                 "actual_output": 900, "target_output": 1000},
            ],
            safety_events=[],
            action_items=[],
            assets={"a1": {"name": "Test Asset"}},
            target_oee=85.0,
            action_plans=[],
            recently_verified_plans=[],
        )

        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_context_builder.build_context = AsyncMock(return_value=context)

        mock_response = MagicMock()
        mock_response.content = "Production data summary without action plans."
        mock_response.response_metadata = {
            "usage": {"prompt_tokens": 300, "completion_tokens": 100}
        }

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(
            supabase_client=mock_supabase_client,
            context_builder=mock_context_builder,
        )

        with patch('app.services.ai.smart_summary.get_llm_config') as mock_config:
            config_mock = MagicMock()
            config_mock.provider = "openai"
            config_mock.get_model_name.return_value = "gpt-4"
            config_mock.is_configured = True
            config_mock.token_usage_alert_threshold = 100000
            mock_config.return_value = config_mock

            with patch('app.services.ai.smart_summary.get_llm_client') as mock_client:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_llm

                summary = await service.generate_smart_summary(target_date=TARGET_DATE)

        assert summary.is_fallback is False
        assert len(summary.summary_text) > 0

    @pytest.mark.asyncio
    async def test_e2e_fallback_with_action_plans(
        self, mock_supabase_client, sample_action_plans
    ):
        """16-6-E2E-003: Fallback summary generation includes action plan notes when LLM fails."""
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 72.5, "asset_id": "asset-1", "asset_name": "Grinder 5",
                 "financial_loss_dollars": 2500, "downtime_minutes": 45, "waste_count": 15,
                 "actual_output": 850, "target_output": 1000},
            ],
            safety_events=[],
            action_items=[],
            assets={"asset-1": {"name": "Grinder 5"}},
            target_oee=85.0,
            action_plans=sample_action_plans,
            recently_verified_plans=[],
        )

        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_context_builder.build_context = AsyncMock(return_value=context)

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(
            supabase_client=mock_supabase_client,
            context_builder=mock_context_builder,
        )

        with patch('app.services.ai.smart_summary.get_llm_config') as mock_config:
            mock_config.return_value = MagicMock(
                provider="openai",
                get_model_name=lambda: "gpt-4",
                is_configured=True,
            )
            with patch('app.services.ai.smart_summary.get_llm_client') as mock_client:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
                mock_client.return_value = mock_llm

                summary = await service.generate_smart_summary(
                    target_date=TARGET_DATE
                )

        assert summary.is_fallback is True
        assert "Action plan:" in summary.summary_text
        assert "Bearing replacement" in summary.summary_text
