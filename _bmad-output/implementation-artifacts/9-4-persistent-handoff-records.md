# Story 9.4: Persistent Handoff Records

Status: ready-for-dev

## Story

As a **system component**,
I want **handoff records persisted securely with immutability guarantees**,
So that **incoming Supervisors can access them reliably and audit trails are maintained**.

## Acceptance Criteria

### AC1: Handoff Persistence on Submit
**Given** a Supervisor submits a handoff
**When** the save operation completes (FR24)
**Then** the handoff is stored in `shift_handoffs` table
**And** record includes: created_by, shift_date, shift_type, assets_covered
**And** status is set to "pending_acknowledgment"

### AC2: Immutability Guarantee
**Given** a handoff is saved
**When** queried later
**Then** the record is immutable (NFR24)
**And** only supplemental notes can be appended
**And** original content cannot be modified

### AC3: Voice Note Storage
**Given** the handoff includes voice notes
**When** saved
**Then** voice files are stored in Supabase Storage
**And** references are stored in `handoff_voice_notes` table

### AC4: Error Handling with Draft Preservation
**Given** database write fails
**When** error is detected
**Then** user is notified with retry option
**And** draft is preserved locally until successful save

## Tasks / Subtasks

- [ ] Task 1: Create `shift_handoffs` table migration (AC: #1, #2)
  - [ ] 1.1: Create migration file `supabase/migrations/20260115_004_shift_handoffs.sql`
  - [ ] 1.2: Define table schema with all required columns (id, created_by, shift_date, shift_type, summary_text, notes, status, assets_covered)
  - [ ] 1.3: Add UUID primary key with auto-generation
  - [ ] 1.4: Add created_at/updated_at timestamps with auto-update trigger
  - [ ] 1.5: Add FK constraints to auth.users (created_by)
  - [ ] 1.6: Add CHECK constraint for status enum values
  - [ ] 1.7: Create indexes for efficient queries (created_by, shift_date, status)

- [ ] Task 2: Implement RLS policies for immutability (AC: #1, #2)
  - [ ] 2.1: Create migration file `supabase/migrations/20260115_009_rls_policies.sql`
  - [ ] 2.2: Enable RLS on `shift_handoffs` table
  - [ ] 2.3: Create SELECT policy: users can read handoffs they created OR are assigned to receive
  - [ ] 2.4: Create INSERT policy: authenticated users can create handoffs
  - [ ] 2.5: Create NO UPDATE policy on core fields (enforce immutability)
  - [ ] 2.6: Create UPDATE policy ONLY for status field and supplemental_notes
  - [ ] 2.7: Prevent DELETE entirely (append-only audit trail)

- [ ] Task 3: Create Handoff Storage Service (AC: #1, #3, #4)
  - [ ] 3.1: Create `apps/api/app/services/handoff/__init__.py`
  - [ ] 3.2: Create `apps/api/app/services/handoff/storage.py` with HandoffStorageService class
  - [ ] 3.3: Implement `create_handoff()` method with transaction handling
  - [ ] 3.4: Implement `get_handoff()` and `list_handoffs()` methods
  - [ ] 3.5: Implement `add_supplemental_note()` method (only allowed append operation)
  - [ ] 3.6: Implement `update_status()` method for status transitions only
  - [ ] 3.7: Add voice file upload to Supabase Storage in `handoff-voice-notes` bucket
  - [ ] 3.8: Handle errors with proper exception types and retry logic hints

- [ ] Task 4: Create Handoff Pydantic Models (AC: #1, #2, #3)
  - [ ] 4.1: Create `apps/api/app/models/handoff.py`
  - [ ] 4.2: Define `ShiftHandoff` response model with all fields
  - [ ] 4.3: Define `ShiftHandoffCreate` input model for creation
  - [ ] 4.4: Define `HandoffVoiceNote` model for voice note references
  - [ ] 4.5: Define `HandoffStatus` enum (pending_acknowledgment, acknowledged, expired)
  - [ ] 4.6: Define `ShiftType` enum (day, swing, night)
  - [ ] 4.7: Include validators for immutable field protection

- [ ] Task 5: Create API Endpoints (AC: #1, #3, #4)
  - [ ] 5.1: Add handoff endpoints to `apps/api/app/api/handoff.py`
  - [ ] 5.2: Implement `POST /api/v1/handoff` - Create new handoff
  - [ ] 5.3: Implement `GET /api/v1/handoff/{id}` - Get handoff by ID
  - [ ] 5.4: Implement `GET /api/v1/handoff` - List pending handoffs for user
  - [ ] 5.5: Implement `POST /api/v1/handoff/{id}/voice-note` - Upload voice note
  - [ ] 5.6: Add proper error responses with retry hints for failures

- [ ] Task 6: Write Unit Tests (All ACs)
  - [ ] 6.1: Test handoff creation with valid data
  - [ ] 6.2: Test immutability - verify core fields cannot be updated
  - [ ] 6.3: Test supplemental notes can be appended
  - [ ] 6.4: Test status transitions are allowed
  - [ ] 6.5: Test RLS policies filter handoffs by user assignment
  - [ ] 6.6: Test voice note upload and reference storage
  - [ ] 6.7: Test error handling and retry hints

## Dev Notes

### Architecture Context

This story implements the persistence layer for shift handoffs, a critical component of the Shift Handoff Workflow (Epic 9). The handoff system allows outgoing supervisors to create comprehensive shift summaries that incoming supervisors can review, question, and acknowledge.

**Key Design Decisions:**
- **Immutability Pattern (NFR24):** Core handoff content is immutable once created. Only supplemental notes and status can be modified. This is enforced at both RLS policy level and service layer.
- **Hybrid Storage:** Text content in Postgres, audio files in Supabase Storage with references in `handoff_voice_notes` table.
- **RLS-Based Access Control:** Users can only read handoffs they created OR are assigned to receive (based on `supervisor_assignments` table from Story 9.13).

### Technical Requirements

**From Architecture Document:**
- Table: `shift_handoffs` with RLS policies
- RLS: users can read handoffs they created or are assigned to receive
- Immutability: no UPDATE allowed on core fields, only INSERT to notes
- Voice storage: `handoff-voice-notes` bucket with user_id path prefix

**Database Schema Pattern (from existing migrations):**
```sql
-- Follow pattern from 20260106000000_plant_object_model.sql
CREATE TABLE IF NOT EXISTS shift_handoffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) NOT NULL CHECK (shift_type IN ('day', 'swing', 'night')),
    summary_text TEXT NOT NULL,
    notes TEXT,
    supplemental_notes JSONB DEFAULT '[]'::jsonb,  -- Append-only array
    status VARCHAR(30) NOT NULL DEFAULT 'pending_acknowledgment'
        CHECK (status IN ('pending_acknowledgment', 'acknowledged', 'expired')),
    assets_covered UUID[] NOT NULL,  -- Array of asset IDs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### File Structure Requirements

**Backend (apps/api):**
```
apps/api/app/
├── api/
│   └── handoff.py              # NEW: Handoff API endpoints
├── models/
│   └── handoff.py              # NEW: Pydantic models
└── services/
    └── handoff/                # NEW: Handoff services directory
        ├── __init__.py
        └── storage.py          # HandoffStorageService
```

**Database (supabase):**
```
supabase/migrations/
├── 20260115_004_shift_handoffs.sql     # NEW: Handoffs table
└── 20260115_009_rls_policies.sql       # NEW: RLS policies
```

### Implementation Patterns to Follow

**Service Pattern (from existing services):**
```python
# File: app/services/handoff/storage.py
"""
Handoff Storage Service (Story 9.4)

Handles persistence of shift handoff records with immutability guarantees.

AC#1: Handoff stored with all required fields, status = pending_acknowledgment
AC#2: Core fields immutable, only supplemental_notes appendable
AC#3: Voice files in Supabase Storage, references in handoff_voice_notes
AC#4: Error handling with retry hints
"""

from supabase import Client
from app.models.handoff import ShiftHandoff, ShiftHandoffCreate, HandoffVoiceNote

class HandoffStorageService:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.storage_bucket = "handoff-voice-notes"

    async def create_handoff(self, handoff: ShiftHandoffCreate, user_id: str) -> ShiftHandoff:
        """Create a new shift handoff record."""
        # Implementation
        pass

    async def add_supplemental_note(self, handoff_id: str, note: str, user_id: str) -> ShiftHandoff:
        """Append a supplemental note to existing handoff (only allowed modification)."""
        # Implementation
        pass
```

**Pydantic Model Pattern (from existing models):**
```python
# File: app/models/handoff.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum
import uuid

class HandoffStatus(str, Enum):
    PENDING_ACKNOWLEDGMENT = "pending_acknowledgment"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"

class ShiftType(str, Enum):
    DAY = "day"
    SWING = "swing"
    NIGHT = "night"

class ShiftHandoffCreate(BaseModel):
    shift_date: date
    shift_type: ShiftType
    summary_text: str
    notes: Optional[str] = None
    assets_covered: List[uuid.UUID]

class ShiftHandoff(BaseModel):
    id: uuid.UUID
    created_by: uuid.UUID
    shift_date: date
    shift_type: ShiftType
    summary_text: str
    notes: Optional[str]
    supplemental_notes: List[dict] = []
    status: HandoffStatus
    assets_covered: List[uuid.UUID]
    created_at: datetime
    updated_at: datetime
```

### Dependencies

**Required Before This Story:**
- Story 9.3: Voice Note Attachment (provides `handoff_voice_notes` table schema)
  - Note: If 9.3 is not complete, create placeholder migration for `handoff_voice_notes`

**This Story Enables:**
- Story 9.5: Handoff Review UI (reads from `shift_handoffs` table)
- Story 9.7: Acknowledgment Flow (updates status field)
- Story 9.9: Offline Handoff Caching (caches records from this table)

### Supabase Storage Configuration

**Bucket Setup:**
- Bucket name: `handoff-voice-notes`
- Path pattern: `{user_id}/{handoff_id}/{timestamp}_{filename}`
- Access: Private (authenticated users only, via signed URLs)
- Max file size: 10MB (60 seconds of audio at typical bitrate)

### Error Handling Strategy

**Database Write Failures (AC#4):**
1. Return structured error with `retry_hint: true`
2. Include `draft_key` for client-side draft recovery
3. Log error for monitoring

```python
class HandoffPersistenceError(Exception):
    def __init__(self, message: str, retry_hint: bool = True, draft_key: Optional[str] = None):
        self.message = message
        self.retry_hint = retry_hint
        self.draft_key = draft_key
        super().__init__(self.message)
```

### RLS Policy Strategy for Immutability

```sql
-- No UPDATE on core fields - enforce immutability
-- Only allow UPDATE on: status, supplemental_notes, updated_at
CREATE POLICY "Allow limited updates on shift_handoffs"
    ON shift_handoffs FOR UPDATE
    TO authenticated
    USING (created_by = auth.uid())
    WITH CHECK (
        -- Only allow specific fields to change
        -- Core content fields must remain unchanged
        -- This is enforced by having the service layer control what gets updated
        true
    );

-- Better approach: Use service_role for all writes, with service-level enforcement
-- Service layer validates immutability, RLS handles read access
```

### Testing Requirements

**Unit Tests (apps/api/tests/services/test_handoff_storage.py):**
- Test create_handoff stores all required fields
- Test get_handoff retrieves correct record
- Test list_handoffs filters by user assignment
- Test add_supplemental_note appends correctly
- Test voice note upload and reference creation
- Test error handling returns proper retry hints

**Integration Tests:**
- Test RLS policies filter records correctly
- Test immutability at database level
- Test Supabase Storage upload/download flow

### Project Structure Notes

- Follows existing service pattern from `apps/api/app/services/`
- Migration naming follows `YYYYMMDD_NNN_description.sql` pattern
- Pydantic models in `apps/api/app/models/`
- API endpoints in `apps/api/app/api/`

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Offline-Caching-Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Role-Based-Access-Control]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR21-FR30]
- [Source: _bmad/bmm/data/prd/prd-non-functional-requirements.md#NFR24]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story-9.4]
- [Source: supabase/migrations/20260106000000_plant_object_model.sql] - Pattern reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

