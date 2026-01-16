"""
TTS Service Tests (Story 8.1 Task 6.2)

Tests for the TTS service layer including:
- TTSService with mocked ElevenLabsClient
- Graceful degradation returns None (not exception)
- fallback_reason population

AC#1: TTS Stream URL Generation
AC#2: Graceful Degradation
AC#4: Voice Preference Handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.voice.tts import (
    TTSService,
    TTSServiceResult,
    UserVoicePreferences,
    get_tts_service,
    FALLBACK_MESSAGES,
)
from app.services.voice.elevenlabs import (
    ElevenLabsClient,
    FallbackReason,
    TTSResult,
)


class TestUserVoicePreferences:
    """Tests for UserVoicePreferences dataclass."""

    def test_default_preferences(self):
        """Test default preferences values."""
        prefs = UserVoicePreferences()

        assert prefs.voice_enabled is True
        assert prefs.preferred_voice_id is None
        assert prefs.playback_speed == 1.0
        assert prefs.auto_play is True
        assert prefs.pause_between_sections is True
        assert prefs.pause_duration_ms == 1500

    def test_custom_preferences(self):
        """Test custom preferences values."""
        prefs = UserVoicePreferences(
            voice_enabled=False,
            preferred_voice_id="custom-voice",
            playback_speed=1.5,
            auto_play=False,
        )

        assert prefs.voice_enabled is False
        assert prefs.preferred_voice_id == "custom-voice"
        assert prefs.playback_speed == 1.5
        assert prefs.auto_play is False


class TestTTSServiceResult:
    """Tests for TTSServiceResult dataclass."""

    def test_result_with_audio(self):
        """Test result with audio URL."""
        result = TTSServiceResult(
            audio_stream_url="/api/voice/tts/stream",
            duration_estimate_ms=5000,
            fallback_reason=FallbackReason.NONE,
            fallback_message=None,
            voice_enabled=True,
        )

        assert result.has_audio is True
        assert result.audio_stream_url is not None

    def test_result_without_audio_voice_disabled(self):
        """Test result when voice is disabled."""
        result = TTSServiceResult(
            audio_stream_url=None,
            duration_estimate_ms=None,
            fallback_reason=FallbackReason.VOICE_DISABLED,
            fallback_message=None,
            voice_enabled=False,
        )

        assert result.has_audio is False
        assert result.voice_enabled is False

    def test_result_without_audio_api_error(self):
        """Test result on API error."""
        result = TTSServiceResult(
            audio_stream_url=None,
            duration_estimate_ms=None,
            fallback_reason=FallbackReason.API_UNAVAILABLE,
            fallback_message="Voice temporarily unavailable - showing text",
            voice_enabled=True,
        )

        assert result.has_audio is False
        assert result.voice_enabled is True
        assert result.fallback_message is not None

    def test_to_dict(self):
        """Test to_dict method."""
        result = TTSServiceResult(
            audio_stream_url="/api/voice/tts/stream",
            duration_estimate_ms=5000,
            fallback_reason=FallbackReason.NONE,
            fallback_message=None,
            voice_enabled=True,
        )

        d = result.to_dict()

        assert d["audio_stream_url"] == "/api/voice/tts/stream"
        assert d["duration_estimate_ms"] == 5000
        assert d["fallback_reason"] == ""
        assert d["fallback_message"] is None
        assert d["voice_enabled"] is True
        assert d["has_audio"] is True


class TestTTSService:
    """Tests for TTSService."""

    @pytest.fixture
    def mock_elevenlabs_client(self):
        """Create a mock ElevenLabs client."""
        client = MagicMock(spec=ElevenLabsClient)
        client.is_configured = True
        return client

    @pytest.fixture
    def service(self, mock_elevenlabs_client):
        """Create a TTSService with mocked client."""
        return TTSService(elevenlabs_client=mock_elevenlabs_client)

    @pytest.mark.asyncio
    async def test_generate_stream_url_success(self, service, mock_elevenlabs_client):
        """Test successful stream URL generation (AC#1)."""
        # Setup mock
        mock_elevenlabs_client.get_tts_stream_url = AsyncMock(return_value=TTSResult(
            audio_stream_url="/api/voice/tts/stream",
            duration_estimate_ms=5000,
            fallback_reason=FallbackReason.NONE,
        ))

        result = await service.generate_stream_url("Hello world")

        assert result.has_audio is True
        assert result.audio_stream_url is not None
        assert result.fallback_reason == FallbackReason.NONE

    @pytest.mark.asyncio
    async def test_generate_stream_url_voice_disabled(self, service):
        """Test voice disabled preference (AC#4)."""
        prefs = UserVoicePreferences(voice_enabled=False)

        result = await service.generate_stream_url("Hello world", user_preferences=prefs)

        assert result.has_audio is False
        assert result.audio_stream_url is None
        assert result.fallback_reason == FallbackReason.VOICE_DISABLED
        assert result.voice_enabled is False
        # Voice disabled is not an error, so no fallback message
        assert result.fallback_message is None

    @pytest.mark.asyncio
    async def test_generate_stream_url_api_error(self, service, mock_elevenlabs_client):
        """Test graceful degradation on API error (AC#2)."""
        # Setup mock to return error
        mock_elevenlabs_client.get_tts_stream_url = AsyncMock(return_value=TTSResult(
            audio_stream_url=None,
            duration_estimate_ms=None,
            fallback_reason=FallbackReason.API_UNAVAILABLE,
            error_message="API error",
        ))

        result = await service.generate_stream_url("Hello world")

        # Should NOT raise exception
        assert result.has_audio is False
        assert result.audio_stream_url is None
        assert result.fallback_reason == FallbackReason.API_UNAVAILABLE
        assert result.fallback_message == FALLBACK_MESSAGES[FallbackReason.API_UNAVAILABLE]

    @pytest.mark.asyncio
    async def test_generate_stream_url_timeout(self, service, mock_elevenlabs_client):
        """Test graceful degradation on timeout (AC#2)."""
        mock_elevenlabs_client.get_tts_stream_url = AsyncMock(return_value=TTSResult(
            audio_stream_url=None,
            duration_estimate_ms=None,
            fallback_reason=FallbackReason.TIMEOUT,
            error_message="Timeout",
        ))

        result = await service.generate_stream_url("Hello world")

        assert result.has_audio is False
        assert result.fallback_reason == FallbackReason.TIMEOUT
        assert result.fallback_message == FALLBACK_MESSAGES[FallbackReason.TIMEOUT]

    @pytest.mark.asyncio
    async def test_generate_stream_url_uses_preferred_voice(self, service, mock_elevenlabs_client):
        """Test using user's preferred voice."""
        prefs = UserVoicePreferences(
            voice_enabled=True,
            preferred_voice_id="user-preferred-voice",
        )

        mock_elevenlabs_client.get_tts_stream_url = AsyncMock(return_value=TTSResult(
            audio_stream_url="/api/voice/tts/stream",
            duration_estimate_ms=5000,
            fallback_reason=FallbackReason.NONE,
        ))

        await service.generate_stream_url("Hello world", user_preferences=prefs)

        # Verify preferred voice was used
        mock_elevenlabs_client.get_tts_stream_url.assert_called_once()
        call_kwargs = mock_elevenlabs_client.get_tts_stream_url.call_args[1]
        assert call_kwargs['voice_id'] == "user-preferred-voice"

    @pytest.mark.asyncio
    async def test_generate_stream_url_voice_id_override(self, service, mock_elevenlabs_client):
        """Test voice_id override takes precedence."""
        prefs = UserVoicePreferences(preferred_voice_id="user-voice")

        mock_elevenlabs_client.get_tts_stream_url = AsyncMock(return_value=TTSResult(
            audio_stream_url="/api/voice/tts/stream",
            duration_estimate_ms=5000,
            fallback_reason=FallbackReason.NONE,
        ))

        await service.generate_stream_url(
            "Hello",
            user_preferences=prefs,
            voice_id="override-voice"
        )

        call_kwargs = mock_elevenlabs_client.get_tts_stream_url.call_args[1]
        assert call_kwargs['voice_id'] == "override-voice"

    @pytest.mark.asyncio
    async def test_generate_stream_urls_for_sections(self, service, mock_elevenlabs_client):
        """Test generating URLs for multiple sections (AC#3)."""
        sections = [
            {"title": "Section 1", "content": "Content 1"},
            {"title": "Section 2", "content": "Content 2"},
            {"title": "Section 3", "content": "Content 3"},
        ]

        mock_elevenlabs_client.get_tts_stream_url = AsyncMock(return_value=TTSResult(
            audio_stream_url="/api/voice/tts/stream",
            duration_estimate_ms=5000,
            fallback_reason=FallbackReason.NONE,
        ))

        results = await service.generate_stream_urls_for_sections(sections)

        assert len(results) == 3
        assert all(r.has_audio for r in results)
        assert mock_elevenlabs_client.get_tts_stream_url.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_stream_urls_for_sections_voice_disabled(self, service):
        """Test sections with voice disabled."""
        sections = [
            {"title": "Section 1", "content": "Content 1"},
        ]
        prefs = UserVoicePreferences(voice_enabled=False)

        results = await service.generate_stream_urls_for_sections(sections, prefs)

        assert len(results) == 1
        assert results[0].has_audio is False
        assert results[0].fallback_reason == FallbackReason.VOICE_DISABLED

    def test_is_configured(self, service, mock_elevenlabs_client):
        """Test is_configured property."""
        mock_elevenlabs_client.is_configured = True
        assert service.is_configured is True

        mock_elevenlabs_client.is_configured = False
        assert service.is_configured is False

    @pytest.mark.asyncio
    async def test_close(self, service, mock_elevenlabs_client):
        """Test close method."""
        mock_elevenlabs_client.close = AsyncMock()

        await service.close()

        mock_elevenlabs_client.close.assert_called_once()


class TestGetTTSService:
    """Tests for singleton getter."""

    def test_get_tts_service_returns_singleton(self):
        """Test singleton pattern."""
        # Reset global
        import app.services.voice.tts as module
        module._tts_service = None

        service1 = get_tts_service()
        service2 = get_tts_service()

        assert service1 is service2


class TestFallbackMessages:
    """Tests for fallback messages."""

    def test_all_fallback_reasons_have_messages(self):
        """Test all fallback reasons are covered."""
        for reason in FallbackReason:
            assert reason in FALLBACK_MESSAGES

    def test_voice_disabled_has_no_message(self):
        """Test voice_disabled has no error message (user choice)."""
        assert FALLBACK_MESSAGES[FallbackReason.VOICE_DISABLED] is None

    def test_error_reasons_have_messages(self):
        """Test error reasons have user-facing messages."""
        error_reasons = [
            FallbackReason.API_UNAVAILABLE,
            FallbackReason.TIMEOUT,
            FallbackReason.NOT_CONFIGURED,
            FallbackReason.RATE_LIMITED,
            FallbackReason.INVALID_RESPONSE,
        ]

        for reason in error_reasons:
            message = FALLBACK_MESSAGES[reason]
            assert message is not None
            assert "text" in message.lower()  # All messages mention text fallback
