# Story 9.7: Acknowledgment Flow

Status: ready-for-dev

## Story

As an **incoming Supervisor**,
I want **to acknowledge receipt of the handoff**,
So that **there's a clear record of knowledge transfer**.

## Acceptance Criteria

1. **AC1: Acknowledgment UI Trigger**
   - **Given** a Supervisor has reviewed a handoff
   - **When** they click "Acknowledge Handoff" (FR27)
   - **Then** a confirmation dialog appears
   - **And** they can optionally add notes (FR29)

2. **AC2: Acknowledgment Record Creation**
   - **Given** acknowledgment is confirmed
   - **When** the action completes
   - **Then** a record is created in `handoff_acknowledgments`
   - **And** handoff status changes to "acknowledged"
   - **And** timestamp and acknowledging user are recorded
   - **And** audit trail is created (FR55)

3. **AC3: Optional Notes Attachment**
   - **Given** acknowledgment includes notes
   - **When** saved
   - **Then** notes are attached to the acknowledgment record
   - **And** visible to both supervisors

4. **AC4: Offline Acknowledgment Queuing**
   - **Given** a Supervisor tries to acknowledge offline
   - **When** the action is triggered
   - **Then** acknowledgment is queued locally (NFR20)
   - **And** syncs when connectivity is restored (NFR21)
   - **And** user sees "Acknowledgment pending sync"

## Tasks / Subtasks

- [ ] **Task 1: Create handoff_acknowledgments migration** (AC: #2)
  - [ ] 1.1 Create `supabase/migrations/20260115_005_handoff_acknowledgments.sql`
  - [ ] 1.2 Define acknowledgments table with FK to shift_handoffs
  - [ ] 1.3 Add columns: id, handoff_id, acknowledged_by, acknowledged_at, notes
  - [ ] 1.4 Create RLS policies (users can only ack handoffs assigned to them)
  - [ ] 1.5 Create index on handoff_id for efficient lookups

- [ ] **Task 2: Implement HandoffAcknowledge component** (AC: #1, #3)
  - [ ] 2.1 Create `apps/web/src/components/handoff/HandoffAcknowledge.tsx`
  - [ ] 2.2 Implement confirmation dialog with modal pattern
  - [ ] 2.3 Add optional notes textarea with character limit
  - [ ] 2.4 Add loading state and success/error feedback
  - [ ] 2.5 Integrate with handoff viewer page

- [ ] **Task 3: Create acknowledgment API endpoint** (AC: #2)
  - [ ] 3.1 Add `acknowledge_handoff` endpoint to `apps/api/app/api/handoff.py`
  - [ ] 3.2 Validate user authorization (must be assigned to receive this handoff)
  - [ ] 3.3 Create acknowledgment record in database
  - [ ] 3.4 Update handoff status to "acknowledged"
  - [ ] 3.5 Create audit log entry

- [ ] **Task 4: Implement audit trail logging** (AC: #2)
  - [ ] 4.1 Add to existing `audit_logs` table or create if needed
  - [ ] 4.2 Log action_type: "handoff_acknowledged"
  - [ ] 4.3 Include before/after state, user_id, timestamp
  - [ ] 4.4 Ensure append-only (no UPDATE/DELETE permissions)

- [ ] **Task 5: Implement offline queue for acknowledgments** (AC: #4)
  - [ ] 5.1 Create `apps/web/src/lib/offline/sync-queue.ts`
  - [ ] 5.2 Implement IndexedDB storage for queued actions
  - [ ] 5.3 Add action type for "acknowledge_handoff"
  - [ ] 5.4 Implement sync on reconnect via Service Worker
  - [ ] 5.5 Add visual feedback for pending sync status

- [ ] **Task 6: Update HandoffViewer to show acknowledgment state** (AC: #2, #3)
  - [ ] 6.1 Display acknowledgment status on handoff detail page
  - [ ] 6.2 Show acknowledging user and timestamp if acknowledged
  - [ ] 6.3 Show acknowledgment notes if present
  - [ ] 6.4 Disable acknowledge button if already acknowledged

- [ ] **Task 7: Write tests** (AC: All)
  - [ ] 7.1 Unit tests for HandoffAcknowledge component
  - [ ] 7.2 Integration tests for acknowledgment API endpoint
  - [ ] 7.3 Tests for offline queue functionality
  - [ ] 7.4 Tests for RLS policy enforcement

## Dev Notes

### Architecture Compliance

**Backend Pattern (from architecture/implementation-patterns.md):**
- API endpoint goes in `apps/api/app/api/handoff.py`
- Use Pydantic models for request/response schemas
- Follow snake_case naming for Python files
- Include Story/AC references in docstrings

**Frontend Pattern:**
- Component goes in `apps/web/src/components/handoff/HandoffAcknowledge.tsx`
- Use PascalCase for component filenames
- Co-locate tests in `__tests__/` folder
- Use existing dialog/modal patterns from Shadcn/UI

**Database Pattern:**
- Table naming: `handoff_acknowledgments` (snake_case, domain_entity pattern)
- Must include RLS policies for security
- Audit logs are append-only (no UPDATE/DELETE)

### Technical Requirements

**API Endpoint:**
```
POST /api/v1/briefing/handoff/{id}/acknowledge
Body: { notes?: string }
Response: { success: boolean, acknowledgment: AcknowledgmentRecord }
```

**Supabase RLS Policy Logic:**
```sql
-- Users can only acknowledge handoffs assigned to them
-- Check supervisor_assignments table for overlap with handoff assets
CREATE POLICY "Users can acknowledge assigned handoffs" ON handoff_acknowledgments
  FOR INSERT TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM shift_handoffs sh
      JOIN supervisor_assignments sa ON sa.asset_id = ANY(sh.assets_covered)
      WHERE sh.id = handoff_acknowledgments.handoff_id
      AND sa.user_id = auth.uid()
    )
  );
```

**IndexedDB Schema for Offline Queue:**
```typescript
interface QueuedAction {
  id: string;           // UUID for deduplication
  action_type: 'acknowledge_handoff';
  payload: {
    handoff_id: string;
    notes?: string;
  };
  created_at: string;   // ISO timestamp
  synced: boolean;
}
```

### Library & Framework Requirements

| Library | Version | Purpose |
|---------|---------|---------|
| @supabase/supabase-js | Latest | Database operations, RLS |
| idb | ^8.0.0 | IndexedDB wrapper for offline queue |
| Shadcn/UI Dialog | Latest | Confirmation modal pattern |

### File Structure Requirements

**Files to Create:**
```
supabase/migrations/20260115_005_handoff_acknowledgments.sql
apps/web/src/components/handoff/HandoffAcknowledge.tsx
apps/web/src/components/handoff/__tests__/HandoffAcknowledge.test.tsx
apps/web/src/lib/offline/sync-queue.ts
```

**Files to Modify:**
```
apps/api/app/api/handoff.py          # Add acknowledge endpoint
apps/api/app/models/handoff.py       # Add Acknowledgment model
apps/web/src/app/(main)/handoff/[id]/page.tsx  # Integrate ack component
```

### Testing Requirements

**Unit Tests (Jest/React Testing Library):**
- HandoffAcknowledge renders confirmation dialog
- Notes field accepts and validates input
- Submit button disabled while loading
- Success callback triggered on completion

**Integration Tests (pytest):**
- Acknowledgment creates record in database
- Handoff status updates to "acknowledged"
- Audit log entry created
- RLS prevents unauthorized acknowledgment

**E2E Tests (Playwright - if available):**
- Full acknowledgment flow from handoff view
- Offline acknowledgment queues correctly
- Sync occurs on reconnect

### Cross-Story Dependencies

**Depends On (Must Be Complete):**
- Story 9.4: Persistent Handoff Records (shift_handoffs table must exist)
- Story 9.5: Handoff Review UI (HandoffViewer component must exist)

**Enables (Future Stories):**
- Story 9.8: Handoff Notifications (triggers notification on acknowledgment)
- Story 9.9: Offline Handoff Caching (uses sync-queue pattern)

### Project Structure Notes

- Alignment with unified project structure: Uses established patterns for components, API, migrations
- Supabase migrations follow existing naming convention: `20260115_XXX_description.sql`
- Offline support introduces new `lib/offline/` directory (first story to create this)

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Offline Caching Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Role-Based Access Control]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Handoff Component Naming]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story 9.7: Acknowledgment Flow]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

