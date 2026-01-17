"""
User Preferences Models (Story 8.8)

Pydantic schemas for user preferences API endpoints.

AC#3: Store preferences in user_preferences table
AC#5: Settings page edit and save

References:
- [Source: architecture/voice-briefing.md#User Preferences Architecture]
- [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class UserRoleEnum(str, Enum):
    """User role for briefing scope."""
    PLANT_MANAGER = "plant_manager"
    SUPERVISOR = "supervisor"


class DetailLevelEnum(str, Enum):
    """Detail level for briefings."""
    SUMMARY = "summary"
    DETAILED = "detailed"


# Default area order from architecture spec
DEFAULT_AREA_ORDER = [
    "Packing",
    "Rychigers",
    "Grinding",
    "Powder",
    "Roasting",
    "Green Bean",
    "Flavor Room",
]


class UserPreferencesBase(BaseModel):
    """
    Base schema for user preferences.

    Contains all preference fields.
    """
    role: UserRoleEnum = Field(
        ...,
        description="User's organizational role: plant_manager or supervisor"
    )
    area_order: List[str] = Field(
        default_factory=lambda: DEFAULT_AREA_ORDER.copy(),
        description="Preferred area order for briefings"
    )
    detail_level: DetailLevelEnum = Field(
        default=DetailLevelEnum.SUMMARY,
        description="Briefing detail level: summary or detailed"
    )
    voice_enabled: bool = Field(
        default=True,
        description="Whether voice briefings are enabled"
    )

    @field_validator('area_order')
    @classmethod
    def validate_area_order(cls, v: List[str]) -> List[str]:
        """Ensure area_order is not empty and contains only valid areas."""
        if not v:
            return DEFAULT_AREA_ORDER.copy()

        # Validate that all provided areas are in the valid set
        valid_areas = set(DEFAULT_AREA_ORDER)
        for area in v:
            if area not in valid_areas:
                raise ValueError(f"Invalid area: '{area}'. Must be one of: {', '.join(DEFAULT_AREA_ORDER)}")

        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate areas are not allowed in area_order")

        return v


class CreateUserPreferencesRequest(UserPreferencesBase):
    """
    Request schema for creating user preferences (onboarding).

    AC#3: POST /api/v1/preferences
    """
    onboarding_complete: bool = Field(
        default=True,
        description="Mark onboarding as complete"
    )


class UpdateUserPreferencesRequest(BaseModel):
    """
    Request schema for updating user preferences (settings page).

    AC#5: PUT /api/v1/preferences
    All fields are optional for partial updates.
    """
    role: Optional[UserRoleEnum] = Field(
        None,
        description="User's organizational role"
    )
    area_order: Optional[List[str]] = Field(
        None,
        description="Preferred area order for briefings"
    )
    detail_level: Optional[DetailLevelEnum] = Field(
        None,
        description="Briefing detail level"
    )
    voice_enabled: Optional[bool] = Field(
        None,
        description="Whether voice briefings are enabled"
    )

    @field_validator('area_order')
    @classmethod
    def validate_area_order(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure area_order contains only valid areas when provided."""
        if v is None:
            return v

        if not v:
            return DEFAULT_AREA_ORDER.copy()

        # Validate that all provided areas are in the valid set
        valid_areas = set(DEFAULT_AREA_ORDER)
        for area in v:
            if area not in valid_areas:
                raise ValueError(f"Invalid area: '{area}'. Must be one of: {', '.join(DEFAULT_AREA_ORDER)}")

        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate areas are not allowed in area_order")

        return v


class UserPreferencesResponse(UserPreferencesBase):
    """
    Response schema for user preferences.

    Includes user_id and metadata.
    """
    user_id: str = Field(..., description="User ID")
    onboarding_complete: bool = Field(
        default=False,
        description="Whether user has completed onboarding"
    )
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")

    class Config:
        from_attributes = True
