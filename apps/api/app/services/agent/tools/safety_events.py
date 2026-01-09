"""
Safety Events Tool (Story 6.1)

Tool for querying safety incidents and events with filtering capabilities.
Helps plant managers track safety issues and their resolution status.

AC#1: Basic Safety Query - Returns count, timestamp, asset, severity, description, status
AC#2: Area-Filtered Safety Query - Filters to events in a specific area with summary
AC#3: Severity-Filtered Safety Query - Filters by severity level
AC#4: No Incidents Response - Positive messaging when no incidents found
AC#5: Citation Compliance - All responses include citations with source and timestamp
AC#6: Performance Requirements - <2s response time, 60s cache TTL
"""

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Type

from pydantic import BaseModel

from app.models.agent import (
    SafetyEventDetail,
    SafetyEventsInput,
    SafetyEventsOutput,
    SafetySummaryStats,
)
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool
from app.services.agent.data_source import (
    DataResult,
    DataSourceError,
    SafetyEvent,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL for safety data (must be fresh)
CACHE_TTL_LIVE = 60  # 60 seconds

# Severity order for sorting (critical first)
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class TimeRange:
    """Parsed time range with start and end dates."""

    def __init__(self, start: date, end: date, description: str):
        self.start = start
        self.end = end
        self.description = description


class SafetyEventsTool(ManufacturingTool):
    """
    Query safety incidents and events.

    Story 6.1: Safety Events Tool Implementation

    Use this tool when a user asks about safety incidents, safety events,
    safety issues, or wants to know the resolution status of safety concerns.
    Returns safety event details sorted by severity (critical first), then recency.

    Examples:
        - "Any safety incidents today?"
        - "Show me safety incidents for the Packaging area"
        - "What critical safety incidents occurred this week?"
        - "Safety status for Grinder 5"
    """

    name: str = "safety_events"
    description: str = (
        "Query safety incidents and events. "
        "Use this tool when user asks about safety incidents, safety events, "
        "safety issues, or wants to know resolution status of safety concerns. "
        "Returns event details sorted by severity (critical first), then recency. "
        "Supports filtering by time range (today, this week, specific dates), "
        "area (Grinding, Packaging, etc.), severity (critical, high, medium, low), "
        "and specific assets. "
        "Examples: 'Any safety incidents today?', 'Show me safety incidents for Packaging', "
        "'What critical safety incidents occurred this week?'"
    )
    args_schema: Type[BaseModel] = SafetyEventsInput
    citations_required: bool = True

    # Story 5.8 / 6.1 AC#6: Apply caching with live tier (60 second TTL)
    # Safety data should be fresh
    @cached_tool(tier="live")
    async def _arun(
        self,
        time_range: str = "today",
        area: Optional[str] = None,
        severity_filter: Optional[str] = None,
        asset_id: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute safety events query and return structured results.

        AC#1-6: Complete safety events implementation

        Args:
            time_range: Time range to query (default: "today")
            area: Optional area name to filter by
            severity_filter: Optional severity level filter
            asset_id: Optional specific asset UUID

        Returns:
            ToolResult with SafetyEventsOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        # Build scope description for messages
        scope = self._build_scope_description(area, asset_id)

        logger.info(
            f"Safety events requested: time_range='{time_range}', "
            f"area='{area}', severity='{severity_filter}', asset_id='{asset_id}'"
        )

        try:
            # Parse time range (AC#1, AC#2)
            parsed_range = self._parse_time_range(time_range)

            # Query safety events with filters
            result = await data_source.get_safety_events(
                asset_id=asset_id,
                start_date=parsed_range.start,
                end_date=parsed_range.end,
                include_resolved=True,  # Include all for complete picture
                area=area,
                severity=severity_filter,
            )
            citations.append(self._result_to_citation(result))

            # Handle no data case (AC#4)
            if not result.has_data:
                return self._no_incidents_response(
                    scope, parsed_range.description, citations
                )

            # Sort events by severity (critical first), then recency (AC#1)
            sorted_events = self._sort_events(result.data)

            # Convert to output format
            event_details = [self._to_event_detail(e) for e in sorted_events]

            # Calculate summary statistics (AC#2)
            summary = self._calculate_summary(sorted_events)

            # Determine if this is a "no incidents" case
            no_incidents = len(sorted_events) == 0

            # Build output
            output = SafetyEventsOutput(
                scope=scope,
                time_range=parsed_range.description,
                events=event_details,
                total_count=len(sorted_events),
                summary=summary,
                message=self._build_message(sorted_events, scope, parsed_range.description),
                no_incidents=no_incidents,
                data_freshness=_utcnow().isoformat(),
            )

            # Generate follow-up questions
            follow_ups = self._generate_follow_ups(output)

            return self._create_success_result(
                data=output.model_dump(),
                citations=citations,
                metadata={
                    "cache_tier": "live",
                    "ttl_seconds": CACHE_TTL_LIVE,
                    "follow_up_questions": follow_ups,
                    "query_timestamp": _utcnow().isoformat(),
                },
            )

        except DataSourceError as e:
            logger.error(f"Data source error during safety events query: {e}")
            return self._create_error_result(
                f"Unable to retrieve safety data for {scope}. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during safety events query: {e}")
            return self._create_error_result(
                "An unexpected error occurred while querying safety events. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Time Range Parsing (AC#1)
    # =========================================================================

    def _parse_time_range(self, time_range: str) -> TimeRange:
        """
        Parse time range string into start and end dates.

        Supports:
        - "today" / "now"
        - "yesterday"
        - "this week"
        - "last 7 days" / "last N days"
        - "2026-01-01 to 2026-01-09" (explicit range)
        """
        today = date.today()
        time_range_lower = time_range.lower().strip()

        # Today
        if time_range_lower in ("today", "now"):
            return TimeRange(today, today, "today")

        # Yesterday
        if time_range_lower == "yesterday":
            yesterday = today - timedelta(days=1)
            return TimeRange(yesterday, yesterday, "yesterday")

        # This week (Monday to today)
        if time_range_lower == "this week":
            # Calculate Monday of current week
            monday = today - timedelta(days=today.weekday())
            return TimeRange(monday, today, "this week")

        # Last N days pattern
        last_n_match = re.match(r"last\s+(\d+)\s+days?", time_range_lower)
        if last_n_match:
            n_days = int(last_n_match.group(1))
            start = today - timedelta(days=n_days)
            return TimeRange(start, today, f"last {n_days} days")

        # Date range pattern: "YYYY-MM-DD to YYYY-MM-DD"
        range_match = re.match(
            r"(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})",
            time_range_lower
        )
        if range_match:
            start = date.fromisoformat(range_match.group(1))
            end = date.fromisoformat(range_match.group(2))
            return TimeRange(start, end, f"{start} to {end}")

        # Default to today if unrecognized
        logger.warning(f"Unrecognized time range '{time_range}', defaulting to 'today'")
        return TimeRange(today, today, "today")

    # =========================================================================
    # Event Sorting (AC#1)
    # =========================================================================

    def _sort_events(self, events: List[SafetyEvent]) -> List[SafetyEvent]:
        """
        Sort events by severity (critical first), then by recency (newest first).

        AC#1: Events are sorted by severity (critical first), then recency.
        """
        return sorted(
            events,
            key=lambda e: (
                SEVERITY_ORDER.get(e.severity.lower(), 99),  # Severity first
                -e.event_timestamp.timestamp(),  # Then recency (negative for descending)
            )
        )

    # =========================================================================
    # Event Conversion
    # =========================================================================

    def _to_event_detail(self, event: SafetyEvent) -> SafetyEventDetail:
        """Convert SafetyEvent to SafetyEventDetail output model."""
        return SafetyEventDetail(
            event_id=event.id,
            timestamp=event.event_timestamp.isoformat(),
            asset_id=event.asset_id,
            asset_name=event.asset_name,
            area=event.area,
            severity=event.severity,
            description=event.description,
            resolution_status=event.resolution_status,
            reported_by=event.reported_by,
        )

    # =========================================================================
    # Summary Statistics (AC#2)
    # =========================================================================

    def _calculate_summary(self, events: List[SafetyEvent]) -> SafetySummaryStats:
        """
        Calculate summary statistics for safety events.

        AC#2: Shows summary statistics (total events, resolved vs open).
        """
        # Initialize counts
        by_severity = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        by_status = {
            "open": 0,
            "under_investigation": 0,
            "resolved": 0,
        }

        for event in events:
            severity = event.severity.lower()
            if severity in by_severity:
                by_severity[severity] += 1

            status = event.resolution_status.lower()
            if status in by_status:
                by_status[status] += 1

        resolved_count = by_status["resolved"]
        open_count = by_status["open"] + by_status["under_investigation"]

        return SafetySummaryStats(
            total_events=len(events),
            by_severity=by_severity,
            by_status=by_status,
            resolved_count=resolved_count,
            open_count=open_count,
        )

    # =========================================================================
    # No Incidents Response (AC#4)
    # =========================================================================

    def _no_incidents_response(
        self,
        scope: str,
        time_range: str,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Generate positive response when no safety incidents found.

        AC#4: States "No safety incidents recorded for [scope] in [time range]"
        and presents this as positive news.
        """
        message = (
            f"No safety incidents recorded for {scope} in {time_range}. "
            "This is positive news for workplace safety!"
        )

        # Create empty summary
        summary = SafetySummaryStats(
            total_events=0,
            by_severity={"critical": 0, "high": 0, "medium": 0, "low": 0},
            by_status={"open": 0, "under_investigation": 0, "resolved": 0},
            resolved_count=0,
            open_count=0,
        )

        output = SafetyEventsOutput(
            scope=scope,
            time_range=time_range,
            events=[],
            total_count=0,
            summary=summary,
            message=message,
            no_incidents=True,
            data_freshness=_utcnow().isoformat(),
        )

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "cache_tier": "live",
                "ttl_seconds": CACHE_TTL_LIVE,
                "follow_up_questions": [
                    "Show me safety incidents from last week",
                    "What was our most recent safety incident?",
                ],
            },
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_scope_description(
        self,
        area: Optional[str],
        asset_id: Optional[str],
    ) -> str:
        """Build human-readable scope description."""
        if asset_id:
            return f"asset {asset_id}"
        elif area:
            return f"the {area} area"
        else:
            return "the plant"

    def _build_message(
        self,
        events: List[SafetyEvent],
        scope: str,
        time_range: str,
    ) -> Optional[str]:
        """Build contextual message based on results."""
        if not events:
            return (
                f"No safety incidents recorded for {scope} in {time_range}. "
                "This is positive news for workplace safety!"
            )

        # Count critical/high severity
        critical_count = sum(1 for e in events if e.severity.lower() == "critical")
        high_count = sum(1 for e in events if e.severity.lower() == "high")
        open_count = sum(
            1 for e in events if e.resolution_status.lower() != "resolved"
        )

        if critical_count > 0:
            return (
                f"Found {len(events)} safety incident(s) for {scope} in {time_range}. "
                f"ATTENTION: {critical_count} critical incident(s) require immediate action."
            )
        elif high_count > 0:
            return (
                f"Found {len(events)} safety incident(s) for {scope} in {time_range}. "
                f"Note: {high_count} high-severity incident(s) require attention."
            )
        elif open_count > 0:
            return (
                f"Found {len(events)} safety incident(s) for {scope} in {time_range}. "
                f"{open_count} incident(s) still open or under investigation."
            )
        else:
            return (
                f"Found {len(events)} safety incident(s) for {scope} in {time_range}. "
                "All incidents have been resolved."
            )

    def _generate_follow_ups(self, output: SafetyEventsOutput) -> List[str]:
        """
        Generate context-aware follow-up questions.

        Args:
            output: The safety events result

        Returns:
            List of suggested questions (max 3)
        """
        questions = []

        if output.total_count > 0:
            # If there are critical events, suggest drilling down
            if output.summary.by_severity.get("critical", 0) > 0:
                questions.append("Tell me more about the critical safety incidents")

            # If there are open events, suggest checking resolution
            if output.summary.open_count > 0:
                questions.append("What's the status of open safety incidents?")

            # Suggest area comparison if viewing plant-wide
            if output.scope == "the plant":
                questions.append("Which area has the most safety incidents?")

        # Always offer time comparison
        if output.time_range == "today":
            questions.append("How does this compare to yesterday?")
        elif output.time_range == "this week":
            questions.append("Show me safety trends for last month")

        return questions[:3]

    def _result_to_citation(self, result: DataResult) -> Citation:
        """
        Convert DataResult to Citation.

        AC#5: Citation Compliance - includes source table and timestamp.
        """
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
        )
