# Story 13.4: Assignment Badge on Action Cards

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Plant Manager,
I want to see who is assigned to each action item directly on the action card,
so that during meetings I know at a glance which items are already being investigated.

## Acceptance Criteria

1. **Given** an action item has a follow-up assigned, **When** the action card renders, **Then** a badge shows on the card with the assignee's name and current status, **And** the badge is color-coded: blue (assigned), amber (in-progress), green (resolved).

2. **Given** an action item has no follow-up assigned, **When** the action card renders, **Then** no assignment badge is shown, **And** the "Assign Follow-Up" button remains prominent (existing behavior preserved).

3. **Given** multiple follow-ups exist for the same action item (reassigned), **When** the card renders, **Then** the most recent active follow-up is shown (determined by `created_at` DESC, excluding resolved unless no active exists).

## Tasks / Subtasks

- [ ] Task 1: Create `useFollowUps` hook to fetch follow-up data (AC: #1, #2, #3)
  - [ ] 1.1 Create `apps/web/src/hooks/useFollowUps.ts` - Query `action_followups` via Supabase client for the current report date
  - [ ] 1.2 Return a `Map<string, FollowUpData>` keyed by `action_item_id` for O(1) lookup
  - [ ] 1.3 Handle multiple follow-ups per action item: sort by `created_at` DESC, return most recent non-resolved (or most recent resolved if all resolved)
  - [ ] 1.4 Include assignee email/name from team members endpoint or user metadata

- [ ] Task 2: Create `AssignmentBadge` component (AC: #1)
  - [ ] 2.1 Create `apps/web/src/components/action-engine/AssignmentBadge.tsx`
  - [ ] 2.2 Use existing Shadcn/UI `Badge` component from `@/components/ui/badge`
  - [ ] 2.3 Implement color coding using badge variants or custom classes:
    - `assigned` -> blue (use `info` variant or custom `bg-info-blue` classes)
    - `in_progress` -> amber (use `warning` variant)
    - `resolved` -> green (use `success` variant)
  - [ ] 2.4 Display format: `"[Status Icon] [Assignee Name] - [Status Label]"`
  - [ ] 2.5 Add ARIA label: `"Assigned to [name], status: [status]"`

- [ ] Task 3: Integrate badge into `InsightEvidenceCard` (AC: #1, #2)
  - [ ] 3.1 Add `followUp?: FollowUpData` optional prop to `InsightEvidenceCardProps`
  - [ ] 3.2 Render `AssignmentBadge` when `followUp` is present, between the priority badge row and the recommendation text
  - [ ] 3.3 When `followUp` exists, conditionally hide or demote the "Assign" button in `InsightSection` (still allow re-assignment)

- [ ] Task 4: Wire up data flow in `InsightEvidenceCardList` (AC: #1, #2, #3)
  - [ ] 4.1 Call `useFollowUps` in `InsightEvidenceCardList` with the current report date
  - [ ] 4.2 Pass matched follow-up data to each `InsightEvidenceCard` via the new `followUp` prop
  - [ ] 4.3 Also wire up in `ActionCardList` if it renders `InsightEvidenceCard` directly

- [ ] Task 5: Export new component from barrel file (AC: #1)
  - [ ] 5.1 Add `AssignmentBadge` export to `apps/web/src/components/action-engine/index.ts`
  - [ ] 5.2 Export `FollowUpData` type from the hook or types file

## Dev Notes

### Architecture Patterns and Constraints

- **Supabase Client-Side Queries**: Follow-ups are read directly via `createClient()` from `@/lib/supabase/client` (same pattern as `AssignFollowUpDialog.tsx`). The `action_followups` table already has RLS policies: users can SELECT rows where they are `assigned_to` or `assigned_by`.
- **No new API endpoint needed**: The `action_followups` table is queried client-side via Supabase JS, not through the FastAPI backend. This is consistent with how `AssignFollowUpDialog` writes to the same table.
- **Component Pattern**: All action-engine components are in `apps/web/src/components/action-engine/`. They use `'use client'` directive, import from `@/lib/utils` for `cn()`, and follow the Industrial Clarity design system.
- **Badge Component**: Use the existing `Badge` from `@/components/ui/badge` (file: `apps/web/src/components/ui/badge.tsx`). It supports `info`, `warning`, and `success` variants that map exactly to the required color coding (blue, amber, green).

### Critical Implementation Details

**Follow-Up Data Query** (for `useFollowUps` hook):
```typescript
// Query pattern - fetch follow-ups for current report date
const { data } = await supabase
  .from('action_followups')
  .select('id, action_item_id, assigned_to, status, note, created_at, updated_at')
  .eq('report_date', reportDate)
  .order('created_at', { ascending: false })
```

**action_followups Table Schema** (migration 0025):
- `id` UUID PK
- `action_item_id` TEXT NOT NULL - matches `ActionItem.id` from the action engine
- `action_summary` TEXT NOT NULL
- `asset_name` TEXT
- `category` TEXT CHECK (safety, oee, financial)
- `assigned_to` UUID FK -> auth.users
- `assigned_by` UUID FK -> auth.users
- `note` TEXT
- `status` TEXT DEFAULT 'assigned' CHECK (assigned, in_progress, resolved)
- `report_date` DATE NOT NULL
- `created_at` TIMESTAMPTZ
- `updated_at` TIMESTAMPTZ

**RLS Policies on action_followups**:
- SELECT: `assigned_to = auth.uid() OR assigned_by = auth.uid()` (authenticated users)
- INSERT: `assigned_by = auth.uid()` (authenticated users)
- UPDATE: `assigned_by = auth.uid()` (only assigner can update)
- ALL: service_role has full access

**Assignee Name Resolution**: The `assigned_to` field is a UUID. To display a human-readable name, either:
1. Join with user metadata (if available in Supabase auth.users)
2. Use the same `/api/v1/team/members` endpoint pattern from `AssignFollowUpDialog` to build a lookup map
3. Store email at assignment time (simplest; would require schema change - NOT recommended for this story)

Recommended approach: fetch team members once via the same pattern in `AssignFollowUpDialog.tsx` (lines 60-91) and build a `Map<string, string>` of user_id -> email for display.

**Multiple Follow-Ups Logic** (AC #3):
```typescript
// Group by action_item_id, take most recent active (non-resolved) first
// If all are resolved, show the most recently resolved one
function getMostRelevantFollowUp(followUps: FollowUp[]): FollowUp | null {
  const active = followUps.filter(f => f.status !== 'resolved')
  if (active.length > 0) return active[0] // Already sorted by created_at DESC
  return followUps[0] // Most recent resolved
}
```

**Badge Placement in Card**: Insert the `AssignmentBadge` in `InsightEvidenceCard.tsx` inside the left-side `InsightSection` area. The badge should appear in the header row alongside the `PriorityBadge`, or directly below it. Do NOT place it in the evidence (right) section.

**Color Mapping Reference**:
| Follow-Up Status | Badge Variant | Color | Tailwind Classes (from badge.tsx) |
|---|---|---|---|
| `assigned` | `info` | Blue | `border-info-blue bg-info-blue-light text-info-blue-dark` |
| `in_progress` | `warning` | Amber | `border-warning-amber bg-warning-amber-light text-warning-amber-dark` |
| `resolved` | `success` | Green | `border-success-green bg-success-green-light text-success-green-dark` |

### Anti-Patterns to Avoid

- **DO NOT** create a new API endpoint in `apps/api/app/api/actions.py` for fetching follow-ups. Use Supabase client-side queries (consistent with existing pattern).
- **DO NOT** modify the `action_followups` migration or schema. The existing table has everything needed.
- **DO NOT** use the `PriorityBadge` component for assignment badges - it is specifically for SAFETY/FINANCIAL/OEE priority levels. Use the Shadcn/UI `Badge` component instead.
- **DO NOT** break the existing "Assign Follow-Up" button behavior. The button in `InsightSection.tsx` (lines 127-145) should still work. When a follow-up exists, either keep the button visible (for re-assignment) or change its label to "Reassign".
- **DO NOT** add follow-up data to the `ActionItem` type in `types.ts`. Keep follow-up data separate and pass it as a prop. This maintains separation of concerns between the action engine data and follow-up tracking data.

### Testing Standards

- Verify badge renders with correct variant for each status (assigned/in_progress/resolved)
- Verify no badge renders when no follow-up exists for an action item
- Verify most recent active follow-up is selected when multiple exist
- Verify assignee name displays correctly (not UUID)
- Verify existing "Assign" button still functions when follow-up exists
- Verify accessibility: badge has proper ARIA attributes
- Manual test: create follow-up via AssignFollowUpDialog, verify badge appears on card

### Project Structure Notes

- All new files go in `apps/web/src/components/action-engine/` (component) and `apps/web/src/hooks/` (hook)
- Follow the existing naming convention: PascalCase for components (`AssignmentBadge.tsx`), camelCase with `use` prefix for hooks (`useFollowUps.ts`)
- The hook location follows existing pattern: `useDailyActions.ts` is in `apps/web/src/hooks/`, so `useFollowUps.ts` goes there too
- Export from barrel file `apps/web/src/components/action-engine/index.ts`

### References

- [Source: _bmad-output/planning-artifacts/epic-13.md#Story 13.4] - Story requirements and acceptance criteria
- [Source: supabase/migrations/0025_action_followups.sql] - action_followups table schema and RLS policies
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx] - Main card component to modify
- [Source: apps/web/src/components/action-engine/InsightSection.tsx] - Left side of card with "Assign" button (lines 127-145)
- [Source: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx] - Existing follow-up assignment dialog, team members fetch pattern (lines 60-91)
- [Source: apps/web/src/components/action-engine/PriorityBadge.tsx] - Existing badge pattern (DO NOT reuse for assignment badges)
- [Source: apps/web/src/components/action-engine/types.ts] - ActionItem type definition
- [Source: apps/web/src/components/action-engine/index.ts] - Barrel file to update with new exports
- [Source: apps/web/src/components/ui/badge.tsx] - Shadcn/UI Badge with info/warning/success variants
- [Source: apps/web/src/hooks/useDailyActions.ts] - Hook pattern to follow for useFollowUps
- [Source: apps/web/src/components/action-engine/InsightEvidenceCardList.tsx] - Data integration wrapper to wire up follow-up data
- [Source: apps/web/src/components/action-engine/transformers.ts] - Data transformer patterns (no changes needed)

## Dev Agent Record

### Agent Model Used

<!-- To be filled by dev agent -->

### Debug Log References

### Completion Notes List

### File List
