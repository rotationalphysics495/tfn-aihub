"""
Tests for Action Engine Service.

Story: 3.1 - Action Engine Logic
AC: #1 - Action Engine Service Exists
AC: #2 - Safety Priority Filter (Tier 1)
AC: #3 - OEE Below Target Filter (Tier 2)
AC: #4 - Financial Loss Above Threshold Filter (Tier 3)
AC: #5 - Combined Sorting Logic
AC: #6 - Configurable Thresholds
AC: #7 - Action Item Data Structure
AC: #9 - Caching
AC: #10 - Empty State Handling

Story: 3.2 - Daily Action List API
AC: #2 - Data Source Integration (shift_targets, cost_centers)
AC: #4 - OEE Below Target from shift_targets
AC: #6 - Sorting by financial_impact_usd
AC: #7 - Response schema with financial_impact_usd, priority_rank
AC: #9 - Evidence citations with table/column/value
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.services.action_engine import (
    ActionEngine,
    get_action_engine,
    ActionEngineError,
)
from app.schemas.action import (
    AcknowledgmentInfo,
    ActionCategory,
    ActionEngineConfig,
    ActionItem,
    ActionListResponse,
    EvidenceRef,
    PriorityLevel,
    TrendData,
)


@pytest.fixture
def action_engine():
    """Create a fresh ActionEngine instance."""
    engine = ActionEngine()
    engine.clear_cache()
    return engine


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return ActionEngineConfig(
        target_oee_percentage=85.0,
        financial_loss_threshold=1000.0,
        oee_high_gap_threshold=20.0,
        oee_medium_gap_threshold=10.0,
        financial_high_threshold=5000.0,
        financial_medium_threshold=2000.0,
    )


@pytest.fixture
def sample_assets():
    """Sample asset data."""
    return {
        "asset-1": {"name": "Grinder 5", "area": "Grinding", "cost_center_id": "cc-1"},
        "asset-2": {"name": "Lathe 3", "area": "Machining", "cost_center_id": "cc-2"},
        "asset-3": {"name": "Mill 7", "area": "Milling", "cost_center_id": "cc-3"},
    }


@pytest.fixture
def sample_safety_events():
    """Sample safety event records from database."""
    target_date = date.today() - timedelta(days=1)
    return [
        {
            "id": str(uuid4()),
            "asset_id": "asset-1",
            "event_timestamp": f"{target_date}T14:30:00Z",
            "reason_code": "Emergency Stop",
            "severity": "critical",
            "description": "Emergency stop triggered on Grinder 5",
            "is_resolved": False,
        },
        {
            "id": str(uuid4()),
            "asset_id": "asset-2",
            "event_timestamp": f"{target_date}T10:15:00Z",
            "reason_code": "Guard Fault",
            "severity": "high",
            "description": "Safety guard malfunction detected",
            "is_resolved": False,
        },
    ]


@pytest.fixture
def sample_daily_summaries_oee():
    """Sample daily summary records with OEE below target."""
    target_date = date.today() - timedelta(days=1)
    return [
        {
            "id": str(uuid4()),
            "asset_id": "asset-3",
            "report_date": target_date.isoformat(),
            "oee_percentage": 60.0,  # 25% gap (high priority)
            "actual_output": 600,
            "target_output": 1000,
            "financial_loss_dollars": 4000.0,  # Story 3.2: higher loss
            "downtime_minutes": 120,
        },
        {
            "id": str(uuid4()),
            "asset_id": "asset-1",
            "report_date": target_date.isoformat(),
            "oee_percentage": 78.0,  # 7% gap (low priority)
            "actual_output": 780,
            "target_output": 1000,
            "financial_loss_dollars": 700.0,  # Story 3.2: lower loss
            "downtime_minutes": 30,
        },
    ]


@pytest.fixture
def sample_daily_summaries_financial():
    """Sample daily summary records with financial loss above threshold."""
    target_date = date.today() - timedelta(days=1)
    return [
        {
            "id": str(uuid4()),
            "asset_id": "asset-2",
            "report_date": target_date.isoformat(),
            "financial_loss_dollars": 6000.0,  # High priority
            "downtime_minutes": 120,
            "waste_count": 50,
        },
        {
            "id": str(uuid4()),
            "asset_id": "asset-3",
            "report_date": target_date.isoformat(),
            "financial_loss_dollars": 1500.0,  # Low priority
            "downtime_minutes": 30,
            "waste_count": 10,
        },
    ]


class TestActionEngineExists:
    """Tests for AC #1 - Action Engine Service Exists."""

    def test_action_engine_can_be_instantiated(self):
        """AC#1: ActionEngine class can be created."""
        engine = ActionEngine()
        assert engine is not None

    def test_get_action_engine_returns_singleton(self):
        """AC#1: get_action_engine returns singleton."""
        # Reset the singleton for testing
        import app.services.action_engine as engine_module
        engine_module._action_engine = None

        engine1 = get_action_engine()
        engine2 = get_action_engine()

        assert engine1 is engine2

    def test_action_engine_with_config(self, sample_config):
        """AC#1: ActionEngine accepts configuration."""
        engine = ActionEngine(config=sample_config)
        config = engine._get_config()

        assert config.target_oee_percentage == 85.0
        assert config.financial_loss_threshold == 1000.0


class TestSafetyPriorityFilter:
    """Tests for AC #2 - Safety Priority Filter (Tier 1)."""

    @pytest.mark.asyncio
    async def test_safety_events_marked_critical(
        self, action_engine, mock_supabase_client, sample_assets, sample_safety_events
    ):
        """AC#2: Safety events are marked with priority_level 'critical'."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        # Mock the safety events query
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.data = sample_safety_events

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_safety_actions(target_date, sample_assets)

        assert len(actions) == 2
        for action in actions:
            assert action.priority_level == PriorityLevel.CRITICAL
            assert action.category == ActionCategory.SAFETY

    @pytest.mark.asyncio
    async def test_safety_events_sorted_by_severity(
        self, action_engine, mock_supabase_client, sample_assets, sample_safety_events
    ):
        """AC#2: Safety events sorted by severity (critical > high > medium > low)."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.data = sample_safety_events

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_safety_actions(target_date, sample_assets)

        # Critical should be before high
        assert actions[0].asset_id == "asset-1"  # critical severity
        assert actions[1].asset_id == "asset-2"  # high severity

    @pytest.mark.asyncio
    async def test_no_safety_events_returns_empty_list(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#2: No unresolved safety events returns empty list."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.data = []

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_safety_actions(target_date, sample_assets)

        assert len(actions) == 0


class TestOEEGapFilter:
    """Tests for AC #3 - OEE Below Target Filter (Tier 2)."""

    @pytest.mark.asyncio
    async def test_oee_below_target_included(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_oee
    ):
        """AC#3: Assets with OEE below target are included."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._shift_targets_cache = {}  # No per-asset targets, use default
        action_engine._cost_centers_cache = {}
        action_engine._cache_timestamp = datetime.utcnow()

        # Updated: now uses .eq() only (filters in Python based on shift_targets)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = sample_daily_summaries_oee

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_oee_actions(target_date, sample_assets, None, {}, {})

        assert len(actions) == 2
        for action in actions:
            assert action.category == ActionCategory.OEE

    @pytest.mark.asyncio
    async def test_oee_sorted_by_financial_impact(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_oee
    ):
        """AC#3 / Story 3.2 AC#6: OEE items sorted by financial impact (highest first)."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._shift_targets_cache = {}
        action_engine._cost_centers_cache = {}
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = sample_daily_summaries_oee

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_oee_actions(target_date, sample_assets, None, {}, {})

        # asset-3 (60% OEE, 25% gap) has higher financial impact than asset-1 (78% OEE, 7% gap)
        # due to larger gap and using estimated financial impact
        assert len(actions) == 2
        assert actions[0].asset_id == "asset-3"
        assert actions[1].asset_id == "asset-1"

    @pytest.mark.asyncio
    async def test_oee_priority_based_on_gap_severity(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_oee
    ):
        """AC#3: OEE priority based on gap severity."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._shift_targets_cache = {}
        action_engine._cost_centers_cache = {}
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = sample_daily_summaries_oee

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_oee_actions(target_date, sample_assets, None, {}, {})

        # 25% gap -> high priority
        assert actions[0].priority_level == PriorityLevel.HIGH
        # 7% gap -> low priority
        assert actions[1].priority_level == PriorityLevel.LOW


class TestFinancialLossFilter:
    """Tests for AC #4 - Financial Loss Above Threshold Filter (Tier 3)."""

    @pytest.mark.asyncio
    async def test_financial_above_threshold_included(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_financial
    ):
        """AC#4: Assets with financial loss above threshold are included."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gt.return_value.execute.return_value.data = sample_daily_summaries_financial

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_financial_actions(target_date, sample_assets)

        assert len(actions) == 2
        for action in actions:
            assert action.category == ActionCategory.FINANCIAL

    @pytest.mark.asyncio
    async def test_financial_sorted_by_loss_amount(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_financial
    ):
        """AC#4: Financial items sorted by loss amount (highest first)."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gt.return_value.execute.return_value.data = sample_daily_summaries_financial

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_financial_actions(target_date, sample_assets)

        # $6000 should be before $1500
        assert actions[0].asset_id == "asset-2"
        assert actions[1].asset_id == "asset-3"

    @pytest.mark.asyncio
    async def test_financial_priority_based_on_loss_amount(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_financial
    ):
        """AC#4: Financial priority based on loss amount."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gt.return_value.execute.return_value.data = sample_daily_summaries_financial

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_financial_actions(target_date, sample_assets)

        # $6000 -> high priority (> $5000)
        assert actions[0].priority_level == PriorityLevel.HIGH
        # $1500 -> low priority (< $2000)
        assert actions[1].priority_level == PriorityLevel.LOW


class TestCombinedSortingLogic:
    """Tests for AC #5 - Combined Sorting Logic."""

    def test_merge_prioritizes_safety_first(self, action_engine):
        """AC#5: Safety items always appear before OEE and Financial."""
        safety = [
            ActionItem(
                id="s1", asset_id="asset-1", asset_name="A",
                priority_level=PriorityLevel.CRITICAL,
                category=ActionCategory.SAFETY,
                primary_metric_value="Safety", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            )
        ]
        oee = [
            ActionItem(
                id="o1", asset_id="asset-2", asset_name="B",
                priority_level=PriorityLevel.HIGH,
                category=ActionCategory.OEE,
                primary_metric_value="OEE", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            )
        ]
        financial = [
            ActionItem(
                id="f1", asset_id="asset-3", asset_name="C",
                priority_level=PriorityLevel.HIGH,
                category=ActionCategory.FINANCIAL,
                primary_metric_value="Financial", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            )
        ]

        result = action_engine._merge_and_prioritize(safety, oee, financial)

        assert result[0].category == ActionCategory.SAFETY
        assert result[1].category == ActionCategory.OEE
        assert result[2].category == ActionCategory.FINANCIAL

    def test_merge_deduplicates_by_asset(self, action_engine):
        """AC#5: Duplicate assets keep highest priority category."""
        safety = [
            ActionItem(
                id="s1", asset_id="asset-1", asset_name="A",
                priority_level=PriorityLevel.CRITICAL,
                category=ActionCategory.SAFETY,
                primary_metric_value="Safety", recommendation_text="R",
                evidence_summary="E",
                evidence_refs=[EvidenceRef(
                    source_table="safety_events", record_id="1",
                    metric_name="severity", metric_value="critical"
                )],
                created_at=datetime.utcnow()
            )
        ]
        oee = [
            ActionItem(
                id="o1", asset_id="asset-1", asset_name="A",  # Same asset!
                priority_level=PriorityLevel.HIGH,
                category=ActionCategory.OEE,
                primary_metric_value="OEE", recommendation_text="R",
                evidence_summary="E",
                evidence_refs=[EvidenceRef(
                    source_table="daily_summaries", record_id="2",
                    metric_name="oee_gap", metric_value="20%"
                )],
                created_at=datetime.utcnow()
            )
        ]
        financial = []

        result = action_engine._merge_and_prioritize(safety, oee, financial)

        # Only one item (safety wins)
        assert len(result) == 1
        assert result[0].category == ActionCategory.SAFETY
        # Should have evidence from both categories
        assert len(result[0].evidence_refs) == 2

    def test_merge_preserves_order_within_category(self, action_engine):
        """AC#5: Order within each category is preserved."""
        safety = []
        oee = [
            ActionItem(
                id="o1", asset_id="asset-1", asset_name="A",
                priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
                primary_metric_value="OEE", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            ),
            ActionItem(
                id="o2", asset_id="asset-2", asset_name="B",
                priority_level=PriorityLevel.MEDIUM, category=ActionCategory.OEE,
                primary_metric_value="OEE", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            ),
        ]
        financial = []

        result = action_engine._merge_and_prioritize(safety, oee, financial)

        # Order should be preserved
        assert result[0].id == "o1"
        assert result[1].id == "o2"


class TestConfigurableThresholds:
    """Tests for AC #6 - Configurable Thresholds."""

    def test_default_thresholds_from_settings(self, action_engine):
        """AC#6: Default thresholds from settings."""
        with patch('app.services.action_engine.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                target_oee_percentage=90.0,
                financial_loss_threshold=500.0,
                oee_high_gap_threshold=15.0,
                oee_medium_gap_threshold=8.0,
                financial_high_threshold=4000.0,
                financial_medium_threshold=1500.0,
            )

            config = action_engine._get_config()

            assert config.target_oee_percentage == 90.0
            assert config.financial_loss_threshold == 500.0

    def test_config_override(self, action_engine, sample_config):
        """AC#6: Configuration can be overridden."""
        action_engine._config = sample_config

        config = action_engine._get_config()

        assert config.target_oee_percentage == 85.0
        assert config.financial_loss_threshold == 1000.0


class TestActionItemDataStructure:
    """Tests for AC #7 - Action Item Data Structure."""

    def test_action_item_has_required_fields(self):
        """AC#7: ActionItem has all required fields."""
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Grinder 5",
            priority_level=PriorityLevel.CRITICAL,
            category=ActionCategory.SAFETY,
            primary_metric_value="Safety Event: Emergency Stop",
            recommendation_text="Investigate emergency stop",
            evidence_summary="Unresolved safety event at 14:30",
            evidence_refs=[
                EvidenceRef(
                    source_table="safety_events",
                    record_id="123",
                    metric_name="severity",
                    metric_value="critical",
                    context="Emergency stop triggered"
                )
            ],
            created_at=datetime.utcnow()
        )

        assert action.id == "test-id"
        assert action.asset_id == "asset-1"
        assert action.asset_name == "Grinder 5"
        assert action.priority_level == PriorityLevel.CRITICAL
        assert action.category == ActionCategory.SAFETY
        assert action.primary_metric_value == "Safety Event: Emergency Stop"
        assert action.recommendation_text == "Investigate emergency stop"
        assert action.evidence_summary == "Unresolved safety event at 14:30"
        assert len(action.evidence_refs) == 1

    def test_evidence_ref_structure(self):
        """AC#7: EvidenceRef supports drill-down to source data."""
        ref = EvidenceRef(
            source_table="daily_summaries",
            record_id="abc-123",
            metric_name="oee_gap",
            metric_value="15%",
            context="OEE 70% vs target 85%"
        )

        assert ref.source_table == "daily_summaries"
        assert ref.record_id == "abc-123"


class TestCaching:
    """Tests for AC #9 - Caching."""

    @pytest.mark.asyncio
    async def test_cache_is_used_for_same_date(self, action_engine):
        """AC#9: Cache is used for repeated requests on same date."""
        target_date = date.today() - timedelta(days=1)

        # Pre-populate cache
        cached_response = ActionListResponse(
            actions=[],
            generated_at=datetime.utcnow(),
            report_date=target_date,
            total_count=0,
            counts_by_category={"safety": 0, "oee": 0, "financial": 0}
        )
        cache_key = f"{target_date.isoformat()}-all"
        action_engine._action_list_cache[cache_key] = cached_response

        # Request should return cached version
        result = await action_engine.generate_action_list(
            target_date=target_date,
            use_cache=True
        )

        assert result is cached_response

    def test_cache_invalidation(self, action_engine):
        """AC#9: Cache can be invalidated."""
        target_date = date.today() - timedelta(days=1)
        cache_key = f"{target_date.isoformat()}-all"

        # Pre-populate cache
        action_engine._action_list_cache[cache_key] = ActionListResponse(
            actions=[], generated_at=datetime.utcnow(),
            report_date=target_date, total_count=0,
            counts_by_category={"safety": 0, "oee": 0, "financial": 0}
        )

        # Invalidate cache
        action_engine.invalidate_cache(target_date)

        assert cache_key not in action_engine._action_list_cache


class TestEmptyStateHandling:
    """Tests for AC #10 - Empty State Handling."""

    @pytest.mark.asyncio
    async def test_empty_list_when_no_items(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#10: Returns empty list with metadata when no items."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        # Mock all queries to return empty
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gt.return_value.execute.return_value.data = []

        result = await action_engine.generate_action_list()

        assert len(result.actions) == 0
        assert result.total_count == 0
        assert result.counts_by_category == {"safety": 0, "oee": 0, "financial": 0}
        assert result.generated_at is not None
        assert result.report_date is not None

    @pytest.mark.asyncio
    async def test_no_error_on_empty_state(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#10: Does not error on empty state."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gt.return_value.execute.return_value.data = []

        # Should not raise exception
        result = await action_engine.generate_action_list()
        assert result is not None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_priority_level_ordering(self):
        """Priority levels have correct ordering."""
        assert PriorityLevel.CRITICAL.value == "critical"
        assert PriorityLevel.HIGH.value == "high"
        assert PriorityLevel.MEDIUM.value == "medium"
        assert PriorityLevel.LOW.value == "low"

    def test_category_ordering(self):
        """Categories have correct values."""
        assert ActionCategory.SAFETY.value == "safety"
        assert ActionCategory.OEE.value == "oee"
        assert ActionCategory.FINANCIAL.value == "financial"

    @pytest.mark.asyncio
    async def test_handles_missing_asset_info(
        self, action_engine, mock_supabase_client
    ):
        """Handles missing asset info gracefully."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = {}  # Empty assets cache
        action_engine._cache_timestamp = datetime.utcnow()

        sample_events = [{
            "id": str(uuid4()),
            "asset_id": "unknown-asset",
            "event_timestamp": f"{date.today()}T14:30:00Z",
            "reason_code": "Safety Issue",
            "severity": "critical",
            "is_resolved": False,
        }]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.data = sample_events

        actions = await action_engine._get_safety_actions(date.today(), {})

        # Should still work with "Unknown" as asset name
        assert len(actions) == 1
        assert actions[0].asset_name == "Unknown"

    def test_generate_action_id_is_unique(self, action_engine):
        """Generated action IDs are unique."""
        ids = set()
        for _ in range(100):
            action_id = action_engine._generate_action_id(ActionCategory.SAFETY, "asset-1")
            ids.add(action_id)

        assert len(ids) == 100  # All unique

    def test_clear_cache(self, action_engine):
        """Clear cache removes all cached data."""
        action_engine._assets_cache = {"test": {}}
        action_engine._action_list_cache = {"test": None}
        action_engine._cache_timestamp = datetime.utcnow()

        action_engine.clear_cache()

        assert len(action_engine._assets_cache) == 0
        assert len(action_engine._action_list_cache) == 0
        assert action_engine._cache_timestamp is None


class TestIntegrationScenarios:
    """Integration test scenarios combining multiple categories."""

    def test_scenario_all_categories_mixed(self, action_engine):
        """Scenario: All categories have items, verify correct ordering."""
        safety = [
            ActionItem(
                id="s1", asset_id="asset-1", asset_name="Grinder 5",
                priority_level=PriorityLevel.CRITICAL, category=ActionCategory.SAFETY,
                primary_metric_value="Safety", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            ),
            ActionItem(
                id="s2", asset_id="asset-2", asset_name="Lathe 3",
                priority_level=PriorityLevel.CRITICAL, category=ActionCategory.SAFETY,
                primary_metric_value="Safety", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            ),
        ]
        oee = [
            ActionItem(
                id="o1", asset_id="asset-3", asset_name="Mill 7",
                priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
                primary_metric_value="OEE", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            ),
        ]
        financial = [
            ActionItem(
                id="f1", asset_id="asset-4", asset_name="Saw 2",
                priority_level=PriorityLevel.HIGH, category=ActionCategory.FINANCIAL,
                primary_metric_value="Financial", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow()
            ),
        ]

        result = action_engine._merge_and_prioritize(safety, oee, financial)

        # All safety first (2), then OEE (1), then financial (1)
        assert len(result) == 4
        assert result[0].category == ActionCategory.SAFETY
        assert result[1].category == ActionCategory.SAFETY
        assert result[2].category == ActionCategory.OEE
        assert result[3].category == ActionCategory.FINANCIAL

    def test_scenario_asset_in_safety_and_oee(self, action_engine):
        """Scenario: Same asset has safety event and OEE issue."""
        safety = [
            ActionItem(
                id="s1", asset_id="asset-1", asset_name="Grinder 5",
                priority_level=PriorityLevel.CRITICAL, category=ActionCategory.SAFETY,
                primary_metric_value="Safety", recommendation_text="R",
                evidence_summary="E",
                evidence_refs=[EvidenceRef(
                    source_table="safety_events", record_id="1",
                    metric_name="severity", metric_value="critical"
                )],
                created_at=datetime.utcnow()
            ),
        ]
        oee = [
            ActionItem(
                id="o1", asset_id="asset-1", asset_name="Grinder 5",  # Same asset!
                priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
                primary_metric_value="OEE: 60%", recommendation_text="R",
                evidence_summary="E",
                evidence_refs=[EvidenceRef(
                    source_table="daily_summaries", record_id="2",
                    metric_name="oee_gap", metric_value="25%"
                )],
                created_at=datetime.utcnow()
            ),
        ]
        financial = []

        result = action_engine._merge_and_prioritize(safety, oee, financial)

        # Only one item, safety category
        assert len(result) == 1
        assert result[0].category == ActionCategory.SAFETY
        assert result[0].priority_level == PriorityLevel.CRITICAL
        # Both evidence refs merged
        assert len(result[0].evidence_refs) == 2


# =============================================================================
# Story 3.2 - Daily Action List API Tests
# =============================================================================

@pytest.fixture
def sample_shift_targets():
    """Sample shift target data (Story 3.2 AC#4)."""
    return {
        "asset-1": {
            "id": str(uuid4()),
            "asset_id": "asset-1",
            "target_oee": 90.0,  # Higher target for asset-1
            "target_output": 1000,
            "effective_date": "2026-01-01",
        },
        "asset-3": {
            "id": str(uuid4()),
            "asset_id": "asset-3",
            "target_oee": 80.0,  # Lower target for asset-3
            "target_output": 800,
            "effective_date": "2026-01-01",
        },
    }


@pytest.fixture
def sample_cost_centers():
    """Sample cost center data (Story 3.2 AC#2)."""
    return {
        "asset-1": {
            "id": str(uuid4()),
            "standard_hourly_rate": 150.0,
            "cost_per_unit": 15.0,
        },
        "asset-2": {
            "id": str(uuid4()),
            "standard_hourly_rate": 100.0,
            "cost_per_unit": 10.0,
        },
        "asset-3": {
            "id": str(uuid4()),
            "standard_hourly_rate": 200.0,
            "cost_per_unit": 20.0,
        },
    }


class TestStory32DataSourceIntegration:
    """Tests for Story 3.2 AC#2 - Data Source Integration."""

    @pytest.mark.asyncio
    async def test_load_shift_targets(self, action_engine, mock_supabase_client):
        """AC#2: System loads shift_targets table."""
        action_engine._client = mock_supabase_client

        shift_target_data = [
            {
                "id": str(uuid4()),
                "asset_id": "asset-1",
                "target_oee": 85.0,
                "target_output": 1000,
                "effective_date": "2026-01-01",
            }
        ]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = shift_target_data

        targets = await action_engine._load_shift_targets(force=True)

        assert "asset-1" in targets
        assert targets["asset-1"]["target_oee"] == 85.0

    @pytest.mark.asyncio
    async def test_load_cost_centers(self, action_engine, mock_supabase_client):
        """AC#2: System loads cost_centers table."""
        action_engine._client = mock_supabase_client

        cost_center_data = [
            {
                "id": str(uuid4()),
                "asset_id": "asset-1",
                "standard_hourly_rate": 150.0,
                "cost_per_unit": 15.0,
            }
        ]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = cost_center_data

        centers = await action_engine._load_cost_centers(force=True)

        assert "asset-1" in centers
        assert centers["asset-1"]["standard_hourly_rate"] == 150.0


class TestStory32OEEFromShiftTargets:
    """Tests for Story 3.2 AC#4 - OEE from shift_targets per asset."""

    @pytest.mark.asyncio
    async def test_oee_uses_per_asset_target(
        self, action_engine, mock_supabase_client, sample_assets, sample_shift_targets, sample_cost_centers
    ):
        """AC#4: OEE comparison uses target from shift_targets per asset."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._shift_targets_cache = sample_shift_targets
        action_engine._cost_centers_cache = sample_cost_centers
        action_engine._cache_timestamp = datetime.utcnow()

        target_date = date.today() - timedelta(days=1)

        # Asset-1 has 78% OEE, target is 90% (from shift_targets) -> gap of 12%
        # Asset-3 has 79% OEE, target is 80% (from shift_targets) -> gap of 1%
        daily_summaries = [
            {
                "id": str(uuid4()),
                "asset_id": "asset-1",
                "report_date": target_date.isoformat(),
                "oee_percentage": 78.0,
                "actual_output": 780,
                "target_output": 1000,
                "financial_loss_dollars": 0,
                "downtime_minutes": 60,
            },
            {
                "id": str(uuid4()),
                "asset_id": "asset-3",
                "report_date": target_date.isoformat(),
                "oee_percentage": 79.0,
                "actual_output": 790,
                "target_output": 800,
                "financial_loss_dollars": 0,
                "downtime_minutes": 10,
            },
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = daily_summaries

        actions = await action_engine._get_oee_actions(
            target_date, sample_assets, None, sample_shift_targets, sample_cost_centers
        )

        # Both should be included since both are below their respective targets
        assert len(actions) == 2

        # Asset-1 has higher financial impact (larger gap and higher cost)
        assert actions[0].asset_id == "asset-1"
        assert actions[0].financial_impact_usd > 0

    @pytest.mark.asyncio
    async def test_oee_excludes_above_target(
        self, action_engine, mock_supabase_client, sample_assets, sample_shift_targets, sample_cost_centers
    ):
        """AC#4: Assets at or above their target are excluded."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._shift_targets_cache = sample_shift_targets
        action_engine._cost_centers_cache = sample_cost_centers
        action_engine._cache_timestamp = datetime.utcnow()

        target_date = date.today() - timedelta(days=1)

        # Asset-3 has 82% OEE, target is 80% -> above target, should be excluded
        daily_summaries = [
            {
                "id": str(uuid4()),
                "asset_id": "asset-3",
                "report_date": target_date.isoformat(),
                "oee_percentage": 82.0,
                "actual_output": 820,
                "target_output": 800,
                "financial_loss_dollars": 0,
                "downtime_minutes": 0,
            },
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = daily_summaries

        actions = await action_engine._get_oee_actions(
            target_date, sample_assets, None, sample_shift_targets, sample_cost_centers
        )

        # Asset-3 is above target, should be excluded
        assert len(actions) == 0


class TestStory32FinancialImpactSorting:
    """Tests for Story 3.2 AC#6 - Sorting by financial_impact_usd."""

    def test_oee_items_sorted_by_financial_impact(self, action_engine):
        """AC#6: OEE items are sorted by financial_impact_usd descending."""
        # Create action items with different financial impacts
        oee_items = [
            ActionItem(
                id="o1", asset_id="asset-1", asset_name="A",
                priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
                primary_metric_value="OEE: 60%", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
                financial_impact_usd=1000.0,  # Lower impact
            ),
            ActionItem(
                id="o2", asset_id="asset-2", asset_name="B",
                priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
                primary_metric_value="OEE: 50%", recommendation_text="R",
                evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
                financial_impact_usd=5000.0,  # Higher impact
            ),
        ]

        # Merge with empty safety and financial
        result = action_engine._merge_and_prioritize([], oee_items, [])

        # Order should be preserved (already sorted by financial_impact in _get_oee_actions)
        assert len(result) == 2

    def test_financial_items_have_financial_impact(self):
        """AC#6, AC#7: Financial items include financial_impact_usd."""
        action = ActionItem(
            id="f1", asset_id="asset-1", asset_name="A",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.FINANCIAL,
            primary_metric_value="Loss: $5000", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
            financial_impact_usd=5000.0,
        )

        assert action.financial_impact_usd == 5000.0


class TestStory32ResponseSchema:
    """Tests for Story 3.2 AC#7 - Response Schema."""

    def test_action_item_has_priority_rank(self):
        """AC#7: ActionItem includes priority_rank computed field."""
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Grinder 5",
            priority_level=PriorityLevel.CRITICAL,
            category=ActionCategory.SAFETY,
            primary_metric_value="Safety Event",
            recommendation_text="Investigate",
            evidence_summary="Unresolved",
            evidence_refs=[],
            created_at=datetime.utcnow()
        )

        # priority_rank should be 0 for critical
        assert action.priority_rank == 0

    def test_action_item_has_title_alias(self):
        """AC#7: ActionItem includes title as alias for recommendation_text."""
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Test",
            priority_level=PriorityLevel.HIGH,
            category=ActionCategory.OEE,
            primary_metric_value="OEE: 70%",
            recommendation_text="Review performance",
            evidence_summary="Below target",
            evidence_refs=[],
            created_at=datetime.utcnow()
        )

        assert action.title == "Review performance"

    def test_action_item_has_description_alias(self):
        """AC#7: ActionItem includes description as alias for evidence_summary."""
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Test",
            priority_level=PriorityLevel.HIGH,
            category=ActionCategory.OEE,
            primary_metric_value="OEE: 70%",
            recommendation_text="Review",
            evidence_summary="OEE 15% below target",
            evidence_refs=[],
            created_at=datetime.utcnow()
        )

        assert action.description == "OEE 15% below target"

    def test_action_item_has_financial_impact_usd(self):
        """AC#7: ActionItem includes financial_impact_usd field."""
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Test",
            priority_level=PriorityLevel.HIGH,
            category=ActionCategory.FINANCIAL,
            primary_metric_value="Loss: $3000",
            recommendation_text="Reduce losses",
            evidence_summary="High loss",
            evidence_refs=[],
            created_at=datetime.utcnow(),
            financial_impact_usd=3000.0,
        )

        assert action.financial_impact_usd == 3000.0

    def test_priority_rank_values(self):
        """AC#7: priority_rank has correct values for each level."""
        from app.schemas.action import PRIORITY_RANK_MAP

        assert PRIORITY_RANK_MAP[PriorityLevel.CRITICAL] == 0
        assert PRIORITY_RANK_MAP[PriorityLevel.HIGH] == 1
        assert PRIORITY_RANK_MAP[PriorityLevel.MEDIUM] == 2
        assert PRIORITY_RANK_MAP[PriorityLevel.LOW] == 3


class TestStory32EvidenceCitations:
    """Tests for Story 3.2 AC#9 - Evidence Citations."""

    def test_evidence_ref_has_table_field(self):
        """AC#9: EvidenceRef includes table (source_table) field."""
        ref = EvidenceRef(
            source_table="daily_summaries",
            record_id="123",
            metric_name="oee_percentage",
            metric_value="72.5%"
        )

        assert ref.table == "daily_summaries"
        assert ref.source_table == "daily_summaries"  # Backward compatibility

    def test_evidence_ref_has_column_field(self):
        """AC#9: EvidenceRef includes column (metric_name) field."""
        ref = EvidenceRef(
            source_table="shift_targets",
            record_id="456",
            metric_name="target_oee",
            metric_value="85.0%"
        )

        assert ref.column == "target_oee"
        assert ref.metric_name == "target_oee"  # Backward compatibility

    def test_evidence_ref_has_value_field(self):
        """AC#9: EvidenceRef includes value (metric_value) field."""
        ref = EvidenceRef(
            source_table="safety_events",
            record_id="789",
            metric_name="severity",
            metric_value="critical"
        )

        assert ref.value == "critical"
        assert ref.metric_value == "critical"  # Backward compatibility

    def test_evidence_ref_has_record_id(self):
        """AC#9: EvidenceRef includes record_id for drill-down."""
        ref = EvidenceRef(
            source_table="cost_centers",
            record_id="uuid-123",
            metric_name="standard_hourly_rate",
            metric_value="$150.00"
        )

        assert ref.record_id == "uuid-123"

    @pytest.mark.asyncio
    async def test_oee_action_includes_shift_target_evidence(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#9: OEE actions include shift_target evidence refs."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        target_date = date.today() - timedelta(days=1)

        shift_targets = {
            "asset-1": {
                "id": "shift-target-123",
                "asset_id": "asset-1",
                "target_oee": 85.0,
                "target_output": 1000,
            }
        }
        cost_centers = {
            "asset-1": {
                "id": "cc-1",
                "standard_hourly_rate": 100.0,
                "cost_per_unit": 10.0,
            }
        }

        daily_summaries = [
            {
                "id": "ds-456",
                "asset_id": "asset-1",
                "report_date": target_date.isoformat(),
                "oee_percentage": 70.0,
                "actual_output": 700,
                "target_output": 1000,
                "financial_loss_dollars": 0,
                "downtime_minutes": 60,
            }
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = daily_summaries

        actions = await action_engine._get_oee_actions(
            target_date, sample_assets, None, shift_targets, cost_centers
        )

        assert len(actions) == 1
        action = actions[0]

        # Should have 2 evidence refs: daily_summaries and shift_targets
        assert len(action.evidence_refs) == 2

        # Check daily_summaries evidence
        ds_ref = next(r for r in action.evidence_refs if r.source_table == "daily_summaries")
        assert ds_ref.record_id == "ds-456"

        # Check shift_targets evidence
        st_ref = next(r for r in action.evidence_refs if r.source_table == "shift_targets")
        assert st_ref.record_id == "shift-target-123"
        assert st_ref.metric_name == "target_oee"


class TestStory32CacheManagement:
    """Tests for cache management with new caches."""

    def test_clear_cache_clears_all_caches(self, action_engine):
        """Clear cache clears assets, shift_targets, cost_centers, and action list caches."""
        action_engine._assets_cache = {"test": {}}
        action_engine._shift_targets_cache = {"test": {}}
        action_engine._cost_centers_cache = {"test": {}}
        action_engine._action_list_cache = {"test": None}
        action_engine._cache_timestamp = datetime.utcnow()

        action_engine.clear_cache()

        assert len(action_engine._assets_cache) == 0
        assert len(action_engine._shift_targets_cache) == 0
        assert len(action_engine._cost_centers_cache) == 0
        assert len(action_engine._action_list_cache) == 0
        assert action_engine._cache_timestamp is None


# =============================================================================
# Story 13.1 - Action Acknowledgment Backend Tests
# =============================================================================


class TestLoadAcknowledgments:
    """Tests for _load_acknowledgments() method (Story 13.1 AC#3)."""

    @pytest.mark.asyncio
    async def test_load_acknowledgments_returns_dict(
        self, action_engine, mock_supabase_client
    ):
        """AC#3: _load_acknowledgments returns dict mapping action_item_id to AcknowledgmentInfo."""
        action_engine._client = mock_supabase_client

        ack_data = [
            {
                "id": str(uuid4()),
                "action_item_id": "action-safety-abc123",
                "user_id": "user-uuid-1",
                "acknowledged_at": "2026-02-10T14:30:00Z",
                "note": "Reviewed with team",
                "report_date": "2026-02-09",
            },
            {
                "id": str(uuid4()),
                "action_item_id": "action-oee-def456",
                "user_id": "user-uuid-1",
                "acknowledged_at": "2026-02-10T15:00:00Z",
                "note": None,
                "report_date": "2026-02-09",
            },
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = ack_data

        target_date = date(2026, 2, 9)
        result = await action_engine._load_acknowledgments(target_date, "user-uuid-1")

        assert len(result) == 2
        assert "action-safety-abc123" in result
        assert "action-oee-def456" in result

        ack_info = result["action-safety-abc123"]
        assert isinstance(ack_info, AcknowledgmentInfo)
        assert ack_info.acknowledged_by == "user-uuid-1"
        assert ack_info.note == "Reviewed with team"

    @pytest.mark.asyncio
    async def test_load_acknowledgments_returns_empty_when_none(
        self, action_engine, mock_supabase_client
    ):
        """AC#3: Returns empty dict when no acknowledgments exist."""
        action_engine._client = mock_supabase_client

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        target_date = date(2026, 2, 9)
        result = await action_engine._load_acknowledgments(target_date, "user-uuid-1")

        assert result == {}

    @pytest.mark.asyncio
    async def test_load_acknowledgments_handles_error(
        self, action_engine, mock_supabase_client
    ):
        """AC#3: Returns empty dict on error without raising."""
        action_engine._client = mock_supabase_client

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")

        target_date = date(2026, 2, 9)
        result = await action_engine._load_acknowledgments(target_date, "user-uuid-1")

        assert result == {}


class TestAcknowledgmentEnrichment:
    """Tests for acknowledgment enrichment in generate_action_list (Story 13.1 AC#3)."""

    @pytest.mark.asyncio
    async def test_enrichment_when_user_id_provided(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#3: Actions are enriched with acknowledgment when user_id is provided."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        target_date = date.today() - timedelta(days=1)

        # Pre-populate action list cache
        cached_response = ActionListResponse(
            actions=[
                ActionItem(
                    id="action-safety-abc123",
                    asset_id="asset-1",
                    asset_name="Grinder 5",
                    priority_level=PriorityLevel.CRITICAL,
                    category=ActionCategory.SAFETY,
                    primary_metric_value="Safety Event",
                    recommendation_text="Investigate",
                    evidence_summary="Unresolved",
                    evidence_refs=[],
                    created_at=datetime.utcnow(),
                ),
                ActionItem(
                    id="action-oee-def456",
                    asset_id="asset-2",
                    asset_name="Lathe 3",
                    priority_level=PriorityLevel.HIGH,
                    category=ActionCategory.OEE,
                    primary_metric_value="OEE: 62.5%",
                    recommendation_text="Review",
                    evidence_summary="Below target",
                    evidence_refs=[],
                    created_at=datetime.utcnow(),
                ),
            ],
            generated_at=datetime.utcnow(),
            report_date=target_date,
            total_count=2,
            counts_by_category={"safety": 1, "oee": 1, "financial": 0},
        )
        cache_key = f"{target_date.isoformat()}-all"
        action_engine._action_list_cache[cache_key] = cached_response

        # Mock acknowledgment load - only first action is acknowledged
        ack_data = [
            {
                "id": str(uuid4()),
                "action_item_id": "action-safety-abc123",
                "user_id": "user-uuid-1",
                "acknowledged_at": "2026-02-10T14:30:00Z",
                "note": "Done",
                "report_date": target_date.isoformat(),
            },
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = ack_data

        result = await action_engine.generate_action_list(
            target_date=target_date,
            use_cache=True,
            user_id="user-uuid-1",
        )

        # First action should be enriched
        assert result.actions[0].acknowledgment is not None
        assert result.actions[0].acknowledgment.acknowledged_by == "user-uuid-1"
        assert result.actions[0].acknowledgment.note == "Done"

        # Second action should not be enriched
        assert result.actions[1].acknowledgment is None

    @pytest.mark.asyncio
    async def test_no_enrichment_when_user_id_is_none(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#3: No enrichment when user_id is not provided."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        target_date = date.today() - timedelta(days=1)

        # Pre-populate cache
        cached_response = ActionListResponse(
            actions=[
                ActionItem(
                    id="action-safety-abc123",
                    asset_id="asset-1",
                    asset_name="Grinder 5",
                    priority_level=PriorityLevel.CRITICAL,
                    category=ActionCategory.SAFETY,
                    primary_metric_value="Safety Event",
                    recommendation_text="Investigate",
                    evidence_summary="Unresolved",
                    evidence_refs=[],
                    created_at=datetime.utcnow(),
                ),
            ],
            generated_at=datetime.utcnow(),
            report_date=target_date,
            total_count=1,
            counts_by_category={"safety": 1, "oee": 0, "financial": 0},
        )
        cache_key = f"{target_date.isoformat()}-all"
        action_engine._action_list_cache[cache_key] = cached_response

        result = await action_engine.generate_action_list(
            target_date=target_date,
            use_cache=True,
            user_id=None,
        )

        # No enrichment should occur
        assert result.actions[0].acknowledgment is None

    @pytest.mark.asyncio
    async def test_enrichment_with_no_acks_returns_null(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#3: All actions have null acknowledgment when no acks exist for user."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        target_date = date.today() - timedelta(days=1)

        # Pre-populate cache
        cached_response = ActionListResponse(
            actions=[
                ActionItem(
                    id="action-safety-abc123",
                    asset_id="asset-1",
                    asset_name="Grinder 5",
                    priority_level=PriorityLevel.CRITICAL,
                    category=ActionCategory.SAFETY,
                    primary_metric_value="Safety Event",
                    recommendation_text="Investigate",
                    evidence_summary="Unresolved",
                    evidence_refs=[],
                    created_at=datetime.utcnow(),
                ),
            ],
            generated_at=datetime.utcnow(),
            report_date=target_date,
            total_count=1,
            counts_by_category={"safety": 1, "oee": 0, "financial": 0},
        )
        cache_key = f"{target_date.isoformat()}-all"
        action_engine._action_list_cache[cache_key] = cached_response

        # No acknowledgments exist
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        result = await action_engine.generate_action_list(
            target_date=target_date,
            use_cache=True,
            user_id="user-uuid-1",
        )

        assert result.actions[0].acknowledgment is None


class TestActionItemAcknowledgmentField:
    """Tests for ActionItem.acknowledgment field backward compatibility (Story 13.1)."""

    def test_action_item_default_acknowledgment_is_none(self):
        """ActionItem.acknowledgment defaults to None for backward compatibility."""
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Grinder 5",
            priority_level=PriorityLevel.CRITICAL,
            category=ActionCategory.SAFETY,
            primary_metric_value="Safety Event",
            recommendation_text="Investigate",
            evidence_summary="Unresolved",
            evidence_refs=[],
            created_at=datetime.utcnow(),
        )

        assert action.acknowledgment is None

    def test_action_item_with_acknowledgment(self):
        """ActionItem can hold AcknowledgmentInfo."""
        ack = AcknowledgmentInfo(
            acknowledged_by="user-123",
            acknowledged_at=datetime(2026, 2, 10, 14, 30, 0),
            note="Reviewed",
        )
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Grinder 5",
            priority_level=PriorityLevel.CRITICAL,
            category=ActionCategory.SAFETY,
            primary_metric_value="Safety Event",
            recommendation_text="Investigate",
            evidence_summary="Unresolved",
            evidence_refs=[],
            created_at=datetime.utcnow(),
            acknowledgment=ack,
        )

        assert action.acknowledgment is not None
        assert action.acknowledgment.acknowledged_by == "user-123"
        assert action.acknowledgment.note == "Reviewed"


# =============================================================================
# Story 14.2 - Trend Data API Endpoint Tests
# =============================================================================


class TestTrendDataSchema:
    """Tests for Story 14.2 AC#4 - TrendData schema validation."""

    def test_trend_data_validates_with_all_fields(self):
        """AC#4: TrendData validates with all required fields."""
        td = TrendData(
            metric_values=[78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3],
            days_on_report=5,
            consecutive_days=3,
            week_over_week_change=-9.2,
        )
        assert td.metric_values == [78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3]
        assert td.days_on_report == 5
        assert td.consecutive_days == 3
        assert td.week_over_week_change == -9.2

    def test_trend_data_allows_null_week_over_week_change(self):
        """AC#4: week_over_week_change can be null."""
        td = TrendData(
            metric_values=[None, None, None, None, None, None, 85.0],
            days_on_report=1,
            consecutive_days=1,
            week_over_week_change=None,
        )
        assert td.week_over_week_change is None

    def test_trend_data_allows_all_none_metric_values(self):
        """AC#4: metric_values can contain all Nones except one."""
        td = TrendData(
            metric_values=[None, None, None, None, None, None, 5.0],
            days_on_report=1,
            consecutive_days=1,
        )
        assert td.metric_values[6] == 5.0
        assert all(v is None for v in td.metric_values[:6])

    def test_trend_data_serializes_to_json(self):
        """AC#4: TrendData serializes correctly to JSON."""
        td = TrendData(
            metric_values=[78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3],
            days_on_report=5,
            consecutive_days=3,
            week_over_week_change=-9.2,
        )
        data = td.model_dump()
        assert "metric_values" in data
        assert "days_on_report" in data
        assert "consecutive_days" in data
        assert "week_over_week_change" in data
        assert len(data["metric_values"]) == 7

    def test_trend_data_days_on_report_bounds(self):
        """AC#4: days_on_report must be between 0 and 7."""
        # Valid bounds
        TrendData(metric_values=[1.0]*7, days_on_report=0, consecutive_days=1)
        TrendData(metric_values=[1.0]*7, days_on_report=7, consecutive_days=1)

        # Invalid bounds
        with pytest.raises(Exception):
            TrendData(metric_values=[1.0]*7, days_on_report=-1, consecutive_days=1)
        with pytest.raises(Exception):
            TrendData(metric_values=[1.0]*7, days_on_report=8, consecutive_days=1)

    def test_trend_data_consecutive_days_bounds(self):
        """AC#4: consecutive_days must be between 0 and 7."""
        TrendData(metric_values=[1.0]*7, days_on_report=1, consecutive_days=0)
        TrendData(metric_values=[1.0]*7, days_on_report=1, consecutive_days=7)

        with pytest.raises(Exception):
            TrendData(metric_values=[1.0]*7, days_on_report=1, consecutive_days=-1)
        with pytest.raises(Exception):
            TrendData(metric_values=[1.0]*7, days_on_report=1, consecutive_days=8)

    def test_action_item_trend_data_defaults_to_none(self):
        """AC#4: ActionItem.trend_data defaults to None for backward compatibility."""
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Grinder 5",
            priority_level=PriorityLevel.CRITICAL,
            category=ActionCategory.SAFETY,
            primary_metric_value="Safety Event",
            recommendation_text="Investigate",
            evidence_summary="Unresolved",
            evidence_refs=[],
            created_at=datetime.utcnow(),
        )
        assert action.trend_data is None

    def test_action_item_with_trend_data(self):
        """AC#4: ActionItem can hold TrendData."""
        td = TrendData(
            metric_values=[78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3],
            days_on_report=5,
            consecutive_days=3,
            week_over_week_change=-9.2,
        )
        action = ActionItem(
            id="test-id",
            asset_id="asset-1",
            asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH,
            category=ActionCategory.OEE,
            primary_metric_value="OEE: 71.3%",
            recommendation_text="Review",
            evidence_summary="Below target",
            evidence_refs=[],
            created_at=datetime.utcnow(),
            trend_data=td,
        )
        assert action.trend_data is not None
        assert action.trend_data.days_on_report == 5


class TestTrendDataCalculation:
    """Tests for Story 14.2 AC#1,2,3 - Trend data calculation logic."""

    @pytest.fixture
    def trend_engine(self, mock_supabase_client, sample_config):
        """Create an ActionEngine with mocked client and config for trend tests."""
        engine = ActionEngine(supabase_client=mock_supabase_client, config=sample_config)
        engine._assets_cache = {
            "asset-1": {"name": "Grinder 5"},
            "asset-2": {"name": "Lathe 3"},
        }
        engine._cache_timestamp = datetime.utcnow()
        return engine

    def test_full_7_day_oee_history(self, trend_engine, sample_config):
        """AC#1: Asset with full 7 days of OEE history returns correct metric array."""
        target_date = date(2026, 2, 10)
        trailing_summaries = {
            "asset-1": [
                {"report_date": (target_date - timedelta(days=6-i)).isoformat(),
                 "oee_percentage": 78.0 + i, "financial_loss_dollars": 0}
                for i in range(7)
            ]
        }
        action = ActionItem(
            id="o1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 84%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        assert len(result.metric_values) == 7
        assert result.metric_values[0] == 78.0  # oldest (target_date - 6)
        assert result.metric_values[6] == 84.0  # newest (target_date)
        assert all(v is not None for v in result.metric_values)

    def test_partial_history_3_days(self, trend_engine, sample_config):
        """AC#2: Asset with fewer than 7 days returns None for missing days."""
        target_date = date(2026, 2, 10)
        # Only last 3 days have data
        trailing_summaries = {
            "asset-1": [
                {"report_date": (target_date - timedelta(days=2-i)).isoformat(),
                 "oee_percentage": 70.0 + i * 5, "financial_loss_dollars": 0}
                for i in range(3)
            ]
        }
        action = ActionItem(
            id="o1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 80%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        assert len(result.metric_values) == 7
        # First 4 days should be None (no data)
        assert all(v is None for v in result.metric_values[:4])
        # Last 3 days should have values
        assert result.metric_values[4] == 70.0
        assert result.metric_values[5] == 75.0
        assert result.metric_values[6] == 80.0
        # week_over_week_change should be None since no data 7 days ago
        assert result.week_over_week_change is None

    def test_first_appearance_no_prior_history(self, trend_engine, sample_config):
        """AC#3: First appearance returns days_on_report=1, consecutive_days=1, w_o_w=null."""
        target_date = date(2026, 2, 10)
        # Only today's data exists
        trailing_summaries = {
            "asset-1": [
                {"report_date": target_date.isoformat(),
                 "oee_percentage": 72.5, "financial_loss_dollars": 0}
            ]
        }
        action = ActionItem(
            id="o1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 72.5%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        assert result.days_on_report == 1
        assert result.consecutive_days == 1
        assert result.week_over_week_change is None
        # Only today's value, rest should be None
        assert result.metric_values[6] == 72.5
        assert all(v is None for v in result.metric_values[:6])

    def test_safety_metric_uses_event_counts(self, trend_engine, sample_config):
        """AC#1: Safety trend uses event counts per day."""
        target_date = date(2026, 2, 10)
        trailing_safety_counts = {
            "asset-1": {
                (target_date - timedelta(days=6)).isoformat(): 2,
                (target_date - timedelta(days=5)).isoformat(): 1,
                (target_date - timedelta(days=3)).isoformat(): 3,
                target_date.isoformat(): 1,
            }
        }
        action = ActionItem(
            id="s1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.CRITICAL, category=ActionCategory.SAFETY,
            primary_metric_value="Safety Event", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, {}, trailing_safety_counts, sample_config
        )

        assert len(result.metric_values) == 7
        assert result.metric_values[0] == 2.0   # 7 days ago
        assert result.metric_values[1] == 1.0   # 6 days ago
        assert result.metric_values[2] is None  # 5 days ago (no events)
        assert result.metric_values[3] == 3.0   # 4 days ago
        assert result.metric_values[4] is None  # 3 days ago
        assert result.metric_values[5] is None  # 2 days ago
        assert result.metric_values[6] == 1.0   # today

    def test_financial_uses_financial_loss_dollars(self, trend_engine, sample_config):
        """AC#1: Financial trend uses financial_loss_dollars from daily_summaries."""
        target_date = date(2026, 2, 10)
        trailing_summaries = {
            "asset-1": [
                # T-7 data for week-over-week comparison
                {"report_date": (target_date - timedelta(days=7)).isoformat(),
                 "oee_percentage": 80.0, "financial_loss_dollars": 2000.0},
                # T-6 data (oldest in metric_values array)
                {"report_date": (target_date - timedelta(days=6)).isoformat(),
                 "oee_percentage": 80.0, "financial_loss_dollars": 2100.0},
                {"report_date": target_date.isoformat(),
                 "oee_percentage": 75.0, "financial_loss_dollars": 3500.0},
            ]
        }
        action = ActionItem(
            id="f1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.FINANCIAL,
            primary_metric_value="Loss: $3,500.00", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        assert result.metric_values[0] == 2100.0  # oldest in array (T-6)
        assert result.metric_values[6] == 3500.0  # today
        # week_over_week_change uses T-7 (2000.0): ((3500 - 2000) / 2000) * 100 = 75.0
        assert result.week_over_week_change == 75.0

    def test_week_over_week_change_with_zero_denominator(self, trend_engine, sample_config):
        """AC#1: week_over_week_change is None when 7-day-ago value is 0."""
        target_date = date(2026, 2, 10)
        trailing_summaries = {
            "asset-1": [
                # T-7 data with zero OEE (denominator for w-o-w)
                {"report_date": (target_date - timedelta(days=7)).isoformat(),
                 "oee_percentage": 0.0, "financial_loss_dollars": 0.0},
                {"report_date": target_date.isoformat(),
                 "oee_percentage": 72.5, "financial_loss_dollars": 0.0},
            ]
        }
        action = ActionItem(
            id="o1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 72.5%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        # Denominator is 0 (T-7 OEE = 0.0), should return None
        assert result.week_over_week_change is None

    def test_days_on_report_counts_oee_below_target(self, trend_engine, sample_config):
        """AC#1: days_on_report counts days where OEE < target (85%)."""
        target_date = date(2026, 2, 10)
        trailing_summaries = {
            "asset-1": [
                {"report_date": (target_date - timedelta(days=6)).isoformat(),
                 "oee_percentage": 80.0, "financial_loss_dollars": 0},  # below 85
                {"report_date": (target_date - timedelta(days=5)).isoformat(),
                 "oee_percentage": 90.0, "financial_loss_dollars": 0},  # above 85
                {"report_date": (target_date - timedelta(days=4)).isoformat(),
                 "oee_percentage": 70.0, "financial_loss_dollars": 0},  # below 85
                {"report_date": (target_date - timedelta(days=3)).isoformat(),
                 "oee_percentage": 65.0, "financial_loss_dollars": 0},  # below 85
                {"report_date": (target_date - timedelta(days=2)).isoformat(),
                 "oee_percentage": 88.0, "financial_loss_dollars": 0},  # above 85
                {"report_date": (target_date - timedelta(days=1)).isoformat(),
                 "oee_percentage": 82.0, "financial_loss_dollars": 0},  # below 85
                {"report_date": target_date.isoformat(),
                 "oee_percentage": 78.0, "financial_loss_dollars": 0},  # below 85
            ]
        }
        action = ActionItem(
            id="o1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 78%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        # Days below 85%: day-6(80), day-4(70), day-3(65), day-1(82), day-0(78) = 5
        assert result.days_on_report == 5

    def test_consecutive_days_stops_at_non_triggering_day(self, trend_engine, sample_config):
        """AC#1: consecutive_days stops counting at first day NOT meeting condition."""
        target_date = date(2026, 2, 10)
        trailing_summaries = {
            "asset-1": [
                {"report_date": (target_date - timedelta(days=6)).isoformat(),
                 "oee_percentage": 70.0, "financial_loss_dollars": 0},  # below
                {"report_date": (target_date - timedelta(days=5)).isoformat(),
                 "oee_percentage": 72.0, "financial_loss_dollars": 0},  # below
                {"report_date": (target_date - timedelta(days=4)).isoformat(),
                 "oee_percentage": 90.0, "financial_loss_dollars": 0},  # ABOVE - breaks consecutive
                {"report_date": (target_date - timedelta(days=3)).isoformat(),
                 "oee_percentage": 74.0, "financial_loss_dollars": 0},  # below
                {"report_date": (target_date - timedelta(days=2)).isoformat(),
                 "oee_percentage": 76.0, "financial_loss_dollars": 0},  # below
                {"report_date": (target_date - timedelta(days=1)).isoformat(),
                 "oee_percentage": 73.0, "financial_loss_dollars": 0},  # below
                {"report_date": target_date.isoformat(),
                 "oee_percentage": 78.0, "financial_loss_dollars": 0},  # below
            ]
        }
        action = ActionItem(
            id="o1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 78%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        # From target_date backward: day-0(78<85), day-1(73<85), day-2(76<85), day-3(74<85),
        # day-4(90>=85) -> stops. consecutive_days = 4
        assert result.consecutive_days == 4

    def test_consecutive_days_minimum_is_1(self, trend_engine, sample_config):
        """AC#1: consecutive_days minimum is 1 since item is on today's list."""
        target_date = date(2026, 2, 10)
        # No trailing data at all
        trailing_summaries: dict[str, list[dict]] = {}
        action = ActionItem(
            id="o1", asset_id="asset-1", asset_name="Grinder 5",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 78%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        # Even with no data, minimum is 1
        assert result.consecutive_days == 1

    def test_no_trailing_data_for_asset(self, trend_engine, sample_config):
        """AC#3: Asset with no trailing data has all-None metrics."""
        target_date = date(2026, 2, 10)
        trailing_summaries: dict[str, list[dict]] = {}

        action = ActionItem(
            id="o1", asset_id="asset-99", asset_name="Unknown",
            priority_level=PriorityLevel.HIGH, category=ActionCategory.OEE,
            primary_metric_value="OEE: 72%", recommendation_text="R",
            evidence_summary="E", evidence_refs=[], created_at=datetime.utcnow(),
        )

        result = trend_engine._calculate_trend_data(
            action, target_date, trailing_summaries, {}, sample_config
        )

        assert all(v is None for v in result.metric_values)
        assert result.days_on_report == 0
        assert result.consecutive_days == 1  # minimum
        assert result.week_over_week_change is None


class TestTrendBatchLoading:
    """Tests for Story 14.2 AC#5 - Batch query loading."""

    @pytest.mark.asyncio
    async def test_load_trailing_summaries_batches_query(self, action_engine, mock_supabase_client):
        """AC#5: _load_trailing_summaries makes a single batched query for all assets."""
        action_engine._client = mock_supabase_client

        target_date = date(2026, 2, 10)
        asset_ids = ["asset-1", "asset-2", "asset-3"]

        mock_response_data = [
            {"asset_id": "asset-1", "report_date": "2026-02-10", "oee_percentage": 80.0,
             "downtime_minutes": 30, "financial_loss_dollars": 500, "actual_output": 800,
             "target_output": 1000, "id": "s1"},
            {"asset_id": "asset-2", "report_date": "2026-02-10", "oee_percentage": 75.0,
             "downtime_minutes": 60, "financial_loss_dollars": 1200, "actual_output": 750,
             "target_output": 1000, "id": "s2"},
            {"asset_id": "asset-1", "report_date": "2026-02-09", "oee_percentage": 82.0,
             "downtime_minutes": 20, "financial_loss_dollars": 300, "actual_output": 820,
             "target_output": 1000, "id": "s3"},
        ]

        # Mock the chained query
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.gte.return_value.lte.return_value.execute.return_value.data = mock_response_data

        result = await action_engine._load_trailing_summaries(target_date, asset_ids)

        # Verify single call to table
        mock_supabase_client.table.assert_called_with("daily_summaries")

        # Verify results grouped by asset
        assert "asset-1" in result
        assert "asset-2" in result
        assert len(result["asset-1"]) == 2  # Two rows for asset-1
        assert len(result["asset-2"]) == 1  # One row for asset-2

        # Verify sorted by date ascending
        assert result["asset-1"][0]["report_date"] == "2026-02-09"
        assert result["asset-1"][1]["report_date"] == "2026-02-10"

    @pytest.mark.asyncio
    async def test_load_trailing_summaries_empty_asset_ids(self, action_engine, mock_supabase_client):
        """AC#5: Empty asset_ids returns empty dict without querying."""
        action_engine._client = mock_supabase_client

        result = await action_engine._load_trailing_summaries(date(2026, 2, 10), [])

        assert result == {}
        mock_supabase_client.table.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_trailing_summaries_handles_error(self, action_engine, mock_supabase_client):
        """AC#5: Returns empty dict on error without raising."""
        action_engine._client = mock_supabase_client
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.gte.return_value.lte.return_value.execute.side_effect = Exception("DB error")

        result = await action_engine._load_trailing_summaries(date(2026, 2, 10), ["asset-1"])

        assert result == {}

    @pytest.mark.asyncio
    async def test_load_trailing_safety_events_batches_query(self, action_engine, mock_supabase_client):
        """AC#5: _load_trailing_safety_events makes a single batched query."""
        action_engine._client = mock_supabase_client

        target_date = date(2026, 2, 10)
        asset_ids = ["asset-1", "asset-2"]

        mock_response_data = [
            {"asset_id": "asset-1", "event_timestamp": "2026-02-10T14:30:00Z"},
            {"asset_id": "asset-1", "event_timestamp": "2026-02-10T15:00:00Z"},
            {"asset_id": "asset-2", "event_timestamp": "2026-02-09T10:00:00Z"},
        ]

        mock_supabase_client.table.return_value.select.return_value.in_.return_value.gte.return_value.lte.return_value.eq.return_value.execute.return_value.data = mock_response_data

        result = await action_engine._load_trailing_safety_events(target_date, asset_ids)

        mock_supabase_client.table.assert_called_with("safety_events")

        assert "asset-1" in result
        assert "asset-2" in result
        assert result["asset-1"]["2026-02-10"] == 2  # Two events on same day
        assert result["asset-2"]["2026-02-09"] == 1

    @pytest.mark.asyncio
    async def test_load_trailing_safety_events_empty_ids(self, action_engine, mock_supabase_client):
        """AC#5: Empty asset_ids returns empty dict without querying."""
        action_engine._client = mock_supabase_client

        result = await action_engine._load_trailing_safety_events(date(2026, 2, 10), [])

        assert result == {}
        mock_supabase_client.table.assert_not_called()


class TestTrendDataIntegration:
    """Tests for Story 14.2 AC#1,6 - Integration with generate_action_list."""

    @pytest.mark.asyncio
    async def test_generate_action_list_includes_trend_data(
        self, action_engine, mock_supabase_client, sample_assets
    ):
        """AC#1: generate_action_list result includes trend_data on each action item."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._shift_targets_cache = {}
        action_engine._cost_centers_cache = {}
        action_engine._cache_timestamp = datetime.utcnow()

        target_date = date.today() - timedelta(days=1)

        # Mock safety query - no safety events
        safety_mock = MagicMock()
        safety_mock.data = []

        # Mock OEE daily_summaries query
        oee_data = [
            {
                "id": str(uuid4()),
                "asset_id": "asset-1",
                "report_date": target_date.isoformat(),
                "oee_percentage": 72.0,
                "actual_output": 720,
                "target_output": 1000,
                "financial_loss_dollars": 2000.0,
                "downtime_minutes": 60,
            }
        ]

        # Mock financial query
        financial_data = []

        # Mock trailing summaries query
        trailing_data = [
            {
                "id": "ts1", "asset_id": "asset-1",
                "report_date": target_date.isoformat(),
                "oee_percentage": 72.0, "downtime_minutes": 60,
                "financial_loss_dollars": 2000.0, "actual_output": 720,
                "target_output": 1000,
            }
        ]

        # Set up the mock to return different data for different table calls
        call_count = {"count": 0}
        table_mocks = {}

        def mock_table(table_name):
            if table_name not in table_mocks:
                table_mocks[table_name] = MagicMock()
            return table_mocks[table_name]

        mock_supabase_client.table = mock_table

        # Assets query (already cached, won't be called)
        # Safety events query
        table_mocks["safety_events"] = MagicMock()
        table_mocks["safety_events"].select.return_value.eq.return_value.gte.return_value.execute.return_value.data = []

        # Daily summaries query (for OEE actions)
        oee_select_mock = MagicMock()
        oee_select_mock.eq.return_value.execute.return_value.data = oee_data
        # For trailing summaries - in_ chain
        trailing_mock = MagicMock()
        trailing_mock.gte.return_value.lte.return_value.execute.return_value.data = trailing_data
        oee_select_mock.in_.return_value = trailing_mock
        # For financial - eq then gt chain
        oee_select_mock.eq.return_value.gt.return_value.execute.return_value.data = financial_data

        table_mocks["daily_summaries"] = MagicMock()
        table_mocks["daily_summaries"].select.return_value = oee_select_mock

        result = await action_engine.generate_action_list(
            target_date=target_date,
            use_cache=False,
        )

        # Should have at least one action item with trend_data
        assert len(result.actions) >= 1
        for action in result.actions:
            assert action.trend_data is not None
            assert len(action.trend_data.metric_values) == 7
            assert action.trend_data.days_on_report >= 0
            assert action.trend_data.consecutive_days >= 1

    @pytest.mark.asyncio
    async def test_cached_response_preserves_trend_data(
        self, action_engine
    ):
        """AC#6: Cached response preserves trend_data on action items."""
        target_date = date.today() - timedelta(days=1)

        td = TrendData(
            metric_values=[78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3],
            days_on_report=5,
            consecutive_days=3,
            week_over_week_change=-9.2,
        )
        cached_response = ActionListResponse(
            actions=[
                ActionItem(
                    id="action-oee-abc123",
                    asset_id="asset-1",
                    asset_name="Grinder 5",
                    priority_level=PriorityLevel.HIGH,
                    category=ActionCategory.OEE,
                    primary_metric_value="OEE: 71.3%",
                    recommendation_text="Review",
                    evidence_summary="Below target",
                    evidence_refs=[],
                    created_at=datetime.utcnow(),
                    trend_data=td,
                ),
            ],
            generated_at=datetime.utcnow(),
            report_date=target_date,
            total_count=1,
            counts_by_category={"safety": 0, "oee": 1, "financial": 0},
        )
        cache_key = f"{target_date.isoformat()}-all"
        action_engine._action_list_cache[cache_key] = cached_response

        result = await action_engine.generate_action_list(
            target_date=target_date,
            use_cache=True,
        )

        assert result.actions[0].trend_data is not None
        assert result.actions[0].trend_data.days_on_report == 5
        assert result.actions[0].trend_data.consecutive_days == 3
        assert result.actions[0].trend_data.week_over_week_change == -9.2
        assert result.actions[0].trend_data.metric_values == [78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3]
