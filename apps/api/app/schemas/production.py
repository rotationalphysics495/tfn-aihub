"""
Production Schemas

Pydantic models for production workcenter summary API responses.

Story: 11.1 - Workcenter Summary API Endpoint
AC: #1 - Workcenter-grouped response with aggregations
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class ShiftBreakdown(BaseModel):
    """Per-shift performance metrics for a workcenter or asset."""

    shift: str = Field(..., description="Shift name (morning, afternoon, night)")
    actual_output: int = Field(0, ge=0, description="Units produced during this shift")
    target_output: int = Field(0, ge=0, description="Target units for this shift")
    attainment_pct: float = Field(0.0, ge=0, description="Actual/target * 100")
    oee: Optional[float] = Field(None, description="OEE percentage for this shift")
    downtime_minutes: Optional[int] = Field(None, description="Downtime minutes for this shift")


class AssetDetail(BaseModel):
    """Per-asset production detail within a workcenter."""

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset display name")
    actual_output: int = Field(..., ge=0, description="Units produced")
    target_output: int = Field(..., ge=0, description="Sum of shift target units")
    attainment_pct: float = Field(..., ge=0, description="Actual/target * 100")
    oee: Optional[float] = Field(None, description="OEE percentage")
    downtime_minutes: Optional[int] = Field(None, description="Total downtime minutes")
    hit_target: bool = Field(..., description="Whether actual >= target")


class WorkcenterEntry(BaseModel):
    """Aggregated production data for one workcenter."""

    workcenter: str = Field(..., description="Workcenter name (e.g., Grinding)")
    total_actual: int = Field(..., ge=0, description="Sum of units_produced across assets")
    total_target: int = Field(..., ge=0, description="Sum of target_units across assets")
    attainment_pct: float = Field(..., ge=0, description="total_actual / total_target * 100")
    assets_hit: int = Field(..., ge=0, description="Count of assets meeting target")
    assets_missed: int = Field(..., ge=0, description="Count of assets below target")
    assets: List[AssetDetail] = Field(default_factory=list, description="Per-asset breakdown")
    shift_breakdown: Optional[List[ShiftBreakdown]] = Field(
        default=None, description="Per-shift breakdown when shift data is available"
    )


class WorkcenterSummaryResponse(BaseModel):
    """Response model for workcenter production summary."""

    workcenters: List[WorkcenterEntry] = Field(default_factory=list)
    report_date: date = Field(..., description="The date for this summary")
    message: Optional[str] = Field(None, description="Status message (e.g., no data available)")


# =============================================================================
# Schedule Attainment Models (Story 12.5)
# =============================================================================


class ProductAttainment(BaseModel):
    """Per-product attainment detail within a workcenter."""

    product_name: str = Field(..., description="Product name")
    product_id: str = Field(..., description="Product UUID")
    scheduled_quantity: int = Field(0, description="Scheduled quantity")
    actual_quantity: int = Field(0, description="Actual quantity produced")
    attainment_pct: float = Field(0.0, description="Attainment percentage")


class VarianceCallout(BaseModel):
    """Variance callout for schedule deviations."""

    asset_name: str = Field(..., description="Asset that had the variance")
    message: str = Field(..., description="Human-readable variance description")
    variance_type: str = Field(..., description="swap, missing, or unscheduled")


class WorkcenterScheduleAttainment(BaseModel):
    """Schedule attainment data for one workcenter."""

    workcenter: str = Field(..., description="Workcenter/area name")
    products: List[ProductAttainment] = Field(default_factory=list)
    variances: List[VarianceCallout] = Field(default_factory=list)
    overall_attainment_pct: float = Field(0.0, description="Overall workcenter attainment %")


class ScheduleAttainmentResponse(BaseModel):
    """Response model for schedule attainment endpoint."""

    date: str = Field(..., description="Report date (YYYY-MM-DD)")
    workcenters: List[WorkcenterScheduleAttainment] = Field(default_factory=list)
    message: Optional[str] = Field(None, description="Status message (e.g., no data)")
    has_data: bool = Field(True, description="Whether schedule data exists for this date")
