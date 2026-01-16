# Story 8.4: Morning Briefing Workflow

Status: ready-for-dev

## Story

As a **Plant Manager**,
I want **to trigger a morning briefing that covers all plant areas**,
so that **I can quickly understand overnight production without clicking through dashboards**.

## Acceptance Criteria

1. **Given** a Plant Manager triggers "Start Morning Briefing"
   **When** the briefing is generated
   **Then** the response covers all 7 production areas:
   - Packing (CAMA, Pack Cells, Variety Pack, Bag Lines, Nuspark)
   - Rychigers (101-109, 1009)
   - Grinding (Grinders 1-5)
   - Powder (1002-1004 Fill & Pack, Manual Bulk)
   - Roasting (Roasters 1-4)
   - Green Bean (Manual, Silo Transfer)
   - Flavor Room (Coffee Flavor Room)
   **And** areas are delivered in user's preferred order (FR36)

2. **Given** the briefing is playing
   **When** a section completes
   **Then** the system asks "Any questions on [Area] before I continue?"
   **And** pauses for user response

3. **Given** the user says "No" / "Continue" / "Next"
   **When** detected
   **Then** the next area section begins

4. **Given** 3-4 seconds of silence after a pause prompt (FR12)
   **When** silence is detected
   **Then** the next area section begins automatically

5. **Given** the user asks a question during a pause
   **When** the question is processed
   **Then** the Q&A response is delivered with citations (FR20)
   **And** the system asks "Anything else on [Area]?"

## Tasks / Subtasks

- [ ] Task 1: Create Morning Briefing Backend Service (AC: #1)
  - [ ] 1.1: Create `apps/api/app/services/briefing/morning.py` with `MorningBriefingService` class
  - [ ] 1.2: Implement `generate_plant_briefing()` method that orchestrates all 7 areas
  - [ ] 1.3: Define area ordering logic based on user preferences (from `user_preferences` table)
  - [ ] 1.4: Integrate with `BriefingService` from Story 8.3 for tool composition
  - [ ] 1.5: Add unit tests in `apps/api/app/tests/services/test_morning_briefing.py`

- [ ] Task 2: Create Briefing API Endpoints (AC: #1, #2, #5)
  - [ ] 2.1: Create `apps/api/app/api/briefing.py` with briefing endpoints
  - [ ] 2.2: Implement `POST /api/v1/briefing/morning` endpoint to generate morning briefing
  - [ ] 2.3: Implement `GET /api/v1/briefing/{briefing_id}` to retrieve briefing details
  - [ ] 2.4: Implement `POST /api/v1/briefing/{briefing_id}/qa` for Q&A during pause
  - [ ] 2.5: Add endpoint tests in `apps/api/app/tests/api/test_briefing_endpoints.py`

- [ ] Task 3: Create Briefing Launcher Page (AC: #1)
  - [ ] 3.1: Create `apps/web/src/app/(main)/briefing/page.tsx` - briefing launcher UI
  - [ ] 3.2: Add "Start Morning Briefing" button with user role context
  - [ ] 3.3: Display area preview based on user's preferred order
  - [ ] 3.4: Integrate with briefing API to initiate briefing generation
  - [ ] 3.5: Add loading state while briefing is being generated

- [ ] Task 4: Create Voice Controls Component (AC: #2, #3, #4)
  - [ ] 4.1: Create `apps/web/src/components/voice/VoiceControls.tsx`
  - [ ] 4.2: Implement Play/Pause/Next/End Briefing controls
  - [ ] 4.3: Add area section navigation (skip forward/back)
  - [ ] 4.4: Integrate with BriefingPlayer for audio control
  - [ ] 4.5: Add visual feedback for current playback state

- [ ] Task 5: Implement Silence Detection for Auto-Continue (AC: #4)
  - [ ] 5.1: Add WebRTC VAD (Voice Activity Detection) integration to frontend
  - [ ] 5.2: Configure 3-4 second silence threshold after pause prompts
  - [ ] 5.3: Implement auto-continue to next section on silence timeout
  - [ ] 5.4: Add visual countdown timer showing silence detection progress
  - [ ] 5.5: Handle edge cases: user starts speaking, network delays

- [ ] Task 6: Implement Q&A During Pause (AC: #5)
  - [ ] 6.1: Integrate push-to-talk from Story 8.2 for question capture
  - [ ] 6.2: Route transcribed questions to Q&A handler via `/briefing/{id}/qa`
  - [ ] 6.3: Display Q&A responses with citations in transcript panel
  - [ ] 6.4: Play Q&A response via TTS before resuming briefing
  - [ ] 6.5: Implement "Anything else on [Area]?" follow-up prompt

- [ ] Task 7: Area Data Aggregation (AC: #1)
  - [ ] 7.1: Create area-to-asset mapping for all 7 production areas
  - [ ] 7.2: Query `daily_summaries` grouped by area
  - [ ] 7.3: Use existing tools (OEE Query, Production Status, Downtime Analysis, Action List)
  - [ ] 7.4: Aggregate tool results into area-level sections
  - [ ] 7.5: Generate narrative per area via `narrative.py` from Story 8.3

## Dev Notes

### Architecture & Patterns

**Service Structure:**
- `MorningBriefingService` in `apps/api/app/services/briefing/morning.py`
- This service orchestrates existing tools to compose area-level briefing sections
- NOT a LangChain tool - follows the `BriefingService` pattern from Story 8.3

**API Pattern:**
```python
# POST /api/v1/briefing/morning
class MorningBriefingRequest(BaseModel):
    user_id: str  # From auth context

class MorningBriefingResponse(BriefingResponse):
    briefing_id: str
    sections: List[BriefingSection]  # One per area
    audio_stream_url: Optional[str]  # Nullable for text-only fallback
    total_duration_estimate: int  # Seconds
```

**Area Definition (Plant Object Model):**
```python
PRODUCTION_AREAS = [
    {"name": "Packing", "assets": ["CAMA", "Pack Cells", "Variety Pack", "Bag Lines", "Nuspark"]},
    {"name": "Rychigers", "assets": ["Rychiger 101-109", "Rychiger 1009"]},
    {"name": "Grinding", "assets": ["Grinder 1", "Grinder 2", "Grinder 3", "Grinder 4", "Grinder 5"]},
    {"name": "Powder", "assets": ["1002-1004 Fill & Pack", "Manual Bulk"]},
    {"name": "Roasting", "assets": ["Roaster 1", "Roaster 2", "Roaster 3", "Roaster 4"]},
    {"name": "Green Bean", "assets": ["Manual", "Silo Transfer"]},
    {"name": "Flavor Room", "assets": ["Coffee Flavor Room"]},
]
```

### Dependencies on Previous Stories

This story depends on:
- **Story 8.1 (ElevenLabs TTS Integration):** TTS stream URL generation for audio delivery
- **Story 8.2 (Push-to-Talk STT Integration):** STT for Q&A questions during pauses
- **Story 8.3 (Briefing Synthesis Engine):** `BriefingService`, `BriefingResponse`, narrative formatting

### Existing Tools to Compose

From Epic 5-7, these tools provide data for briefing sections:
- `ProductionStatusTool` - Current output vs target per asset
- `OEEQueryTool` - OEE for asset/area with breakdown
- `DowntimeAnalysisTool` - Top downtime reasons
- `ActionListTool` - Prioritized action items
- `SafetyEventsTool` - Safety incidents (from Epic 6)

### Data Source

- **Primary:** `daily_summaries` table (T-1 data, refreshed at 06:00 AM daily)
- **Data is pre-aggregated** - no live MSSQL queries during briefing
- **Performance budget:** Total briefing generation < 30 seconds (NFR8)
- **Target briefing duration:** ~75 seconds for full plant overview

### Frontend State Management

```typescript
// apps/web/src/lib/hooks/useBriefing.ts
interface BriefingState {
  briefingId: string | null;
  sections: BriefingSection[];
  currentSectionIndex: number;
  status: 'idle' | 'loading' | 'playing' | 'paused' | 'qa' | 'complete';
  silenceCountdown: number | null;  // For auto-continue
  transcript: TranscriptEntry[];
}
```

### Silence Detection Implementation

- Use WebRTC Voice Activity Detection (VAD) for silence detection
- Configure threshold: 3-4 seconds of silence triggers auto-continue
- Visual feedback: countdown timer during silence detection
- Cancel detection if user starts speaking or presses push-to-talk

### Error Handling

1. **Tool Failure:** If a tool fails, the briefing continues with available data and notes the failed section
2. **TTS Failure:** Fall back to text-only mode (nullable `audio_stream_url`)
3. **Q&A Timeout:** If Q&A takes > 2 seconds, show loading state, don't block briefing
4. **Network Loss:** Queue any pending Q&A, show offline indicator

### Project Structure Notes

**Backend Files to Create:**
- `apps/api/app/services/briefing/morning.py` - Morning briefing orchestration
- `apps/api/app/api/briefing.py` - Briefing API endpoints
- `apps/api/app/tests/services/test_morning_briefing.py` - Unit tests
- `apps/api/app/tests/api/test_briefing_endpoints.py` - API tests

**Frontend Files to Create:**
- `apps/web/src/app/(main)/briefing/page.tsx` - Briefing launcher
- `apps/web/src/components/voice/VoiceControls.tsx` - Playback controls
- `apps/web/src/lib/hooks/useBriefing.ts` - Briefing state hook (may already exist from 8.3)

**Files from Prior Stories (Expected to Exist):**
- `apps/api/app/services/briefing/service.py` - BriefingService (Story 8.3)
- `apps/api/app/services/briefing/narrative.py` - Narrative formatting (Story 8.3)
- `apps/api/app/models/briefing.py` - BriefingResponse, BriefingSection (Story 8.3)
- `apps/api/app/services/voice/tts.py` - TTS stream URL generation (Story 8.1)
- `apps/web/src/components/voice/BriefingPlayer.tsx` - Audio playback (Story 8.1)
- `apps/web/src/components/voice/PushToTalkButton.tsx` - STT capture (Story 8.2)

### Testing Strategy

1. **Unit Tests (morning.py):**
   - Test area ordering respects user preferences
   - Test briefing generation with mocked tool responses
   - Test section composition for each of 7 areas
   - Test graceful degradation when tools fail

2. **API Tests (briefing.py):**
   - Test `POST /api/v1/briefing/morning` returns valid BriefingResponse
   - Test Q&A endpoint during pause
   - Test authentication and role-based access

3. **Integration Tests:**
   - Test end-to-end briefing flow with mock ElevenLabs
   - Test silence detection triggers auto-continue
   - Test Q&A interruption and resumption

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#BriefingService Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Voice Integration Architecture]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#BriefingService Pattern]
- [Source: _bmad/bmm/data/architecture.md#Data Models & Plant Object Model]
- [Source: _bmad-output/planning-artifacts/epic-8.md#Story 8.4]
- [Source: apps/api/app/services/agent/tools/action_list.py] - Existing Action List Tool pattern
- [Source: apps/api/app/services/agent/tools/oee_query.py] - Existing OEE Query Tool pattern
- [Source: apps/api/app/services/pipelines/morning_report.py] - Existing morning report pipeline

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
