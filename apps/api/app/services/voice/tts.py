"""
TTS Service Layer (Story 8.1)

High-level text-to-speech service that wraps ElevenLabsClient.
Handles user preferences and provides graceful degradation.

AC#1: TTS Stream URL Generation
AC#2: Graceful Degradation
AC#4: Voice Preference Handling

References:
- [Source: architecture/voice-briefing.md#Voice Integration Architecture]
- [Source: prd/prd-non-functional-requirements.md#NFR22]
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.services.voice.elevenlabs import (
    ElevenLabsClient,
    get_elevenlabs_client,
    TTSResult,
    FallbackReason,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class UserVoicePreferences:
    """
    User voice preferences for TTS (Story 8.1 AC#4).

    These preferences are stored in user_preferences table (Story 8.8)
    and synced to Mem0 for AI context (Story 8.9).
    """
    voice_enabled: bool = True
    preferred_voice_id: Optional[str] = None
    playback_speed: float = 1.0  # 0.5 - 2.0
    auto_play: bool = True
    pause_between_sections: bool = True
    pause_duration_ms: int = 1500


@dataclass
class TTSServiceResult:
    """
    Result from TTSService including user-facing messages.

    AC#2: Includes fallback notification text for UI display
    """
    audio_stream_url: Optional[str]
    duration_estimate_ms: Optional[int]
    fallback_reason: FallbackReason
    fallback_message: Optional[str]  # User-facing message
    voice_enabled: bool

    @property
    def has_audio(self) -> bool:
        """Check if audio is available."""
        return self.audio_stream_url is not None and self.voice_enabled

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "audio_stream_url": self.audio_stream_url,
            "duration_estimate_ms": self.duration_estimate_ms,
            "fallback_reason": self.fallback_reason.value if self.fallback_reason else None,
            "fallback_message": self.fallback_message,
            "voice_enabled": self.voice_enabled,
            "has_audio": self.has_audio,
        }


# User-facing fallback messages (AC#2)
FALLBACK_MESSAGES = {
    FallbackReason.NONE: None,
    FallbackReason.API_UNAVAILABLE: "Voice temporarily unavailable - showing text",
    FallbackReason.TIMEOUT: "Voice service timed out - showing text",
    FallbackReason.VOICE_DISABLED: None,  # Not an error, user choice
    FallbackReason.NOT_CONFIGURED: "Voice service not configured - showing text",
    FallbackReason.RATE_LIMITED: "Voice service busy - showing text",
    FallbackReason.INVALID_RESPONSE: "Voice service error - showing text",
}


class TTSService:
    """
    High-level TTS service with user preference handling.

    Story 8.1 Implementation:
    - AC#1: Generates streaming audio URLs via ElevenLabsClient
    - AC#2: Graceful degradation with user-facing messages
    - AC#4: Checks voice_enabled preference before calling ElevenLabs

    Usage:
        service = get_tts_service()
        result = await service.generate_stream_url(
            text="Good morning! Here's your briefing...",
            user_preferences=UserVoicePreferences(voice_enabled=True)
        )

        if result.has_audio:
            # Play audio from result.audio_stream_url
        else:
            # Show text-only with result.fallback_message
    """

    def __init__(self, elevenlabs_client: Optional[ElevenLabsClient] = None):
        """
        Initialize TTS service.

        Args:
            elevenlabs_client: Optional ElevenLabsClient instance (for testing)
        """
        self._client = elevenlabs_client
        self._settings = None

    def _get_client(self) -> ElevenLabsClient:
        """Get the ElevenLabs client (lazy initialization)."""
        if self._client is None:
            self._client = get_elevenlabs_client()
        return self._client

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def is_configured(self) -> bool:
        """Check if TTS service is properly configured."""
        return self._get_client().is_configured

    async def generate_stream_url(
        self,
        text: str,
        user_preferences: Optional[UserVoicePreferences] = None,
        voice_id: Optional[str] = None,
    ) -> TTSServiceResult:
        """
        Generate a streaming audio URL for the given text.

        AC#1: TTS Stream URL Generation
        - Generates streaming URL if voice is enabled
        - Returns URL within performance budget (<500ms)

        AC#4: Voice Preference Handling
        - Checks voice_enabled preference first
        - Returns None (not error) when voice disabled

        AC#2: Graceful Degradation
        - Returns None URL with fallback_reason on any error
        - Populates user-facing fallback_message

        Args:
            text: Text to convert to speech
            user_preferences: User's voice preferences (default: voice enabled)
            voice_id: Optional override for voice ID

        Returns:
            TTSServiceResult with audio URL or fallback information
        """
        # Default preferences if not provided
        prefs = user_preferences or UserVoicePreferences()

        # AC#4: Check voice preference first
        if not prefs.voice_enabled:
            logger.debug("Voice disabled by user preference - returning text-only")
            return TTSServiceResult(
                audio_stream_url=None,
                duration_estimate_ms=None,
                fallback_reason=FallbackReason.VOICE_DISABLED,
                fallback_message=None,  # Not an error, user's choice
                voice_enabled=False,
            )

        # Use user's preferred voice if available
        effective_voice_id = voice_id or prefs.preferred_voice_id

        # Call ElevenLabs client
        client = self._get_client()
        tts_result = await client.get_tts_stream_url(
            text=text,
            voice_id=effective_voice_id,
        )

        # Build service result with user-facing message
        fallback_message = FALLBACK_MESSAGES.get(tts_result.fallback_reason)

        return TTSServiceResult(
            audio_stream_url=tts_result.audio_stream_url,
            duration_estimate_ms=tts_result.duration_estimate_ms,
            fallback_reason=tts_result.fallback_reason,
            fallback_message=fallback_message,
            voice_enabled=True,
        )

    async def generate_stream_urls_for_sections(
        self,
        sections: List[Dict[str, str]],
        user_preferences: Optional[UserVoicePreferences] = None,
    ) -> List[TTSServiceResult]:
        """
        Generate streaming URLs for multiple briefing sections.

        AC#3: Section Pause Points
        - Each section gets its own audio URL
        - Enables pause between sections for user interaction

        Args:
            sections: List of dicts with 'title' and 'content' keys
            user_preferences: User's voice preferences

        Returns:
            List of TTSServiceResult, one per section
        """
        results = []

        for section in sections:
            title = section.get("title", "")
            content = section.get("content", "")

            # Combine title and content for natural delivery
            full_text = f"{title}. {content}" if title else content

            result = await self.generate_stream_url(
                text=full_text,
                user_preferences=user_preferences,
            )
            results.append(result)

        return results

    async def close(self) -> None:
        """Close the underlying client."""
        if self._client:
            await self._client.close()


# Module-level singleton
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """
    Get the singleton TTSService instance.

    Returns:
        TTSService singleton instance
    """
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
