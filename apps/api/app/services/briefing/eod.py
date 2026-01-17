"""
End of Day Summary Service (Story 9.10)

Generates EOD summaries by orchestrating existing tools and comparing
against morning briefing predictions.

AC#1: EOD Summary Trigger - FR31
AC#2: Summary Content Structure
AC#3: No Morning Briefing Fallback

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
- [Source: prd/prd-functional-requirements.md#FR31-FR34]
"""

import logging
import asyncio
import sys
import uuid
from datetime import datetime, time, timezone, date
from typing import Optional, List, Dict, Any, Tuple

# Python 3.11+ has asyncio.timeout, earlier versions need async_timeout
if sys.version_info >= (3, 11):
    from asyncio import timeout as async_timeout
else:
    try:
        from async_timeout import timeout as async_timeout
    except ImportError:
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def async_timeout(seconds):
            """Simple timeout context manager fallback."""
            try:
                yield
            except asyncio.CancelledError:
                raise asyncio.TimeoutError()

from app.models.briefing import (
    BriefingSection,
    BriefingSectionStatus,
    BriefingResponseMetadata,
    BriefingData,
    ToolResultData,
    BriefingCitation,
    EODSummaryResponse,
    EODSection,
    MorningComparisonResult,
)
from app.services.briefing.service import (
    BriefingService,
    get_briefing_service,
    TOTAL_TIMEOUT_SECONDS,
    PER_TOOL_TIMEOUT_SECONDS,
)
from app.services.briefing.formatters import (
    format_number_for_voice,
    format_percentage_for_voice,
    format_duration_for_voice,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# EOD Timeout configuration (within NFR8: 30-second briefing)
EOD_TOTAL_TIMEOUT_SECONDS = 30
EOD_TOOL_ORCHESTRATION_TIMEOUT = 18
EOD_MORNING_LOOKUP_TIMEOUT = 2
EOD_COMPARISON_TIMEOUT = 3
EOD_NARRATIVE_TIMEOUT = 5

# Default day start time (06:00 AM)
DEFAULT_DAY_START_HOUR = 6


class MorningBriefingRecord:
    """Record of a morning briefing for comparison purposes."""

    def __init__(
        self,
        id: str,
        generated_at: datetime,
        concerns: List[str],
        wins: List[str],
        sections: List[Dict[str, Any]],
    ):
        self.id = id
        self.generated_at = generated_at
        self.concerns = concerns
        self.wins = wins
        self.sections = sections


class EODService:
    """
    Orchestrates End of Day summary generation (Story 9.10).

    AC#1: EOD Summary Trigger - FR31
    - Generates EOD summary for Plant Managers
    - Time range: 06:00 AM to current time

    AC#2: Summary Content Structure
    - Day's overall performance vs target
    - Comparison to morning briefing highlights
    - Wins that materialized
    - Concerns that escalated or resolved
    - Tomorrow's outlook

    AC#3: No Morning Briefing Fallback
    - Shows day's performance without comparison
    - Notes "No morning briefing to compare"

    This is NOT a ManufacturingTool - it's an orchestration layer.

    Usage:
        service = get_eod_service()
        summary = await service.generate_eod_summary(
            user_id="user123",
            date=datetime.now().date()
        )
    """

    def __init__(self, briefing_service: Optional[BriefingService] = None):
        """
        Initialize the EOD service.

        Args:
            briefing_service: Optional BriefingService instance (for testing)
        """
        self._briefing_service = briefing_service

    def _get_briefing_service(self) -> BriefingService:
        """Get the base briefing service."""
        if self._briefing_service is None:
            self._briefing_service = get_briefing_service()
        return self._briefing_service

    async def generate_eod_summary(
        self,
        user_id: str,
        summary_date: Optional[date] = None,
        include_audio: bool = True,
    ) -> EODSummaryResponse:
        """
        Generate End of Day summary for Plant Manager.

        AC#1: EOD Summary Trigger (FR31)
        AC#2: Summary Content Structure
        AC#3: No Morning Briefing Fallback

        Args:
            user_id: User requesting the EOD summary
            summary_date: Date to generate summary for (defaults to today)
            include_audio: Whether to include TTS audio URL

        Returns:
            EODSummaryResponse with all sections and comparison data
        """
        start_time = _utcnow()
        summary_id = str(uuid.uuid4())

        # Determine date and time range
        if summary_date is None:
            summary_date = datetime.now().date()

        # Time range: 06:00 AM to current time (or end of day)
        time_range_start = datetime.combine(
            summary_date,
            time(DEFAULT_DAY_START_HOUR, 0),
            tzinfo=timezone.utc
        )
        time_range_end = _utcnow()

        logger.info(
            f"Generating EOD summary {summary_id} for user {user_id}, "
            f"date={summary_date}, range={time_range_start} to {time_range_end}"
        )

        sections: List[BriefingSection] = []
        tool_failures: List[str] = []
        timed_out = False
        morning_briefing: Optional[MorningBriefingRecord] = None
        morning_comparison: Optional[MorningComparisonResult] = None

        try:
            async with async_timeout(EOD_TOTAL_TIMEOUT_SECONDS):
                # Step 1: Find morning briefing (if exists)
                morning_briefing = await self._find_morning_briefing(summary_date)

                # Step 2: Orchestrate tools for day's data
                briefing_data = await self._orchestrate_eod_tools(
                    time_range_start,
                    time_range_end
                )

                # Track failed tools
                tool_failures = briefing_data.failed_tools

                # Step 3: Generate comparison if morning briefing exists
                if morning_briefing:
                    morning_comparison = await self._compare_to_morning(
                        morning_briefing,
                        briefing_data
                    )

                # Step 4: Generate narrative sections
                sections = await self._generate_eod_narrative(
                    briefing_data,
                    morning_briefing,
                    morning_comparison
                )

        except asyncio.TimeoutError:
            logger.warning(
                f"EOD summary {summary_id} timed out after {EOD_TOTAL_TIMEOUT_SECONDS}s"
            )
            timed_out = True
            # Mark any incomplete sections as timed out
            for section in sections:
                if section.status == BriefingSectionStatus.PENDING:
                    section.status = BriefingSectionStatus.TIMED_OUT
                    section.error_message = "Generation timed out"

        except Exception as e:
            logger.error(f"EOD summary generation failed: {e}", exc_info=True)
            return self._create_error_response(summary_id, user_id, str(e))

        # Calculate completion
        completed_count = len([s for s in sections if s.is_complete])
        total_count = len(sections) if sections else 1
        completion_pct = (completed_count / total_count) * 100 if total_count > 0 else 0

        # Calculate duration
        end_time = _utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Estimate audio duration (~150 words/min, ~5 chars/word)
        total_chars = sum(len(s.content) for s in sections)
        duration_estimate_seconds = max(int(total_chars / 12.5), 60)  # Min 60s

        # Build response
        return EODSummaryResponse(
            id=summary_id,
            title=self._get_eod_title(summary_date),
            scope="eod",
            user_id=user_id,
            sections=sections,
            audio_stream_url=None,  # TTS integration handled separately (Story 8.1)
            total_duration_estimate=duration_estimate_seconds,
            metadata=BriefingResponseMetadata(
                generated_at=start_time,
                generation_duration_ms=duration_ms,
                completion_percentage=completion_pct,
                timed_out=timed_out,
                tool_failures=tool_failures,
                cache_hit=False,
            ),
            # EOD-specific fields
            morning_briefing_id=morning_briefing.id if morning_briefing else None,
            comparison_available=morning_briefing is not None,
            morning_comparison=morning_comparison,
            prediction_accuracy=None,  # For Story 9.11
            summary_date=datetime.combine(summary_date, time(0, 0), tzinfo=timezone.utc),
            time_range_start=time_range_start,
            time_range_end=time_range_end,
        )

    async def _find_morning_briefing(
        self,
        summary_date: date
    ) -> Optional[MorningBriefingRecord]:
        """
        Find this morning's briefing record for comparison.

        AC#3: Returns None if no briefing was generated today.

        Args:
            summary_date: Date to find morning briefing for

        Returns:
            MorningBriefingRecord if found, None otherwise
        """
        try:
            async with async_timeout(EOD_MORNING_LOOKUP_TIMEOUT):
                # For MVP, check the in-memory briefing store
                # In production, this would query a database table
                from app.api.briefing import _active_briefings

                # Find briefings from today that look like morning briefings
                for briefing_id, briefing in _active_briefings.items():
                    if briefing.metadata.generated_at.date() == summary_date:
                        # Check if it's a morning briefing (generated before noon)
                        gen_time = briefing.metadata.generated_at
                        if gen_time.hour < 12:
                            # Extract concerns and wins from sections
                            concerns = []
                            wins = []
                            sections_data = []

                            for section in briefing.sections:
                                sections_data.append({
                                    "type": section.section_type,
                                    "title": section.title,
                                    "content": section.content,
                                })
                                if section.section_type == "concerns":
                                    concerns.append(section.content)
                                elif section.section_type == "wins":
                                    wins.append(section.content)

                            return MorningBriefingRecord(
                                id=briefing_id,
                                generated_at=gen_time,
                                concerns=concerns,
                                wins=wins,
                                sections=sections_data,
                            )

                logger.info(f"No morning briefing found for {summary_date}")
                return None

        except asyncio.TimeoutError:
            logger.warning("Morning briefing lookup timed out")
            return None
        except Exception as e:
            logger.warning(f"Failed to find morning briefing: {e}")
            return None

    async def _orchestrate_eod_tools(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> BriefingData:
        """
        Orchestrate tool execution for EOD data.

        AC#1: Tool Orchestration for EOD context
        Uses the same tools as morning briefing with EOD-specific filtering.

        Args:
            start_time: Day start time (06:00 AM)
            end_time: Current time

        Returns:
            BriefingData with results from all tools
        """
        briefing_data = BriefingData()

        # Import tools
        from app.services.agent.tools.production_status import ProductionStatusTool
        from app.services.agent.tools.oee_query import OEEQueryTool
        from app.services.agent.tools.downtime_analysis import DowntimeAnalysisTool
        from app.services.agent.tools.safety_events import SafetyEventsTool
        from app.services.agent.tools.action_list import ActionListTool

        # Define tools to run in parallel
        tool_tasks = [
            self._run_tool_with_timeout(
                "production_status",
                self._get_production_status,
                ProductionStatusTool(),
                start_time,
                end_time
            ),
            self._run_tool_with_timeout(
                "oee_data",
                self._get_oee_data,
                OEEQueryTool()
            ),
            self._run_tool_with_timeout(
                "safety_events",
                self._get_safety_events,
                SafetyEventsTool()
            ),
            self._run_tool_with_timeout(
                "downtime_analysis",
                self._get_downtime_analysis,
                DowntimeAnalysisTool()
            ),
            self._run_tool_with_timeout(
                "action_list",
                self._get_action_list,
                ActionListTool()
            ),
        ]

        try:
            async with async_timeout(EOD_TOOL_ORCHESTRATION_TIMEOUT):
                results = await asyncio.gather(*tool_tasks, return_exceptions=True)

                # Map results to briefing data
                tool_names = [
                    "production_status", "oee_data", "safety_events",
                    "downtime_analysis", "action_list"
                ]

                for name, result in zip(tool_names, results):
                    if isinstance(result, Exception):
                        logger.error(f"Tool {name} raised exception: {result}")
                        setattr(briefing_data, name, ToolResultData(
                            tool_name=name,
                            success=False,
                            error_message=str(result),
                        ))
                    elif isinstance(result, ToolResultData):
                        setattr(briefing_data, name, result)
                    else:
                        logger.warning(f"Unexpected result type from {name}: {type(result)}")

        except asyncio.TimeoutError:
            logger.warning("Tool orchestration timed out")

        return briefing_data

    async def _run_tool_with_timeout(
        self,
        tool_name: str,
        tool_func,
        *args,
    ) -> ToolResultData:
        """
        Run a tool with individual timeout.

        AC#4: Graceful Tool Failure Handling
        """
        try:
            async with async_timeout(PER_TOOL_TIMEOUT_SECONDS):
                return await tool_func(*args)

        except asyncio.TimeoutError:
            logger.warning(f"Tool {tool_name} timed out after {PER_TOOL_TIMEOUT_SECONDS}s")
            return ToolResultData(
                tool_name=tool_name,
                success=False,
                error_message=f"Tool timed out after {PER_TOOL_TIMEOUT_SECONDS} seconds",
            )

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return ToolResultData(
                tool_name=tool_name,
                success=False,
                error_message=str(e),
            )

    async def _get_production_status(
        self,
        tool,
        start_time: datetime,
        end_time: datetime
    ) -> ToolResultData:
        """Get production status for the day."""
        try:
            # Query plant-wide production for the day
            result = await tool._arun(area=None)

            citations = [
                BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                for c in result.citations
            ] if hasattr(result, 'citations') and result.citations else []

            return ToolResultData(
                tool_name="production_status",
                success=result.success,
                data=result.data if result.success else None,
                citations=citations,
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(
                tool_name="production_status",
                success=False,
                error_message=str(e)
            )

    async def _get_oee_data(self, tool) -> ToolResultData:
        """Get OEE data for the day."""
        try:
            result = await tool._arun(scope="plant", days=1)

            citations = [
                BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                for c in result.citations
            ] if hasattr(result, 'citations') and result.citations else []

            return ToolResultData(
                tool_name="oee_data",
                success=result.success,
                data=result.data if result.success else None,
                citations=citations,
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(tool_name="oee_data", success=False, error_message=str(e))

    async def _get_safety_events(self, tool) -> ToolResultData:
        """Get safety events for the day."""
        try:
            result = await tool._arun(area=None, days=1)

            citations = [
                BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                for c in result.citations
            ] if hasattr(result, 'citations') and result.citations else []

            return ToolResultData(
                tool_name="safety_events",
                success=result.success,
                data=result.data if result.success else None,
                citations=citations,
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(tool_name="safety_events", success=False, error_message=str(e))

    async def _get_downtime_analysis(self, tool) -> ToolResultData:
        """Get downtime analysis for the day."""
        try:
            result = await tool._arun(area=None, days=1)

            citations = [
                BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                for c in result.citations
            ] if hasattr(result, 'citations') and result.citations else []

            return ToolResultData(
                tool_name="downtime_analysis",
                success=result.success,
                data=result.data if result.success else None,
                citations=citations,
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(
                tool_name="downtime_analysis",
                success=False,
                error_message=str(e)
            )

    async def _get_action_list(self, tool) -> ToolResultData:
        """Get action list status."""
        try:
            result = await tool._arun()

            citations = [
                BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                for c in result.citations
            ] if hasattr(result, 'citations') and result.citations else []

            return ToolResultData(
                tool_name="action_list",
                success=result.success,
                data=result.data if result.success else None,
                citations=citations,
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(tool_name="action_list", success=False, error_message=str(e))

    async def _compare_to_morning(
        self,
        morning_briefing: MorningBriefingRecord,
        briefing_data: BriefingData
    ) -> MorningComparisonResult:
        """
        Compare morning briefing predictions to actual outcomes.

        AC#2: Compare flagged concerns to actual outcomes

        Args:
            morning_briefing: This morning's briefing record
            briefing_data: Current day's actual data

        Returns:
            MorningComparisonResult with comparison details
        """
        try:
            async with async_timeout(EOD_COMPARISON_TIMEOUT):
                concerns_resolved = []
                concerns_escalated = []
                actual_wins = []

                # Analyze production status for wins
                if briefing_data.production_status and briefing_data.production_status.success:
                    data = briefing_data.production_status.data or {}
                    summary = data.get("summary", {})
                    variance = summary.get("total_variance_percent", 0)

                    if variance > 0:
                        actual_wins.append(
                            f"Production exceeded target by {format_percentage_for_voice(variance)}"
                        )

                    # Check assets that exceeded targets
                    ahead_count = summary.get("ahead_count", 0)
                    if ahead_count > 0:
                        actual_wins.append(f"{ahead_count} assets exceeded their targets")

                # Analyze safety - if no events, concern resolved
                if briefing_data.safety_events and briefing_data.safety_events.success:
                    data = briefing_data.safety_events.data or {}
                    if data.get("total_events", 0) == 0:
                        concerns_resolved.append("No safety incidents occurred")
                    else:
                        concerns_escalated.append(
                            f"{data.get('total_events')} safety event(s) occurred"
                        )

                # Generate summary
                summary_parts = []
                if actual_wins:
                    summary_parts.append(f"Today's wins: {'; '.join(actual_wins[:2])}")
                if concerns_resolved:
                    summary_parts.append(f"Resolved: {'; '.join(concerns_resolved[:2])}")
                if concerns_escalated:
                    summary_parts.append(f"Needs attention: {'; '.join(concerns_escalated[:2])}")

                prediction_summary = " ".join(summary_parts) if summary_parts else \
                    "Day proceeded as expected based on morning briefing."

                return MorningComparisonResult(
                    morning_briefing_id=morning_briefing.id,
                    morning_generated_at=morning_briefing.generated_at,
                    flagged_concerns=morning_briefing.concerns,
                    concerns_resolved=concerns_resolved,
                    concerns_escalated=concerns_escalated,
                    predicted_wins=morning_briefing.wins,
                    actual_wins=actual_wins,
                    prediction_summary=prediction_summary,
                )

        except asyncio.TimeoutError:
            logger.warning("Morning comparison timed out")
            return MorningComparisonResult(
                morning_briefing_id=morning_briefing.id,
                morning_generated_at=morning_briefing.generated_at,
                prediction_summary="Comparison timed out - showing available data only.",
            )

        except Exception as e:
            logger.error(f"Morning comparison failed: {e}")
            return MorningComparisonResult(
                morning_briefing_id=morning_briefing.id,
                morning_generated_at=morning_briefing.generated_at,
                prediction_summary="Unable to complete morning comparison.",
            )

    async def _generate_eod_narrative(
        self,
        briefing_data: BriefingData,
        morning_briefing: Optional[MorningBriefingRecord],
        morning_comparison: Optional[MorningComparisonResult],
    ) -> List[BriefingSection]:
        """
        Generate EOD narrative sections.

        AC#2: Summary Content Structure
        - Day's overall performance vs target
        - Comparison to morning briefing highlights
        - Wins that materialized
        - Concerns that escalated or resolved
        - Tomorrow's outlook

        AC#3: No Morning Briefing Fallback
        """
        try:
            async with async_timeout(EOD_NARRATIVE_TIMEOUT):
                sections = []
                all_citations = briefing_data.all_citations

                # Section 1: Day's Performance
                sections.append(self._generate_performance_section(briefing_data, all_citations))

                # Section 2: Morning Comparison (or fallback)
                sections.append(self._generate_comparison_section(
                    morning_briefing,
                    morning_comparison,
                    all_citations
                ))

                # Section 3: Wins That Materialized
                sections.append(self._generate_wins_section(
                    briefing_data,
                    morning_comparison,
                    all_citations
                ))

                # Section 4: Concerns Resolved/Escalated
                sections.append(self._generate_concerns_section(
                    briefing_data,
                    morning_comparison,
                    all_citations
                ))

                # Section 5: Tomorrow's Outlook
                sections.append(self._generate_outlook_section(
                    briefing_data,
                    all_citations
                ))

                return sections

        except asyncio.TimeoutError:
            logger.warning("EOD narrative generation timed out")
            return self._create_fallback_sections(briefing_data)

        except Exception as e:
            logger.error(f"EOD narrative generation failed: {e}")
            return self._create_fallback_sections(briefing_data)

    def _generate_performance_section(
        self,
        briefing_data: BriefingData,
        citations: List[BriefingCitation]
    ) -> BriefingSection:
        """Generate the Day's Performance section."""
        parts = []

        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})

            output = summary.get("total_output")
            target = summary.get("total_target")
            variance = summary.get("total_variance_percent", 0)

            if output is not None:
                output_formatted = format_number_for_voice(output, "units")
                parts.append(f"Today's total output: {output_formatted}.")

            if target is not None:
                target_formatted = format_number_for_voice(target, "units")
                parts.append(f"Target was {target_formatted}.")

            if variance >= 0:
                variance_formatted = format_percentage_for_voice(variance)
                parts.append(f"We finished {variance_formatted} ahead of target.")
            else:
                variance_formatted = format_percentage_for_voice(abs(variance))
                parts.append(f"We finished {variance_formatted} behind target.")

        # OEE summary
        if briefing_data.oee_data and briefing_data.oee_data.success:
            data = briefing_data.oee_data.data or {}
            oee = data.get("oee_percentage", data.get("oee"))
            if oee is not None:
                oee_formatted = format_percentage_for_voice(oee)
                parts.append(f"Plant OEE for the day: {oee_formatted}. [Source: daily_summaries]")

        content = " ".join(parts) if parts else \
            "Production data is being finalized. Check the dashboard for current status."

        return BriefingSection(
            section_type=EODSection.PERFORMANCE.value,
            title="Day's Performance",
            content=content,
            citations=citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        )

    def _generate_comparison_section(
        self,
        morning_briefing: Optional[MorningBriefingRecord],
        morning_comparison: Optional[MorningComparisonResult],
        citations: List[BriefingCitation]
    ) -> BriefingSection:
        """Generate the Morning Comparison section (or fallback)."""
        # AC#3: No Morning Briefing Fallback
        if morning_briefing is None:
            return BriefingSection(
                section_type=EODSection.COMPARISON.value,
                title="Morning Comparison",
                content=(
                    "No morning briefing was generated today. "
                    "Showing day's performance without comparison to morning predictions."
                ),
                citations=[],
                status=BriefingSectionStatus.COMPLETE,
                pause_point=False,
            )

        # Morning briefing exists - show comparison
        if morning_comparison:
            content = morning_comparison.prediction_summary
        else:
            content = (
                f"Morning briefing was generated at "
                f"{morning_briefing.generated_at.strftime('%I:%M %p')}. "
                "Detailed comparison data is being processed."
            )

        return BriefingSection(
            section_type=EODSection.COMPARISON.value,
            title="Morning vs Actual",
            content=content,
            citations=citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        )

    def _generate_wins_section(
        self,
        briefing_data: BriefingData,
        morning_comparison: Optional[MorningComparisonResult],
        citations: List[BriefingCitation]
    ) -> BriefingSection:
        """Generate the Wins That Materialized section."""
        wins = []

        # Get wins from comparison
        if morning_comparison and morning_comparison.actual_wins:
            wins.extend(morning_comparison.actual_wins)

        # Check production for additional wins
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})

            ahead_count = summary.get("ahead_count", 0)
            if ahead_count > 0 and f"{ahead_count} assets" not in str(wins):
                wins.append(f"{ahead_count} assets finished ahead of their targets")

            # Check for top performers
            assets = data.get("assets", [])
            top_performers = [
                a.get("asset_name") for a in assets
                if a.get("status") == "ahead"
            ][:2]
            if top_performers:
                wins.append(f"Top performers: {', '.join(top_performers)}")

        # Safety win if no incidents
        if briefing_data.safety_events and briefing_data.safety_events.success:
            data = briefing_data.safety_events.data or {}
            if data.get("total_events", 0) == 0 and "No safety" not in str(wins):
                wins.append("Clean safety record - no incidents today")

        if wins:
            content = f"Today's wins: {'; '.join(wins[:3])}. [Source: live_snapshots]"
        else:
            content = "Keep up the momentum - every day builds on our progress."

        return BriefingSection(
            section_type=EODSection.WINS.value,
            title="Wins That Materialized",
            content=content,
            citations=citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        )

    def _generate_concerns_section(
        self,
        briefing_data: BriefingData,
        morning_comparison: Optional[MorningComparisonResult],
        citations: List[BriefingCitation]
    ) -> BriefingSection:
        """Generate the Concerns Resolved/Escalated section."""
        resolved = []
        escalated = []

        # Get from comparison
        if morning_comparison:
            resolved.extend(morning_comparison.concerns_resolved)
            escalated.extend(morning_comparison.concerns_escalated)

        # Check current data for concerns
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})

            behind_count = summary.get("behind_count", 0)
            if behind_count > 0:
                attention = summary.get("assets_needing_attention", [])[:2]
                if attention:
                    escalated.append(f"{', '.join(attention)} behind target")

        # Downtime concerns
        if briefing_data.downtime_analysis and briefing_data.downtime_analysis.success:
            data = briefing_data.downtime_analysis.data or {}
            reasons = data.get("top_reasons", [])
            if reasons:
                top = reasons[0]
                duration = top.get("duration_minutes", 0)
                if duration > 30:  # Significant downtime
                    reason = top.get("reason", "unplanned downtime")
                    duration_formatted = format_duration_for_voice(duration)
                    escalated.append(
                        f"{reason} caused {duration_formatted} of downtime"
                    )

        # Build content
        parts = []
        if resolved:
            parts.append(f"Resolved today: {'; '.join(resolved[:2])}")
        if escalated:
            parts.append(f"Needs follow-up: {'; '.join(escalated[:2])}")

        if parts:
            content = f"{' '.join(parts)}. [Source: live_snapshots, downtime_events]"
        else:
            content = "No major concerns carried over. Great work keeping things on track!"

        return BriefingSection(
            section_type=EODSection.CONCERNS.value,
            title="Concerns Status",
            content=content,
            citations=citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        )

    def _generate_outlook_section(
        self,
        briefing_data: BriefingData,
        citations: List[BriefingCitation]
    ) -> BriefingSection:
        """Generate Tomorrow's Outlook section."""
        parts = []

        # Check for carry-forward issues
        if briefing_data.action_list and briefing_data.action_list.success:
            data = briefing_data.action_list.data or {}
            actions = data.get("actions", [])
            pending = [a for a in actions if a.get("status") != "completed"][:2]
            if pending:
                action_items = "; ".join([a.get("title", "Action") for a in pending])
                parts.append(f"Carry-forward priorities: {action_items}")

        # Check for ongoing concerns
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})
            attention = summary.get("assets_needing_attention", [])[:1]
            if attention:
                parts.append(f"Monitor {attention[0]} closely tomorrow")

        # Downtime patterns
        if briefing_data.downtime_analysis and briefing_data.downtime_analysis.success:
            data = briefing_data.downtime_analysis.data or {}
            reasons = data.get("top_reasons", [])
            if reasons:
                top_reason = reasons[0].get("reason", "")
                if top_reason and "maintenance" not in top_reason.lower():
                    parts.append(f"Watch for recurring {top_reason.lower()}")

        if parts:
            content = f"Tomorrow's focus: {' '.join(parts)}. [Source: action_recommendations]"
        else:
            content = (
                "Tomorrow looks clear. Focus on maintaining today's momentum and "
                "addressing any overnight alerts. [Source: action_recommendations]"
            )

        return BriefingSection(
            section_type=EODSection.OUTLOOK.value,
            title="Tomorrow's Outlook",
            content=content,
            citations=citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        )

    def _create_fallback_sections(
        self,
        briefing_data: BriefingData
    ) -> List[BriefingSection]:
        """Create fallback sections when narrative generation fails."""
        return [
            BriefingSection(
                section_type=EODSection.PERFORMANCE.value,
                title="Day's Performance",
                content="End of day summary is being generated. Please check the dashboard for current status.",
                status=BriefingSectionStatus.PARTIAL,
                pause_point=True,
            ),
            BriefingSection(
                section_type=EODSection.COMPARISON.value,
                title="Morning Comparison",
                content="Comparison data is being processed.",
                status=BriefingSectionStatus.PARTIAL,
                pause_point=False,
            ),
        ]

    def _create_error_response(
        self,
        summary_id: str,
        user_id: str,
        error_message: str,
    ) -> EODSummaryResponse:
        """Create error response when generation fails completely."""
        return EODSummaryResponse(
            id=summary_id,
            title="End of Day Summary Unavailable",
            scope="error",
            user_id=user_id,
            sections=[
                BriefingSection(
                    section_type="error",
                    title="Unable to Generate EOD Summary",
                    content=(
                        "We encountered an error generating your end of day summary. "
                        "Please try again in a few minutes. "
                        f"Error: {error_message}"
                    ),
                    status=BriefingSectionStatus.FAILED,
                    error_message=error_message,
                )
            ],
            metadata=BriefingResponseMetadata(
                completion_percentage=0,
                timed_out=False,
                tool_failures=["all"],
            ),
            comparison_available=False,
        )

    def _get_eod_title(self, summary_date: date) -> str:
        """Get the EOD summary title."""
        date_str = summary_date.strftime("%A, %B %d")
        return f"End of Day Summary - {date_str}"


# Module-level singleton
_eod_service: Optional[EODService] = None


def get_eod_service() -> EODService:
    """
    Get the singleton EODService instance.

    Returns:
        EODService singleton instance
    """
    global _eod_service
    if _eod_service is None:
        _eod_service = EODService()
    return _eod_service
