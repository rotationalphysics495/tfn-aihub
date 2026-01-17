# Story 9.1: Shift Handoff Trigger

Status: done

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

- [x] **Task 1: Create ShiftHandoff Pydantic Schema** (AC: 1, 2)
  - [x] Create `apps/api/app/models/handoff.py` with ShiftHandoff schema
  - [x] Define fields: id, user_id, shift_date, shift_type, assets_covered, summary, text_notes, status, created_at
  - [x] Add ShiftType enum (morning, afternoon, night)
  - [x] Add HandoffStatus enum (draft, pending_acknowledgment, acknowledged)
  - [x] Export from `apps/api/app/models/__init__.py`

- [x] **Task 2: Create Handoff API Endpoints** (AC: 1, 3, 4)
  - [x] Create `apps/api/app/api/handoff.py` with FastAPI router
  - [x] Implement `POST /api/v1/handoff/` - Create new handoff
  - [x] Implement `GET /api/v1/handoff/` - List user's handoffs
  - [x] Implement `GET /api/v1/handoff/{id}` - Get handoff details
  - [x] Implement `PATCH /api/v1/handoff/{id}` - Update draft handoff
  - [x] Add shift detection logic (based on current time vs standard shift windows)
  - [x] Add duplicate handoff check for same user + shift

- [x] **Task 3: Implement Supervisor Assignment Check** (AC: 3)
  - [x] Query `supervisor_assignments` table to check user's assigned assets
  - [x] Return 400 error with "No assets assigned" message if empty
  - [x] Pre-populate handoff with assigned asset IDs

- [x] **Task 4: Create Handoff Creator Component** (AC: 1, 2)
  - [x] Create `apps/web/src/components/handoff/HandoffCreator.tsx`
  - [x] Implement wizard-style flow with steps:
    - Step 1: Shift confirmation (auto-detected shift, assets list)
    - Step 2: Summary display (auto-generated + editable text notes)
    - Step 3: Voice notes (placeholder for Story 9.3)
    - Step 4: Confirmation
  - [x] Add loading states and error handling

- [x] **Task 5: Create Handoff Page** (AC: 1, 2)
  - [x] Create `apps/web/src/app/(main)/handoff/new/page.tsx`
  - [x] Integrate HandoffCreator component
  - [x] Add route protection (Supervisor role only)
  - [x] Handle redirect after successful creation

- [x] **Task 6: Add Shift Detection Utilities** (AC: 1)
  - [x] Create `apps/api/app/services/handoff/__init__.py`
  - [x] Create `apps/api/app/services/handoff/shift_detection.py`
  - [x] Implement shift window detection:
    - Morning: 6:00 AM - 2:00 PM
    - Afternoon: 2:00 PM - 10:00 PM
    - Night: 10:00 PM - 6:00 AM
  - [x] Calculate shift time range (last 8 hours from current time)

- [x] **Task 7: Handle Existing Handoff Scenario** (AC: 4)
  - [x] Check for existing handoff with same user_id + shift_date + shift_type
  - [x] If exists with status 'draft': redirect to edit
  - [x] If exists with status 'pending_acknowledgment': offer supplemental note option
  - [x] Return appropriate response/redirect

- [x] **Task 8: Write Unit Tests** (AC: 1, 2, 3, 4)
  - [x] Create `apps/api/app/tests/api/test_handoff_endpoints.py`
  - [x] Test create handoff endpoint
  - [x] Test no assets assigned scenario
  - [x] Test duplicate handoff scenario
  - [x] Create `apps/web/src/components/handoff/__tests__/HandoffCreator.test.tsx`
  - [x] Test wizard step navigation
  - [x] Test form validation

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

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 20 backend API tests passing
- All 17 frontend component tests passing

### Completion Notes List

1. **Backend Implementation:**
   - Created `apps/api/app/models/handoff.py` with ShiftHandoff, ShiftType, HandoffStatus schemas
   - Created `apps/api/app/api/handoff.py` with full CRUD endpoints for handoff management
   - Created `apps/api/app/services/handoff/` module with shift detection utilities
   - Integrated handoff router in `apps/api/app/main.py`
   - In-memory handoff storage for MVP (Story 9.4 will add database persistence)

2. **Frontend Implementation:**
   - Created `apps/web/src/components/handoff/HandoffCreator.tsx` - wizard-style handoff creation flow
   - Created `apps/web/src/app/(main)/handoff/new/page.tsx` - handoff creation page
   - Voice notes step shows placeholder (Story 9.3 will implement)
   - Summary auto-generation shows placeholder (Story 9.2 will implement)

3. **Testing:**
   - Created `apps/api/app/tests/api/test_handoff_endpoints.py` with 20 tests
   - Created `apps/web/src/components/handoff/__tests__/HandoffCreator.test.tsx` with 17 tests

4. **Acceptance Criteria Coverage:**
   - AC#1: Handoff creation with pre-populated assets and auto-detected shift - COMPLETE
   - AC#2: Handoff screen with summary, notes, confirmation - COMPLETE (placeholders for 9.2, 9.3)
   - AC#3: No assets assigned error handling - COMPLETE
   - AC#4: Duplicate handoff detection and handling - COMPLETE

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Story created via create-story workflow | Claude Opus 4.5 |
| 2026-01-17 | Implementation complete, all tests passing | Claude Opus 4.5 |
| 2026-01-17 | Code review passed with fixes (7 issues fixed) | Claude Opus 4.5 |

### Code Review Record

**Review Date:** 2026-01-17
**Reviewer:** Claude Opus 4.5 (code-review workflow)
**Result:** PASSED WITH FIXES

**Issues Found and Fixed:**

1. **[HIGH] Security: Missing JWT Authentication on API Endpoints**
   - All endpoints accepted `user_id` as query param, allowing impersonation
   - Fixed: Added `get_current_user` dependency to all endpoints
   - User ID now extracted from JWT token server-side

2. **[HIGH] Security: Frontend Passed user_id in URL**
   - Frontend was sending `user_id` in query string (visible in logs/history)
   - Fixed: Removed user_id from frontend fetch URLs
   - Backend now uses JWT token for user identification

3. **[MEDIUM] Missing input validation on text_notes**
   - Frontend enforced 2000 char limit, backend had none
   - Fixed: Added `max_length=2000` to CreateHandoffRequest.text_notes

4. **[MEDIUM] Test isolation - global state pollution**
   - Tests shared global `_handoffs` dict without cleanup
   - Fixed: Added `@pytest.fixture(autouse=True)` to reset state between tests

5. **[MEDIUM] Improved mock data logging**
   - Mock data was returned silently in production
   - Fixed: Added logging when mock data is returned for transparency

6. **[MEDIUM] Missing export in handoff service**
   - `get_shift_for_handoff` not exported from `__init__.py`
   - Fixed: Added to exports

7. **[LOW] Updated tests to use authentication fixtures**
   - All tests now use `authenticated_client` fixture
   - Tests properly mock JWT authentication

### File List

**New Files Created:**
- `apps/api/app/models/handoff.py` - Pydantic schemas for handoff
- `apps/api/app/api/handoff.py` - FastAPI router with CRUD endpoints
- `apps/api/app/services/handoff/__init__.py` - Handoff services module init
- `apps/api/app/services/handoff/shift_detection.py` - Shift detection utilities
- `apps/api/app/tests/api/test_handoff_endpoints.py` - Backend API tests
- `apps/web/src/components/handoff/HandoffCreator.tsx` - Handoff creation wizard
- `apps/web/src/components/handoff/__tests__/HandoffCreator.test.tsx` - Frontend tests
- `apps/web/src/app/(main)/handoff/new/page.tsx` - Handoff creation page

**Modified Files:**
- `apps/api/app/models/__init__.py` - Added handoff model exports
- `apps/api/app/main.py` - Registered handoff router
