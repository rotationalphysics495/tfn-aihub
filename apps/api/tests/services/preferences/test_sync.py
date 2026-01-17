"""
Tests for Preference Mem0 Sync Service (Story 8.9)

AC#2: Mem0 context includes semantic descriptions
AC#4: Sync includes semantic context with version history
AC#5: Graceful degradation when Mem0 unavailable

Tests semantic formatting and retry logic.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.services.preferences.sync import (
    sync_preferences_to_mem0,
    format_preferences_for_mem0,
    get_preference_context_from_mem0,
    _sync_with_retry,
    MAX_RETRIES,
)
from app.models.preferences import (
    UserPreferencesResponse,
    Mem0PreferenceContext,
    UserRoleEnum,
    DetailLevelEnum,
    DEFAULT_AREA_ORDER,
)
from app.services.memory.mem0_service import MemoryServiceError


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return str(uuid4())


@pytest.fixture
def sample_preferences():
    """Sample user preferences for testing."""
    return UserPreferencesResponse(
        user_id="test-user-123",
        role=UserRoleEnum.PLANT_MANAGER,
        area_order=["Grinding", "Packing", "Roasting"],
        detail_level=DetailLevelEnum.SUMMARY,
        voice_enabled=True,
        onboarding_complete=True,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


@pytest.fixture
def sample_supervisor_preferences():
    """Sample supervisor preferences for testing."""
    return UserPreferencesResponse(
        user_id="test-supervisor-123",
        role=UserRoleEnum.SUPERVISOR,
        area_order=["Packing", "Grinding"],
        detail_level=DetailLevelEnum.DETAILED,
        voice_enabled=False,
        onboarding_complete=True,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


@pytest.fixture
def mock_memory_service():
    """Mock memory service for testing."""
    with patch('app.services.preferences.sync.get_memory_service') as mock_get:
        mock_service = MagicMock()
        mock_service.is_configured.return_value = True
        mock_service.add_memory = AsyncMock(return_value={"id": "mem-123", "status": "stored"})
        mock_service.search_memory = AsyncMock(return_value=[])
        mock_get.return_value = mock_service
        yield mock_service


class TestSemanticFormatting:
    """Tests for AC#2 - semantic descriptions formatting."""

    def test_format_plant_manager_role(self, sample_preferences):
        """AC#2: Plant manager role converted to semantic description."""
        result = format_preferences_for_mem0(sample_preferences)

        assert "Plant Manager" in result
        assert "full visibility" in result

    def test_format_supervisor_role(self, sample_supervisor_preferences):
        """AC#2: Supervisor role converted to semantic description."""
        result = format_preferences_for_mem0(sample_supervisor_preferences)

        assert "Supervisor" in result
        assert "scoped access" in result

    def test_format_area_order(self, sample_preferences):
        """AC#2: Area order converted to natural language."""
        result = format_preferences_for_mem0(sample_preferences)

        assert "Grinding first" in result
        assert "briefings" in result

    def test_format_summary_detail_level(self, sample_preferences):
        """AC#2: Summary detail level converted correctly."""
        result = format_preferences_for_mem0(sample_preferences)

        assert "concise summary" in result

    def test_format_detailed_detail_level(self, sample_supervisor_preferences):
        """AC#2: Detailed level converted correctly."""
        result = format_preferences_for_mem0(sample_supervisor_preferences)

        assert "detailed" in result.lower()
        assert "comprehensive" in result

    def test_format_voice_enabled(self, sample_preferences):
        """AC#2: Voice enabled preference converted correctly."""
        result = format_preferences_for_mem0(sample_preferences)

        assert "voice delivery" in result

    def test_format_voice_disabled(self, sample_supervisor_preferences):
        """AC#2: Voice disabled preference converted correctly."""
        result = format_preferences_for_mem0(sample_supervisor_preferences)

        assert "text-only" in result

    def test_format_includes_reason_when_provided(self, sample_preferences):
        """AC#4: Reason/context included when provided."""
        reason = "User prefers grinding first because that's where most issues occur"
        result = format_preferences_for_mem0(sample_preferences, reason=reason)

        assert "Context:" in result
        assert reason in result

    def test_format_includes_timestamp(self, sample_preferences):
        """AC#4: Timestamp included in formatted context."""
        result = format_preferences_for_mem0(sample_preferences)

        assert "updated at" in result.lower()


class TestMem0PreferenceContextModel:
    """Tests for Mem0PreferenceContext Pydantic model."""

    def test_from_preferences_creates_semantic_descriptions(self, sample_preferences):
        """Mem0PreferenceContext.from_preferences generates descriptions."""
        context = Mem0PreferenceContext.from_preferences(sample_preferences)

        assert len(context.semantic_descriptions) > 0
        assert context.metadata is not None
        assert "user_id" in context.metadata
        assert "timestamp" in context.metadata

    def test_from_preferences_includes_reason(self, sample_preferences):
        """Mem0PreferenceContext.from_preferences includes reason."""
        reason = "Test reason"
        context = Mem0PreferenceContext.from_preferences(sample_preferences, reason=reason)

        assert context.preference_reason == reason

    def test_from_preferences_version_metadata(self, sample_preferences):
        """AC#4: Version history metadata included."""
        context = Mem0PreferenceContext.from_preferences(sample_preferences)

        assert "preference_version" in context.metadata
        assert context.metadata["preference_version"] == sample_preferences.updated_at


class TestSyncToMem0:
    """Tests for AC#5 - sync with retry and graceful degradation."""

    @pytest.mark.asyncio
    async def test_sync_succeeds_with_configured_service(
        self, sample_user_id, sample_preferences, mock_memory_service
    ):
        """AC#1: Sync succeeds when Mem0 is configured."""
        result = await sync_preferences_to_mem0(
            sample_user_id, sample_preferences
        )

        assert result is True
        mock_memory_service.add_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_returns_false_when_not_configured(
        self, sample_user_id, sample_preferences
    ):
        """AC#5: Graceful degradation when Mem0 not configured."""
        with patch('app.services.preferences.sync.get_memory_service') as mock_get:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = False
            mock_get.return_value = mock_service

            result = await sync_preferences_to_mem0(
                sample_user_id, sample_preferences
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_sync_includes_metadata(
        self, sample_user_id, sample_preferences, mock_memory_service
    ):
        """AC#4: Sync includes metadata for version history."""
        await sync_preferences_to_mem0(sample_user_id, sample_preferences)

        call_kwargs = mock_memory_service.add_memory.call_args[1]
        metadata = call_kwargs["metadata"]

        assert "preference_type" in metadata
        assert metadata["preference_type"] == "user_preferences"
        assert "preference_version" in metadata
        assert "timestamp" in metadata

    @pytest.mark.asyncio
    async def test_sync_includes_reason_in_context(
        self, sample_user_id, sample_preferences, mock_memory_service
    ):
        """AC#4: Sync includes reason context when provided."""
        reason = "Initial setup during onboarding"
        await sync_preferences_to_mem0(
            sample_user_id, sample_preferences, reason=reason
        )

        call_kwargs = mock_memory_service.add_memory.call_args[1]
        messages = call_kwargs["messages"]

        # Check that the reason appears in the content
        assert len(messages) > 0
        assert reason in messages[0]["content"]


class TestRetryLogic:
    """Tests for AC#5 - retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self, sample_user_id):
        """AC#5: Retry succeeds after initial failure."""
        mock_service = MagicMock()
        mock_service.add_memory = AsyncMock(
            side_effect=[MemoryServiceError("First fail"), {"id": "mem-123"}]
        )

        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await _sync_with_retry(
                memory_service=mock_service,
                user_id=sample_user_id,
                semantic_context="Test context",
                metadata={"test": True},
                max_retries=3,
            )

        assert result is True
        assert mock_service.add_memory.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self, sample_user_id):
        """AC#5: Returns False after max retries exhausted."""
        mock_service = MagicMock()
        mock_service.add_memory = AsyncMock(
            side_effect=MemoryServiceError("Always fail")
        )

        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await _sync_with_retry(
                memory_service=mock_service,
                user_id=sample_user_id,
                semantic_context="Test context",
                metadata={"test": True},
                max_retries=2,
            )

        assert result is False
        # Initial attempt + 2 retries = 3 total calls
        assert mock_service.add_memory.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_uses_exponential_backoff(self, sample_user_id):
        """AC#5: Exponential backoff: 1s, 2s, 4s."""
        mock_service = MagicMock()
        mock_service.add_memory = AsyncMock(
            side_effect=[
                MemoryServiceError("Fail 1"),
                MemoryServiceError("Fail 2"),
                MemoryServiceError("Fail 3"),
                {"id": "success"},
            ]
        )

        sleep_times = []

        async def mock_sleep(duration):
            sleep_times.append(duration)

        with patch('asyncio.sleep', side_effect=mock_sleep):
            await _sync_with_retry(
                memory_service=mock_service,
                user_id=sample_user_id,
                semantic_context="Test context",
                metadata={"test": True},
                max_retries=3,
            )

        # Verify exponential backoff pattern
        assert len(sleep_times) >= 2
        assert sleep_times[0] == 1.0  # First retry: 1s
        assert sleep_times[1] == 2.0  # Second retry: 2s


class TestGracefulDegradation:
    """Tests for AC#5 - graceful degradation."""

    @pytest.mark.asyncio
    async def test_sync_handles_unexpected_exception(
        self, sample_user_id, sample_preferences
    ):
        """AC#5: Sync returns False on unexpected exceptions."""
        with patch('app.services.preferences.sync.get_memory_service') as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            result = await sync_preferences_to_mem0(
                sample_user_id, sample_preferences
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_sync_does_not_raise_on_failure(
        self, sample_user_id, sample_preferences
    ):
        """AC#5: Sync never raises, always returns bool."""
        with patch('app.services.preferences.sync.get_memory_service') as mock_get:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.add_memory = AsyncMock(side_effect=Exception("Fatal error"))
            mock_get.return_value = mock_service

            # Should not raise
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await sync_preferences_to_mem0(
                    sample_user_id, sample_preferences
                )

            assert result is False


class TestGetPreferenceContextFromMem0:
    """Tests for retrieving preference context from Mem0."""

    @pytest.mark.asyncio
    async def test_get_context_returns_empty_when_not_configured(
        self, sample_user_id
    ):
        """Returns empty list when Mem0 not configured."""
        with patch('app.services.preferences.sync.get_memory_service') as mock_get:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = False
            mock_get.return_value = mock_service

            result = await get_preference_context_from_mem0(sample_user_id)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_context_filters_to_preference_type(
        self, sample_user_id
    ):
        """Only returns memories with preference_type metadata."""
        with patch('app.services.preferences.sync.get_memory_service') as mock_get:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(return_value=[
                {"id": "mem-1", "metadata": {"preference_type": "user_preferences"}},
                {"id": "mem-2", "metadata": {"other_type": "something"}},
                {"id": "mem-3", "metadata": {"preference_type": "user_preferences"}},
            ])
            mock_get.return_value = mock_service

            result = await get_preference_context_from_mem0(sample_user_id)

            assert len(result) == 2
            assert all(
                m["metadata"].get("preference_type") == "user_preferences"
                for m in result
            )

    @pytest.mark.asyncio
    async def test_get_context_handles_error_gracefully(
        self, sample_user_id
    ):
        """Returns empty list on error."""
        with patch('app.services.preferences.sync.get_memory_service') as mock_get:
            mock_service = MagicMock()
            mock_service.is_configured.return_value = True
            mock_service.search_memory = AsyncMock(side_effect=Exception("Error"))
            mock_get.return_value = mock_service

            result = await get_preference_context_from_mem0(sample_user_id)

            assert result == []
