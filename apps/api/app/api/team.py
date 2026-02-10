"""
Team API Endpoints

Provides team member listing for any authenticated user.
Used by features like Assign Follow-Up where non-admin users
need to see available team members.
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client, create_client

from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.user import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class TeamMember(BaseModel):
    """A team member with their role."""
    user_id: UUID = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="User email (if available)")
    role: str = Field(..., description="User role: plant_manager, supervisor, admin")


class TeamMembersResponse(BaseModel):
    """Response for listing team members."""
    members: List[TeamMember]
    total_count: int


# ============================================================================
# Helpers
# ============================================================================


def _get_supabase_client() -> Optional[Client]:
    """Get Supabase client for database operations."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_key)


# Mock data for development without Supabase
_mock_team_members = [
    {"user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "email": "supervisor1@example.com", "role": "supervisor"},
    {"user_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "email": "supervisor2@example.com", "role": "supervisor"},
    {"user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "email": "manager@example.com", "role": "plant_manager"},
    {"user_id": "dddddddd-dddd-dddd-dddd-dddddddddddd", "email": "admin@example.com", "role": "admin"},
]


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/members", response_model=TeamMembersResponse)
async def list_team_members(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List all team members with their roles.

    Accessible to any authenticated user. Returns user_id, email (when
    available), and role for each team member in the user_roles table.
    Users not present in the auth table will still appear with a null email.
    """
    logger.info(f"User {current_user.id} listing team members")

    supabase = _get_supabase_client()

    if supabase is None:
        # Return mock data for development
        return TeamMembersResponse(
            members=[TeamMember(**m) for m in _mock_team_members],
            total_count=len(_mock_team_members),
        )

    try:
        # Query all rows from user_roles (service-role key bypasses RLS)
        result = supabase.table("user_roles").select("user_id, role").execute()

        members: List[TeamMember] = []
        for row in result.data:
            # Try to get email from auth.users; gracefully handle missing users
            email = None
            try:
                user_auth = supabase.auth.admin.get_user_by_id(row["user_id"])
                if user_auth and user_auth.user:
                    email = user_auth.user.email
            except Exception:
                # User may not exist in auth table — that's fine
                pass

            members.append(TeamMember(
                user_id=UUID(row["user_id"]),
                email=email,
                role=row["role"],
            ))

        return TeamMembersResponse(
            members=members,
            total_count=len(members),
        )

    except Exception as e:
        logger.error(f"Error listing team members: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list team members: {str(e)}",
        )
