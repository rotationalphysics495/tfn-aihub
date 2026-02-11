# Story 12.6: Schedule Attainment UI Section

Status: done

## Story

As a Plant Manager,
I want a schedule attainment section on the morning report showing planned vs. actual by product,
so that I can see at a glance whether we made the right stuff.

## Acceptance Criteria

1. **Given** schedule attainment data exists for the report date, **When** the morning report loads, **Then** a "Schedule Attainment" section appears between the MorningSummarySection and the "Today's Action Items" section, **And** each workcenter shows: scheduled products, actual products, attainment % per product, **And** variance callouts are highlighted (wrong product runs, underproduction by SKU).

2. **Given** a product was swapped (different product produced than scheduled), **When** the attainment section renders, **Then** the swap is highlighted in amber/orange with text like "Ran Colombian instead of scheduled Brazilian".

3. **Given** no schedule data exists for the date, **When** the attainment section renders, **Then** a prompt appears: "No schedule uploaded for this date. Upload schedule ->" with a link to `/settings/schedule-upload`.

4. **Given** the overall product mix is shown, **When** the user views the section, **Then** a simple bar comparison shows planned vs. actual mix percentages using Recharts `BarChart`.

## Tasks / Subtasks

- [ ] Task 1: Create `useScheduleAttainment` data fetching hook (AC: #1, #3)
  - [ ] 1.1 Create `apps/web/src/hooks/useScheduleAttainment.ts`
  - [ ] 1.2 Define TypeScript interfaces for API response types
  - [ ] 1.3 Implement fetch with Bearer token auth (follow `useDailyActions` pattern)
  - [ ] 1.4 Handle empty/no-schedule state with `hasSchedule` boolean
  - [ ] 1.5 Accept `date` parameter for report date (default T-1)
- [ ] Task 2: Create `ScheduleAttainment.tsx` main section component (AC: #1, #3)
  - [ ] 2.1 Create `apps/web/src/components/production/ScheduleAttainment.tsx`
  - [ ] 2.2 Render workcenter-grouped attainment cards using `Card mode="retrospective"`
  - [ ] 2.3 Show per-product rows: product name, scheduled qty, actual qty, attainment %
  - [ ] 2.4 Display overall workcenter attainment percentage
  - [ ] 2.5 Implement empty state with upload link when no schedule data
  - [ ] 2.6 Add loading skeleton following `InsightEvidenceCardSkeleton` pattern
- [ ] Task 3: Create `ProductVarianceCallout.tsx` component (AC: #2)
  - [ ] 3.1 Create `apps/web/src/components/production/ProductVarianceCallout.tsx`
  - [ ] 3.2 Highlight product swaps in amber/orange with descriptive text
  - [ ] 3.3 Highlight underproduction with percentage shortfall
  - [ ] 3.4 Use existing Tailwind color tokens: `warning-amber` for swaps
- [ ] Task 4: Create product mix comparison bar chart (AC: #4)
  - [ ] 4.1 Add Recharts `BarChart` with planned vs. actual grouped bars
  - [ ] 4.2 Use `ResponsiveContainer` for responsive sizing
  - [ ] 4.3 Apply Industrial Clarity color palette from Tailwind theme
- [ ] Task 5: Integrate into morning report page (AC: #1)
  - [ ] 5.1 Import `ScheduleAttainment` in `apps/web/src/app/(main)/morning-report/page.tsx`
  - [ ] 5.2 Position between `MorningSummarySection` and the action items `section`
  - [ ] 5.3 Wrap in `section` element with `aria-label="Schedule attainment"`
- [ ] Task 6: Update production components barrel export
  - [ ] 6.1 Add `ScheduleAttainment` and `ProductVarianceCallout` to `apps/web/src/components/production/index.ts`

## Dev Notes

### Architecture & Patterns

- **Component location:** All new components go in `apps/web/src/components/production/` -- this directory already exists with `ThroughputDashboard`, `StatusBadge`, `EmptyState`, etc.
- **Hook location:** `apps/web/src/hooks/useScheduleAttainment.ts` -- follows existing pattern alongside `useDailyActions.ts`, `useSafetyAlerts.ts`, `useSmartSummary.ts`.
- **Morning report page location:** The actual page is at `apps/web/src/app/(main)/morning-report/page.tsx` (note the `(main)` route group -- NOT directly under `app/morning-report/`).
- **Card styling:** Use `<Card mode="retrospective">` for all cards since this is T-1 historical data, consistent with `MorningSummarySection` and `InsightEvidenceCard`.
- **API endpoint:** This hook calls `GET /api/v1/production/schedule-attainment?date={date}` (created in Story 12.5).

### API Authentication Pattern

Follow the exact auth pattern from `useDailyActions.ts`:
```typescript
const supabase = createClient()  // from '@/lib/supabase/client'
const { data: { session } } = await supabase.auth.getSession()
// Use: Authorization: `Bearer ${session.access_token}`
```
Do NOT use `credentials: 'include'` (cookie-based) -- use Bearer token in Authorization header.

### API Response Shape (from Story 12.5)

The `GET /api/v1/production/schedule-attainment?date={date}` endpoint returns:
```typescript
interface ScheduleAttainmentResponse {
  workcenters: WorkcenterAttainment[]
  report_date: string
  has_schedule: boolean
  message?: string  // e.g., "No schedule data for this date"
}

interface WorkcenterAttainment {
  workcenter_name: string  // e.g., "Roasting", "Grinding"
  overall_attainment_pct: number
  products: ProductAttainment[]
  variance_callouts: VarianceCallout[]
}

interface ProductAttainment {
  product_name: string
  scheduled_quantity: number
  actual_quantity: number
  attainment_pct: number
}

interface VarianceCallout {
  type: 'product_swap' | 'underproduction' | 'unscheduled'
  asset_name: string
  message: string  // e.g., "Roaster 1 ran Colombian instead of scheduled Brazilian"
  scheduled_product?: string
  actual_product?: string
  quantity_gap?: number
}
```

### Color Tokens & Styling

Use existing Tailwind/Industrial Clarity tokens:
- **On-target attainment (>=95%):** `text-success-green` / green badge
- **Warning attainment (80-94%):** `text-warning-amber` / amber badge
- **Critical attainment (<80%):** `text-safety-red` / red badge
- **Product swap callouts:** `bg-warning-amber/10` background with `text-warning-amber-dark dark:text-warning-amber` text and amber left border
- **Unscheduled production:** `bg-info-blue/10` with `text-info-blue`

### Recharts Configuration

- The project uses `Recharts 3.6+` (confirmed in `architecture-web.md`)
- Import from `'recharts'`: `BarChart`, `Bar`, `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip`, `Legend`, `ResponsiveContainer`
- Wrap charts in `<ResponsiveContainer width="100%" height={250}>` for proper responsive behavior
- Use CSS variable colors for chart bars: `hsl(var(--info-blue))` for planned, `hsl(var(--success-green))` for actual

### Key Existing Components to Reuse

- `Card`, `CardContent`, `CardHeader`, `CardTitle` from `@/components/ui/card`
- `Badge` from `@/components/ui/badge`
- `cn()` from `@/lib/utils` for conditional class names
- `EmptyState` from `@/components/production/EmptyState` for no-data state (or create a custom one with upload link)
- `StatusBadge` from `@/components/production/StatusBadge` as reference for attainment status styling

### Morning Report Page Integration

Current page structure in `apps/web/src/app/(main)/morning-report/page.tsx`:
```tsx
<SafetyAlertsSection />
<Breadcrumb />
<div className="mb-6 md:mb-8">  {/* Page Header */}
<div className="space-y-6">
  <MorningSummarySection />
  {/* INSERT ScheduleAttainment HERE */}
  <section aria-label="Action items with evidence">
    <InsightEvidenceCardList />
  </section>
</div>
```

The new `<ScheduleAttainment />` goes inside the `space-y-6` div, between `MorningSummarySection` and the action items section. This page is a Server Component -- `ScheduleAttainment` must be a Client Component (add `'use client'` directive) since it fetches data client-side.

### Critical Anti-Patterns to Avoid

1. **Do NOT create a new route/page** -- this is a section within the existing morning report page.
2. **Do NOT use `fetch` with `credentials: 'include'`** -- use Bearer token auth pattern.
3. **Do NOT hard-code the API URL** -- use `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`.
4. **Do NOT put components in `app/(main)/morning-report/`** -- components go in `components/production/`.
5. **Do NOT import from `recharts` without `'use client'`** -- Recharts requires client-side rendering.
6. **Do NOT use `mode="live"` on cards** -- this is retrospective T-1 data, use `mode="retrospective"`.

### Project Structure Notes

- Alignment with unified project structure: All files follow existing domain-based organization in `components/production/` and `hooks/`.
- The morning report page uses named imports from barrel exports -- update `components/production/index.ts` to export new components.
- No conflicts with existing components detected -- `ScheduleAttainment` and `ProductVarianceCallout` are new files.

### Dependencies

- **Story 12.5 (Schedule Attainment API):** This story depends on the API endpoint created in 12.5. If the API is not yet available, create the hook with the expected response shape and test with mock data.
- **Story 12.1 (Data Model):** The `products`, `production_schedule`, and `production_actuals` tables must exist.
- **Story 12.2 (Seed Data):** Seed data should be available for development/testing.

### References

- [Source: _bmad-output/planning-artifacts/epic-12.md#Story 12.6] - Story requirements and acceptance criteria
- [Source: docs/architecture-web.md#Directory Structure] - Component organization and technology stack
- [Source: docs/architecture-web.md#Component Architecture] - Component category patterns
- [Source: docs/architecture-api.md#Domain Routes] - API routing patterns (`/api/production`)
- [Source: docs/data-models.md#Core Tables] - Assets table with `area` column for workcenter grouping
- [Source: apps/web/src/hooks/useDailyActions.ts] - Auth pattern and hook structure reference
- [Source: apps/web/src/components/action-list/MorningSummarySection.tsx] - Card styling and layout reference
- [Source: apps/web/src/app/(main)/morning-report/page.tsx] - Integration point and page structure
- [Source: apps/web/src/components/ui/card.tsx] - Card mode variants (retrospective/live)
- [Source: apps/web/src/components/production/index.ts] - Barrel export pattern for production components
- [Source: _bmad-output/planning-artifacts/epics-improvements.md#FR-I2] - FR-I2 Schedule Attainment & Product Mix requirements

## Dev Agent Record

### Implementation Summary
Implemented the Schedule Attainment UI section for the morning report page. Created a data-fetching hook (`useScheduleAttainment`) following the established `useWorkcenterSummary` pattern with Bearer token auth, mountedRef lifecycle management, and API response mapping. Built three presentation components: `ScheduleAttainment` (main section with four states: loading/error/empty/success), `ProductVarianceCallout` (color-coded variance callouts for swaps/underproduction/unscheduled), and `ProductMixChart` (Recharts grouped BarChart showing planned vs actual mix percentages). Integrated the section into the morning report page between WorkcenterScorecard and action items.

### Files Created
- apps/web/src/hooks/useScheduleAttainment.ts - Data-fetching hook with Bearer token auth, API response mapping, auto-fetch on mount
- apps/web/src/components/production/ScheduleAttainment.tsx - Main section component with loading/error/empty/success states
- apps/web/src/components/production/ProductVarianceCallout.tsx - Variance callout component with amber (swap/underproduction) and blue (unscheduled) styling
- apps/web/src/components/production/ProductMixChart.tsx - Recharts BarChart showing planned vs actual product mix percentages

### Files Modified
- apps/web/src/components/production/index.ts - Added barrel exports for ScheduleAttainment, ProductVarianceCallout, ProductMixChart
- apps/web/src/app/(main)/morning-report/page.tsx - Imported ScheduleAttainment and placed it between WorkcenterScorecard and action items section

### Key Decisions
- API response mapping: The actual API (Story 12.5) uses field names `workcenter`, `variances`, `variance_type`, `has_data`, `date` while the UI tests expect `workcenter_name`, `variance_callouts`, `type`, `has_schedule`, `report_date`. The hook includes a `mapApiResponse` function that normalizes both shapes, supporting either API version seamlessly.
- Attainment color thresholds: Used >=95 green, >=80 amber, <80 red to match the test expectations (tests check `class` for 80.0% attainment expects amber, which differs from WorkcenterRow's >=85 threshold). This aligns with the story's color spec.
- Placed ScheduleAttainment after WorkcenterScorecard (not directly after MorningSummarySection) since WorkcenterScorecard was added in Epic 11. This keeps production data sections together.

### Tests Added
- apps/web/src/hooks/__tests__/useScheduleAttainment.test.ts - 12 tests covering auth, endpoint, date defaults, loading states, error handling, refetch, unmount safety, empty state
- apps/web/src/components/production/__tests__/ScheduleAttainment.test.tsx - 18 tests covering section rendering, workcenter cards, product rows, attainment colors, variance callouts, loading/error/empty states, className prop
- apps/web/src/components/production/__tests__/ProductVarianceCallout.test.tsx - 6 tests covering swap/underproduction/unscheduled styling, icons, ordering, message text
- apps/web/src/components/production/__tests__/ProductMixChart.test.tsx - 7 tests covering chart rendering, mix percentages, responsive container, legend, empty state, color tokens, DOM order
- apps/web/src/app/(main)/morning-report/__tests__/page.test.tsx - 1 integration test verifying ScheduleAttainment positioned between WorkcenterScorecard and action items

### Notes for Reviewer
- All 44 TDD tests pass (tests were pre-written, implementation makes them pass)
- Pre-existing test failures in unrelated files (action-list, command-center, handoff, voice, etc.) are not caused by these changes
- The hook maps API response fields to support both the actual API schema (12.5) and the test fixture schema — this ensures forward compatibility

### Test Results
All 44 Story 12.6 tests pass:
- useScheduleAttainment.test.ts: 12/12 passed
- ScheduleAttainment.test.tsx: 18/18 passed
- ProductVarianceCallout.test.tsx: 6/6 passed
- ProductMixChart.test.tsx: 7/7 passed
- page.test.tsx (integration): 1/1 passed

### Acceptance Criteria Status
- [x] AC1 - Schedule attainment section with workcenter/product breakdown - implemented in ScheduleAttainment.tsx, useScheduleAttainment.ts, page.tsx
- [x] AC2 - Product swap highlighting in amber/orange - implemented in ProductVarianceCallout.tsx
- [x] AC3 - No schedule data prompt with upload link - implemented in ScheduleAttainment.tsx (empty state)
- [x] AC4 - Product mix bar comparison chart - implemented in ProductMixChart.tsx

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-11
**Diff Size**: 2123 lines (12 files)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | `useScheduleAttainment` initializes `isLoading: true` while all other hooks initialize `isLoading: false` — minor pattern inconsistency, but arguably better UX | LOW | Documented |
| 2 | `date` query parameter not URI-encoded — matches existing pattern in all other hooks, date format is safe | LOW | Documented |
| 3 | Array index used as React key for variance callouts (`key={i}`) — acceptable since list is static per render | LOW | Documented |
| 4 | `mapApiResponse` uses extensive type assertions for dual-schema support — adds complexity but justified for API compatibility | LOW | Documented |
| 5 | Missing 404 response handling in `useScheduleAttainment` — `useWorkcenterSummary` handles 404 gracefully but this hook did not | MEDIUM | Fixed |
| 6 | Section placed after WorkcenterScorecard rather than directly after MorningSummarySection — intentional grouping of production sections, story spec predates WorkcenterScorecard | LOW | Documented |

**Totals**: 0 HIGH, 1 MEDIUM, 5 LOW

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 5 | Added explicit 404 response handling that returns empty state (`has_schedule: false`, empty workcenters) consistent with `useWorkcenterSummary` pattern | All 44 tests pass |

### Remaining Issues (Low Severity)
- Issue 1: Initial `isLoading` state differs from other hooks (cosmetic, actually better behavior)
- Issue 2: URL parameter encoding (matches project-wide pattern, safe for date strings)
- Issue 3: Array index keys for variance callouts (static list, no reordering)
- Issue 4: Dual-schema mapping complexity (justified for API compatibility)
- Issue 6: Section positioning (intentional architectural decision)

### Final Status
Approved with fixes

## Test Quality Review

**Reviewer**: Test Architect (TEA)
**Date**: 2026-02-11
**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 44 across 5 files

### Quality Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | BDD Format (Given-When-Then) | PASS | All 44 tests use explicit Given-When-Then comments |
| 2 | Test ID Conventions | PASS | All tests have IDs (UNIT-001–043, INT-001) |
| 3 | Hard Waits Detection | PASS | No hard waits; uses waitFor() properly |
| 4 | Determinism | PASS | No random values, no conditional flow control |
| 5 | Isolation & Cleanup | PASS | beforeEach/afterEach with clearAllMocks/restoreAllMocks in all suites |
| 6 | Explicit Assertions | PASS | Every test has explicit expect() assertions |
| 7 | Test Length | WARN | ScheduleAttainment.test.tsx at 529 lines (justified by 18 tests across 2 ACs) |
| 8 | Test Duration | PASS | All 44 tests complete in <1s total |
| 9 | Fixture Patterns | PASS | Comprehensive factory functions with overrides in all files |
| 10 | Data Factories | PASS | All test data via factories, no hardcoded magic values |
| 11 | Network-First Pattern | N/A | Unit tests with mocked hooks, not E2E |
| 12 | Flakiness Patterns | PASS | No tight timeouts, race conditions, or timing dependencies |

### Issues Found
- 0 Critical
- 0 High
- 2 Medium: Test file lengths (ScheduleAttainment.test.tsx 529 lines, useScheduleAttainment.test.ts 399 lines) — both justified by comprehensive coverage and well-organized sections
- 0 Low

### Fixes Applied
- None required

### Bonus Points Awarded
- Excellent BDD structure (+5)
- Comprehensive fixture patterns (+5)
- Perfect isolation (+5)
- All test IDs present (+5)
