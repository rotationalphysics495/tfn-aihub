# Story 12.6: Schedule Attainment UI Section

Status: ready-for-dev

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

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
