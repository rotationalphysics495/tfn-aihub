"""
Downtime Data Models

Pydantic models for the Downtime Pareto Analysis feature (Story 2.5).
Handles downtime events, Pareto analysis calculations, and financial impact data.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DataSource(str, Enum):
    """Data source for downtime analysis."""
    DAILY_SUMMARIES = "daily_summaries"
    LIVE_SNAPSHOTS = "live_snapshots"


class SeverityLevel(str, Enum):
    """Severity levels for safety events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Downtime Event Models
# =============================================================================


class DowntimeEvent(BaseModel):
    """Single downtime event with financial impact."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_id": "123e4567-e89b-12d3-a456-426614174001",
                "asset_name": "CNC Mill 01",
                "area": "Machining",
                "reason_code": "Mechanical Failure",
                "duration_minutes": 45,
                "event_timestamp": "2026-01-05T14:30:00Z",
                "end_timestamp": "2026-01-05T15:15:00Z",
                "financial_impact": 337.50,
                "is_safety_related": False,
            }
        }
    )

    id: Optional[str] = Field(None, description="Event ID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset display name")
    area: Optional[str] = Field(None, description="Plant area")
    reason_code: str = Field(..., description="Downtime reason code")
    duration_minutes: int = Field(..., ge=0, description="Downtime duration in minutes")
    event_timestamp: str = Field(..., description="Event start timestamp (ISO format)")
    end_timestamp: Optional[str] = Field(None, description="Event end timestamp (ISO format)")
    financial_impact: float = Field(0.0, ge=0, description="Financial impact in dollars")
    is_safety_related: bool = Field(False, description="Whether this is a safety-related event")
    severity: Optional[str] = Field(None, description="Safety severity level if applicable")
    description: Optional[str] = Field(None, description="Event description")


class DowntimeEventsResponse(BaseModel):
    """Response model for downtime events list."""

    events: List[DowntimeEvent] = Field(default_factory=list, description="List of downtime events")
    total_count: int = Field(0, description="Total count of events (for pagination)")
    total_downtime_minutes: int = Field(0, description="Sum of all downtime minutes")
    total_financial_impact: float = Field(0.0, description="Sum of all financial impact")
    data_source: str = Field(..., description="Data source used: daily_summaries or live_snapshots")
    last_updated: str = Field(..., description="ISO timestamp of data freshness")


# =============================================================================
# Pareto Analysis Models
# =============================================================================


class ParetoItem(BaseModel):
    """Single item in Pareto analysis results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reason_code": "Mechanical Failure",
                "total_minutes": 180,
                "percentage": 35.5,
                "cumulative_percentage": 35.5,
                "financial_impact": 1350.00,
                "event_count": 4,
                "is_safety_related": False,
            }
        }
    )

    reason_code: str = Field(..., description="Downtime reason code")
    total_minutes: int = Field(..., ge=0, description="Total downtime minutes for this reason")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total downtime")
    cumulative_percentage: float = Field(..., ge=0, le=100, description="Cumulative percentage")
    financial_impact: float = Field(0.0, ge=0, description="Total financial impact for this reason")
    event_count: int = Field(0, ge=0, description="Number of events for this reason")
    is_safety_related: bool = Field(False, description="Whether this reason is safety-related")


class ParetoResponse(BaseModel):
    """Response model for Pareto analysis."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total_downtime_minutes": 507,
                "total_financial_impact": 3802.50,
                "total_events": 12,
                "data_source": "daily_summaries",
                "last_updated": "2026-01-05T06:00:00Z",
                "threshold_80_index": 3,
            }
        }
    )

    items: List[ParetoItem] = Field(default_factory=list, description="Pareto items sorted by descending duration")
    total_downtime_minutes: int = Field(0, description="Total downtime across all reasons")
    total_financial_impact: float = Field(0.0, description="Total financial impact")
    total_events: int = Field(0, description="Total number of downtime events")
    data_source: str = Field(..., description="Data source used")
    last_updated: str = Field(..., description="ISO timestamp of data freshness")
    threshold_80_index: Optional[int] = Field(None, description="Index where cumulative percentage crosses 80%")


# =============================================================================
# Summary Widget Models
# =============================================================================


class CostOfLossSummary(BaseModel):
    """Summary widget data for Cost of Loss display."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_financial_loss": 3802.50,
                "total_downtime_minutes": 507,
                "total_downtime_hours": 8.45,
                "top_reason_code": "Mechanical Failure",
                "top_reason_percentage": 35.5,
                "safety_events_count": 2,
                "safety_downtime_minutes": 90,
            }
        }
    )

    total_financial_loss: float = Field(0.0, description="Total financial loss in dollars")
    total_downtime_minutes: int = Field(0, description="Total downtime in minutes")
    total_downtime_hours: float = Field(0.0, description="Total downtime in hours")
    top_reason_code: Optional[str] = Field(None, description="Top reason code by downtime")
    top_reason_percentage: Optional[float] = Field(None, description="Percentage of top reason")
    safety_events_count: int = Field(0, description="Number of safety-related events")
    safety_downtime_minutes: int = Field(0, description="Total safety-related downtime")
    data_source: str = Field(..., description="Data source used")
    last_updated: str = Field(..., description="ISO timestamp of data freshness")


# =============================================================================
# Safety Event Models (extended from pipeline models)
# =============================================================================


class SafetyEventDetail(BaseModel):
    """Detailed safety event information for modal/panel display."""

    id: str = Field(..., description="Safety event ID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset display name")
    area: Optional[str] = Field(None, description="Plant area")
    event_timestamp: str = Field(..., description="Event timestamp (ISO format)")
    reason_code: str = Field(..., description="Reason code")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    description: Optional[str] = Field(None, description="Event description")
    duration_minutes: Optional[int] = Field(None, description="Duration if calculated")
    financial_impact: Optional[float] = Field(None, description="Financial impact if calculated")
    is_resolved: bool = Field(False, description="Whether event is resolved")
    resolved_at: Optional[str] = Field(None, description="Resolution timestamp")


# =============================================================================
# Filter and Query Models
# =============================================================================


class DowntimeQueryParams(BaseModel):
    """Query parameters for downtime API endpoints."""

    start_date: Optional[date] = Field(None, description="Start date for query range")
    end_date: Optional[date] = Field(None, description="End date for query range")
    asset_id: Optional[str] = Field(None, description="Filter by specific asset")
    area: Optional[str] = Field(None, description="Filter by plant area")
    shift: Optional[str] = Field(None, description="Filter by shift")
    source: Optional[str] = Field(None, description="Data source: 'yesterday' or 'live'")
    limit: int = Field(50, ge=1, le=500, description="Maximum number of records to return")
    offset: int = Field(0, ge=0, description="Number of records to skip")
