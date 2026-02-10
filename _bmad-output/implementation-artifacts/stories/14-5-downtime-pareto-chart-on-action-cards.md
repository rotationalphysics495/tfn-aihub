# Story 14.5: Downtime Pareto Chart on Action Cards

Status: ready-for-dev

## Story

As a Plant Manager,
I want to see a reason code breakdown chart on action items that have downtime,
so that I can understand *why* an asset lost time and direct investigations effectively.

## Acceptance Criteria

1. **Given** an action item is an OEE-miss or downtime-related item, **When** the action card renders and downtime Pareto data is available, **Then** a horizontal bar chart shows the top 3-5 reason codes sorted by duration, **And** each bar shows: reason code name, duration in minutes, percentage of total, **And** planned vs. unplanned downtime is visually distinguished (e.g., hatched vs. solid bars).

2. **Given** an action item is a safety-only or financial-only item (no downtime component), **When** the card renders, **Then** no Pareto chart is shown.

3. **Given** the Pareto data is loading, **When** the card renders, **Then** a skeleton loader placeholder is shown where the chart would be.

## Tasks / Subtasks

- [ ] Task 1: Create `useDowntimePareto` data-fetching hook (AC: #1, #3)
  - [ ] 1.1 Define `DowntimeParetoData` TypeScript interface matching backend `ParetoResponse`
  - [ ] 1.2 Implement hook with `useState`/`useEffect` pattern matching `useDailyActions` hook conventions
  - [ ] 1.3 Accept `assetId` and `date` params; call `GET /api/v1/downtime/pareto?asset_id={id}&start_date={date}`
  - [ ] 1.4 Include Supabase auth token in request header (same pattern as `useDailyActions`)
  - [ ] 1.5 Handle loading, error, and empty states
  - [ ] 1.6 Return `{ data, isLoading, error, refetch }` matching project hook conventions

- [ ] Task 2: Create `DowntimePareto.tsx` component (AC: #1, #2, #3)
  - [ ] 2.1 Create horizontal `BarChart` using Recharts (already installed; see existing `ParetoChart.tsx` in `downtime/`)
  - [ ] 2.2 Display top 3-5 reason codes as horizontal bars sorted by `total_minutes` descending
  - [ ] 2.3 Each bar label shows: reason code name, duration in minutes, percentage of total
  - [ ] 2.4 Visually distinguish planned vs. unplanned downtime (solid fill for unplanned, hatched/striped pattern for planned via CSS/SVG)
  - [ ] 2.5 Use Industrial Clarity color palette consistent with existing `ParetoChart.tsx`
  - [ ] 2.6 Build a skeleton loader variant (`DowntimeParetoSkeleton`) for loading state (AC #3)
  - [ ] 2.7 Return `null` when category is not `oee` (AC #2 — no chart for safety/financial-only items)
  - [ ] 2.8 Handle empty Pareto data gracefully (no chart, no error)
  - [ ] 2.9 Ensure dark mode support via Tailwind `dark:` variants

- [ ] Task 3: Integrate `DowntimePareto` into `EvidenceSection.tsx` (AC: #1, #2)
  - [ ] 3.1 Import `DowntimePareto` and `useDowntimePareto` into `EvidenceSection`
  - [ ] 3.2 Conditionally render below existing evidence content when `evidence.type === 'oee_deviation'`
  - [ ] 3.3 Pass `assetId` and `date` from evidence source to hook
  - [ ] 3.4 Show skeleton while loading, chart when loaded, nothing for non-OEE items

- [ ] Task 4: Update barrel exports and types (AC: #1)
  - [ ] 4.1 Export `DowntimePareto` and `DowntimeParetoSkeleton` from `action-engine/index.ts`
  - [ ] 4.2 Add Pareto-related types to `action-engine/types.ts` if needed

- [ ] Task 5: Write tests (AC: #1, #2, #3)
  - [ ] 5.1 Unit test `useDowntimePareto` hook: loading, success, error, empty states
  - [ ] 5.2 Component test `DowntimePareto`: renders bars for OEE items, renders nothing for safety/financial items
  - [ ] 5.3 Component test skeleton loader display during loading state
  - [ ] 5.4 Integration test: `EvidenceSection` with Pareto chart conditional rendering

## Dev Notes

### Architecture Patterns and Constraints

**Technology Stack (MUST follow):**
- **Framework:** Next.js 14+ with App Router
- **Language:** TypeScript 5.x (strict mode)
- **Styling:** Tailwind CSS 3.4+ with `cn()` utility from `@/lib/utils`
- **UI Library:** Radix UI + Shadcn/UI primitives
- **Charts:** Recharts 3.6+ (already installed, already used extensively)
- **Testing:** Vitest + Testing Library

**Existing Recharts Patterns to Reuse:**
- `apps/web/src/components/downtime/ParetoChart.tsx` -- Full-size Pareto chart using `ComposedChart`, `Bar`, `Line`, `XAxis`, `YAxis`, `ResponsiveContainer`, `Cell`, `ReferenceLine` from Recharts. This is the _full dashboard version_; story 14-5 creates a _compact inline version_ for action cards.
- Color palette constants: `CHART_COLORS` object with `bar.retrospective`, `bar.live`, `barSafety`, `line.*`, `threshold` values using HSL.
- Custom tooltip pattern: render a `<div>` with `bg-card border border-border rounded-lg shadow-lg p-3`.

**Key Difference from Existing ParetoChart:**
The existing `ParetoChart.tsx` is a full-page dashboard component inside a `Card` wrapper. Story 14-5 needs a **compact, inline horizontal bar chart** embedded inside the `EvidenceSection` of an `InsightEvidenceCard`. It should be small (~120-150px height), without its own Card wrapper, without the cumulative % line, and without the full legend. Think "sparkline-sized Pareto," not "dashboard Pareto."

### Existing Data Flow (CRITICAL -- Do Not Reinvent)

**Backend API already exists:**
- `GET /api/v1/downtime/pareto` -- Returns `ParetoResponse` with `items: ParetoItem[]`, `total_downtime_minutes`, `total_financial_impact`, `total_events`, `threshold_80_index`
- Each `ParetoItem` has: `reason_code`, `total_minutes`, `percentage`, `cumulative_percentage`, `financial_impact`, `event_count`, `is_safety_related`
- Supports query params: `start_date`, `end_date`, `asset_id`, `area`, `source`
- Authentication: Bearer token from Supabase session (same as `useDailyActions`)

**Backend Pareto Model (`apps/api/app/models/downtime.py`):**
```python
class ParetoItem(BaseModel):
    reason_code: str
    total_minutes: int
    percentage: float
    cumulative_percentage: float
    financial_impact: float
    event_count: int
    is_safety_related: bool

class ParetoResponse(BaseModel):
    items: List[ParetoItem]
    total_downtime_minutes: int
    total_financial_impact: float
    total_events: int
    data_source: str
    last_updated: str
    threshold_80_index: Optional[int]
```

**NOTE:** The `ParetoItem` does NOT have an `is_planned` field from the existing model. The `downtime_events` table (Story 14.1) introduces `is_planned` but the existing `ParetoResponse` aggregates by `reason_code` without a planned/unplanned split. For AC #1's "planned vs. unplanned" visual distinction, the developer has two options:
1. Use `reason_code` name as a proxy -- "Planned Maintenance" reason_code = planned, all others = unplanned. (Simpler, recommended for this story.)
2. Add a new backend field `planned_minutes` to `ParetoItem`. (Better long-term, but requires API change outside this story's scope.)

Recommend approach #1 for this story. The standard reason codes from Story 14.1 are: Mechanical, Changeover, Material Shortage, Quality Hold, Operator Unavailable, **Planned Maintenance**. Check if `reason_code === 'Planned Maintenance'` to flag as planned.

### Existing Hook Pattern to Follow

**Reference: `apps/web/src/hooks/useDailyActions.ts`**
- Uses `useState`, `useEffect`, `useCallback`, `useRef` (for mount tracking)
- Gets Supabase session via `createClient()` from `@/lib/supabase/client`
- Passes Bearer token in `Authorization` header
- Returns `{ data, isLoading, error, refetch }` pattern
- Handles auth errors, network errors, 404s
- Default API URL from `NEXT_PUBLIC_API_URL` env var

### Existing Component Integration Points

**`EvidenceSection.tsx` (`apps/web/src/components/action-engine/EvidenceSection.tsx`):**
- Already has type-based rendering: `SafetyEvidenceDisplay`, `OEEEvidenceDisplay`, `FinancialEvidenceDisplay`
- The Pareto chart should render inside `OEEEvidenceDisplay` or as an additional section below it when `evidence.type === 'oee_deviation'`
- The `evidence.source` object contains `table`, `date`, `recordId` -- use `date` for the Pareto API call
- Need `asset.id` which is NOT currently passed into `EvidenceSection`. The `InsightEvidenceCard` has `item.asset.id`. Thread the `assetId` prop down, or use the hook at the `InsightEvidenceCard` level and pass data down.

**Recommended approach:** Add an optional `assetId` prop to `EvidenceSection` and an optional `reportDate` prop. Conditionally call `useDowntimePareto` inside `EvidenceSection` when evidence type is `oee_deviation`.

**`InsightEvidenceCard.tsx` already computes `reportDate`:**
```tsx
const reportDate = item.timestamp
  ? item.timestamp.split('T')[0]
  : new Date(Date.now() - 86400000).toISOString().split('T')[0]
```
Pass `item.asset.id` and `reportDate` to `EvidenceSection`.

### Action Engine Type System

**`types.ts` (`apps/web/src/components/action-engine/types.ts`):**
- `Evidence.type` can be: `'safety_event' | 'oee_deviation' | 'financial_loss'`
- Only show Pareto for `'oee_deviation'` type
- `ActionItem.asset.id` provides the asset UUID for the Pareto API call
- `ActionItem.evidence.source.date` provides the report date

**`transformers.ts` maps API categories:**
- `'oee'` category maps to `'oee_deviation'` evidence type -- these are the items that get Pareto charts.

### File Structure Requirements

**Files to Create:**
- `apps/web/src/hooks/useDowntimePareto.ts` -- New data-fetching hook
- `apps/web/src/components/action-engine/DowntimePareto.tsx` -- Compact horizontal bar chart + skeleton

**Files to Modify:**
- `apps/web/src/components/action-engine/EvidenceSection.tsx` -- Add Pareto chart integration
- `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` -- Pass `assetId` and `reportDate` to `EvidenceSection`
- `apps/web/src/components/action-engine/index.ts` -- Export new components

**Do NOT Modify:**
- `apps/api/app/api/downtime.py` -- Backend already has the Pareto endpoint
- `apps/api/app/models/downtime.py` -- Backend models already correct
- `apps/web/src/components/downtime/ParetoChart.tsx` -- This is the dashboard Pareto, leave untouched

### Testing Standards

- **Framework:** Vitest + React Testing Library
- **Test location:** `apps/web/src/components/action-engine/__tests__/` for component tests, `apps/web/src/hooks/__tests__/` for hook tests
- **Existing test examples:**
  - `apps/web/src/components/downtime/__tests__/ParetoChart.test.tsx` -- test patterns for Pareto chart
  - `apps/web/src/components/chat/__tests__/ChatMessage.test.tsx` -- component test patterns
- **Run tests:** `cd apps/web && npm run test`
- **Mock `fetch` for API calls**, mock `createClient` for Supabase auth

### UI/UX Requirements

- **Industrial Clarity Design System:** Inter font, high contrast, readable at 3 feet on control room monitors
- **Dark/light mode:** All new components must support both via Tailwind `dark:` variants
- **Responsive:** Chart should work on `md:` breakpoint (tablet) and desktop
- **Skeleton loaders:** Use `animate-pulse` with `bg-industrial-200 dark:bg-industrial-700` (consistent with `InsightEvidenceCardSkeleton`)
- **No Pareto for non-OEE items:** AC #2 is critical -- only OEE/downtime cards show the chart

### Cross-Story Dependencies

- **Story 14.1 (Downtime Events Data Model):** Creates the `downtime_events` table with `is_planned`, `reason_code`, `duration_minutes`. Must be complete before seed data produces meaningful Pareto results.
- **Story 14.3 (Downtime Pareto API Endpoint):** Creates/enhances `GET /api/v1/downtime/pareto`. The endpoint already exists from Story 2.5 but Story 14.3 enhances it with `downtime_events` table queries. If 14.3 is not yet complete, the existing Pareto endpoint still works with `daily_summaries` data.
- **Story 14.4 (Trend Indicators on Action Cards):** Adds `TrendIndicator.tsx` and `RepeatOffenderBadge.tsx` to action cards. Coordinate to avoid conflicting changes to `InsightEvidenceCard.tsx` and `EvidenceSection.tsx`.

### Project Structure Notes

- All new hooks go in `apps/web/src/hooks/` (root hooks directory, not `lib/hooks/`)
- Action engine components stay in `apps/web/src/components/action-engine/`
- Follow existing barrel export pattern in `index.ts`
- Use `'use client'` directive for all React components with hooks

### References

- [Source: _bmad-output/planning-artifacts/epic-14.md#Story 14.5]
- [Source: docs/architecture-web.md#Technology Stack]
- [Source: docs/architecture-web.md#Component Architecture]
- [Source: docs/architecture-api.md#Domain Routes]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: apps/api/app/models/downtime.py#ParetoItem, ParetoResponse]
- [Source: apps/api/app/api/downtime.py#get_downtime_pareto]
- [Source: apps/web/src/components/downtime/ParetoChart.tsx] -- Existing full-dashboard Pareto (DO NOT duplicate, create compact inline version)
- [Source: apps/web/src/hooks/useDailyActions.ts] -- Hook pattern to follow
- [Source: apps/web/src/components/action-engine/EvidenceSection.tsx] -- Integration target
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx] -- Parent component to modify
- [Source: apps/web/src/components/action-engine/types.ts] -- Type system for action items

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
