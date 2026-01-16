"""
Voice API Endpoints (Story 8.2)

REST and WebSocket endpoints for voice features including:
- TTS streaming proxy
- STT WebSocket for push-to-talk

AC#2: WebSocket STT Streaming
AC#3: Q&A Processing Integration

References:
- [Source: architecture/voice-briefing.md#Voice Integration Architecture]
"""

import logging
import json
import base64
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.services.voice import get_stt_service, get_tts_service, STTErrorCode
from app.models.voice import (
    STTRequest,
    STTResultSchema,
    STTWebSocketMessage,
    TranscriptionMessage,
    ErrorMessage,
    NoSpeechMessage,
    TTSRequest,
    TTSResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# TTS Endpoints (Story 8.1)
# ============================================================================


@router.post("/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate TTS for given text.

    Returns a streaming URL or fallback information.
    """
    tts_service = get_tts_service()

    result = await tts_service.generate_stream_url(
        text=request.text,
        voice_id=request.voice_id,
    )

    return TTSResponse(
        audio_stream_url=result.audio_stream_url,
        duration_estimate_ms=result.duration_estimate_ms,
        fallback_reason=result.fallback_reason.value if result.fallback_reason else None,
        fallback_message=result.fallback_message,
        voice_enabled=result.voice_enabled,
    )


@router.get("/tts/stream")
async def stream_tts(
    voice_id: str = Query(..., description="ElevenLabs voice ID"),
    model_id: str = Query("eleven_flash_v2_5", description="Model ID"),
    text: str = Query(..., description="Text to synthesize"),
    stability: float = Query(0.5, ge=0.0, le=1.0),
    similarity_boost: float = Query(0.75, ge=0.0, le=1.0),
):
    """
    Stream TTS audio from ElevenLabs.

    This endpoint proxies the audio stream from ElevenLabs to the client.
    Used by the frontend BriefingPlayer component.
    """
    settings = get_settings()

    if not settings.elevenlabs_configured:
        raise HTTPException(status_code=503, detail="TTS service not configured")

    # Import here to avoid circular dependency
    import httpx

    async def stream_audio():
        """Generator that streams audio from ElevenLabs."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        stream_audio(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
        }
    )


# ============================================================================
# STT WebSocket Endpoint (Story 8.2)
# ============================================================================


@router.websocket("/stt")
async def websocket_stt(
    websocket: WebSocket,
    session_id: Optional[str] = Query(None, description="Session ID"),
):
    """
    WebSocket endpoint for push-to-talk STT.

    AC#2: WebSocket STT Streaming
    - Client sends audio chunks during recording
    - Server sends transcription when recording ends

    Protocol:
    - Client -> Server: { type: "audio_chunk", data: base64_audio }
    - Client -> Server: { type: "end_recording" }
    - Server -> Client: { type: "transcription", text: string, confidence: float }
    - Server -> Client: { type: "error", message: string }
    - Server -> Client: { type: "no_speech" }
    """
    await websocket.accept()

    # Generate session ID if not provided
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())

    stt_service = get_stt_service()
    handler = await stt_service.create_session(session_id)

    logger.info(f"STT WebSocket connected: {session_id}")

    try:
        # Set up callbacks
        async def on_transcription(result):
            if result.has_text:
                await websocket.send_json({
                    "type": "transcription",
                    "text": result.text,
                    "confidence": result.confidence,
                    "duration_ms": result.duration_ms,
                })
            elif result.error_code == STTErrorCode.NO_SPEECH:
                await websocket.send_json({
                    "type": "no_speech",
                    "message": "No speech detected",
                })

        async def on_error(error_msg):
            await websocket.send_json({
                "type": "error",
                "message": error_msg,
            })

        handler.set_callbacks(on_transcription=on_transcription, on_error=on_error)

        # Message loop
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "start_recording":
                    await handler.start_recording()
                    await websocket.send_json({"type": "recording_started"})

                elif msg_type == "audio_chunk":
                    # Decode base64 audio
                    audio_data = base64.b64decode(data.get("data", ""))
                    await handler.stream_audio(audio_data)

                elif msg_type == "end_recording":
                    result = await handler.finish_recording()

                    if result.has_error:
                        if result.error_code == STTErrorCode.NO_SPEECH:
                            await websocket.send_json({
                                "type": "no_speech",
                                "message": result.error_message or "No speech detected",
                            })
                        elif result.error_code == STTErrorCode.RECORDING_TOO_SHORT:
                            # Silent filter for short recordings
                            await websocket.send_json({
                                "type": "recording_too_short",
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": result.error_message or "Transcription failed",
                                "error_code": result.error_code.value,
                            })
                    else:
                        await websocket.send_json({
                            "type": "transcription",
                            "text": result.text,
                            "confidence": result.confidence,
                            "duration_ms": result.duration_ms,
                        })

                elif msg_type == "cancel_recording":
                    await handler.cancel_recording()
                    await websocket.send_json({"type": "recording_cancelled"})

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message",
                })
            except Exception as e:
                logger.error(f"STT WebSocket error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal error",
                })

    except WebSocketDisconnect:
        logger.info(f"STT WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"STT WebSocket error: {e}", exc_info=True)
    finally:
        await stt_service.close_session(session_id)
        logger.info(f"STT session closed: {session_id}")


# ============================================================================
# STT REST Endpoints (alternative to WebSocket)
# ============================================================================


@router.post("/stt/transcribe", response_model=STTResultSchema)
async def transcribe_audio(
    request: STTRequest,
):
    """
    Transcribe audio file.

    Alternative to WebSocket for single-shot transcription.
    For real-time streaming, use the WebSocket endpoint.
    """
    # This would handle file upload transcription
    # For now, return a placeholder
    raise HTTPException(
        status_code=501,
        detail="File upload transcription not implemented. Use WebSocket /stt endpoint."
    )
