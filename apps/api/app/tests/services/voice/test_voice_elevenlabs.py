"""
ElevenLabs Client Tests (Story 8.1 Task 6.1)

Tests for the ElevenLabs API client including:
- Successful stream URL generation
- Timeout handling
- API error handling
- Voice preference checks

AC#1: TTS Stream URL Generation
AC#2: Graceful Degradation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.voice.elevenlabs import (
    ElevenLabsClient,
    FallbackReason,
    TTSResult,
    get_elevenlabs_client,
)


class TestElevenLabsClient:
    """Tests for ElevenLabsClient."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return ElevenLabsClient()

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.elevenlabs_api_key = "test-api-key"
        settings.elevenlabs_model = "eleven_flash_v2_5"
        settings.elevenlabs_voice_id = "test-voice-id"
        settings.elevenlabs_timeout = 10
        return settings

    def test_client_initialization(self, client):
        """Test client initializes correctly."""
        assert client._settings is None
        assert client._client is None

    def test_is_configured_returns_false_when_not_configured(self, client):
        """Test is_configured returns False when API key not set."""
        with patch.object(client, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="")
            assert client.is_configured is False

    def test_is_configured_returns_true_when_configured(self, client, mock_settings):
        """Test is_configured returns True when API key is set."""
        with patch.object(client, '_get_settings', return_value=mock_settings):
            assert client.is_configured is True

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_not_configured(self, client):
        """Test stream URL generation when not configured (AC#2)."""
        with patch.object(client, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="")

            result = await client.get_tts_stream_url("Hello world")

            assert result.audio_stream_url is None
            assert result.fallback_reason == FallbackReason.NOT_CONFIGURED
            assert "not configured" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_no_voice_id(self, client, mock_settings):
        """Test stream URL generation when no voice ID configured."""
        mock_settings.elevenlabs_voice_id = ""

        with patch.object(client, '_get_settings', return_value=mock_settings):
            result = await client.get_tts_stream_url("Hello world")

            assert result.audio_stream_url is None
            assert result.fallback_reason == FallbackReason.NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_success(self, client, mock_settings):
        """Test successful stream URL generation (AC#1)."""
        with patch.object(client, '_get_settings', return_value=mock_settings):
            with patch.object(client, '_make_tts_request') as mock_request:
                expected_result = TTSResult(
                    audio_stream_url="/api/voice/tts/stream?voice_id=test",
                    duration_estimate_ms=5000,
                    fallback_reason=FallbackReason.NONE,
                )
                mock_request.return_value = expected_result

                result = await client.get_tts_stream_url("Hello world")

                assert result.audio_stream_url is not None
                assert result.fallback_reason == FallbackReason.NONE
                assert result.duration_estimate_ms > 0

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_timeout(self, client, mock_settings):
        """Test timeout handling (AC#2)."""
        with patch.object(client, '_get_settings', return_value=mock_settings):
            with patch.object(client, '_make_tts_request') as mock_request:
                mock_request.side_effect = httpx.TimeoutException("Request timed out")

                result = await client.get_tts_stream_url("Hello world")

                assert result.audio_stream_url is None
                assert result.fallback_reason == FallbackReason.TIMEOUT

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_http_error(self, client, mock_settings):
        """Test HTTP error handling (AC#2)."""
        with patch.object(client, '_get_settings', return_value=mock_settings):
            with patch.object(client, '_make_tts_request') as mock_request:
                response = MagicMock()
                response.status_code = 500
                mock_request.side_effect = httpx.HTTPStatusError(
                    "Server error",
                    request=MagicMock(),
                    response=response
                )

                result = await client.get_tts_stream_url("Hello world")

                assert result.audio_stream_url is None
                assert result.fallback_reason == FallbackReason.API_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_rate_limited(self, client, mock_settings):
        """Test rate limit handling (AC#2)."""
        with patch.object(client, '_get_settings', return_value=mock_settings):
            with patch.object(client, '_make_tts_request') as mock_request:
                response = MagicMock()
                response.status_code = 429
                mock_request.side_effect = httpx.HTTPStatusError(
                    "Rate limited",
                    request=MagicMock(),
                    response=response
                )

                result = await client.get_tts_stream_url("Hello world")

                assert result.audio_stream_url is None
                assert result.fallback_reason == FallbackReason.RATE_LIMITED

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_retry_logic(self, client, mock_settings):
        """Test retry logic with exponential backoff."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            return TTSResult(
                audio_stream_url="/api/voice/tts/stream",
                duration_estimate_ms=5000,
                fallback_reason=FallbackReason.NONE,
            )

        with patch.object(client, '_get_settings', return_value=mock_settings):
            with patch.object(client, '_make_tts_request', side_effect=mock_request):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    result = await client.get_tts_stream_url("Hello world")

                    # Should succeed on 3rd attempt
                    assert result.audio_stream_url is not None
                    assert call_count == 3

    @pytest.mark.asyncio
    async def test_get_tts_stream_url_custom_voice_id(self, client, mock_settings):
        """Test using custom voice ID."""
        custom_voice_id = "custom-voice-123"

        with patch.object(client, '_get_settings', return_value=mock_settings):
            with patch.object(client, '_make_tts_request') as mock_request:
                mock_request.return_value = TTSResult(
                    audio_stream_url="/api/voice/tts/stream",
                    duration_estimate_ms=5000,
                    fallback_reason=FallbackReason.NONE,
                )

                await client.get_tts_stream_url("Hello", voice_id=custom_voice_id)

                # Verify custom voice_id was passed
                mock_request.assert_called_once()
                call_args = mock_request.call_args
                assert call_args[1]['voice_id'] == custom_voice_id

    def test_build_streaming_url(self, client):
        """Test streaming URL construction."""
        url = client._build_streaming_url(
            voice_id="test-voice",
            model_id="eleven_flash_v2_5",
            text="Hello world",
            stability=0.5,
            similarity_boost=0.75,
        )

        assert "/api/voice/tts/stream" in url
        assert "voice_id=test-voice" in url
        assert "model_id=eleven_flash_v2_5" in url
        assert "stability=0.5" in url
        assert "similarity_boost=0.75" in url

    @pytest.mark.asyncio
    async def test_list_voices_not_configured(self, client):
        """Test list voices when not configured."""
        with patch.object(client, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="")

            result = await client.list_voices()

            assert result["voices"] == []
            assert "error" in result

    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test client cleanup."""
        mock_http_client = AsyncMock()
        mock_http_client.is_closed = False
        client._client = mock_http_client

        await client.close()

        mock_http_client.aclose.assert_called_once()
        assert client._client is None


class TestGetElevenLabsClient:
    """Tests for singleton getter."""

    def test_get_elevenlabs_client_returns_singleton(self):
        """Test singleton pattern."""
        # Reset global
        import app.services.voice.elevenlabs as module
        module._elevenlabs_client = None

        client1 = get_elevenlabs_client()
        client2 = get_elevenlabs_client()

        assert client1 is client2


class TestTTSResult:
    """Tests for TTSResult dataclass."""

    def test_tts_result_with_audio(self):
        """Test TTSResult with audio URL."""
        result = TTSResult(
            audio_stream_url="/api/voice/tts/stream",
            duration_estimate_ms=5000,
            fallback_reason=FallbackReason.NONE,
        )

        assert result.audio_stream_url is not None
        assert result.duration_estimate_ms == 5000
        assert result.fallback_reason == FallbackReason.NONE
        assert result.error_message is None

    def test_tts_result_fallback(self):
        """Test TTSResult with fallback."""
        result = TTSResult(
            audio_stream_url=None,
            duration_estimate_ms=None,
            fallback_reason=FallbackReason.TIMEOUT,
            error_message="Request timed out",
        )

        assert result.audio_stream_url is None
        assert result.fallback_reason == FallbackReason.TIMEOUT
        assert result.error_message == "Request timed out"


class TestFallbackReason:
    """Tests for FallbackReason enum."""

    def test_fallback_reason_values(self):
        """Test all fallback reason values exist."""
        assert FallbackReason.NONE.value == ""
        assert FallbackReason.API_UNAVAILABLE.value == "api_unavailable"
        assert FallbackReason.TIMEOUT.value == "timeout"
        assert FallbackReason.VOICE_DISABLED.value == "voice_disabled"
        assert FallbackReason.NOT_CONFIGURED.value == "not_configured"
        assert FallbackReason.RATE_LIMITED.value == "rate_limited"
        assert FallbackReason.INVALID_RESPONSE.value == "invalid_response"
