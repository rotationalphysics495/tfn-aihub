"""
Agent Pydantic Models (Story 5.1, 5.3)

Request and response models for the Agent API endpoints and tools.

AC#5: Structured Response with Citations
AC#7: Agent Chat Endpoint
Story 5.3: Asset Lookup Tool Input/Output Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Story 5.3: Asset Lookup Tool Models
# =============================================================================


class AssetStatus(str, Enum):
    """Status enum for asset operational state."""
    RUNNING = "running"
    DOWN = "down"
    IDLE = "idle"
    UNKNOWN = "unknown"


class OEETrend(str, Enum):
    """Trend indicator for OEE performance."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class AssetLookupInput(BaseModel):
    """
    Input schema for Asset Lookup tool.

    Story 5.3 AC#1: Asset Lookup by Name
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_name": "Grinder 5",
                "include_performance": True,
                "days_back": 7
            }
        }
    )

    asset_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the asset to look up (e.g., 'Grinder 5', 'CAMA 800-1')"
    )
    include_performance: bool = Field(
        default=True,
        description="Include 7-day performance summary (OEE, downtime)"
    )
    days_back: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Number of days to analyze for performance metrics"
    )


class AssetMetadata(BaseModel):
    """
    Asset metadata from Plant Object Model.

    Story 5.3 AC#1: Returns asset metadata (name, area, cost center)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Grinder 5",
                "source_id": "GRD005",
                "area": "Grinding",
                "cost_center": "GR-001"
            }
        }
    )

    id: str = Field(..., description="Asset UUID")
    name: str = Field(..., description="Human-readable asset name")
    source_id: Optional[str] = Field(None, description="Source system ID (e.g., MSSQL locationName)")
    area: Optional[str] = Field(None, description="Plant area location")
    cost_center: Optional[str] = Field(None, description="Cost center identifier")


class AssetCurrentStatus(BaseModel):
    """
    Current live status of an asset.

    Story 5.3 AC#4: Live status display with freshness tracking
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "running",
                "output_current": 847,
                "output_target": 900,
                "variance": -53,
                "variance_percent": -5.9,
                "last_updated": "2026-01-09T14:45:00Z",
                "data_stale": False,
                "stale_warning": None
            }
        }
    )

    status: AssetStatus = Field(..., description="Current operational status")
    output_current: Optional[int] = Field(None, description="Current production count")
    output_target: Optional[int] = Field(None, description="Target production count for shift")
    variance: Optional[int] = Field(None, description="Units variance from target (can be negative)")
    variance_percent: Optional[float] = Field(None, description="Percentage variance from target")
    last_updated: Optional[str] = Field(None, description="Timestamp of last live data (ISO format)")
    data_stale: bool = Field(default=False, description="True if data is older than 30 minutes")
    stale_warning: Optional[str] = Field(None, description="Warning message if data is stale")


class AssetPerformance(BaseModel):
    """
    Performance summary for an asset over a time period.

    Story 5.3 AC#5: Performance summary with OEE, trend, and downtime
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "avg_oee": 78.3,
                "oee_trend": "stable",
                "total_downtime_minutes": 252,
                "top_downtime_reason": "Material Jam",
                "top_downtime_percent": 38.1,
                "days_analyzed": 7,
                "no_data": False,
                "message": None
            }
        }
    )

    avg_oee: Optional[float] = Field(None, ge=0.0, le=100.0, description="Average OEE percentage")
    oee_trend: OEETrend = Field(
        default=OEETrend.INSUFFICIENT_DATA,
        description="OEE trend: improving, stable, declining, or insufficient_data"
    )
    total_downtime_minutes: int = Field(default=0, description="Total downtime in minutes")
    top_downtime_reason: Optional[str] = Field(None, description="Most common downtime reason")
    top_downtime_percent: Optional[float] = Field(None, description="Percentage of downtime from top reason")
    days_analyzed: int = Field(default=7, description="Number of days analyzed")
    no_data: bool = Field(default=False, description="True if no performance data available")
    message: Optional[str] = Field(None, description="Message about data availability")


class AssetLookupOutput(BaseModel):
    """
    Output schema for Asset Lookup tool.

    Story 5.3 AC#1, AC#2, AC#3: Complete asset lookup response
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "found": True,
                "metadata": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Grinder 5",
                    "area": "Grinding",
                    "cost_center": "GR-001"
                },
                "current_status": {
                    "status": "running",
                    "output_current": 847,
                    "output_target": 900,
                    "variance": -53,
                    "variance_percent": -5.9
                },
                "performance": {
                    "avg_oee": 78.3,
                    "oee_trend": "stable",
                    "total_downtime_minutes": 252,
                    "top_downtime_reason": "Material Jam"
                },
                "suggestions": None,
                "message": None
            }
        }
    )

    found: bool = Field(default=True, description="Whether the asset was found")
    metadata: Optional[AssetMetadata] = Field(None, description="Asset metadata from POM")
    current_status: Optional[AssetCurrentStatus] = Field(None, description="Current live status")
    performance: Optional[AssetPerformance] = Field(None, description="Performance summary")
    suggestions: Optional[List[str]] = Field(
        None,
        max_length=5,
        description="Similar asset names when requested asset not found (max 5)"
    )
    message: Optional[str] = Field(None, description="Additional message (e.g., 'Asset not found')")


class FollowUpQuestion(BaseModel):
    """Suggested follow-up question for the user."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What was the downtime breakdown?",
                "category": "analysis"
            }
        }
    )

    question: str = Field(
        ...,
        description="The suggested follow-up question text"
    )
    category: Optional[str] = Field(
        None,
        description="Category of the question (analysis, comparison, drill-down)"
    )


class AgentCitation(BaseModel):
    """
    Citation from agent tool execution.

    Follows the citation format from Story 4.5 for consistency.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "daily_summaries",
                "query": "SELECT * FROM daily_summaries WHERE asset_id = 'grinder-5'",
                "timestamp": "2026-01-09T10:30:00Z",
                "table": "daily_summaries",
                "record_id": "550e8400-e29b-41d4-a716-446655440000",
                "confidence": 0.95,
                "display_text": "[Source: daily_summaries/2026-01-08]"
            }
        }
    )

    source: str = Field(
        ...,
        description="Data source identifier"
    )
    query: str = Field(
        ...,
        description="Query or operation that retrieved the data"
    )
    timestamp: str = Field(
        ...,
        description="When the data was retrieved (ISO format)"
    )
    table: Optional[str] = Field(
        None,
        description="Database table name if applicable"
    )
    record_id: Optional[str] = Field(
        None,
        description="Specific record identifier"
    )
    asset_id: Optional[str] = Field(
        None,
        description="Asset identifier from Plant Object Model"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this citation"
    )
    display_text: str = Field(
        ...,
        description="Human-readable citation text for display"
    )


class QueryContext(BaseModel):
    """Optional context for enhancing agent queries."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_focus": "Grinder 5",
                "time_range": "yesterday",
                "previous_queries": ["What is OEE?"]
            }
        }
    )

    asset_focus: Optional[str] = Field(
        None,
        description="Specific asset to focus on"
    )
    time_range: Optional[str] = Field(
        None,
        description="Time range context (today, yesterday, last week)"
    )
    previous_queries: Optional[List[str]] = Field(
        None,
        description="Previous queries in this conversation"
    )


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "What was Grinder 5's OEE yesterday?"
            }
        }
    )

    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        ...,
        description="Message content"
    )


class AgentChatRequest(BaseModel):
    """
    Request body for POST /api/agent/chat endpoint.

    AC#7: Agent Chat Endpoint
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "What was Grinder 5's OEE yesterday?",
                "context": {
                    "asset_focus": "Grinder 5",
                    "time_range": "yesterday"
                },
                "chat_history": [
                    {"role": "user", "content": "Show me Grinder 5 status"},
                    {"role": "assistant", "content": "Grinder 5 is currently running..."}
                ]
            }
        }
    )

    message: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="User's natural language message"
    )
    context: Optional[QueryContext] = Field(
        None,
        description="Optional context for enhancing the query"
    )
    chat_history: Optional[List[ChatMessage]] = Field(
        None,
        description="Previous messages in the conversation"
    )
    force_refresh: bool = Field(
        default=False,
        description="Bypass cache and fetch fresh data (Story 5.8 AC#5)"
    )


class AgentResponse(BaseModel):
    """
    Response from POST /api/agent/chat endpoint.

    AC#5: Structured Response with Citations
    AC#7: Agent Chat Endpoint - response follows AgentResponse schema
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Based on yesterday's data, Grinder 5 had an OEE of 87.5%. [Source: daily_summaries/2026-01-08]",
                "tool_used": "asset_status",
                "citations": [
                    {
                        "source": "daily_summaries",
                        "query": "SELECT * FROM daily_summaries",
                        "timestamp": "2026-01-09T10:30:00Z",
                        "table": "daily_summaries",
                        "confidence": 0.95,
                        "display_text": "[Source: daily_summaries/2026-01-08]"
                    }
                ],
                "suggested_questions": [
                    "What caused the downtime?",
                    "How does this compare to last week?"
                ],
                "execution_time_ms": 1250.5,
                "meta": {
                    "model": "gpt-4-turbo-preview",
                    "timestamp": "2026-01-09T10:30:00Z"
                }
            }
        }
    )

    content: str = Field(
        ...,
        description="Natural language response from the agent"
    )
    tool_used: Optional[str] = Field(
        None,
        description="Name of the tool that was invoked, if any"
    )
    citations: List[AgentCitation] = Field(
        default_factory=list,
        description="Data source citations for NFR1 compliance"
    )
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Time taken to process the message in milliseconds"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )


class AgentServiceStatus(BaseModel):
    """Status information for the agent service."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "configured": True,
                "initialized": True,
                "status": "ready",
                "available_tools": ["asset_status", "production_query"],
                "model": "gpt-4-turbo-preview"
            }
        }
    )

    configured: bool = Field(
        ...,
        description="Whether the agent is properly configured"
    )
    initialized: bool = Field(
        ...,
        description="Whether the agent has been initialized"
    )
    status: str = Field(
        ...,
        description="Current status: ready, not_initialized, not_configured"
    )
    available_tools: List[str] = Field(
        default_factory=list,
        description="List of available tool names"
    )
    model: Optional[str] = Field(
        None,
        description="LLM model being used"
    )


# =============================================================================
# Story 6.1: Safety Events Tool Models
# =============================================================================


class SafetySeverity(str, Enum):
    """Severity levels for safety events (ordered by priority)."""
    CRITICAL = "critical"  # Immediate danger, requires immediate action
    HIGH = "high"          # Serious safety concern
    MEDIUM = "medium"      # Moderate safety issue
    LOW = "low"            # Minor safety concern


class ResolutionStatus(str, Enum):
    """Resolution status for safety events."""
    OPEN = "open"                        # Not yet addressed
    UNDER_INVESTIGATION = "under_investigation"  # Being investigated
    RESOLVED = "resolved"                # Issue resolved


class SafetyEventsInput(BaseModel):
    """
    Input schema for Safety Events tool.

    Story 6.1 AC#1-3: Query safety incidents with optional filters.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time_range": "today",
                "area": "Packaging",
                "severity_filter": "critical",
                "asset_id": None
            }
        }
    )

    time_range: str = Field(
        default="today",
        description=(
            "Time range to query: 'today', 'yesterday', 'this week', "
            "'last 7 days', 'last N days', or date range like '2026-01-01 to 2026-01-09'"
        )
    )
    area: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Area name to filter by (e.g., 'Grinding', 'Packaging')"
    )
    severity_filter: Optional[str] = Field(
        default=None,
        description="Severity level filter: 'critical', 'high', 'medium', 'low'"
    )
    asset_id: Optional[str] = Field(
        default=None,
        description="Specific asset UUID to filter by"
    )


class SafetyEventDetail(BaseModel):
    """
    Single safety event with full details.

    Story 6.1 AC#1: For each event: timestamp, asset, severity, description
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "evt-001",
                "timestamp": "2026-01-09T06:42:00Z",
                "asset_id": "ast-pkg-002",
                "asset_name": "Packaging Line 2",
                "area": "Packaging",
                "severity": "critical",
                "description": "Safety stop triggered - emergency shutoff activated",
                "resolution_status": "under_investigation",
                "reported_by": "Sensor Alert"
            }
        }
    )

    event_id: str = Field(..., description="Event UUID")
    timestamp: str = Field(..., description="When the event occurred (ISO format)")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Human-readable asset name")
    area: Optional[str] = Field(None, description="Plant area")
    severity: str = Field(..., description="Severity level: critical/high/medium/low")
    description: Optional[str] = Field(None, description="Event description")
    resolution_status: str = Field(
        default="open",
        description="Status: open/under_investigation/resolved"
    )
    reported_by: Optional[str] = Field(None, description="Who reported the event")


class SafetySummaryStats(BaseModel):
    """
    Summary statistics for safety events.

    Story 6.1 AC#2: Summary statistics (total events, resolved vs open)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_events": 5,
                "by_severity": {"critical": 1, "high": 2, "medium": 1, "low": 1},
                "by_status": {"open": 2, "under_investigation": 1, "resolved": 2},
                "resolved_count": 2,
                "open_count": 3
            }
        }
    )

    total_events: int = Field(..., ge=0, description="Total number of events")
    by_severity: Dict[str, int] = Field(
        ..., description="Count by severity level"
    )
    by_status: Dict[str, int] = Field(
        ..., description="Count by resolution status"
    )
    resolved_count: int = Field(default=0, ge=0, description="Number of resolved events")
    open_count: int = Field(default=0, ge=0, description="Number of open events (including under investigation)")


class SafetyEventsOutput(BaseModel):
    """
    Output schema for Safety Events tool.

    Story 6.1 AC#1, AC#4, AC#5: Complete safety events response.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scope": "Packaging",
                "time_range": "today",
                "events": [],
                "total_count": 1,
                "summary": {
                    "total_events": 1,
                    "by_severity": {"critical": 1, "high": 0, "medium": 0, "low": 0},
                    "by_status": {"open": 0, "under_investigation": 1, "resolved": 0},
                    "resolved_count": 0,
                    "open_count": 1
                },
                "message": None,
                "no_incidents": False,
                "data_freshness": "2026-01-09T09:00:00Z"
            }
        }
    )

    scope: str = Field(..., description="Scope of query: 'all', area name, or asset name")
    time_range: str = Field(..., description="Time range queried")
    events: List[SafetyEventDetail] = Field(
        default_factory=list,
        description="List of safety events (sorted by severity, then recency)"
    )
    total_count: int = Field(default=0, ge=0, description="Total number of events")
    summary: SafetySummaryStats = Field(..., description="Summary statistics")
    message: Optional[str] = Field(
        None,
        description="Additional message (e.g., 'No safety incidents recorded')"
    )
    no_incidents: bool = Field(
        default=False,
        description="True if no incidents found (positive news)"
    )
    data_freshness: str = Field(
        ...,
        description="Data freshness timestamp (ISO format)"
    )
