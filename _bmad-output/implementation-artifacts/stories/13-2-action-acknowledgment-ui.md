# Story 13.2: Action Acknowledgment UI

Status: ready-for-dev

## Story

As a **Plant Manager**,
I want **a checkbox or button on each action card to mark it as reviewed**,
so that **I can track which items I've addressed during my morning review**.

## Acceptance Criteria

1. **Given** the morning report displays action items, **When** each action card renders, **Then** it shows an acknowledgment button/checkbox in an unacknowledged state.

2. **Given** the user clicks the acknowledge button on an action card, **When** the acknowledgment API is called, **Then** the button immediately updates to "acknowledged" state (optimistic UI), **And** the card visually changes (e.g., muted styling or checkmark overlay), **And** a timestamp shows when it was acknowledged.

3. **Given** an action item was previously acknowledged, **When** the morning report reloads, **Then** the acknowledged state is preserved from the database.

4. **Given** all action items are acknowledged, **When** the action list renders, **Then** a summary shows "All items reviewed" with a count.

## Tasks / Subtasks

- [ ] Task 1: Create `useActionAcknowledgment` hook (AC: #1, #2, #3)
  - [ ] 1.1 Create `apps/web/src/hooks/useActionAcknowledgment.ts`
  - [ ] 1.2 Implement `POST /api/v1/actions/{action_id}/acknowledge` API call using Bearer token auth pattern
  - [ ] 1.3 Implement optimistic state update (immediate UI change, rollback on failure)
  - [ ] 1.4 Implement bulk acknowledgment state fetching for initial page load (GET endpoint that returns acknowledged items for report date)
  - [ ] 1.5 Handle error states with rollback and user-visible error toast
- [ ] Task 2: Add acknowledge button to `InsightEvidenceCard` (AC: #1, #2)
  - [ ] 2.1 Add `CheckCircle2` icon button in the `InsightSection` context row (next to Assign button)
  - [ ] 2.2 Implement unacknowledged state: outline circle icon, "Mark Reviewed" label
  - [ ] 2.3 Implement acknowledged state: filled green checkmark, "Reviewed" label with timestamp
  - [ ] 2.4 Add click handler calling `useActionAcknowledgment.acknowledge(actionId)`
  - [ ] 2.5 Add `aria-label` and keyboard support for accessibility
- [ ] Task 3: Add acknowledged visual styling to `InsightEvidenceCard` (AC: #2)
  - [ ] 3.1 When acknowledged, apply `opacity-60` + muted left-border color to the card
  - [ ] 3.2 Add a subtle checkmark overlay or badge in the top-right corner
  - [ ] 3.3 Ensure the acknowledged timestamp displays below the button in `text-sm text-muted-foreground`
- [ ] Task 4: Persist and restore acknowledged state (AC: #3)
  - [ ] 4.1 On `InsightEvidenceCardList` mount, call hook to fetch all acknowledgments for current report date
  - [ ] 4.2 Pass `acknowledgment` data (who, when, note) into each `InsightEvidenceCard` via props
  - [ ] 4.3 Restore acknowledged visual state on reload from database response
- [ ] Task 5: "All items reviewed" summary (AC: #4)
  - [ ] 5.1 Track `acknowledgedCount` vs `totalCount` in `InsightEvidenceCardList`
  - [ ] 5.2 When `acknowledgedCount === totalCount && totalCount > 0`, render a success banner above the action list
  - [ ] 5.3 Banner text: "All items reviewed" with green checkmark icon and count (e.g., "5/5 reviewed")
  - [ ] 5.4 Style with `bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800`
- [ ] Task 6: Testing (AC: #1-4)
  - [ ] 6.1 Unit test `useActionAcknowledgment` hook: optimistic update, rollback on error, initial fetch
  - [ ] 6.2 Component test `InsightEvidenceCard` with acknowledged and unacknowledged states
  - [ ] 6.3 Component test "All items reviewed" banner rendering logic

## Dev Notes

### Architecture & Technical Patterns

**Frontend Stack (must use):**
- Next.js 14+ with App Router, TypeScript 5.x
- Tailwind CSS 3.4+ for styling
- Shadcn/UI primitives (`Button`, `Badge` from `@/components/ui/`)
- Lucide React icons (`CheckCircle2`, `Circle` for toggle states)
- Vitest + Testing Library for tests

**API Communication Pattern (must follow):**
- All API calls use Bearer token from Supabase session: `Authorization: Bearer ${session.access_token}`
- Get session via `createClient()` from `@/lib/supabase/client` then `supabase.auth.getSession()`
- API base URL from `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
- See existing pattern in `apps/web/src/hooks/useDailyActions.ts` lines 122-149

**Optimistic Update Pattern:**
```typescript
// 1. Save current state for rollback
const previousState = { ...state };
// 2. Immediately update UI
setState(optimisticNewState);
// 3. Call API
try {
  await fetch(url, { method: 'POST', headers, body });
} catch {
  // 4. Rollback on failure
  setState(previousState);
  // 5. Show error
}
```

**Acknowledgment API Contract (Story 13.1 provides):**
- `POST /api/v1/actions/{action_id}/acknowledge` with body `{ note?: string }`
- Response: `{ id, action_item_id, user_id, acknowledged_at, note, report_date }`
- Table: `action_acknowledgments` with unique constraint on `(action_item_id, user_id, report_date)`
- Upsert behavior: calling again updates existing acknowledgment

**Fetching existing acknowledgments:**
- The daily actions endpoint (`GET /api/v1/actions/daily`) will include an `acknowledgment` field on each action item (null if unacknowledged, object with `user_id`, `acknowledged_at`, `note` if acknowledged) per Story 13.1 AC #3
- The hook should read this from the action items data already fetched by `useDailyActions`

### Component Integration Points

**`InsightEvidenceCard.tsx`** (`apps/web/src/components/action-engine/InsightEvidenceCard.tsx`):
- Currently has `InsightSection` (left) and `EvidenceSection` (right) in a 2-column grid
- Has existing `onAssign` callback pattern in `InsightSection` to reference for button placement
- Props interface `InsightEvidenceCardProps` needs new optional `acknowledgment` prop and `onAcknowledge` callback
- Card already uses `cn()` utility for conditional styling -- add acknowledged muting there

**`InsightSection.tsx`** (`apps/web/src/components/action-engine/InsightSection.tsx`):
- Context row at bottom has: Asset name button, Clock timestamp, Assign button
- Add the Acknowledge button to this row, positioned BEFORE the Assign button
- Follow the same button styling pattern as the existing Assign button (lines 127-145)

**`InsightEvidenceCardList.tsx`** (`apps/web/src/components/action-engine/InsightEvidenceCardList.tsx`):
- This renders the list of `InsightEvidenceCard` components
- Add acknowledgment tracking state here (manages which items are acknowledged)
- Add the "All items reviewed" summary banner here

**`ActionItem` type** (`apps/web/src/components/action-engine/types.ts`):
- Add optional `acknowledgment` field to the `ActionItem` interface:
  ```typescript
  acknowledgment?: {
    user_id: string
    acknowledged_at: string
    note?: string
  } | null
  ```

**`useDailyActions` hook** (`apps/web/src/hooks/useDailyActions.ts`):
- The `ActionItem` interface here (line 31-47) will need an optional `acknowledgment` field added
- This field comes from Story 13.1's enriched action item response

### Shadcn/UI Components Available

The project has these UI primitives installed (`apps/web/src/components/ui/`):
- `button.tsx` -- use for the acknowledge toggle
- `badge.tsx` -- use for the "Reviewed" state badge
- `card.tsx` -- already used by `InsightEvidenceCard`
- `tooltip.tsx` -- use for timestamp tooltip on hover

**No `Checkbox` component is installed.** Use a `Button` with variant `ghost` and icon toggle pattern instead:
```tsx
<Button
  variant="ghost"
  size="sm"
  onClick={handleAcknowledge}
  className={cn(
    'flex items-center gap-1.5',
    isAcknowledged && 'text-green-600 dark:text-green-400'
  )}
>
  {isAcknowledged ? (
    <CheckCircle2 className="w-4 h-4" />
  ) : (
    <Circle className="w-4 h-4" />
  )}
  <span>{isAcknowledged ? 'Reviewed' : 'Mark Reviewed'}</span>
</Button>
```

### Existing Design Patterns to Follow

- **Industrial Clarity Design System**: Inter font, Tailwind CSS with custom theme, dark/light mode support
- **Safety Red Rule**: Red color ONLY for safety items, never for general UI states
- **24px+ for key values**: Text sizing follows glanceability requirements
- **Priority colors**: Safety Red, Warning Amber, Info Blue, Industrial Gray (from `PriorityBadge.tsx`)
- **Acknowledged green**: Use Tailwind's `green-600`/`green-400` for acknowledged states -- NOT safety-red

### Project Structure Notes

- All new hooks go in `apps/web/src/hooks/` (not `src/lib/hooks/` -- that pattern is for lib-scoped hooks only)
- Action engine components in `apps/web/src/components/action-engine/`
- Update barrel exports in `apps/web/src/components/action-engine/index.ts` if adding new components
- All components use `'use client'` directive since they have interactivity

### Dependencies on Story 13.1

This story depends on Story 13.1 (Action Acknowledgment Backend) providing:
1. The `POST /api/v1/actions/{action_id}/acknowledge` endpoint
2. The `action_acknowledgments` table (migration 0027)
3. The enriched daily actions response with `acknowledgment` field on each action item

If Story 13.1 is not yet implemented, the UI can be built with mocked API responses for development, then connected when the backend is ready.

### Testing Standards

- Framework: Vitest + React Testing Library
- Test files: `__tests__/` directory adjacent to component files
- Run: `cd apps/web && npm run test`
- Test the hook with mocked fetch (use `vi.fn()` to mock `fetch` and `createClient`)
- Test components with `render()` and `fireEvent.click()` for acknowledge button
- Verify optimistic update applies immediately, then rollback on simulated failure

### References

- [Source: _bmad-output/planning-artifacts/epic-13.md#Story 13.2]
- [Source: docs/architecture-web.md#Component Architecture]
- [Source: docs/architecture-api.md#API Endpoints]
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx]
- [Source: apps/web/src/components/action-engine/InsightSection.tsx]
- [Source: apps/web/src/hooks/useDailyActions.ts]
- [Source: apps/web/src/components/action-engine/types.ts]
- [Source: supabase/migrations/0025_action_followups.sql]
- [Source: apps/api/app/schemas/action.py]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
