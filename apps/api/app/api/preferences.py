"""
User Preferences API Endpoints (Story 8.8, 8.9)

REST endpoints for user preferences management with Mem0 sync.

Story 8.8:
AC#3: GET /api/v1/preferences - Get current user preferences
      POST /api/v1/preferences - Create preferences (onboarding)
AC#5: PUT /api/v1/preferences - Update preferences (settings page)

Story 8.9:
AC#1: Preferences written to user_preferences table immediately, synced to Mem0 within 5 seconds
AC#3: Supabase record updated immediately, Mem0 context reflects change
AC#5: Mem0 sync failures don't block Supabase saves (graceful degradation)

References:
- [Source: architecture/voice-briefing.md#User Preferences Architecture]
- [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from supabase import Client, create_client

from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import CurrentUser
from app.models.preferences import (
    CreateUserPreferencesRequest,
    UpdateUserPreferencesRequest,
    UserPreferencesResponse,
    DEFAULT_AREA_ORDER,
)
from app.services.preferences.sync import sync_preferences_to_mem0

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_supabase_client() -> Client:
    """Get Supabase client for database operations."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase not configured",
        )
    return create_client(settings.supabase_url, settings.supabase_key)


def _format_preferences_response(data: dict, user_id: str) -> UserPreferencesResponse:
    """Format database row to response schema."""
    return UserPreferencesResponse(
        user_id=user_id,
        role=data.get("role", "plant_manager"),
        area_order=data.get("area_order") or DEFAULT_AREA_ORDER,
        detail_level=data.get("detail_level", "summary"),
        voice_enabled=data.get("voice_enabled", True),
        onboarding_complete=data.get("onboarding_complete", False),
        updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
    )


@router.get("", response_model=UserPreferencesResponse)
async def get_preferences(
    current_user: CurrentUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Get current user's preferences.

    Returns 404 if no preferences exist (triggers onboarding).
    """
    logger.info(f"Getting preferences for user {current_user.id}")

    try:
        result = supabase.table("user_preferences").select("*").eq(
            "user_id", current_user.id
        ).maybe_single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found. Please complete onboarding.",
            )

        return _format_preferences_response(result.data, current_user.id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch preferences",
        )


@router.post("", response_model=UserPreferencesResponse, status_code=status.HTTP_201_CREATED)
async def create_preferences(
    request: CreateUserPreferencesRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Create user preferences (onboarding completion).

    Story 8.8 AC#3: Store preferences in user_preferences table.
    Story 8.9 AC#1: Sync to Mem0 within 5 seconds via background task.
    Story 8.9 AC#5: Mem0 failures don't block Supabase saves.
    """
    logger.info(f"Creating preferences for user {current_user.id}")

    try:
        # Check if preferences already exist
        existing = supabase.table("user_preferences").select("user_id").eq(
            "user_id", current_user.id
        ).maybe_single().execute()

        if existing.data:
            # Update existing preferences instead of creating new
            update_data = {
                "role": request.role.value,
                "area_order": request.area_order,
                "detail_level": request.detail_level.value,
                "voice_enabled": request.voice_enabled,
                "onboarding_complete": request.onboarding_complete,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            result = supabase.table("user_preferences").update(
                update_data
            ).eq("user_id", current_user.id).execute()

            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update preferences",
                )

            response = _format_preferences_response(result.data[0], current_user.id)

            # Story 8.9: Fire-and-forget Mem0 sync (AC#1, AC#5)
            background_tasks.add_task(
                sync_preferences_to_mem0,
                current_user.id,
                response,
                "Preferences updated via onboarding re-submission",
            )

            return response

        # Create new preferences
        insert_data = {
            "user_id": current_user.id,
            "role": request.role.value,
            "area_order": request.area_order,
            "detail_level": request.detail_level.value,
            "voice_enabled": request.voice_enabled,
            "onboarding_complete": request.onboarding_complete,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = supabase.table("user_preferences").insert(insert_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create preferences",
            )

        response = _format_preferences_response(result.data[0], current_user.id)

        # Story 8.9: Fire-and-forget Mem0 sync (AC#1, AC#5)
        background_tasks.add_task(
            sync_preferences_to_mem0,
            current_user.id,
            response,
            "Initial preferences set during onboarding",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create preferences",
        )


@router.put("", response_model=UserPreferencesResponse)
async def update_preferences(
    request: UpdateUserPreferencesRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Update existing user preferences (settings page).

    Story 8.8 AC#5: All onboarding options available to edit.
    Story 8.9 AC#3: Supabase updated immediately, Mem0 reflects change.
    Story 8.9 AC#5: Mem0 failures don't block Supabase saves.
    """
    logger.info(f"Updating preferences for user {current_user.id}")

    try:
        # Check if preferences exist
        existing = supabase.table("user_preferences").select("*").eq(
            "user_id", current_user.id
        ).maybe_single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found. Please complete onboarding first.",
            )

        # Build update data from non-None fields
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if request.role is not None:
            update_data["role"] = request.role.value
        if request.area_order is not None:
            update_data["area_order"] = request.area_order
        if request.detail_level is not None:
            update_data["detail_level"] = request.detail_level.value
        if request.voice_enabled is not None:
            update_data["voice_enabled"] = request.voice_enabled

        result = supabase.table("user_preferences").update(
            update_data
        ).eq("user_id", current_user.id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences",
            )

        response = _format_preferences_response(result.data[0], current_user.id)

        # Story 8.9: Fire-and-forget Mem0 sync (AC#3, AC#5)
        background_tasks.add_task(
            sync_preferences_to_mem0,
            current_user.id,
            response,
            "Preferences updated via settings page",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences",
        )


@router.patch("", response_model=UserPreferencesResponse)
async def patch_preferences(
    request: UpdateUserPreferencesRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Partially update user preferences (Story 8.9).

    Story 8.9 AC#3: Supabase updated immediately, Mem0 reflects change.
    Story 8.9 AC#5: Mem0 failures don't block Supabase saves.

    This endpoint is an alias for PUT with the same behavior,
    allowing semantic PATCH requests for partial updates.
    """
    return await update_preferences(request, background_tasks, current_user, supabase)
