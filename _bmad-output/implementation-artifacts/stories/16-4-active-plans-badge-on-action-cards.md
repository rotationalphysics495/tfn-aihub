# Story 16.4: Active Plans Badge on Action Cards

Status: ready-for-dev

## Story

As a Plant Manager,
I want to see on the morning report action card if an asset already has an active action plan,
so that I don't create redundant assignments and the team knows the issue is being addressed.

## Acceptance Criteria

1. **Given** an action item's asset has an open/in-progress action plan, **When** the action card renders, **Then** a badge is displayed: "Action plan: {title} (due {date}, {status})" **And** clicking the badge opens the action plan detail.

2. **Given** an asset has multiple active action plans, **When** the action card renders, **Then** a summary badge shows: "2 active action plans" with a dropdown or link to view them.

3. **Given** an asset has no action plans or only completed/verified plans, **When** the action card renders, **Then** no action plan badge is shown.

## Tasks / Subtasks

- [ ] Task 1: Create `useActiveActionPlans` hook (AC: #1, #2, #3)
  - [ ] 1.1 Create `apps/web/src/hooks/useActiveActionPlans.ts`
  - [ ] 1.2 Implement fetch logic calling `GET /api/v1/action-plans?status=open,in_progress&asset_id={id}` with Bearer token auth
  - [ ] 1.3 Return typed `ActiveActionPlan[]` with title, due_date, status, id
  - [ ] 1.4 Handle loading, error, and empty states
  - [ ] 1.5 Accept `assetId: string` parameter, skip fetch when undefined

- [ ] Task 2: Create `ActivePlanBadge` component (AC: #1, #2, #3)
  - [ ] 2.1 Create `apps/web/src/components/action-engine/ActivePlanBadge.tsx`
  - [ ] 2.2 Single plan: render Shadcn `Badge` variant="info" with plan title, due date, status
  - [ ] 2.3 Multiple plans: render summary badge "N active action plans" with dropdown list (use Shadcn `Popover` or `DropdownMenu`)
  - [ ] 2.4 No plans / only completed: render `null`
  - [ ] 2.5 Badge click navigates to `/action-plans/{id}` for single plan or `/action-plans?asset_id={id}` for multiple
  - [ ] 2.6 Add `aria-label` for accessibility, `role="link"` semantics

- [ ] Task 3: Integrate badge into `InsightEvidenceCard` (AC: #1, #2, #3)
  - [ ] 3.1 Import and render `ActivePlanBadge` inside `InsightSection` context row (below asset name)
  - [ ] 3.2 Pass `assetId={item.asset.id}` to the badge
  - [ ] 3.3 Ensure badge does not disrupt existing card layout or priority styling

- [ ] Task 4: Backend - extend action plans list endpoint for asset filtering (AC: #1, #2, #3)
  - [ ] 4.1 Ensure `GET /api/v1/action-plans` supports query param `asset_id` filter
  - [ ] 4.2 Ensure `status` filter supports comma-separated values: `open,in_progress`
  - [ ] 4.3 Return minimal fields needed for badge: `id`, `title`, `due_date`, `status`
  - [ ] 4.4 Add index on `action_plans(asset_id, status)` if not already present from Story 16.1 migration

- [ ] Task 5: Export and barrel updates (AC: #1)
  - [ ] 5.1 Add `ActivePlanBadge` export to `apps/web/src/components/action-engine/index.ts`

## Dev Notes

### Architecture Patterns and Constraints

- **Frontend framework:** Next.js 14 App Router with TypeScript 5.x
- **UI library:** Shadcn/UI (Radix primitives) + Tailwind CSS 3.4+. Use the existing `Badge` component at `apps/web/src/components/ui/badge.tsx` with the `info` variant for the action plan badge. Do NOT create a custom badge from scratch.
- **Auth pattern:** All API calls use Bearer token from Supabase session. Follow the exact pattern in `useDailyActions.ts`: get session via `createClient()` then `supabase.auth.getSession()`, pass `Authorization: Bearer ${session.access_token}` header.
- **Hook pattern:** Follow the pattern established by `useDailyActions.ts` at `apps/web/src/hooks/useDailyActions.ts` - useState for state management, useCallback for fetch, useEffect for auto-fetch, mountedRef for cleanup.
- **API URL:** Use `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`.
- **Backend router:** The action plans CRUD API will be at `apps/api/app/api/action_plans.py` (created in Story 16.2). The list endpoint must already support filtering by `asset_id` and `status` query params.
- **RLS:** All queries go through Supabase RLS. Authenticated users can read all action plans.

### Component Placement

The `ActivePlanBadge` renders inside the `InsightSection` component (`apps/web/src/components/action-engine/InsightSection.tsx`), specifically in the context row `<div>` that already contains the asset name button, timestamp, and assign button. Place the badge between the timestamp and the assign button for visual flow:

```
[Priority Badge] [$Impact]
[Recommendation Text]
[Asset Name] [Timestamp] [ActivePlanBadge] [Assign Button]
```

### Existing InsightEvidenceCard Structure

The `InsightEvidenceCard` at `apps/web/src/components/action-engine/InsightEvidenceCard.tsx`:
- Accepts `ActionItem` type with `asset: AssetReference` containing `{ id, name, area }`
- Renders `InsightSection` (left) and `EvidenceSection` (right) in a 2-column grid
- The `InsightSection` receives `asset`, `priority`, `recommendation`, `financialImpact`, `timestamp`, `onAssign`
- The asset ID is available as `item.asset.id` and will be passed to the hook

### Badge Behavior

- **Single active plan:** `Badge variant="info"` showing `"Plan: {title} (due {formatted_date})"` - clickable, navigates to plan detail
- **Multiple active plans:** `Badge variant="info"` showing `"{count} active plans"` - click opens a `Popover` listing plan titles with links, or navigates to filtered dashboard
- **No active plans / completed only:** Return `null`, render nothing
- **Loading state:** Show a small shimmer/skeleton inline (keep it minimal, do NOT block card rendering)
- **Error state:** Silently fail, show nothing (action plan badge is informational, not critical)

### Action Plans Data Model (from Story 16.1)

Key fields of `action_plans` table used by this story:
- `id` UUID PK
- `title` TEXT
- `asset_id` UUID FK to assets (nullable for plant-wide)
- `status` TEXT CHECK ('draft', 'open', 'in_progress', 'completed', 'verified')
- `due_date` DATE
- Indexes on `asset_id`, `status` (from Story 16.1 migration 0031)

Active plans = WHERE `status IN ('open', 'in_progress')` AND `asset_id = {target_asset_id}`

### Dependencies

- **Story 16.1** (Action Plans Data Model) must be complete - provides `action_plans` table
- **Story 16.2** (Action Plans CRUD API) must be complete - provides `GET /api/v1/action-plans` endpoint with filtering
- **Story 16.3** (Create Action Plan from Follow-Up) should be complete for full E2E flow, but badge can render independently

### Project Structure Notes

- New hook: `apps/web/src/hooks/useActiveActionPlans.ts` - follows existing hooks directory pattern (`useDailyActions.ts`, `useSafetyAlerts.ts`, etc.)
- New component: `apps/web/src/components/action-engine/ActivePlanBadge.tsx` - follows action-engine component organization
- Modified component: `apps/web/src/components/action-engine/InsightSection.tsx` - add badge to context row
- Modified barrel: `apps/web/src/components/action-engine/index.ts` - add export
- Potential backend: `apps/api/app/api/action_plans.py` - ensure asset_id filter param works (may already exist from Story 16.2)

### Type Definitions

Add to or import in the badge component:

```typescript
interface ActiveActionPlan {
  id: string
  title: string
  due_date: string  // ISO date string
  status: 'open' | 'in_progress'
}

interface ActivePlanBadgeProps {
  assetId: string
  className?: string
}
```

### Testing Standards

- Use Vitest + Testing Library (project standard)
- Test file: `apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx`
- Test cases:
  - Renders badge for single active plan with correct title and date
  - Renders summary badge for multiple active plans
  - Renders nothing when no active plans
  - Renders nothing when only completed/verified plans
  - Click navigates to plan detail
  - Handles loading state gracefully
  - Handles API error silently

### Performance Considerations

- The hook fetches per action card per asset. If multiple action cards share the same asset, consider deduplication. A simple approach: the hook can be called per-card and rely on HTTP caching or React Query (if introduced), but for MVP, per-card fetch is acceptable.
- Keep badge rendering lightweight - no heavy computations, no waterfalls. Use `useMemo` for date formatting if needed.

### References

- [Source: _bmad-output/planning-artifacts/epic-16.md#Story 16.4]
- [Source: docs/architecture-web.md#Component Architecture]
- [Source: docs/architecture-api.md#Domain Routes]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx]
- [Source: apps/web/src/components/action-engine/InsightSection.tsx]
- [Source: apps/web/src/components/action-engine/types.ts]
- [Source: apps/web/src/components/action-engine/PriorityBadge.tsx]
- [Source: apps/web/src/components/ui/badge.tsx]
- [Source: apps/web/src/hooks/useDailyActions.ts]
- [Source: apps/web/src/components/action-engine/index.ts]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
