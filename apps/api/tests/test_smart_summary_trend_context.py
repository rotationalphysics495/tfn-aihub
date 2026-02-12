"""
Tests for Story 14.6: AI Summary with Trend Context

Test-first development: these tests define the expected behavior for
trend context features (WoW OEE, repeat offenders, downtime drivers)
added to the Smart Summary generation pipeline.

Story: 14.6 - AI Summary with Trend Context
AC: #1 - WoW OEE comparison in summary
AC: #2 - Repeat offender identification (3+ consecutive days)
AC: #3 - Top downtime drivers from Pareto data
AC: #4 - Graceful omission when trend data unavailable
AC: #5 - Fallback template includes trend lines
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.services.ai.smart_summary import (
    SmartSummaryService,
    SmartSummary,
)
from app.services.ai.context_builder import (
    ContextBuilder,
    SummaryContext,
)
from app.services.ai.prompts import (
    get_system_prompt,
    render_data_prompt,
    SYSTEM_PROMPT_DEFAULT,
)


# =============================================================================
# Fixtures
# =============================================================================

TARGET_DATE = date(2026, 2, 10)
PREVIOUS_WEEK_DATE = date(2026, 2, 3)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_daily_summaries_target_date():
    """Daily summary records for the target date (2026-02-10) with 3 assets."""
    return [
        {
            "id": "sum-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "report_date": "2026-02-10",
            "oee_percentage": 78.0,
            "actual_output": 780,
            "target_output": 1000,
            "financial_loss_dollars": 1500.00,
            "downtime_minutes": 30,
            "waste_count": 10,
        },
        {
            "id": "sum-2",
            "asset_id": "asset-2",
            "asset_name": "CAMA 2400",
            "report_date": "2026-02-10",
            "oee_percentage": 82.6,
            "actual_output": 826,
            "target_output": 1000,
            "financial_loss_dollars": 800.00,
            "downtime_minutes": 15,
            "waste_count": 5,
        },
        {
            "id": "sum-3",
            "asset_id": "asset-3",
            "asset_name": "Wrapper 1",
            "report_date": "2026-02-10",
            "oee_percentage": 83.0,
            "actual_output": 830,
            "target_output": 1000,
            "financial_loss_dollars": 700.00,
            "downtime_minutes": 12,
            "waste_count": 3,
        },
    ]


@pytest.fixture
def sample_daily_summaries_previous_week():
    """Daily summary records for the previous week (2026-02-03)."""
    return [
        {
            "id": "sum-pw-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "report_date": "2026-02-03",
            "oee_percentage": 84.0,
            "actual_output": 840,
            "target_output": 1000,
            "financial_loss_dollars": 1000.00,
            "downtime_minutes": 20,
            "waste_count": 8,
        },
        {
            "id": "sum-pw-2",
            "asset_id": "asset-2",
            "asset_name": "CAMA 2400",
            "report_date": "2026-02-03",
            "oee_percentage": 85.0,
            "actual_output": 850,
            "target_output": 1000,
            "financial_loss_dollars": 500.00,
            "downtime_minutes": 10,
            "waste_count": 3,
        },
        {
            "id": "sum-pw-3",
            "asset_id": "asset-3",
            "asset_name": "Wrapper 1",
            "report_date": "2026-02-03",
            "oee_percentage": 83.9,
            "actual_output": 839,
            "target_output": 1000,
            "financial_loss_dollars": 600.00,
            "downtime_minutes": 11,
            "waste_count": 4,
        },
    ]


@pytest.fixture
def sample_trend_data():
    """Pre-computed trend data for testing."""
    return {
        "plant_oee_current": 81.2,
        "plant_oee_previous_week": 84.3,
        "plant_oee_wow_change": -3.1,
    }


@pytest.fixture
def sample_repeat_offenders():
    """Sample repeat offenders list."""
    return [
        {"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"},
        {"asset_name": "CAMA 2400", "consecutive_days": 4, "category": "oee"},
    ]


@pytest.fixture
def sample_top_downtime_drivers():
    """Sample top downtime drivers."""
    return [
        {"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4},
        {"reason_code": "Changeover", "total_minutes": 95, "asset_count": 2},
    ]


@pytest.fixture
def sample_safety_events():
    """Sample safety events for context."""
    return [
        {
            "id": "safety-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "event_timestamp": "2026-02-10T10:30:00Z",
            "duration_minutes": 15,
            "reason_code": "Emergency Stop",
            "severity": "critical",
            "description": "Operator triggered e-stop due to material jam",
            "is_resolved": False,
        },
    ]


@pytest.fixture
def sample_action_items():
    """Sample action items for context."""
    return [
        {
            "id": "action-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "category": "oee",
            "priority_level": "high",
            "primary_metric_value": "OEE: 78.0%",
            "recommendation_text": "Review performance on Grinder 5",
            "evidence_summary": "OEE 7% below target",
            "financial_impact_usd": 1500.00,
        },
    ]


@pytest.fixture
def minimal_context():
    """Minimal SummaryContext with only pre-14.6 fields."""
    return SummaryContext(
        target_date=TARGET_DATE,
        daily_summaries=[{"oee_percentage": 80.0, "asset_id": "asset-1", "asset_name": "Test"}],
        safety_events=[],
        action_items=[],
        assets={"asset-1": {"name": "Test"}},
    )


@pytest.fixture
def context_with_trends(
    sample_daily_summaries_target_date,
    sample_safety_events,
    sample_action_items,
    sample_trend_data,
    sample_repeat_offenders,
    sample_top_downtime_drivers,
):
    """SummaryContext with all trend fields populated."""
    return SummaryContext(
        target_date=TARGET_DATE,
        daily_summaries=sample_daily_summaries_target_date,
        safety_events=sample_safety_events,
        action_items=sample_action_items,
        assets={
            "asset-1": {"name": "Grinder 5"},
            "asset-2": {"name": "CAMA 2400"},
            "asset-3": {"name": "Wrapper 1"},
        },
        target_oee=85.0,
        trend_data=sample_trend_data,
        repeat_offenders=sample_repeat_offenders,
        top_downtime_drivers=sample_top_downtime_drivers,
    )


@pytest.fixture
def context_without_trends(
    sample_daily_summaries_target_date,
    sample_safety_events,
    sample_action_items,
):
    """SummaryContext with no trend data (pre-14.6 behavior)."""
    return SummaryContext(
        target_date=TARGET_DATE,
        daily_summaries=sample_daily_summaries_target_date,
        safety_events=sample_safety_events,
        action_items=sample_action_items,
        assets={
            "asset-1": {"name": "Grinder 5"},
            "asset-2": {"name": "CAMA 2400"},
            "asset-3": {"name": "Wrapper 1"},
        },
        target_oee=85.0,
        trend_data=None,
        repeat_offenders=[],
        top_downtime_drivers=[],
    )


# =============================================================================
# AC#1: Week-over-Week OEE Comparison Tests
# =============================================================================

class TestTrendDataFetching:
    """Tests for fetch_trend_data() on ContextBuilder (AC#1)."""

    @pytest.mark.asyncio
    async def test_UNIT_001_fetch_trend_data_returns_wow_change(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-001:
        fetch_trend_data returns WoW OEE change when 7-day history exists.

        Given: daily_summaries for target_date (2026-02-10) has 3 assets averaging 81.2% OEE,
               and target_date - 7 (2026-02-03) has 3 assets averaging 84.3% OEE
        When:  fetch_trend_data(target_date=date(2026, 2, 10)) is called
        Then:  returns {"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}
        """
        # Mock Supabase queries for target_date and previous week
        target_date_data = [
            {"oee_percentage": 78.0},
            {"oee_percentage": 82.6},
            {"oee_percentage": 83.0},
        ]
        previous_week_data = [
            {"oee_percentage": 84.0},
            {"oee_percentage": 85.0},
            {"oee_percentage": 83.9},
        ]

        # Configure mock chain for two different date queries
        def mock_eq(field, value):
            result = MagicMock()
            if value == TARGET_DATE.isoformat():
                result.execute.return_value = MagicMock(data=target_date_data)
            elif value == PREVIOUS_WEEK_DATE.isoformat():
                result.execute.return_value = MagicMock(data=previous_week_data)
            else:
                result.execute.return_value = MagicMock(data=[])
            return result

        mock_supabase_client.table.return_value.select.return_value.eq = mock_eq

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_trend_data(target_date=TARGET_DATE)

        assert result is not None
        assert abs(result["plant_oee_current"] - 81.2) < 0.1
        assert abs(result["plant_oee_previous_week"] - 84.3) < 0.1
        assert abs(result["plant_oee_wow_change"] - (-3.1)) < 0.1

    @pytest.mark.asyncio
    async def test_UNIT_008_fetch_trend_data_computes_correct_average(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-008:
        fetch_trend_data computes correct plant-wide average across multiple assets.

        Given: 5 assets on target_date with OEE [72.0, 80.0, 85.0, 90.0, 78.0] (avg 81.0)
               5 assets on target_date-7 with [75.0, 82.0, 88.0, 92.0, 80.0] (avg 83.4)
        When:  fetch_trend_data(target_date) is called
        Then:  returns plant_oee_current=81.0, plant_oee_previous_week=83.4, plant_oee_wow_change=-2.4
        """
        target_date_data = [
            {"oee_percentage": 72.0},
            {"oee_percentage": 80.0},
            {"oee_percentage": 85.0},
            {"oee_percentage": 90.0},
            {"oee_percentage": 78.0},
        ]
        previous_week_data = [
            {"oee_percentage": 75.0},
            {"oee_percentage": 82.0},
            {"oee_percentage": 88.0},
            {"oee_percentage": 92.0},
            {"oee_percentage": 80.0},
        ]

        def mock_eq(field, value):
            result = MagicMock()
            if value == TARGET_DATE.isoformat():
                result.execute.return_value = MagicMock(data=target_date_data)
            elif value == PREVIOUS_WEEK_DATE.isoformat():
                result.execute.return_value = MagicMock(data=previous_week_data)
            else:
                result.execute.return_value = MagicMock(data=[])
            return result

        mock_supabase_client.table.return_value.select.return_value.eq = mock_eq

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_trend_data(target_date=TARGET_DATE)

        assert result is not None
        assert abs(result["plant_oee_current"] - 81.0) < 0.1
        assert abs(result["plant_oee_previous_week"] - 83.4) < 0.1
        assert abs(result["plant_oee_wow_change"] - (-2.4)) < 0.1


class TestSummaryContextTrendFields:
    """Tests for trend fields on SummaryContext (AC#1, AC#2, AC#3)."""

    def test_UNIT_002_trend_data_defaults_to_none(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-002:
        SummaryContext trend_data field is Optional with None default.

        Given: SummaryContext constructed with only required fields
        When:  Instantiated without passing trend_data
        Then:  context.trend_data is None, has_data returns True if daily_summaries non-empty
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[{"oee_percentage": 80.0}],
        )
        assert context.trend_data is None
        assert context.has_data is True

    def test_UNIT_015_repeat_offenders_defaults_to_empty(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-015:
        SummaryContext repeat_offenders field defaults to empty list.

        Given: SummaryContext constructed without passing repeat_offenders
        When:  Instantiated
        Then:  context.repeat_offenders equals []
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[],
        )
        assert context.repeat_offenders == []

    def test_UNIT_022_top_downtime_drivers_defaults_to_empty(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-022:
        SummaryContext top_downtime_drivers field defaults to empty list.

        Given: SummaryContext constructed without passing top_downtime_drivers
        When:  Instantiated
        Then:  context.top_downtime_drivers equals []
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[],
        )
        assert context.top_downtime_drivers == []


class TestBuildContextTrend:
    """Tests for build_context populating trend fields (AC#1, AC#2, AC#3)."""

    @pytest.mark.asyncio
    async def test_UNIT_003_build_context_populates_trend_data(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-003:
        build_context populates trend_data when historical data is available.

        Given: Supabase daily_summaries has data for both target_date and target_date - 7
        When:  build_context(target_date=date(2026, 2, 10)) is called
        Then:  returned SummaryContext has trend_data populated with
               plant_oee_current, plant_oee_previous_week, plant_oee_wow_change
        """
        # Set up mock returns for all required fetches
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 78.0, "asset_id": "asset-1", "report_date": "2026-02-10",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        # Generic chain mock
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        # Mock the action engine
        with patch.object(builder, 'fetch_action_items', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock, return_value={
                 "plant_oee_current": 81.2,
                 "plant_oee_previous_week": 84.3,
                 "plant_oee_wow_change": -3.1,
             }), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock, return_value=[]), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        # This will fail until build_context is updated to call fetch_trend_data
        # and populate the trend_data field
        assert context.trend_data is not None
        assert "plant_oee_current" in context.trend_data
        assert "plant_oee_previous_week" in context.trend_data
        assert "plant_oee_wow_change" in context.trend_data

    @pytest.mark.asyncio
    async def test_UNIT_016_build_context_populates_repeat_offenders(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-016:
        build_context populates repeat_offenders when trailing data exists.

        Given: Supabase has 7 days of daily_summaries with an asset below OEE target
               for 3+ consecutive days
        When:  build_context(target_date) is called
        Then:  returned SummaryContext has repeat_offenders with at least one entry
        """
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 78.0, "asset_id": "asset-1", "report_date": "2026-02-10",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        with patch.object(builder, 'fetch_action_items', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock, return_value=None), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock, return_value=[
                 {"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"},
             ]), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock, return_value=[]), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        # Will fail until build_context calls fetch_repeat_offenders
        assert len(context.repeat_offenders) >= 1
        assert context.repeat_offenders[0]["asset_name"] == "Grinder 5"

    @pytest.mark.asyncio
    async def test_UNIT_023_build_context_populates_top_downtime_drivers(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-023:
        build_context populates top_downtime_drivers when downtime_events data exists.

        Given: Supabase downtime_events table has rows for target_date
        When:  build_context(target_date) is called
        Then:  returned SummaryContext has top_downtime_drivers with aggregated entries
        """
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 78.0, "asset_id": "asset-1", "report_date": "2026-02-10",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        with patch.object(builder, 'fetch_action_items', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock, return_value=None), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock, return_value=[]), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock, return_value=[
                 {"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4},
             ]), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        # Will fail until build_context calls fetch_top_downtime_drivers
        assert len(context.top_downtime_drivers) >= 1
        assert context.top_downtime_drivers[0]["reason_code"] == "Mechanical"


class TestFormatTrendContext:
    """Tests for format_trend_context() in prompts.py (AC#1, AC#2, AC#3)."""

    def test_UNIT_004_format_trend_context_renders_wow_oee(self, sample_trend_data):
        """
        14-6-ai-summary-with-trend-context-UNIT-004:
        format_trend_context renders WoW OEE comparison line.

        Given: trend_data with plant_oee_current=81.2, plant_oee_previous_week=84.3, wow_change=-3.1
        When:  format_trend_context(trend_data=trend_data) is called
        Then:  output contains "Week-over-Week OEE: Current 81.2% vs Last Week 84.3% (change: -3.1 points)"
        """
        from app.services.ai.prompts import format_trend_context

        result = format_trend_context(trend_data=sample_trend_data)

        assert "Week-over-Week OEE" in result
        assert "81.2%" in result
        assert "84.3%" in result
        assert "-3.1 points" in result

    def test_UNIT_007_format_trend_context_positive_change(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-007:
        format_trend_context handles positive WoW change correctly.

        Given: trend_data with positive wow_change=+3.2
        When:  format_trend_context(trend_data=...) is called
        Then:  output contains "change: +3.2 points" (with plus sign)
        """
        from app.services.ai.prompts import format_trend_context

        trend_data = {
            "plant_oee_current": 87.5,
            "plant_oee_previous_week": 84.3,
            "plant_oee_wow_change": 3.2,
        }
        result = format_trend_context(trend_data=trend_data)

        assert "+3.2 points" in result

    def test_UNIT_014_format_trend_context_renders_repeat_offenders(
        self, sample_repeat_offenders
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-014:
        format_trend_context renders repeat offenders section.

        Given: repeat_offenders list with two entries
        When:  format_trend_context(repeat_offenders=repeat_offenders) is called
        Then:  output contains "Repeat Offenders (3+ consecutive days on report):"
               AND "Grinder 5: 3 consecutive days"
               AND "CAMA 2400: 4 consecutive days"
        """
        from app.services.ai.prompts import format_trend_context

        result = format_trend_context(repeat_offenders=sample_repeat_offenders)

        assert "Repeat Offenders (3+ consecutive days on report):" in result
        assert "Grinder 5: 3 consecutive days" in result
        assert "CAMA 2400: 4 consecutive days" in result

    def test_UNIT_021_format_trend_context_renders_downtime_drivers(
        self, sample_top_downtime_drivers
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-021:
        format_trend_context renders top downtime drivers section.

        Given: top_downtime_drivers list with two entries
        When:  format_trend_context(top_downtime_drivers=...) is called
        Then:  output contains "Top Downtime Drivers (yesterday):"
               AND "Mechanical: 187 min across 4 assets"
               AND "Changeover: 95 min across 2 assets"
        """
        from app.services.ai.prompts import format_trend_context

        result = format_trend_context(top_downtime_drivers=sample_top_downtime_drivers)

        assert "Top Downtime Drivers (yesterday):" in result
        assert "Mechanical: 187 min across 4 assets" in result
        assert "Changeover: 95 min across 2 assets" in result


class TestRenderDataPromptTrend:
    """Tests for render_data_prompt with trend context (AC#1)."""

    def test_UNIT_005_render_data_prompt_includes_trend_section(self, sample_trend_data):
        """
        14-6-ai-summary-with-trend-context-UNIT-005:
        render_data_prompt includes TREND CONTEXT section when trend data provided.

        Given: render_data_prompt called with valid trend_data kwarg
        When:  render_data_prompt(target_date=..., ..., trend_data={...})
        Then:  returned prompt string contains "TREND CONTEXT" section header
               AND the WoW OEE comparison text
        """
        result = render_data_prompt(
            target_date=TARGET_DATE,
            safety_events=[],
            daily_summaries=[],
            action_items=[],
            trend_data=sample_trend_data,
        )

        assert "TREND CONTEXT" in result
        assert "Week-over-Week OEE" in result
        assert "81.2%" in result

    def test_UNIT_031_render_data_prompt_backward_compatible(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-031:
        render_data_prompt works without trend kwargs (backward compatible).

        Given: render_data_prompt called with only pre-14.6 arguments
        When:  render_data_prompt(target_date=..., safety_events=[], daily_summaries=[], action_items=[])
        Then:  returns a valid prompt string without errors;
               TREND CONTEXT section contains graceful "no data" text
        """
        result = render_data_prompt(
            target_date=TARGET_DATE,
            safety_events=[],
            daily_summaries=[],
            action_items=[],
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain TREND CONTEXT section with graceful no-data message
        assert "TREND CONTEXT" in result


class TestGenerateWithLLMTrend:
    """Tests for _generate_with_llm passing trend data (AC#1)."""

    @pytest.mark.asyncio
    async def test_UNIT_006_generate_with_llm_passes_trend_data(
        self, sample_trend_data
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-006:
        _generate_with_llm passes trend_data from context to render_data_prompt.

        Given: SummaryContext has trend_data populated
        When:  _generate_with_llm(context) is called with mocked LLM
        Then:  render_data_prompt is called with trend_data kwarg matching context.trend_data
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[{"oee_percentage": 80.0, "asset_id": "a1", "asset_name": "Test"}],
            safety_events=[],
            action_items=[],
            trend_data=sample_trend_data,
            repeat_offenders=[],
            top_downtime_drivers=[],
        )

        service = SmartSummaryService()

        mock_response = MagicMock()
        mock_response.content = "Test summary with trend data"
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

            # Verify render_data_prompt was called with trend_data
            mock_render.assert_called_once()
            call_kwargs = mock_render.call_args
            assert call_kwargs.kwargs.get("trend_data") == sample_trend_data or \
                   (len(call_kwargs.args) > 0 and "trend_data" in str(call_kwargs))


class TestSystemPromptTrend:
    """Tests for system prompt containing trend instructions (AC#1)."""

    def test_UNIT_009_system_prompt_includes_trend_instructions(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-009:
        SYSTEM_PROMPT_DEFAULT includes trend context instructions.

        Given: SYSTEM_PROMPT_DEFAULT is loaded
        When:  the prompt text is inspected
        Then:  it contains instructions to incorporate week-over-week trends,
               repeat offenders, and downtime drivers when available
        """
        prompt = get_system_prompt()

        # Should contain instructions about trend context
        prompt_lower = prompt.lower()
        assert "week-over-week" in prompt_lower or "trend" in prompt_lower
        assert "repeat" in prompt_lower or "consecutive" in prompt_lower
        assert "downtime" in prompt_lower or "driver" in prompt_lower


# =============================================================================
# AC#2: Repeat Offender Identification Tests
# =============================================================================

class TestRepeatOffenders:
    """Tests for fetch_repeat_offenders() on ContextBuilder (AC#2)."""

    @pytest.mark.asyncio
    async def test_UNIT_010_identifies_3_consecutive_days(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-010:
        fetch_repeat_offenders identifies asset below target for 3 consecutive days.

        Given: daily_summaries for trailing 7 days shows "Grinder 5" (asset-1)
               with OEE below target (85%) for the last 3 consecutive days
        When:  fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
        Then:  returns [{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}]
        """
        # 7 days of data for asset-1: [86, 87, 85, 88, 78, 72, 75]
        # dates: 2/4, 2/5, 2/6, 2/7, 2/8, 2/9, 2/10
        # Last 3 (2/8, 2/9, 2/10) are below 85 target
        trailing_data = [
            {"asset_id": "asset-1", "report_date": "2026-02-04", "oee_percentage": 86.0},
            {"asset_id": "asset-1", "report_date": "2026-02-05", "oee_percentage": 87.0},
            {"asset_id": "asset-1", "report_date": "2026-02-06", "oee_percentage": 85.0},
            {"asset_id": "asset-1", "report_date": "2026-02-07", "oee_percentage": 88.0},
            {"asset_id": "asset-1", "report_date": "2026-02-08", "oee_percentage": 78.0},
            {"asset_id": "asset-1", "report_date": "2026-02-09", "oee_percentage": 72.0},
            {"asset_id": "asset-1", "report_date": "2026-02-10", "oee_percentage": 75.0},
        ]

        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=trailing_data
        )
        # Also mock assets lookup
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "asset-1", "name": "Grinder 5"}]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_repeat_offenders(target_date=TARGET_DATE)

        assert len(result) >= 1
        offender = next(
            (r for r in result if r["asset_name"] == "Grinder 5"), None
        )
        assert offender is not None
        assert offender["consecutive_days"] == 3
        assert offender["category"] == "oee"

    @pytest.mark.asyncio
    async def test_UNIT_011_identifies_4_consecutive_days(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-011:
        fetch_repeat_offenders identifies asset below target for 4+ consecutive days.

        Given: daily_summaries shows "CAMA 2400" (asset-2) below target for 4 consecutive days
        When:  fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
        Then:  returns entry with consecutive_days=4
        """
        trailing_data = [
            {"asset_id": "asset-2", "report_date": "2026-02-04", "oee_percentage": 90.0},
            {"asset_id": "asset-2", "report_date": "2026-02-05", "oee_percentage": 88.0},
            {"asset_id": "asset-2", "report_date": "2026-02-06", "oee_percentage": 86.0},
            {"asset_id": "asset-2", "report_date": "2026-02-07", "oee_percentage": 80.0},
            {"asset_id": "asset-2", "report_date": "2026-02-08", "oee_percentage": 78.0},
            {"asset_id": "asset-2", "report_date": "2026-02-09", "oee_percentage": 75.0},
            {"asset_id": "asset-2", "report_date": "2026-02-10", "oee_percentage": 72.0},
        ]

        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=trailing_data
        )
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "asset-2", "name": "CAMA 2400"}]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_repeat_offenders(target_date=TARGET_DATE)

        assert len(result) >= 1
        offender = next(
            (r for r in result if r["asset_name"] == "CAMA 2400"), None
        )
        assert offender is not None
        assert offender["consecutive_days"] == 4
        assert offender["category"] == "oee"

    @pytest.mark.asyncio
    async def test_UNIT_012_excludes_2_day_offender(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-012:
        fetch_repeat_offenders excludes asset below target for only 2 consecutive days.

        Given: asset below target for only 2 consecutive days (2/9 and 2/10)
        When:  fetch_repeat_offenders(target_date) is called
        Then:  returns empty list
        """
        trailing_data = [
            {"asset_id": "asset-3", "report_date": "2026-02-04", "oee_percentage": 90.0},
            {"asset_id": "asset-3", "report_date": "2026-02-05", "oee_percentage": 88.0},
            {"asset_id": "asset-3", "report_date": "2026-02-06", "oee_percentage": 87.0},
            {"asset_id": "asset-3", "report_date": "2026-02-07", "oee_percentage": 86.0},
            {"asset_id": "asset-3", "report_date": "2026-02-08", "oee_percentage": 89.0},
            {"asset_id": "asset-3", "report_date": "2026-02-09", "oee_percentage": 78.0},
            {"asset_id": "asset-3", "report_date": "2026-02-10", "oee_percentage": 75.0},
        ]

        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=trailing_data
        )
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "asset-3", "name": "Wrapper 1"}]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_repeat_offenders(target_date=TARGET_DATE)

        assert result == []

    @pytest.mark.asyncio
    async def test_UNIT_013_handles_non_consecutive_gap(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-013:
        fetch_repeat_offenders handles non-consecutive below-target days.

        Given: asset below target on 2/5, 2/6, 2/8, 2/9, 2/10 but NOT 2/7
        When:  fetch_repeat_offenders(target_date) is called
        Then:  returns consecutive_days=3 (only 2/8, 2/9, 2/10 trailing streak)
        """
        trailing_data = [
            {"asset_id": "asset-1", "report_date": "2026-02-04", "oee_percentage": 90.0},
            {"asset_id": "asset-1", "report_date": "2026-02-05", "oee_percentage": 78.0},
            {"asset_id": "asset-1", "report_date": "2026-02-06", "oee_percentage": 75.0},
            {"asset_id": "asset-1", "report_date": "2026-02-07", "oee_percentage": 88.0},  # gap
            {"asset_id": "asset-1", "report_date": "2026-02-08", "oee_percentage": 78.0},
            {"asset_id": "asset-1", "report_date": "2026-02-09", "oee_percentage": 72.0},
            {"asset_id": "asset-1", "report_date": "2026-02-10", "oee_percentage": 75.0},
        ]

        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=trailing_data
        )
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "asset-1", "name": "Grinder 5"}]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_repeat_offenders(target_date=TARGET_DATE)

        assert len(result) >= 1
        offender = result[0]
        assert offender["consecutive_days"] == 3

    @pytest.mark.asyncio
    async def test_UNIT_017_multiple_offenders_sorted_descending(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-017:
        fetch_repeat_offenders returns multiple offenders sorted by consecutive_days descending.

        Given: Two assets qualify with different streak lengths (3 and 5 days)
        When:  fetch_repeat_offenders(target_date) is called
        Then:  returns both, ordered by consecutive_days descending (5-day first)
        """
        trailing_data = [
            # asset-1: below target for last 3 days
            {"asset_id": "asset-1", "report_date": "2026-02-04", "oee_percentage": 90.0},
            {"asset_id": "asset-1", "report_date": "2026-02-05", "oee_percentage": 90.0},
            {"asset_id": "asset-1", "report_date": "2026-02-06", "oee_percentage": 90.0},
            {"asset_id": "asset-1", "report_date": "2026-02-07", "oee_percentage": 90.0},
            {"asset_id": "asset-1", "report_date": "2026-02-08", "oee_percentage": 78.0},
            {"asset_id": "asset-1", "report_date": "2026-02-09", "oee_percentage": 72.0},
            {"asset_id": "asset-1", "report_date": "2026-02-10", "oee_percentage": 75.0},
            # asset-2: below target for last 5 days
            {"asset_id": "asset-2", "report_date": "2026-02-04", "oee_percentage": 90.0},
            {"asset_id": "asset-2", "report_date": "2026-02-05", "oee_percentage": 90.0},
            {"asset_id": "asset-2", "report_date": "2026-02-06", "oee_percentage": 78.0},
            {"asset_id": "asset-2", "report_date": "2026-02-07", "oee_percentage": 75.0},
            {"asset_id": "asset-2", "report_date": "2026-02-08", "oee_percentage": 72.0},
            {"asset_id": "asset-2", "report_date": "2026-02-09", "oee_percentage": 70.0},
            {"asset_id": "asset-2", "report_date": "2026-02-10", "oee_percentage": 68.0},
        ]

        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=trailing_data
        )
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "asset-1", "name": "Grinder 5"},
                {"id": "asset-2", "name": "CAMA 2400"},
            ]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_repeat_offenders(target_date=TARGET_DATE)

        assert len(result) == 2
        # Should be sorted descending by consecutive_days
        assert result[0]["consecutive_days"] >= result[1]["consecutive_days"]
        assert result[0]["consecutive_days"] == 5
        assert result[1]["consecutive_days"] == 3


# =============================================================================
# AC#3: Top Downtime Drivers Tests
# =============================================================================

class TestTopDowntimeDrivers:
    """Tests for fetch_top_downtime_drivers() on ContextBuilder (AC#3)."""

    @pytest.mark.asyncio
    async def test_UNIT_018_aggregates_by_reason_code(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-018:
        fetch_top_downtime_drivers aggregates by reason_code correctly.

        Given: downtime_events with 6 rows for target_date
        When:  fetch_top_downtime_drivers(target_date) is called
        Then:  returns aggregated results with Mechanical=187min/4 assets, Changeover=95min/2 assets
        """
        downtime_data = [
            {"reason_code": "Mechanical", "asset_id": "asset-1", "duration_minutes": 60, "event_date": "2026-02-10"},
            {"reason_code": "Mechanical", "asset_id": "asset-2", "duration_minutes": 45, "event_date": "2026-02-10"},
            {"reason_code": "Mechanical", "asset_id": "asset-3", "duration_minutes": 40, "event_date": "2026-02-10"},
            {"reason_code": "Mechanical", "asset_id": "asset-4", "duration_minutes": 42, "event_date": "2026-02-10"},
            {"reason_code": "Changeover", "asset_id": "asset-1", "duration_minutes": 50, "event_date": "2026-02-10"},
            {"reason_code": "Changeover", "asset_id": "asset-5", "duration_minutes": 45, "event_date": "2026-02-10"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=downtime_data
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_top_downtime_drivers(target_date=TARGET_DATE)

        assert len(result) >= 2

        mechanical = next(
            (r for r in result if r["reason_code"] == "Mechanical"), None
        )
        assert mechanical is not None
        assert mechanical["total_minutes"] == 187
        assert mechanical["asset_count"] == 4

        changeover = next(
            (r for r in result if r["reason_code"] == "Changeover"), None
        )
        assert changeover is not None
        assert changeover["total_minutes"] == 95
        assert changeover["asset_count"] == 2

    @pytest.mark.asyncio
    async def test_UNIT_019_returns_top_3_only(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-019:
        fetch_top_downtime_drivers returns top 3 only when more than 3 reason codes exist.

        Given: downtime_events with 5 distinct reason_codes
        When:  fetch_top_downtime_drivers(target_date) is called
        Then:  returns exactly 3 entries sorted by total_minutes descending
        """
        downtime_data = [
            {"reason_code": "Mechanical", "asset_id": "a1", "duration_minutes": 200, "event_date": "2026-02-10"},
            {"reason_code": "Changeover", "asset_id": "a2", "duration_minutes": 150, "event_date": "2026-02-10"},
            {"reason_code": "Material", "asset_id": "a3", "duration_minutes": 100, "event_date": "2026-02-10"},
            {"reason_code": "Electrical", "asset_id": "a4", "duration_minutes": 50, "event_date": "2026-02-10"},
            {"reason_code": "Quality", "asset_id": "a5", "duration_minutes": 25, "event_date": "2026-02-10"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=downtime_data
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_top_downtime_drivers(target_date=TARGET_DATE)

        assert len(result) == 3
        # Should be sorted descending
        assert result[0]["total_minutes"] >= result[1]["total_minutes"]
        assert result[1]["total_minutes"] >= result[2]["total_minutes"]

    @pytest.mark.asyncio
    async def test_UNIT_020_counts_distinct_assets(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-020:
        fetch_top_downtime_drivers counts distinct assets per reason_code.

        Given: Mechanical has events: asset-1/30min, asset-1/25min, asset-2/40min
        When:  fetch_top_downtime_drivers(target_date) is called
        Then:  Mechanical total_minutes=95, asset_count=2 (distinct assets)
        """
        downtime_data = [
            {"reason_code": "Mechanical", "asset_id": "asset-1", "duration_minutes": 30, "event_date": "2026-02-10"},
            {"reason_code": "Mechanical", "asset_id": "asset-1", "duration_minutes": 25, "event_date": "2026-02-10"},
            {"reason_code": "Mechanical", "asset_id": "asset-2", "duration_minutes": 40, "event_date": "2026-02-10"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=downtime_data
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_top_downtime_drivers(target_date=TARGET_DATE)

        assert len(result) >= 1
        mechanical = result[0]
        assert mechanical["total_minutes"] == 95
        assert mechanical["asset_count"] == 2  # distinct assets, not 3

    @pytest.mark.asyncio
    async def test_UNIT_024_returns_empty_when_no_events(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-UNIT-024:
        fetch_top_downtime_drivers returns empty list when no downtime events.

        Given: downtime_events has no rows for target_date
        When:  fetch_top_downtime_drivers(target_date) is called
        Then:  returns []
        """
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_top_downtime_drivers(target_date=TARGET_DATE)

        assert result == []


# =============================================================================
# AC#4: Graceful Degradation Tests
# =============================================================================

class TestGracefulDegradation:
    """Tests for graceful omission when trend data unavailable (AC#4)."""

    @pytest.mark.asyncio
    async def test_UNIT_025_fetch_trend_data_returns_none_no_history(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-025:
        fetch_trend_data returns None when no historical data exists.

        Given: daily_summaries has no data for target_date - 7
        When:  fetch_trend_data(target_date) is called
        Then:  returns None
        """
        def mock_eq(field, value):
            result = MagicMock()
            if value == TARGET_DATE.isoformat():
                result.execute.return_value = MagicMock(
                    data=[{"oee_percentage": 80.0}]
                )
            else:
                # Previous week: no data
                result.execute.return_value = MagicMock(data=[])
            return result

        mock_supabase_client.table.return_value.select.return_value.eq = mock_eq

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_trend_data(target_date=TARGET_DATE)

        assert result is None

    @pytest.mark.asyncio
    async def test_UNIT_026_fetch_trend_data_returns_none_on_exception(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-026:
        fetch_trend_data returns None on Supabase exception.

        Given: Supabase raises an exception during query
        When:  fetch_trend_data(target_date) is called
        Then:  returns None (does not raise), error is logged
        """
        mock_supabase_client.table.side_effect = Exception("connection error")

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_trend_data(target_date=TARGET_DATE)

        assert result is None

    @pytest.mark.asyncio
    async def test_UNIT_027_fetch_repeat_offenders_returns_empty_on_exception(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-027:
        fetch_repeat_offenders returns empty list on Supabase exception.

        Given: Supabase raises an exception during query
        When:  fetch_repeat_offenders(target_date) is called
        Then:  returns [] (does not raise), error is logged
        """
        mock_supabase_client.table.side_effect = Exception("connection error")

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_repeat_offenders(target_date=TARGET_DATE)

        assert result == []

    @pytest.mark.asyncio
    async def test_UNIT_028_fetch_downtime_drivers_returns_empty_on_missing_table(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-028:
        fetch_top_downtime_drivers returns empty list when table does not exist.

        Given: downtime_events table does not exist, Supabase raises error
        When:  fetch_top_downtime_drivers(target_date) is called
        Then:  returns [] (does not raise), error is logged
        """
        mock_supabase_client.table.side_effect = Exception(
            "relation \"downtime_events\" does not exist"
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_top_downtime_drivers(target_date=TARGET_DATE)

        assert result == []

    @pytest.mark.asyncio
    async def test_UNIT_029_build_context_succeeds_with_all_trend_fetches_failing(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-029:
        build_context succeeds with all trend fetches failing.

        Given: fetch_trend_data, fetch_repeat_offenders, fetch_top_downtime_drivers all raise
        When:  build_context(target_date) is called
        Then:  returns valid SummaryContext with trend_data=None, repeat_offenders=[],
               top_downtime_drivers=[], and core fields populated normally
        """
        # Mock core fetches to succeed
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 80.0, "asset_id": "asset-1", "report_date": "2026-02-10",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "asset-1", "name": "Test Asset"}]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        # Mock trend fetches to raise exceptions
        with patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock,
                         side_effect=Exception("trend failure")), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock,
                         side_effect=Exception("repeat failure")), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock,
                         side_effect=Exception("downtime failure")), \
             patch.object(builder, 'fetch_action_items', new_callable=AsyncMock, return_value=[]), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        # Core data should be populated
        assert context.daily_summaries is not None
        assert context.target_date == TARGET_DATE

        # Trend data should default gracefully
        assert context.trend_data is None
        assert context.repeat_offenders == []
        assert context.top_downtime_drivers == []

    def test_UNIT_030_format_trend_context_all_empty(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-030:
        format_trend_context with all None/empty inputs returns graceful message.

        Given: trend_data=None, repeat_offenders=[], top_downtime_drivers=[]
        When:  format_trend_context(...) is called
        Then:  returns graceful "no data" message (not empty, not error)
        """
        from app.services.ai.prompts import format_trend_context

        result = format_trend_context(
            trend_data=None,
            repeat_offenders=[],
            top_downtime_drivers=[],
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Should be a benign message, not an error
        assert "no trend data" in result.lower() or "not available" in result.lower()

    def test_UNIT_032_format_trend_context_partial_data(self, sample_trend_data):
        """
        14-6-ai-summary-with-trend-context-UNIT-032:
        format_trend_context with partial data renders only available sections.

        Given: trend_data populated but repeat_offenders=[] and top_downtime_drivers=[]
        When:  format_trend_context(trend_data=..., repeat_offenders=[], top_downtime_drivers=[])
        Then:  output contains "Week-over-Week OEE" but NOT "Repeat Offenders" or "Top Downtime Drivers"
        """
        from app.services.ai.prompts import format_trend_context

        result = format_trend_context(
            trend_data=sample_trend_data,
            repeat_offenders=[],
            top_downtime_drivers=[],
        )

        assert "Week-over-Week OEE" in result
        assert "Repeat Offenders" not in result
        assert "Top Downtime Drivers" not in result

    @pytest.mark.asyncio
    async def test_UNIT_033_build_context_isolates_trend_failure(
        self, mock_supabase_client
    ):
        """
        14-6-ai-summary-with-trend-context-UNIT-033:
        build_context isolates trend fetch failure from repeat offender fetch.

        Given: fetch_trend_data raises, fetch_repeat_offenders and fetch_top_downtime_drivers succeed
        When:  build_context(target_date) is called
        Then:  trend_data=None but repeat_offenders and top_downtime_drivers populated
        """
        mock_response = MagicMock()
        mock_response.data = [
            {"oee_percentage": 80.0, "asset_id": "asset-1", "report_date": "2026-02-10",
             "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
             "actual_output": 100, "target_output": 100, "id": "s1"},
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "asset-1", "name": "Test Asset"}]
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)

        with patch.object(builder, 'fetch_trend_data', new_callable=AsyncMock,
                         side_effect=Exception("trend failure")), \
             patch.object(builder, 'fetch_repeat_offenders', new_callable=AsyncMock,
                         return_value=[{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}]), \
             patch.object(builder, 'fetch_top_downtime_drivers', new_callable=AsyncMock,
                         return_value=[{"reason_code": "Mechanical", "total_minutes": 100, "asset_count": 2}]), \
             patch.object(builder, 'fetch_action_items', new_callable=AsyncMock, return_value=[]), \
             patch('app.services.ai.context_builder.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=85.0,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
            context = await builder.build_context(target_date=TARGET_DATE)

        assert context.trend_data is None
        assert len(context.repeat_offenders) == 1
        assert len(context.top_downtime_drivers) == 1


# =============================================================================
# AC#5: Fallback Summary with Trend Lines Tests
# =============================================================================

class TestFallbackSummaryTrends:
    """Tests for fallback summary including trend lines (AC#5)."""

    def test_UNIT_034_fallback_includes_wow_oee(self, context_with_trends):
        """
        14-6-ai-summary-with-trend-context-UNIT-034:
        Fallback summary includes WoW OEE comparison when trend_data is present.

        Given: SummaryContext has trend_data with plant_oee_current=81.2, wow_change=-3.1
        When:  generate_fallback_summary(context) is called
        Then:  summary_text contains "Overall plant OEE 81.2%" and "down 3.1 points from last week"
        """
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_with_trends)

        assert "81.2%" in summary.summary_text
        assert "down 3.1 points from last week" in summary.summary_text

    def test_UNIT_035_fallback_positive_wow_change(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-035:
        Fallback summary includes positive WoW OEE with "up" direction.

        Given: SummaryContext has trend_data with positive wow_change=2.5
        When:  generate_fallback_summary(context) is called
        Then:  summary_text contains "up 2.5 points from last week"
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 87.5, "asset_id": "a1", "asset_name": "Test",
                 "financial_loss_dollars": 0, "downtime_minutes": 0, "waste_count": 0,
                 "actual_output": 100, "target_output": 100},
            ],
            safety_events=[],
            action_items=[],
            trend_data={
                "plant_oee_current": 87.5,
                "plant_oee_previous_week": 85.0,
                "plant_oee_wow_change": 2.5,
            },
            repeat_offenders=[],
            top_downtime_drivers=[],
        )

        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context)

        assert "up 2.5 points from last week" in summary.summary_text

    def test_UNIT_036_fallback_includes_recurring_issues(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-036:
        Fallback summary includes Recurring Issues section when repeat_offenders exist.

        Given: SummaryContext has repeat_offenders with Grinder 5 for 3 consecutive days
        When:  generate_fallback_summary(context) is called
        Then:  summary_text contains "**Recurring Issues**" AND "Grinder 5" AND
               "3 consecutive days" AND "consider escalating to maintenance planning"
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 78.0, "asset_id": "a1", "asset_name": "Grinder 5",
                 "financial_loss_dollars": 500, "downtime_minutes": 30, "waste_count": 5,
                 "actual_output": 800, "target_output": 1000},
            ],
            safety_events=[],
            action_items=[],
            trend_data=None,
            repeat_offenders=[
                {"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"},
            ],
            top_downtime_drivers=[],
        )

        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context)

        assert "**Recurring Issues**" in summary.summary_text
        assert "Grinder 5" in summary.summary_text
        assert "3 consecutive days" in summary.summary_text
        assert "consider escalating to maintenance planning" in summary.summary_text.lower() or \
               "escalat" in summary.summary_text.lower()

    def test_UNIT_037_fallback_includes_downtime_drivers(self):
        """
        14-6-ai-summary-with-trend-context-UNIT-037:
        Fallback summary includes Downtime Drivers section when top_downtime_drivers exist.

        Given: SummaryContext has top_downtime_drivers with Mechanical
        When:  generate_fallback_summary(context) is called
        Then:  summary_text contains "**Downtime Drivers**" AND "Mechanical: 187 min across 4 assets"
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 78.0, "asset_id": "a1", "asset_name": "Test",
                 "financial_loss_dollars": 500, "downtime_minutes": 30, "waste_count": 5,
                 "actual_output": 800, "target_output": 1000},
            ],
            safety_events=[],
            action_items=[],
            trend_data=None,
            repeat_offenders=[],
            top_downtime_drivers=[
                {"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4},
            ],
        )

        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context)

        assert "**Downtime Drivers**" in summary.summary_text
        assert "Mechanical" in summary.summary_text
        assert "187 min" in summary.summary_text
        assert "4 assets" in summary.summary_text

    def test_UNIT_038_fallback_includes_all_trend_sections(self, context_with_trends):
        """
        14-6-ai-summary-with-trend-context-UNIT-038:
        Fallback summary includes all three trend sections simultaneously.

        Given: SummaryContext has trend_data, repeat_offenders (2), top_downtime_drivers (2) all populated
        When:  generate_fallback_summary(context) is called
        Then:  summary_text contains WoW OEE line, **Recurring Issues**, **Downtime Drivers**,
               AND existing sections (**Safety**, **Productivity**) are present
        """
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_with_trends)

        text = summary.summary_text

        # Trend sections
        assert "81.2%" in text
        assert "down 3.1 points" in text or "-3.1" in text
        assert "**Recurring Issues**" in text
        assert "Grinder 5" in text
        assert "CAMA 2400" in text
        assert "**Downtime Drivers**" in text
        assert "Mechanical" in text
        assert "Changeover" in text

        # Existing sections should still be present
        assert "**Safety**" in text
        assert "**Productivity**" in text

    def test_UNIT_039_fallback_without_trends_unchanged(self, context_without_trends):
        """
        14-6-ai-summary-with-trend-context-UNIT-039:
        Fallback summary without trend data is unchanged from pre-14.6 behavior.

        Given: SummaryContext has trend_data=None, repeat_offenders=[], top_downtime_drivers=[]
        When:  generate_fallback_summary(context) is called
        Then:  summary_text does NOT contain "Recurring Issues", "Downtime Drivers",
               or "points from last week"; existing sections present and correct
        """
        # Verify the context has the new trend fields (will fail until SummaryContext is updated)
        assert hasattr(context_without_trends, 'trend_data')
        assert context_without_trends.trend_data is None
        assert hasattr(context_without_trends, 'repeat_offenders')
        assert context_without_trends.repeat_offenders == []
        assert hasattr(context_without_trends, 'top_downtime_drivers')
        assert context_without_trends.top_downtime_drivers == []

        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_without_trends)

        text = summary.summary_text

        # Should NOT have trend sections
        assert "Recurring Issues" not in text
        assert "Downtime Drivers" not in text
        assert "points from last week" not in text

        # Should still have existing sections
        assert "**Safety**" in text or "**Productivity**" in text

    def test_UNIT_040_fallback_partial_trends(self, sample_trend_data):
        """
        14-6-ai-summary-with-trend-context-UNIT-040:
        Fallback summary with partial trend data includes only available sections.

        Given: SummaryContext has trend_data but repeat_offenders=[] and top_downtime_drivers=[]
        When:  generate_fallback_summary(context) is called
        Then:  summary_text contains WoW OEE but NOT "Recurring Issues" or "Downtime Drivers"
        """
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 78.0, "asset_id": "a1", "asset_name": "Test",
                 "financial_loss_dollars": 500, "downtime_minutes": 30, "waste_count": 5,
                 "actual_output": 800, "target_output": 1000},
            ],
            safety_events=[],
            action_items=[],
            trend_data=sample_trend_data,
            repeat_offenders=[],
            top_downtime_drivers=[],
        )

        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context)

        text = summary.summary_text
        assert "81.2%" in text
        assert "Recurring Issues" not in text
        assert "Downtime Drivers" not in text

    def test_UNIT_041_fallback_metadata_fields(self, context_with_trends):
        """
        14-6-ai-summary-with-trend-context-UNIT-041:
        Fallback summary is_fallback=True and model_used="fallback_template".

        Given: SummaryContext with all trend fields populated
        When:  generate_fallback_summary(context) is called
        Then:  is_fallback=True and model_used="fallback_template"
               Trend data in context does not change these metadata fields
        """
        # Verify context has trend data (will fail until SummaryContext updated)
        assert context_with_trends.trend_data is not None
        assert len(context_with_trends.repeat_offenders) > 0
        assert len(context_with_trends.top_downtime_drivers) > 0

        service = SmartSummaryService()
        summary = service.generate_fallback_summary(context_with_trends)

        assert summary.is_fallback is True
        assert summary.model_used == "fallback_template"
        # Trend data should be incorporated but not change metadata
        assert summary.prompt_tokens == 0
        assert summary.completion_tokens == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestSmartSummaryTrendIntegration:
    """Integration tests for end-to-end trend context in summary generation."""

    @pytest.mark.asyncio
    async def test_INT_001_e2e_summary_includes_wow_in_prompt(
        self, mock_supabase_client, sample_trend_data
    ):
        """
        14-6-ai-summary-with-trend-context-INT-001:
        End-to-end summary generation includes WoW OEE comparison in LLM prompt.

        Given: Supabase returns 7-day history, LLM is mocked to echo received data
        When:  generate_smart_summary(target_date) is called
        Then:  prompt sent to LLM contains "Week-over-Week OEE" and "change:" text,
               generated summary_text is non-empty
        """
        # Build a context with trend data
        context = SummaryContext(
            target_date=TARGET_DATE,
            daily_summaries=[
                {"oee_percentage": 78.0, "asset_id": "a1", "asset_name": "Grinder 5",
                 "financial_loss_dollars": 1500, "downtime_minutes": 30, "waste_count": 10,
                 "actual_output": 800, "target_output": 1000},
            ],
            safety_events=[],
            action_items=[],
            assets={"a1": {"name": "Grinder 5"}},
            target_oee=85.0,
            trend_data=sample_trend_data,
            repeat_offenders=[],
            top_downtime_drivers=[],
        )

        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_context_builder.build_context = AsyncMock(return_value=context)

        # Capture what prompt was sent to LLM
        captured_prompts = []

        mock_response = MagicMock()
        mock_response.content = (
            "Plant OEE is 81.2%, down 3.1 points from last week. "
            "[Asset: Grinder 5, OEE: 78%]"
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

        # The data prompt (HumanMessage) should contain trend context
        data_prompt = captured_prompts[-1] if captured_prompts else ""
        assert "Week-over-Week OEE" in data_prompt or "TREND CONTEXT" in data_prompt
        assert "change:" in data_prompt.lower() or "81.2" in data_prompt

    @pytest.mark.asyncio
    async def test_INT_002_e2e_no_trend_data_first_day(self, mock_supabase_client):
        """
        14-6-ai-summary-with-trend-context-INT-002:
        Full summary generation succeeds on first day of operation with no trend data.

        Given: Supabase has daily_summaries for target_date only (no prior history)
        When:  generate_smart_summary(target_date) is called with mocked LLM
        Then:  summary is generated successfully, is_fallback=False,
               summary_text does not contain trend commentary, no exceptions raised
        """
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
            trend_data=None,
            repeat_offenders=[],
            top_downtime_drivers=[],
        )

        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_context_builder.build_context = AsyncMock(return_value=context)

        mock_response = MagicMock()
        mock_response.content = "Production data summary for first day of operation."
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
        # Should not contain trend commentary since no trend data
        assert "points from last week" not in summary.summary_text

        # Verify the context has trend fields (will fail until SummaryContext is updated)
        assert hasattr(context, 'trend_data')
        assert context.trend_data is None
        assert hasattr(context, 'repeat_offenders')
        assert context.repeat_offenders == []
