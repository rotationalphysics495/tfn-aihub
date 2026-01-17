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
import re
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
        async def async_timeout(seconds: float):
            """
            Simple timeout context manager fallback for Python < 3.11.

            Note: This fallback uses asyncio.wait_for pattern.
            For proper timeout support, install async_timeout package.
            """
            # Create a task that will be cancelled after timeout
            loop = asyncio.get_event_loop()

            async def _timeout_task():
                await asyncio.sleep(seconds)
                raise asyncio.TimeoutError(f"Operation timed out after {seconds}s")

            timeout_task = loop.create_task(_timeout_task())
            try:
                yield
            finally:
                timeout_task.cancel()
                try:
                    await timeout_task
                except asyncio.CancelledError:
                    pass

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
    # Story 9.11 models
    ConcernOutcome,
    ConcernComparison,
    AccuracyMetrics,
    EODComparisonResult,
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

# Timeouts for Story 9.11 comparison operations
EOD_ACCURACY_CALCULATION_TIMEOUT = 2


class MorningConcern:
    """A concern flagged in the morning briefing."""

    def __init__(
        self,
        concern_id: str,
        description: str,
        issue_type: str,
        severity: str = "medium",
        asset_id: Optional[str] = None,
        asset_name: Optional[str] = None,
        area: Optional[str] = None,
    ):
        self.concern_id = concern_id
        self.description = description
        self.issue_type = issue_type
        self.severity = severity
        self.asset_id = asset_id
        self.asset_name = asset_name
        self.area = area


class MorningBriefingRecord:
    """Record of a morning briefing for comparison purposes."""

    def __init__(
        self,
        id: str,
        generated_at: datetime,
        concerns: List[str],
        wins: List[str],
        sections: List[Dict[str, Any]],
        structured_concerns: Optional[List[MorningConcern]] = None,
    ):
        self.id = id
        self.generated_at = generated_at
        self.concerns = concerns
        self.wins = wins
        self.sections = sections
        self.structured_concerns = structured_concerns or []


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
        # Story 9.11: Enhanced comparison data
        eod_comparison_result: Optional[EODComparisonResult] = None
        prediction_accuracy: Optional[float] = None

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

                    # Story 9.11: Perform detailed comparison with accuracy metrics
                    structured_concerns = self._extract_structured_concerns(morning_briefing)
                    comparisons = await self._compare_concerns_to_actuals(
                        structured_concerns,
                        briefing_data
                    )
                    unexpected_issues = self._detect_unexpected_issues(
                        structured_concerns,
                        briefing_data
                    )
                    accuracy_metrics = self._calculate_accuracy_metrics(
                        comparisons,
                        unexpected_issues
                    )

                    eod_comparison_result = EODComparisonResult(
                        morning_briefing_id=morning_briefing.id,
                        morning_generated_at=morning_briefing.generated_at,
                        eod_summary_id=summary_id,
                        comparisons=comparisons,
                        accuracy_metrics=accuracy_metrics,
                        unexpected_issues=unexpected_issues,
                        comparison_summary=self._generate_comparison_summary(
                            comparisons,
                            accuracy_metrics,
                            unexpected_issues
                        ),
                        has_morning_briefing=True,
                    )
                    prediction_accuracy = accuracy_metrics.accuracy_percentage

                    # Store accuracy metrics for trend tracking (AC#4)
                    await self.store_accuracy_metrics(
                        user_id,
                        summary_date,
                        eod_comparison_result,
                        summary_id
                    )

                # Step 4: Generate narrative sections
                sections = await self._generate_eod_narrative(
                    briefing_data,
                    morning_briefing,
                    morning_comparison,
                    eod_comparison_result,  # Story 9.11: Pass comparison result
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
            prediction_accuracy=prediction_accuracy,  # Story 9.11: Accuracy percentage
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
        eod_comparison_result: Optional[EODComparisonResult] = None,  # Story 9.11
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

        Story 9.11 Enhancement:
        - Integrates detailed comparison results with accuracy metrics
        """
        try:
            async with async_timeout(EOD_NARRATIVE_TIMEOUT):
                sections = []
                all_citations = briefing_data.all_citations

                # Section 1: Day's Performance
                sections.append(self._generate_performance_section(briefing_data, all_citations))

                # Section 2: Morning Comparison (or fallback) - Story 9.11 Enhanced
                sections.append(self._generate_comparison_section(
                    morning_briefing,
                    morning_comparison,
                    all_citations,
                    eod_comparison_result,  # Story 9.11: Pass enhanced comparison
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
                    all_citations,
                    eod_comparison_result,  # Story 9.11: Pass enhanced comparison
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
        citations: List[BriefingCitation],
        eod_comparison_result: Optional[EODComparisonResult] = None,  # Story 9.11
    ) -> BriefingSection:
        """
        Generate the Morning Comparison section (or fallback).

        Story 9.11 Enhancement: Includes accuracy metrics in comparison.
        """
        # AC#5: No Morning Briefing Handling
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

        # Story 9.11: Use enhanced comparison if available (AC#2, AC#3)
        if eod_comparison_result and eod_comparison_result.has_morning_briefing:
            # Build enhanced content with accuracy metrics
            parts = []

            # Include accuracy (AC#3)
            accuracy = eod_comparison_result.accuracy_metrics.accuracy_percentage
            parts.append(
                f"Morning prediction accuracy: {format_percentage_for_voice(accuracy)}."
            )

            # Outcome counts (AC#2)
            metrics = eod_comparison_result.accuracy_metrics
            if metrics.correct_predictions > 0:
                parts.append(
                    f"{metrics.correct_predictions} prediction(s) correct."
                )
            if metrics.false_positives > 0:
                parts.append(
                    f"{metrics.false_positives} concern(s) did not materialize (false positives)."
                )
            if metrics.misses > 0:
                parts.append(
                    f"{metrics.misses} issue(s) occurred that were not predicted (misses)."
                )

            # Add comparison summary
            if eod_comparison_result.comparison_summary:
                parts.append(eod_comparison_result.comparison_summary)

            content = " ".join(parts)
            content += " [Source: morning_briefing, daily_summaries]"

        # Fallback to basic comparison
        elif morning_comparison:
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
        citations: List[BriefingCitation],
        eod_comparison_result: Optional[EODComparisonResult] = None,  # Story 9.11
    ) -> BriefingSection:
        """
        Generate the Concerns Resolved/Escalated section.

        Story 9.11 Enhancement: Uses detailed outcome classification.
        """
        resolved = []
        escalated = []
        materialized = []
        unexpected = []

        # Story 9.11: Use enhanced comparison if available (AC#2)
        if eod_comparison_result and eod_comparison_result.comparisons:
            for comparison in eod_comparison_result.comparisons:
                if comparison.outcome == ConcernOutcome.AVERTED:
                    resolved.append(comparison.morning_description[:80])
                elif comparison.outcome == ConcernOutcome.ESCALATED:
                    escalated.append(comparison.actual_description or comparison.morning_description[:80])
                elif comparison.outcome == ConcernOutcome.MATERIALIZED:
                    materialized.append(comparison.actual_description or comparison.morning_description[:80])

            # Add unexpected issues
            unexpected.extend(eod_comparison_result.unexpected_issues[:2])

        # Fallback to basic comparison
        elif morning_comparison:
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

        # Build content with Story 9.11 outcome classification (AC#2)
        parts = []
        if materialized:
            parts.append(f"Materialized: {'; '.join(materialized[:2])}")
        if resolved:
            parts.append(f"Averted: {'; '.join(resolved[:2])}")
        if escalated:
            parts.append(f"Escalated: {'; '.join(escalated[:2])}")
        if unexpected:
            parts.append(f"Unexpected: {'; '.join(unexpected[:2])}")

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

    # =========================================================================
    # Story 9.11: Morning vs Actual Comparison Methods
    # =========================================================================

    async def compare_to_morning_briefing(
        self,
        user_id: str,
        summary_date: Optional[date] = None,
    ) -> EODComparisonResult:
        """
        Compare morning briefing predictions to actual outcomes (Story 9.11 AC#1).

        Main entry point for comparison functionality. Retrieves morning briefing,
        compares flagged concerns to actual outcomes, and calculates accuracy metrics.

        Args:
            user_id: User ID to retrieve morning briefing for
            summary_date: Date to compare (defaults to today)

        Returns:
            EODComparisonResult with comparisons and metrics
        """
        if summary_date is None:
            summary_date = datetime.now().date()

        logger.info(
            f"Comparing morning briefing to actual outcomes for user {user_id}, "
            f"date={summary_date}"
        )

        # Step 1: Retrieve morning briefing (AC#1)
        morning_briefing = await self._find_morning_briefing(summary_date)

        # AC#5: Handle no morning briefing case
        if morning_briefing is None:
            logger.info(f"No morning briefing found for {summary_date}")
            return EODComparisonResult(
                has_morning_briefing=False,
                comparison_summary=(
                    "No morning briefing to compare. "
                    "Showing day's performance without prediction comparison."
                ),
            )

        # Step 2: Get actual outcomes from tools
        time_range_start = datetime.combine(
            summary_date,
            time(DEFAULT_DAY_START_HOUR, 0),
            tzinfo=timezone.utc
        )
        time_range_end = _utcnow()

        briefing_data = await self._orchestrate_eod_tools(
            time_range_start,
            time_range_end
        )

        # Step 3: Extract structured concerns from morning briefing
        structured_concerns = self._extract_structured_concerns(morning_briefing)

        # Step 4: Perform detailed comparison (AC#2)
        comparisons = await self._compare_concerns_to_actuals(
            structured_concerns,
            briefing_data
        )

        # Step 5: Detect unexpected issues (AC#2 - UNEXPECTED classification)
        unexpected_issues = self._detect_unexpected_issues(
            structured_concerns,
            briefing_data
        )

        # Step 6: Calculate accuracy metrics (AC#3)
        accuracy_metrics = self._calculate_accuracy_metrics(
            comparisons,
            unexpected_issues
        )

        # Step 7: Generate comparison summary
        comparison_summary = self._generate_comparison_summary(
            comparisons,
            accuracy_metrics,
            unexpected_issues
        )

        return EODComparisonResult(
            morning_briefing_id=morning_briefing.id,
            morning_generated_at=morning_briefing.generated_at,
            comparisons=comparisons,
            accuracy_metrics=accuracy_metrics,
            unexpected_issues=unexpected_issues,
            comparison_summary=comparison_summary,
            has_morning_briefing=True,
        )

    def _extract_structured_concerns(
        self,
        morning_briefing: MorningBriefingRecord
    ) -> List[MorningConcern]:
        """
        Extract structured concerns from morning briefing (Story 9.11 Task 2.2).

        Parses the morning briefing sections to extract concerns with
        asset/area information for matching.

        Args:
            morning_briefing: The morning briefing record

        Returns:
            List of MorningConcern objects
        """
        # If structured concerns already exist, use them
        if morning_briefing.structured_concerns:
            return morning_briefing.structured_concerns

        structured_concerns: List[MorningConcern] = []
        concern_id = 0

        for section in morning_briefing.sections:
            section_type = section.get("type", "")
            content = section.get("content", "")

            # Extract concerns from concern sections
            if section_type == "concerns":
                concern_id += 1
                # Parse content to determine issue type
                issue_type = self._infer_issue_type(content)

                # Try to extract asset/area from content
                asset_info = self._extract_asset_info(content)

                structured_concerns.append(MorningConcern(
                    concern_id=f"mc-{concern_id}",
                    description=content,
                    issue_type=issue_type,
                    severity=self._infer_severity(content),
                    asset_id=asset_info.get("asset_id"),
                    asset_name=asset_info.get("asset_name"),
                    area=asset_info.get("area"),
                ))

        # Also parse concern strings from the briefing
        for concern_text in morning_briefing.concerns:
            concern_id += 1
            issue_type = self._infer_issue_type(concern_text)
            asset_info = self._extract_asset_info(concern_text)

            structured_concerns.append(MorningConcern(
                concern_id=f"mc-{concern_id}",
                description=concern_text,
                issue_type=issue_type,
                severity=self._infer_severity(concern_text),
                asset_id=asset_info.get("asset_id"),
                asset_name=asset_info.get("asset_name"),
                area=asset_info.get("area"),
            ))

        return structured_concerns

    def _infer_issue_type(self, content: str) -> str:
        """Infer issue type from content text."""
        content_lower = content.lower()
        if any(word in content_lower for word in ["safety", "incident", "injury", "hazard"]):
            return "safety"
        elif any(word in content_lower for word in ["downtime", "offline", "stopped", "maintenance"]):
            return "downtime"
        elif any(word in content_lower for word in ["quality", "defect", "reject", "scrap"]):
            return "quality"
        else:
            return "production"

    def _infer_severity(self, content: str) -> str:
        """Infer severity from content text."""
        content_lower = content.lower()
        if any(word in content_lower for word in ["critical", "severe", "urgent", "high"]):
            return "high"
        elif any(word in content_lower for word in ["minor", "low", "small"]):
            return "low"
        else:
            return "medium"

    def _extract_asset_info(self, content: str) -> Dict[str, Optional[str]]:
        """Extract asset/area information from content."""
        # Simple extraction - can be enhanced with NLP
        # Look for common patterns like "Line 1", "Area A", asset names
        result: Dict[str, Optional[str]] = {
            "asset_id": None,
            "asset_name": None,
            "area": None,
        }

        # Look for line references
        line_match = re.search(r"[Ll]ine\s*(\d+|[A-Za-z])", content)
        if line_match:
            result["asset_name"] = f"Line {line_match.group(1)}"

        # Look for area references
        area_match = re.search(r"[Aa]rea\s*(\d+|[A-Za-z])", content)
        if area_match:
            result["area"] = f"Area {area_match.group(1)}"

        return result

    async def _compare_concerns_to_actuals(
        self,
        concerns: List[MorningConcern],
        briefing_data: BriefingData
    ) -> List[ConcernComparison]:
        """
        Compare morning concerns to actual outcomes (Story 9.11 AC#2 Task 3.1-3.2).

        Matches each concern to actual data and classifies the outcome.

        Args:
            concerns: List of morning concerns
            briefing_data: Actual day data from tools

        Returns:
            List of ConcernComparison objects
        """
        comparisons: List[ConcernComparison] = []

        for concern in concerns:
            outcome, actual_description, notes = self._classify_concern_outcome(
                concern,
                briefing_data
            )

            comparisons.append(ConcernComparison(
                concern_id=concern.concern_id,
                asset_id=concern.asset_id,
                asset_name=concern.asset_name,
                area=concern.area,
                issue_type=concern.issue_type,
                morning_description=concern.description,
                morning_severity=concern.severity,
                actual_description=actual_description,
                outcome=outcome,
                notes=notes,
            ))

        return comparisons

    def _classify_concern_outcome(
        self,
        concern: MorningConcern,
        briefing_data: BriefingData
    ) -> Tuple[ConcernOutcome, Optional[str], Optional[str]]:
        """
        Classify the outcome for a single concern (Story 9.11 AC#2 Task 3.2).

        Args:
            concern: The morning concern to classify
            briefing_data: Actual day data

        Returns:
            Tuple of (outcome, actual_description, notes)
        """
        issue_type = concern.issue_type

        # Safety concerns
        if issue_type == "safety":
            return self._classify_safety_concern(concern, briefing_data)

        # Downtime concerns
        elif issue_type == "downtime":
            return self._classify_downtime_concern(concern, briefing_data)

        # Quality concerns
        elif issue_type == "quality":
            return self._classify_quality_concern(concern, briefing_data)

        # Production concerns
        else:
            return self._classify_production_concern(concern, briefing_data)

    def _classify_safety_concern(
        self,
        concern: MorningConcern,
        briefing_data: BriefingData
    ) -> Tuple[ConcernOutcome, Optional[str], Optional[str]]:
        """Classify safety concern outcome."""
        if not briefing_data.safety_events or not briefing_data.safety_events.success:
            return (
                ConcernOutcome.AVERTED,
                "Unable to verify - no safety data available",
                "Safety data unavailable for comparison"
            )

        data = briefing_data.safety_events.data or {}
        total_events = data.get("total_events", 0)

        if total_events == 0:
            return (
                ConcernOutcome.AVERTED,
                "No safety incidents occurred today",
                "Concern was successfully addressed or didn't materialize"
            )

        # Check if any events match the concern's area/asset
        events = data.get("events", [])
        matching_events = []

        for event in events:
            event_area = event.get("area", "")
            if concern.area and concern.area.lower() in event_area.lower():
                matching_events.append(event)
            elif concern.asset_name and concern.asset_name.lower() in str(event).lower():
                matching_events.append(event)

        if matching_events:
            # Check severity escalation
            if concern.severity == "medium" and any(
                e.get("severity") == "high" for e in matching_events
            ):
                return (
                    ConcernOutcome.ESCALATED,
                    f"Safety incident occurred and was more severe than predicted",
                    f"{len(matching_events)} matching event(s) found"
                )
            return (
                ConcernOutcome.MATERIALIZED,
                f"Safety incident occurred as predicted",
                f"{len(matching_events)} matching event(s) found"
            )

        return (
            ConcernOutcome.AVERTED,
            f"Safety concern did not materialize ({total_events} unrelated events)",
            "No matching safety events for this concern"
        )

    def _classify_downtime_concern(
        self,
        concern: MorningConcern,
        briefing_data: BriefingData
    ) -> Tuple[ConcernOutcome, Optional[str], Optional[str]]:
        """Classify downtime concern outcome."""
        if not briefing_data.downtime_analysis or not briefing_data.downtime_analysis.success:
            return (
                ConcernOutcome.AVERTED,
                "Unable to verify - no downtime data available",
                "Downtime data unavailable for comparison"
            )

        data = briefing_data.downtime_analysis.data or {}
        total_minutes = data.get("total_downtime_minutes", 0)
        top_reasons = data.get("top_reasons", [])

        if total_minutes == 0:
            return (
                ConcernOutcome.AVERTED,
                "No downtime occurred today",
                "Concern was successfully prevented"
            )

        # Check for matching downtime by reason or asset
        concern_keywords = concern.description.lower().split()
        matched_downtime = 0

        for reason in top_reasons:
            reason_text = reason.get("reason", "").lower()
            if any(keyword in reason_text for keyword in concern_keywords if len(keyword) > 3):
                matched_downtime += reason.get("duration_minutes", 0)

        if matched_downtime > 0:
            duration_formatted = format_duration_for_voice(matched_downtime)
            # Check if worse than expected
            if matched_downtime > 60:  # More than 1 hour is escalation threshold
                return (
                    ConcernOutcome.ESCALATED,
                    f"Downtime of {duration_formatted} occurred - exceeded expectations",
                    "Issue was more impactful than predicted"
                )
            return (
                ConcernOutcome.MATERIALIZED,
                f"Downtime of {duration_formatted} occurred as predicted",
                "Concern materialized"
            )

        return (
            ConcernOutcome.AVERTED,
            f"Predicted downtime didn't occur (total: {format_duration_for_voice(total_minutes)})",
            "No matching downtime events"
        )

    def _classify_quality_concern(
        self,
        concern: MorningConcern,
        briefing_data: BriefingData
    ) -> Tuple[ConcernOutcome, Optional[str], Optional[str]]:
        """Classify quality concern outcome."""
        # Quality data might come from OEE (quality component) or production status
        if briefing_data.oee_data and briefing_data.oee_data.success:
            data = briefing_data.oee_data.data or {}
            quality_rate = data.get("quality_rate", data.get("quality", 100))

            if quality_rate is not None and quality_rate < 95:
                return (
                    ConcernOutcome.MATERIALIZED,
                    f"Quality rate at {format_percentage_for_voice(quality_rate)}",
                    "Quality issues occurred as predicted"
                )
            elif quality_rate is not None and quality_rate >= 98:
                return (
                    ConcernOutcome.AVERTED,
                    f"Quality maintained at {format_percentage_for_voice(quality_rate)}",
                    "Quality concern was addressed successfully"
                )

        return (
            ConcernOutcome.AVERTED,
            "Quality concern did not materialize",
            "No quality issues detected in today's data"
        )

    def _classify_production_concern(
        self,
        concern: MorningConcern,
        briefing_data: BriefingData
    ) -> Tuple[ConcernOutcome, Optional[str], Optional[str]]:
        """Classify production concern outcome."""
        if not briefing_data.production_status or not briefing_data.production_status.success:
            return (
                ConcernOutcome.AVERTED,
                "Unable to verify - no production data available",
                "Production data unavailable for comparison"
            )

        data = briefing_data.production_status.data or {}
        summary = data.get("summary", {})
        variance = summary.get("total_variance_percent", 0)
        behind_count = summary.get("behind_count", 0)

        # Check if concern was about being behind target
        if behind_count > 0 and variance < 0:
            if variance < -10:  # Significantly behind
                return (
                    ConcernOutcome.ESCALATED,
                    f"Production {format_percentage_for_voice(abs(variance))} behind target",
                    f"{behind_count} assets behind schedule"
                )
            return (
                ConcernOutcome.MATERIALIZED,
                f"Production slightly behind ({format_percentage_for_voice(abs(variance))})",
                "Production concern materialized"
            )

        elif variance >= 0:
            return (
                ConcernOutcome.AVERTED,
                f"Production on/ahead of target ({format_percentage_for_voice(variance)} ahead)",
                "Production concern was addressed successfully"
            )

        return (
            ConcernOutcome.AVERTED,
            "Production concern did not materialize",
            "No significant production issues"
        )

    def _detect_unexpected_issues(
        self,
        concerns: List[MorningConcern],
        briefing_data: BriefingData
    ) -> List[str]:
        """
        Detect unexpected issues not predicted in morning (Story 9.11 AC#2 Task 3.3).

        Args:
            concerns: List of morning concerns
            briefing_data: Actual day data

        Returns:
            List of unexpected issue descriptions
        """
        unexpected: List[str] = []
        concern_types = {c.issue_type for c in concerns}
        concern_text = " ".join(c.description.lower() for c in concerns)

        # Check for unexpected safety events
        if briefing_data.safety_events and briefing_data.safety_events.success:
            data = briefing_data.safety_events.data or {}
            events = data.get("events", [])

            for event in events:
                event_desc = event.get("description", str(event))
                # If no safety concerns were flagged, any event is unexpected
                if "safety" not in concern_types:
                    unexpected.append(f"Unexpected safety event: {event_desc[:100]}")
                elif event_desc.lower() not in concern_text:
                    unexpected.append(f"Unforecasted safety event: {event_desc[:100]}")

        # Check for unexpected significant downtime
        if briefing_data.downtime_analysis and briefing_data.downtime_analysis.success:
            data = briefing_data.downtime_analysis.data or {}
            top_reasons = data.get("top_reasons", [])

            for reason in top_reasons:
                reason_text = reason.get("reason", "")
                duration = reason.get("duration_minutes", 0)

                # Significant unexpected downtime (> 30 min and not mentioned)
                if duration > 30 and reason_text.lower() not in concern_text:
                    duration_formatted = format_duration_for_voice(duration)
                    unexpected.append(
                        f"Unexpected downtime: {reason_text} ({duration_formatted})"
                    )

        # Check for unexpected production misses
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            assets = data.get("assets", [])

            for asset in assets:
                status = asset.get("status", "")
                asset_name = asset.get("asset_name", asset.get("name", "Unknown"))

                # If significantly behind and not mentioned
                if status == "behind" and asset_name.lower() not in concern_text:
                    variance = asset.get("variance_percent", 0)
                    if variance < -10:  # Significant miss
                        unexpected.append(
                            f"Unexpected production miss: {asset_name} "
                            f"({format_percentage_for_voice(abs(variance))} behind)"
                        )

        return unexpected[:5]  # Limit to top 5 unexpected issues

    def _calculate_accuracy_metrics(
        self,
        comparisons: List[ConcernComparison],
        unexpected_issues: List[str]
    ) -> AccuracyMetrics:
        """
        Calculate prediction accuracy metrics (Story 9.11 AC#3 Task 4.1-4.4).

        Args:
            comparisons: List of concern comparisons
            unexpected_issues: List of unexpected issues

        Returns:
            AccuracyMetrics with calculated values
        """
        total_predictions = len(comparisons)
        misses = len(unexpected_issues)

        # Count outcomes
        materialized = sum(1 for c in comparisons if c.outcome == ConcernOutcome.MATERIALIZED)
        averted = sum(1 for c in comparisons if c.outcome == ConcernOutcome.AVERTED)
        escalated = sum(1 for c in comparisons if c.outcome == ConcernOutcome.ESCALATED)

        # False positives are concerns that were flagged but never occurred
        # (averted outcomes where nothing happened)
        false_positives = averted

        # Correct predictions are ones that materialized or were correctly averted
        # (averted means the prediction helped prevent the issue)
        correct_predictions = materialized + escalated  # These were real issues

        # Calculate accuracy
        # Accuracy = (correct predictions) / (total predictions + misses)
        # This accounts for both false positives and misses
        total_outcomes = total_predictions + misses
        if total_outcomes > 0:
            # True positives (materialized + escalated) vs all outcomes
            accuracy = (correct_predictions / total_outcomes) * 100
        else:
            accuracy = 100.0  # No predictions and no issues = perfect

        # Clamp accuracy to valid range [0, 100]
        accuracy = max(0.0, min(100.0, accuracy))

        return AccuracyMetrics(
            accuracy_percentage=round(accuracy, 1),
            total_predictions=total_predictions,
            correct_predictions=correct_predictions,
            false_positives=false_positives,
            misses=misses,
            averted_count=averted,
            escalated_count=escalated,
        )

    def _generate_comparison_summary(
        self,
        comparisons: List[ConcernComparison],
        metrics: AccuracyMetrics,
        unexpected_issues: List[str]
    ) -> str:
        """
        Generate natural language comparison summary.

        Args:
            comparisons: List of concern comparisons
            metrics: Accuracy metrics
            unexpected_issues: List of unexpected issues

        Returns:
            Natural language summary string
        """
        parts = []

        # Overall accuracy
        accuracy = metrics.accuracy_percentage
        if accuracy >= 80:
            parts.append(
                f"Morning predictions were {format_percentage_for_voice(accuracy)} accurate."
            )
        elif accuracy >= 50:
            parts.append(
                f"Morning predictions were moderately accurate "
                f"({format_percentage_for_voice(accuracy)})."
            )
        else:
            parts.append(
                f"Morning predictions had low accuracy "
                f"({format_percentage_for_voice(accuracy)}). Review forecasting methods."
            )

        # Materialized concerns
        materialized = [c for c in comparisons if c.outcome == ConcernOutcome.MATERIALIZED]
        if materialized:
            parts.append(
                f"{len(materialized)} concern(s) materialized as predicted."
            )

        # Escalated concerns
        escalated = [c for c in comparisons if c.outcome == ConcernOutcome.ESCALATED]
        if escalated:
            parts.append(
                f"{len(escalated)} issue(s) escalated beyond predictions."
            )

        # Averted concerns
        averted = [c for c in comparisons if c.outcome == ConcernOutcome.AVERTED]
        if averted:
            parts.append(
                f"{len(averted)} concern(s) were successfully averted."
            )

        # Unexpected issues
        if unexpected_issues:
            parts.append(
                f"{len(unexpected_issues)} unexpected issue(s) occurred."
            )

        return " ".join(parts) if parts else "Day proceeded as expected."

    async def store_accuracy_metrics(
        self,
        user_id: str,
        summary_date: date,
        comparison_result: EODComparisonResult,
        eod_summary_id: Optional[str] = None,
    ) -> bool:
        """
        Store accuracy metrics for trend tracking (Story 9.11 AC#4 Task 5.1).

        Stores daily accuracy metrics to enable trend analysis and
        Action Engine tuning feedback.

        Args:
            user_id: User ID
            summary_date: Date of the comparison
            comparison_result: The EODComparisonResult with metrics
            eod_summary_id: Optional EOD summary ID

        Returns:
            True if stored successfully, False otherwise

        Note:
            MVP implementation logs metrics only. Production implementation
            should insert into briefing_accuracy_metrics table using the
            migration in supabase/migrations/20260117_002_briefing_accuracy.sql
        """
        try:
            # MVP: Log metrics for observability
            # TODO: Production - Insert into briefing_accuracy_metrics table
            logger.info(
                f"Storing accuracy metrics for user {user_id}, date={summary_date}: "
                f"accuracy={comparison_result.accuracy_metrics.accuracy_percentage}%, "
                f"predictions={comparison_result.accuracy_metrics.total_predictions}, "
                f"false_positives={comparison_result.accuracy_metrics.false_positives}, "
                f"misses={comparison_result.accuracy_metrics.misses}"
            )

            # In production, this would insert into briefing_accuracy_metrics table
            # See Dev Notes for table schema

            return True

        except Exception as e:
            logger.error(f"Failed to store accuracy metrics: {e}")
            return False

    async def get_accuracy_trends(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Query accuracy trends over time (Story 9.11 AC#4 Task 5.2).

        Args:
            user_id: User ID
            days: Number of days to include in trend

        Returns:
            List of daily accuracy records for trend analysis

        Note:
            MVP implementation returns empty list. Production implementation
            should query briefing_accuracy_metrics table ordered by date DESC.
        """
        try:
            # MVP: Return empty list - trends require database storage
            # TODO: Production - Query briefing_accuracy_metrics table
            logger.info(
                f"Querying accuracy trends for user {user_id}, days={days}"
            )

            # Production query would be:
            # SELECT * FROM briefing_accuracy_metrics
            # WHERE user_id = {user_id}
            # ORDER BY date DESC
            # LIMIT {days}

            return []

        except Exception as e:
            logger.error(f"Failed to query accuracy trends: {e}")
            return []

    def get_action_engine_feedback(
        self,
        accuracy_metrics: AccuracyMetrics
    ) -> Dict[str, Any]:
        """
        Generate feedback for Action Engine tuning (Story 9.11 AC#4 Task 5.3).

        Based on accuracy metrics, provides recommendations for
        adjusting prediction weights.

        Args:
            accuracy_metrics: The calculated accuracy metrics

        Returns:
            Feedback dictionary for Action Engine tuning
        """
        feedback: Dict[str, Any] = {
            "accuracy_percentage": accuracy_metrics.accuracy_percentage,
            "recommendations": [],
            "weight_adjustments": {},
        }

        # High false positives suggest over-sensitive predictions
        if accuracy_metrics.false_positives > accuracy_metrics.correct_predictions:
            feedback["recommendations"].append(
                "Consider raising prediction thresholds - too many false positives"
            )
            feedback["weight_adjustments"]["sensitivity"] = -0.1

        # High misses suggest under-sensitive predictions
        if accuracy_metrics.misses > 2:
            feedback["recommendations"].append(
                "Consider lowering prediction thresholds - missing actual issues"
            )
            feedback["weight_adjustments"]["sensitivity"] = 0.1

        # Escalations suggest severity assessment needs calibration
        if accuracy_metrics.escalated_count > 0:
            feedback["recommendations"].append(
                f"{accuracy_metrics.escalated_count} issues escalated beyond predictions - "
                "review severity assessment"
            )
            feedback["weight_adjustments"]["severity_factor"] = 0.05

        # Good accuracy
        if accuracy_metrics.accuracy_percentage >= 80:
            feedback["recommendations"].append(
                "Prediction accuracy is good - maintain current parameters"
            )

        return feedback


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
