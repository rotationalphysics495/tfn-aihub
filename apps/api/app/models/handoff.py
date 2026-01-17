"""
Handoff Models (Story 9.1)

Pydantic schemas for shift handoff management.
Used by the handoff service for creating and managing shift handoffs.

AC#1: Create handoff flow with pre-populated assets and auto-detected shift
AC#2: Handoff screen with summary, notes, and confirmation
AC#3: No assets assigned error handling
AC#4: Duplicate handoff handling

References:
- [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
- [Source: prd-functional-requirements.md#FR21-FR30]
"""

from typing import Optional, List
from enum import Enum
from datetime import datetime, date, timezone
from uuid import UUID
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class ShiftType(str, Enum):
    """
    Type of shift for handoff (AC#1).

    Standard 8-hour shifts:
    - Morning: 6:00 AM - 2:00 PM
    - Afternoon: 2:00 PM - 10:00 PM
    - Night: 10:00 PM - 6:00 AM
    """
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


class HandoffStatus(str, Enum):
    """
    Status of a shift handoff (AC#4).

    draft: Handoff is being created, can be edited
    pending_acknowledgment: Handoff submitted, waiting for incoming supervisor
    acknowledged: Incoming supervisor has acknowledged receipt
    """
    DRAFT = "draft"
    PENDING_ACKNOWLEDGMENT = "pending_acknowledgment"
    ACKNOWLEDGED = "acknowledged"


class ShiftHandoffBase(BaseModel):
    """
    Base schema for shift handoff data.

    Common fields shared between create and read operations.
    """
    shift_date: date = Field(..., description="Date of the shift")
    shift_type: ShiftType = Field(..., description="Type of shift (morning/afternoon/night)")
    assets_covered: List[UUID] = Field(
        default_factory=list,
        description="List of asset IDs covered in this handoff"
    )
    summary: Optional[str] = Field(None, description="Auto-generated shift summary")
    text_notes: Optional[str] = Field(None, description="User-added text notes")


class ShiftHandoffCreate(ShiftHandoffBase):
    """
    Schema for creating a new shift handoff (AC#1, AC#2).

    Used when a supervisor initiates the handoff process.
    """
    pass


class ShiftHandoffUpdate(BaseModel):
    """
    Schema for updating a draft handoff (AC#4).

    Only draft handoffs can be updated.
    """
    summary: Optional[str] = Field(None, description="Updated summary")
    text_notes: Optional[str] = Field(None, description="Updated text notes")
    assets_covered: Optional[List[UUID]] = Field(None, description="Updated asset list")


class ShiftHandoff(ShiftHandoffBase):
    """
    Complete shift handoff schema (AC#1, AC#2).

    Represents a full handoff record with all fields.
    """
    id: UUID = Field(..., description="Unique handoff identifier")
    user_id: UUID = Field(..., description="User ID of the outgoing supervisor")
    status: HandoffStatus = Field(
        default=HandoffStatus.DRAFT,
        description="Current handoff status"
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="When the handoff was created"
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        description="When the handoff was last updated"
    )

    model_config = {"from_attributes": True}


class ShiftTimeRange(BaseModel):
    """
    Time range for a shift (AC#1).

    Represents the start and end times for shift data collection.
    """
    shift_type: ShiftType = Field(..., description="Detected shift type")
    start_time: datetime = Field(..., description="Start of shift period")
    end_time: datetime = Field(..., description="End of shift period")
    shift_date: date = Field(..., description="Date of the shift")


class SupervisorAsset(BaseModel):
    """
    Asset assigned to a supervisor (AC#1, AC#3).

    Represents an asset in the supervisor_assignments table.
    """
    asset_id: UUID = Field(..., description="Asset unique identifier")
    asset_name: str = Field(..., description="Asset display name")
    area_name: Optional[str] = Field(None, description="Production area name")


class HandoffExistsResponse(BaseModel):
    """
    Response when a handoff already exists (AC#4).

    Provides information about the existing handoff.
    """
    exists: bool = Field(..., description="Whether a handoff exists")
    existing_handoff_id: Optional[UUID] = Field(None, description="ID of existing handoff")
    status: Optional[HandoffStatus] = Field(None, description="Status of existing handoff")
    message: str = Field(..., description="User-friendly message")
    can_edit: bool = Field(False, description="Whether user can edit the existing handoff")
    can_add_supplemental: bool = Field(
        False,
        description="Whether user can add a supplemental note"
    )


class HandoffCreationResponse(BaseModel):
    """
    Response after handoff creation attempt.

    Includes shift detection info and pre-populated data.
    """
    handoff: Optional[ShiftHandoff] = Field(None, description="Created handoff if successful")
    shift_info: ShiftTimeRange = Field(..., description="Detected shift information")
    assigned_assets: List[SupervisorAsset] = Field(
        default_factory=list,
        description="Assets assigned to the supervisor"
    )
    existing_handoff: Optional[HandoffExistsResponse] = Field(
        None,
        description="Info about existing handoff if one exists"
    )


class NoAssetsError(BaseModel):
    """
    Error response when supervisor has no assigned assets (AC#3).
    """
    error: str = Field(
        default="No assets assigned - contact your administrator",
        description="Error message"
    )
    code: str = Field(default="NO_ASSETS_ASSIGNED", description="Error code")
