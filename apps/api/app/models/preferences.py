"""
User Preferences Models (Story 8.8, 8.9)

Pydantic schemas for user preferences API endpoints.

AC#3: Store preferences in user_preferences table
AC#5: Settings page edit and save

Story 8.9 additions:
- Mem0PreferenceContext schema for AI-ready semantic format
- Support for dual storage (Supabase + Mem0)

References:
- [Source: architecture/voice-briefing.md#User Preferences Architecture]
- [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
"""

from typing import List, Optional, Dict, Any
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


class Mem0PreferenceContext(BaseModel):
    """
    Schema for AI-ready semantic preference context (Story 8.9).

    Transforms structured preferences to natural language for Mem0 storage.
    Used for AI context enrichment and personalization.

    AC#2: Mem0 context includes semantic descriptions
    AC#4: Semantic context about why preferences were set
    """
    semantic_descriptions: List[str] = Field(
        default_factory=list,
        description="Natural language descriptions of user preferences"
    )
    preference_reason: Optional[str] = Field(
        None,
        description="Optional context about why preferences were set (from onboarding/conversation)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for Mem0 storage (timestamps, version info)"
    )

    @classmethod
    def from_preferences(
        cls,
        preferences: "UserPreferencesResponse",
        reason: Optional[str] = None,
    ) -> "Mem0PreferenceContext":
        """
        Transform structured preferences to semantic Mem0 context.

        Args:
            preferences: User preferences from database
            reason: Optional context about why preferences were set

        Returns:
            Mem0PreferenceContext with natural language descriptions
        """
        descriptions = []

        # Role description
        if preferences.role == UserRoleEnum.PLANT_MANAGER:
            descriptions.append(
                "User is a Plant Manager with full visibility across all plant areas and assets"
            )
        elif preferences.role == UserRoleEnum.SUPERVISOR:
            descriptions.append(
                "User is a Supervisor with scoped access to assigned assets only"
            )

        # Area order description
        if preferences.area_order:
            first_area = preferences.area_order[0]
            area_list = ", then ".join(preferences.area_order[:3])
            if len(preferences.area_order) > 3:
                area_list += ", and others"
            descriptions.append(
                f"User prefers to hear about {first_area} first, followed by {area_list} in their briefings"
            )

        # Detail level description
        if preferences.detail_level == DetailLevelEnum.SUMMARY:
            descriptions.append(
                "User prefers concise summary briefings rather than detailed reports"
            )
        elif preferences.detail_level == DetailLevelEnum.DETAILED:
            descriptions.append(
                "User prefers detailed, comprehensive briefings with full analysis"
            )

        # Voice preference description
        if preferences.voice_enabled:
            descriptions.append("User prefers voice delivery for briefings")
        else:
            descriptions.append(
                "User prefers text-only briefings without voice delivery"
            )

        return cls(
            semantic_descriptions=descriptions,
            preference_reason=reason,
            metadata={
                "user_id": preferences.user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "preference_version": preferences.updated_at,
            },
        )
