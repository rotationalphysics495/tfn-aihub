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
    ActionCategory,
    ActionEngineConfig,
    ActionItem,
    ActionListResponse,
    EvidenceRef,
    PriorityLevel,
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
        },
        {
            "id": str(uuid4()),
            "asset_id": "asset-1",
            "report_date": target_date.isoformat(),
            "oee_percentage": 78.0,  # 7% gap (low priority)
            "actual_output": 780,
            "target_output": 1000,
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
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value.data = sample_daily_summaries_oee

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_oee_actions(target_date, sample_assets)

        assert len(actions) == 2
        for action in actions:
            assert action.category == ActionCategory.OEE

    @pytest.mark.asyncio
    async def test_oee_sorted_by_gap_magnitude(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_oee
    ):
        """AC#3: OEE items sorted by gap magnitude (worst first)."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value.data = sample_daily_summaries_oee

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_oee_actions(target_date, sample_assets)

        # asset-3 (60% OEE, 25% gap) should be before asset-1 (78% OEE, 7% gap)
        assert actions[0].asset_id == "asset-3"
        assert actions[1].asset_id == "asset-1"

    @pytest.mark.asyncio
    async def test_oee_priority_based_on_gap_severity(
        self, action_engine, mock_supabase_client, sample_assets, sample_daily_summaries_oee
    ):
        """AC#3: OEE priority based on gap severity."""
        action_engine._client = mock_supabase_client
        action_engine._assets_cache = sample_assets
        action_engine._cache_timestamp = datetime.utcnow()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value.data = sample_daily_summaries_oee

        target_date = date.today() - timedelta(days=1)
        actions = await action_engine._get_oee_actions(target_date, sample_assets)

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
