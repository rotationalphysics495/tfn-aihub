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


# =============================================================================
# Story 6.2: Financial Impact Tool Models
# =============================================================================


class FinancialImpactInput(BaseModel):
    """
    Input schema for Financial Impact tool.

    Story 6.2 AC#1-2: Query financial impact for assets or areas.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time_range": "yesterday",
                "asset_id": None,
                "area": "Grinding",
                "include_breakdown": True
            }
        }
    )

    time_range: str = Field(
        default="yesterday",
        description=(
            "Time range to query: 'today', 'yesterday', 'this week', "
            "'last 7 days', 'last N days', or date range like '2026-01-01 to 2026-01-09'"
        )
    )
    asset_id: Optional[str] = Field(
        default=None,
        description="Specific asset UUID to calculate financial impact for"
    )
    area: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Area name to aggregate financial impact for (e.g., 'Grinding', 'Packaging')"
    )
    include_breakdown: bool = Field(
        default=True,
        description="Include detailed breakdown by cost category"
    )


class CostBreakdown(BaseModel):
    """
    Breakdown of a cost category with calculation details.

    Story 6.2 AC#4: Transparent calculations with formulas.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "downtime",
                "amount": 1875.00,
                "calculation_basis": {
                    "downtime_minutes": 47,
                    "standard_hourly_rate": 2393.62
                },
                "formula_used": "47 min * $2393.62/hr / 60 = $1875.00"
            }
        }
    )

    category: str = Field(..., description="Cost category: 'downtime' or 'waste'")
    amount: float = Field(..., ge=0.0, description="Cost amount in dollars")
    calculation_basis: Dict[str, Any] = Field(
        ..., description="Values used in calculation"
    )
    formula_used: str = Field(..., description="Human-readable formula showing calculation")


class AssetFinancialSummary(BaseModel):
    """
    Financial summary for a single asset.

    Story 6.2 AC#1, AC#2: Per-asset financial breakdown.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "ast-grd-005",
                "asset_name": "Grinder 5",
                "total_loss": 2340.50,
                "downtime_cost": 1875.00,
                "waste_cost": 465.50,
                "hourly_rate": 2393.62,
                "cost_per_unit": 20.24,
                "downtime_minutes": 47,
                "waste_count": 23
            }
        }
    )

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Human-readable asset name")
    total_loss: float = Field(..., ge=0.0, description="Total financial loss in dollars")
    downtime_cost: float = Field(default=0.0, ge=0.0, description="Cost from downtime")
    waste_cost: float = Field(default=0.0, ge=0.0, description="Cost from waste/scrap")
    hourly_rate: Optional[float] = Field(None, description="Hourly rate used for calculation")
    cost_per_unit: Optional[float] = Field(None, description="Cost per unit used for waste calculation")
    downtime_minutes: int = Field(default=0, ge=0, description="Total downtime minutes")
    waste_count: int = Field(default=0, ge=0, description="Total waste count")


class HighestCostAsset(BaseModel):
    """
    Identifies the highest-cost asset in an area query.

    Story 6.2 AC#2: Identifies highest-cost asset.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "ast-grd-005",
                "asset_name": "Grinder 5",
                "total_loss": 2340.50
            }
        }
    )

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset name")
    total_loss: float = Field(..., ge=0.0, description="Total loss amount")


class AverageComparison(BaseModel):
    """
    Comparison to average loss for the asset/area.

    Story 6.2 AC#1: Comparison to average loss.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "average_daily_loss": 1850.00,
                "current_loss": 2340.50,
                "variance": 490.50,
                "variance_percent": 26.5,
                "comparison_text": "$490.50 (26.5%) above average"
            }
        }
    )

    average_daily_loss: float = Field(..., ge=0.0, description="Average daily loss")
    current_loss: float = Field(..., ge=0.0, description="Current period loss")
    variance: float = Field(..., description="Difference from average (can be negative)")
    variance_percent: float = Field(..., description="Percentage variance from average")
    comparison_text: str = Field(..., description="Human-readable comparison")


class NonFinancialMetric(BaseModel):
    """
    Non-financial metrics returned when cost center data is missing.

    Story 6.2 AC#3: Returns available non-financial metrics.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "ast-001",
                "asset_name": "Grinder 5",
                "downtime_minutes": 47,
                "waste_count": 23,
                "note": "Unable to calculate financial impact - no cost center data"
            }
        }
    )

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset name")
    downtime_minutes: Optional[int] = Field(None, ge=0, description="Downtime minutes if available")
    waste_count: Optional[int] = Field(None, ge=0, description="Waste count if available")
    note: str = Field(..., description="Note explaining why financial data unavailable")


class FinancialImpactOutput(BaseModel):
    """
    Output schema for Financial Impact tool.

    Story 6.2 AC#1-5: Complete financial impact response.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scope": "asset: Grinder 5",
                "time_range": "yesterday",
                "total_loss": 2340.50,
                "breakdown": [],
                "per_asset_breakdown": None,
                "highest_cost_asset": None,
                "average_comparison": None,
                "message": None,
                "non_financial_metrics": None,
                "data_freshness": "2026-01-09T09:00:00Z"
            }
        }
    )

    scope: str = Field(..., description="Query scope: asset name, area name, or 'plant-wide'")
    time_range: str = Field(..., description="Time range queried")
    total_loss: Optional[float] = Field(
        None, ge=0.0, description="Total financial loss (None if no cost data)"
    )
    breakdown: List[CostBreakdown] = Field(
        default_factory=list,
        description="Breakdown by cost category (downtime, waste)"
    )
    per_asset_breakdown: Optional[List[AssetFinancialSummary]] = Field(
        None, description="Per-asset breakdown for area queries"
    )
    highest_cost_asset: Optional[HighestCostAsset] = Field(
        None, description="Asset with highest cost in area queries"
    )
    average_comparison: Optional[AverageComparison] = Field(
        None, description="Comparison to historical average"
    )
    message: Optional[str] = Field(
        None, description="Additional message (e.g., missing cost data warning)"
    )
    non_financial_metrics: Optional[List[NonFinancialMetric]] = Field(
        None, description="Available metrics when cost data unavailable"
    )
    data_freshness: str = Field(
        ..., description="Data freshness timestamp (ISO format)"
    )


# =============================================================================
# Story 6.3: Cost of Loss Tool Models
# =============================================================================


class LossCategory(str, Enum):
    """Categories of financial losses."""
    DOWNTIME = "downtime"   # Lost production from machine stoppages
    WASTE = "waste"         # Scrap and rework costs
    QUALITY = "quality"     # Quality defects, returns


class TrendDirection(str, Enum):
    """Direction of trend change."""
    UP = "up"           # Increased loss (worse)
    DOWN = "down"       # Decreased loss (better)
    STABLE = "stable"   # Within 5% threshold


class CostOfLossInput(BaseModel):
    """
    Input schema for Cost of Loss tool.

    Story 6.3 AC#1-3: Query cost of loss with optional filters.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time_range": "yesterday",
                "area": None,
                "limit": 10,
                "include_trends": False
            }
        }
    )

    time_range: str = Field(
        default="yesterday",
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
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of ranked items to return (default: 10)"
    )
    include_trends: bool = Field(
        default=False,
        description="Include trend comparison to previous period"
    )


class LossItem(BaseModel):
    """
    Single loss item in ranked list.

    Story 6.3 AC#1: For each loss: asset, category, amount, root cause
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "ast-grd-005",
                "asset_name": "Grinder 5",
                "category": "downtime",
                "amount": 3125.50,
                "root_cause": "Material Jam",
                "percentage_of_total": 25.1,
                "duration_minutes": 78
            }
        }
    )

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Human-readable asset name")
    category: str = Field(..., description="Loss category: 'downtime', 'waste', or 'quality'")
    amount: float = Field(..., ge=0.0, description="Cost amount in dollars")
    root_cause: Optional[str] = Field(
        None, description="Root cause (e.g., 'Material Jam') - available for downtime category"
    )
    percentage_of_total: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of total loss"
    )
    duration_minutes: Optional[int] = Field(
        None, ge=0, description="Duration in minutes (for downtime category)"
    )


class CategorySummary(BaseModel):
    """
    Summary of losses by category.

    Story 6.3 AC#4: Each category shows subtotal and percentage of total loss.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "downtime",
                "total_amount": 8750.50,
                "item_count": 12,
                "percentage_of_total": 70.3,
                "top_contributors": ["Material Jam", "Safety Stop", "Blade Change"]
            }
        }
    )

    category: str = Field(..., description="Loss category: 'downtime', 'waste', or 'quality'")
    total_amount: float = Field(..., ge=0.0, description="Total loss amount for this category")
    item_count: int = Field(..., ge=0, description="Number of items in this category")
    percentage_of_total: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of total loss"
    )
    top_contributors: List[str] = Field(
        default_factory=list,
        description="Top reasons/contributors for this category (max 3)"
    )


class TrendComparison(BaseModel):
    """
    Trend comparison vs previous period.

    Story 6.3 AC#2: Includes trend vs previous week (up/down/stable).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "previous_period_total": 10200.00,
                "current_period_total": 12450.75,
                "change_amount": 2250.75,
                "change_percent": 22.1,
                "trend_direction": "up"
            }
        }
    )

    previous_period_total: float = Field(..., ge=0.0, description="Total loss in previous period")
    current_period_total: float = Field(..., ge=0.0, description="Total loss in current period")
    change_amount: float = Field(..., description="Absolute change in dollars (can be negative)")
    change_percent: float = Field(..., description="Percentage change (can be negative)")
    trend_direction: str = Field(..., description="Trend direction: 'up', 'down', or 'stable'")


class AreaComparison(BaseModel):
    """
    Area comparison vs plant-wide average.

    Story 6.3 AC#3: Compares area loss to plant-wide average.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "area_loss": 5125.50,
                "plant_wide_average": 3112.69,
                "variance": 2012.81,
                "variance_percent": 64.7,
                "comparison_text": "Grinding area is 64.7% above plant average"
            }
        }
    )

    area_loss: float = Field(..., ge=0.0, description="Total loss for the filtered area")
    plant_wide_average: float = Field(..., ge=0.0, description="Plant-wide average loss")
    variance: float = Field(..., description="Variance from average (can be negative)")
    variance_percent: float = Field(..., description="Percentage variance from average")
    comparison_text: str = Field(..., description="Human-readable comparison text")


class CostOfLossOutput(BaseModel):
    """
    Output schema for Cost of Loss tool.

    Story 6.3 AC#1-5: Complete cost of loss response.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scope": "plant-wide",
                "time_range": "yesterday",
                "total_loss": 12450.75,
                "ranked_items": [],
                "category_summaries": [],
                "trend_comparison": None,
                "area_comparison": None,
                "message": None,
                "data_freshness": "2026-01-09T09:00:00Z"
            }
        }
    )

    scope: str = Field(..., description="Query scope: 'plant-wide' or area name")
    time_range: str = Field(..., description="Time range queried")
    total_loss: float = Field(..., ge=0.0, description="Total financial loss across all items")
    ranked_items: List[LossItem] = Field(
        default_factory=list,
        description="Ranked list of losses (highest first)"
    )
    category_summaries: List[CategorySummary] = Field(
        default_factory=list,
        description="Summary by category (downtime, waste, quality)"
    )
    trend_comparison: Optional[TrendComparison] = Field(
        None, description="Trend comparison to previous period (if include_trends=True)"
    )
    area_comparison: Optional[AreaComparison] = Field(
        None, description="Area vs plant-wide comparison (if area filter applied)"
    )
    message: Optional[str] = Field(
        None, description="Additional message (e.g., 'No data found')"
    )
    data_freshness: str = Field(
        ..., description="Data freshness timestamp (ISO format)"
    )


# =============================================================================
# Story 6.4: Trend Analysis Tool Models
# =============================================================================


class MetricType(str, Enum):
    """Supported metrics for trend analysis."""
    OEE = "oee"                    # Overall Equipment Effectiveness
    OUTPUT = "output"              # Production output (units)
    DOWNTIME = "downtime"          # Downtime minutes
    WASTE = "waste"                # Waste/scrap count
    AVAILABILITY = "availability"  # OEE availability component
    PERFORMANCE = "performance"    # OEE performance component
    QUALITY = "quality"            # OEE quality component


class TrendAnalysisDirection(str, Enum):
    """Direction of trend change for trend analysis tool."""
    IMPROVING = "improving"   # Slope > +5% normalized
    DECLINING = "declining"   # Slope < -5% normalized
    STABLE = "stable"         # Slope within +/- 5%


class TrendAnalysisInput(BaseModel):
    """
    Input schema for Trend Analysis tool.

    Story 6.4 AC#1-3: Query trends with optional filters and time range.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "ast-grd-005",
                "area": None,
                "metric": "oee",
                "time_range_days": 30
            }
        }
    )

    asset_id: Optional[str] = Field(
        default=None,
        description="Specific asset UUID to analyze trend for"
    )
    area: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Area name to analyze trend for (e.g., 'Grinding', 'Packaging')"
    )
    metric: str = Field(
        default="oee",
        description=(
            "Metric to analyze: 'oee', 'output', 'downtime', 'waste', "
            "'availability', 'performance', 'quality'"
        )
    )
    time_range_days: int = Field(
        default=30,
        ge=7,
        le=90,
        description="Number of days to analyze (7, 14, 30, 60, or 90 days)"
    )


class MinMaxValue(BaseModel):
    """Min or max value with date for trend statistics."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": 62.3,
                "date": "2025-12-15"
            }
        }
    )

    value: float = Field(..., description="The metric value")
    date: str = Field(..., description="Date when this value occurred (ISO format)")


class TrendStatistics(BaseModel):
    """
    Statistical summary of trend data.

    Story 6.4 AC#1: Includes mean, min/max with dates, std dev, and slope.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mean": 78.5,
                "min": {"value": 62.3, "date": "2025-12-15"},
                "max": {"value": 89.2, "date": "2026-01-05"},
                "std_dev": 6.8,
                "trend_slope": 0.42
            }
        }
    )

    mean: float = Field(..., description="Average metric value over the period")
    min: MinMaxValue = Field(..., description="Minimum value with date")
    max: MinMaxValue = Field(..., description="Maximum value with date")
    std_dev: float = Field(..., ge=0.0, description="Standard deviation")
    trend_slope: float = Field(..., description="Linear regression slope (per day)")


class TrendAnomaly(BaseModel):
    """
    Detected anomaly in trend data.

    Story 6.4 AC#5: Anomalies >2 standard deviations from mean.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-12-15",
                "value": 62.3,
                "expected_value": 78.5,
                "deviation": 16.2,
                "deviation_std_devs": 2.38,
                "possible_cause": "Material Jam"
            }
        }
    )

    date: str = Field(..., description="Date of the anomaly (ISO format)")
    value: float = Field(..., description="Actual metric value")
    expected_value: float = Field(..., description="Expected value (mean)")
    deviation: float = Field(..., ge=0.0, description="Absolute deviation from mean")
    deviation_std_devs: float = Field(
        ..., ge=0.0, description="Deviation in standard deviations"
    )
    possible_cause: Optional[str] = Field(
        None, description="Possible cause from downtime reasons (if available)"
    )


class TrendBaselinePeriod(BaseModel):
    """Period definition for baseline comparison."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": "2025-12-10",
                "end": "2025-12-16"
            }
        }
    )

    start: str = Field(..., description="Start date of baseline period (ISO format)")
    end: str = Field(..., description="End date of baseline period (ISO format)")


class TrendBaselineComparison(BaseModel):
    """
    Comparison of current period to baseline (first 7 days).

    Story 6.4 AC#1: Compare current performance to baseline.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baseline_period": {"start": "2025-12-10", "end": "2025-12-16"},
                "baseline_value": 74.2,
                "current_value": 82.8,
                "change_amount": 8.6,
                "change_percent": 11.6
            }
        }
    )

    baseline_period: TrendBaselinePeriod = Field(
        ..., description="Time period used as baseline"
    )
    baseline_value: float = Field(..., description="Average value during baseline period")
    current_value: float = Field(..., description="Average value during current period")
    change_amount: float = Field(..., description="Absolute change from baseline")
    change_percent: float = Field(..., description="Percentage change from baseline")


class TrendDataPoint(BaseModel):
    """Single data point in trend time series."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2026-01-08",
                "value": 85.2
            }
        }
    )

    date: str = Field(..., description="Date of data point (ISO format)")
    value: float = Field(..., description="Metric value for this date")


class TrendAnalysisOutput(BaseModel):
    """
    Output schema for Trend Analysis tool.

    Story 6.4 AC#1-6: Complete trend analysis response.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scope": "asset: Grinder 5",
                "metric": "oee",
                "time_range_days": 30,
                "trend_direction": "improving",
                "statistics": {
                    "mean": 78.5,
                    "min": {"value": 62.3, "date": "2025-12-15"},
                    "max": {"value": 89.2, "date": "2026-01-05"},
                    "std_dev": 6.8,
                    "trend_slope": 0.42
                },
                "anomalies": [],
                "baseline_comparison": {
                    "baseline_period": {"start": "2025-12-10", "end": "2025-12-16"},
                    "baseline_value": 74.2,
                    "current_value": 82.8,
                    "change_amount": 8.6,
                    "change_percent": 11.6
                },
                "conclusion_text": "Grinder 5's OEE has been improving over the last 30 days.",
                "granularity": "daily",
                "data_points": None,
                "available_data": None,
                "suggestion": None,
                "data_freshness": "2026-01-09T09:00:00Z"
            }
        }
    )

    scope: str = Field(..., description="Query scope: asset name, area name, or 'plant-wide'")
    metric: str = Field(..., description="Metric analyzed (oee, output, downtime, etc.)")
    time_range_days: int = Field(..., description="Number of days analyzed")
    trend_direction: Optional[str] = Field(
        None, description="Trend direction: 'improving', 'declining', or 'stable' (None if insufficient data)"
    )
    statistics: Optional[TrendStatistics] = Field(
        None, description="Statistical summary (None if insufficient data)"
    )
    anomalies: List[TrendAnomaly] = Field(
        default_factory=list,
        description="Detected anomalies (values >2 std dev from mean)"
    )
    baseline_comparison: Optional[TrendBaselineComparison] = Field(
        None, description="Comparison to baseline period (first 7 days)"
    )
    conclusion_text: str = Field(
        ..., description="Human-readable conclusion about the trend"
    )
    granularity: str = Field(
        default="daily", description="Data granularity: 'daily' or 'weekly'"
    )
    data_points: Optional[List[TrendDataPoint]] = Field(
        None, description="Time series data points (optional, for charting)"
    )
    available_data: Optional[List[Dict[str, Any]]] = Field(
        None, description="Available point-in-time data when insufficient for trend (AC#4)"
    )
    suggestion: Optional[str] = Field(
        None, description="Suggestion when insufficient data (AC#4)"
    )
    data_freshness: str = Field(
        ..., description="Data freshness timestamp (ISO format)"
    )
