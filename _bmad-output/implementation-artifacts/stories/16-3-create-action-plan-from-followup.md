# Story 16.3: Create Action Plan from Follow-Up

Status: ready-for-dev

## Story

As a Plant Manager,
I want to create an action plan directly from a follow-up investigation response,
so that the plan is pre-populated with the asset, issue context, and engineer's findings — closing the loop from issue to corrective action.

## Acceptance Criteria

1. **Given** a follow-up has a response from the assignee with investigation findings, **When** the manager clicks "Create Action Plan" on the follow-up detail, **Then** an action plan creation form opens pre-populated with:
   - `asset_id` from the original action item (looked up from `asset_name` in `action_followups`)
   - `description` from the action item summary + assignee's response
   - `root_cause` from the assignee's response text
   - `source_followup_id` linking back to the follow-up
   - The manager can edit any pre-filled field before saving

2. **Given** the action plan is created from a follow-up, **When** the follow-up detail is viewed later, **Then** a link to the created action plan is visible and the follow-up shows "Action plan created" status.

3. **Given** the "Create Action Plan" button, **When** the follow-up has no response yet (status is still `assigned`), **Then** the button is not shown — it only appears on follow-ups with responses.

4. **Given** the action plan form is open, **When** the manager submits with required fields (title, category, priority, due_date), **Then** the plan is created via `POST /api/v1/action-plans` with `status='open'` and the current user as owner.

5. **Given** the action plan is created successfully, **When** the form closes, **Then** the follow-up entry updates to show the linked action plan without a full page reload.

## Tasks / Subtasks

- [ ] Task 1: Create `useActionPlans` hook for CRUD operations (AC: #1, #4)
  - [ ] 1.1 Create `apps/web/src/hooks/useActionPlans.ts` following `useDailyActions.ts` pattern
  - [ ] 1.2 Implement `createActionPlan()` calling `POST /api/v1/action-plans`
  - [ ] 1.3 Implement `getActionPlanByFollowUpId()` for checking existing links
  - [ ] 1.4 Add TypeScript interfaces for `ActionPlan`, `CreateActionPlanRequest`, `CreateActionPlanResponse`
- [ ] Task 2: Create `ActionPlanForm` component (AC: #1, #4)
  - [ ] 2.1 Create `apps/web/src/components/action-plans/ActionPlanForm.tsx` as a Dialog (follow `AssignFollowUpDialog.tsx` pattern)
  - [ ] 2.2 Build form fields: title, description, category (corrective/preventive/improvement), root_cause, corrective_action, preventive_action, priority (low/medium/high/critical), due_date, asset display (read-only from pre-fill)
  - [ ] 2.3 Accept `prefill` prop with follow-up context for auto-population
  - [ ] 2.4 Form validation: title required, category required, priority required, due_date required
  - [ ] 2.5 Submit handler calls `useActionPlans.createActionPlan()` with loading/error/success states
- [ ] Task 3: Add "Create Action Plan" button to follow-up entries (AC: #1, #3)
  - [ ] 3.1 Identify where follow-up entries render (likely within the morning report or a "My Assignments" panel)
  - [ ] 3.2 Create or modify a `FollowUpEntry` component to show "Create Action Plan" button when status !== 'assigned' (i.e., has response)
  - [ ] 3.3 Wire button to open `ActionPlanForm` dialog with pre-filled data from the follow-up
- [ ] Task 4: Show linked action plan on follow-up entry (AC: #2, #5)
  - [ ] 4.1 Query action plans by `source_followup_id` to check if a plan already exists
  - [ ] 4.2 If plan exists, show a link/badge: "Action Plan: {title}" instead of the "Create Action Plan" button
  - [ ] 4.3 Clicking the link navigates to `/action-plans/{id}` (or opens detail, depending on Story 16.5 progress)
- [ ] Task 5: Wire Supabase client for action_plans table (AC: #1, #4)
  - [ ] 5.1 All CRUD goes through the Supabase JS client (same pattern as `AssignFollowUpDialog.tsx` line 112-124)
  - [ ] 5.2 Ensure RLS compatibility — the current user is set as `owner_id`

## Dev Notes

### Dependencies / Prerequisites

**This story depends on Story 16.1 (Action Plans Data Model) and Story 16.2 (Action Plans CRUD API) being complete.** The `action_plans` and `action_plan_updates` tables must exist, and the `POST /api/v1/action-plans` endpoint must be available. If those stories are not yet implemented, the developer must create the migration and API endpoint as part of this story or stub them.

Key tables this story interacts with:
- `action_followups` (existing, migration `0025_action_followups.sql`) — read follow-up data
- `action_plans` (from Story 16.1, migration `0031_action_plans.sql`) — create new plans
- `assets` (existing) — resolve `asset_id` from `asset_name`

### Architecture & Code Patterns

**Frontend stack:** Next.js 14 App Router, TypeScript, Tailwind CSS, Shadcn/UI components, Radix UI primitives.

**Supabase client pattern (CRITICAL):** This project calls Supabase directly from the frontend for CRUD operations on Supabase-managed tables. Follow the exact pattern in `AssignFollowUpDialog.tsx`:
```typescript
const supabase = createClient()  // from '@/lib/supabase/client'
const { data: { session } } = await supabase.auth.getSession()
const { data, error } = await supabase.from('action_plans').insert({...})
```

**API calls pattern:** For FastAPI backend endpoints, follow the pattern in `useDailyActions.ts`:
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const response = await fetch(`${apiUrl}/api/v1/action-plans`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${session?.access_token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(payload),
})
```

**Choose the right pattern:** If Story 16.2 created a FastAPI endpoint (`POST /api/v1/action-plans`), use the fetch-based pattern. If the developer is going directly to Supabase (no FastAPI intermediary), use the Supabase client pattern. The `action_followups` table is accessed directly via Supabase client (see `AssignFollowUpDialog.tsx`), so it is reasonable for `action_plans` to follow the same approach.

**Dialog component pattern:** Use the Shadcn/UI `Dialog` with `DialogContent`, `DialogHeader`, `DialogFooter`, `DialogTitle`, `DialogDescription` — exactly as done in `AssignFollowUpDialog.tsx`. Import from `@/components/ui/dialog`.

**Form components available:** `Button` (`@/components/ui/button`), `Textarea` (`@/components/ui/textarea`), `select` (native HTML select styled with Tailwind — see `AssignFollowUpDialog.tsx` line 183-199). For date input, use a native `<input type="date" />` styled with the same `cn()` utility classes. Shadcn `Input` is NOT currently in the project's UI components — check `apps/web/src/components/ui/` before importing.

### Existing Component Map

| Component / File | Purpose | Relevance |
|---|---|---|
| `AssignFollowUpDialog.tsx` | Dialog for assigning follow-ups | **PRIMARY PATTERN** — copy structure for ActionPlanForm |
| `InsightEvidenceCard.tsx` | Action card with assign button | Shows how dialog state is managed (useState + onOpenChange) |
| `InsightSection.tsx` | Left side of action cards | Contains the "Assign" button that opens AssignFollowUpDialog |
| `useDailyActions.ts` | Hook for fetching action list | **HOOK PATTERN** — follow for useActionPlans |
| `action-engine/types.ts` | TypeScript types for action items | Reference for ActionItem interface shape |
| `action-engine/index.ts` | Barrel exports | Follow pattern for new action-plans barrel export |
| `PriorityBadge.tsx` | Priority badge component | Reuse for action plan priority display |

### `action_followups` Table Schema (existing)

```sql
action_followups (
  id UUID PK,
  action_item_id TEXT NOT NULL,
  action_summary TEXT NOT NULL,
  asset_name TEXT,                    -- Use this to look up asset_id from assets table
  category TEXT CHECK ('safety','oee','financial'),
  assigned_to UUID FK -> auth.users,
  assigned_by UUID FK -> auth.users,
  note TEXT,
  status TEXT DEFAULT 'assigned' CHECK ('assigned','in_progress','resolved'),
  report_date DATE NOT NULL,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)
```

### `action_plans` Table Schema (from Story 16.1)

```sql
action_plans (
  id UUID PK,
  title TEXT,
  description TEXT,
  asset_id UUID FK -> assets (nullable),
  category TEXT CHECK ('corrective','preventive','improvement'),
  root_cause TEXT,
  corrective_action TEXT,
  preventive_action TEXT,
  source_followup_id UUID FK -> action_followups (nullable),
  owner_id UUID FK -> auth.users,
  status TEXT CHECK ('draft','open','in_progress','completed','verified'),
  priority TEXT CHECK ('low','medium','high','critical'),
  due_date DATE,
  completed_at TIMESTAMPTZ,
  verified_by UUID FK -> auth.users (nullable),
  verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)
```

### Pre-fill Mapping (Follow-Up -> Action Plan)

When creating an action plan from a follow-up, map fields as follows:

| Action Plan Field | Source | Value |
|---|---|---|
| `title` | Generated | `"Action Plan: {followup.action_summary}"` (truncated to ~80 chars, editable) |
| `description` | `followup.action_summary` + `followup.note` | Concatenate action summary and any manager/assignee notes |
| `asset_id` | `followup.asset_name` | Look up UUID from `assets` table where `name = followup.asset_name` |
| `root_cause` | `followup.note` (if assignee response) | Pre-fill with the assignee's investigation notes |
| `source_followup_id` | `followup.id` | Direct UUID link |
| `category` | `followup.category` mapped | `'safety' -> 'corrective'`, `'oee' -> 'improvement'`, `'financial' -> 'corrective'` |
| `priority` | `followup.category` mapped | `'safety' -> 'high'`, `'oee' -> 'medium'`, `'financial' -> 'medium'` |
| `corrective_action` | Empty | Manager fills in |
| `preventive_action` | Empty | Manager fills in |
| `due_date` | Empty | Manager must set |
| `status` | Default | `'open'` |
| `owner_id` | Current user | `session.user.id` |

### Asset ID Resolution

The `action_followups` table stores `asset_name` (TEXT) not `asset_id` (UUID). To get the `asset_id` for the action plan:

```typescript
const { data: asset } = await supabase
  .from('assets')
  .select('id')
  .eq('name', followup.asset_name)
  .single()
```

If no match is found, set `asset_id` to `null` (it is nullable in the action_plans schema).

### Project Structure Notes

New files to create:
- `apps/web/src/hooks/useActionPlans.ts` — CRUD hook (in `src/hooks/`, NOT `src/lib/hooks/` — follow `useDailyActions.ts` location)
- `apps/web/src/components/action-plans/ActionPlanForm.tsx` — Dialog form component
- `apps/web/src/components/action-plans/index.ts` — Barrel exports

Files to modify:
- The component that renders follow-up entries (likely in `action-engine/` or a follow-up list view) — add "Create Action Plan" button
- `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` — potentially, if follow-up entries are shown within evidence cards

**Directory structure alignment:** Hooks go in `apps/web/src/hooks/` (single-file hooks like `useDailyActions.ts`, `useSafetyAlerts.ts`). Components go in `apps/web/src/components/{feature}/`. Follow existing naming: PascalCase for components, camelCase for hooks.

### Follow-Up Entry Location

Currently, follow-up entries are created via `AssignFollowUpDialog.tsx` but there is NO dedicated "follow-up list" or "follow-up entry" component yet. The `FollowUpEntry.tsx` listed in the epic does not exist. The developer will need to either:

1. **Create a new `FollowUpEntry` component** that displays individual follow-up records with status, assignee, notes, and the "Create Action Plan" button, OR
2. **Add the "Create Action Plan" button to wherever follow-ups will be displayed** in the UI (this might be part of a "My Assignments" panel or the morning report page).

Since Epic 13 (follow-up tracking) may already have created a follow-up list view, the developer should search for any components rendering `action_followups` data before creating new ones. Check: `grep -r "action_followups" apps/web/src/`.

### RLS Considerations

The `action_plans` table (from Story 16.1) should have RLS policies allowing:
- Owners can CRUD their own plans
- Authenticated users can read all plans
- Service role has full access

When inserting, ensure `owner_id = session.user.id` is set — RLS will enforce this.

### Testing Standards

- **Unit tests:** Vitest + Testing Library for React components
- **Test location:** `apps/web/src/components/action-plans/__tests__/ActionPlanForm.test.tsx`
- **Key test cases:**
  - Form renders with pre-filled data from follow-up
  - Required field validation (title, category, priority, due_date)
  - Successful submission calls Supabase insert
  - Error state displays on submission failure
  - "Create Action Plan" button only shows when follow-up has response
  - Linked action plan displays when plan already exists for follow-up

### References

- [Source: _bmad-output/planning-artifacts/epic-16.md#Story 16.3]
- [Source: docs/architecture-web.md#Directory Structure]
- [Source: docs/architecture-api.md#API Endpoints]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: supabase/migrations/0025_action_followups.sql]
- [Source: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx]
- [Source: apps/web/src/hooks/useDailyActions.ts]
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx]
- [Source: apps/web/src/components/action-engine/types.ts]
- [Source: apps/api/app/main.py#Router Registration]

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
