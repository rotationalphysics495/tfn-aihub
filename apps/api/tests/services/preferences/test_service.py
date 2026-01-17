"""
Tests for Preference Service (Story 8.9)

AC#1: Preferences written to user_preferences table immediately
AC#3: Supabase record updated immediately on changes

Tests CRUD operations with Supabase mocked.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.services.preferences.service import (
    PreferenceService,
    PreferenceServiceError,
    get_preference_service,
    DEFAULT_PREFERENCES,
)
from app.models.preferences import (
    CreateUserPreferencesRequest,
    UpdateUserPreferencesRequest,
    UserPreferencesResponse,
    UserRoleEnum,
    DetailLevelEnum,
    DEFAULT_AREA_ORDER,
)


@pytest.fixture
def preference_svc():
    """Create a fresh PreferenceService instance for testing."""
    mock_client = MagicMock()
    svc = PreferenceService(supabase_client=mock_client)
    return svc, mock_client


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return str(uuid4())


@pytest.fixture
def sample_preferences_data():
    """Sample preferences data from database."""
    return {
        "user_id": "test-user-123",
        "role": "plant_manager",
        "area_order": ["Grinding", "Packing", "Roasting"],
        "detail_level": "summary",
        "voice_enabled": True,
        "onboarding_complete": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_create_request():
    """Sample create preferences request."""
    return CreateUserPreferencesRequest(
        role=UserRoleEnum.PLANT_MANAGER,
        area_order=["Grinding", "Packing", "Roasting"],
        detail_level=DetailLevelEnum.SUMMARY,
        voice_enabled=True,
        onboarding_complete=True,
    )


@pytest.fixture
def sample_update_request():
    """Sample update preferences request."""
    return UpdateUserPreferencesRequest(
        area_order=["Packing", "Grinding", "Roasting"],
    )


class TestPreferenceServiceExists:
    """Tests for service instantiation."""

    def test_preference_service_can_be_instantiated(self):
        """PreferenceService class can be created."""
        svc = PreferenceService()
        assert svc is not None

    def test_get_preference_service_returns_singleton(self):
        """get_preference_service returns singleton instance."""
        # Reset the singleton for this test
        import app.services.preferences.service as svc_module
        svc_module._preference_service = None

        svc1 = get_preference_service()
        svc2 = get_preference_service()
        assert svc1 is svc2


class TestGetPreferences:
    """Tests for AC#1 - get_preferences returns defaults if not found."""

    @pytest.mark.asyncio
    async def test_get_preferences_returns_data_when_exists(
        self, preference_svc, sample_user_id, sample_preferences_data
    ):
        """AC#1: Get preferences returns stored data."""
        svc, mock_client = preference_svc

        # Mock database response
        mock_result = MagicMock()
        mock_result.data = sample_preferences_data
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        result = await svc.get_preferences(sample_user_id)

        assert result is not None
        assert result.role == sample_preferences_data["role"]
        assert result.area_order == sample_preferences_data["area_order"]
        assert result.detail_level == sample_preferences_data["detail_level"]
        assert result.voice_enabled == sample_preferences_data["voice_enabled"]

    @pytest.mark.asyncio
    async def test_get_preferences_returns_defaults_when_not_found(
        self, preference_svc, sample_user_id
    ):
        """AC#1: Get preferences returns defaults when no record exists."""
        svc, mock_client = preference_svc

        # Mock empty database response
        mock_result = MagicMock()
        mock_result.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        result = await svc.get_preferences(sample_user_id)

        assert result is not None
        assert result.role == DEFAULT_PREFERENCES["role"]
        assert result.area_order == DEFAULT_PREFERENCES["area_order"]
        assert result.detail_level == DEFAULT_PREFERENCES["detail_level"]
        assert result.voice_enabled == DEFAULT_PREFERENCES["voice_enabled"]
        assert result.onboarding_complete == DEFAULT_PREFERENCES["onboarding_complete"]

    @pytest.mark.asyncio
    async def test_get_preferences_handles_database_error(
        self, preference_svc, sample_user_id
    ):
        """Error handling: get_preferences raises on database error."""
        svc, mock_client = preference_svc

        # Mock database error
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = Exception("DB Error")

        with pytest.raises(PreferenceServiceError) as exc_info:
            await svc.get_preferences(sample_user_id)

        assert "Failed to fetch preferences" in str(exc_info.value)


class TestSavePreferences:
    """Tests for AC#1 - save_preferences upsert pattern."""

    @pytest.mark.asyncio
    async def test_save_preferences_inserts_when_new(
        self, preference_svc, sample_user_id, sample_create_request, sample_preferences_data
    ):
        """AC#1: Save preferences creates new record."""
        svc, mock_client = preference_svc

        # Mock no existing record
        mock_existing = MagicMock()
        mock_existing.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock insert response
        mock_insert = MagicMock()
        mock_insert.data = [sample_preferences_data]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert

        result = await svc.save_preferences(sample_user_id, sample_create_request)

        assert result is not None
        mock_client.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_preferences_updates_when_exists(
        self, preference_svc, sample_user_id, sample_create_request, sample_preferences_data
    ):
        """AC#1: Save preferences updates existing record."""
        svc, mock_client = preference_svc

        # Mock existing record
        mock_existing = MagicMock()
        mock_existing.data = {"user_id": sample_user_id}
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock update response
        mock_update = MagicMock()
        mock_update.data = [sample_preferences_data]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        result = await svc.save_preferences(sample_user_id, sample_create_request)

        assert result is not None
        mock_client.table.return_value.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_preferences_handles_failure(
        self, preference_svc, sample_user_id, sample_create_request
    ):
        """Error handling: save_preferences raises on insert failure."""
        svc, mock_client = preference_svc

        # Mock no existing record
        mock_existing = MagicMock()
        mock_existing.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock failed insert
        mock_insert = MagicMock()
        mock_insert.data = None
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert

        with pytest.raises(PreferenceServiceError) as exc_info:
            await svc.save_preferences(sample_user_id, sample_create_request)

        assert "Failed to save preferences" in str(exc_info.value)


class TestUpdatePreferences:
    """Tests for AC#3 - update_preferences partial updates."""

    @pytest.mark.asyncio
    async def test_update_preferences_merges_fields(
        self, preference_svc, sample_user_id, sample_update_request, sample_preferences_data
    ):
        """AC#3: Update preferences merges partial updates."""
        svc, mock_client = preference_svc

        # Mock existing record
        mock_existing = MagicMock()
        mock_existing.data = sample_preferences_data
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock update response
        updated_data = sample_preferences_data.copy()
        updated_data["area_order"] = sample_update_request.area_order
        mock_update = MagicMock()
        mock_update.data = [updated_data]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        result = await svc.update_preferences(sample_user_id, sample_update_request)

        assert result is not None
        assert result.area_order == sample_update_request.area_order

    @pytest.mark.asyncio
    async def test_update_preferences_fails_when_not_found(
        self, preference_svc, sample_user_id, sample_update_request
    ):
        """AC#3: Update preferences fails if record doesn't exist."""
        svc, mock_client = preference_svc

        # Mock no existing record
        mock_existing = MagicMock()
        mock_existing.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        with pytest.raises(PreferenceServiceError) as exc_info:
            await svc.update_preferences(sample_user_id, sample_update_request)

        assert "Preferences not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_preferences_only_updates_provided_fields(
        self, preference_svc, sample_user_id, sample_preferences_data
    ):
        """AC#3: Update only touches provided fields."""
        svc, mock_client = preference_svc

        # Mock existing record
        mock_existing = MagicMock()
        mock_existing.data = sample_preferences_data
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_existing

        # Mock update response
        mock_update = MagicMock()
        mock_update.data = [sample_preferences_data]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        # Only update voice_enabled
        update_request = UpdateUserPreferencesRequest(voice_enabled=False)
        await svc.update_preferences(sample_user_id, update_request)

        # Verify update was called with only voice_enabled (and updated_at)
        call_args = mock_client.table.return_value.update.call_args[0][0]
        assert "voice_enabled" in call_args
        assert call_args["voice_enabled"] is False
        assert "updated_at" in call_args
        # Role should NOT be in update since it wasn't provided
        assert "role" not in call_args


class TestPreferencesExist:
    """Tests for preferences_exist helper."""

    @pytest.mark.asyncio
    async def test_preferences_exist_returns_true_when_found(
        self, preference_svc, sample_user_id
    ):
        """preferences_exist returns True when record exists."""
        svc, mock_client = preference_svc

        mock_result = MagicMock()
        mock_result.data = {"user_id": sample_user_id}
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        result = await svc.preferences_exist(sample_user_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_preferences_exist_returns_false_when_not_found(
        self, preference_svc, sample_user_id
    ):
        """preferences_exist returns False when record doesn't exist."""
        svc, mock_client = preference_svc

        mock_result = MagicMock()
        mock_result.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        result = await svc.preferences_exist(sample_user_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_preferences_exist_returns_false_on_error(
        self, preference_svc, sample_user_id
    ):
        """preferences_exist returns False on error (graceful degradation)."""
        svc, mock_client = preference_svc

        mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = Exception("Error")

        result = await svc.preferences_exist(sample_user_id)
        assert result is False
