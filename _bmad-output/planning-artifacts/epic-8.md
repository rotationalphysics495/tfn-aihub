---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad/bmm/data/prd.md"
  - "_bmad/bmm/data/prd/prd-functional-requirements.md"
  - "_bmad/bmm/data/prd/prd-non-functional-requirements.md"
  - "_bmad/bmm/data/prd/prd-epics.md"
  - "_bmad/bmm/data/architecture.md"
  - "_bmad/bmm/data/architecture/voice-briefing.md"
  - "_bmad/bmm/data/ux-design.md"
epic: 8
status: "ready"
---

# Epic 8: Voice Briefing Foundation

## Overview

**Goal:** Enable voice-first operations with Morning Briefing workflow, allowing Plant Managers and Supervisors to receive synthesized briefings hands-free.

**Dependencies:** Epic 7 (Proactive Agent Capabilities)

**User Value:** Plant Managers can receive a synthesized morning briefing hands-free while walking to their office or pouring coffee. Supervisors receive focused briefings on their assigned assets only. The 45-minute morning dashboard review becomes a 3-minute voice briefing.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR8-FR13 (Voice & Briefing Delivery) | Full |
| FR14-FR20 (Morning Briefing Workflow) | Full |
| FR35-FR45 (User Preferences & Onboarding) | Full |
| NFR7 (Q&A < 2s) | Full |
| NFR8 (Briefing < 30s) | Full |
| NFR9 (TTS < 2s start) | Full |
| NFR10 (STT < 2s) | Full |
| NFR22 (Voice fallback to text) | Full |

## Stories

---

### Story 8.1: ElevenLabs TTS Integration

**As a** Plant Manager,
**I want** briefings delivered via natural-sounding voice,
**So that** I can receive information hands-free while multitasking.

**Acceptance Criteria:**

**Given** a briefing is ready to deliver
**When** the user has voice enabled in preferences
**Then** the system generates a streaming audio URL via ElevenLabs Flash v2.5
**And** audio playback begins within 2 seconds of text generation (NFR9)
**And** text transcript is displayed simultaneously (FR13)

**Given** ElevenLabs API is unavailable
**When** TTS is requested
**Then** the system gracefully degrades to text-only mode (NFR22)
**And** user is notified: "Voice temporarily unavailable - showing text"
**And** no error is thrown to the user

**Given** audio is streaming
**When** playback completes for a section
**Then** the system pauses at designated pause points
**And** waits for user input or silence detection

**Given** user has voice disabled in preferences
**When** a briefing is generated
**Then** `audio_stream_url` is null in the response
**And** only text is displayed

**Technical Notes:**
- ElevenLabs Flash v2.5 model (~75ms inference)
- Expected latency: 300-500ms to first audio
- Streaming URL approach: backend requests URL, frontend streams directly
- Response structure: `BriefingResponse { sections, audio_stream_url?, total_duration_estimate }`
- Graceful degradation: nullable `audio_stream_url` enables clean fallback

**Files to Create/Modify:**
- `apps/api/app/services/voice/elevenlabs.py` - ElevenLabs API client
- `apps/api/app/services/voice/tts.py` - TTS stream URL generation
- `apps/api/app/models/voice.py` - TTSRequest, TTSResponse schemas
- `apps/web/src/lib/voice/elevenlabs-client.ts` - Frontend streaming client
- `apps/web/src/components/voice/BriefingPlayer.tsx` - Audio playback component

---

### Story 8.2: Push-to-Talk STT Integration

**As a** Plant Manager,
**I want** to ask follow-up questions using my voice during briefings,
**So that** I can interact naturally without touching my device.

**Acceptance Criteria:**

**Given** a briefing is in progress
**When** the user presses and holds the push-to-talk button
**Then** audio recording begins immediately
**And** a visual indicator shows recording is active

**Given** the user is recording
**When** they release the push-to-talk button
**Then** audio is streamed to ElevenLabs Scribe v2 for transcription
**And** transcription completes within 2 seconds (NFR10)
**And** transcribed text is displayed in the transcript panel

**Given** transcription completes
**When** text is received
**Then** the text is sent to the Q&A handler for processing
**And** response is delivered via TTS (if enabled) and text

**Given** no speech is detected during recording
**When** the button is released
**Then** the system displays "No speech detected"
**And** no Q&A request is made

**Given** network connectivity is lost during recording
**When** the button is released
**Then** the system displays "Connection lost - please try again"
**And** no partial transcription is processed

**Technical Notes:**
- ElevenLabs Scribe v2 Realtime via WebSocket
- Expected latency: ~150ms transcription
- WebSocket maintained during active briefing session
- Audio format: WebM/Opus for efficient streaming
- Noise threshold: filter out recordings <0.5s

**Files to Create/Modify:**
- `apps/api/app/services/voice/stt.py` - STT WebSocket handler
- `apps/web/src/lib/voice/push-to-talk.ts` - Recording utilities
- `apps/web/src/components/voice/PushToTalkButton.tsx` - Recording component
- `apps/web/src/components/voice/TranscriptPanel.tsx` - Transcript display
- `apps/web/src/lib/voice/audio-context.ts` - Web Audio API helpers

---

### Story 8.3: Briefing Synthesis Engine

**As a** system component,
**I want** to compose existing LangChain tools into coherent narrative briefings,
**So that** users receive synthesized insights rather than raw data.

**Acceptance Criteria:**

**Given** a briefing is requested
**When** the BriefingService is invoked
**Then** it orchestrates the following tools in sequence:
  - Production Status (current output vs target)
  - Safety Events (any incidents)
  - OEE Query (plant-wide or scoped)
  - Downtime Analysis (top reasons)
  - Action List (prioritized issues)
**And** results are aggregated into a unified data structure

**Given** tool results are aggregated
**When** narrative generation is triggered
**Then** the LLM formats data into natural language sections:
  - Headline summary
  - Top wins (areas >100% target)
  - Top concerns (gaps, issues)
  - Recommended actions
**And** all metrics include citations

**Given** briefing generation starts
**When** 30 seconds have elapsed (NFR8)
**Then** the system returns whatever is complete
**And** indicates any sections that timed out

**Given** a tool fails during orchestration
**When** the failure is detected
**Then** the briefing continues with available data
**And** the failed section is noted: "Unable to retrieve [section] data"

**Technical Notes:**
- BriefingService is a dedicated orchestration layer (not LangChain chains)
- Deterministic tool sequencing for predictable narratives
- Leverage existing `daily_summaries` cache for performance
- Section-based output with natural pause points
- Testable without LLM - mock tool responses

**Files to Create/Modify:**
- `apps/api/app/services/briefing/__init__.py` - Package init
- `apps/api/app/services/briefing/service.py` - BriefingService class
- `apps/api/app/services/briefing/narrative.py` - LLM narrative formatting
- `apps/api/app/models/briefing.py` - BriefingResponse, BriefingSection schemas

---

### Story 8.4: Morning Briefing Workflow

**As a** Plant Manager,
**I want** to trigger a morning briefing that covers all plant areas,
**So that** I can quickly understand overnight production without clicking through dashboards.

**Acceptance Criteria:**

**Given** a Plant Manager triggers "Start Morning Briefing"
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

**Given** the briefing is playing
**When** a section completes
**Then** the system asks "Any questions on [Area] before I continue?"
**And** pauses for user response

**Given** the user says "No" / "Continue" / "Next"
**When** detected
**Then** the next area section begins

**Given** 3-4 seconds of silence after a pause prompt (FR12)
**When** silence is detected
**Then** the next area section begins automatically

**Given** the user asks a question during a pause
**When** the question is processed
**Then** the Q&A response is delivered with citations (FR20)
**And** the system asks "Anything else on [Area]?"

**Technical Notes:**
- Briefing scope: Plant Manager = all areas, all assets
- Data source: `daily_summaries` (T-1 data, refreshed 06:00 AM)
- Silence detection: 3-4 second threshold via WebRTC VAD
- Pause points: after each area section
- Total briefing target: ~75 seconds for full plant overview

**Files to Create/Modify:**
- `apps/api/app/services/briefing/morning.py` - Morning briefing logic
- `apps/api/app/api/briefing.py` - Briefing API endpoints
- `apps/web/src/app/(main)/briefing/page.tsx` - Briefing launcher page
- `apps/web/src/components/voice/VoiceControls.tsx` - Play/pause/next controls

---

### Story 8.5: Supervisor Scoped Briefings

**As a** Supervisor,
**I want** my morning briefing to cover only my assigned assets,
**So that** I get focused information relevant to my responsibilities.

**Acceptance Criteria:**

**Given** a Supervisor triggers "Start Morning Briefing"
**When** the briefing is generated
**Then** only assets from `supervisor_assignments` table are included (FR15)
**And** no plant-wide headline is shown (straight to their areas)
**And** detail level matches their preference (FR37)

**Given** a Supervisor has 3 assigned assets across 2 areas
**When** the briefing is generated
**Then** those 3 assets are covered in detail
**And** areas are delivered in user's preferred order (FR39)

**Given** a Supervisor has no assets assigned
**When** they trigger a briefing
**Then** the system displays "No assets assigned - contact your administrator"
**And** no briefing is generated

**Given** a Supervisor's assignment changes mid-session
**When** they request a new briefing
**Then** the new assignment is reflected immediately

**Technical Notes:**
- Query: `supervisor_assignments` WHERE user_id = current_user
- Join with `assets` to get asset details
- BriefingService filters `daily_summaries` based on assigned asset_ids
- No caching of assignment lookups (always fresh)
- FastAPI dependency: `get_current_user_with_role()` provides context

**Files to Create/Modify:**
- `apps/api/app/services/briefing/morning.py` - Add supervisor scoping logic
- `apps/api/app/core/dependencies.py` - Add `get_current_user_with_role()`
- `supabase/migrations/20260115_002_supervisor_assignments.sql` - Create table

---

### Story 8.6: Voice Number Formatting

**As a** user listening to a voice briefing,
**I want** numbers formatted for natural speech,
**So that** I can easily understand metrics without mental conversion.

**Acceptance Criteria:**

**Given** a metric value is 2,130,500 units
**When** formatted for voice delivery (FR19)
**Then** it reads as "about 2.1 million units"

**Given** a metric value is 87.3%
**When** formatted for voice delivery
**Then** it reads as "87 percent" (not "87.3 percent")

**Given** a dollar amount is $45,230
**When** formatted for voice delivery
**Then** it reads as "about 45 thousand dollars"

**Given** a time duration is 4,320 minutes
**When** formatted for voice delivery
**Then** it reads as "about 72 hours" or "3 days"

**Given** a small precise value is needed (e.g., 5 units)
**When** formatted for voice delivery
**Then** exact value is used: "5 units"

**Technical Notes:**
- Formatting rules:
  - Numbers >1M: "X.X million"
  - Numbers >1K: "X thousand" or "about X thousand"
  - Percentages: round to nearest integer
  - Durations: convert to largest sensible unit
  - Small numbers (<100): use exact values
- Apply formatting in narrative.py before TTS

**Files to Create/Modify:**
- `apps/api/app/services/briefing/narrative.py` - Add `format_for_voice()` function
- `apps/api/app/services/briefing/formatters.py` - Voice formatting utilities

---

### Story 8.7: Area-by-Area Delivery UI

**As a** user,
**I want** a clear visual interface showing briefing progress,
**So that** I can follow along and know what's coming next.

**Acceptance Criteria:**

**Given** a briefing is in progress
**When** viewing the briefing page
**Then** the UI displays:
  - Current section name and progress indicator
  - Text transcript of current section
  - List of upcoming areas (dimmed)
  - Completed areas (checked)
  - Controls: Pause, Skip to Next, End Briefing

**Given** a section is playing
**When** audio completes
**Then** the pause prompt appears
**And** a countdown timer shows silence detection progress

**Given** the user clicks "Skip to Next"
**When** in a section or at a pause
**Then** the current section ends immediately
**And** the next section begins

**Given** the user clicks "End Briefing"
**When** confirmed
**Then** briefing playback stops
**And** user returns to the main briefing page
**And** partial completion is noted in session

**Technical Notes:**
- React state: `useBriefing()` hook manages sections, current index, status
- Progress visualization: stepper component with area names
- Transcript: auto-scroll to current text
- Responsive design: works on tablet (primary) and desktop

**Files to Create/Modify:**
- `apps/web/src/app/(main)/briefing/[id]/page.tsx` - Briefing playback view
- `apps/web/src/components/voice/BriefingPlayer.tsx` - Main player component
- `apps/web/src/components/voice/AreaProgress.tsx` - Progress stepper
- `apps/web/src/lib/hooks/useBriefing.ts` - Briefing state management

---

### Story 8.8: User Preference Onboarding

**As a** first-time user,
**I want** a quick onboarding flow to set my preferences,
**So that** briefings are personalized from my first interaction.

**Acceptance Criteria:**

**Given** a user interacts with the system for the first time (FR42)
**When** onboarding is detected
**Then** the onboarding flow is triggered before the original request
**And** flow completes in under 2 minutes (FR43)

**Given** onboarding begins
**When** the user progresses through steps (FR44)
**Then** the flow includes:
  1. Welcome + explain quick setup
  2. Role selection (Plant Manager or Supervisor)
  3. For Supervisor: display assigned assets (from `supervisor_assignments`)
  4. Area order preference (drag-to-reorder or numbered selection)
  5. Detail level preference (Summary or Detailed)
  6. Voice preference (On/Off)
  7. Confirmation + handoff to original request

**Given** the user completes onboarding
**When** preferences are saved
**Then** preferences are stored in `user_preferences` table
**And** user is redirected to their original destination

**Given** the user abandons onboarding
**When** they close or navigate away
**Then** default preferences are applied
**And** onboarding triggers again on next visit

**Given** a user wants to modify preferences later (FR45)
**When** they navigate to Settings > Preferences
**Then** all onboarding options are available to edit

**Technical Notes:**
- First-time detection: `user_preferences` table has no record for user_id
- Onboarding state: multi-step form with local state
- Supervisor assets: read-only display (admin-configured)
- Area order: drag-and-drop or number input
- Default preferences if abandoned: role=plant_manager, detail=summary, voice=true

**Files to Create/Modify:**
- `apps/web/src/components/onboarding/WelcomeStep.tsx`
- `apps/web/src/components/onboarding/RoleStep.tsx`
- `apps/web/src/components/onboarding/PreferencesStep.tsx`
- `apps/web/src/components/preferences/OnboardingFlow.tsx` - Flow orchestrator
- `apps/web/src/components/preferences/AreaOrderSelector.tsx`
- `apps/web/src/components/preferences/DetailLevelToggle.tsx`
- `apps/web/src/components/preferences/VoiceToggle.tsx`
- `apps/web/src/app/(main)/settings/preferences/page.tsx` - Settings page
- `supabase/migrations/20260115_003_user_preferences.sql` - Create table

---

### Story 8.9: Mem0 Preference Storage

**As a** system component,
**I want** user preferences stored in both Supabase and Mem0,
**So that** preferences are queryable AND available for AI context.

**Acceptance Criteria:**

**Given** a user saves preferences
**When** the save operation completes
**Then** preferences are written to `user_preferences` table immediately (FR40)
**And** relevant context is synced to Mem0 within 5 seconds

**Given** preferences are stored in Mem0
**When** the AI agent processes a request
**Then** Mem0 context includes: "User prefers grinding updates first because that's where most issues occur"
**And** preferences influence response personalization (FR41)

**Given** a user updates their area order
**When** the update is saved
**Then** Supabase record is updated immediately
**And** Mem0 context reflects the change
**And** next briefing uses new order

**Given** the user has a conversation history
**When** preferences sync to Mem0
**Then** the sync includes semantic context about why preferences were set
**And** historical preference versions are maintained (NFR26)

**Technical Notes:**
- Supabase `user_preferences` for structured queries
- Mem0 for AI context enrichment
- Sync pattern: write to Supabase, background job syncs to Mem0
- Mem0 content: semantic descriptions, not just key-value pairs
- Version history: Mem0 naturally maintains versions

**Files to Create/Modify:**
- `apps/api/app/services/preferences/__init__.py` - Package init
- `apps/api/app/services/preferences/service.py` - Preference CRUD
- `apps/api/app/services/preferences/sync.py` - Mem0 sync logic
- `apps/api/app/api/preferences.py` - Preference API endpoints
- `apps/api/app/models/preferences.py` - UserPreferences schema

---

## Epic Acceptance Criteria

- [ ] ElevenLabs TTS begins playback within 2 seconds (NFR9)
- [ ] Push-to-talk transcription completes within 2 seconds (NFR10)
- [ ] Briefing generation completes within 30 seconds (NFR8)
- [ ] Plant Managers see all areas; Supervisors see assigned assets only
- [ ] Numbers formatted for voice (e.g., "2.1 million" not "2,130,500")
- [ ] Users can pause and ask follow-up questions with cited answers
- [ ] Onboarding completes in under 2 minutes
- [ ] Preferences persist across sessions via Supabase + Mem0
- [ ] Voice gracefully degrades to text-only if ElevenLabs unavailable (NFR22)
- [ ] Q&A interactions complete within 2 seconds (NFR7)
