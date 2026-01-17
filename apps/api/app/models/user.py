"""
User models for authentication (Story 8.5)

Models for user authentication and role-based access control.

References:
- [Source: architecture/voice-briefing.md#Role-Based Access Control]
"""
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class UserRole(str, Enum):
    """
    User organizational role for RBAC.

    Used to determine briefing scope and access control.
    """
    PLANT_MANAGER = "plant_manager"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    """
    Represents the currently authenticated user extracted from JWT token.
    Used as the return type for the get_current_user dependency.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "role": "authenticated",
            }
        }
    )

    id: str
    email: Optional[str] = None
    role: str = "authenticated"


class CurrentUserWithRole(BaseModel):
    """
    Extends CurrentUser with organizational role context (Story 8.5).

    Used by briefing services to scope content based on user role:
    - Plant Manager: Sees all areas (plant-wide)
    - Supervisor: Sees only assigned assets (scoped)
    - Admin: Full access for management

    AC#1: Role context for briefing scoping (FR15)
    AC#4: Fresh assignment queries for immediate reflection

    References:
    - [Source: architecture/voice-briefing.md#Role-Based Access Control]
    - [Source: prd/prd-functional-requirements.md#FR15]
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "supervisor@example.com",
                "role": "authenticated",
                "user_role": "supervisor",
                "assigned_asset_ids": [
                    "asset-uuid-1",
                    "asset-uuid-2",
                ],
            }
        }
    )

    # From JWT token
    id: str = Field(..., description="User ID from JWT sub claim")
    email: Optional[str] = Field(None, description="User email from JWT")
    role: str = Field("authenticated", description="JWT role (authenticated/service_role)")

    # From user_roles table
    user_role: UserRole = Field(
        UserRole.SUPERVISOR,
        description="Organizational role: plant_manager | supervisor | admin"
    )

    # From supervisor_assignments table (for supervisors only)
    assigned_asset_ids: List[str] = Field(
        default_factory=list,
        description="Asset IDs assigned to supervisor (empty for plant managers)"
    )

    @property
    def is_supervisor(self) -> bool:
        """Check if user is a supervisor."""
        return self.user_role == UserRole.SUPERVISOR

    @property
    def is_plant_manager(self) -> bool:
        """Check if user is a plant manager."""
        return self.user_role == UserRole.PLANT_MANAGER

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.user_role == UserRole.ADMIN

    @property
    def has_assigned_assets(self) -> bool:
        """Check if user has any assigned assets."""
        return len(self.assigned_asset_ids) > 0


class UserPreferences(BaseModel):
    """
    User preferences for briefing delivery (Story 8.5, 8.8).

    Stores preferences that affect how briefings are generated and delivered.

    References:
    - [Source: prd/prd-functional-requirements.md#FR37]
    - [Source: prd/prd-functional-requirements.md#FR39]
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "supervisor",
                "area_order": ["grinding", "packing", "roasting"],
                "detail_level": "detailed",
                "voice_enabled": True,
            }
        }
    )

    user_id: str = Field(..., description="User ID")
    role: Optional[str] = Field(None, description="Denormalized role for quick access")
    area_order: List[str] = Field(
        default_factory=list,
        description="Preferred area order for briefings (FR39)"
    )
    detail_level: str = Field(
        "detailed",
        description="Detail level: summary | detailed (FR37)"
    )
    voice_enabled: bool = Field(True, description="Whether voice briefings are enabled")
