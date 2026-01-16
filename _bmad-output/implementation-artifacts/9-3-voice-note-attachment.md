# Story 9.3: Voice Note Attachment

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **outgoing Supervisor**,
I want **to add voice notes to my handoff**,
So that **I can quickly convey context that's hard to type**.

## Acceptance Criteria

1. **AC1: Voice Note Recording Initiation**
   - **Given** the Supervisor is creating a handoff
   - **When** they select "Add Voice Note" (FR23)
   - **Then** push-to-talk recording begins
   - **And** visual indicator shows recording active

2. **AC2: Recording Completion and Transcription**
   - **Given** recording completes
   - **When** the Supervisor releases the button
   - **Then** the audio is transcribed for searchability
   - **And** both audio and transcript are attached to handoff
   - **And** Supervisor can review and re-record if needed

3. **AC3: Multiple Voice Notes Management**
   - **Given** multiple voice notes are added
   - **When** the handoff is saved
   - **Then** all notes are preserved in order
   - **And** each note shows duration and timestamp

4. **AC4: Recording Error Handling**
   - **Given** recording fails (permissions, hardware)
   - **When** the error is detected
   - **Then** the system suggests text input as fallback
   - **And** error is logged for troubleshooting

## Tasks / Subtasks

- [ ] **Task 1: Voice Notes Database Migration** (AC: #2, #3)
  - [ ] 1.1 Create `supabase/migrations/20260115_006_handoff_voice_notes.sql`
  - [ ] 1.2 Define `handoff_voice_notes` table schema:
    - `id` UUID PRIMARY KEY
    - `handoff_id` UUID FK -> shift_handoffs(id)
    - `user_id` UUID FK -> auth.users(id)
    - `storage_path` TEXT (Supabase Storage path)
    - `transcript` TEXT (ElevenLabs Scribe output)
    - `duration_seconds` INTEGER
    - `sequence_order` INTEGER
    - `created_at` TIMESTAMPTZ DEFAULT now()
  - [ ] 1.3 Add RLS policies: users can CRUD their own voice notes within handoff context
  - [ ] 1.4 Create Supabase Storage bucket `handoff-voice-notes` with user_id path prefix

- [ ] **Task 2: Backend Voice Note Upload Endpoint** (AC: #2, #3)
  - [ ] 2.1 Add endpoint to `apps/api/app/api/handoff.py`:
    - `POST /api/v1/handoff/{handoff_id}/voice-notes` - Upload voice note
    - `GET /api/v1/handoff/{handoff_id}/voice-notes` - List voice notes
    - `DELETE /api/v1/handoff/{handoff_id}/voice-notes/{note_id}` - Delete voice note
  - [ ] 2.2 Implement file upload handling with multipart/form-data
  - [ ] 2.3 Upload audio file to Supabase Storage with path: `{user_id}/{handoff_id}/{note_id}.webm`
  - [ ] 2.4 Call ElevenLabs Scribe v2 for transcription after upload
  - [ ] 2.5 Store voice note record in `handoff_voice_notes` table
  - [ ] 2.6 Validate max note duration (60 seconds)
  - [ ] 2.7 Validate max notes per handoff (5 notes)

- [ ] **Task 3: Voice Note Models** (AC: #2, #3)
  - [ ] 3.1 Add to `apps/api/app/models/handoff.py`:
    - `VoiceNoteCreate` - input for upload (audio file, handoff_id)
    - `VoiceNote` - response with id, transcript, duration, storage_url, sequence
    - `VoiceNoteList` - list response with notes array
  - [ ] 3.2 Define validation for 60s max duration, 5 notes max limit

- [ ] **Task 4: VoiceNoteRecorder Component** (AC: #1, #2, #4)
  - [ ] 4.1 Create `apps/web/src/components/handoff/VoiceNoteRecorder.tsx`
  - [ ] 4.2 **REUSE** push-to-talk infrastructure from Story 8.2:
    - Import `apps/web/src/lib/voice/push-to-talk.ts` - Recording utilities
    - Import `apps/web/src/lib/voice/audio-context.ts` - Web Audio API helpers
  - [ ] 4.3 Implement press-and-hold recording button (reuse PushToTalkButton pattern)
  - [ ] 4.4 Add visual states: idle, recording (pulsing), processing (upload/transcribe), complete
  - [ ] 4.5 Display audio level visualization during recording
  - [ ] 4.6 Add 60-second max recording indicator with countdown timer
  - [ ] 4.7 Handle permission denial with text fallback suggestion
  - [ ] 4.8 Write component tests

- [ ] **Task 5: Voice Note List Component** (AC: #3)
  - [ ] 5.1 Create `apps/web/src/components/handoff/VoiceNoteList.tsx`
  - [ ] 5.2 Display list of recorded voice notes with:
    - Sequence number badge
    - Duration display (e.g., "0:45")
    - Timestamp
    - Play button for review
    - Delete button (with confirmation)
  - [ ] 5.3 Support drag-and-drop reordering of notes
  - [ ] 5.4 Display transcript below each note (expandable)
  - [ ] 5.5 Write component tests

- [ ] **Task 6: Voice Note Playback Component** (AC: #3)
  - [ ] 6.1 Create `apps/web/src/components/handoff/VoiceNotePlayer.tsx`
  - [ ] 6.2 HTML5 audio player with:
    - Play/pause toggle
    - Progress bar with seek
    - Current time / duration display
  - [ ] 6.3 Fetch audio from Supabase Storage signed URL
  - [ ] 6.4 Display transcript below audio controls
  - [ ] 6.5 Write component tests

- [ ] **Task 7: Integration with HandoffCreator** (AC: #1-4)
  - [ ] 7.1 Add VoiceNoteRecorder section to HandoffCreator.tsx wizard
  - [ ] 7.2 Display VoiceNoteList showing attached notes
  - [ ] 7.3 Enable re-recording (delete + record new)
  - [ ] 7.4 Show notes count indicator: "2/5 voice notes"
  - [ ] 7.5 Disable "Add Voice Note" when limit reached

- [ ] **Task 8: End-to-End Testing** (AC: #1-4)
  - [ ] 8.1 Integration test: record -> upload -> transcribe -> display
  - [ ] 8.2 Integration test: multiple notes -> order preserved -> playback works
  - [ ] 8.3 Error scenario tests: permission denied, upload failure, transcription failure
  - [ ] 8.4 Limit enforcement tests: 60s max, 5 notes max

## Dev Notes

### Technical Specifications

**Voice Note Recording:**
- **Max Duration:** 60 seconds per note (hard limit, auto-stop at 60s)
- **Max Notes:** 5 per handoff (business requirement)
- **Audio Format:** WebM/Opus (efficient, MediaRecorder default)
- **Storage:** Supabase Storage bucket `handoff-voice-notes`
- **Transcription:** ElevenLabs Scribe v2 (same as Story 8.2)

**Push-to-Talk Infrastructure Reuse:**
This story heavily reuses the infrastructure from Story 8.2:
- `apps/web/src/lib/voice/push-to-talk.ts` - MediaRecorder setup, recording state machine
- `apps/web/src/lib/voice/audio-context.ts` - AudioContext initialization, permission handling
- `apps/web/src/components/voice/PushToTalkButton.tsx` - Pattern for press-and-hold interaction

**Key Differences from Story 8.2:**
| Aspect | Story 8.2 (Q&A) | Story 9.3 (Voice Notes) |
|--------|-----------------|-------------------------|
| Purpose | Real-time Q&A during briefing | Persistent attachment to handoff |
| Storage | Not stored (immediate process) | Stored in Supabase Storage |
| Transcription | Streaming (WebSocket) | Batch (after recording ends) |
| Max Duration | No limit (natural speech) | 60 seconds (hard limit) |
| Delivery | Response via TTS | Attached to handoff record |

### Architecture Patterns

**Backend Voice Note Endpoint Pattern:**
```python
# File: apps/api/app/api/handoff.py
# Add to existing handoff router

@router.post("/{handoff_id}/voice-notes")
async def upload_voice_note(
    handoff_id: UUID,
    audio: UploadFile,
    user: User = Depends(get_current_user)
) -> VoiceNote:
    """
    Upload a voice note for a shift handoff.

    1. Validate handoff ownership and note limits
    2. Upload audio to Supabase Storage
    3. Transcribe via ElevenLabs Scribe v2
    4. Store record in handoff_voice_notes table
    5. Return voice note with transcript
    """
    # Validate limits (5 notes max, 60s max)
    # Upload to storage: handoff-voice-notes/{user_id}/{handoff_id}/{note_id}.webm
    # Transcribe via ElevenLabs (non-streaming, batch mode)
    # Insert into handoff_voice_notes
    return VoiceNote(...)
```

**Frontend VoiceNoteRecorder Pattern:**
```typescript
// File: apps/web/src/components/handoff/VoiceNoteRecorder.tsx
// Reuses push-to-talk infrastructure from Story 8.2

interface VoiceNoteRecorderProps {
  /** Handoff ID to attach note to */
  handoffId: string
  /** Called when note successfully recorded and transcribed */
  onNoteAdded: (note: VoiceNote) => void
  /** Called on recording error */
  onError: (error: string) => void
  /** Whether max notes limit reached */
  disabled?: boolean
}

export function VoiceNoteRecorder({ ... }: VoiceNoteRecorderProps) {
  // States: idle, recording, uploading, transcribing, complete, error
  // Reuse: push-to-talk utilities from lib/voice/
  // Display: 60s countdown timer during recording
}
```

### Database Schema

**handoff_voice_notes Table:**
```sql
CREATE TABLE handoff_voice_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handoff_id UUID NOT NULL REFERENCES shift_handoffs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    storage_path TEXT NOT NULL,
    transcript TEXT,
    duration_seconds INTEGER NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT valid_duration CHECK (duration_seconds <= 60)
);

-- Index for efficient queries
CREATE INDEX idx_voice_notes_handoff ON handoff_voice_notes(handoff_id, sequence_order);

-- RLS policies
ALTER TABLE handoff_voice_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own voice notes"
ON handoff_voice_notes
FOR ALL
USING (auth.uid() = user_id);
```

**Supabase Storage Bucket:**
```
Bucket: handoff-voice-notes
Path pattern: {user_id}/{handoff_id}/{note_id}.webm
Access: Private (signed URLs for playback)
```

### API Endpoint Specifications

```
POST   /api/v1/handoff/{handoff_id}/voice-notes
       Request: multipart/form-data with audio file
       Response: VoiceNote { id, transcript, duration_seconds, storage_url, sequence_order }
       Errors: 400 (limit exceeded), 403 (not owner), 413 (file too large)

GET    /api/v1/handoff/{handoff_id}/voice-notes
       Response: VoiceNoteList { notes: VoiceNote[], count: number }

DELETE /api/v1/handoff/{handoff_id}/voice-notes/{note_id}
       Response: 204 No Content
       Errors: 403 (not owner), 404 (not found)
```

### Error Handling Requirements

1. **Permission Denied:**
   - If browser denies microphone access
   - Display: "Microphone access required. You can add text notes instead."
   - Log error for troubleshooting
   - Offer text input as fallback

2. **Recording Too Long:**
   - Auto-stop at 60 seconds
   - Display countdown timer in last 10 seconds
   - Audio recorded up to 60s is saved
   - No error - graceful auto-stop

3. **Upload Failure:**
   - Network error during upload
   - Display: "Upload failed. Tap to retry."
   - Retain recording locally for retry
   - Log error with details

4. **Transcription Failure:**
   - ElevenLabs API error
   - Still save audio (transcript optional)
   - Display: "Note saved (transcription unavailable)"
   - Log error for monitoring

5. **Limit Exceeded:**
   - 5 notes already attached
   - Disable "Add Voice Note" button
   - Display: "Maximum 5 voice notes reached"
   - Allow deletion to add more

### Environment Variables Required

```env
# Already configured from Story 8.2:
ELEVENLABS_API_KEY=<api_key>

# Supabase Storage (already configured):
SUPABASE_URL=<url>
SUPABASE_SERVICE_ROLE_KEY=<key>
```

### Project Structure Notes

**New Files to Create:**

Database:
- `supabase/migrations/20260115_006_handoff_voice_notes.sql` - Voice notes table

Backend (extend existing):
- Add to `apps/api/app/api/handoff.py` - Voice note endpoints
- Add to `apps/api/app/models/handoff.py` - VoiceNote schemas

Frontend:
- `apps/web/src/components/handoff/VoiceNoteRecorder.tsx` - Recording component
- `apps/web/src/components/handoff/VoiceNoteList.tsx` - List display
- `apps/web/src/components/handoff/VoiceNotePlayer.tsx` - Playback component
- `apps/web/src/components/handoff/__tests__/VoiceNoteRecorder.test.tsx`
- `apps/web/src/components/handoff/__tests__/VoiceNoteList.test.tsx`
- `apps/web/src/components/handoff/__tests__/VoiceNotePlayer.test.tsx`

**Directories (may need creation):**
- `apps/web/src/components/handoff/` (check if exists from Story 9.1/9.2)
- `apps/web/src/components/handoff/__tests__/`

### Dependencies & Integration Points

**Story Dependencies:**
- Story 8.2 (Push-to-Talk STT Integration) - **MUST be complete** for push-to-talk infrastructure
- Story 9.1 (Shift Handoff Trigger) - For HandoffCreator.tsx integration
- Story 9.2 (Shift Data Synthesis) - For handoff context

**Shared Infrastructure from Story 8.2:**
- `apps/web/src/lib/voice/push-to-talk.ts` - Recording utilities
- `apps/web/src/lib/voice/audio-context.ts` - Web Audio API helpers
- `apps/api/app/services/voice/stt.py` - Can reuse transcription logic
- ElevenLabs API client patterns

**Integration with HandoffCreator:**
- VoiceNoteRecorder embedded in handoff creation wizard
- Voice notes displayed in VoiceNoteList
- Notes attached to handoff record before save

### Testing Standards

**Backend Tests:**
- Unit test voice note upload with mocked storage
- Unit test transcription with mocked ElevenLabs
- Test limit enforcement (60s, 5 notes)
- Test RLS policies (ownership validation)

**Frontend Tests:**
- Component tests with React Testing Library
- Mock MediaRecorder API (same pattern as Story 8.2)
- Test recording states (idle -> recording -> uploading -> complete)
- Test error state rendering and fallback offers
- Test 60s countdown timer display
- Test 5 notes limit enforcement

### References

- [Source: _bmad-output/planning-artifacts/epic-9.md#Story 9.3]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Voice Integration Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Offline Caching Architecture]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Handoff Component Naming]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Voice Integration Rules]
- [Source: _bmad-output/implementation-artifacts/8-2-push-to-talk-stt-integration.md]
- [Source: _bmad/bmm/data/prd.md#FR23 Voice Note Support]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
