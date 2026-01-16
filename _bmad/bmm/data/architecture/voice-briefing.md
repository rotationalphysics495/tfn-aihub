# Voice Briefing Extension - Architecture

> **Parent Document:** [architecture.md](../architecture.md)
> **Domain:** Voice Briefing Feature Extension
> **Status:** READY FOR IMPLEMENTATION

---

## 1. Project Context

### Requirements Overview

**Functional Requirements (50 FRs):**
- Voice & Delivery: FR1-FR6 (ElevenLabs TTS/STT, push-to-talk, transcript display)
- Morning Briefing: FR7-FR13 (role-scoped synthesis, wins/concerns highlighting, Q&A)
- Shift Handoff: FR14-FR23 (create, review, acknowledge, offline cache)
- EOD Summary: FR24-FR27 (prediction accuracy feedback loop)
- User Preferences: FR28-FR38 (Mem0 storage, onboarding flow)
- Admin: FR39-FR43 (asset assignment, role management, audit)
- Data & Citations: FR44-FR50 (source tracking, audit trails)

**Non-Functional Requirements (17 NFRs):**
- Performance: <2s Q&A, <30s briefing, <2s TTS start (NFR1-5)
- Reliability: 99.9% uptime during shift changes, offline caching (NFR6-9)
- Integration: Graceful degradation, citation integrity, push notifications (NFR10-13)
- Data Integrity: 15-min data freshness, immutable records, 90-day retention (NFR14-17)

**Scale & Complexity:**
- Primary domain: Full-stack AI Application (brownfield extension)
- Complexity level: Medium-High
- New architectural components: ~8-10

### Technical Constraints & Dependencies

- **Existing Stack:** Next.js 14 + FastAPI + Supabase + LangChain (must integrate cleanly)
- **Voice Provider:** ElevenLabs (TTS + STT) - external API dependency
- **Memory:** Mem0 (already integrated, extended usage for preferences)
- **Offline:** Service Worker + IndexedDB (new frontend capability)
- **Push Notifications:** Web Push API (new infrastructure)

### Cross-Cutting Concerns Identified

1. **Citation Integrity** - LangChain tool composition must preserve source tracking
2. **Role-Based Access Control** - Plant Manager vs Supervisor scoping throughout
3. **Voice/Text Parity** - All voice features have text fallback
4. **Audit Trail** - Handoffs, acknowledgments, admin changes
5. **Performance Budgets** - Strict latency targets across all interactions

---

## 2. Architectural Insights (Party Mode Analysis)

**Dual Delivery Pattern:**
- Text is primary channel (always visible, always reliable)
- Audio is async enhancement via ElevenLabs streaming
- Frontend manages both channels independently
- If audio fails, text continues seamlessly - no user-visible error

**BriefingService Architecture:**
- New dedicated orchestration layer (not LangChain chains)
- Deterministic tool sequencing for predictable narratives
- More testable than LLM-driven tool selection
- Section-based output with natural pause points for Q&A

**Performance Strategy:**
- Leverage existing `daily_summaries` cache (T-1 data, 06:00 AM refresh)
- Briefing generation reads cache, not live MSSQL queries
- LLM narrative formatting ~5-10s on cached data
- 30s budget achievable without real-time database hits

**API Contract Pattern:**
```python
class BriefingResponse(BaseModel):
    sections: List[BriefingSection]  # Text + citations (always present)
    audio_stream_url: Optional[str]  # Nullable = graceful degradation
    total_duration_estimate: int     # For progress UI
```

**Testing Strategy:**
- Nullable `audio_stream_url` enables clean test isolation
- Contract tests for ElevenLabs API compliance
- Chaos testing: kill audio mid-stream, verify text continues
- E2E with mocked external dependencies

---

## 3. Core Architectural Decisions

### Decision Summary Table

| Category | Decision | Rationale |
|----------|----------|-----------|
| **Voice TTS** | Hybrid (Backend URL + Client Stream) | Backend control + client streaming performance, ~300-500ms latency |
| **Voice STT** | ElevenLabs Scribe v2 Realtime | Single vendor, ~150ms WebSocket latency |
| **RBAC** | Hybrid (RLS + Service-Level) | RLS for sensitive data, service-level for complex aggregations |
| **Offline Caching** | Service Worker + IndexedDB | Full control, standard PWA pattern, append-only sync |
| **User Preferences** | Hybrid (Supabase + Mem0) | Structured queries + AI context enrichment |
| **Push Notifications** | Supabase Edge Functions + Web Push | Stays within Supabase ecosystem |
| **Admin UI** | Separate Route Group (`/admin/*`) | Clean separation without separate deployment |

### Voice Integration Architecture

**TTS (Text-to-Speech):**
- Backend generates briefing text via `BriefingService`
- Backend requests ElevenLabs streaming URL (Flash v2.5 model for ~75ms inference)
- Returns `BriefingResponse` with text sections + `audio_stream_url`
- Frontend streams audio directly from ElevenLabs
- If `audio_stream_url` is null, graceful text-only mode

**STT (Speech-to-Text):**
- Frontend maintains WebSocket connection to ElevenLabs Scribe v2 during briefing
- Push-to-talk captures audio, streams to Scribe
- ~150ms transcription latency
- Transcribed text sent to backend for Q&A processing

**Latency Budget:**

| Component | Target | Expected |
|-----------|--------|----------|
| STT (push-to-talk → text) | <2s | ~150-300ms |
| Q&A Processing (text → response) | <2s | ~500-1000ms |
| TTS (text → audio start) | <2s | ~300-500ms |
| **Total Q&A Round-Trip** | <2s | ~1-1.5s |

### Role-Based Access Control

**Database Level (Supabase RLS):**
- `shift_handoffs` - Users can only read handoffs they created or are assigned to receive
- `handoff_acknowledgments` - Users can only create acknowledgments for handoffs assigned to them
- `audit_logs` - Read-only for admins, append-only for system

**Service Level (FastAPI):**
- `BriefingService` filters `daily_summaries` based on user role:
  - Plant Manager: All areas
  - Supervisor: Only assigned assets (from `supervisor_assignments` table)
- FastAPI dependency `get_current_user_with_role()` injects role context

**New Tables Required:**
```sql
-- Supervisor asset assignments (Admin-managed)
CREATE TABLE supervisor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    asset_id UUID REFERENCES assets(id),
    assigned_by UUID REFERENCES auth.users(id),
    assigned_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, asset_id)
);

-- User roles
CREATE TABLE user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    role TEXT CHECK (role IN ('plant_manager', 'supervisor', 'admin')),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### Offline Caching Architecture

**Scope:** Shift handoff records only (Morning Briefing requires live data)

**Implementation:**
- Service Worker registered on app load
- Caches handoff records to IndexedDB on fetch
- Cache invalidation: 48-hour TTL for handoff records
- Sync strategy: Acknowledgments queued in IndexedDB, synced on reconnect

**Sync Flow:**
```
1. User views handoff (online) → cached to IndexedDB
2. User goes offline → can still view cached handoffs
3. User acknowledges handoff (offline) → queued in IndexedDB
4. User reconnects → Service Worker syncs acknowledgment to API
5. Outgoing supervisor receives notification
```

### User Preferences Architecture

**Supabase (`user_preferences` table):**
```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    role TEXT, -- Denormalized for quick access
    area_order TEXT[], -- ['Grinding', 'Packing', ...]
    detail_level TEXT CHECK (detail_level IN ('summary', 'detailed')),
    voice_enabled BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Mem0 (AI Context):**
- Stores semantic preference context: "User prefers grinding updates first because that's where most issues occur"
- Stores interaction history: "User asked about Grinder 5 blade issues last week"
- Used by LangChain agent to personalize responses

**Sync Pattern:**
- On preference change: Write to Supabase immediately
- Background job syncs relevant context to Mem0 within 5 seconds (NFR11)

### Push Notifications Architecture

**Infrastructure:**
- Supabase Edge Function: `send-eod-reminder`
- Triggered by Supabase scheduled job (cron)
- Sends Web Push to subscribed Plant Managers

**Flow:**
```
1. User enables EOD reminders in preferences
2. Frontend requests Web Push permission, stores subscription in Supabase
3. Daily at configured time, Edge Function triggers
4. Edge Function queries users with reminders enabled
5. Sends Web Push via VAPID-signed request
6. Service Worker displays notification
```

### Admin UI Architecture

**Route Structure:**
```
apps/web/src/app/
├── (main)/           # Main user routes
│   ├── briefing/
│   ├── handoff/
│   └── ...
└── (admin)/          # Admin route group
    ├── layout.tsx    # Admin-specific layout with nav
    ├── page.tsx      # Admin dashboard
    ├── users/        # Role management
    └── assignments/  # Supervisor-asset assignments
```

**Access Control:**
- Middleware checks `user_roles.role = 'admin'` for `/admin/*` routes
- Non-admins redirected to main app
- Admin actions logged to `audit_logs` table

---

## 4. Project Structure

### New Backend Structure (apps/api)

```
apps/api/app/
├── api/
│   ├── briefing.py              # NEW: Briefing endpoints
│   ├── handoff.py               # NEW: Shift handoff endpoints
│   ├── voice.py                 # NEW: Voice/TTS/STT endpoints
│   └── admin.py                 # NEW: Admin management endpoints
├── models/
│   ├── briefing.py              # NEW: BriefingResponse, BriefingSection
│   ├── handoff.py               # NEW: ShiftHandoff, Acknowledgment
│   ├── voice.py                 # NEW: TTSRequest, STTResult
│   └── preferences.py           # NEW: UserPreferences, UserRole
├── services/
│   ├── briefing/                # NEW: Briefing orchestration
│   │   ├── __init__.py
│   │   ├── service.py           # BriefingService class
│   │   ├── morning.py           # Morning briefing logic
│   │   ├── handoff.py           # Shift handoff logic
│   │   ├── eod.py               # End of day logic
│   │   └── narrative.py         # LLM narrative formatting
│   ├── voice/                   # NEW: Voice integration
│   │   ├── __init__.py
│   │   ├── elevenlabs.py        # ElevenLabs API client
│   │   ├── tts.py               # TTS stream URL generation
│   │   └── stt.py               # STT WebSocket handler
│   └── preferences/             # NEW: User preferences
│       ├── __init__.py
│       ├── service.py           # Preference CRUD
│       └── sync.py              # Mem0 sync logic
└── tests/
    ├── services/
    │   ├── test_briefing_service.py
    │   ├── test_voice_elevenlabs.py
    │   └── test_preferences_service.py
    └── api/
        ├── test_briefing_endpoints.py
        ├── test_handoff_endpoints.py
        └── test_admin_endpoints.py
```

### New Frontend Structure (apps/web)

```
apps/web/src/
├── app/
│   ├── (main)/                  # Existing main layout
│   │   ├── briefing/            # NEW: Briefing pages
│   │   │   ├── page.tsx         # Morning briefing launcher
│   │   │   └── [id]/page.tsx    # Briefing playback view
│   │   ├── handoff/             # NEW: Shift handoff pages
│   │   │   ├── page.tsx         # Handoff list
│   │   │   ├── new/page.tsx     # Create handoff
│   │   │   └── [id]/page.tsx    # View/acknowledge handoff
│   │   └── settings/            # NEW: User settings
│   │       └── preferences/page.tsx
│   └── (admin)/                 # NEW: Admin route group
│       ├── layout.tsx           # Admin layout with nav
│       ├── page.tsx             # Admin dashboard
│       ├── users/
│       │   ├── page.tsx         # User list with role badges
│       │   └── [id]/page.tsx    # User role management
│       └── assignments/
│           └── page.tsx         # Supervisor-asset grid
├── components/
│   ├── voice/                   # NEW: Voice components
│   │   ├── VoiceControls.tsx
│   │   ├── PushToTalkButton.tsx
│   │   ├── TranscriptPanel.tsx
│   │   ├── BriefingPlayer.tsx
│   │   ├── AudioWaveform.tsx
│   │   └── __tests__/
│   ├── handoff/                 # NEW: Handoff components
│   │   ├── HandoffCreator.tsx
│   │   ├── HandoffViewer.tsx
│   │   ├── HandoffAcknowledge.tsx
│   │   ├── HandoffList.tsx
│   │   ├── HandoffCard.tsx
│   │   ├── VoiceNoteRecorder.tsx
│   │   └── __tests__/
│   ├── admin/                   # NEW: Admin components
│   │   ├── UserRoleTable.tsx
│   │   ├── AssetAssignmentGrid.tsx
│   │   ├── AdminNav.tsx
│   │   └── __tests__/
│   ├── preferences/             # NEW: Preference components
│   │   ├── OnboardingFlow.tsx
│   │   ├── AreaOrderSelector.tsx
│   │   ├── DetailLevelToggle.tsx
│   │   ├── VoiceToggle.tsx
│   │   └── __tests__/
│   └── onboarding/              # NEW: First-time user flow
│       ├── WelcomeStep.tsx
│       ├── RoleStep.tsx
│       ├── PreferencesStep.tsx
│       └── __tests__/
├── lib/
│   ├── offline/                 # NEW: Offline support
│   │   ├── handoff-cache.ts     # IndexedDB for handoffs
│   │   ├── sync-queue.ts        # Offline action queue
│   │   └── sw-registration.ts   # Service Worker lifecycle
│   ├── voice/                   # NEW: Voice utilities
│   │   ├── elevenlabs-client.ts # ElevenLabs streaming
│   │   ├── audio-context.ts     # Web Audio API helpers
│   │   └── push-to-talk.ts      # Recording utilities
│   └── hooks/                   # NEW: Voice hooks
│       ├── useBriefing.ts       # Briefing state management
│       ├── useVoice.ts          # TTS/STT state
│       ├── useHandoff.ts        # Handoff operations
│       └── useOfflineSync.ts    # Offline sync status
└── public/
    └── sw.js                    # NEW: Service Worker
```

### New Database Structure (Supabase)

```
supabase/migrations/
├── 20260115_001_user_roles.sql
├── 20260115_002_supervisor_assignments.sql
├── 20260115_003_user_preferences.sql
├── 20260115_004_shift_handoffs.sql
├── 20260115_005_handoff_acknowledgments.sql
├── 20260115_006_handoff_voice_notes.sql
├── 20260115_007_audit_logs.sql
├── 20260115_008_push_subscriptions.sql
└── 20260115_009_rls_policies.sql

supabase/functions/
└── send-eod-reminder/           # NEW: Edge Function
    └── index.ts
```

---

## 5. Requirements to Structure Mapping

| PRD Feature | Backend Location | Frontend Location | Database |
|-------------|------------------|-------------------|----------|
| **Morning Briefing** | `services/briefing/morning.py` | `app/(main)/briefing/` | `daily_summaries` (existing) |
| **Voice TTS** | `services/voice/tts.py` | `components/voice/BriefingPlayer.tsx` | - |
| **Voice STT** | `services/voice/stt.py` | `components/voice/PushToTalkButton.tsx` | - |
| **Shift Handoff** | `services/briefing/handoff.py` | `app/(main)/handoff/` | `shift_handoffs` |
| **Acknowledgments** | `api/handoff.py` | `components/handoff/HandoffAcknowledge.tsx` | `handoff_acknowledgments` |
| **User Preferences** | `services/preferences/` | `components/preferences/` | `user_preferences` |
| **Onboarding** | - | `components/onboarding/` | `user_preferences` |
| **Admin: Roles** | `api/admin.py` | `app/(admin)/users/` | `user_roles` |
| **Admin: Assignments** | `api/admin.py` | `app/(admin)/assignments/` | `supervisor_assignments` |
| **Offline Caching** | - | `lib/offline/` | IndexedDB (client) |
| **Push Notifications** | `supabase/functions/` | `lib/offline/sw-registration.ts` | `push_subscriptions` |

---

## 6. Integration Boundaries

**API Boundaries:**
```
/api/v1/briefing/*     → BriefingService (orchestrates tools)
/api/v1/voice/*        → ElevenLabs integration
/api/v1/handoff/*      → Handoff CRUD with RLS
/api/v1/admin/*        → Admin-only with role check
/api/v1/preferences/*  → User preference CRUD
```

**Data Flow:**
```
Morning Briefing:
User Request → BriefingService → [OEE, Downtime, Safety tools]
            → daily_summaries cache → LLM narrative
            → ElevenLabs TTS URL → Frontend dual delivery

Shift Handoff:
Outgoing Creates → shift_handoffs (RLS) → Notification
            → Incoming Reviews (offline capable)
            → Acknowledgment → audit_logs
```

---

## Related Documents

- **Parent:** [architecture.md](../architecture.md) - Core platform architecture
- **Patterns:** [implementation-patterns.md](./implementation-patterns.md) - Code patterns & consistency rules
- **Validation:** [validation-results.md](./validation-results.md) - Architecture validation & readiness
