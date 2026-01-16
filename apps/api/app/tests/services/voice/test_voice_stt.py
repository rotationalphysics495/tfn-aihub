"""
STT Service Tests (Story 8.2)

Tests for the STT service including:
- WebSocket connection management
- Audio streaming
- No speech detection
- Error handling

AC#2: WebSocket STT Streaming
AC#4: No Speech Detection
AC#5: Network Error Handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.voice.stt import (
    STTWebSocketHandler,
    STTService,
    STTResult,
    STTState,
    STTErrorCode,
    get_stt_service,
)


class TestSTTResult:
    """Tests for STTResult dataclass."""

    def test_result_with_text(self):
        """Test result with valid text."""
        result = STTResult(
            text="Hello world",
            confidence=0.95,
            duration_ms=2000,
        )

        assert result.has_text is True
        assert result.has_error is False
        assert result.error_code == STTErrorCode.NONE

    def test_result_no_text(self):
        """Test result with empty text."""
        result = STTResult(
            text="",
            confidence=0.0,
            duration_ms=1000,
            error_code=STTErrorCode.NO_SPEECH,
        )

        assert result.has_text is False
        assert result.has_error is True

    def test_result_whitespace_text(self):
        """Test result with whitespace-only text."""
        result = STTResult(
            text="   ",
            confidence=0.1,
            duration_ms=500,
        )

        assert result.has_text is False

    def test_to_dict(self):
        """Test to_dict conversion."""
        result = STTResult(
            text="Test text",
            confidence=0.9,
            duration_ms=1500,
        )

        d = result.to_dict()

        assert d["text"] == "Test text"
        assert d["confidence"] == 0.9
        assert d["duration_ms"] == 1500
        assert d["error_code"] == ""
        assert d["has_text"] is True
        assert d["has_error"] is False


class TestSTTWebSocketHandler:
    """Tests for STTWebSocketHandler."""

    @pytest.fixture
    def handler(self):
        """Create a test handler."""
        return STTWebSocketHandler()

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.elevenlabs_api_key = "test-api-key"
        return settings

    def test_handler_initialization(self, handler):
        """Test handler initializes correctly."""
        assert handler.state == STTState.DISCONNECTED
        assert handler.is_connected is False
        assert handler.is_recording is False

    def test_is_configured_false_without_api_key(self, handler):
        """Test is_configured returns False without API key."""
        with patch.object(handler, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="")
            assert handler.is_configured is False

    def test_is_configured_true_with_api_key(self, handler, mock_settings):
        """Test is_configured returns True with API key."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            assert handler.is_configured is True

    @pytest.mark.asyncio
    async def test_connect_success(self, handler, mock_settings):
        """Test successful connection."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            result = await handler.connect("test-session-123")

            assert result is True
            assert handler.state == STTState.CONNECTED
            assert handler.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_not_configured(self, handler):
        """Test connection failure when not configured."""
        with patch.object(handler, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="")

            result = await handler.connect("test-session")

            assert result is False
            assert handler.state == STTState.ERROR

    @pytest.mark.asyncio
    async def test_start_recording(self, handler, mock_settings):
        """Test starting recording."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            result = await handler.start_recording()

            assert result is True
            assert handler.state == STTState.RECORDING
            assert handler.is_recording is True

    @pytest.mark.asyncio
    async def test_start_recording_not_connected(self, handler):
        """Test starting recording when not connected."""
        result = await handler.start_recording()

        assert result is False
        assert handler.is_recording is False

    @pytest.mark.asyncio
    async def test_stream_audio(self, handler, mock_settings):
        """Test streaming audio chunks."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            await handler.start_recording()

            # Stream some audio chunks
            chunk1 = b"audio chunk 1"
            chunk2 = b"audio chunk 2"

            await handler.stream_audio(chunk1)
            await handler.stream_audio(chunk2)

            # Verify chunks are stored
            assert len(handler._audio_chunks) == 2

    @pytest.mark.asyncio
    async def test_finish_recording_too_short(self, handler, mock_settings):
        """Test finishing recording that's too short (AC#4)."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            await handler.start_recording()

            # Simulate very short recording (mocked timing)
            handler._recording_start_time = datetime.utcnow()

            # Immediately finish (too short)
            result = await handler.finish_recording()

            assert result.has_error is True
            assert result.error_code == STTErrorCode.RECORDING_TOO_SHORT
            assert handler.state == STTState.CONNECTED

    @pytest.mark.asyncio
    async def test_finish_recording_no_audio(self, handler, mock_settings):
        """Test finishing recording with no audio chunks."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            await handler.start_recording()

            # Wait to exceed minimum duration
            handler._recording_start_time = datetime(2020, 1, 1)  # Force old time

            result = await handler.finish_recording()

            assert result.has_error is True
            assert result.error_code == STTErrorCode.NO_SPEECH

    @pytest.mark.asyncio
    async def test_finish_recording_success(self, handler, mock_settings):
        """Test successful transcription."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            await handler.start_recording()

            # Add audio chunk
            await handler.stream_audio(b"audio data")

            # Force old recording time to pass duration check
            handler._recording_start_time = datetime(2020, 1, 1)

            # Mock the transcription API
            with patch.object(handler, '_transcribe_audio') as mock_transcribe:
                mock_transcribe.return_value = STTResult(
                    text="Hello world",
                    confidence=0.95,
                    duration_ms=2000,
                )

                result = await handler.finish_recording()

                assert result.has_text is True
                assert result.text == "Hello world"
                assert result.confidence == 0.95
                assert handler.state == STTState.CONNECTED

    @pytest.mark.asyncio
    async def test_finish_recording_api_error(self, handler, mock_settings):
        """Test transcription API error (AC#5)."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            await handler.start_recording()
            await handler.stream_audio(b"audio data")
            handler._recording_start_time = datetime(2020, 1, 1)

            with patch.object(handler, '_transcribe_audio') as mock_transcribe:
                mock_transcribe.side_effect = Exception("API error")

                result = await handler.finish_recording()

                assert result.has_error is True
                assert result.error_code == STTErrorCode.API_ERROR
                assert handler.state == STTState.ERROR

    @pytest.mark.asyncio
    async def test_cancel_recording(self, handler, mock_settings):
        """Test cancelling recording."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            await handler.start_recording()
            await handler.stream_audio(b"audio data")

            await handler.cancel_recording()

            assert handler.state == STTState.CONNECTED
            assert len(handler._audio_chunks) == 0

    @pytest.mark.asyncio
    async def test_disconnect(self, handler, mock_settings):
        """Test disconnecting."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")

            await handler.disconnect()

            assert handler.state == STTState.DISCONNECTED
            assert handler.is_connected is False

    @pytest.mark.asyncio
    async def test_reconnect(self, handler, mock_settings):
        """Test reconnection (AC#5)."""
        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            handler._state = STTState.ERROR

            result = await handler.reconnect()

            assert result is True
            assert handler.state == STTState.CONNECTED

    @pytest.mark.asyncio
    async def test_callbacks(self, handler, mock_settings):
        """Test callback invocation."""
        transcription_callback = AsyncMock()
        error_callback = AsyncMock()

        handler.set_callbacks(
            on_transcription=transcription_callback,
            on_error=error_callback,
        )

        with patch.object(handler, '_get_settings', return_value=mock_settings):
            await handler.connect("test-session")
            await handler.start_recording()
            await handler.stream_audio(b"audio data")
            handler._recording_start_time = datetime(2020, 1, 1)

            with patch.object(handler, '_transcribe_audio') as mock_transcribe:
                mock_transcribe.return_value = STTResult(
                    text="Test text",
                    confidence=0.9,
                    duration_ms=1500,
                )

                await handler.finish_recording()

                transcription_callback.assert_called_once()


class TestSTTService:
    """Tests for STTService."""

    @pytest.fixture
    def service(self):
        """Create a test service."""
        return STTService()

    @pytest.mark.asyncio
    async def test_create_session(self, service):
        """Test creating a session."""
        with patch.object(STTWebSocketHandler, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="test-key")

            handler = await service.create_session("test-session")

            assert handler is not None
            assert service.active_session_count == 1

    @pytest.mark.asyncio
    async def test_get_session(self, service):
        """Test getting an existing session."""
        with patch.object(STTWebSocketHandler, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="test-key")

            await service.create_session("test-session")
            handler = await service.get_session("test-session")

            assert handler is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, service):
        """Test getting a non-existent session."""
        handler = await service.get_session("nonexistent")
        assert handler is None

    @pytest.mark.asyncio
    async def test_close_session(self, service):
        """Test closing a session."""
        with patch.object(STTWebSocketHandler, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="test-key")

            await service.create_session("test-session")
            await service.close_session("test-session")

            assert service.active_session_count == 0

    @pytest.mark.asyncio
    async def test_close_all_sessions(self, service):
        """Test closing all sessions."""
        with patch.object(STTWebSocketHandler, '_get_settings') as mock:
            mock.return_value = MagicMock(elevenlabs_api_key="test-key")

            await service.create_session("session-1")
            await service.create_session("session-2")

            await service.close_all_sessions()

            assert service.active_session_count == 0


class TestGetSTTService:
    """Tests for singleton getter."""

    def test_get_stt_service_returns_singleton(self):
        """Test singleton pattern."""
        import app.services.voice.stt as module
        module._stt_service = None

        service1 = get_stt_service()
        service2 = get_stt_service()

        assert service1 is service2


class TestSTTErrorCode:
    """Tests for STTErrorCode enum."""

    def test_error_code_values(self):
        """Test all error code values exist."""
        assert STTErrorCode.NONE.value == ""
        assert STTErrorCode.NO_SPEECH.value == "no_speech"
        assert STTErrorCode.NETWORK_ERROR.value == "network_error"
        assert STTErrorCode.TIMEOUT.value == "timeout"
        assert STTErrorCode.API_ERROR.value == "api_error"
        assert STTErrorCode.RECORDING_TOO_SHORT.value == "recording_too_short"
        assert STTErrorCode.NOT_CONFIGURED.value == "not_configured"


class TestSTTState:
    """Tests for STTState enum."""

    def test_state_values(self):
        """Test all state values exist."""
        assert STTState.DISCONNECTED.value == "disconnected"
        assert STTState.CONNECTING.value == "connecting"
        assert STTState.CONNECTED.value == "connected"
        assert STTState.RECORDING.value == "recording"
        assert STTState.PROCESSING.value == "processing"
        assert STTState.ERROR.value == "error"
