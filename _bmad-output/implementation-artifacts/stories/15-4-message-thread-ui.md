# Story 15.4: Message Thread UI

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Plant Manager,
I want to see the full conversation thread for a follow-up (what was sent, what was replied, when),
so that I can review the assignee's findings without leaving the app.

## Acceptance Criteria

1. **Given** a follow-up has messages (outbound notification + inbound response), **When** the manager views the follow-up detail (from My Assignments panel or action card), **Then** a chronological message thread is displayed showing:
   - Assignment notification: "Sent to {assignee} at {time}" with the original message
   - Response: "{assignee} replied at {time}" with the response text
   - Status updates: "{assignee} marked as in-progress at {time}"

2. **Given** a response has come in that the manager hasn't viewed, **When** the My Assignments panel shows, **Then** an unread indicator (badge/dot) appears on the follow-up entry.

3. **Given** a follow-up has no responses yet, **When** the thread view is opened, **Then** only the outbound notification is shown, **And** a note appears: "Awaiting response from {assignee_name}".

4. **Given** the messages API endpoint is called, **When** a valid follow-up ID is provided, **Then** messages are returned in chronological order with sender info, direction, message type, subject, body, and timestamps.

5. **Given** the user does not have access to the follow-up (neither assigner nor assignee), **When** the messages endpoint is called, **Then** an empty result or 403 is returned (RLS enforced).

## Tasks / Subtasks

- [ ] Task 1: Create Messages API Endpoint (AC: #4, #5)
  - [ ] 1.1 Add `GET /api/v1/followups/{id}/messages` route in `apps/api/app/api/followups.py`
  - [ ] 1.2 Create Pydantic response models: `FollowUpMessageResponse`, `FollowUpMessageListResponse` in `apps/api/app/schemas/followup.py`
  - [ ] 1.3 Query `followup_messages` table joined with `action_followups` for context
  - [ ] 1.4 Return messages sorted by `sent_at` ascending (chronological)
  - [ ] 1.5 RLS ensures only assigner/assignee can read (enforced at DB level via existing policy from Story 15.1)
  - [ ] 1.6 Include sender display info (email, role if available)
  - [ ] 1.7 Write pytest tests for the endpoint

- [ ] Task 2: Create `useFollowUpMessages` Hook (AC: #1, #3)
  - [ ] 2.1 Create `apps/web/src/hooks/useFollowUpMessages.ts`
  - [ ] 2.2 Fetch from `GET /api/v1/followups/{id}/messages` with auth token
  - [ ] 2.3 Return typed messages array, loading state, error state, and refetch function
  - [ ] 2.4 Follow existing hook pattern from `useDailyActions.ts`: Supabase auth session, Bearer token, error message mapping

- [ ] Task 3: Create `MessageThread` Component (AC: #1, #3)
  - [ ] 3.1 Create `apps/web/src/components/action-list/MessageThread.tsx`
  - [ ] 3.2 Render chronological message list with chat-style alternating alignment:
    - Outbound (sent) messages aligned right with muted background
    - Inbound (received) messages aligned left with card background
  - [ ] 3.3 Display message metadata: sender name/email, timestamp, message type badge
  - [ ] 3.4 Handle empty state: show "Awaiting response from {assignee_name}" when no inbound messages exist
  - [ ] 3.5 Use Shadcn/UI components (Card, Badge, ScrollArea) and Tailwind for styling
  - [ ] 3.6 Follow Industrial Clarity Design System: 18px minimum body text, Inter font
  - [ ] 3.7 Support loading skeleton state
  - [ ] 3.8 Accessible: proper ARIA roles (role="log", aria-label for messages)

- [ ] Task 4: Create `FollowUpEntry` Component with Unread Indicator (AC: #2)
  - [ ] 4.1 Create `apps/web/src/components/action-list/FollowUpEntry.tsx`
  - [ ] 4.2 Display follow-up summary: action summary, assignee, status, created date
  - [ ] 4.3 Add unread indicator (blue dot/badge) when latest inbound message `sent_at` > `last_viewed_at`
  - [ ] 4.4 On click/expand, show the `MessageThread` component for that follow-up
  - [ ] 4.5 Update `last_viewed_at` when thread is opened (via API PATCH or Supabase direct update)

- [ ] Task 5: Integrate into Existing Follow-Up Views (AC: #1, #2)
  - [ ] 5.1 Update `apps/web/src/components/action-list/index.ts` barrel exports to include new components
  - [ ] 5.2 Integrate `FollowUpEntry` into the action card detail view where follow-ups are shown
  - [ ] 5.3 Ensure the thread is accessible from the action card drill-down (Story 3.4 flow)

- [ ] Task 6: Add `last_viewed_at` Tracking (AC: #2)
  - [ ] 6.1 Add migration `supabase/migrations/0031_followup_last_viewed.sql` to add `last_viewed_at TIMESTAMPTZ` column to `action_followups` table
  - [ ] 6.2 Add `PATCH /api/v1/followups/{id}/viewed` endpoint to update `last_viewed_at`
  - [ ] 6.3 Call viewed endpoint when thread is opened in the UI

- [ ] Task 7: Testing (AC: #1-5)
  - [ ] 7.1 Backend: pytest for `GET /api/v1/followups/{id}/messages` (auth, RLS, empty, populated)
  - [ ] 7.2 Backend: pytest for `PATCH /api/v1/followups/{id}/viewed`
  - [ ] 7.3 Frontend: Vitest + Testing Library for `MessageThread` (renders messages, empty state, loading)
  - [ ] 7.4 Frontend: Vitest + Testing Library for `FollowUpEntry` (unread indicator, click expand)

## Dev Notes

### Architecture & Patterns

- **Backend Framework:** FastAPI 0.109+ with async endpoints. Follow existing router pattern in `apps/api/app/api/actions.py`.
- **Frontend Framework:** Next.js 14 App Router, TypeScript 5.x, Tailwind CSS 3.4+, Shadcn/UI (Radix primitives).
- **Database:** Supabase PostgreSQL with RLS. The `followup_messages` table is created by Story 15.1 (migration `0030_followup_messages.sql`). The `action_followups` table already exists (migration `0025_action_followups.sql`).
- **Auth Pattern:** JWT via Supabase session. Frontend hooks get token from `createClient()` + `getSession()`. Backend uses `get_current_user` dependency.
- **API Pattern:** Prefix routes under `/api/v1/followups`. Use `Depends(get_current_user)` for auth. Return Pydantic models.

### Critical Dependencies (from Earlier Stories in Epic 15)

- **Story 15.1 (Follow-Up Messages Data Model):** MUST exist before this story. Creates `followup_messages` table with columns: `id`, `followup_id`, `sender_id`, `sender_email`, `direction` (outbound/inbound), `message_type` (assignment/response/escalation/status_update), `subject`, `body`, `sent_at`, `created_at`. Indexes on `followup_id`, `direction`, `sent_at`. RLS: assigner and assignee can read.
- **Story 15.2 (Email Notification Service):** Creates outbound `followup_messages` records when follow-ups are assigned.
- **Story 15.3 (Response Capture via Token Link):** Creates inbound `followup_messages` records when assignees respond.
- **Epic 13 (Follow-Up Assignments):** The `action_followups` table (migration `0025`) with FK relationships. Already in codebase.

### Existing Code to Reuse (DO NOT Reinvent)

- **Hook pattern:** Follow `apps/web/src/hooks/useDailyActions.ts` exactly for auth, fetch, error handling, state management. Uses `createClient()` from `@/lib/supabase/client`, `getSession()` for token, `mountedRef` pattern for cleanup.
- **Component patterns:** Follow `apps/web/src/components/action-list/ActionItemCard.tsx` for card layout, priority styling, accessibility (ARIA roles, keyboard navigation).
- **Shadcn/UI components:** Import from `@/components/ui/` -- Card, CardContent, Badge, ScrollArea, Button. Already available.
- **Utility:** `cn()` from `@/lib/utils` for conditional classnames.
- **Icons:** Import from `lucide-react` (e.g., `MessageSquare`, `Send`, `Mail`, `Clock`, `Eye`).
- **API security:** Follow `apps/api/app/api/actions.py` pattern for `Depends(get_current_user)`, `CurrentUser` model import.
- **Supabase client (backend):** Use `supabase-py 2.0+` for queries. The `from('followup_messages').select().eq('followup_id', id).order('sent_at')` pattern.
- **AssignFollowUpDialog:** Reference `apps/web/src/components/action-engine/AssignFollowUpDialog.tsx` for how follow-ups are created and displayed.

### API Endpoint Specifications

**`GET /api/v1/followups/{followup_id}/messages`**
- Auth: Required (Bearer token)
- Path param: `followup_id` (UUID)
- Response 200:
```json
{
  "followup_id": "uuid",
  "action_summary": "string",
  "assignee_name": "string",
  "assignee_email": "string",
  "status": "assigned|in_progress|resolved",
  "messages": [
    {
      "id": "uuid",
      "direction": "outbound|inbound",
      "message_type": "assignment|response|escalation|status_update",
      "sender_email": "string",
      "subject": "string",
      "body": "string",
      "sent_at": "ISO datetime"
    }
  ],
  "has_unread": false,
  "last_viewed_at": "ISO datetime | null"
}
```
- Response 404: Follow-up not found or not accessible (RLS)

**`PATCH /api/v1/followups/{followup_id}/viewed`**
- Auth: Required (Bearer token)
- Response 200: `{ "success": true, "last_viewed_at": "ISO datetime" }`

### Database Changes

- **New column on `action_followups`:** `last_viewed_at TIMESTAMPTZ DEFAULT NULL`
- Migration file: `supabase/migrations/0031_followup_last_viewed.sql`
- No new RLS policies needed for this column -- existing `action_followups` policies cover it.

### Unread Logic

- A follow-up has unread messages when: there exists at least one `followup_messages` record with `direction = 'inbound'` AND `sent_at > COALESCE(action_followups.last_viewed_at, '1970-01-01')`.
- The `has_unread` field in the messages response should be computed server-side.
- When the thread is opened, the client calls `PATCH /api/v1/followups/{id}/viewed` to update `last_viewed_at = NOW()`.

### UI Layout Specification

- **Message Thread (chat-style):**
  - Container: `ScrollArea` with max-height for scrollable thread
  - Outbound messages: right-aligned, `bg-industrial-100 dark:bg-industrial-800` background, rounded corners
  - Inbound messages: left-aligned, `bg-card` border, rounded corners
  - Each message shows: sender label, timestamp (relative, e.g., "2h ago"), message body
  - Message type badges: "Assignment" (blue), "Response" (green), "Status Update" (gray)
  - Empty state: centered text "Awaiting response from {name}" with `Clock` icon

- **FollowUpEntry:**
  - Card-based layout showing: action summary (truncated), assignee email, status badge, date
  - Unread indicator: small blue dot (8px circle, `bg-info-blue`) positioned top-right of entry
  - Click to expand/collapse the `MessageThread` inline

### Testing Standards

- **Backend (pytest):** Tests in `apps/api/tests/`. Mock Supabase client. Test: auth required, returns messages for valid follow-up, returns 404 for inaccessible, chronological ordering, viewed endpoint updates timestamp.
- **Frontend (Vitest + Testing Library):** Tests in component `__tests__/` directories. Test: MessageThread renders messages correctly, shows empty state, shows loading skeleton. FollowUpEntry shows unread dot, hides when no unread, expands thread on click.

### Project Structure Notes

- All new frontend components go in `apps/web/src/components/action-list/` (the follow-up thread is part of the action list domain).
- New hook goes in `apps/web/src/hooks/` following existing convention.
- New API router file `apps/api/app/api/followups.py` must be registered in `apps/api/app/main.py` with prefix `/api/v1/followups`.
- New schema file `apps/api/app/schemas/followup.py` for Pydantic models.
- Migration numbering: `0031_*` follows after `0030_followup_messages.sql` from Story 15.1.

### References

- [Source: _bmad-output/planning-artifacts/epic-15.md#Story 15.4]
- [Source: docs/architecture-web.md#Component Architecture]
- [Source: docs/architecture-api.md#API Endpoints]
- [Source: docs/architecture-api.md#Security]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: supabase/migrations/0025_action_followups.sql]
- [Source: apps/web/src/hooks/useDailyActions.ts]
- [Source: apps/web/src/components/action-list/ActionItemCard.tsx]
- [Source: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx]
- [Source: apps/web/src/components/action-engine/types.ts]

## Dev Agent Record

### Agent Model Used

<!-- To be filled by dev agent -->

### Debug Log References

### Completion Notes List

### File List
