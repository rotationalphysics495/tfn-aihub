"""
Voice Models (Story 8.1)

Pydantic schemas for voice-related requests and responses.
Used by TTS, STT, and briefing delivery features.

AC#1: TTS Stream URL Generation - TTSRequest, TTSResponse
AC#4: Voice Preference Handling - VoiceConfig

References:
- [Source: architecture/voice-briefing.md#Voice Integration Architecture]
"""

from typing import Optional, List, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class FallbackReasonEnum(str, Enum):
    """Reasons for TTS fallback to text-only mode."""
    NONE = ""
    API_UNAVAILABLE = "api_unavailable"
    TIMEOUT = "timeout"
    VOICE_DISABLED = "voice_disabled"
    NOT_CONFIGURED = "not_configured"
    RATE_LIMITED = "rate_limited"
    INVALID_RESPONSE = "invalid_response"


class TTSRequest(BaseModel):
    """
    Request schema for TTS generation (Story 8.1 Task 2.1).

    Attributes:
        text: Text to convert to speech
        voice_id: Optional voice ID (uses default if not provided)
        streaming: Whether to use streaming mode (default True)
        model_id: Optional model override (default: eleven_flash_v2_5)
    """
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice_id: Optional[str] = Field(None, description="ElevenLabs voice ID")
    streaming: bool = Field(True, description="Use streaming mode for low latency")
    model_id: Optional[str] = Field(None, description="ElevenLabs model ID")

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Ensure text is not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Text cannot be empty or whitespace only")
        return stripped


class TTSResponse(BaseModel):
    """
    Response schema for TTS generation (Story 8.1 Task 2.1).

    AC#2: Includes fallback_reason for graceful degradation tracking.

    Attributes:
        audio_stream_url: URL for streaming audio (None if fallback)
        duration_estimate_ms: Estimated audio duration in milliseconds
        fallback_reason: Reason if audio unavailable (AC#2)
        fallback_message: User-facing message when fallback occurs
        voice_enabled: Whether voice is enabled for user
    """
    audio_stream_url: Optional[str] = Field(None, description="Streaming audio URL")
    duration_estimate_ms: Optional[int] = Field(None, description="Estimated duration in ms")
    fallback_reason: Optional[FallbackReasonEnum] = Field(None, description="Fallback reason if no audio")
    fallback_message: Optional[str] = Field(None, description="User-facing fallback message")
    voice_enabled: bool = Field(True, description="Whether voice is enabled for user")

    @property
    def has_audio(self) -> bool:
        """Check if audio is available."""
        return self.audio_stream_url is not None and self.voice_enabled


class VoiceConfig(BaseModel):
    """
    Voice configuration for TTS (Story 8.1 Task 2.1).

    Used to configure voice settings for a user or session.

    Attributes:
        voice_id: ElevenLabs voice ID
        model: ElevenLabs model ID (default: eleven_flash_v2_5)
        stability: Voice stability (0-1)
        similarity_boost: Voice similarity boost (0-1)
    """
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    model: str = Field("eleven_flash_v2_5", description="ElevenLabs model ID")
    stability: float = Field(0.5, ge=0.0, le=1.0, description="Voice stability (0-1)")
    similarity_boost: float = Field(0.75, ge=0.0, le=1.0, description="Voice similarity boost (0-1)")


class BriefingSection(BaseModel):
    """
    A section of a briefing with text and optional audio.

    AC#3: Section Pause Points - Each section can have its own audio stream.

    Attributes:
        id: Section identifier
        title: Section title
        content: Section content text
        area_id: Optional area identifier for area-specific sections
        audio_stream_url: Optional audio URL for this section
        duration_estimate_ms: Estimated audio duration
    """
    id: str = Field(..., description="Section identifier")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content text")
    area_id: Optional[str] = Field(None, description="Area identifier for scoped sections")
    audio_stream_url: Optional[str] = Field(None, description="Audio URL for this section")
    duration_estimate_ms: Optional[int] = Field(None, description="Estimated audio duration in ms")

    @property
    def has_audio(self) -> bool:
        """Check if this section has audio."""
        return self.audio_stream_url is not None


class BriefingResponse(BaseModel):
    """
    Complete briefing response with text and audio.

    Used by Morning Briefing (Story 8.4) and Supervisor Briefings (Story 8.5).

    Attributes:
        id: Briefing identifier
        title: Briefing title
        sections: List of briefing sections
        total_duration_ms: Total estimated audio duration
        fallback_reason: Fallback reason if audio unavailable
        fallback_message: User-facing fallback message
        generated_at: ISO timestamp when briefing was generated
    """
    id: str = Field(..., description="Briefing identifier")
    title: str = Field(..., description="Briefing title")
    sections: List[BriefingSection] = Field(..., description="Briefing sections")
    total_duration_ms: Optional[int] = Field(None, description="Total estimated audio duration")
    fallback_reason: Optional[FallbackReasonEnum] = Field(None, description="Fallback reason if no audio")
    fallback_message: Optional[str] = Field(None, description="User-facing fallback message")
    generated_at: str = Field(..., description="ISO timestamp when generated")

    @property
    def has_audio(self) -> bool:
        """Check if any section has audio."""
        return any(section.has_audio for section in self.sections)

    @property
    def section_count(self) -> int:
        """Get the number of sections."""
        return len(self.sections)


class UserVoicePreferencesSchema(BaseModel):
    """
    User voice preferences schema (Story 8.8, 8.9).

    Stored in user_preferences table and synced to Mem0.

    Attributes:
        voice_enabled: Master toggle for voice features
        preferred_voice_id: User's preferred voice
        playback_speed: Playback speed multiplier
        auto_play: Auto-play briefings
        pause_between_sections: Pause at section boundaries
        pause_duration_ms: Duration of pause in milliseconds
    """
    voice_enabled: bool = Field(True, description="Master toggle for voice features")
    preferred_voice_id: Optional[str] = Field(None, description="Preferred voice ID")
    playback_speed: float = Field(1.0, ge=0.5, le=2.0, description="Playback speed (0.5-2.0)")
    auto_play: bool = Field(True, description="Auto-play briefings")
    pause_between_sections: bool = Field(True, description="Pause at section boundaries")
    pause_duration_ms: int = Field(1500, ge=0, le=5000, description="Pause duration in ms")


class StreamProxyRequest(BaseModel):
    """
    Request schema for TTS stream proxy endpoint.

    Used internally to proxy audio from ElevenLabs.
    """
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    model_id: str = Field("eleven_flash_v2_5", description="ElevenLabs model ID")
    text: str = Field(..., description="Text to convert to speech")
    stability: float = Field(0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(0.75, ge=0.0, le=1.0)


# ============================================================================
# STT Models (Story 8.2)
# ============================================================================


class STTErrorCodeEnum(str, Enum):
    """Error codes for STT failures."""
    NONE = ""
    NO_SPEECH = "no_speech"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    API_ERROR = "api_error"
    RECORDING_TOO_SHORT = "recording_too_short"
    NOT_CONFIGURED = "not_configured"
    AUTHENTICATION_ERROR = "authentication_error"


class STTRequest(BaseModel):
    """
    Request schema for STT session initialization (Story 8.2 Task 2.2).

    Attributes:
        user_id: User identifier from JWT claims
        session_id: Unique session identifier
        audio_format: Audio format (webm, wav, etc.)
    """
    user_id: str = Field(..., description="User identifier from JWT")
    session_id: str = Field(..., description="Unique session identifier")
    audio_format: str = Field("webm", description="Audio format (webm, wav)")


class STTResultSchema(BaseModel):
    """
    Result schema for STT transcription (Story 8.2 Task 2.3).

    Attributes:
        text: Transcribed text
        confidence: Confidence score (0-1)
        duration_ms: Recording duration in milliseconds
        error_code: Error code if failed
        error_message: Human-readable error message
    """
    text: str = Field("", description="Transcribed text")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")
    duration_ms: int = Field(0, ge=0, description="Recording duration in ms")
    error_code: Optional[STTErrorCodeEnum] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Human-readable error message")

    @property
    def has_text(self) -> bool:
        """Check if transcription has text."""
        return bool(self.text and self.text.strip())

    @property
    def has_error(self) -> bool:
        """Check if there was an error."""
        return self.error_code is not None and self.error_code != STTErrorCodeEnum.NONE


class STTWebSocketMessage(BaseModel):
    """
    WebSocket message schema for STT communication (Story 8.2 Task 2.4).

    Message types:
    - audio_chunk: Client sends audio data
    - end_recording: Client signals recording end
    - transcription: Server sends transcription result
    - error: Server sends error
    - no_speech: Server indicates no speech detected
    """
    type: str = Field(..., description="Message type")
    data: Optional[str] = Field(None, description="Base64 encoded audio for audio_chunk")
    text: Optional[str] = Field(None, description="Transcribed text for transcription")
    confidence: Optional[float] = Field(None, description="Confidence score")
    message: Optional[str] = Field(None, description="Error message")


class AudioChunkMessage(BaseModel):
    """Audio chunk message from client."""
    type: Literal["audio_chunk"] = "audio_chunk"
    data: str = Field(..., description="Base64 encoded audio data")


class EndRecordingMessage(BaseModel):
    """End recording message from client."""
    type: Literal["end_recording"] = "end_recording"


class TranscriptionMessage(BaseModel):
    """Transcription result message from server."""
    type: Literal["transcription"] = "transcription"
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Confidence score")
    duration_ms: int = Field(..., description="Recording duration in ms")


class ErrorMessage(BaseModel):
    """Error message from server."""
    type: Literal["error"] = "error"
    message: str = Field(..., description="Error message")
    error_code: STTErrorCodeEnum = Field(..., description="Error code")


class NoSpeechMessage(BaseModel):
    """No speech detected message from server."""
    type: Literal["no_speech"] = "no_speech"
    message: str = Field("No speech detected", description="Status message")


class TranscriptEntry(BaseModel):
    """
    Entry in the transcript panel (Story 8.2 Task 7).

    Represents either a user voice input or an AI response.
    """
    id: str = Field(..., description="Unique entry ID")
    type: str = Field(..., description="Entry type: 'user' or 'assistant'")
    text: str = Field(..., description="Entry text content")
    timestamp: str = Field(..., description="ISO timestamp")
    confidence: Optional[float] = Field(None, description="STT confidence for user entries")
    citations: Optional[List[str]] = Field(None, description="Citations for assistant entries")
