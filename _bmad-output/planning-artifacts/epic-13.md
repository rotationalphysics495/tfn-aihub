---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "docs/improvements.md"
  - "docs/architecture-api.md"
  - "docs/architecture-web.md"
  - "docs/data-models.md"
epic: 13
status: "ready"
---

# Epic 13: Action Accountability Loop

## Overview

**Goal:** Plant managers can acknowledge action items, track follow-up assignments with status visibility, and see at a glance which items are being worked on and by whom — closing the accountability gap.

**Dependencies:** Uses existing `action_followups` table (migration 0025)

**User Value:** The morning report goes from a "newspaper you read and throw away" to an accountability system. Managers see assignment badges, assignees update status, and the "My Assignments" panel shows everything in one place.

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| FR-I4 (Action Item Acknowledgment) | Full |
| FR-I5 (Follow-Up Status Tracking) | Full |
| NFR-I3 (Audit Trail) | Partial (acknowledgment + follow-up tracking) |
| NFR-I8 (RLS Compliance) | Full |

## Stories

---

### Story 13.1: Action Acknowledgment Backend

**As a** Plant Manager,
**I want** to mark action items as reviewed/completed with the acknowledgment persisted,
**So that** there's a record of what I've seen and addressed.

**Acceptance Criteria:**

**Given** an authenticated user sends `POST /api/v1/actions/{action_id}/acknowledge`
**When** the request includes an optional note
**Then** a record is created in `action_acknowledgments` with:
  - `action_item_id` (the action being acknowledged)
  - `user_id` (who acknowledged it)
  - `acknowledged_at` (timestamp)
  - `note` (optional text)
**And** the response includes the created acknowledgment record

**Given** an action item has already been acknowledged by this user
**When** the acknowledge endpoint is called again
**Then** the existing acknowledgment is updated (upsert behavior)
**And** the timestamp is refreshed

**Given** the daily actions endpoint is called
**When** acknowledged action items exist for the current date
**Then** each action item includes an `acknowledgment` field with who acknowledged it and when (or null if unacknowledged)

**Technical Notes:**
- New migration: `supabase/migrations/0027_action_acknowledgments.sql`
- Table: `action_acknowledgments` with columns: `id`, `action_item_id` (TEXT), `user_id` (UUID FK), `acknowledged_at` (TIMESTAMPTZ), `note` (TEXT), `report_date` (DATE)
- Unique constraint on (action_item_id, user_id, report_date)
- RLS: users can read/write their own acknowledgments, service role full access

**Files to Create/Modify:**
- `supabase/migrations/0027_action_acknowledgments.sql` - New table
- `apps/api/app/api/actions.py` - Add acknowledge endpoint
- `apps/api/app/schemas/action.py` - Add acknowledgment schemas
- `apps/api/app/services/action_engine.py` - Enrich action items with acknowledgment status

---

### Story 13.2: Action Acknowledgment UI

**As a** Plant Manager,
**I want** a checkbox or button on each action card to mark it as reviewed,
**So that** I can track which items I've addressed during my morning review.

**Acceptance Criteria:**

**Given** the morning report displays action items
**When** each action card renders
**Then** it shows an acknowledgment button/checkbox (unacknowledged state)

**Given** the user clicks the acknowledge button on an action card
**When** the acknowledgment API is called
**Then** the button immediately updates to "acknowledged" state (optimistic UI)
**And** the card visually changes (e.g., muted styling or checkmark overlay)
**And** a timestamp shows when it was acknowledged

**Given** an action item was previously acknowledged
**When** the morning report reloads
**Then** the acknowledged state is preserved from the database

**Given** all action items are acknowledged
**When** the action list renders
**Then** a summary shows "All items reviewed" with a count

**Technical Notes:**
- Update `InsightEvidenceCard` or `ActionItemCard` component to include acknowledgment UI
- Optimistic update pattern: update UI immediately, confirm with API
- Use existing Shadcn/UI `Checkbox` or `Button` component

**Files to Create/Modify:**
- `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` - Add acknowledge button
- `apps/web/src/hooks/useActionAcknowledgment.ts` - Acknowledgment API hook with optimistic updates
- `apps/web/src/components/action-list/ActionItemCard.tsx` - Add acknowledge button (if used here too)

---

### Story 13.3: Follow-Up Status Updates & RLS

**As a** team member assigned a follow-up,
**I want** to update the status of my assignment (in-progress, resolved) with a note,
**So that** the manager can see progress without asking in person.

**Acceptance Criteria:**

**Given** an assignee is authenticated and has follow-ups assigned to them
**When** they call `PATCH /api/v1/followups/{followup_id}` with `status` and optional `note`
**Then** the follow-up status is updated in `action_followups`
**And** the `updated_at` timestamp is refreshed
**And** only the fields provided are updated (partial update)

**Given** an assignee tries to update a follow-up not assigned to them
**When** the update request is made
**Then** the request is denied with 403 (RLS enforcement)

**Given** a manager queries follow-ups they created
**When** the follow-up has been updated by the assignee
**Then** the response includes the current status and the assignee's note

**Technical Notes:**
- Update RLS on `action_followups` to allow assignees UPDATE access on their own records
- New RLS policy: `"Assignees can update their own followups"` with `USING (assigned_to = auth.uid())`
- New endpoint: `PATCH /api/v1/followups/{followup_id}`

**Files to Create/Modify:**
- `supabase/migrations/0028_followup_assignee_rls.sql` - Add assignee UPDATE policy
- `apps/api/app/api/actions.py` - Add follow-up update endpoint
- `apps/api/app/schemas/action.py` - Add follow-up update schema

---

### Story 13.4: Assignment Badge on Action Cards

**As a** Plant Manager,
**I want** to see who is assigned to each action item directly on the action card,
**So that** during meetings I know at a glance which items are already being investigated.

**Acceptance Criteria:**

**Given** an action item has a follow-up assigned
**When** the action card renders
**Then** a badge shows on the card with the assignee's name and current status
**And** the badge is color-coded: blue (assigned), amber (in-progress), green (resolved)

**Given** an action item has no follow-up assigned
**When** the action card renders
**Then** no assignment badge is shown
**And** the "Assign Follow-Up" button remains prominent

**Given** multiple follow-ups exist for the same action item (reassigned)
**When** the card renders
**Then** the most recent active follow-up is shown

**Technical Notes:**
- Fetch follow-up data alongside action items (join or separate query)
- Display as a Shadcn/UI `Badge` component on the action card
- Match follow-ups to action items via `action_item_id`

**Files to Create/Modify:**
- `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` - Add assignment badge
- `apps/web/src/components/action-engine/AssignmentBadge.tsx` - New badge component
- `apps/web/src/hooks/useFollowUps.ts` - Hook to fetch follow-up data for action items

---

### Story 13.5: "My Assignments" Panel

**As a** Plant Manager,
**I want** a panel on the morning report showing all open follow-ups I've created, grouped by status,
**So that** I can track assignment progress without leaving the report.

**Acceptance Criteria:**

**Given** the manager has created follow-up assignments
**When** the "My Assignments" panel is visible on the morning report
**Then** it shows all follow-ups grouped by status:
  - **Assigned** (blue) — awaiting action
  - **In Progress** (amber) — assignee is working on it
  - **Resolved** (green) — assignee has completed investigation
**And** each entry shows: asset name, action summary, assignee name, time since assigned

**Given** a follow-up was recently updated by the assignee
**When** the panel refreshes
**Then** the follow-up moves to its new status group
**And** a "New update" indicator appears if the manager hasn't viewed the update yet

**Given** the manager clicks on a follow-up entry
**When** the detail view opens
**Then** it shows the full assignment context: original action item, assigned note, assignee's status updates with timestamps

**Given** the manager has no open follow-ups
**When** the panel renders
**Then** it shows an empty state: "No open follow-ups. Assign actions from the report below."

**Technical Notes:**
- New component in `apps/web/src/components/action-list/`
- Fetch via `GET /api/v1/followups?assigned_by=me&status=active`
- Position: sidebar panel or collapsible section on morning report page
- Consider using Shadcn/UI `Sheet` or `Collapsible`

**Files to Create/Modify:**
- `apps/web/src/components/action-list/MyAssignmentsPanel.tsx` - Main panel component
- `apps/web/src/components/action-list/FollowUpEntry.tsx` - Individual follow-up entry
- `apps/web/src/hooks/useMyFollowUps.ts` - Hook to fetch manager's follow-ups
- `apps/api/app/api/actions.py` - Add follow-ups list endpoint with filters
- `apps/web/src/app/morning-report/page.tsx` - Integrate panel
