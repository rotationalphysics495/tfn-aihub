"""
Briefing Service (Story 8.3)

Main orchestration service for generating briefings.
Composes existing LangChain tools into coherent narratives.

AC#1: Tool Orchestration Sequence
AC#3: 30-Second Timeout Compliance (NFR8)
AC#4: Graceful Tool Failure Handling

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
- [Source: prd/prd-non-functional-requirements.md#NFR8]
"""

import logging
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from app.models.briefing import (
    BriefingResponse,
    BriefingSection,
    BriefingSectionStatus,
    BriefingResponseMetadata,
    BriefingData,
    ToolResultData,
    BriefingCitation,
    BriefingScope,
    BriefingRequest,
)
from app.services.briefing.narrative import get_narrative_generator
from app.services.agent.tools.production_status import ProductionStatusTool
from app.services.agent.tools.safety_events import SafetyEventsTool
from app.services.agent.tools.oee_query import OEEQueryTool
from app.services.agent.tools.downtime_analysis import DowntimeAnalysisTool
from app.services.agent.tools.action_list import ActionListTool

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# Timeout configuration (NFR8: 30-second briefing)
TOTAL_TIMEOUT_SECONDS = 30
PER_TOOL_TIMEOUT_SECONDS = 5
NARRATIVE_TIMEOUT_SECONDS = 8


class BriefingService:
    """
    Briefing synthesis orchestration service.

    Story 8.3 Implementation:
    - AC#1: Orchestrates tools in sequence (Production, Safety, OEE, Downtime, Actions)
    - AC#3: Enforces 30-second total timeout
    - AC#4: Handles individual tool failures gracefully

    This is NOT a ManufacturingTool - it's an orchestration layer.

    Usage:
        service = get_briefing_service()
        briefing = await service.generate_briefing(
            user_id="user123",
            scope=BriefingScope.PLANT_WIDE
        )
    """

    def __init__(self):
        """Initialize the briefing service."""
        self._narrative_generator = None

    def _get_narrative_generator(self):
        """Get narrative generator (lazy init)."""
        if self._narrative_generator is None:
            self._narrative_generator = get_narrative_generator()
        return self._narrative_generator

    async def generate_briefing(
        self,
        user_id: str,
        scope: BriefingScope = BriefingScope.PLANT_WIDE,
        area_id: Optional[str] = None,
        include_audio: bool = True,
    ) -> BriefingResponse:
        """
        Generate a complete briefing.

        AC#1: Orchestrates tools in sequence
        AC#3: 30-second timeout compliance
        AC#4: Graceful tool failure handling

        Args:
            user_id: User requesting the briefing
            scope: Briefing scope (plant-wide or supervisor)
            area_id: Optional area filter for supervisor scope
            include_audio: Whether to include TTS audio URL

        Returns:
            BriefingResponse with sections and optional audio
        """
        start_time = _utcnow()
        briefing_id = str(uuid.uuid4())

        logger.info(f"Generating briefing {briefing_id} for user {user_id}, scope={scope}")

        sections: List[BriefingSection] = []
        tool_failures: List[str] = []
        timed_out = False

        try:
            # AC#3: Overall 30-second timeout
            async with asyncio.timeout(TOTAL_TIMEOUT_SECONDS):
                # AC#1: Orchestrate tools
                briefing_data = await self._orchestrate_tools(area_id)

                # Track failed tools
                tool_failures = briefing_data.failed_tools

                # Generate narrative sections
                sections = await self._generate_narrative_sections(briefing_data)

        except asyncio.TimeoutError:
            logger.warning(f"Briefing {briefing_id} timed out after {TOTAL_TIMEOUT_SECONDS}s")
            timed_out = True
            # Mark any incomplete sections as timed out
            for section in sections:
                if section.status == BriefingSectionStatus.PENDING:
                    section.status = BriefingSectionStatus.TIMED_OUT
                    section.error_message = "Generation timed out"

        except Exception as e:
            logger.error(f"Briefing generation failed: {e}", exc_info=True)
            # Return minimal error response
            return self._create_error_response(briefing_id, user_id, str(e))

        # Calculate completion
        completed_count = len([s for s in sections if s.is_complete])
        total_count = len(sections) if sections else 1
        completion_pct = (completed_count / total_count) * 100 if total_count > 0 else 0

        # Calculate duration
        end_time = _utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Estimate audio duration (rough estimate: 150 words/min, ~5 chars/word)
        total_chars = sum(len(s.content) for s in sections)
        duration_estimate_seconds = int(total_chars / 12.5)  # ~750 chars/min

        # Build response
        return BriefingResponse(
            id=briefing_id,
            title=self._get_briefing_title(scope, area_id),
            scope=scope.value,
            user_id=user_id,
            sections=sections,
            audio_stream_url=None,  # TTS integration is separate (Story 8.1)
            total_duration_estimate=duration_estimate_seconds,
            metadata=BriefingResponseMetadata(
                generated_at=start_time,
                generation_duration_ms=duration_ms,
                completion_percentage=completion_pct,
                timed_out=timed_out,
                tool_failures=tool_failures,
                cache_hit=False,
            ),
        )

    async def _orchestrate_tools(
        self,
        area_id: Optional[str] = None,
    ) -> BriefingData:
        """
        Orchestrate tool execution for briefing data.

        AC#1: Tool Orchestration Sequence
        Runs tools with individual timeouts and aggregates results.

        Args:
            area_id: Optional area filter

        Returns:
            BriefingData with results from all tools
        """
        briefing_data = BriefingData()

        # Define tools to run (in parallel for performance)
        tool_tasks = [
            self._run_tool_with_timeout("production_status", self._get_production_status, area_id),
            self._run_tool_with_timeout("safety_events", self._get_safety_events, area_id),
            self._run_tool_with_timeout("oee_data", self._get_oee_data, area_id),
            self._run_tool_with_timeout("downtime_analysis", self._get_downtime_analysis, area_id),
            self._run_tool_with_timeout("action_list", self._get_action_list),
        ]

        # Run all tools in parallel
        results = await asyncio.gather(*tool_tasks, return_exceptions=True)

        # Map results to briefing data
        tool_names = ["production_status", "safety_events", "oee_data", "downtime_analysis", "action_list"]

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
        start_time = _utcnow()

        try:
            async with asyncio.timeout(PER_TOOL_TIMEOUT_SECONDS):
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

    async def _get_production_status(self, area_id: Optional[str] = None) -> ToolResultData:
        """Get production status from tool."""
        tool = ProductionStatusTool()
        result = await tool._arun(area=area_id)

        citations = [
            BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
            for c in result.citations
        ]

        return ToolResultData(
            tool_name="production_status",
            success=result.success,
            data=result.data if result.success else None,
            citations=citations,
            error_message=result.error_message,
        )

    async def _get_safety_events(self, area_id: Optional[str] = None) -> ToolResultData:
        """Get safety events from tool."""
        tool = SafetyEventsTool()
        result = await tool._arun(area=area_id, days=1)

        citations = [
            BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
            for c in result.citations
        ]

        return ToolResultData(
            tool_name="safety_events",
            success=result.success,
            data=result.data if result.success else None,
            citations=citations,
            error_message=result.error_message,
        )

    async def _get_oee_data(self, area_id: Optional[str] = None) -> ToolResultData:
        """Get OEE data from tool."""
        tool = OEEQueryTool()
        result = await tool._arun(scope="plant", days=1)

        citations = [
            BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
            for c in result.citations
        ]

        return ToolResultData(
            tool_name="oee_data",
            success=result.success,
            data=result.data if result.success else None,
            citations=citations,
            error_message=result.error_message,
        )

    async def _get_downtime_analysis(self, area_id: Optional[str] = None) -> ToolResultData:
        """Get downtime analysis from tool."""
        tool = DowntimeAnalysisTool()
        result = await tool._arun(area=area_id, days=1)

        citations = [
            BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
            for c in result.citations
        ]

        return ToolResultData(
            tool_name="downtime_analysis",
            success=result.success,
            data=result.data if result.success else None,
            citations=citations,
            error_message=result.error_message,
        )

    async def _get_action_list(self) -> ToolResultData:
        """Get action list from tool."""
        tool = ActionListTool()
        result = await tool._arun()

        citations = [
            BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
            for c in result.citations
        ]

        return ToolResultData(
            tool_name="action_list",
            success=result.success,
            data=result.data if result.success else None,
            citations=citations,
            error_message=result.error_message,
        )

    async def _generate_narrative_sections(
        self,
        briefing_data: BriefingData,
    ) -> List[BriefingSection]:
        """
        Generate narrative sections from tool data.

        AC#2: Narrative Generation
        Uses LLM to format data into natural language sections.
        """
        generator = self._get_narrative_generator()

        try:
            async with asyncio.timeout(NARRATIVE_TIMEOUT_SECONDS):
                sections = await generator.generate_sections(briefing_data)
                return sections

        except asyncio.TimeoutError:
            logger.warning("Narrative generation timed out, using fallback")
            return self._create_fallback_sections(briefing_data)

        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            return self._create_fallback_sections(briefing_data)

    def _create_fallback_sections(
        self,
        briefing_data: BriefingData,
    ) -> List[BriefingSection]:
        """
        Create fallback sections without LLM narrative.

        AC#4: Falls back to structured data when LLM fails.
        """
        sections = []

        # Headline
        sections.append(BriefingSection(
            section_type="headline",
            title="Morning Briefing",
            content="Here's your morning briefing summary. Some sections may have limited detail.",
            status=BriefingSectionStatus.PARTIAL,
        ))

        # Production status
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})
            content = (
                f"Production: {summary.get('total_output', 'N/A')} units produced "
                f"against {summary.get('total_target', 'N/A')} target. "
                f"{summary.get('behind_count', 0)} assets behind."
            )
            sections.append(BriefingSection(
                section_type="production",
                title="Production Status",
                content=content,
                citations=briefing_data.production_status.citations,
                status=BriefingSectionStatus.COMPLETE,
            ))
        elif briefing_data.production_status:
            sections.append(BriefingSection(
                section_type="production",
                title="Production Status",
                content=f"Unable to retrieve production data: {briefing_data.production_status.error_message}",
                status=BriefingSectionStatus.FAILED,
                error_message=briefing_data.production_status.error_message,
            ))

        # Safety
        if briefing_data.safety_events and briefing_data.safety_events.success:
            data = briefing_data.safety_events.data or {}
            total = data.get("total_events", 0)
            if total == 0:
                content = "No safety incidents reported in the last 24 hours."
            else:
                content = f"{total} safety event(s) recorded. Please review for details."
            sections.append(BriefingSection(
                section_type="safety",
                title="Safety Update",
                content=content,
                citations=briefing_data.safety_events.citations,
                status=BriefingSectionStatus.COMPLETE,
            ))

        # OEE
        if briefing_data.oee_data and briefing_data.oee_data.success:
            data = briefing_data.oee_data.data or {}
            oee = data.get("oee_percentage", data.get("oee", "N/A"))
            content = f"Plant OEE: {oee}%."
            sections.append(BriefingSection(
                section_type="oee",
                title="OEE Overview",
                content=content,
                citations=briefing_data.oee_data.citations,
                status=BriefingSectionStatus.COMPLETE,
            ))

        # Actions
        if briefing_data.action_list and briefing_data.action_list.success:
            data = briefing_data.action_list.data or {}
            actions = data.get("actions", [])
            if actions:
                action_items = "; ".join([a.get("title", "Action") for a in actions[:3]])
                content = f"Top priorities: {action_items}."
            else:
                content = "No critical actions identified."
            sections.append(BriefingSection(
                section_type="actions",
                title="Recommended Actions",
                content=content,
                citations=briefing_data.action_list.citations,
                status=BriefingSectionStatus.COMPLETE,
            ))

        return sections

    def _create_error_response(
        self,
        briefing_id: str,
        user_id: str,
        error_message: str,
    ) -> BriefingResponse:
        """Create error response when generation fails completely."""
        return BriefingResponse(
            id=briefing_id,
            title="Briefing Unavailable",
            scope="error",
            user_id=user_id,
            sections=[
                BriefingSection(
                    section_type="error",
                    title="Unable to Generate Briefing",
                    content=(
                        "We encountered an error generating your briefing. "
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
        )

    def _get_briefing_title(
        self,
        scope: BriefingScope,
        area_id: Optional[str] = None,
    ) -> str:
        """Get briefing title based on scope."""
        now = _utcnow()
        date_str = now.strftime("%A, %B %d")

        if scope == BriefingScope.SUPERVISOR and area_id:
            return f"{area_id} Briefing - {date_str}"
        elif scope == BriefingScope.AREA and area_id:
            return f"{area_id} Area Briefing - {date_str}"
        else:
            return f"Morning Briefing - {date_str}"


# Module-level singleton
_briefing_service: Optional[BriefingService] = None


def get_briefing_service() -> BriefingService:
    """
    Get the singleton BriefingService instance.

    Returns:
        BriefingService singleton instance
    """
    global _briefing_service
    if _briefing_service is None:
        _briefing_service = BriefingService()
    return _briefing_service
