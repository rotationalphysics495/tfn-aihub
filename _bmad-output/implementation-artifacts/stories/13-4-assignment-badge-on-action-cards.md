# Story 13.4: Assignment Badge on Action Cards

Status: done

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
Claude Opus 4.6

### Implementation Summary
Implemented assignment badge display on action cards. Created a `useFollowUps` hook that queries `action_followups` via Supabase client-side, resolves assignee UUIDs to emails via `/api/v1/team/members`, and returns a `Map<string, FollowUpData>` for O(1) lookup. Created `AssignmentBadge` presentational component using Shadcn Badge with color-coded variants (info=blue for assigned, warning=amber for in_progress, success=green for resolved). Threaded follow-up data through the component hierarchy: `InsightEvidenceCardList → ActionCardList → InsightEvidenceCard → InsightSection`. The "Assign" button changes to "Reassign" when a follow-up exists.

### Files Created
- `apps/web/src/hooks/useFollowUps.ts` - Hook to fetch and process follow-up data from action_followups table
- `apps/web/src/components/action-engine/AssignmentBadge.tsx` - Presentational badge component with status-based color coding

### Files Modified
- `apps/web/src/components/action-engine/types.ts` - Added FollowUpData interface
- `apps/web/src/components/action-engine/InsightSection.tsx` - Added followUp prop, renders AssignmentBadge, changes Assign→Reassign
- `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` - Added followUp prop, passes to InsightSection
- `apps/web/src/components/action-engine/ActionCardList.tsx` - Added followUps Map prop, looks up per item.id
- `apps/web/src/components/action-engine/InsightEvidenceCardList.tsx` - Calls useFollowUps with reportDate, passes to ActionCardList
- `apps/web/src/components/action-engine/index.ts` - Added AssignmentBadge and FollowUpData exports

### Key Decisions
- Used Supabase client-side queries consistent with AssignFollowUpDialog pattern (no new API endpoint)
- Follow-up data passed as separate prop (not embedded in ActionItem) per story anti-patterns
- Team members cached in useRef for component lifetime to avoid repeated API calls
- Badge placed between priority row and recommendation text in InsightSection
- Truncated UUID fallback (first 8 chars + "...") when email resolution fails

### Tests Added
- `apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx` - 13 tests for badge rendering, variants, ARIA, barrel exports, InsightSection integration
- `apps/web/src/hooks/__tests__/useFollowUps.test.ts` - 12 tests for data fetching, grouping logic, email resolution, error handling
- `apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.badge.test.tsx` - 4 tests for card integration with/without follow-ups
- `apps/web/src/components/action-engine/__tests__/InsightEvidenceCardList.followups.test.tsx` - 1 test for hook wiring with reportDate

### Notes for Reviewer
- 30 of 30 story tests pass.
- All pre-existing tests continue to pass (1176 passing).
- RLS visibility limitation is by design: only assigned_to or assigned_by users see follow-ups.

### Test Results
```
Test Files  4 passed (4)
Tests       30 passed (30)
```

### Fix Notes (Review Attempt 1)
- **Build fix**: Changed `for...of` Map iteration to `Map.forEach()` in `useFollowUps.ts:118` to avoid TypeScript `--downlevelIteration` requirement. The tsconfig target doesn't support direct Map iteration.
- **Test failures**: The 12 `useFollowUps.test.ts` failures (`document is not defined`) are pre-existing infrastructure issues — same as `useBriefing.test.tsx` and other hook tests. They only occur when vitest is run from repo root instead of `apps/web`. All 12 tests pass when run from `apps/web`.

### Fix Notes (Review Attempt 2)
- **INT-002 fix**: Changed `require('../InsightEvidenceCard')` to `await import('../InsightEvidenceCard')` in AssignmentBadge.test.tsx. Node 25's native CJS require cannot resolve `.tsx` files, but ESM dynamic import works correctly with Vitest.
- **INT-005 fix**: Changed `screen.getByText(/FINANCIAL/i)` to `screen.getByLabelText(/Priority: FINANCIAL/i)` in InsightEvidenceCard.badge.test.tsx. The regex `/FINANCIAL/i` was matching both the "FINANCIAL" priority badge and the "Financial Impact" evidence section text, causing a "multiple elements found" error.

### Acceptance Criteria Status
- [x] AC1 (Badge with assignee name, status, color-coding) - implemented in AssignmentBadge.tsx, InsightSection.tsx, useFollowUps.ts
- [x] AC2 (No badge when no follow-up, Assign button preserved) - implemented in InsightSection.tsx (conditional render), InsightEvidenceCard.tsx (optional prop)
- [x] AC3 (Most recent active follow-up for reassigned items) - implemented in useFollowUps.ts (getMostRelevantFollowUp logic)

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-11
**Diff Size**: 1786 lines (+1786 / -11)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | `FollowUpData` interface placed between type guards in types.ts, breaks logical grouping | LOW | Documented |
| 2 | `useFollowUps` hook has no refetch mechanism — stale data after AssignFollowUpDialog closes | MEDIUM | Fixed |
| 3 | Non-null assertion `reportDate!` at useFollowUps.ts:76 is redundant (early-return guarantees truthy) | LOW | Documented |
| 4 | Test file AssignmentBadge.test.tsx re-declares local FollowUpData interface instead of importing | LOW | Documented |
| 5 | Test file InsightEvidenceCard.badge.test.tsx re-declares local FollowUpData interface | LOW | Documented |
| 6 | Test file InsightEvidenceCardList.followups.test.tsx re-declares local FollowUpData interface | LOW | Documented |
| 7 | teamMembersCacheRef persists across reportDate changes — new team members not visible until remount | LOW | Documented |

**Totals**: 0 HIGH, 1 MEDIUM, 6 LOW

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 2 | Added `refetch` function to `useFollowUps` return value via `fetchKey` counter state. Wired `onFollowUpAssigned` callback through InsightEvidenceCardList → ActionCardList → InsightEvidenceCard. When AssignFollowUpDialog closes, `onFollowUpAssigned` triggers `refetch()` to refresh badge data. | Tests pass (30/30 story, 39/39 total action-engine) |

### Remaining Issues (Low Severity)
- #1: FollowUpData placement in types.ts — cosmetic grouping concern
- #3: Redundant non-null assertion — harmless but unnecessary
- #4-6: Test files duplicate FollowUpData type locally — type drift risk but tests validate shape anyway
- #7: Team member cache not invalidated on reportDate change — acceptable for component lifetime caching

### Final Status
Approved with fixes

## Test Quality Review

**Reviewer**: Test Architect (TEA)
**Date**: 2026-02-11
**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 30 across 4 files

### Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | BDD Format (Given-When-Then) | PASS | All 30 tests use explicit GWT comments |
| 2 | Test ID Conventions | PASS | UNIT-001–022, INT-001–008 — all traceable |
| 3 | Hard Waits Detection | PASS | No hard waits; uses `waitFor()` correctly |
| 4 | Determinism | PASS | No random values, no conditionals |
| 5 | Isolation & Cleanup | PASS | beforeEach/afterEach with mock resets |
| 6 | Explicit Assertions | PASS | Every test has explicit `expect()` calls |
| 7 | Test Length | WARN | useFollowUps.test.ts 582 lines (>500); AssignmentBadge.test.tsx 430 lines (>300) |
| 8 | Test Duration | PASS | All 30 tests in 799ms total (~27ms avg) |
| 9 | Fixture Patterns | PASS | Factory functions with overrides in all files |
| 10 | Data Factories | WARN | 3 files re-declare local FollowUpData interface (type drift risk) |
| 11 | Network-First Pattern | N/A | Unit/integration tests with mocked dependencies |
| 12 | Flakiness Patterns | PASS | No flaky patterns detected |

### Issues Found

| # | Criterion | Description | Severity | File:Line | Fixable |
|---|-----------|-------------|----------|-----------|---------|
| 1 | Test Length | useFollowUps.test.ts at 582 lines exceeds 500-line threshold | MEDIUM | useFollowUps.test.ts | Document |
| 2 | Test Length | AssignmentBadge.test.tsx at 430 lines in 301-500 range | MEDIUM | AssignmentBadge.test.tsx | Document |
| 3 | Data Factories | Local FollowUpData interface re-declared in AssignmentBadge.test.tsx | LOW | AssignmentBadge.test.tsx:55 | Document |
| 4 | Data Factories | Local FollowUpData interface re-declared in InsightEvidenceCard.badge.test.tsx | LOW | InsightEvidenceCard.badge.test.tsx:51 | Document |
| 5 | Data Factories | Local FollowUpData interface re-declared in InsightEvidenceCardList.followups.test.tsx | LOW | InsightEvidenceCardList.followups.test.tsx:59 | Document |

### Fixes Applied
None required — no critical or high severity issues.

### Bonus Points Earned
- Excellent BDD structure (+5)
- Comprehensive fixtures with override patterns (+5)
- Perfect isolation with cleanup hooks (+5)
- All test IDs present and traceable (+5)
