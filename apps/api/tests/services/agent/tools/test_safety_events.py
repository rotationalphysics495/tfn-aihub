"""
Tests for Safety Events Tool (Story 6.1)

Comprehensive test coverage for all acceptance criteria:
AC#1: Basic Safety Query - Returns count, timestamp, asset, severity, description, status
AC#2: Area-Filtered Safety Query - Filters to events in a specific area with summary
AC#3: Severity-Filtered Safety Query - Filters by severity level
AC#4: No Incidents Response - Positive messaging when no incidents found
AC#5: Citation Compliance - All responses include citations with source and timestamp
AC#6: Performance Requirements - <2s response time, 60s cache TTL
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, patch

from app.models.agent import (
    SafetyEventDetail,
    SafetyEventsInput,
    SafetyEventsOutput,
    SafetySummaryStats,
)
from app.services.agent.base import Citation, ToolResult
from app.services.agent.data_source.protocol import DataResult, SafetyEvent
from app.services.agent.tools.safety_events import (
    SafetyEventsTool,
    CACHE_TTL_LIVE,
    SEVERITY_ORDER,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def safety_events_tool():
    """Create an instance of SafetyEventsTool."""
    return SafetyEventsTool()


@pytest.fixture
def mock_safety_events():
    """Create mock SafetyEvent objects with various severities and statuses.

    Note: DB uses is_resolved boolean; resolution_status is derived property.
    - is_resolved=False -> resolution_status="open"
    - is_resolved=True -> resolution_status="resolved"
    """
    now = _utcnow()
    return [
        # Critical event - open (under investigation in real world)
        SafetyEvent(
            id="evt-001",
            asset_id="asset-1",
            asset_name="Packaging Line 2",
            area="Packaging",
            event_timestamp=now - timedelta(hours=2),
            reason_code="ESTOP",
            severity="critical",
            description="Emergency stop triggered - safety shutoff activated",
            is_resolved=False,  # Maps to resolution_status="open"
        ),
        # High event - open
        SafetyEvent(
            id="evt-002",
            asset_id="asset-2",
            asset_name="Grinder 5",
            area="Grinding",
            event_timestamp=now - timedelta(hours=4),
            reason_code="GUARD",
            severity="high",
            description="Safety guard sensor fault",
            is_resolved=False,  # Maps to resolution_status="open"
        ),
        # Medium event - resolved
        SafetyEvent(
            id="evt-003",
            asset_id="asset-3",
            asset_name="Press 1",
            area="Pressing",
            event_timestamp=now - timedelta(hours=6),
            reason_code="SLIP",
            severity="medium",
            description="Near-miss slip incident reported",
            is_resolved=True,  # Maps to resolution_status="resolved"
        ),
        # Low event - resolved
        SafetyEvent(
            id="evt-004",
            asset_id="asset-1",
            asset_name="Packaging Line 2",
            area="Packaging",
            event_timestamp=now - timedelta(hours=8),
            reason_code="NOISE",
            severity="low",
            description="Excessive noise level warning",
            is_resolved=True,  # Maps to resolution_status="resolved"
        ),
    ]


@pytest.fixture
def mock_safety_events_packaging_only():
    """Create mock SafetyEvent objects for Packaging area only."""
    now = _utcnow()
    return [
        SafetyEvent(
            id="evt-001",
            asset_id="asset-1",
            asset_name="Packaging Line 2",
            area="Packaging",
            event_timestamp=now - timedelta(hours=2),
            reason_code="ESTOP",
            severity="critical",
            description="Emergency stop triggered",
            is_resolved=False,
        ),
        SafetyEvent(
            id="evt-004",
            asset_id="asset-1",
            asset_name="Packaging Line 2",
            area="Packaging",
            event_timestamp=now - timedelta(hours=8),
            reason_code="NOISE",
            severity="low",
            description="Excessive noise level warning",
            is_resolved=True,
        ),
    ]


@pytest.fixture
def mock_safety_events_critical_only():
    """Create mock SafetyEvent objects with only critical severity."""
    now = _utcnow()
    return [
        SafetyEvent(
            id="evt-001",
            asset_id="asset-1",
            asset_name="Packaging Line 2",
            area="Packaging",
            event_timestamp=now - timedelta(hours=2),
            reason_code="ESTOP",
            severity="critical",
            description="Emergency stop triggered",
            is_resolved=False,
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
# Test: Tool Properties (AC#7 Tool Registration)
# =============================================================================


class TestSafetyEventsToolProperties:
    """Tests for tool class properties."""

    def test_tool_name(self, safety_events_tool):
        """Tool name is 'safety_events'."""
        assert safety_events_tool.name == "safety_events"

    def test_tool_description_for_intent_matching(self, safety_events_tool):
        """Tool description enables correct intent matching."""
        description = safety_events_tool.description.lower()
        assert "safety" in description
        assert "incidents" in description or "events" in description
        assert "severity" in description

    def test_tool_args_schema(self, safety_events_tool):
        """Args schema is SafetyEventsInput."""
        assert safety_events_tool.args_schema == SafetyEventsInput

    def test_tool_citations_required(self, safety_events_tool):
        """Citations are required."""
        assert safety_events_tool.citations_required is True


# =============================================================================
# Test: Input Schema Validation
# =============================================================================


class TestSafetyEventsInput:
    """Tests for SafetyEventsInput validation."""

    def test_valid_input_defaults(self):
        """Test valid input with defaults."""
        input_model = SafetyEventsInput()
        assert input_model.time_range == "today"
        assert input_model.area is None
        assert input_model.severity_filter is None
        assert input_model.asset_id is None

    def test_valid_input_with_all_filters(self):
        """Test valid input with all filters."""
        input_model = SafetyEventsInput(
            time_range="this week",
            area="Packaging",
            severity_filter="critical",
            asset_id="asset-123"
        )
        assert input_model.time_range == "this week"
        assert input_model.area == "Packaging"
        assert input_model.severity_filter == "critical"
        assert input_model.asset_id == "asset-123"


# =============================================================================
# Test: Basic Safety Query (AC#1)
# =============================================================================


class TestBasicSafetyQuery:
    """Tests for basic safety events queries."""

    @pytest.mark.asyncio
    async def test_basic_query_returns_success(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#1: Successful basic query returns all expected data."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            assert result.success is True
            assert result.data is not None
            assert result.data["scope"] == "the plant"

    @pytest.mark.asyncio
    async def test_basic_query_returns_all_events(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#1: Response includes all safety events in time range."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            assert result.data["total_count"] == 4
            assert len(result.data["events"]) == 4

    @pytest.mark.asyncio
    async def test_events_include_required_fields(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#1: Each event includes timestamp, asset, severity, description, status."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            for event in result.data["events"]:
                assert "event_id" in event
                assert "timestamp" in event
                assert "asset_id" in event
                assert "severity" in event
                assert "resolution_status" in event

    @pytest.mark.asyncio
    async def test_events_sorted_by_severity_then_recency(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#1: Events are sorted by severity (critical first), then recency."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            events = result.data["events"]
            # First should be critical, then high, medium, low
            assert events[0]["severity"] == "critical"
            assert events[1]["severity"] == "high"
            assert events[2]["severity"] == "medium"
            assert events[3]["severity"] == "low"

    @pytest.mark.asyncio
    async def test_data_freshness_included(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#1, AC#5: Response includes data freshness timestamp."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            assert "data_freshness" in result.data
            assert result.data["data_freshness"] is not None


# =============================================================================
# Test: Area-Filtered Safety Query (AC#2)
# =============================================================================


class TestAreaFilteredSafetyQuery:
    """Tests for area-filtered safety events queries."""

    @pytest.mark.asyncio
    async def test_area_filter_applied(
        self,
        safety_events_tool,
        mock_safety_events_packaging_only,
    ):
        """AC#2: Filters to events in the specified area only."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events_packaging_only, "safety_events"
            )

            result = await safety_events_tool._arun(area="Packaging")

            # Verify the data source was called with area filter
            mock_ds.get_safety_events.assert_called_once()
            call_kwargs = mock_ds.get_safety_events.call_args[1]
            assert call_kwargs["area"] == "Packaging"

    @pytest.mark.asyncio
    async def test_area_filter_scope_in_response(
        self,
        safety_events_tool,
        mock_safety_events_packaging_only,
    ):
        """AC#2: Response scope reflects the filtered area."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events_packaging_only, "safety_events"
            )

            result = await safety_events_tool._arun(area="Packaging")

            assert result.data["scope"] == "the Packaging area"

    @pytest.mark.asyncio
    async def test_area_filter_includes_summary_stats(
        self,
        safety_events_tool,
        mock_safety_events_packaging_only,
    ):
        """AC#2: Shows summary statistics (total events, resolved vs open)."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events_packaging_only, "safety_events"
            )

            result = await safety_events_tool._arun(area="Packaging")

            summary = result.data["summary"]
            assert summary["total_events"] == 2
            assert "by_severity" in summary
            assert "by_status" in summary
            assert "resolved_count" in summary
            assert "open_count" in summary


# =============================================================================
# Test: Severity-Filtered Safety Query (AC#3)
# =============================================================================


class TestSeverityFilteredSafetyQuery:
    """Tests for severity-filtered safety events queries."""

    @pytest.mark.asyncio
    async def test_severity_filter_applied(
        self,
        safety_events_tool,
        mock_safety_events_critical_only,
    ):
        """AC#3: Only events matching severity are returned."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events_critical_only, "safety_events"
            )

            result = await safety_events_tool._arun(severity_filter="critical")

            # Verify the data source was called with severity filter
            mock_ds.get_safety_events.assert_called_once()
            call_kwargs = mock_ds.get_safety_events.call_args[1]
            assert call_kwargs["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_severity_filter_all_events_match(
        self,
        safety_events_tool,
        mock_safety_events_critical_only,
    ):
        """AC#3: All returned events match the severity filter."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events_critical_only, "safety_events"
            )

            result = await safety_events_tool._arun(severity_filter="critical")

            for event in result.data["events"]:
                assert event["severity"] == "critical"


# =============================================================================
# Test: No Incidents Response (AC#4)
# =============================================================================


class TestNoIncidentsResponse:
    """Tests for no incidents handling."""

    @pytest.mark.asyncio
    async def test_no_incidents_returns_positive_message(
        self,
        safety_events_tool,
    ):
        """AC#4: Returns positive message when no incidents found."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )

            result = await safety_events_tool._arun(area="Grinding")

            assert result.success is True
            assert result.data["no_incidents"] is True
            assert "No safety incidents recorded" in result.data["message"]
            assert "positive news" in result.data["message"].lower()

    @pytest.mark.asyncio
    async def test_no_incidents_includes_scope_and_time_range(
        self,
        safety_events_tool,
    ):
        """AC#4: Message includes scope and time range."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )

            result = await safety_events_tool._arun(
                area="Grinding",
                time_range="this week"
            )

            assert "Grinding" in result.data["message"]
            assert "this week" in result.data["message"]

    @pytest.mark.asyncio
    async def test_no_incidents_empty_events_list(
        self,
        safety_events_tool,
    ):
        """AC#4: Events list is empty when no incidents."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )

            result = await safety_events_tool._arun()

            assert result.data["total_count"] == 0
            assert len(result.data["events"]) == 0

    @pytest.mark.asyncio
    async def test_no_incidents_summary_all_zeros(
        self,
        safety_events_tool,
    ):
        """AC#4: Summary statistics show all zeros."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                [], "safety_events"
            )

            result = await safety_events_tool._arun()

            summary = result.data["summary"]
            assert summary["total_events"] == 0
            assert summary["resolved_count"] == 0
            assert summary["open_count"] == 0


# =============================================================================
# Test: Citation Compliance (AC#5)
# =============================================================================


class TestCitationCompliance:
    """Tests for citation generation and compliance."""

    @pytest.mark.asyncio
    async def test_response_includes_citations(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#5: All responses include citations."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            assert len(result.citations) >= 1

    @pytest.mark.asyncio
    async def test_citation_includes_source_table(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#5: Citations include source table."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            citation = result.citations[0]
            assert citation.table == "safety_events"

    @pytest.mark.asyncio
    async def test_citation_includes_timestamp(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#5: Citations include timestamp."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            citation = result.citations[0]
            assert citation.timestamp is not None


# =============================================================================
# Test: Caching Support (AC#6)
# =============================================================================


class TestCachingSupport:
    """Tests for cache metadata."""

    @pytest.mark.asyncio
    async def test_cache_tier_is_live(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#6: Cache tier is 'live' for safety data."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            assert result.metadata["cache_tier"] == "live"

    @pytest.mark.asyncio
    async def test_ttl_is_60_seconds(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """AC#6: TTL is 60 seconds."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            assert result.metadata["ttl_seconds"] == CACHE_TTL_LIVE
            assert result.metadata["ttl_seconds"] == 60


# =============================================================================
# Test: Time Range Parsing
# =============================================================================


class TestTimeRangeParsing:
    """Tests for time range parsing."""

    def test_parse_today(self, safety_events_tool):
        """Parse 'today' time range."""
        result = safety_events_tool._parse_time_range("today")
        today = date.today()
        assert result.start == today
        assert result.end == today
        assert result.description == "today"

    def test_parse_yesterday(self, safety_events_tool):
        """Parse 'yesterday' time range."""
        result = safety_events_tool._parse_time_range("yesterday")
        yesterday = date.today() - timedelta(days=1)
        assert result.start == yesterday
        assert result.end == yesterday
        assert result.description == "yesterday"

    def test_parse_this_week(self, safety_events_tool):
        """Parse 'this week' time range."""
        result = safety_events_tool._parse_time_range("this week")
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        assert result.start == monday
        assert result.end == today
        assert result.description == "this week"

    def test_parse_last_n_days(self, safety_events_tool):
        """Parse 'last 7 days' time range."""
        result = safety_events_tool._parse_time_range("last 7 days")
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        assert result.start == seven_days_ago
        assert result.end == today
        assert result.description == "last 7 days"

    def test_parse_date_range(self, safety_events_tool):
        """Parse explicit date range."""
        result = safety_events_tool._parse_time_range("2026-01-01 to 2026-01-09")
        assert result.start == date(2026, 1, 1)
        assert result.end == date(2026, 1, 9)

    def test_parse_unknown_defaults_to_today(self, safety_events_tool):
        """Unknown time range defaults to today."""
        result = safety_events_tool._parse_time_range("unknown value")
        today = date.today()
        assert result.start == today
        assert result.end == today


# =============================================================================
# Test: Event Sorting
# =============================================================================


class TestEventSorting:
    """Tests for event sorting logic."""

    def test_sort_by_severity(self, safety_events_tool, mock_safety_events):
        """Events are sorted by severity (critical first)."""
        sorted_events = safety_events_tool._sort_events(mock_safety_events)

        severities = [e.severity for e in sorted_events]
        expected_order = ["critical", "high", "medium", "low"]
        assert severities == expected_order

    def test_sort_by_recency_within_severity(self, safety_events_tool):
        """Events with same severity are sorted by recency (newest first)."""
        now = _utcnow()
        events = [
            SafetyEvent(
                id="evt-1",
                asset_id="a1",
                event_timestamp=now - timedelta(hours=4),
                reason_code="TEST",
                severity="high",
                is_resolved=False,
            ),
            SafetyEvent(
                id="evt-2",
                asset_id="a2",
                event_timestamp=now - timedelta(hours=2),
                reason_code="TEST",
                severity="high",
                is_resolved=False,
            ),
            SafetyEvent(
                id="evt-3",
                asset_id="a3",
                event_timestamp=now - timedelta(hours=6),
                reason_code="TEST",
                severity="high",
                is_resolved=False,
            ),
        ]

        sorted_events = safety_events_tool._sort_events(events)

        # Should be ordered by recency (newest first)
        assert sorted_events[0].id == "evt-2"  # 2 hours ago
        assert sorted_events[1].id == "evt-1"  # 4 hours ago
        assert sorted_events[2].id == "evt-3"  # 6 hours ago


# =============================================================================
# Test: Summary Statistics
# =============================================================================


class TestSummaryStatistics:
    """Tests for summary statistics calculation."""

    def test_summary_counts_by_severity(
        self, safety_events_tool, mock_safety_events
    ):
        """Summary includes correct counts by severity."""
        summary = safety_events_tool._calculate_summary(mock_safety_events)

        assert summary.by_severity["critical"] == 1
        assert summary.by_severity["high"] == 1
        assert summary.by_severity["medium"] == 1
        assert summary.by_severity["low"] == 1

    def test_summary_counts_by_status(
        self, safety_events_tool, mock_safety_events
    ):
        """Summary includes correct counts by status.

        Note: With is_resolved boolean, we only have open/resolved.
        Mock data has 2 events with is_resolved=False (open) and 2 with True (resolved).
        """
        summary = safety_events_tool._calculate_summary(mock_safety_events)

        assert summary.by_status["open"] == 2  # is_resolved=False events
        assert summary.by_status["under_investigation"] == 0  # Not tracked in current schema
        assert summary.by_status["resolved"] == 2  # is_resolved=True events

    def test_summary_resolved_vs_open(
        self, safety_events_tool, mock_safety_events
    ):
        """Summary includes resolved vs open counts."""
        summary = safety_events_tool._calculate_summary(mock_safety_events)

        assert summary.resolved_count == 2
        assert summary.open_count == 2  # open only (under_investigation=0)


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_data_source_error_returns_friendly_message(
        self, safety_events_tool
    ):
        """Returns user-friendly error message for data source errors."""
        from app.services.agent.data_source.exceptions import DataSourceQueryError

        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.side_effect = DataSourceQueryError(
                "Database connection failed",
                source_name="supabase",
                table_name="safety_events",
            )

            result = await safety_events_tool._arun()

            assert result.success is False
            assert result.error_message is not None
            assert "Unable to retrieve" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error_handled(self, safety_events_tool):
        """Unexpected errors are caught and logged."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.side_effect = RuntimeError("Unexpected failure")

            result = await safety_events_tool._arun()

            assert result.success is False
            assert result.error_message is not None
            assert "unexpected error" in result.error_message.lower()


# =============================================================================
# Test: Follow-up Question Generation
# =============================================================================


class TestFollowUpQuestions:
    """Tests for follow-up question generation."""

    @pytest.mark.asyncio
    async def test_follow_up_questions_generated(
        self,
        safety_events_tool,
        mock_safety_events,
    ):
        """Follow-up questions are generated in metadata."""
        with patch(
            "app.services.agent.tools.safety_events.get_data_source"
        ) as mock_get_ds:
            mock_ds = AsyncMock()
            mock_get_ds.return_value = mock_ds

            mock_ds.get_safety_events.return_value = create_data_result(
                mock_safety_events, "safety_events"
            )

            result = await safety_events_tool._arun()

            assert "follow_up_questions" in result.metadata
            assert len(result.metadata["follow_up_questions"]) <= 3


# =============================================================================
# Test: Tool Registration (Integration)
# =============================================================================


class TestToolRegistration:
    """Tests for tool registration with the registry."""

    def test_tool_can_be_instantiated(self):
        """Tool can be instantiated without errors."""
        tool = SafetyEventsTool()
        assert tool is not None
        assert tool.name == "safety_events"

    def test_tool_is_manufacturing_tool(self):
        """Tool extends ManufacturingTool."""
        tool = SafetyEventsTool()
        from app.services.agent.base import ManufacturingTool

        assert isinstance(tool, ManufacturingTool)


# =============================================================================
# Test: Message Building
# =============================================================================


class TestMessageBuilding:
    """Tests for contextual message building."""

    def test_message_for_critical_incidents(
        self, safety_events_tool, mock_safety_events
    ):
        """Message highlights critical incidents."""
        message = safety_events_tool._build_message(
            mock_safety_events, "the plant", "today"
        )
        assert "ATTENTION" in message
        assert "critical" in message.lower()

    def test_message_for_no_incidents(self, safety_events_tool):
        """Message is positive when no incidents."""
        message = safety_events_tool._build_message([], "the plant", "today")
        assert "No safety incidents recorded" in message
        assert "positive news" in message.lower()

    def test_message_all_resolved(self, safety_events_tool):
        """Message notes when all resolved."""
        now = _utcnow()
        events = [
            SafetyEvent(
                id="evt-1",
                asset_id="a1",
                event_timestamp=now,
                reason_code="TEST",
                severity="medium",
                is_resolved=True,
            ),
        ]
        message = safety_events_tool._build_message(events, "the plant", "today")
        assert "resolved" in message.lower()
