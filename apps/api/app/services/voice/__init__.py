"""
Voice Services Package (Story 8.1, 8.2)

Provides voice input/output services for the Manufacturing Performance Assistant.
Includes ElevenLabs TTS integration and speech-to-text services.

Components:
- ElevenLabsClient: Direct API client for ElevenLabs TTS
- TTSService: High-level TTS service with graceful degradation
- STTWebSocketHandler: WebSocket handler for STT streaming
- STTService: High-level STT service for voice input
"""

from app.services.voice.elevenlabs import ElevenLabsClient, get_elevenlabs_client
from app.services.voice.tts import TTSService, get_tts_service
from app.services.voice.stt import (
    STTWebSocketHandler,
    STTService,
    STTResult,
    STTState,
    STTErrorCode,
    get_stt_service,
)

__all__ = [
    # TTS (Story 8.1)
    "ElevenLabsClient",
    "get_elevenlabs_client",
    "TTSService",
    "get_tts_service",
    # STT (Story 8.2)
    "STTWebSocketHandler",
    "STTService",
    "STTResult",
    "STTState",
    "STTErrorCode",
    "get_stt_service",
]
