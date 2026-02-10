# Story 13.5: "My Assignments" Panel

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **a panel on the morning report showing all open follow-ups I've created, grouped by status**,
so that **I can track assignment progress without leaving the report**.

## Acceptance Criteria

1. **Given** the manager has created follow-up assignments, **When** the "My Assignments" panel is visible on the morning report, **Then** it shows all follow-ups grouped by status:
   - **Assigned** (blue) -- awaiting action
   - **In Progress** (amber) -- assignee is working on it
   - **Resolved** (green) -- assignee has completed investigation
   **And** each entry shows: asset name, action summary, assignee name, time since assigned.

2. **Given** a follow-up was recently updated by the assignee, **When** the panel refreshes, **Then** the follow-up moves to its new status group **And** a "New update" indicator appears if the manager hasn't viewed the update yet.

3. **Given** the manager clicks on a follow-up entry, **When** the detail view opens, **Then** it shows the full assignment context: original action item, assigned note, assignee's status updates with timestamps.

4. **Given** the manager has no open follow-ups, **When** the panel renders, **Then** it shows an empty state: "No open follow-ups. Assign actions from the report below."

## Tasks / Subtasks

- [ ] Task 1: Backend - Follow-ups list endpoint with filters (AC: #1, #2)
  - [ ] 1.1 Add `GET /api/v1/followups` endpoint to `apps/api/app/api/actions.py` with query params: `assigned_by=me`, `status` filter (assigned/in_progress/resolved/all), `include_resolved` boolean
  - [ ] 1.2 Add Pydantic response schemas `FollowUpItem` and `FollowUpListResponse` in `apps/api/app/schemas/action.py` -- include `id`, `action_item_id`, `action_summary`, `asset_name`, `category`, `assigned_to` (UUID), `assigned_to_email` (resolved), `assigned_by`, `note`, `status`, `report_date`, `created_at`, `updated_at`
  - [ ] 1.3 Join `action_followups` with auth.users or team members endpoint to resolve assignee email/name for display
  - [ ] 1.4 Add `last_viewed_at` tracking (see Dev Notes below for approach) to support "New update" indicator
  - [ ] 1.5 Write pytest tests for the new endpoint: auth required, filter by assigned_by, status grouping, empty response

- [ ] Task 2: Frontend - `useMyFollowUps` hook (AC: #1, #2)
  - [ ] 2.1 Create `apps/web/src/hooks/useMyFollowUps.ts` following the exact pattern in `useDailyActions.ts`: Supabase auth session for Bearer token, `useState`/`useEffect`/`useCallback`/`useRef` pattern, error handling with user-friendly messages
  - [ ] 2.2 Return type: `{ followups: FollowUpItem[], isLoading, error, refetch, grouped: { assigned: FollowUpItem[], in_progress: FollowUpItem[], resolved: FollowUpItem[] }, totalCount, hasFollowUps }`
  - [ ] 2.3 Auto-fetch on mount, expose `refetch()` for manual refresh

- [ ] Task 3: Frontend - `MyAssignmentsPanel` component (AC: #1, #4)
  - [ ] 3.1 Create `apps/web/src/components/action-list/MyAssignmentsPanel.tsx` as a collapsible section (use Shadcn `Card` with expand/collapse toggle since `Collapsible` is not installed)
  - [ ] 3.2 Header: "My Assignments" with count badge, expand/collapse chevron icon
  - [ ] 3.3 Group follow-ups by status with color-coded section headers using existing Shadcn `Badge` component: blue variant for assigned, amber for in_progress, green for resolved
  - [ ] 3.4 Loading skeleton state, error state with retry, empty state per AC #4
  - [ ] 3.5 Default state: expanded if there are follow-ups, collapsed if empty

- [ ] Task 4: Frontend - `FollowUpEntry` component (AC: #1, #2, #3)
  - [ ] 4.1 Create `apps/web/src/components/action-list/FollowUpEntry.tsx` showing: asset name, action summary (truncated), assignee name/email, relative time since assigned (e.g., "2h ago", "1d ago")
  - [ ] 4.2 "New update" dot indicator when `updated_at > last_viewed_at` (AC #2)
  - [ ] 4.3 Click handler opens detail view in a Shadcn `Dialog` (not `Sheet` -- `Dialog` is already installed and used by `AssignFollowUpDialog`)
  - [ ] 4.4 Detail dialog shows: original action item context (priority badge, recommendation text, asset), manager's assignment note, current status with assignee's notes, full timeline of updates with timestamps

- [ ] Task 5: Frontend - Integrate panel into morning report page (AC: #1)
  - [ ] 5.1 Import `MyAssignmentsPanel` into `apps/web/src/app/(main)/morning-report/page.tsx`
  - [ ] 5.2 Position panel between `MorningSummarySection` and the "Today's Action Items" section
  - [ ] 5.3 Add barrel export in `apps/web/src/components/action-list/index.ts`

- [ ] Task 6: Testing and polish (all ACs)
  - [ ] 6.1 Verify panel renders correctly with 0, 1, and many follow-ups
  - [ ] 6.2 Verify status grouping and color coding matches spec
  - [ ] 6.3 Verify "New update" indicator appears/disappears correctly
  - [ ] 6.4 Verify detail dialog shows complete assignment context
  - [ ] 6.5 Verify empty state message matches AC #4 exactly
  - [ ] 6.6 Verify responsive layout (mobile stacked, desktop side-by-side considerations)

## Dev Notes

### Critical Architecture Patterns

- **API Framework**: FastAPI 0.109+ with async endpoints; all new endpoints MUST use `async def` and `Depends(get_current_user)` for auth
- **Frontend Framework**: Next.js 14 with App Router; `'use client'` directive required on all components with hooks/state
- **UI Library**: Shadcn/UI + Radix primitives + Tailwind CSS; do NOT install new UI packages -- use what exists in `apps/web/src/components/ui/`
- **Supabase Client**: Use `createClient()` from `@/lib/supabase/client` for browser-side auth; pattern established in `AssignFollowUpDialog.tsx`
- **Design System**: "Industrial Clarity" -- Inter font, high-contrast, dark/light mode via `next-themes`

### Existing Components to Reuse (DO NOT Reinvent)

| Component | Path | Reuse For |
|-----------|------|-----------|
| `Badge` | `components/ui/badge.tsx` | Status badges (assigned/in_progress/resolved) |
| `Card` | `components/ui/card.tsx` | Panel container |
| `Dialog` | `components/ui/dialog.tsx` | Follow-up detail overlay |
| `Button` | `components/ui/button.tsx` | Expand/collapse, refresh |
| `ScrollArea` | `components/ui/scroll-area.tsx` | Scrollable follow-up list if many items |
| `PriorityBadge` | `components/action-engine/PriorityBadge.tsx` | Show original action priority in detail view |
| `AssignFollowUpDialog` | `components/action-engine/AssignFollowUpDialog.tsx` | Reference pattern for Supabase auth + API calls |
| `ActionListSkeleton` | `components/action-list/ActionListSkeleton.tsx` | Reference pattern for skeleton loading states |
| `EmptyActionState` | `components/action-list/EmptyActionState.tsx` | Reference pattern for empty state design |

### Database Schema Reference

The `action_followups` table (migration `0025_action_followups.sql`) already exists:

```sql
CREATE TABLE action_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_item_id TEXT NOT NULL,
    action_summary TEXT NOT NULL,
    asset_name TEXT,
    category TEXT CHECK (category IN ('safety', 'oee', 'financial')),
    assigned_to UUID NOT NULL REFERENCES auth.users(id),
    assigned_by UUID NOT NULL REFERENCES auth.users(id),
    note TEXT,
    status TEXT DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'resolved')),
    report_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**RLS Policies** (already in place):
- SELECT: `assigned_to = auth.uid() OR assigned_by = auth.uid()`
- INSERT: `assigned_by = auth.uid()`
- UPDATE: `assigned_by = auth.uid()`
- Service role: full access

**Important RLS note for Story 13.5**: The existing RLS allows managers to SELECT their own follow-ups via `assigned_by = auth.uid()`. The API endpoint should use the service role Supabase client to join user data (emails) since RLS on auth.users would block cross-user lookups, then filter by `assigned_by` in the query WHERE clause.

### "New Update" Indicator Strategy

For the "New update" indicator (AC #2), use a lightweight client-side approach:
- Store `lastViewedTimestamp` per follow-up in `localStorage` (key: `followup-viewed-{followup_id}`)
- Compare `updated_at` from the API response against `lastViewedTimestamp`
- When user opens the detail dialog, update `localStorage` with current timestamp
- This avoids needing a new database table/column for view tracking in this story

### API Endpoint Design

```
GET /api/v1/followups?assigned_by=me&status=active
```

Query parameters:
- `assigned_by`: `me` (resolves to `current_user.id`), or explicit UUID
- `status`: `assigned`, `in_progress`, `resolved`, `active` (assigned + in_progress), or `all`
- `limit`: Optional, default 50
- `offset`: Optional for pagination

Response shape:
```json
{
  "followups": [
    {
      "id": "uuid",
      "action_item_id": "action-xxx",
      "action_summary": "Investigate...",
      "asset_name": "Grinder 5",
      "category": "safety",
      "assigned_to": "uuid",
      "assigned_to_email": "john@company.com",
      "assigned_by": "uuid",
      "note": "Please check by EOD",
      "status": "assigned",
      "report_date": "2026-02-09",
      "created_at": "2026-02-09T08:30:00Z",
      "updated_at": "2026-02-09T08:30:00Z"
    }
  ],
  "total_count": 5,
  "counts_by_status": {
    "assigned": 2,
    "in_progress": 2,
    "resolved": 1
  }
}
```

### Color Coding Reference

Match the existing design system colors used throughout the app:
- **Assigned (blue)**: `text-blue-600 dark:text-blue-400` / `bg-blue-100 dark:bg-blue-900/30`
- **In Progress (amber)**: `text-warning-amber-dark dark:text-warning-amber` / `bg-warning-amber-light/10 dark:bg-warning-amber-dark/10` (same pattern used in `ActionListContainer.tsx` error state)
- **Resolved (green)**: `text-success-green` / `bg-green-100 dark:bg-green-900/30` (same as `CheckCircle2` color in `AssignFollowUpDialog.tsx`)

### Relative Time Formatting

Use a simple utility function (do NOT add `date-fns` or `dayjs` -- this project has no date library dependency):

```typescript
function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
```

### Morning Report Page Integration

Current page structure in `apps/web/src/app/(main)/morning-report/page.tsx`:

```tsx
<SafetyAlertsSection />    // Keep first
<Breadcrumb />             // Keep second
<Page Header />            // Keep third
<MorningSummarySection />  // Keep fourth
// INSERT MyAssignmentsPanel HERE
<InsightEvidenceCardList /> // Keep last
```

The panel is a Server Component page importing a Client Component (`MyAssignmentsPanel`). Follow the same pattern as `InsightEvidenceCardList` -- the panel itself is `'use client'`.

### File Structure Requirements

All new files for this story:

```
apps/web/src/
  components/action-list/
    MyAssignmentsPanel.tsx       # NEW - Main collapsible panel
    FollowUpEntry.tsx            # NEW - Individual follow-up row
    FollowUpDetailDialog.tsx     # NEW - Detail overlay dialog
    index.ts                     # MODIFY - Add barrel exports
  hooks/
    useMyFollowUps.ts            # NEW - Data fetching hook
  app/(main)/morning-report/
    page.tsx                     # MODIFY - Add panel import + placement

apps/api/app/
  api/
    actions.py                   # MODIFY - Add GET /api/v1/followups endpoint
  schemas/
    action.py                    # MODIFY - Add FollowUpItem, FollowUpListResponse schemas
```

### Testing Standards

- **Backend**: pytest with `httpx.AsyncClient`; mock Supabase client; test auth required, filter combinations, empty results
- **Frontend**: Vitest + Testing Library pattern (see `apps/web/src/components/chat/__tests__/` for examples); test loading, error, empty, and populated states
- **Naming**: Test files go in `__tests__/` sibling directories or `.test.ts(x)` suffix

### Dependencies on Previous Stories in Epic 13

- **Story 13.1** (Action Acknowledgment Backend): Independent -- no dependency
- **Story 13.2** (Action Acknowledgment UI): Independent -- no dependency
- **Story 13.3** (Follow-Up Status Updates & RLS): **Soft dependency** -- this story reads follow-up status that 13.3 allows assignees to update. The panel will work without 13.3 (all follow-ups will just stay in "assigned" status), but full functionality requires 13.3's RLS update allowing assignees to update their own follow-ups
- **Story 13.4** (Assignment Badge on Action Cards): Independent -- no dependency
- **Story 13.5** depends on migration `0025_action_followups.sql` (already applied) and the `AssignFollowUpDialog` component (already implemented)

### Project Structure Notes

- Alignment with unified project structure: New components go in `components/action-list/` per the established domain-based organization (matching `ActionListContainer`, `ActionItemCard`, etc.)
- The hook goes in `hooks/` at the same level as `useDailyActions.ts`
- The API endpoint extends the existing `actions.py` router rather than creating a new router file, keeping follow-up-related endpoints co-located with action endpoints
- No new migration required -- the `action_followups` table already has all needed columns

### References

- [Source: _bmad-output/planning-artifacts/epic-13.md#Story 13.5] - Story requirements and acceptance criteria
- [Source: supabase/migrations/0025_action_followups.sql] - Database schema for action_followups table
- [Source: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx] - Follow-up creation pattern (Supabase insert, team member loading)
- [Source: apps/web/src/hooks/useDailyActions.ts] - Hook pattern for API data fetching with auth
- [Source: apps/web/src/app/(main)/morning-report/page.tsx] - Morning report page layout for integration point
- [Source: apps/web/src/components/action-list/ActionListContainer.tsx] - Container component pattern with loading/error/empty states
- [Source: apps/api/app/api/actions.py] - Existing actions API router for endpoint co-location
- [Source: apps/api/app/schemas/action.py] - Existing Pydantic schema patterns for action engine
- [Source: docs/architecture-api.md] - API architecture (FastAPI, router patterns)
- [Source: docs/architecture-web.md] - Web architecture (Next.js 14, component categories, Shadcn/UI)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
