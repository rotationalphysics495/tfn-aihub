# Story 9.1: Shift Handoff Trigger

Status: ready-for-dev

## Story

As an **outgoing Supervisor**,
I want **to initiate a shift handoff process**,
so that **I can transfer knowledge to the incoming shift**.

## Acceptance Criteria

1. **Given** an outgoing Supervisor is ending their shift, **When** they select "Create Shift Handoff" (FR21), **Then** the handoff creation flow begins **And** the system pre-populates with their assigned assets **And** shift time range is auto-detected (last 8 hours).

2. **Given** the handoff flow starts, **When** the Supervisor views the handoff screen, **Then** they see:
   - Auto-generated shift summary (from tools)
   - Option to add voice notes
   - Option to add text notes
   - Confirmation button

3. **Given** the Supervisor has no assigned assets, **When** they try to create a handoff, **Then** the system displays "No assets assigned - contact your administrator" **And** no handoff can be created.

4. **Given** a handoff already exists for this shift, **When** the Supervisor tries to create another, **Then** they are prompted to edit the existing handoff **Or** create a supplemental note.

## Tasks / Subtasks

- [ ] **Task 1: Create ShiftHandoff Pydantic Schema** (AC: 1, 2)
  - [ ] Create `apps/api/app/models/handoff.py` with ShiftHandoff schema
  - [ ] Define fields: id, user_id, shift_date, shift_type, assets_covered, summary, text_notes, status, created_at
  - [ ] Add ShiftType enum (morning, afternoon, night)
  - [ ] Add HandoffStatus enum (draft, pending_acknowledgment, acknowledged)
  - [ ] Export from `apps/api/app/models/__init__.py`

- [ ] **Task 2: Create Handoff API Endpoints** (AC: 1, 3, 4)
  - [ ] Create `apps/api/app/api/handoff.py` with FastAPI router
  - [ ] Implement `POST /api/v1/handoff/` - Create new handoff
  - [ ] Implement `GET /api/v1/handoff/` - List user's handoffs
  - [ ] Implement `GET /api/v1/handoff/{id}` - Get handoff details
  - [ ] Implement `PATCH /api/v1/handoff/{id}` - Update draft handoff
  - [ ] Add shift detection logic (based on current time vs standard shift windows)
  - [ ] Add duplicate handoff check for same user + shift

- [ ] **Task 3: Implement Supervisor Assignment Check** (AC: 3)
  - [ ] Query `supervisor_assignments` table to check user's assigned assets
  - [ ] Return 400 error with "No assets assigned" message if empty
  - [ ] Pre-populate handoff with assigned asset IDs

- [ ] **Task 4: Create Handoff Creator Component** (AC: 1, 2)
  - [ ] Create `apps/web/src/components/handoff/HandoffCreator.tsx`
  - [ ] Implement wizard-style flow with steps:
    - Step 1: Shift confirmation (auto-detected shift, assets list)
    - Step 2: Summary display (auto-generated + editable text notes)
    - Step 3: Voice notes (placeholder for Story 9.3)
    - Step 4: Confirmation
  - [ ] Add loading states and error handling

- [ ] **Task 5: Create Handoff Page** (AC: 1, 2)
  - [ ] Create `apps/web/src/app/(main)/handoff/new/page.tsx`
  - [ ] Integrate HandoffCreator component
  - [ ] Add route protection (Supervisor role only)
  - [ ] Handle redirect after successful creation

- [ ] **Task 6: Add Shift Detection Utilities** (AC: 1)
  - [ ] Create `apps/api/app/services/handoff/__init__.py`
  - [ ] Create `apps/api/app/services/handoff/shift_detection.py`
  - [ ] Implement shift window detection:
    - Morning: 6:00 AM - 2:00 PM
    - Afternoon: 2:00 PM - 10:00 PM
    - Night: 10:00 PM - 6:00 AM
  - [ ] Calculate shift time range (last 8 hours from current time)

- [ ] **Task 7: Handle Existing Handoff Scenario** (AC: 4)
  - [ ] Check for existing handoff with same user_id + shift_date + shift_type
  - [ ] If exists with status 'draft': redirect to edit
  - [ ] If exists with status 'pending_acknowledgment': offer supplemental note option
  - [ ] Return appropriate response/redirect

- [ ] **Task 8: Write Unit Tests** (AC: 1, 2, 3, 4)
  - [ ] Create `apps/api/app/tests/api/test_handoff_endpoints.py`
  - [ ] Test create handoff endpoint
  - [ ] Test no assets assigned scenario
  - [ ] Test duplicate handoff scenario
  - [ ] Create `apps/web/src/components/handoff/__tests__/HandoffCreator.test.tsx`
  - [ ] Test wizard step navigation
  - [ ] Test form validation

## Dev Notes

### Architecture & Pattern Compliance

- **Backend Pattern:** Follow FastAPI router pattern from existing `apps/api/app/api/` modules
- **Frontend Pattern:** Follow component structure from `apps/web/src/components/` with `__tests__/` co-location
- **Database:** Uses Supabase PostgreSQL with RLS policies
- **API Authentication:** All endpoints protected via Supabase Auth (JWT validation in FastAPI dependency)

### Relevant Architecture Decisions

From `_bmad/bmm/data/architecture/voice-briefing.md`:
- Shift handoffs use hybrid RBAC (RLS for data access + service-level filtering)
- Handoff records stored in `shift_handoffs` table with RLS policies
- Service Worker + IndexedDB for offline handoff caching (future Story 9.9)

### Database Schema (To Be Created in Story 9.4)

Note: Database migrations will be created in Story 9.4 (Persistent Handoff Records). This story assumes the following schema exists or uses in-memory/mock data for initial development:

```sql
-- From architecture/voice-briefing.md
CREATE TABLE shift_handoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    shift_date DATE NOT NULL,
    shift_type TEXT CHECK (shift_type IN ('morning', 'afternoon', 'night')) NOT NULL,
    assets_covered UUID[] NOT NULL, -- Array of asset IDs
    summary TEXT, -- Auto-generated summary
    text_notes TEXT, -- User-added notes
    status TEXT CHECK (status IN ('draft', 'pending_acknowledgment', 'acknowledged')) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, shift_date, shift_type)
);

-- Supervisor assignments (may already exist from Epic 8)
CREATE TABLE supervisor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    asset_id UUID REFERENCES assets(id),
    assigned_by UUID REFERENCES auth.users(id),
    assigned_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, asset_id)
);
```

### Project Structure Notes

Files to create:
```
apps/api/app/
├── api/
│   └── handoff.py              # NEW: Handoff API endpoints
├── models/
│   └── handoff.py              # NEW: ShiftHandoff, HandoffStatus schemas
├── services/
│   └── handoff/                # NEW: Handoff service module
│       ├── __init__.py
│       └── shift_detection.py  # Shift time utilities
└── tests/
    └── api/
        └── test_handoff_endpoints.py

apps/web/src/
├── app/
│   └── (main)/
│       └── handoff/
│           └── new/
│               └── page.tsx    # NEW: Create handoff page
└── components/
    └── handoff/                # NEW: Handoff components
        ├── HandoffCreator.tsx
        └── __tests__/
            └── HandoffCreator.test.tsx
```

### API Endpoint Patterns

Following established pattern from `_bmad/bmm/data/architecture/implementation-patterns.md`:

```
POST /api/v1/handoff/              # Create new shift handoff
GET  /api/v1/handoff/              # List current user's handoffs
GET  /api/v1/handoff/{id}          # Get handoff by ID
PATCH /api/v1/handoff/{id}         # Update draft handoff
```

### Shift Detection Logic

Standard shift windows (configurable):
- **Morning Shift:** 6:00 AM - 2:00 PM (8 hours)
- **Afternoon Shift:** 2:00 PM - 10:00 PM (8 hours)
- **Night Shift:** 10:00 PM - 6:00 AM (8 hours)

Detection algorithm:
1. Get current time
2. Determine which shift window the current time falls into
3. Calculate shift start time as 8 hours before current time
4. Return shift_type and time_range for handoff scope

### Dependencies on Previous Epics

- **Epic 5-7:** LangChain agent tools for generating shift summary (used in Story 9.2)
- **Epic 8:** Voice infrastructure patterns (TTS/STT for voice notes in Story 9.3)
- **Existing tables:** `assets`, `supervisor_assignments` (may need creation if not existing)

### Frontend Wizard Flow

```
Step 1: Shift Confirmation
├── Display detected shift type (Morning/Afternoon/Night)
├── Display shift time range (e.g., "2:00 PM - 10:00 PM")
├── List assigned assets with checkboxes (all selected by default)
└── "Next" button

Step 2: Shift Summary
├── Auto-generated summary (loading state initially)
├── Summary preview (read-only or placeholder for Story 9.2)
├── Text notes textarea (optional)
└── "Next" / "Back" buttons

Step 3: Voice Notes (Placeholder)
├── "Add Voice Note" button (disabled - Story 9.3)
├── List of attached voice notes (empty)
└── "Next" / "Back" buttons

Step 4: Confirmation
├── Review all information
├── "Submit Handoff" button
└── Success/Error handling
```

### Error Handling

| Scenario | Response |
|----------|----------|
| No assigned assets | 400: "No assets assigned - contact your administrator" |
| Duplicate handoff (draft) | 409: Redirect to edit existing |
| Duplicate handoff (submitted) | 409: Offer supplemental note option |
| Database error | 500: Generic error with retry |
| Auth failure | 401: Redirect to login |

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Shift-Handoff-Workflow]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR21-FR30]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Handoff-Component-Naming]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story-9.1]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Story created via create-story workflow | Claude Opus 4.5 |

### File List
