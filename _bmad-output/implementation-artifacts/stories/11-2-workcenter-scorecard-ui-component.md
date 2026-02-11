# Story 11.2: Workcenter Scorecard UI Component

Status: done

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

- [x] Task 1: Create `useWorkcenterSummary` data fetching hook (AC: #1, #3)
  - [x] 1.1 Define TypeScript interfaces for workcenter summary response matching the API contract from Story 11.1
  - [x] 1.2 Implement hook with Bearer token auth pattern (follow `useDailyActions` pattern exactly)
  - [x] 1.3 Add loading, error, and empty state handling
  - [x] 1.4 Default date to T-1 (yesterday) when no date parameter provided
- [x] Task 2: Create `WorkcenterScorecard.tsx` main container component (AC: #1, #3)
  - [x] 2.1 Implement container with loading skeleton, error state with retry, and empty state
  - [x] 2.2 Render list of `WorkcenterRow` components from API data
  - [x] 2.3 Add section header "Production Scorecard" with appropriate styling
- [x] Task 3: Create `WorkcenterRow.tsx` expandable row component (AC: #1, #2)
  - [x] 3.1 Display workcenter name, actual/target output, attainment %, and asset hit/miss count
  - [x] 3.2 Implement attainment color coding: green >= 95%, yellow 85-94%, red < 85%
  - [x] 3.3 Add click/expand toggle to reveal `AssetDetailTable`
  - [x] 3.4 Use simple React state toggle (Option A from Dev Notes - no new dependency needed)
- [x] Task 4: Create `AssetDetailTable.tsx` expanded detail component (AC: #2)
  - [x] 4.1 Display table with columns: asset name, actual vs. target, OEE %, downtime minutes
  - [x] 4.2 Color-code each asset row: green if actual >= target, red if missed
  - [x] 4.3 Format numbers for readability (use `toLocaleString()` for comma separation)
- [x] Task 5: Create barrel export `index.ts` for production scorecard components (AC: all)
  - [x] 5.1 Export all new components from `components/production/index.ts` (update existing barrel)
- [x] Task 6: Integrate scorecard into morning report page (AC: #1)
  - [x] 6.1 Import `WorkcenterScorecard` into `apps/web/src/app/(main)/morning-report/page.tsx`
  - [x] 6.2 Position scorecard between `MorningSummarySection` and the action items section
  - [x] 6.3 Ensure scorecard renders as a client component wrapper if needed (page is server component)
- [x] Task 7: Ensure glanceability and responsive design (AC: #4)
  - [x] 7.1 Use large font sizes for key numbers (text-3xl for attainment %)
  - [x] 7.2 Test responsive layout on tablet-size viewports
  - [x] 7.3 Ensure touch-friendly expand/collapse targets (min 44px tap target)

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

Claude Opus 4.6

### Implementation Summary

Implemented the Workcenter Scorecard UI component for the morning report page. The scorecard displays one expandable row per workcenter showing production attainment with color-coded performance indicators (green/yellow/red). Each row can be expanded to reveal per-asset detail tables with hit/miss color coding. The component includes loading skeleton, error state with retry, and empty state handling.

### Files Created
- `apps/web/src/hooks/useWorkcenterSummary.ts` - Data fetching hook with Bearer token auth, T-1 date default, 404-as-empty-state handling, mountedRef cleanup
- `apps/web/src/components/production/AssetDetailTable.tsx` - Per-asset breakdown table with green/red row coloring based on target attainment
- `apps/web/src/components/production/WorkcenterRow.tsx` - Expandable workcenter row with attainment color coding, glanceable typography (text-3xl), 44px touch targets
- `apps/web/src/components/production/WorkcenterScorecard.tsx` - Container component with loading/error/empty/success states following ActionListContainer pattern

### Files Modified
- `apps/web/src/components/production/index.ts` - Added barrel exports for WorkcenterScorecard, WorkcenterRow, AssetDetailTable
- `apps/web/src/app/(main)/morning-report/page.tsx` - Added WorkcenterScorecard between MorningSummarySection and action items section

### Key Decisions
- Used Option A (simple React state toggle) for expand/collapse instead of installing Shadcn Collapsible - simpler, no new dependency
- Used `actual >= target` comparison for asset row hit/miss coloring (matching test expectations for green/red backgrounds)
- Used `\u2014` (em dash) as fallback for null OEE and downtime_minutes values
- Matched test interface exactly: `workcenter_name`, `attainment_percentage`, `assets_on_target`, `total_assets` field names
- 404 responses treated as empty state with synthetic empty WorkcenterSummaryResponse (not error)

### Tests Added
- `apps/web/src/components/production/__tests__/WorkcenterScorecard.test.tsx` - 42 tests covering all 4 ACs (rendering, color coding, expand/collapse, empty state, loading, error, glanceability, page integration)
- `apps/web/src/hooks/__tests__/useWorkcenterSummary.test.ts` - 10 tests covering auth, date defaulting, error handling (401/404/500/network), refetch, unmount cleanup

### Notes for Reviewer
- All 52 tests pass (42 component + 10 hook)
- Tests must be run from `apps/web/` directory (vitest config resolves `@/` alias from there)
- The hook interface matches the story's API contract types (with nullable oee/downtime_minutes for AssetDetail)
- No new npm dependencies added

### Test Results
```
 ✓ src/components/production/__tests__/WorkcenterScorecard.test.tsx  (42 tests) 186ms
 ✓ src/hooks/__tests__/useWorkcenterSummary.test.ts  (10 tests) 495ms

 Test Files  2 passed (2)
      Tests  52 passed (52)
```

### Acceptance Criteria Status
- [x] AC1 - Scorecard renders one row per workcenter with name, actual/target, attainment %, asset count, color coding - implemented in WorkcenterScorecard.tsx, WorkcenterRow.tsx
- [x] AC2 - Click/expand shows per-asset breakdown with name, actual/target, OEE %, downtime, green/red row coloring - implemented in WorkcenterRow.tsx, AssetDetailTable.tsx
- [x] AC3 - Empty state when no data, uses API message or default fallback - implemented in WorkcenterScorecard.tsx, useWorkcenterSummary.ts (404 handling)
- [x] AC4 - Glanceability: text-3xl font-bold tabular-nums for attainment, text-lg font-semibold for names, 44px touch targets - implemented in WorkcenterRow.tsx

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-11
**Diff Size**: 1751 lines (9 files changed)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Redundant `role="button"` on native `<button>` element in WorkcenterRow.tsx:29 — violates WCAG best practice (implicit role is sufficient) | MEDIUM | Fixed |
| 2 | `workcenter_name` used as React list key in WorkcenterScorecard.tsx:99 — potential collision if duplicate names exist in data | LOW | Documented |
| 3 | `asset_name` used as React list key in AssetDetailTable.tsx:27 — same collision risk as #2 | LOW | Documented |
| 4 | `Content-Type: application/json` header on GET request is semantically unnecessary (no body) — matches existing project convention | LOW | Documented |
| 5 | `isLoading` initializes as `false` with `autoFetch: true`, brief flash possible before fetch starts — matches canonical `useDailyActions` pattern | LOW | Documented |

**Totals**: 0 HIGH, 1 MEDIUM, 4 LOW

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 1 | Removed redundant `role="button"` from native `<button>` element in WorkcenterRow.tsx | Tests pass (52/52) |

### Remaining Issues (Low Severity)
- Issues #2-3: List key collision risk is theoretical — API data is expected to have unique names. Could add index-based keys in a future cleanup.
- Issue #4: Content-Type on GET is harmless and matches project convention. No action needed.
- Issue #5: Initial isLoading state matches canonical hook pattern. Would require codebase-wide refactor to change.

### Review Notes
- All 52 tests pass (42 component + 10 hook)
- Auth pattern correctly follows `useDailyActions.ts` canonical pattern (Bearer token via Supabase session)
- Color coding thresholds match spec: green >= 95%, yellow 85-94%, red < 85%
- Color tokens (`success-green-dark`, `warning-amber-dark`, `safety-red`, `success-green-light`, `safety-red-light`) all exist in project Tailwind config
- Component follows existing container pattern (loading -> error -> empty -> success) from ActionListContainer.tsx
- Page integration correctly positions scorecard between MorningSummarySection and action items
- No new dependencies added
- No security issues found (no user input injection vectors, proper auth handling)

### Final Status
Approved with fixes

## Test Quality Review

**Reviewer**: Test Architect (TEA)
**Date**: 2026-02-11
**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 52 (42 component + 10 hook)

### Files Reviewed
- `apps/web/src/components/production/__tests__/WorkcenterScorecard.test.tsx` (42 tests, 908 lines)
- `apps/web/src/hooks/__tests__/useWorkcenterSummary.test.ts` (10 tests, 342 lines)

### Criteria Results

| Criterion | WorkcenterScorecard.test.tsx | useWorkcenterSummary.test.ts |
|-----------|-----|------|
| BDD Format (Given-When-Then) | PASS | PASS |
| Test ID Conventions | PASS (UNIT-001–041, INT-001) | PASS (UNIT-042–051) |
| Hard Waits Detection | PASS (none) | PASS (none) |
| Determinism | PASS | PASS |
| Isolation & Cleanup | PASS | PASS |
| Explicit Assertions | PASS | PASS |
| Test Length | WARN (908 lines) | PASS (342 lines) |
| Test Duration | PASS (179ms total) | PASS (488ms total) |
| Fixture Patterns | PASS (excellent) | PASS |
| Data Factories | PASS (5 factories with overrides) | PASS (3 factories with overrides) |
| Network-First Pattern | N/A (unit tests) | N/A (mocked fetch) |
| Flakiness Patterns | PASS (none detected) | PASS (none detected) |

### Issues Found
- 0 Critical
- 0 High
- 1 Medium: WorkcenterScorecard.test.tsx exceeds 500-line threshold (908 lines) — well-organized into 5 describe blocks by AC, splitting would reduce cohesion
- 1 Low: Misleading "No assertion needed" comment in UNIT-051 despite assertion being present (useWorkcenterSummary.test.ts:337)

### Fixes Applied
- None required (no critical or high issues)

### Quality Highlights
- Excellent BDD structure with explicit Given-When-Then comments on every test
- Comprehensive factory pattern: 8 factory functions across both files with Partial override support
- Perfect test isolation: beforeEach/afterEach cleanup, no shared mutable state
- Complete test ID traceability: 52 tests with sequential UNIT-NNN IDs
- Thorough boundary testing: color thresholds at 84.9%, 85.0%, 95.0%, 100.0%, 112.5%
- Null handling tested: OEE and downtime_minutes null cases covered
- All 52 tests pass deterministically in <1s total
