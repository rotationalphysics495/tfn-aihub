"""
Production Schemas

Pydantic models for production workcenter summary API responses.

Story: 11.1 - Workcenter Summary API Endpoint
AC: #1 - Workcenter-grouped response with aggregations
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


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


class WorkcenterSummaryResponse(BaseModel):
    """Response model for workcenter production summary."""

    workcenters: List[WorkcenterEntry] = Field(default_factory=list)
    report_date: date = Field(..., description="The date for this summary")
    message: Optional[str] = Field(None, description="Status message (e.g., no data available)")
