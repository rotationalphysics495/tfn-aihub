"""
Schedule Upload Schemas

Pydantic models for schedule upload preview/confirm request-response cycle.

Story: 12.3 - Schedule Upload API
AC: #1 - CSV Upload Preview
AC: #2 - Upload Confirmation
AC: #3 - Excel Support
AC: #4 - Fuzzy Asset Matching
AC: #5 - Validation Errors
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetMatchStatus(str, Enum):
    """Status of asset name matching against existing assets."""
    MATCHED = "matched"
    SUGGESTED = "suggested"
    UNMATCHED = "unmatched"


class RowValidationError(BaseModel):
    """Validation error for a specific field in a row."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "row_number": 2,
                "field": "scheduled_quantity",
                "message": "Scheduled quantity must be a positive integer",
            }
        }
    )

    row_number: int = Field(..., description="1-based row number in the uploaded file")
    field: str = Field(..., description="Field name that has the validation error")
    message: str = Field(..., description="Human-readable error description")


class ScheduleRowPreview(BaseModel):
    """Preview of a single parsed schedule row with match and validation status."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "row_number": 1,
                "date": "2026-02-16",
                "shift": "Day",
                "asset_name": "Grinder 1",
                "product_name": "Dark Roast 12oz",
                "scheduled_quantity": "500",
                "asset_match_status": "matched",
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "suggestions": [],
                "product_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_new_product": False,
                "errors": [],
            }
        }
    )

    row_number: int = Field(..., description="1-based row number in the uploaded file")
    date: str = Field(..., description="Scheduled date from the file")
    shift: str = Field(..., description="Shift value from the file")
    asset_name: str = Field(..., description="Asset name from the file")
    product_name: str = Field(..., description="Product name from the file")
    scheduled_quantity: str = Field(..., description="Scheduled quantity from the file")
    asset_match_status: str = Field(..., description="Asset matching status: matched, suggested, or unmatched")
    asset_id: Optional[str] = Field(None, description="Matched asset UUID, if found")
    suggestions: List[str] = Field(default_factory=list, description="Suggested asset names for fuzzy matches")
    product_id: Optional[str] = Field(None, description="Matched product UUID, if found")
    is_new_product: bool = Field(False, description="Whether this product needs to be created")
    errors: List[RowValidationError] = Field(default_factory=list, description="Validation errors for this row")


class SchedulePreviewResponse(BaseModel):
    """Response model for schedule upload preview (AC#1)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parsed_rows_count": 3,
                "rows": [],
                "has_errors": False,
                "matched_assets": [],
                "matched_products": [],
                "new_products": [],
            }
        }
    )

    parsed_rows_count: int = Field(..., description="Total number of data rows parsed")
    rows: List[ScheduleRowPreview] = Field(default_factory=list, description="Preview of each parsed row")
    has_errors: bool = Field(False, description="True if any row has validation or matching errors")
    matched_assets: List[str] = Field(default_factory=list, description="List of successfully matched asset names")
    matched_products: List[str] = Field(default_factory=list, description="List of matched existing product names")
    new_products: List[str] = Field(default_factory=list, description="List of new product names to be created")


class ScheduleConfirmRow(BaseModel):
    """A single confirmed row for schedule insertion (AC#2)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "product_name": "Dark Roast 12oz",
                "scheduled_date": "2026-02-16",
                "shift": "Day",
                "scheduled_quantity": 500,
            }
        }
    )

    asset_id: str = Field(..., description="Resolved asset UUID")
    product_name: str = Field(..., description="Product name (existing or new)")
    scheduled_date: str = Field(..., description="Scheduled date (YYYY-MM-DD)")
    shift: str = Field(..., description="Shift identifier")
    scheduled_quantity: int = Field(..., gt=0, description="Scheduled production quantity")

    @field_validator("scheduled_date")
    @classmethod
    def validate_scheduled_date(cls, v: str) -> str:
        """Validate scheduled_date is a valid ISO date string."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("scheduled_date must be in YYYY-MM-DD format")
        return v


class ScheduleConfirmRequest(BaseModel):
    """Request model for confirming and committing schedule data (AC#2)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rows": [
                    {
                        "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                        "product_name": "Dark Roast 12oz",
                        "scheduled_date": "2026-02-16",
                        "shift": "Day",
                        "scheduled_quantity": 500,
                    }
                ]
            }
        }
    )

    rows: List[ScheduleConfirmRow] = Field(..., description="List of confirmed schedule rows to insert")


class ScheduleConfirmResponse(BaseModel):
    """Response model for schedule confirmation (AC#2)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rows_inserted": 3,
                "products_created": 1,
                "total_processed": 3,
            }
        }
    )

    rows_inserted: int = Field(..., description="Number of schedule rows inserted")
    products_created: int = Field(0, description="Number of new products created")
    total_processed: int = Field(..., description="Total number of rows processed")
