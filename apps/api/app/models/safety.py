"""
Safety Alert Data Models

Pydantic models for the Safety Alert System (Story 2.6).
Handles safety event data structures for API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeverityLevel(str, Enum):
    """Severity levels for safety events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Safety Event Models
# =============================================================================


class SafetyEventBase(BaseModel):
    """Base model for safety events."""

    asset_id: UUID = Field(..., description="Asset UUID")
    event_timestamp: datetime = Field(..., description="When the safety event occurred")
    reason_code: str = Field(..., description="Safety reason code from MSSQL")
    severity: SeverityLevel = Field(
        default=SeverityLevel.CRITICAL,
        description="Severity level (safety events are typically critical)"
    )
    description: Optional[str] = Field(None, description="Event description")
    source_record_id: Optional[str] = Field(
        None,
        description="Reference to original MSSQL record for deduplication"
    )
    duration_minutes: Optional[int] = Field(None, description="Duration if known")


class SafetyEventCreate(SafetyEventBase):
    """Model for creating a new safety event."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_timestamp": "2026-01-06T14:30:00Z",
                "reason_code": "Safety Issue",
                "severity": "critical",
                "description": "Emergency stop triggered",
                "source_record_id": "MSSQL_DT_12345",
                "duration_minutes": 15,
            }
        }
    )


class SafetyEventResponse(SafetyEventBase):
    """Response model for safety events."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_name": "Grinder 5",
                "area": "Grinding",
                "event_timestamp": "2026-01-06T14:30:00Z",
                "reason_code": "Safety Issue",
                "severity": "critical",
                "description": "Emergency stop triggered",
                "acknowledged": False,
                "financial_impact": 1240.50,
                "created_at": "2026-01-06T14:31:00Z",
            }
        }
    )

    id: UUID = Field(..., description="Safety event ID")
    asset_name: str = Field(..., description="Asset display name")
    area: Optional[str] = Field(None, description="Plant area")
    acknowledged: bool = Field(
        default=False,
        description="Whether event has been acknowledged"
    )
    acknowledged_at: Optional[datetime] = Field(
        None,
        description="When the event was acknowledged"
    )
    acknowledged_by: Optional[UUID] = Field(
        None,
        description="User who acknowledged the event"
    )
    financial_impact: Optional[float] = Field(
        None,
        description="Calculated financial impact from cost_centers"
    )
    created_at: datetime = Field(..., description="When the event was created in system")


class SafetyEventsResponse(BaseModel):
    """Response model for safety events list."""

    events: List[SafetyEventResponse] = Field(
        default_factory=list,
        description="List of safety events"
    )
    count: int = Field(0, description="Total count of events")
    last_updated: str = Field(..., description="ISO timestamp of data freshness")


class ActiveSafetyAlertsResponse(BaseModel):
    """Response model for active (unacknowledged) safety alerts."""

    events: List[SafetyEventResponse] = Field(
        default_factory=list,
        description="List of active safety events"
    )
    count: int = Field(0, description="Count of active alerts")
    last_updated: str = Field(..., description="ISO timestamp of data freshness")


class AcknowledgeRequest(BaseModel):
    """Request model for acknowledging a safety event."""

    acknowledged_by: Optional[str] = Field(
        None,
        description="Optional user ID who acknowledged the event"
    )


class AcknowledgeResponse(BaseModel):
    """Response model after acknowledging a safety event."""

    success: bool = Field(..., description="Whether acknowledgement succeeded")
    event: Optional[SafetyEventResponse] = Field(
        None,
        description="Updated event details"
    )
    message: Optional[str] = Field(None, description="Status message")


# =============================================================================
# Dashboard Status Models
# =============================================================================


class DashboardStatusResponse(BaseModel):
    """Response model for dashboard status including safety alerts."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "safety_alert_count": 2,
                "safety_alerts_active": True,
                "total_assets": 15,
                "assets_on_target": 10,
                "assets_below_target": 3,
                "assets_above_target": 2,
                "last_poll_time": "2026-01-06T14:30:00Z",
            }
        }
    )

    safety_alert_count: int = Field(
        0,
        description="Count of unacknowledged safety alerts"
    )
    safety_alerts_active: bool = Field(
        False,
        description="Whether any safety alerts are currently active"
    )
    total_assets: int = Field(0, description="Total number of monitored assets")
    assets_on_target: int = Field(0, description="Assets currently on target")
    assets_below_target: int = Field(0, description="Assets currently below target")
    assets_above_target: int = Field(0, description="Assets currently above target")
    last_poll_time: Optional[str] = Field(
        None,
        description="Timestamp of last Live Pulse poll"
    )
