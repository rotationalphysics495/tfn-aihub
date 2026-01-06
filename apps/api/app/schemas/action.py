"""
Action Engine Schemas

Pydantic models for Action Engine prioritization and API responses.

Story: 3.1 - Action Engine Logic
AC: #7 - Action Item Data Structure
"""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActionCategory(str, Enum):
    """Category of action item - determines tier priority."""
    SAFETY = "safety"      # Tier 1 - Always first
    OEE = "oee"            # Tier 2 - After all safety
    FINANCIAL = "financial"  # Tier 3 - After all OEE


class PriorityLevel(str, Enum):
    """Priority level within category."""
    CRITICAL = "critical"  # Safety events only
    HIGH = "high"          # Severe OEE gap (>20%) or high financial loss (>$5000)
    MEDIUM = "medium"      # Moderate gaps/losses
    LOW = "low"            # Minor issues still above threshold


class EvidenceRef(BaseModel):
    """Reference to source data supporting an action item."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_table": "safety_events",
                "record_id": "123e4567-e89b-12d3-a456-426614174001",
                "metric_name": "severity",
                "metric_value": "critical",
                "context": "Emergency stop triggered on Grinder 5",
            }
        }
    )

    source_table: str = Field(..., description="Source table name (safety_events, daily_summaries)")
    record_id: str = Field(..., description="UUID of the source record")
    metric_name: str = Field(..., description="Name of the key metric")
    metric_value: str = Field(..., description="Value of the key metric")
    context: Optional[str] = Field(None, description="Additional context about the evidence")


class ActionItem(BaseModel):
    """
    A prioritized action item for the Daily Action List.

    Supports the Evidence Card UI pattern with recommendation + evidence.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "action-123e4567-e89b-12d3-a456-426614174001",
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_name": "Grinder 5",
                "priority_level": "critical",
                "category": "safety",
                "primary_metric_value": "Safety Event: Emergency Stop",
                "recommendation_text": "Investigate emergency stop trigger on Grinder 5",
                "evidence_summary": "Unresolved safety event detected at 14:30",
                "evidence_refs": [
                    {
                        "source_table": "safety_events",
                        "record_id": "123e4567-e89b-12d3-a456-426614174001",
                        "metric_name": "severity",
                        "metric_value": "critical",
                        "context": "Emergency stop triggered",
                    }
                ],
                "created_at": "2026-01-06T15:00:00Z",
            }
        }
    )

    id: str = Field(..., description="Generated action item ID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset display name")
    priority_level: PriorityLevel = Field(..., description="Priority level (critical/high/medium/low)")
    category: ActionCategory = Field(..., description="Category (safety/oee/financial)")
    primary_metric_value: str = Field(..., description="Primary metric display value (e.g., 'OEE: 72.5%')")
    recommendation_text: str = Field(..., description="Brief action recommendation")
    evidence_summary: str = Field(..., description="One-line evidence description")
    evidence_refs: List[EvidenceRef] = Field(
        default_factory=list,
        description="References to source data records (NFR1 compliance)"
    )
    created_at: datetime = Field(..., description="When the action item was generated")


class ActionListResponse(BaseModel):
    """Response model for the daily action list endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "actions": [],
                "generated_at": "2026-01-06T06:30:00Z",
                "report_date": "2026-01-05",
                "total_count": 0,
                "counts_by_category": {"safety": 0, "oee": 0, "financial": 0},
            }
        }
    )

    actions: List[ActionItem] = Field(
        default_factory=list,
        description="Prioritized list of action items"
    )
    generated_at: datetime = Field(..., description="When the action list was generated")
    report_date: date = Field(..., description="The report date (T-1)")
    total_count: int = Field(0, ge=0, description="Total number of action items")
    counts_by_category: Dict[str, int] = Field(
        default_factory=lambda: {"safety": 0, "oee": 0, "financial": 0},
        description="Count of items per category"
    )


class ActionEngineConfig(BaseModel):
    """Configuration for Action Engine thresholds."""

    target_oee_percentage: float = Field(
        default=85.0,
        ge=0,
        le=100,
        description="Target OEE percentage for filtering"
    )
    financial_loss_threshold: float = Field(
        default=1000.0,
        ge=0,
        description="Minimum financial loss to include (USD)"
    )
    oee_high_gap_threshold: float = Field(
        default=20.0,
        ge=0,
        le=100,
        description="OEE gap percentage for 'high' priority"
    )
    oee_medium_gap_threshold: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="OEE gap percentage for 'medium' priority"
    )
    financial_high_threshold: float = Field(
        default=5000.0,
        ge=0,
        description="Financial loss for 'high' priority (USD)"
    )
    financial_medium_threshold: float = Field(
        default=2000.0,
        ge=0,
        description="Financial loss for 'medium' priority (USD)"
    )
