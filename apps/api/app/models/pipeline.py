"""
Pipeline Data Models

Pydantic models for the Morning Report batch pipeline (Story 2.1).
Handles raw data extraction, transformation, and calculation schemas.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PipelineStatus(str, Enum):
    """Status of a pipeline execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SeverityLevel(str, Enum):
    """Severity levels for safety events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Raw Data Models (from MSSQL extraction)
# =============================================================================


class RawProductionRecord(BaseModel):
    """Raw production output record extracted from MSSQL."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "GRINDER_05",
                "production_date": "2026-01-05",
                "units_produced": 1500,
                "units_scrapped": 25,
                "planned_units": 1800,
            }
        }
    )

    source_id: str = Field(..., description="MSSQL locationName mapping to assets.source_id")
    production_date: date
    units_produced: Optional[int] = None
    units_scrapped: Optional[int] = None
    planned_units: Optional[int] = None


class RawDowntimeRecord(BaseModel):
    """Raw downtime record extracted from MSSQL."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "GRINDER_05",
                "event_timestamp": "2026-01-05T14:30:00",
                "duration_minutes": 45,
                "reason_code": "Mechanical Failure",
                "description": "Belt replacement required",
            }
        }
    )

    source_id: str
    event_timestamp: datetime
    duration_minutes: int
    reason_code: Optional[str] = None
    description: Optional[str] = None


class RawQualityRecord(BaseModel):
    """Raw quality/scrap record extracted from MSSQL."""

    source_id: str
    production_date: date
    good_units: Optional[int] = None
    total_units: Optional[int] = None
    scrap_units: Optional[int] = None
    rework_units: Optional[int] = None


class RawLaborRecord(BaseModel):
    """Raw labor record extracted from MSSQL."""

    source_id: str
    production_date: date
    planned_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    headcount: Optional[int] = None


class ExtractedData(BaseModel):
    """Aggregate of all raw data extracted from MSSQL for a given date."""

    target_date: date
    production_records: List[RawProductionRecord] = Field(default_factory=list)
    downtime_records: List[RawDowntimeRecord] = Field(default_factory=list)
    quality_records: List[RawQualityRecord] = Field(default_factory=list)
    labor_records: List[RawLaborRecord] = Field(default_factory=list)


# =============================================================================
# Transformed Data Models (after cleansing)
# =============================================================================


class CleanedProductionData(BaseModel):
    """Production data after cleansing and transformation."""

    asset_id: UUID
    source_id: str
    production_date: date

    # Validated production counts (NULLs resolved to 0)
    units_produced: int = 0
    units_scrapped: int = 0
    planned_units: int = 0

    # Quality metrics
    good_units: int = 0
    total_units: int = 0

    # Downtime aggregate
    total_downtime_minutes: int = 0

    # Flags
    has_production_data: bool = False  # False if no data existed (vs 0 output)

    @field_validator("units_produced", "units_scrapped", "planned_units",
                     "good_units", "total_units", "total_downtime_minutes", mode="before")
    @classmethod
    def validate_non_negative(cls, v):
        """Ensure all counts are non-negative."""
        if v is None:
            return 0
        return max(0, int(v))


# =============================================================================
# Calculation Result Models
# =============================================================================


class OEEMetrics(BaseModel):
    """OEE (Overall Equipment Effectiveness) calculation results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "availability": 0.92,
                "performance": 0.85,
                "quality": 0.98,
                "oee_overall": 0.767,
            }
        }
    )

    # Individual OEE components (0.0 to 1.0)
    availability: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    performance: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    quality: Decimal = Field(default=Decimal("0"), ge=0, le=1)

    # Overall OEE (availability x performance x quality)
    oee_overall: Decimal = Field(default=Decimal("0"), ge=0, le=1)

    # Supporting data for calculations
    run_time_minutes: int = 0
    planned_production_time_minutes: int = 0
    actual_output: int = 0
    theoretical_max_output: int = 0
    good_units: int = 0
    total_units: int = 0


class FinancialMetrics(BaseModel):
    """Financial impact calculation results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "downtime_cost_dollars": Decimal("2250.00"),
                "waste_cost_dollars": Decimal("175.50"),
                "total_financial_loss_dollars": Decimal("2425.50"),
            }
        }
    )

    # Cost breakdown
    downtime_cost_dollars: Decimal = Field(default=Decimal("0"), ge=0)
    waste_cost_dollars: Decimal = Field(default=Decimal("0"), ge=0)

    # Total loss
    total_financial_loss_dollars: Decimal = Field(default=Decimal("0"), ge=0)

    # Supporting data
    downtime_minutes: int = 0
    hourly_rate: Decimal = Field(default=Decimal("0"), ge=0)
    scrap_units: int = 0
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)


# =============================================================================
# Daily Summary Models (for Supabase storage)
# =============================================================================


class DailySummaryCreate(BaseModel):
    """Data model for creating/updating a daily summary in Supabase."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "report_date": "2026-01-05",
                "oee_percentage": 76.7,
                "actual_output": 1500,
                "target_output": 1800,
                "downtime_minutes": 45,
                "waste_count": 25,
                "financial_loss_dollars": 2425.50,
            }
        }
    )

    asset_id: UUID
    report_date: date
    oee_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)
    actual_output: Optional[int] = Field(default=None, ge=0)
    target_output: Optional[int] = Field(default=None, ge=0)
    downtime_minutes: Optional[int] = Field(default=None, ge=0)
    waste_count: Optional[int] = Field(default=None, ge=0)
    financial_loss_dollars: Optional[Decimal] = Field(default=None, ge=0)
    smart_summary_text: Optional[str] = None


class DailySummaryResponse(DailySummaryCreate):
    """Response model for daily summary with timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Safety Event Models
# =============================================================================


class SafetyEventCreate(BaseModel):
    """Data model for creating a safety event in Supabase."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_timestamp": "2026-01-05T14:30:00Z",
                "reason_code": "Safety Issue",
                "severity": "critical",
                "description": "Emergency stop triggered",
            }
        }
    )

    asset_id: UUID
    event_timestamp: datetime
    reason_code: str
    severity: SeverityLevel = SeverityLevel.CRITICAL
    description: Optional[str] = None


class SafetyEventResponse(SafetyEventCreate):
    """Response model for safety event with metadata."""

    id: UUID
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    created_at: datetime


# =============================================================================
# Pipeline Execution Models
# =============================================================================


class PipelineExecutionLog(BaseModel):
    """Log entry for a pipeline execution."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pipeline_name": "morning_report",
                "target_date": "2026-01-05",
                "status": "success",
                "started_at": "2026-01-06T06:00:00Z",
                "completed_at": "2026-01-06T06:02:30Z",
                "records_processed": 15,
                "records_failed": 0,
            }
        }
    )

    pipeline_name: str
    target_date: date
    status: PipelineStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    records_failed: int = 0
    assets_processed: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    duration_seconds: Optional[float] = None


class PipelineResult(BaseModel):
    """Result of a complete pipeline execution."""

    status: PipelineStatus
    execution_log: PipelineExecutionLog
    summaries_created: int = 0
    summaries_updated: int = 0
    safety_events_created: int = 0
    error_message: Optional[str] = None


# =============================================================================
# API Request/Response Models
# =============================================================================


class PipelineTriggerRequest(BaseModel):
    """Request to manually trigger the pipeline."""

    target_date: Optional[date] = Field(
        default=None,
        description="Date to process. Defaults to yesterday (T-1)."
    )
    force: bool = Field(
        default=False,
        description="Force re-run even if data exists for the date."
    )


class PipelineTriggerResponse(BaseModel):
    """Response after triggering pipeline."""

    message: str
    status: PipelineStatus
    target_date: date
    execution_id: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    """Response for pipeline status query."""

    last_run: Optional[PipelineExecutionLog] = None
    is_running: bool = False
    next_scheduled_run: Optional[datetime] = None
