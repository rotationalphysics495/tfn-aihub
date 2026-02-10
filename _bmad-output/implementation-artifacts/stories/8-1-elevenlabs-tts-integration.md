# Story 8.1: ElevenLabs TTS Integration

Status: ready-for-dev

## Story

As a Plant Manager,
I want briefings delivered via natural-sounding voice,
so that I can receive information hands-free while multitasking.

## Acceptance Criteria

1. **AC1: TTS Stream URL Generation**
   - Given a briefing is ready to deliver
   - When the user has voice enabled in preferences
   - Then the system generates a streaming audio URL via ElevenLabs Flash v2.5
   - And audio playback begins within 2 seconds of text generation (NFR9)
   - And text transcript is displayed simultaneously (FR13)

2. **AC2: Graceful Degradation**
   - Given ElevenLabs API is unavailable
   - When TTS is requested
   - Then the system gracefully degrades to text-only mode (NFR22)
   - And user is notified: "Voice temporarily unavailable - showing text"
   - And no error is thrown to the user

3. **AC3: Section Pause Points**
   - Given audio is streaming
   - When playback completes for a section
   - Then the system pauses at designated pause points
   - And waits for user input or silence detection

4. **AC4: Voice Preference Handling**
   - Given user has voice disabled in preferences
   - When a briefing is generated
   - Then `audio_stream_url` is null in the response
   - And only text is displayed

## Tasks / Subtasks

- [ ] **Task 1: Backend Voice Service Structure** (AC: 1, 2, 4)
  - [ ] 1.1 Create `apps/api/app/services/voice/__init__.py` package
  - [ ] 1.2 Create `apps/api/app/services/voice/elevenlabs.py` - ElevenLabs API client
    - Implement `ElevenLabsClient` class with async methods
    - Add `get_tts_stream_url(text: str, voice_id: str) -> Optional[str]`
    - Handle API authentication via config
    - Implement retry logic with exponential backoff (3 retries)
    - Log all API interactions for debugging
  - [ ] 1.3 Create `apps/api/app/services/voice/tts.py` - TTS service layer
    - Implement `TTSService` class wrapping ElevenLabsClient
    - Add `generate_stream_url(text: str, user_preferences: UserPreferences) -> Optional[str]`
    - Check voice_enabled preference before calling ElevenLabs
    - Return None (not error) when voice disabled or API fails
  - [ ] 1.4 Add configuration to `apps/api/app/core/config.py`
    - `elevenlabs_api_key: str = ""`
    - `elevenlabs_model: str = "eleven_flash_v2_5"` (Flash v2.5)
    - `elevenlabs_voice_id: str = ""` (default voice)
    - `elevenlabs_timeout: int = 10` (seconds)
    - `elevenlabs_configured` property

- [ ] **Task 2: Voice Models** (AC: 1, 4)
  - [ ] 2.1 Create `apps/api/app/models/voice.py` with Pydantic schemas
    - `TTSRequest(text: str, voice_id: Optional[str], streaming: bool = True)`
    - `TTSResponse(audio_stream_url: Optional[str], duration_estimate_ms: Optional[int], fallback_reason: Optional[str])`
    - `VoiceConfig(voice_id: str, model: str, stability: float, similarity_boost: float)`

- [ ] **Task 3: Graceful Degradation Implementation** (AC: 2)
  - [ ] 3.1 Implement try/except in `ElevenLabsClient.get_tts_stream_url()`
    - Catch `httpx.TimeoutException` - return None, log warning
    - Catch `httpx.HTTPStatusError` - return None, log error with status
    - Catch generic `Exception` - return None, log error
  - [ ] 3.2 Add `fallback_reason` field to track why voice unavailable
    - "api_unavailable" - ElevenLabs returned error
    - "timeout" - Request exceeded timeout
    - "voice_disabled" - User preference
  - [ ] 3.3 Update TTSResponse to include fallback notification text

- [ ] **Task 4: Frontend Voice Client** (AC: 1, 3)
  - [ ] 4.1 Create `apps/web/src/lib/voice/elevenlabs-client.ts`
    - `ElevenLabsClient` class for frontend audio streaming
    - `playStream(url: string): Promise<void>` - Play audio from URL
    - `pause(): void` - Pause playback
    - `resume(): void` - Resume playback
    - `stop(): void` - Stop and cleanup
    - Event handlers: `onComplete`, `onError`, `onTimeUpdate`
  - [ ] 4.2 Create `apps/web/src/lib/voice/audio-context.ts`
    - Web Audio API helper utilities
    - `createAudioContext(): AudioContext`
    - `decodeAudioData(arrayBuffer: ArrayBuffer): Promise<AudioBuffer>`
    - Handle browser autoplay policies

- [ ] **Task 5: BriefingPlayer Component** (AC: 1, 3)
  - [ ] 5.1 Create `apps/web/src/components/voice/BriefingPlayer.tsx`
    - Props: `sections: BriefingSection[]`, `audioStreamUrl: string | null`, `onSectionComplete: (index: number) => void`
    - State: `currentSection`, `isPlaying`, `isPaused`
    - Dual delivery: text always visible, audio plays if URL provided
    - Pause points: emit `onSectionComplete` when section audio ends
  - [ ] 5.2 Add playback controls
    - Play/Pause button
    - Progress indicator (time elapsed / total estimate)
    - Volume control
    - Mute toggle
  - [ ] 5.3 Create `apps/web/src/components/voice/__tests__/BriefingPlayer.test.tsx`
    - Test text-only rendering when no audio URL
    - Test playback state transitions
    - Test pause point callback

- [ ] **Task 6: Integration Testing** (AC: 1, 2, 3, 4)
  - [ ] 6.1 Create `apps/api/app/tests/services/test_voice_elevenlabs.py`
    - Mock ElevenLabs API responses
    - Test successful stream URL generation
    - Test timeout handling
    - Test API error handling
    - Test voice preference check
  - [ ] 6.2 Create `apps/api/app/tests/services/test_voice_tts.py`
    - Test TTSService with mocked ElevenLabsClient
    - Test graceful degradation returns None (not exception)
    - Test fallback_reason population

## Dev Notes

### Architecture Compliance

This story implements the **Voice TTS** component as specified in `architecture/voice-briefing.md`:

- **Pattern:** Hybrid Backend URL + Client Streaming
- **Flow:**
  1. Backend generates briefing text via BriefingService (Story 8.3)
  2. Backend requests ElevenLabs streaming URL via TTSService
  3. Returns `BriefingResponse` with text sections + `audio_stream_url`
  4. Frontend streams audio directly from ElevenLabs
  5. If `audio_stream_url` is null, graceful text-only mode

### ElevenLabs API Specifications

From architecture documentation:
- **Model:** ElevenLabs Flash v2.5 (~75ms inference latency)
- **Expected total latency:** 300-500ms to first audio byte
- **API Pattern:** POST to `/v1/text-to-speech/{voice_id}/stream`
- **Response:** Chunked audio stream (mp3/mpeg by default)
- **NFR9 Target:** Audio playback within 2 seconds of text generation

### Critical Implementation Notes

1. **Nullable audio_stream_url is NOT an error state**
   - Architecture explicitly states: "If `audio_stream_url` is null, graceful text-only mode"
   - NEVER throw exceptions for voice failures - always return None and fallback_reason
   - Voice is an enhancement, text is the primary channel

2. **Do NOT create new tools or modify existing ManufacturingTools**
   - This story creates SERVICES, not tools
   - TTSService is a standalone service, not part of the agent tool system
   - BriefingService (Story 8.3) will orchestrate these services

3. **Environment Configuration**
   - Add `elevenlabs_api_key` to config.py
   - Add `elevenlabs_configured` property to check availability
   - NEVER hardcode API keys or voice IDs

### File Structure Alignment

Per architecture `voice-briefing.md` Section 4:

```
apps/api/app/
  services/voice/
    __init__.py           # Story 8.1
    elevenlabs.py         # Story 8.1
    tts.py                # Story 8.1
    stt.py                # Story 8.2 (NOT this story)
  models/
    voice.py              # Story 8.1

apps/web/src/
  lib/voice/
    elevenlabs-client.ts  # Story 8.1
    audio-context.ts      # Story 8.1
    push-to-talk.ts       # Story 8.2 (NOT this story)
  components/voice/
    BriefingPlayer.tsx    # Story 8.1
    PushToTalkButton.tsx  # Story 8.2 (NOT this story)
```

### Testing Standards

- Backend tests use `pytest` with `pytest-asyncio`
- Mock external APIs using `respx` or `unittest.mock`
- Frontend tests use Jest + React Testing Library
- Test graceful degradation paths (API failure, timeout)

### Dependencies

- **Python:** `httpx` (async HTTP client for ElevenLabs API)
- **Frontend:** No new npm packages required (use native Web Audio API)

### Performance Budget

| Metric | Target | Measurement |
|--------|--------|-------------|
| TTS stream URL generation | < 500ms | Backend API call duration |
| Audio playback start | < 2s from text | Frontend metric (NFR9) |
| Fallback detection | < 100ms | Time from error to text-only mode |

### Project Structure Notes

- Follow `snake_case` for Python files, `PascalCase` for TypeScript
- Co-locate tests in `__tests__/` folders for frontend
- Backend tests in `apps/api/app/tests/` mirroring source structure
- Reference Story 8.1 in all docstrings

### Relationship to Other Stories

- **Depends on:** None (first story in Epic 8)
- **Depended on by:**
  - Story 8.3 (Briefing Synthesis Engine) - Uses TTSService
  - Story 8.4 (Morning Briefing Workflow) - Uses BriefingPlayer
  - Story 8.7 (Area-by-Area Delivery UI) - Extends BriefingPlayer

### References

- [Source: architecture/voice-briefing.md#Voice Integration Architecture]
- [Source: architecture/voice-briefing.md#Latency Budget]
- [Source: architecture/implementation-patterns.md#Voice Integration Rules]
- [Source: prd/prd-functional-requirements.md#FR8-FR13]
- [Source: prd/prd-non-functional-requirements.md#NFR9]
- [Source: prd/prd-non-functional-requirements.md#NFR22]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

N/A

### Completion Notes List

- Created voice services package with ElevenLabs API client
- Implemented TTSService with graceful degradation (returns None, not exceptions)
- Added fallback_reason tracking for all failure modes (timeout, api_unavailable, rate_limited, etc.)
- Created voice models (TTSRequest, TTSResponse, VoiceConfig, BriefingSection, BriefingResponse)
- Updated config.py with ElevenLabs settings (api_key, model, voice_id, timeout)
- Added elevenlabs_configured property to Settings
- Created frontend ElevenLabsClient for audio streaming with full playback controls
- Created audio-context.ts utilities for Web Audio API and autoplay unlock
- Built BriefingPlayer component with dual text/audio delivery and section pause points
- Created comprehensive backend tests for ElevenLabsClient and TTSService
- Created frontend tests for BriefingPlayer component

### File List

Backend:
- apps/api/app/services/voice/__init__.py
- apps/api/app/services/voice/elevenlabs.py
- apps/api/app/services/voice/tts.py
- apps/api/app/models/voice.py
- apps/api/app/core/config.py (modified)
- apps/api/app/tests/services/voice/__init__.py
- apps/api/app/tests/services/voice/test_voice_elevenlabs.py
- apps/api/app/tests/services/voice/test_voice_tts.py

Frontend:
- apps/web/src/lib/voice/elevenlabs-client.ts
- apps/web/src/lib/voice/audio-context.ts
- apps/web/src/lib/voice/index.ts
- apps/web/src/components/voice/BriefingPlayer.tsx
- apps/web/src/components/voice/index.ts
- apps/web/src/components/voice/__tests__/BriefingPlayer.test.tsx

