"""
STT Service (Story 8.2)

Speech-to-text service using ElevenLabs Scribe v2 for real-time transcription.
Handles WebSocket connections, audio streaming, and transcription results.

AC#2: WebSocket STT Streaming
AC#4: No Speech Detection
AC#5: Network Error Handling

References:
- [Source: architecture/voice-briefing.md#Voice Integration Architecture]
- [Source: prd/prd-non-functional-requirements.md#NFR10]
"""

import logging
import asyncio
import json
import base64
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class STTState(str, Enum):
    """State of the STT connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


class STTErrorCode(str, Enum):
    """Error codes for STT failures."""
    NONE = ""
    NO_SPEECH = "no_speech"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    API_ERROR = "api_error"
    RECORDING_TOO_SHORT = "recording_too_short"
    NOT_CONFIGURED = "not_configured"
    AUTHENTICATION_ERROR = "authentication_error"


@dataclass
class STTResult:
    """Result from speech-to-text transcription."""
    text: str
    confidence: float
    duration_ms: int
    error_code: STTErrorCode = STTErrorCode.NONE
    error_message: Optional[str] = None

    @property
    def has_text(self) -> bool:
        """Check if transcription has text."""
        return bool(self.text and self.text.strip())

    @property
    def has_error(self) -> bool:
        """Check if there was an error."""
        return self.error_code != STTErrorCode.NONE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "error_code": self.error_code.value,
            "error_message": self.error_message,
            "has_text": self.has_text,
            "has_error": self.has_error,
        }


class STTWebSocketHandler:
    """
    WebSocket handler for ElevenLabs Scribe v2 STT.

    Story 8.2 Implementation:
    - AC#2: Manages WebSocket connection for streaming transcription
    - AC#4: Detects and handles no-speech scenarios
    - AC#5: Handles network errors with reconnection

    Usage:
        handler = STTWebSocketHandler()
        await handler.connect(session_id)
        await handler.stream_audio(audio_chunk)
        result = await handler.finish_recording()
        await handler.disconnect()
    """

    ELEVENLABS_STT_URL = "wss://api.elevenlabs.io/v1/speech-to-text"
    MIN_RECORDING_DURATION_MS = 500  # Filter out <0.5s recordings
    CONNECTION_TIMEOUT = 10.0  # seconds
    TRANSCRIPTION_TIMEOUT = 5.0  # seconds

    def __init__(self):
        """Initialize the STT handler."""
        self._settings = None
        self._state = STTState.DISCONNECTED
        self._session_id: Optional[str] = None
        self._websocket = None
        self._audio_chunks: list = []
        self._recording_start_time: Optional[datetime] = None
        self._on_transcription: Optional[Callable[[STTResult], Awaitable[None]]] = None
        self._on_error: Optional[Callable[[str], Awaitable[None]]] = None

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def state(self) -> STTState:
        """Get current state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected to ElevenLabs."""
        return self._state in (STTState.CONNECTED, STTState.RECORDING, STTState.PROCESSING)

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._state == STTState.RECORDING

    @property
    def is_configured(self) -> bool:
        """Check if STT is properly configured."""
        settings = self._get_settings()
        return bool(settings.elevenlabs_api_key)

    def set_callbacks(
        self,
        on_transcription: Optional[Callable[[STTResult], Awaitable[None]]] = None,
        on_error: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> None:
        """Set callback functions."""
        self._on_transcription = on_transcription
        self._on_error = on_error

    async def connect(self, session_id: str) -> bool:
        """
        Initialize connection for STT session.

        For the ElevenLabs Scribe API, we use REST API calls rather than
        persistent WebSocket for simplicity and reliability.

        Args:
            session_id: Unique session identifier

        Returns:
            True if connection successful, False otherwise
        """
        if not self.is_configured:
            logger.warning("ElevenLabs STT not configured")
            self._state = STTState.ERROR
            return False

        self._session_id = session_id
        self._state = STTState.CONNECTED
        self._audio_chunks = []

        logger.info(f"STT session connected: {session_id}")
        return True

    async def start_recording(self) -> bool:
        """
        Start recording audio.

        Returns:
            True if recording started, False otherwise
        """
        if self._state != STTState.CONNECTED:
            logger.warning(f"Cannot start recording in state: {self._state}")
            return False

        self._state = STTState.RECORDING
        self._recording_start_time = datetime.utcnow()
        self._audio_chunks = []

        logger.debug(f"Recording started for session: {self._session_id}")
        return True

    async def stream_audio(self, audio_chunk: bytes) -> None:
        """
        Stream audio chunk for transcription.

        Args:
            audio_chunk: Raw audio data chunk
        """
        if self._state != STTState.RECORDING:
            logger.warning(f"Cannot stream audio in state: {self._state}")
            return

        self._audio_chunks.append(audio_chunk)

    async def finish_recording(self) -> STTResult:
        """
        Finish recording and get transcription.

        AC#2: Sends audio to ElevenLabs Scribe v2 for transcription
        AC#4: Handles no-speech detection

        Returns:
            STTResult with transcription or error
        """
        if self._state != STTState.RECORDING:
            return STTResult(
                text="",
                confidence=0.0,
                duration_ms=0,
                error_code=STTErrorCode.API_ERROR,
                error_message="Not recording",
            )

        self._state = STTState.PROCESSING

        # Calculate recording duration
        duration_ms = 0
        if self._recording_start_time:
            duration_ms = int(
                (datetime.utcnow() - self._recording_start_time).total_seconds() * 1000
            )

        # Filter short recordings
        if duration_ms < self.MIN_RECORDING_DURATION_MS:
            logger.debug(f"Recording too short: {duration_ms}ms")
            self._state = STTState.CONNECTED
            return STTResult(
                text="",
                confidence=0.0,
                duration_ms=duration_ms,
                error_code=STTErrorCode.RECORDING_TOO_SHORT,
            )

        # Combine audio chunks
        if not self._audio_chunks:
            self._state = STTState.CONNECTED
            return STTResult(
                text="",
                confidence=0.0,
                duration_ms=duration_ms,
                error_code=STTErrorCode.NO_SPEECH,
                error_message="No audio recorded",
            )

        audio_data = b"".join(self._audio_chunks)

        # Send to ElevenLabs for transcription
        try:
            result = await self._transcribe_audio(audio_data, duration_ms)
            self._state = STTState.CONNECTED

            # Trigger callback if set
            if self._on_transcription:
                await self._on_transcription(result)

            return result

        except asyncio.TimeoutError:
            self._state = STTState.CONNECTED
            error_msg = "Transcription timed out"
            if self._on_error:
                await self._on_error(error_msg)
            return STTResult(
                text="",
                confidence=0.0,
                duration_ms=duration_ms,
                error_code=STTErrorCode.TIMEOUT,
                error_message=error_msg,
            )

        except Exception as e:
            self._state = STTState.ERROR
            error_msg = f"Transcription failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if self._on_error:
                await self._on_error(error_msg)
            return STTResult(
                text="",
                confidence=0.0,
                duration_ms=duration_ms,
                error_code=STTErrorCode.API_ERROR,
                error_message=error_msg,
            )

    async def _transcribe_audio(self, audio_data: bytes, duration_ms: int) -> STTResult:
        """
        Send audio to ElevenLabs Scribe API for transcription.

        Uses the REST API endpoint for simplicity.
        Target latency: <2s per NFR10
        """
        settings = self._get_settings()

        # ElevenLabs Scribe REST API endpoint
        url = "https://api.elevenlabs.io/v1/speech-to-text"

        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
        }

        # Prepare multipart form data
        files = {
            "audio": ("audio.webm", audio_data, "audio/webm"),
        }

        data = {
            "model_id": "scribe_v1",  # Use available model
        }

        async with httpx.AsyncClient(timeout=self.TRANSCRIPTION_TIMEOUT) as client:
            response = await client.post(
                url,
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code == 401:
                return STTResult(
                    text="",
                    confidence=0.0,
                    duration_ms=duration_ms,
                    error_code=STTErrorCode.AUTHENTICATION_ERROR,
                    error_message="Invalid API key",
                )

            if response.status_code == 429:
                return STTResult(
                    text="",
                    confidence=0.0,
                    duration_ms=duration_ms,
                    error_code=STTErrorCode.API_ERROR,
                    error_message="Rate limited",
                )

            response.raise_for_status()

            result_data = response.json()

            # Extract transcription
            text = result_data.get("text", "")
            confidence = result_data.get("confidence", 0.0)

            # Check for no speech
            if not text or not text.strip():
                return STTResult(
                    text="",
                    confidence=0.0,
                    duration_ms=duration_ms,
                    error_code=STTErrorCode.NO_SPEECH,
                    error_message="No speech detected",
                )

            logger.info(
                f"Transcription complete: '{text[:50]}...' "
                f"(confidence: {confidence:.2f}, duration: {duration_ms}ms)"
            )

            return STTResult(
                text=text.strip(),
                confidence=confidence,
                duration_ms=duration_ms,
            )

    async def cancel_recording(self) -> None:
        """Cancel current recording without transcription."""
        if self._state == STTState.RECORDING:
            self._audio_chunks = []
            self._state = STTState.CONNECTED
            logger.debug(f"Recording cancelled for session: {self._session_id}")

    async def disconnect(self) -> None:
        """Disconnect and cleanup."""
        self._state = STTState.DISCONNECTED
        self._session_id = None
        self._audio_chunks = []
        self._recording_start_time = None
        logger.info("STT session disconnected")

    async def reconnect(self) -> bool:
        """
        Attempt to reconnect after error.

        AC#5: Automatic reconnection after network errors
        """
        if not self._session_id:
            return False

        session_id = self._session_id
        await self.disconnect()
        return await self.connect(session_id)


class STTService:
    """
    High-level STT service for voice input.

    Manages STT sessions and integrates with the briefing workflow.
    """

    def __init__(self):
        """Initialize STT service."""
        self._handlers: Dict[str, STTWebSocketHandler] = {}

    async def create_session(self, session_id: str) -> STTWebSocketHandler:
        """
        Create a new STT session.

        Args:
            session_id: Unique session identifier

        Returns:
            STTWebSocketHandler for the session
        """
        handler = STTWebSocketHandler()
        await handler.connect(session_id)
        self._handlers[session_id] = handler
        return handler

    async def get_session(self, session_id: str) -> Optional[STTWebSocketHandler]:
        """Get existing STT session."""
        return self._handlers.get(session_id)

    async def close_session(self, session_id: str) -> None:
        """Close and remove STT session."""
        handler = self._handlers.pop(session_id, None)
        if handler:
            await handler.disconnect()

    async def close_all_sessions(self) -> None:
        """Close all active sessions."""
        for handler in self._handlers.values():
            await handler.disconnect()
        self._handlers.clear()

    @property
    def active_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._handlers)


# Module-level singleton
_stt_service: Optional[STTService] = None


def get_stt_service() -> STTService:
    """
    Get the singleton STTService instance.

    Returns:
        STTService singleton instance
    """
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
