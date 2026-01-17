"""
Preference Service (Story 8.9)

Provides CRUD operations for user preferences stored in Supabase.
This is the primary storage layer - Mem0 sync is handled separately.

AC#1: Preferences written to user_preferences table immediately
AC#3: Supabase record updated immediately on area order changes

References:
- [Source: architecture/voice-briefing.md#User Preferences Architecture]
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from supabase import Client, create_client

from app.core.config import get_settings
from app.models.preferences import (
    UserPreferencesResponse,
    CreateUserPreferencesRequest,
    UpdateUserPreferencesRequest,
    DEFAULT_AREA_ORDER,
    UserRoleEnum,
    DetailLevelEnum,
)

logger = logging.getLogger(__name__)


# Default preferences when no record exists
DEFAULT_PREFERENCES = {
    "role": "plant_manager",
    "area_order": DEFAULT_AREA_ORDER.copy(),
    "detail_level": "summary",
    "voice_enabled": True,
    "onboarding_complete": False,
}


class PreferenceServiceError(Exception):
    """Base exception for Preference Service errors."""
    pass


class PreferenceService:
    """
    Service for managing user preferences in Supabase.

    Provides CRUD operations with:
    - get_preferences: Returns defaults if not found
    - save_preferences: Upsert pattern
    - update_preferences: Partial updates
    """

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the Preference Service.

        Args:
            supabase_client: Optional Supabase client (for testing)
        """
        self._client = supabase_client
        self._settings = None

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def _get_client(self) -> Client:
        """Get Supabase client, creating if necessary."""
        if self._client is not None:
            return self._client

        settings = self._get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            raise PreferenceServiceError("Supabase not configured")

        self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    def _format_response(self, data: Dict[str, Any], user_id: str) -> UserPreferencesResponse:
        """Format database row to response schema."""
        return UserPreferencesResponse(
            user_id=user_id,
            role=data.get("role", DEFAULT_PREFERENCES["role"]),
            area_order=data.get("area_order") or DEFAULT_PREFERENCES["area_order"],
            detail_level=data.get("detail_level", DEFAULT_PREFERENCES["detail_level"]),
            voice_enabled=data.get("voice_enabled", DEFAULT_PREFERENCES["voice_enabled"]),
            onboarding_complete=data.get("onboarding_complete", DEFAULT_PREFERENCES["onboarding_complete"]),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )

    async def get_preferences(self, user_id: str) -> UserPreferencesResponse:
        """
        Get user preferences, returning defaults if not found.

        AC#1: Preferences are queryable from Supabase

        Args:
            user_id: User identifier

        Returns:
            UserPreferencesResponse with user preferences (or defaults)
        """
        logger.debug(f"Getting preferences for user {user_id}")

        try:
            client = self._get_client()
            result = client.table("user_preferences").select("*").eq(
                "user_id", user_id
            ).maybe_single().execute()

            if not result.data:
                logger.info(f"No preferences found for user {user_id}, returning defaults")
                return UserPreferencesResponse(
                    user_id=user_id,
                    role=DEFAULT_PREFERENCES["role"],
                    area_order=DEFAULT_PREFERENCES["area_order"],
                    detail_level=DEFAULT_PREFERENCES["detail_level"],
                    voice_enabled=DEFAULT_PREFERENCES["voice_enabled"],
                    onboarding_complete=DEFAULT_PREFERENCES["onboarding_complete"],
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )

            return self._format_response(result.data, user_id)

        except PreferenceServiceError:
            raise
        except Exception as e:
            logger.error(f"Error fetching preferences for user {user_id}: {e}")
            raise PreferenceServiceError(f"Failed to fetch preferences: {e}")

    async def save_preferences(
        self,
        user_id: str,
        preferences: CreateUserPreferencesRequest,
    ) -> UserPreferencesResponse:
        """
        Save user preferences using upsert pattern.

        AC#1: Preferences written to user_preferences table immediately

        Args:
            user_id: User identifier
            preferences: Full preferences to save

        Returns:
            UserPreferencesResponse with saved preferences
        """
        logger.info(f"Saving preferences for user {user_id}")

        try:
            client = self._get_client()
            now = datetime.now(timezone.utc).isoformat()

            # Check if record exists
            existing = client.table("user_preferences").select("user_id").eq(
                "user_id", user_id
            ).maybe_single().execute()

            data = {
                "role": preferences.role.value,
                "area_order": preferences.area_order,
                "detail_level": preferences.detail_level.value,
                "voice_enabled": preferences.voice_enabled,
                "onboarding_complete": preferences.onboarding_complete,
                "updated_at": now,
            }

            if existing.data:
                # Update existing
                result = client.table("user_preferences").update(data).eq(
                    "user_id", user_id
                ).execute()
            else:
                # Insert new
                data["user_id"] = user_id
                data["created_at"] = now
                result = client.table("user_preferences").insert(data).execute()

            if not result.data:
                raise PreferenceServiceError("Failed to save preferences")

            return self._format_response(result.data[0], user_id)

        except PreferenceServiceError:
            raise
        except Exception as e:
            logger.error(f"Error saving preferences for user {user_id}: {e}")
            raise PreferenceServiceError(f"Failed to save preferences: {e}")

    async def update_preferences(
        self,
        user_id: str,
        updates: UpdateUserPreferencesRequest,
    ) -> UserPreferencesResponse:
        """
        Partially update user preferences.

        AC#3: Supabase record updated immediately on changes

        Args:
            user_id: User identifier
            updates: Partial updates to apply

        Returns:
            UserPreferencesResponse with updated preferences

        Raises:
            PreferenceServiceError: If preferences don't exist
        """
        logger.info(f"Updating preferences for user {user_id}")

        try:
            client = self._get_client()

            # Check if preferences exist
            existing = client.table("user_preferences").select("*").eq(
                "user_id", user_id
            ).maybe_single().execute()

            if not existing.data:
                raise PreferenceServiceError(
                    "Preferences not found. Please complete onboarding first."
                )

            # Build update data from non-None fields
            update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

            if updates.role is not None:
                update_data["role"] = updates.role.value
            if updates.area_order is not None:
                update_data["area_order"] = updates.area_order
            if updates.detail_level is not None:
                update_data["detail_level"] = updates.detail_level.value
            if updates.voice_enabled is not None:
                update_data["voice_enabled"] = updates.voice_enabled

            result = client.table("user_preferences").update(update_data).eq(
                "user_id", user_id
            ).execute()

            if not result.data:
                raise PreferenceServiceError("Failed to update preferences")

            return self._format_response(result.data[0], user_id)

        except PreferenceServiceError:
            raise
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            raise PreferenceServiceError(f"Failed to update preferences: {e}")

    async def preferences_exist(self, user_id: str) -> bool:
        """
        Check if preferences exist for a user.

        Args:
            user_id: User identifier

        Returns:
            True if preferences exist, False otherwise
        """
        try:
            client = self._get_client()
            result = client.table("user_preferences").select("user_id").eq(
                "user_id", user_id
            ).maybe_single().execute()
            return result.data is not None
        except Exception as e:
            logger.error(f"Error checking preferences existence for user {user_id}: {e}")
            return False


# Module-level singleton instance
_preference_service: Optional[PreferenceService] = None


def get_preference_service() -> PreferenceService:
    """
    Get the singleton PreferenceService instance.

    Returns:
        PreferenceService singleton instance
    """
    global _preference_service
    if _preference_service is None:
        _preference_service = PreferenceService()
    return _preference_service
