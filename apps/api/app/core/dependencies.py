"""
FastAPI Dependencies for Role-Based Access Control (Story 8.5)

Provides dependencies for injecting user role context into endpoints.
Used by briefing services to scope content based on user role.

AC#1: Role context for briefing scoping (FR15)
AC#4: Fresh assignment queries for immediate reflection - NO CACHING

References:
- [Source: architecture/voice-briefing.md#Role-Based Access Control]
- [Source: prd/prd-functional-requirements.md#FR15]
"""

import logging
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from supabase import create_client, Client

from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.user import CurrentUser, CurrentUserWithRole, UserRole, UserPreferences

logger = logging.getLogger(__name__)


# Supabase client (lazy initialization)
_supabase_client: Optional[Client] = None


def _get_supabase_client() -> Client:
    """
    Get or create Supabase client for database queries.

    Uses service_role key for bypassing RLS when needed.
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not configured",
            )
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
    return _supabase_client


async def get_user_role(user_id: str) -> UserRole:
    """
    Query user_roles table for user's organizational role.

    Args:
        user_id: User ID to look up

    Returns:
        UserRole enum value (defaults to SUPERVISOR if not found)
    """
    try:
        client = _get_supabase_client()
        result = client.table("user_roles").select("role").eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            role_str = result.data[0].get("role", "supervisor")
            try:
                return UserRole(role_str)
            except ValueError:
                logger.warning(f"Unknown role '{role_str}' for user {user_id}, defaulting to supervisor")
                return UserRole.SUPERVISOR

        # Default to supervisor if no role found
        logger.info(f"No role found for user {user_id}, defaulting to supervisor")
        return UserRole.SUPERVISOR

    except Exception as e:
        logger.error(f"Error querying user role for {user_id}: {e}")
        # Default to supervisor on error (principle of least privilege for briefing scope)
        return UserRole.SUPERVISOR


async def get_supervisor_assignments(user_id: str) -> List[str]:
    """
    Query supervisor_assignments table for user's assigned assets.

    IMPORTANT: No caching - always query fresh for immediate assignment changes (AC#4).

    Args:
        user_id: User ID to look up assignments for

    Returns:
        List of asset IDs assigned to the user
    """
    try:
        client = _get_supabase_client()
        result = (
            client.table("supervisor_assignments")
            .select("asset_id")
            .eq("user_id", user_id)
            .execute()
        )

        if result.data:
            return [row["asset_id"] for row in result.data]

        return []

    except Exception as e:
        logger.error(f"Error querying supervisor assignments for {user_id}: {e}")
        # Return empty list on error - supervisor will see "no assets assigned" message
        return []


async def get_user_preferences(user_id: str) -> Optional[UserPreferences]:
    """
    Query user_preferences table for user's briefing preferences.

    Args:
        user_id: User ID to look up preferences for

    Returns:
        UserPreferences if found, None otherwise
    """
    try:
        client = _get_supabase_client()
        result = (
            client.table("user_preferences")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if result.data and len(result.data) > 0:
            data = result.data[0]
            return UserPreferences(
                user_id=data.get("user_id", user_id),
                role=data.get("role"),
                area_order=data.get("area_order") or [],
                detail_level=data.get("detail_level", "detailed"),
                voice_enabled=data.get("voice_enabled", True),
            )

        return None

    except Exception as e:
        logger.error(f"Error querying user preferences for {user_id}: {e}")
        return None


async def get_current_user_with_role(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUserWithRole:
    """
    FastAPI dependency that provides user with role context.

    Extends the base JWT user with organizational role and assigned assets.
    Used by briefing services to scope content appropriately.

    AC#1: Provides role context for briefing scoping (FR15)
    AC#4: Fresh queries for supervisor_assignments - NO CACHING

    Usage:
    ```python
    @router.get("/briefing")
    async def get_briefing(user: CurrentUserWithRole = Depends(get_current_user_with_role)):
        if user.is_supervisor:
            # Scope to assigned assets
            assets = user.assigned_asset_ids
        else:
            # Plant manager sees all
            pass
    ```

    Args:
        current_user: Authenticated user from JWT

    Returns:
        CurrentUserWithRole with role and assignments populated
    """
    # Query role from user_roles table
    user_role = await get_user_role(current_user.id)

    # For supervisors, query fresh assignments (no caching per AC#4)
    assigned_asset_ids: List[str] = []
    if user_role == UserRole.SUPERVISOR:
        assigned_asset_ids = await get_supervisor_assignments(current_user.id)

    return CurrentUserWithRole(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        user_role=user_role,
        assigned_asset_ids=assigned_asset_ids,
    )


async def get_current_user_with_preferences(
    current_user: CurrentUser = Depends(get_current_user),
) -> tuple[CurrentUserWithRole, Optional[UserPreferences]]:
    """
    FastAPI dependency that provides user with role context AND preferences.

    Useful for briefing endpoints that need both role scoping and preferences.

    Returns:
        Tuple of (CurrentUserWithRole, UserPreferences or None)
    """
    # Get user with role
    user_with_role = await get_current_user_with_role(current_user)

    # Get preferences
    preferences = await get_user_preferences(current_user.id)

    return user_with_role, preferences


async def require_plant_manager_or_admin(
    current_user: CurrentUserWithRole = Depends(get_current_user_with_role),
) -> CurrentUserWithRole:
    """
    FastAPI dependency that requires plant_manager or admin role.

    Used for endpoints that should only be accessible to managers and admins.

    Args:
        current_user: User with role context

    Returns:
        CurrentUserWithRole if authorized

    Raises:
        HTTPException: If user is not a plant manager or admin
    """
    if current_user.user_role not in (UserRole.PLANT_MANAGER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Plant manager or admin access required",
        )
    return current_user


async def require_admin(
    current_user: CurrentUserWithRole = Depends(get_current_user_with_role),
) -> CurrentUserWithRole:
    """
    FastAPI dependency that requires admin role.

    Used for admin management endpoints.

    Args:
        current_user: User with role context

    Returns:
        CurrentUserWithRole if authorized

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
