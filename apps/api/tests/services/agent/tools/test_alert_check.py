"""
Tests for Alert Check Tool (Story 7.4)

Comprehensive test coverage for all acceptance criteria:
AC#1: Active Alerts Query - Returns count by severity, details for each alert
AC#2: Severity Filtering - Filter by critical/warning/info
AC#3: No Alerts Scenario - "No active alerts - all systems normal" with last alert time
AC#4: Stale Alert Flagging - Alerts >1 hour flagged as "Requires Attention"
AC#5: Alert Sources - Safety events, production variance >20%, equipment status
AC#6: Data Freshness & Caching - 60 second cache TTL, force_refresh support
AC#7: Citation Compliance - All alerts include source citations
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, patch

from app.models.agent import (
    Alert,
    AlertCheckCitation,
    AlertCheckInput,
    AlertCheckOutput,
    AlertSeverity,
    AlertType,
)
from app.services.agent.base import Citation, ToolResult
from app.services.agent.cache import reset_tool_cache
from app.services.agent.data_source.protocol import (
    DataResult,
    ProductionStatus,
    SafetyEvent,
)
from app.services.agent.tools.alert_check import (
    AlertCheckTool,
    CACHE_TTL_LIVE,
    PRODUCTION_VARIANCE_THRESHOLD,
    SEVERITY_ORDER,
    STALE_ALERT_THRESHOLD_MINUTES,
)


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the tool cache before each test to avoid cross-test contamination."""
    reset_tool_cache()
    yield
    reset_tool_cache()


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def alert_check_tool():
    """Create an instance of AlertCheckTool."""
    return AlertCheckTool()


@pytest.fixture
def mock_safety_events():
    """Create mock SafetyEvent objects with various severities.

    Note: DB uses is_resolved boolean; resolution_status is derived property.
    """
    now = _utcnow()
    return [
        # Critical event - open (45 minutes old)
        SafetyEvent(
            id="evt-001",
            asset_id="asset-1",
            asset_name="Packaging Line 2",
            area="Packaging",
            event_timestamp=now - timedelta(minutes=45),
            reason_code="ESTOP",
            severity="critical",
            description="Safety interlock triggered - operator investigation required",
            is_resolved=False,
        ),
        # High event - open (30 minutes old)
        SafetyEvent(
            id="evt-002",
            asset_id="asset-2",
            asset_name="Grinder 5",
            area="Grinding",
            event_timestamp=now - timedelta(minutes=30),
            reason_code="GUARD",
            severity="high",
            description="Safety guard sensor fault",
            is_resolved=False,
        ),
        # Medium event - open (15 minutes old)
        SafetyEvent(
            id="evt-003",
            asset_id="asset-3",
            asset_name="Press 1",
            area="Pressing",
            event_timestamp=now - timedelta(minutes=15),
            reason_code="SLIP",
            severity="medium",
            description="Near-miss slip incident reported",
            is_resolved=False,
        ),
    ]


@pytest.fixture
def mock_safety_events_stale():
    """Create mock SafetyEvent objects with stale alerts (>1 hour old)."""
    now = _utcnow()
    return [
        # Critical event - 90 minutes old (stale)
        SafetyEvent(
            id="evt-001",
            asset_id="asset-1",
            asset_name="Packaging Line 2",
            area="Packaging",
            event_timestamp=now - timedelta(minutes=90),
            reason_code="ESTOP",
            severity="critical",
            description="Safety interlock triggered",
            is_resolved=False,
        ),
        # Warning event - 75 minutes old (stale)
        SafetyEvent(
            id="evt-002",
            asset_id="asset-2",
            asset_name="Grinder 5",
            area="Grinding",
            event_timestamp=now - timedelta(minutes=75),
            reason_code="GUARD",
            severity="medium",
            description="Safety guard sensor fault",
            is_resolved=False,
        ),
    ]


@pytest.fixture
def mock_production_snapshots():
    """Create mock ProductionStatus objects with variance data."""
    now = _utcnow()
    return [
        # Asset with 25% variance (below target) - should trigger alert
        ProductionStatus(
            id="snap-001",
            asset_id="asset-5",
            asset_name="Grinder 5",
            area="Grinding",
            snapshot_timestamp=now - timedelta(minutes=10),
            current_output=750,
            target_output=1000,
            output_variance=-250,
            status="behind",
        ),
        # Asset with 5% variance (within normal) - should NOT trigger alert
        ProductionStatus(
            id="snap-002",
            asset_id="asset-6",
            asset_name="Grinder 6",
            area="Grinding",
            snapshot_timestamp=now - timedelta(minutes=5),
            current_output=950,
            target_output=1000,
            output_variance=-50,
            status="on_target",
        ),
        # Asset with 30% variance (below target) - should trigger alert
        ProductionStatus(
            id="snap-003",
            asset_id="asset-7",
            asset_name="Press 2",
            area="Pressing",
            snapshot_timestamp=now - timedelta(minutes=8),
            current_output=700,
            target_output=1000,
            output_variance=-300,
            status="behind",
        ),
    ]


def create_data_result(data: Any, table_name: str, query: str = None) -> DataResult:
    """Helper to create DataResult objects for testing."""
    row_count = 0
    if data is not None:
        if isinstance(data, list):
            row_count = len(data)
        elif data:
            row_count = 1

    return DataResult(
        data=data,
        source_name="supabase",
        table_name=table_name,
        query_timestamp=_utcnow(),
        query=query or f"Test query on {table_name}",
        row_count=row_count,
    )


# =============================================================================
# Test: Tool Properties (Tool Registration)
# =============================================================================


class TestAlertCheckToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, alert_check_tool):
        """Tool name is 'alert_check'."""
        assert alert_check_tool.name == "alert_check"

    def test_tool_description_for_intent_matching(self, alert_check_tool):
        """Tool description enables correct intent matching."""
        description = alert_check_tool.description.lower()
        assert "alert" in description
        assert "warning" in description
        assert "severity" in description
        assert "critical" in description

    def test_tool_args_schema(self, alert_check_tool):
        """Args schema is AlertCheckInput."""
        assert alert_check_tool.args_schema == AlertCheckInput

    def test_tool_citations_required(self, alert_check_tool):
        """Citations are required."""
        assert alert_check_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestAlertCheckInput:
    """Tests for AlertCheckInput validation."""

    def test_valid_input_defaults(self):
        """Test valid input with defaults."""
        input_model = AlertCheckInput()
        assert input_model.severity_filter is None
        assert input_model.area_filter is None
        assert input_model.include_resolved is False
        assert input_model.force_refresh is False

    def test_valid_input_with_all_filters(self):
        """Test valid input with all filters."""
        input_model = AlertCheckInput(
            severity_filter="critical",
            area_filter="Packaging",
            include_resolved=True,
            force_refresh=True
        )
        assert input_model.severity_filter == "critical"
        assert input_model.area_filter == "Packaging"
        assert input_model.include_resolved is True
        assert input_model.force_refresh is True


# =============================================================================
# Test: Active Alerts Query (AC#1)
# =============================================================================


class TestActiveAlertsQuery:
    """Tests for active alerts query - AC#1."""

    @pytest.mark.asyncio
    async def test_basic_query_returns_success(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#1: Successful basic query returns all expected data."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            assert result.success is True
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_alerts_include_count_by_severity(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#1: Response includes count by severity."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            assert "count_by_severity" in result.data
            count_by_severity = result.data["count_by_severity"]
            assert "critical" in count_by_severity
            assert "warning" in count_by_severity
            assert "info" in count_by_severity

    @pytest.mark.asyncio
    async def test_alerts_sorted_by_severity(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#1: Alerts are sorted by severity (critical first)."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            alerts = result.data["alerts"]
            if len(alerts) > 1:
                # Verify sorting: each alert should have same or higher priority than next
                for i in range(len(alerts) - 1):
                    curr_severity = SEVERITY_ORDER.get(alerts[i]["severity"], 99)
                    next_severity = SEVERITY_ORDER.get(alerts[i + 1]["severity"], 99)
                    assert curr_severity <= next_severity

    @pytest.mark.asyncio
    async def test_each_alert_includes_required_fields(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#1: Each alert includes type, asset, description, recommended response."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            for alert in result.data["alerts"]:
                assert "alert_id" in alert
                assert "type" in alert
                assert "severity" in alert
                assert "asset" in alert
                assert "description" in alert
                assert "recommended_response" in alert
                assert "triggered_at" in alert
                assert "duration_minutes" in alert

    @pytest.mark.asyncio
    async def test_data_freshness_included(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#1: Response includes data freshness timestamp."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            assert "data_freshness" in result.data
            assert result.data["data_freshness"] is not None


# =============================================================================
# Test: Severity Filtering (AC#2)
# =============================================================================


class TestSeverityFiltering:
    """Tests for severity filtering - AC#2."""

    @pytest.mark.asyncio
    async def test_severity_filter_critical_only(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#2: Filter by critical returns only critical alerts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(severity_filter="critical")

            for alert in result.data["alerts"]:
                assert alert["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_severity_filter_indicated_in_response(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#2: Response indicates filter was applied."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(severity_filter="critical")

            assert result.data["filter_applied"] is not None
            assert "critical" in result.data["filter_applied"].lower()

    @pytest.mark.asyncio
    async def test_severity_filter_warning_only(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#2: Filter by warning returns only warning alerts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(severity_filter="warning")

            for alert in result.data["alerts"]:
                assert alert["severity"] == "warning"


# =============================================================================
# Test: No Alerts Scenario (AC#3)
# =============================================================================


class TestNoAlertsScenario:
    """Tests for no alerts handling - AC#3."""

    @pytest.mark.asyncio
    async def test_no_alerts_returns_all_clear_message(
        self,
        alert_check_tool,
    ):
        """AC#3: Returns 'No active alerts - all systems normal' when clear."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Return empty results for all data sources
            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            assert result.success is True
            assert result.data["total_count"] == 0
            assert "no active alerts" in result.data["summary"].lower()
            assert "normal" in result.data["summary"].lower()

    @pytest.mark.asyncio
    async def test_no_alerts_empty_alerts_list(
        self,
        alert_check_tool,
    ):
        """AC#3: Alerts list is empty when no active alerts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            assert len(result.data["alerts"]) == 0

    @pytest.mark.asyncio
    async def test_no_alerts_count_by_severity_all_zeros(
        self,
        alert_check_tool,
    ):
        """AC#3: Count by severity shows all zeros when no alerts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            count_by_severity = result.data["count_by_severity"]
            assert count_by_severity["critical"] == 0
            assert count_by_severity["warning"] == 0
            assert count_by_severity["info"] == 0


# =============================================================================
# Test: Stale Alert Flagging (AC#4)
# =============================================================================


class TestStaleAlertFlagging:
    """Tests for stale alert flagging - AC#4."""

    @pytest.mark.asyncio
    async def test_stale_alerts_flagged_requires_attention(
        self,
        alert_check_tool,
        mock_safety_events_stale,
    ):
        """AC#4: Alerts >1 hour are flagged as requires_attention."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events_stale, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            # All alerts in mock_safety_events_stale are >1 hour old
            for alert in result.data["alerts"]:
                assert alert["requires_attention"] is True
                assert alert["duration_minutes"] > STALE_ALERT_THRESHOLD_MINUTES

    @pytest.mark.asyncio
    async def test_fresh_alerts_not_flagged(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#4: Alerts <1 hour are not flagged as requires_attention."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            # All alerts in mock_safety_events are <1 hour old
            for alert in result.data["alerts"]:
                assert alert["requires_attention"] is False
                assert alert["duration_minutes"] < STALE_ALERT_THRESHOLD_MINUTES

    @pytest.mark.asyncio
    async def test_stale_alert_summary_mentions_requires_attention(
        self,
        alert_check_tool,
        mock_safety_events_stale,
    ):
        """AC#4: Summary mentions stale alerts requiring attention."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events_stale, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            assert "require attention" in result.data["summary"].lower()


# =============================================================================
# Test: Alert Sources (AC#5)
# =============================================================================


class TestAlertSources:
    """Tests for alert sources - AC#5."""

    @pytest.mark.asyncio
    async def test_safety_events_as_alert_source(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#5: Safety events are included as alerts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            safety_alerts = [
                a for a in result.data["alerts"]
                if a["type"] == AlertType.SAFETY.value
            ]
            assert len(safety_alerts) > 0

    @pytest.mark.asyncio
    async def test_production_variance_as_alert_source(
        self,
        alert_check_tool,
        mock_production_snapshots,
    ):
        """AC#5: Production variance >20% creates alerts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_production_snapshots, "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            variance_alerts = [
                a for a in result.data["alerts"]
                if a["type"] == AlertType.PRODUCTION_VARIANCE.value
            ]
            # Should have 2 alerts (25% and 30% variance), not 3 (5% is normal)
            assert len(variance_alerts) == 2

    @pytest.mark.asyncio
    async def test_production_variance_within_threshold_no_alert(
        self,
        alert_check_tool,
    ):
        """AC#5: Production variance <=20% does not create alerts."""
        now = _utcnow()
        normal_snapshots = [
            ProductionStatus(
                id="snap-001",
                asset_id="asset-1",
                asset_name="Grinder 1",
                area="Grinding",
                snapshot_timestamp=now,
                current_output=900,  # 10% variance
                target_output=1000,
                output_variance=-100,
                status="on_target",
            ),
        ]

        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                normal_snapshots, "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            variance_alerts = [
                a for a in result.data["alerts"]
                if a["type"] == AlertType.PRODUCTION_VARIANCE.value
            ]
            assert len(variance_alerts) == 0

    @pytest.mark.asyncio
    async def test_aggregation_from_multiple_sources(
        self,
        alert_check_tool,
        mock_safety_events,
        mock_production_snapshots,
    ):
        """AC#5: Alerts aggregated from multiple sources."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_production_snapshots, "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            # Should have alerts from both sources
            source_types = set(a["type"] for a in result.data["alerts"])
            assert AlertType.SAFETY.value in source_types
            assert AlertType.PRODUCTION_VARIANCE.value in source_types


# =============================================================================
# Test: Data Freshness & Caching (AC#6)
# =============================================================================


class TestDataFreshnessCaching:
    """Tests for caching behavior - AC#6."""

    @pytest.mark.asyncio
    async def test_cache_tier_is_live(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#6: Cache tier is 'live' for alert data."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            assert result.metadata["cache_tier"] == "live"

    @pytest.mark.asyncio
    async def test_ttl_is_60_seconds(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#6: TTL is 60 seconds."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            assert result.metadata["ttl_seconds"] == CACHE_TTL_LIVE
            assert result.metadata["ttl_seconds"] == 60


# =============================================================================
# Test: Citation Compliance (AC#7)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation - AC#7."""

    @pytest.mark.asyncio
    async def test_response_includes_citations(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#7: All responses include citations."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            assert len(result.citations) >= 1

    @pytest.mark.asyncio
    async def test_citation_includes_source_table(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#7: Citations include source table."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            citation = result.citations[0]
            assert citation.table is not None

    @pytest.mark.asyncio
    async def test_citation_includes_timestamp(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#7: Citations include timestamp."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            citation = result.citations[0]
            assert citation.timestamp is not None

    @pytest.mark.asyncio
    async def test_alert_citations_in_output(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#7: Output includes AlertCheckCitation objects."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            # Check output citations
            assert "citations" in result.data
            if result.data["alerts"]:
                assert len(result.data["citations"]) > 0
                for citation in result.data["citations"]:
                    assert "source_table" in citation
                    assert "timestamp" in citation
                    assert "display_text" in citation


# =============================================================================
# Test: Area Filtering
# =============================================================================


class TestAreaFiltering:
    """Tests for area-based filtering."""

    @pytest.mark.asyncio
    async def test_area_filter_applied(
        self,
        alert_check_tool,
    ):
        """Area filter is passed to data source."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )
            mock_ds.get_live_snapshots_by_area.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(area_filter="Grinding", force_refresh=True)

            # Verify area filter was passed to safety events (first call)
            # Note: get_safety_events may be called twice (once for alerts, once for last_alert_time)
            first_call_kwargs = mock_ds.get_safety_events.call_args_list[0][1]
            assert first_call_kwargs["area"] == "Grinding"

            # Verify area-specific snapshots were queried
            mock_ds.get_live_snapshots_by_area.assert_called_once_with("Grinding")


# =============================================================================
# Test: Severity Mapping
# =============================================================================


class TestSeverityMapping:
    """Tests for safety severity to alert severity mapping."""

    def test_map_critical_severity(self, alert_check_tool):
        """Critical safety event maps to critical alert."""
        result = alert_check_tool._map_safety_severity("critical")
        assert result == AlertSeverity.CRITICAL.value

    def test_map_high_severity(self, alert_check_tool):
        """High safety event maps to critical alert."""
        result = alert_check_tool._map_safety_severity("high")
        assert result == AlertSeverity.CRITICAL.value

    def test_map_medium_severity(self, alert_check_tool):
        """Medium safety event maps to warning alert."""
        result = alert_check_tool._map_safety_severity("medium")
        assert result == AlertSeverity.WARNING.value

    def test_map_low_severity(self, alert_check_tool):
        """Low safety event maps to info alert."""
        result = alert_check_tool._map_safety_severity("low")
        assert result == AlertSeverity.INFO.value


# =============================================================================
# Test: Summary Generation
# =============================================================================


class TestSummaryGeneration:
    """Tests for summary text generation."""

    def test_summary_no_alerts(self, alert_check_tool):
        """Summary for no alerts scenario."""
        summary = alert_check_tool._generate_summary(
            alerts=[],
            counts={"critical": 0, "warning": 0, "info": 0},
            severity_filter=None,
            area_filter=None,
        )
        assert "no active alerts" in summary.lower()
        assert "normal" in summary.lower()

    def test_summary_with_alerts(self, alert_check_tool):
        """Summary includes alert counts."""
        mock_alerts = [
            Alert(
                alert_id="test-1",
                type="safety",
                severity="critical",
                asset="Test Asset",
                description="Test",
                recommended_response="Test",
                triggered_at=_utcnow(),
                duration_minutes=10,
                requires_attention=False,
                source_table="safety_events",
            )
        ]
        summary = alert_check_tool._generate_summary(
            alerts=mock_alerts,
            counts={"critical": 1, "warning": 0, "info": 0},
            severity_filter=None,
            area_filter=None,
        )
        assert "1" in summary
        assert "critical" in summary.lower()

    def test_summary_with_area_filter(self, alert_check_tool):
        """Summary includes area when filtered."""
        summary = alert_check_tool._generate_summary(
            alerts=[],
            counts={"critical": 0, "warning": 0, "info": 0},
            severity_filter=None,
            area_filter="Grinding",
        )
        assert "grinding" in summary.lower()


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios.

    Note: The AlertCheckTool is designed to be resilient to individual
    data source failures. If one source fails, it continues with others.
    This ensures the tool returns partial results rather than failing completely.
    """

    @pytest.mark.asyncio
    async def test_partial_failure_still_returns_results(
        self, alert_check_tool
    ):
        """Tool returns results even if one data source fails."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Safety events fail, but live snapshots succeed
            mock_ds.get_safety_events.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="safety_events",
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            # Tool should still succeed with partial data
            assert result.success is True
            # But should return empty alerts since safety events failed
            assert result.data["total_count"] == 0

    @pytest.mark.asyncio
    async def test_complete_failure_returns_success_with_no_alerts(
        self, alert_check_tool
    ):
        """When all sources fail gracefully, returns success with no alerts."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Both sources fail
            mock_ds.get_safety_events.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="safety_events",
            )
            mock_ds.get_all_live_snapshots.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="live_snapshots",
            )

            result = await alert_check_tool._arun(force_refresh=True)

            # Tool still succeeds but with no alerts
            assert result.success is True
            assert result.data["total_count"] == 0
            assert "no active alerts" in result.data["summary"].lower()

    @pytest.mark.asyncio
    async def test_individual_source_error_does_not_crash(
        self,
        alert_check_tool,
        mock_production_snapshots,
    ):
        """Tool continues when individual sources fail."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            # Safety events fail, but live snapshots work with variance alerts
            mock_ds.get_safety_events.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="safety_events",
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                mock_production_snapshots, "live_snapshots"
            )

            result = await alert_check_tool._arun(force_refresh=True)

            # Tool succeeds and returns variance alerts from working source
            assert result.success is True
            # Should have alerts from live_snapshots even though safety failed
            variance_alerts = [
                a for a in result.data["alerts"]
                if a["type"] == AlertType.PRODUCTION_VARIANCE.value
            ]
            assert len(variance_alerts) == 2  # From mock_production_snapshots


# =============================================================================
# Test: Follow-up Questions
# =============================================================================


class TestFollowUpQuestions:
    """Tests for follow-up question generation."""

    @pytest.mark.asyncio
    async def test_follow_up_questions_generated(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """Follow-up questions are generated in metadata."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3


# =============================================================================
# Test: Tool Registration (Integration)
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = AlertCheckTool()
        assert tool is not None
        assert tool.name == "alert_check"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = AlertCheckTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)


# =============================================================================
# Test: Count by Severity Calculation
# =============================================================================


class TestCountBySeverity:
    """Tests for count by severity calculation."""

    @pytest.mark.asyncio
    async def test_count_matches_actual_alerts(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#1: Count by severity matches actual alert counts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            # Manually count alerts by severity
            alerts = result.data["alerts"]
            manual_count = {"critical": 0, "warning": 0, "info": 0}
            for alert in alerts:
                if alert["severity"] in manual_count:
                    manual_count[alert["severity"]] += 1

            assert result.data["count_by_severity"] == manual_count

    @pytest.mark.asyncio
    async def test_total_count_equals_sum_of_severity_counts(
        self,
        alert_check_tool,
        mock_safety_events,
    ):
        """AC#1: Total count equals sum of severity counts."""
        with patch(
            "app.services.agent.tools.alert_check.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )
            mock_ds.get_all_live_snapshots.return_value = create_data_result(
                [], "live_snapshots"
            )

            result = await alert_check_tool._arun()

            count_by_severity = result.data["count_by_severity"]
            total_from_counts = sum(count_by_severity.values())
            assert total_from_counts == result.data["total_count"]
