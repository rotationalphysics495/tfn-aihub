"""
Financial Impact Schemas

Pydantic models for financial impact calculations and API responses.

Story: 2.7 - Financial Impact Calculator
AC: #4 - Combined Financial Impact
AC: #5 - API Endpoint for Financial Data
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialImpactResponse(BaseModel):
    """Response model for financial impact calculations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "period_start": "2026-01-05",
                "period_end": "2026-01-05",
                "downtime_minutes": 45,
                "downtime_loss": 112.50,
                "waste_count": 10,
                "waste_loss": 250.00,
                "total_loss": 362.50,
                "currency": "USD",
                "standard_hourly_rate": 150.00,
                "cost_per_unit": 25.00,
                "is_estimated": False,
            }
        }
    )

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Asset display name")
    period_start: date = Field(..., description="Start date of the period")
    period_end: date = Field(..., description="End date of the period")
    downtime_minutes: int = Field(0, ge=0, description="Total downtime in minutes")
    downtime_loss: float = Field(0.0, ge=0, description="Financial loss from downtime in dollars")
    waste_count: int = Field(0, ge=0, description="Total waste/scrap count")
    waste_loss: float = Field(0.0, ge=0, description="Financial loss from waste in dollars")
    total_loss: float = Field(0.0, ge=0, description="Total financial loss in dollars")
    currency: str = Field("USD", description="Currency code")
    standard_hourly_rate: float = Field(0.0, ge=0, description="Hourly rate used for calculation")
    cost_per_unit: float = Field(0.0, ge=0, description="Cost per unit used for waste calculation")
    is_estimated: bool = Field(False, description="True if default rates were used (no cost_centers entry)")


class FinancialImpactBreakdown(BaseModel):
    """Detailed breakdown of financial impact components."""

    downtime_minutes: int = Field(0, ge=0, description="Downtime duration in minutes")
    downtime_hours: float = Field(0.0, ge=0, description="Downtime duration in hours")
    hourly_rate: float = Field(0.0, ge=0, description="Standard hourly rate")
    downtime_loss: float = Field(0.0, ge=0, description="Downtime financial loss")
    waste_count: int = Field(0, ge=0, description="Waste/scrap count")
    cost_per_unit: float = Field(0.0, ge=0, description="Cost per waste unit")
    waste_loss: float = Field(0.0, ge=0, description="Waste financial loss")
    total_loss: float = Field(0.0, ge=0, description="Total financial loss")


class AssetFinancialContext(BaseModel):
    """Financial context for a single asset."""

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Asset display name")
    standard_hourly_rate: float = Field(0.0, ge=0, description="Asset's standard hourly rate")
    cost_per_unit: float = Field(0.0, ge=0, description="Cost per unit for this asset")
    is_estimated: bool = Field(False, description="True if using default rates")


class LiveFinancialImpact(BaseModel):
    """Live financial impact for current shift (Pipeline B)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "shift_start": "2026-01-06T06:00:00Z",
                "accumulated_downtime_minutes": 30,
                "accumulated_downtime_loss": 75.00,
                "accumulated_waste_count": 5,
                "accumulated_waste_loss": 125.00,
                "accumulated_total_loss": 200.00,
                "currency": "USD",
                "is_estimated": False,
            }
        }
    )

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: Optional[str] = Field(None, description="Asset display name")
    shift_start: Optional[str] = Field(None, description="Shift start timestamp (ISO format)")
    accumulated_downtime_minutes: int = Field(0, ge=0, description="Accumulated downtime this shift")
    accumulated_downtime_loss: float = Field(0.0, ge=0, description="Accumulated downtime loss this shift")
    accumulated_waste_count: int = Field(0, ge=0, description="Accumulated waste count this shift")
    accumulated_waste_loss: float = Field(0.0, ge=0, description="Accumulated waste loss this shift")
    accumulated_total_loss: float = Field(0.0, ge=0, description="Accumulated total loss this shift")
    currency: str = Field("USD", description="Currency code")
    is_estimated: bool = Field(False, description="True if using default rates")
