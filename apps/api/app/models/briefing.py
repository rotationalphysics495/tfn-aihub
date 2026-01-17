"""
Briefing Models (Story 8.3)

Pydantic schemas for briefing generation and delivery.
Used by BriefingService to structure synthesized content.

AC#1: Tool Orchestration Sequence - BriefingData structure
AC#2: Narrative Generation - BriefingSection, BriefingResponse
AC#3: 30-Second Timeout Compliance - BriefingSectionStatus
AC#4: Graceful Tool Failure Handling - Section status tracking

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class BriefingSectionStatus(str, Enum):
    """
    Status of a briefing section (AC#3, AC#4).

    Used to track completion and failures during generation.
    """
    PENDING = "pending"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class EODSection(str, Enum):
    """
    Section types for End of Day summary (Story 9.10).

    AC#2: Summary Content Structure
    """
    PERFORMANCE = "performance"  # Day's overall vs target
    COMPARISON = "comparison"    # Morning vs actual (if morning briefing exists)
    WINS = "wins"                # Areas that exceeded targets
    CONCERNS = "concerns"        # Issues that escalated or resolved
    OUTLOOK = "outlook"          # Tomorrow's predicted focus areas


class BriefingMetric(BaseModel):
    """
    A single metric in a briefing section (Task 2.4).

    Represents quantitative data with formatting for display and voice.

    Attributes:
        name: Metric name (e.g., "OEE", "Production Output")
        value: Raw numeric value
        formatted_value: Display formatted value (e.g., "87.5%")
        voice_value: Voice-optimized value (e.g., "eighty-seven point five percent")
        unit: Optional unit of measurement
        trend: Optional trend indicator (up, down, flat)
        comparison: Optional comparison text (e.g., "vs 85% target")
    """
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Raw numeric value")
    formatted_value: str = Field(..., description="Display formatted value")
    voice_value: Optional[str] = Field(None, description="Voice-optimized value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    trend: Optional[str] = Field(None, description="Trend indicator: up/down/flat")
    comparison: Optional[str] = Field(None, description="Comparison text")


class BriefingCitation(BaseModel):
    """
    Citation for a briefing data source.

    Simplified citation for briefing context.
    """
    source: str = Field(..., description="Data source name")
    table: Optional[str] = Field(None, description="Database table")
    timestamp: datetime = Field(default_factory=_utcnow, description="When retrieved")


class BriefingSection(BaseModel):
    """
    A section of a briefing (Task 2.2).

    Represents a logical segment of the briefing with content and metadata.

    Attributes:
        section_type: Type identifier (headline, wins, concerns, actions, area)
        title: Section title for display
        content: Natural language narrative content
        metrics: List of metrics in this section
        citations: Data source citations
        status: Completion status
        pause_point: Whether to pause after this section for Q&A
        area_id: Optional area identifier for area-specific sections
    """
    section_type: str = Field(..., description="Section type: headline/wins/concerns/actions/area")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Natural language narrative content")
    metrics: List[BriefingMetric] = Field(default_factory=list, description="Metrics in section")
    citations: List[BriefingCitation] = Field(default_factory=list, description="Data citations")
    status: BriefingSectionStatus = Field(
        default=BriefingSectionStatus.PENDING,
        description="Section completion status"
    )
    pause_point: bool = Field(True, description="Pause after this section for Q&A")
    area_id: Optional[str] = Field(None, description="Area ID for area-specific sections")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    @property
    def is_complete(self) -> bool:
        """Check if section is complete."""
        return self.status == BriefingSectionStatus.COMPLETE

    @property
    def has_error(self) -> bool:
        """Check if section has error."""
        return self.status in (BriefingSectionStatus.FAILED, BriefingSectionStatus.TIMED_OUT)


class BriefingResponseMetadata(BaseModel):
    """
    Metadata for briefing response.

    Tracks generation performance and completion status.
    """
    generated_at: datetime = Field(default_factory=_utcnow, description="When generated")
    generation_duration_ms: Optional[int] = Field(None, description="Generation time in ms")
    completion_percentage: float = Field(100.0, description="Percentage of sections completed")
    timed_out: bool = Field(False, description="Whether generation timed out")
    tool_failures: List[str] = Field(default_factory=list, description="Names of failed tools")
    cache_hit: bool = Field(False, description="Whether served from cache")


class BriefingResponse(BaseModel):
    """
    Complete briefing response (Task 2.3).

    Contains all sections, optional audio URL, and metadata.

    Attributes:
        id: Unique briefing identifier
        title: Briefing title
        scope: Briefing scope (plant-wide or supervisor)
        sections: List of briefing sections
        audio_stream_url: Optional TTS audio URL (from Story 8.1)
        total_duration_estimate: Estimated total duration in seconds
        metadata: Generation metadata
    """
    id: str = Field(..., description="Unique briefing ID")
    title: str = Field(..., description="Briefing title")
    scope: str = Field("plant_wide", description="Briefing scope: plant_wide/supervisor")
    user_id: Optional[str] = Field(None, description="User ID if personalized")
    sections: List[BriefingSection] = Field(default_factory=list, description="Briefing sections")
    audio_stream_url: Optional[str] = Field(None, description="TTS audio URL (nullable)")
    total_duration_estimate: int = Field(0, description="Estimated duration in seconds")
    metadata: BriefingResponseMetadata = Field(
        default_factory=BriefingResponseMetadata,
        description="Generation metadata"
    )

    @property
    def section_count(self) -> int:
        """Get number of sections."""
        return len(self.sections)

    @property
    def completed_section_count(self) -> int:
        """Get number of completed sections."""
        return len([s for s in self.sections if s.is_complete])

    @property
    def has_audio(self) -> bool:
        """Check if audio is available."""
        return self.audio_stream_url is not None

    def get_sections_by_type(self, section_type: str) -> List[BriefingSection]:
        """Get sections of a specific type."""
        return [s for s in self.sections if s.section_type == section_type]


class BriefingScope(str, Enum):
    """
    Scope of briefing generation.

    Determines which data to include in the briefing.
    """
    PLANT_WIDE = "plant_wide"
    SUPERVISOR = "supervisor"
    AREA = "area"


class BriefingRequest(BaseModel):
    """
    Request for briefing generation.

    Used to initiate briefing generation with optional scoping.
    """
    user_id: str = Field(..., description="User requesting briefing")
    scope: BriefingScope = Field(BriefingScope.PLANT_WIDE, description="Briefing scope")
    area_id: Optional[str] = Field(None, description="Area ID for area-scoped briefing")
    include_audio: bool = Field(True, description="Generate TTS audio")
    detail_level: str = Field("standard", description="Detail level: brief/standard/detailed")


class ToolResultData(BaseModel):
    """
    Aggregated data from a single tool execution.

    Used internally to track tool outputs during orchestration.
    """
    tool_name: str = Field(..., description="Name of the tool")
    success: bool = Field(True, description="Whether tool execution succeeded")
    data: Optional[Dict[str, Any]] = Field(None, description="Tool output data")
    citations: List[BriefingCitation] = Field(default_factory=list, description="Citations")
    error_message: Optional[str] = Field(None, description="Error if failed")
    execution_time_ms: Optional[int] = Field(None, description="Execution time")


class BriefingData(BaseModel):
    """
    Aggregated data from all tool executions (AC#1).

    Internal structure used during briefing synthesis.
    """
    production_status: Optional[ToolResultData] = None
    safety_events: Optional[ToolResultData] = None
    oee_data: Optional[ToolResultData] = None
    downtime_analysis: Optional[ToolResultData] = None
    action_list: Optional[ToolResultData] = None

    @property
    def all_citations(self) -> List[BriefingCitation]:
        """Get all citations from all tools."""
        citations = []
        for field in [self.production_status, self.safety_events, self.oee_data,
                      self.downtime_analysis, self.action_list]:
            if field and field.citations:
                citations.extend(field.citations)
        return citations

    @property
    def successful_tools(self) -> List[str]:
        """Get names of tools that succeeded."""
        tools = []
        for name, field in [
            ("production_status", self.production_status),
            ("safety_events", self.safety_events),
            ("oee_data", self.oee_data),
            ("downtime_analysis", self.downtime_analysis),
            ("action_list", self.action_list),
        ]:
            if field and field.success:
                tools.append(name)
        return tools

    @property
    def failed_tools(self) -> List[str]:
        """Get names of tools that failed."""
        tools = []
        for name, field in [
            ("production_status", self.production_status),
            ("safety_events", self.safety_events),
            ("oee_data", self.oee_data),
            ("downtime_analysis", self.downtime_analysis),
            ("action_list", self.action_list),
        ]:
            if field and not field.success:
                tools.append(name)
        return tools


# =============================================================================
# End of Day Summary Models (Story 9.10)
# =============================================================================


class MorningComparisonResult(BaseModel):
    """
    Result of comparing morning briefing predictions to actual outcomes (Story 9.10).

    AC#2: Summary Content Structure - comparison to morning briefing highlights
    """
    morning_briefing_id: str = Field(..., description="ID of the morning briefing")
    morning_generated_at: datetime = Field(..., description="When morning briefing was generated")
    flagged_concerns: List[str] = Field(
        default_factory=list,
        description="Concerns flagged in morning briefing"
    )
    concerns_resolved: List[str] = Field(
        default_factory=list,
        description="Concerns that were resolved during the day"
    )
    concerns_escalated: List[str] = Field(
        default_factory=list,
        description="Concerns that escalated during the day"
    )
    predicted_wins: List[str] = Field(
        default_factory=list,
        description="Wins predicted in morning briefing"
    )
    actual_wins: List[str] = Field(
        default_factory=list,
        description="Wins that actually materialized"
    )
    prediction_summary: str = Field(
        "",
        description="Natural language summary of morning vs actual comparison"
    )


class EODSummaryResponse(BriefingResponse):
    """
    Extended response for End of Day summary (Story 9.10).

    AC#1: EOD Summary Trigger (FR31)
    AC#2: Summary Content Structure
    AC#3: No Morning Briefing Fallback

    Extends BriefingResponse with EOD-specific fields.
    """
    morning_briefing_id: Optional[str] = Field(
        None,
        description="ID of today's morning briefing (if exists)"
    )
    comparison_available: bool = Field(
        False,
        description="Whether morning briefing comparison is available"
    )
    morning_comparison: Optional[MorningComparisonResult] = Field(
        None,
        description="Detailed comparison to morning briefing (if available)"
    )
    prediction_accuracy: Optional[float] = Field(
        None,
        description="Prediction accuracy percentage (for Story 9.11)"
    )
    summary_date: datetime = Field(
        default_factory=_utcnow,
        description="Date this EOD summary covers"
    )
    time_range_start: Optional[datetime] = Field(
        None,
        description="Start of the day's time range (typically 06:00 AM)"
    )
    time_range_end: Optional[datetime] = Field(
        None,
        description="End of the day's time range (current time or shift end)"
    )


class EODRequest(BaseModel):
    """
    Request for End of Day summary generation (Story 9.10).

    AC#1: EOD Summary Trigger
    """
    date: Optional[str] = Field(
        None,
        description="Date for EOD summary (ISO format). Defaults to today."
    )
    include_audio: bool = Field(True, description="Generate TTS audio")
