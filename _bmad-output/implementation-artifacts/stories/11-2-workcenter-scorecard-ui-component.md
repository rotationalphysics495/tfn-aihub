# Story 11.2: Workcenter Scorecard UI Component

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want a **visual scorecard at the top of the morning report showing each workcenter's production performance**,
so that **I can absorb the whole plant's performance in 5 seconds**.

## Acceptance Criteria

1. **Given** the morning report page loads with workcenter summary data, **When** the scorecard section renders, **Then** it displays one row per workcenter showing: workcenter name, actual output vs. target output (e.g., "4,200 / 5,000"), attainment percentage with color coding (green >= 95%, yellow 85-94%, red < 85%), and count of assets hit vs. missed (e.g., "3 of 4 assets on target"). The scorecard appears above the action items section.

2. **Given** a workcenter row is clicked or expanded, **When** the detail view opens, **Then** it shows per-asset breakdown: asset name, actual vs. target, OEE %, downtime minutes. Each asset row is color-coded green (hit target) or red (missed).

3. **Given** no workcenter data is available for the date, **When** the scorecard section renders, **Then** it shows an appropriate empty state message.

4. **Given** the page is viewed on a tablet, **When** the scorecard renders, **Then** text and numbers are readable from 3 feet away (NFR-I1 glanceability requirement).

## Tasks / Subtasks

- [ ] Task 1: Create `useWorkcenterSummary` data fetching hook (AC: #1, #3)
  - [ ] 1.1 Define TypeScript interfaces for workcenter summary response matching the API contract from Story 11.1
  - [ ] 1.2 Implement hook with Bearer token auth pattern (follow `useDailyActions` pattern exactly)
  - [ ] 1.3 Add loading, error, and empty state handling
  - [ ] 1.4 Default date to T-1 (yesterday) when no date parameter provided
- [ ] Task 2: Create `WorkcenterScorecard.tsx` main container component (AC: #1, #3)
  - [ ] 2.1 Implement container with loading skeleton, error state with retry, and empty state
  - [ ] 2.2 Render list of `WorkcenterRow` components from API data
  - [ ] 2.3 Add section header "Production Scorecard" with appropriate styling
- [ ] Task 3: Create `WorkcenterRow.tsx` expandable row component (AC: #1, #2)
  - [ ] 3.1 Display workcenter name, actual/target output, attainment %, and asset hit/miss count
  - [ ] 3.2 Implement attainment color coding: green >= 95%, yellow 85-94%, red < 85%
  - [ ] 3.3 Add click/expand toggle to reveal `AssetDetailTable`
  - [ ] 3.4 Use Shadcn Card component with Collapsible pattern (see Dev Notes for implementation without Shadcn Collapsible)
- [ ] Task 4: Create `AssetDetailTable.tsx` expanded detail component (AC: #2)
  - [ ] 4.1 Display table with columns: asset name, actual vs. target, OEE %, downtime minutes
  - [ ] 4.2 Color-code each asset row: green if actual >= target, red if missed
  - [ ] 4.3 Format numbers for readability (use `toLocaleString()` for comma separation)
- [ ] Task 5: Create barrel export `index.ts` for production scorecard components (AC: all)
  - [ ] 5.1 Export all new components from `components/production/index.ts` (update existing barrel)
- [ ] Task 6: Integrate scorecard into morning report page (AC: #1)
  - [ ] 6.1 Import `WorkcenterScorecard` into `apps/web/src/app/(main)/morning-report/page.tsx`
  - [ ] 6.2 Position scorecard between `MorningSummarySection` and the action items section
  - [ ] 6.3 Ensure scorecard renders as a client component wrapper if needed (page is server component)
- [ ] Task 7: Ensure glanceability and responsive design (AC: #4)
  - [ ] 7.1 Use large font sizes for key numbers (text-2xl minimum for attainment %)
  - [ ] 7.2 Test responsive layout on tablet-size viewports
  - [ ] 7.3 Ensure touch-friendly expand/collapse targets (min 44px tap target)

## Dev Notes

### Architecture Compliance

- **Component Location:** All new components go in `apps/web/src/components/production/` -- this directory already exists with ThroughputCard, StatusBadge, EmptyState, etc.
- **Hook Location:** New hook goes in `apps/web/src/hooks/useWorkcenterSummary.ts` -- follows existing pattern alongside `useDailyActions.ts`, `useSafetyAlerts.ts`, `useSmartSummary.ts`.
- **Page Integration:** The morning report page is at `apps/web/src/app/(main)/morning-report/page.tsx` (note the `(main)` route group -- NOT `apps/web/src/app/morning-report/page.tsx`).
- **Design System:** Use Industrial Clarity Design System -- Inter font, Tailwind CSS, Shadcn/UI components (Card, Badge from `@/components/ui/`).
- **Auth Pattern:** All API calls MUST use Bearer token auth via Supabase session. Follow `useDailyActions.ts` exactly: `createClient()` -> `getSession()` -> `Authorization: Bearer ${session.access_token}`.

### API Contract (from Story 11.1)

The hook will call `GET /api/v1/production/workcenter-summary?date={date}` which returns:

```typescript
interface WorkcenterSummaryResponse {
  workcenters: WorkcenterEntry[]
  date: string
  total_actual: number
  total_target: number
  total_attainment: number
}

interface WorkcenterEntry {
  workcenter_name: string       // e.g., "Grinding"
  total_actual: number          // Sum of units_produced for assets in area
  total_target: number          // Sum of target_units for assets in area
  attainment_percentage: number // actual / target * 100
  assets_on_target: number     // Count of assets that hit target
  assets_missed: number        // Count that missed
  total_assets: number         // Total asset count
  assets: AssetDetail[]        // Per-asset breakdown
}

interface AssetDetail {
  asset_name: string
  actual: number
  target: number
  oee: number                  // Decimal (e.g., 85.2)
  downtime_minutes: number
}
```

**IMPORTANT:** This API endpoint is created in Story 11.1. If Story 11.1 is not yet implemented, the hook should gracefully handle 404 responses and show the empty state. Do NOT stub or mock the API in production code.

### Color Coding Logic

Attainment thresholds (consistent with epic spec):
- **Green** (`text-success-green-dark dark:text-success-green`): attainment >= 95%
- **Yellow** (`text-warning-amber-dark dark:text-warning-amber`): attainment 85-94%
- **Red** (`text-safety-red`): attainment < 85%

Asset row colors:
- **Green** background tint: actual >= target
- **Red** background tint: actual < target

Use the existing color tokens from the project's Tailwind config -- do NOT introduce new colors. Reference `ThroughputCard.tsx` for the exact class names used for `success-green`, `warning-amber`, and `safety-red` variants.

### Collapsible Pattern

There is NO existing Shadcn Collapsible component installed. Two options:

**Option A (Preferred):** Use simple React state toggle with CSS transitions:
```tsx
const [isExpanded, setIsExpanded] = useState(false)
// Toggle with click handler, show/hide AssetDetailTable with conditional render
```

**Option B:** Install Shadcn Collapsible via `npx shadcn@latest add collapsible` -- only if the developer prefers the Radix primitive approach. But Option A is simpler and avoids adding a dependency.

### Existing Patterns to Follow

1. **`ThroughputCard.tsx`** (`apps/web/src/components/production/ThroughputCard.tsx`): Shows actual-vs-target visualization with color coding, number formatting (`formatNumber`), progress bars. Reuse the `formatNumber` utility or extract it to a shared util.

2. **`ActionListContainer.tsx`** (`apps/web/src/components/action-list/ActionListContainer.tsx`): Shows the loading -> error -> empty -> data pattern for container components. Follow this exact pattern for `WorkcenterScorecard.tsx`.

3. **`MorningSummarySection.tsx`** (`apps/web/src/components/action-list/MorningSummarySection.tsx`): Shows how components integrate into the morning report page, uses Card component with `mode="retrospective"`, handles loading states.

4. **`useDailyActions.ts`** (`apps/web/src/hooks/useDailyActions.ts`): The canonical hook pattern -- Bearer auth, error messages, `mountedRef` cleanup, `useCallback` for fetch, `autoFetch` option.

### Morning Report Page Integration

Current page structure in `apps/web/src/app/(main)/morning-report/page.tsx`:
```
SafetyAlertsSection
Breadcrumb
Page Header ("Morning Report")
MorningSummarySection
Action Items (InsightEvidenceCardList)
```

After integration, the scorecard should appear between `MorningSummarySection` and the action items:
```
SafetyAlertsSection
Breadcrumb
Page Header ("Morning Report")
MorningSummarySection
WorkcenterScorecard  <-- NEW
Action Items (InsightEvidenceCardList)
```

The page is a **Server Component** (no `'use client'` directive). Since `WorkcenterScorecard` requires client-side data fetching, it must be a client component (`'use client'`). This is fine -- Next.js App Router supports client components imported into server components.

### Number Formatting

Use comma-separated numbers for readability:
- `4,200 / 5,000` (not `4200 / 5000`)
- `95.2%` (one decimal place for percentages)
- `3 of 4 assets on target` (plain English)

Consider extracting or reusing `formatNumber` from `ThroughputCard.tsx` if possible, or create a similar local utility.

### Glanceability (NFR-I1)

- Attainment percentage should be the largest visual element per row (minimum `text-2xl`, ideally `text-3xl`)
- Workcenter name in bold, clearly readable
- Color provides instant status signal without reading numbers
- On tablet viewports (768px+), card padding and font sizes should be generous
- `tabular-nums` font variant for aligned number columns

### Testing Approach

- Vitest + Testing Library for component tests
- Test file location: `apps/web/src/components/production/__tests__/WorkcenterScorecard.test.tsx`
- Key test cases:
  - Renders all workcenters from mock data
  - Correct color coding for each attainment threshold
  - Expand/collapse shows and hides asset detail
  - Empty state when no data
  - Loading skeleton displayed during fetch
  - Error state with retry button

### Project Structure Notes

- All paths align with existing monorepo structure (`apps/web/src/`)
- New files follow domain-based component organization (`components/production/`)
- Hook follows existing convention in `hooks/` directory (not `lib/hooks/`)
- Barrel export update to existing `components/production/index.ts`
- No new dependencies required (uses existing Shadcn Card, Badge, Tailwind)

### Files to Create

| File | Purpose |
|------|---------|
| `apps/web/src/hooks/useWorkcenterSummary.ts` | Data fetching hook for workcenter summary API |
| `apps/web/src/components/production/WorkcenterScorecard.tsx` | Main scorecard container component |
| `apps/web/src/components/production/WorkcenterRow.tsx` | Individual workcenter row with expand/collapse |
| `apps/web/src/components/production/AssetDetailTable.tsx` | Expanded per-asset detail table |

### Files to Modify

| File | Change |
|------|--------|
| `apps/web/src/components/production/index.ts` | Add exports for WorkcenterScorecard, WorkcenterRow, AssetDetailTable |
| `apps/web/src/app/(main)/morning-report/page.tsx` | Import and render WorkcenterScorecard between summary and action items |

### References

- [Source: _bmad-output/planning-artifacts/epic-11.md#Story 11.2]
- [Source: _bmad-output/planning-artifacts/epics-improvements.md#FR-I1]
- [Source: _bmad-output/planning-artifacts/epics-improvements.md#NFR-I1]
- [Source: docs/architecture-web.md#Directory Structure]
- [Source: docs/architecture-web.md#Component Architecture]
- [Source: docs/architecture-api.md#Domain Routes]
- [Source: docs/data-models.md#daily_summaries]
- [Source: docs/data-models.md#shift_targets]
- [Source: docs/data-models.md#assets]
- [Source: apps/web/src/hooks/useDailyActions.ts] -- Auth pattern reference
- [Source: apps/web/src/components/production/ThroughputCard.tsx] -- Color coding and number formatting reference
- [Source: apps/web/src/components/action-list/ActionListContainer.tsx] -- Container pattern reference
- [Source: apps/web/src/app/(main)/morning-report/page.tsx] -- Page integration target

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
