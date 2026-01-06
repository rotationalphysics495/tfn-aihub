"""
Action Engine Schemas

Pydantic models for Action Engine prioritization and API responses.

Story: 3.1 - Action Engine Logic
Story: 3.2 - Daily Action List API
AC: #7 - Action Item Data Structure (3.1)
AC: #7 - Response Schema (3.2)
AC: #9 - Evidence Citations NFR1 Compliance (3.2)
"""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field


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


# Story 3.2 AC#9: Priority rank mapping for sorting
PRIORITY_RANK_MAP = {
    PriorityLevel.CRITICAL: 0,
    PriorityLevel.HIGH: 1,
    PriorityLevel.MEDIUM: 2,
    PriorityLevel.LOW: 3,
}


class EvidenceRef(BaseModel):
    """
    Reference to source data supporting an action item.

    Story 3.2 AC#9: Evidence citations to prevent AI hallucination.
    Each evidence ref links to a specific data point in the database.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "table": "safety_events",
                "column": "severity",
                "value": "critical",
                "record_id": "123e4567-e89b-12d3-a456-426614174001",
                "context": "Emergency stop triggered on Grinder 5",
            }
        },
        populate_by_name=True,
    )

    # Story 3.2 AC#9: Fields per specification
    table: str = Field(
        ...,
        alias="source_table",
        description="Source table name (safety_events, daily_summaries, shift_targets, cost_centers)"
    )
    column: str = Field(
        ...,
        alias="metric_name",
        description="Column name of the key metric"
    )
    value: str = Field(
        ...,
        alias="metric_value",
        description="Value of the key metric"
    )
    record_id: str = Field(..., description="UUID of the source record")
    context: Optional[str] = Field(None, description="Additional context about the evidence")

    # Backward compatibility: expose original field names
    @computed_field
    @property
    def source_table(self) -> str:
        """Backward compatibility alias for 'table'."""
        return self.table

    @computed_field
    @property
    def metric_name(self) -> str:
        """Backward compatibility alias for 'column'."""
        return self.column

    @computed_field
    @property
    def metric_value(self) -> str:
        """Backward compatibility alias for 'value'."""
        return self.value


class ActionItem(BaseModel):
    """
    A prioritized action item for the Daily Action List.

    Supports the Evidence Card UI pattern with recommendation + evidence.

    Story 3.2 AC#7: Response schema with required fields:
    - id, priority_rank, category, asset_id, asset_name, title, description,
      financial_impact_usd, evidence_refs[], created_at
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "action-123e4567-e89b-12d3-a456-426614174001",
                "priority_rank": 0,
                "category": "safety",
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_name": "Grinder 5",
                "title": "Investigate emergency stop trigger on Grinder 5",
                "description": "Unresolved safety event detected at 14:30",
                "financial_impact_usd": 0.0,
                "evidence_refs": [
                    {
                        "table": "safety_events",
                        "column": "severity",
                        "value": "critical",
                        "record_id": "123e4567-e89b-12d3-a456-426614174001",
                        "context": "Emergency stop triggered",
                    }
                ],
                "created_at": "2026-01-06T15:00:00Z",
                "priority_level": "critical",
                "primary_metric_value": "Safety Event: Emergency Stop",
                "recommendation_text": "Investigate emergency stop trigger on Grinder 5",
                "evidence_summary": "Unresolved safety event detected at 14:30",
            }
        },
        populate_by_name=True,
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

    # Story 3.2 AC#7: Financial impact field (explicit, default 0 for non-financial items)
    financial_impact_usd: float = Field(
        default=0.0,
        ge=0,
        description="Financial impact in USD (for sorting by AC#6)"
    )

    # Story 3.2 AC#7: Computed fields for alias compatibility
    @computed_field
    @property
    def priority_rank(self) -> int:
        """
        Story 3.2 AC#7: Numeric priority rank for sorting.
        0 = critical (safety), 1 = high, 2 = medium, 3 = low
        """
        return PRIORITY_RANK_MAP.get(self.priority_level, 3)

    @computed_field
    @property
    def title(self) -> str:
        """Story 3.2 AC#7: Alias for recommendation_text."""
        return self.recommendation_text

    @computed_field
    @property
    def description(self) -> str:
        """Story 3.2 AC#7: Alias for evidence_summary."""
        return self.evidence_summary


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
