# Story 8.2: Push-to-Talk STT Integration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask follow-up questions using my voice during briefings**,
So that **I can interact naturally without touching my device**.

## Acceptance Criteria

1. **AC1: Push-to-Talk Recording Initiation**
   - **Given** a briefing is in progress
   - **When** the user presses and holds the push-to-talk button
   - **Then** audio recording begins immediately
   - **And** a visual indicator shows recording is active (pulsing microphone, waveform, or similar)

2. **AC2: WebSocket STT Streaming**
   - **Given** the user is recording
   - **When** they release the push-to-talk button
   - **Then** audio is streamed to ElevenLabs Scribe v2 for transcription
   - **And** transcription completes within 2 seconds (NFR10)
   - **And** transcribed text is displayed in the transcript panel

3. **AC3: Q&A Processing Integration**
   - **Given** transcription completes
   - **When** text is received
   - **Then** the text is sent to the Q&A handler for processing
   - **And** response is delivered via TTS (if enabled) and text

4. **AC4: No Speech Detection**
   - **Given** no speech is detected during recording
   - **When** the button is released
   - **Then** the system displays "No speech detected"
   - **And** no Q&A request is made
   - **And** the user can immediately retry

5. **AC5: Network Error Handling**
   - **Given** network connectivity is lost during recording
   - **When** the button is released
   - **Then** the system displays "Connection lost - please try again"
   - **And** no partial transcription is processed
   - **And** WebSocket reconnection is attempted automatically

## Tasks / Subtasks

- [ ] **Task 1: Backend STT WebSocket Handler** (AC: #2, #4, #5)
  - [ ] 1.1 Create `apps/api/app/services/voice/stt.py` - STT WebSocket handler
  - [ ] 1.2 Implement ElevenLabs Scribe v2 WebSocket connection management
  - [ ] 1.3 Handle audio chunk streaming from client to ElevenLabs
  - [ ] 1.4 Implement transcription response parsing and forwarding
  - [ ] 1.5 Add error handling for connection drops, timeouts, and API errors
  - [ ] 1.6 Implement noise threshold filtering (<0.5s recordings rejected)
  - [ ] 1.7 Write unit tests with mocked ElevenLabs WebSocket

- [ ] **Task 2: Voice Models** (AC: #2, #3)
  - [ ] 2.1 Create/extend `apps/api/app/models/voice.py` with STT schemas
  - [ ] 2.2 Define STTRequest model (user_id, session_id, audio_format)
  - [ ] 2.3 Define STTResult model (text, confidence, duration_ms)
  - [ ] 2.4 Define WebSocket message schemas (audio_chunk, transcription, error)

- [ ] **Task 3: Voice API Endpoint** (AC: #2)
  - [ ] 3.1 Add WebSocket endpoint `WS /api/v1/voice/stt` to voice router
  - [ ] 3.2 Implement WebSocket lifecycle (connect, message, disconnect)
  - [ ] 3.3 Add authentication for WebSocket connections
  - [ ] 3.4 Integrate with existing Supabase Auth JWT validation

- [ ] **Task 4: Frontend Push-to-Talk Utilities** (AC: #1, #2)
  - [ ] 4.1 Create `apps/web/src/lib/voice/push-to-talk.ts` - Recording utilities
  - [ ] 4.2 Implement MediaRecorder setup with WebM/Opus codec
  - [ ] 4.3 Create WebSocket client for streaming to backend
  - [ ] 4.4 Handle audio chunk buffering and streaming
  - [ ] 4.5 Implement recording state machine (idle, recording, processing)

- [ ] **Task 5: Web Audio API Helpers** (AC: #1)
  - [ ] 5.1 Create `apps/web/src/lib/voice/audio-context.ts` - Web Audio API helpers
  - [ ] 5.2 Implement AudioContext initialization with proper permissions
  - [ ] 5.3 Add audio level detection for visual feedback
  - [ ] 5.4 Handle browser permissions flow for microphone access

- [ ] **Task 6: Push-to-Talk Button Component** (AC: #1, #4, #5)
  - [ ] 6.1 Create `apps/web/src/components/voice/PushToTalkButton.tsx`
  - [ ] 6.2 Implement press-and-hold interaction (mouse + touch)
  - [ ] 6.3 Add visual states: idle, recording (pulsing), processing (spinner)
  - [ ] 6.4 Add audio level visualization during recording
  - [ ] 6.5 Display error states with retry affordance
  - [ ] 6.6 Ensure 44px minimum touch target (accessibility)
  - [ ] 6.7 Write component tests

- [ ] **Task 7: Transcript Panel Component** (AC: #2, #3)
  - [ ] 7.1 Create `apps/web/src/components/voice/TranscriptPanel.tsx`
  - [ ] 7.2 Display transcribed user input with timestamp
  - [ ] 7.3 Show "transcribing..." state during processing
  - [ ] 7.4 Display Q&A response below user input
  - [ ] 7.5 Auto-scroll to latest entry
  - [ ] 7.6 Write component tests

- [ ] **Task 8: Integration with Q&A Handler** (AC: #3)
  - [ ] 8.1 Connect transcribed text to existing chat/Q&A endpoint
  - [ ] 8.2 Ensure citations are included in Q&A response (FR20)
  - [ ] 8.3 Trigger TTS response if voice is enabled in preferences

- [ ] **Task 9: End-to-End Testing** (AC: #1-5)
  - [ ] 9.1 Integration test: push-to-talk -> transcription -> display
  - [ ] 9.2 Integration test: transcription -> Q&A -> response
  - [ ] 9.3 Error scenario tests: no speech, network loss, timeout

## Dev Notes

### Technical Specifications

**ElevenLabs Scribe v2 Integration:**
- **Model:** ElevenLabs Scribe v2 Realtime
- **Connection:** WebSocket (maintained during active briefing session)
- **Expected Latency:** ~150ms transcription (target <2s per NFR10)
- **Audio Format:** WebM/Opus for efficient streaming (supported by MediaRecorder)
- **Noise Threshold:** Filter out recordings <0.5 seconds (likely accidental taps)

**Latency Budget (from Architecture):**

| Component | Target | Expected |
|-----------|--------|----------|
| STT (push-to-talk -> text) | <2s | ~150-300ms |
| Q&A Processing (text -> response) | <2s | ~500-1000ms |
| TTS (text -> audio start) | <2s | ~300-500ms |
| **Total Q&A Round-Trip** | <2s | ~1-1.5s |

### Architecture Patterns

**Backend WebSocket Pattern:**
```python
# File: apps/api/app/services/voice/stt.py
# WebSocket handler for STT streaming

class STTWebSocketHandler:
    """
    Manages WebSocket connection to ElevenLabs Scribe v2.

    - Maintains persistent connection during briefing session
    - Streams audio chunks from client to ElevenLabs
    - Returns transcription results to client
    """

    async def connect(self, session_id: str) -> None:
        """Initialize WebSocket connection to ElevenLabs."""
        pass

    async def stream_audio(self, audio_chunk: bytes) -> None:
        """Stream audio chunk to ElevenLabs for transcription."""
        pass

    async def get_transcription(self) -> STTResult:
        """Receive transcription result from ElevenLabs."""
        pass
```

**Frontend Component Pattern:**
```typescript
// File: apps/web/src/components/voice/PushToTalkButton.tsx
// Pattern: PascalCase filename, feature-organized

interface PushToTalkButtonProps {
  /** Whether the briefing session is active */
  isSessionActive: boolean
  /** Callback when transcription is complete */
  onTranscription: (text: string) => void
  /** Callback on error */
  onError: (error: string) => void
  /** Whether voice is enabled in user preferences */
  voiceEnabled: boolean
}

export function PushToTalkButton({ ... }: PushToTalkButtonProps) {
  // States: idle, recording, processing, error
  // Implementation
}
```

### API Endpoint Pattern

```
WS /api/v1/voice/stt    # WebSocket for push-to-talk STT

WebSocket Messages:
- Client -> Server: { type: "audio_chunk", data: base64_audio }
- Client -> Server: { type: "end_recording" }
- Server -> Client: { type: "transcription", text: string, confidence: float }
- Server -> Client: { type: "error", message: string }
- Server -> Client: { type: "no_speech" }
```

### Error Handling Requirements

1. **No Speech Detected:**
   - If ElevenLabs returns empty/no-speech result
   - Display friendly message, no Q&A request made
   - Allow immediate retry

2. **Network Disconnection:**
   - WebSocket disconnect during recording
   - Display error, attempt reconnection
   - Queue retry when connection restored

3. **ElevenLabs API Error:**
   - Rate limiting, authentication, or service errors
   - Log error, display user-friendly message
   - Do not expose technical details to user

4. **Recording Too Short:**
   - <0.5 second recordings filtered
   - No API call made
   - No error shown (silent filter)

### Browser Compatibility Notes

- **MediaRecorder API:** Supported in Chrome, Firefox, Safari 14.1+, Edge
- **WebM/Opus:** Preferred codec for low latency
- **Fallback:** If MediaRecorder unavailable, disable voice features gracefully
- **Permissions:** Must handle `NotAllowedError` for microphone access denial

### Project Structure Notes

**New Files to Create:**

Backend:
- `apps/api/app/services/voice/stt.py` - STT WebSocket handler
- `apps/api/app/models/voice.py` - Voice-related Pydantic models (may extend if exists)

Frontend:
- `apps/web/src/lib/voice/push-to-talk.ts` - Recording utilities
- `apps/web/src/lib/voice/audio-context.ts` - Web Audio API helpers
- `apps/web/src/components/voice/PushToTalkButton.tsx` - Recording component
- `apps/web/src/components/voice/TranscriptPanel.tsx` - Transcript display
- `apps/web/src/components/voice/__tests__/PushToTalkButton.test.tsx`
- `apps/web/src/components/voice/__tests__/TranscriptPanel.test.tsx`

**Directory Creation Required:**
- `apps/api/app/services/voice/` (create directory + `__init__.py`)
- `apps/web/src/lib/voice/` (create directory)
- `apps/web/src/components/voice/` (create directory)
- `apps/web/src/components/voice/__tests__/` (create directory)

### Dependencies & Integration Points

**Story 8.1 Dependency:**
- This story depends on Story 8.1 (ElevenLabs TTS Integration) being complete
- Shares the ElevenLabs API client patterns from `services/voice/elevenlabs.py`
- Shares voice models from `models/voice.py`
- If 8.1 not complete, create foundational files with STT focus first

**Integration with Existing Systems:**
- Q&A handler: Uses existing chat/agent endpoint for processing transcribed text
- User preferences: Check `voice_enabled` preference before showing STT features
- TTS: Response triggers TTS if `voice_enabled` (from Story 8.1)

### Environment Variables Required

```env
ELEVENLABS_API_KEY=<api_key>
ELEVENLABS_STT_WEBSOCKET_URL=wss://api.elevenlabs.io/v1/speech-to-text
```

### Testing Standards

**Backend Tests:**
- Unit tests with mocked ElevenLabs WebSocket
- Test connection lifecycle (connect, stream, disconnect)
- Test error scenarios (no speech, timeout, API error)
- Test noise threshold filtering

**Frontend Tests:**
- Component tests with React Testing Library
- Mock MediaRecorder API
- Test interaction states (idle -> recording -> processing -> complete)
- Test error state rendering

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Voice Integration Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Latency Budget]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Voice Component Naming]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#API Endpoint Pattern for Voice]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR9-FR10]
- [Source: _bmad/bmm/data/prd/prd-non-functional-requirements.md#NFR10]
- [Source: _bmad-output/planning-artifacts/epic-8.md#Story 8.2]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

N/A

### Completion Notes List

- Created STT service with WebSocket handler for ElevenLabs Scribe API
- Implemented state machine (disconnected -> connected -> recording -> processing)
- Added noise threshold filtering (<0.5s recordings silently rejected)
- Implemented error handling for no speech, timeout, API errors, network issues
- Extended voice models with STT schemas (STTRequest, STTResult, WebSocket messages)
- Created Voice API endpoints (REST + WebSocket) and added router to main.py
- Built PushToTalk utility class with MediaRecorder, WebSocket streaming, audio level detection
- Created PushToTalkButton component with press-and-hold interaction, visual states, 44px touch target
- Created TranscriptPanel component for voice interaction display
- Wrote comprehensive backend tests for STT service
- Wrote frontend component tests for PushToTalkButton and TranscriptPanel

### File List

Backend:
- apps/api/app/services/voice/stt.py
- apps/api/app/services/voice/__init__.py (modified)
- apps/api/app/models/voice.py (modified - added STT schemas)
- apps/api/app/api/voice.py
- apps/api/app/main.py (modified - added voice router)
- apps/api/app/tests/services/voice/test_voice_stt.py

Frontend:
- apps/web/src/lib/voice/push-to-talk.ts
- apps/web/src/lib/voice/index.ts (modified)
- apps/web/src/components/voice/PushToTalkButton.tsx
- apps/web/src/components/voice/TranscriptPanel.tsx
- apps/web/src/components/voice/index.ts (modified)
- apps/web/src/components/voice/__tests__/PushToTalkButton.test.tsx
- apps/web/src/components/voice/__tests__/TranscriptPanel.test.tsx
