# Story 17.4: Shift Breakdown API & UI

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to see per-shift performance breakdown on the workcenter scorecard and action items**,
so that **I can identify which shift caused a daily miss and direct investigations accordingly**.

## Acceptance Criteria

1. **Given** the workcenter summary endpoint is called with shift data available, **When** the response is returned, **Then** each workcenter entry includes a `shift_breakdown` array with per-shift metrics (shift name, actual output, target output, attainment %, OEE, downtime minutes) **And** the overall workcenter figures are the aggregation across shifts.

2. **Given** the workcenter scorecard renders with shift data, **When** the user clicks a shift tab or toggle (Morning / Afternoon / Night / All), **Then** the scorecard filters to show only that shift's data **And** the action items below also filter to the selected shift.

3. **Given** an action item missed target primarily on one shift, **When** the action card renders, **Then** it shows shift attribution: e.g. "Grinder 5: 72 min downtime (afternoon shift -- 58 min mechanical)" **And** the recommendation targets the responsible shift.

4. **Given** all three shifts missed target (systemic issue), **When** the action card renders, **Then** it remains a daily-level item without shift attribution **And** the recommendation reflects a systemic rather than shift-specific issue.

## Tasks / Subtasks

- [ ] Task 1: Add shift breakdown to workcenter summary API (AC: #1)
  - [ ] 1.1 Create `ShiftBreakdown` Pydantic model in `apps/api/app/schemas/action.py` or a new `schemas/shift.py`
  - [ ] 1.2 Create new endpoint `GET /api/production/workcenter-summary` in `apps/api/app/api/production.py` that queries `daily_summaries` joined with `shift_summaries` and returns per-workcenter data with optional `shift_breakdown` array
  - [ ] 1.3 Add query parameter `?date=YYYY-MM-DD` defaulting to T-1, and optional `?shift=morning|afternoon|night` filter
  - [ ] 1.4 Ensure aggregation: overall workcenter figures = sum of shift values (validate consistency)
  - [ ] 1.5 Write pytest tests for the new endpoint covering: shift data present, shift data absent (graceful fallback), shift filter parameter

- [ ] Task 2: Add shift attribution logic to Action Engine (AC: #3, #4)
  - [ ] 2.1 Add `_get_shift_attribution` method to `ActionEngine` class in `apps/api/app/services/action_engine.py`
  - [ ] 2.2 Query `shift_summaries` table for the target date and asset to get per-shift breakdown
  - [ ] 2.3 Implement attribution logic: if one shift accounts for >60% of the total miss, attribute to that shift; otherwise treat as systemic
  - [ ] 2.4 Add `shift_attribution` optional field to `ActionItem` schema (nullable string, e.g. "afternoon shift -- 58 min mechanical")
  - [ ] 2.5 Update `recommendation_text` to include shift context when attribution is available
  - [ ] 2.6 Write pytest tests for: single-shift miss, systemic miss, no shift data available

- [ ] Task 3: Create ShiftTabs UI component (AC: #2)
  - [ ] 3.1 Create `apps/web/src/components/production/ShiftTabs.tsx` using Shadcn/UI `Tabs` component
  - [ ] 3.2 Tabs: "All" (default), "Morning", "Afternoon", "Night"
  - [ ] 3.3 Emit `onShiftChange(shift: string | null)` callback
  - [ ] 3.4 Style with Tailwind to match Industrial Clarity Design System
  - [ ] 3.5 Write Vitest test for tab rendering and callback behavior

- [ ] Task 4: Create WorkcenterScorecard component (AC: #1, #2)
  - [ ] 4.1 Create `apps/web/src/components/production/WorkcenterScorecard.tsx`
  - [ ] 4.2 Display workcenter rows with: name, actual output, target output, attainment %, OEE, downtime
  - [ ] 4.3 Accept `selectedShift` prop and filter displayed data accordingly
  - [ ] 4.4 When shift is selected, show that shift's metrics instead of the aggregate
  - [ ] 4.5 Include visual indicators (red/amber/green) for attainment thresholds
  - [ ] 4.6 Export from `apps/web/src/components/production/index.ts`

- [ ] Task 5: Add shift attribution display to InsightSection (AC: #3, #4)
  - [ ] 5.1 Update `InsightSection.tsx` to accept optional `shiftAttribution` prop
  - [ ] 5.2 When present, render shift badge below recommendation text (e.g. "Afternoon Shift" pill)
  - [ ] 5.3 When absent (systemic), render "All Shifts" or no shift badge
  - [ ] 5.4 Update `ActionItem` type in `types.ts` to include optional `shiftAttribution` field

- [ ] Task 6: Integrate shift filtering on Morning Report page (AC: #2)
  - [ ] 6.1 Add `useWorkcenterSummary(date, shift)` hook in `apps/web/src/hooks/useWorkcenterSummary.ts`
  - [ ] 6.2 Add ShiftTabs + WorkcenterScorecard to `apps/web/src/app/morning-report/page.tsx`
  - [ ] 6.3 Wire shift state: when shift changes, re-fetch workcenter summary and filter action items
  - [ ] 6.4 Ensure URL state: `?shift=afternoon` query param for shareability (NFR-I7)

- [ ] Task 7: End-to-end testing and backward compatibility (AC: #1-4, NFR-I6)
  - [ ] 7.1 Verify daily aggregate view still works when no shift data exists (backward compatibility)
  - [ ] 7.2 Verify "All" tab shows same data as current daily view
  - [ ] 7.3 Test with seed data: ensure shift values sum to daily totals
  - [ ] 7.4 Manual smoke test: shift tabs filter both scorecard and action items

## Dev Notes

### Architecture & Patterns

- **API Framework:** FastAPI 0.109+ with Pydantic v2 models. All endpoints require `get_current_user` dependency for JWT auth.
- **Frontend Framework:** Next.js 14 App Router with TypeScript 5.x. Client components use `'use client'` directive.
- **UI Components:** Shadcn/UI + Radix UI primitives + Tailwind CSS. Use existing `Tabs` component from Shadcn/UI for shift selector.
- **State Management:** URL search params (`useSearchParams`) for filter state. No Redux/Zustand -- use React hooks + URL state.
- **Data Fetching:** Frontend uses `fetch()` to `NEXT_PUBLIC_API_URL` endpoints. No SWR/React Query currently -- use simple `useEffect` + `useState` pattern matching existing hooks (see `useDailyActions.ts`, `useLivePulse.ts`).

### Database Context

- **Story 17.3 prerequisite:** This story depends on the `shift_summaries` table created in Story 17.3. The table schema is:
  - `id` (UUID PK), `asset_id` (UUID FK -> assets), `date` (DATE), `shift` (TEXT CHECK 'morning','afternoon','night'), `oee` (DECIMAL(5,2)), `availability` (DECIMAL(5,2)), `performance` (DECIMAL(5,2)), `quality` (DECIMAL(5,2)), `downtime_minutes` (INTEGER), `units_produced` (INTEGER), `created_at` (TIMESTAMPTZ)
  - Unique constraint on `(asset_id, date, shift)`
  - Indexes on `asset_id`, `date`
- **Existing tables used:** `daily_summaries`, `assets`, `shift_targets`, `cost_centers`, `safety_events`
- **Supabase client pattern:** Use `create_client(settings.supabase_url, settings.supabase_key)` -- see `production.py` line 103-114 for the established pattern.
- **RLS:** Follow existing patterns. The `shift_summaries` table will already have RLS from Story 17.3.

### API Endpoint Design

- **New endpoint:** `GET /api/production/workcenter-summary?date=YYYY-MM-DD&shift=morning|afternoon|night`
  - Add to existing `apps/api/app/api/production.py` router
  - Response model should include: `workcenters: List[WorkcenterSummary]` where each has `name`, `area`, `actual_output`, `target_output`, `attainment_pct`, `oee`, `downtime_minutes`, and optional `shift_breakdown: List[ShiftBreakdown]`
  - When `shift` query param is provided, return only that shift's data (not the aggregate)
  - When no `shift` param, return aggregate with `shift_breakdown` array populated
- **Router registration:** The production router is already registered at `/api/production` in `main.py`. New endpoints will be available under that prefix.

### Action Engine Integration

- **Existing architecture:** `ActionEngine` class in `action_engine.py` uses a singleton pattern (`get_action_engine()`). It queries `daily_summaries` for OEE and financial data, `safety_events` for safety data.
- **Add shift attribution:** Extend the `_get_oee_actions()` method (or add a post-processing step) to query `shift_summaries` for each flagged asset. Determine if one shift is predominantly responsible.
- **Attribution threshold:** If one shift contributes >60% of the total miss (downtime or output gap), attribute to that shift. Otherwise mark as systemic.
- **Schema extension:** Add optional `shift_attribution: Optional[str]` to `ActionItem` in `schemas/action.py`. Default to `None` for backward compatibility.
- **Backward compatibility (NFR-I6):** The `shift_attribution` field is optional/nullable. Existing consumers that don't use it will see no change.

### Frontend Component Design

- **ShiftTabs:** Simple Shadcn `Tabs` component. Values: `"all"`, `"morning"`, `"afternoon"`, `"night"`. Default to `"all"`.
- **WorkcenterScorecard:** New component in `components/production/`. Table layout showing workcenter rows. Use existing `cn()` utility from `@/lib/utils` for conditional styling.
- **InsightSection update:** The existing `InsightSection.tsx` accepts `priority`, `recommendation`, `asset`, `financialImpact`, `timestamp`. Add optional `shiftAttribution?: string` prop. When present, render a small badge/pill below the recommendation text.
- **Type updates:** Add `shiftAttribution?: string` to `ActionItem` interface in `components/action-engine/types.ts`.

### Existing Code Patterns to Follow

- **API endpoint pattern:** See `get_throughput_data()` in `production.py` -- uses `get_supabase_client()`, queries with `.select()`, `.eq()`, `.execute()`, returns Pydantic response model.
- **Action engine pattern:** See `_get_oee_actions()` in `action_engine.py` -- queries `daily_summaries`, builds `ActionItem` with `EvidenceRef`, sorts by financial impact.
- **Frontend component pattern:** See `InsightSection.tsx` -- uses `'use client'`, imports from `@/lib/utils`, uses Tailwind classes, follows accessible patterns with `aria-label`.
- **Hook pattern:** See `useDailyActions.ts` -- accepts date parameter, returns data/loading/error state.

### Files to Create

| File | Purpose |
|------|---------|
| `apps/web/src/components/production/ShiftTabs.tsx` | Shift selector component (Morning/Afternoon/Night/All) |
| `apps/web/src/components/production/WorkcenterScorecard.tsx` | Workcenter summary table with shift filtering |
| `apps/web/src/hooks/useWorkcenterSummary.ts` | Data hook for workcenter summary API |

### Files to Modify

| File | Change |
|------|--------|
| `apps/api/app/api/production.py` | Add `GET /api/production/workcenter-summary` endpoint with shift breakdown |
| `apps/api/app/services/action_engine.py` | Add `_get_shift_attribution()` method, update OEE actions with shift context |
| `apps/api/app/schemas/action.py` | Add `shift_attribution: Optional[str]` to `ActionItem`, add `ShiftBreakdown` and `WorkcenterSummary` models |
| `apps/web/src/components/action-engine/InsightSection.tsx` | Add optional `shiftAttribution` prop and badge display |
| `apps/web/src/components/action-engine/types.ts` | Add `shiftAttribution?: string` to `ActionItem` interface |
| `apps/web/src/components/production/index.ts` | Export new `ShiftTabs` and `WorkcenterScorecard` components |
| `apps/web/src/app/morning-report/page.tsx` | Integrate ShiftTabs, WorkcenterScorecard, wire shift state to action list |

### Project Structure Notes

- All new API models go in `apps/api/app/schemas/` -- do NOT create ad-hoc models in route files
- All new frontend components follow the `components/{domain}/` pattern -- ShiftTabs and WorkcenterScorecard go in `components/production/`
- Hooks go in `apps/web/src/hooks/` (top-level hooks, not `lib/hooks/` which is for utility hooks)
- Tests: API tests in `apps/api/tests/`, frontend tests co-located with components in `__tests__/` directories

### Testing Standards

- **API:** pytest with async support. Mock Supabase client for unit tests. Test happy path, empty state, and error handling.
- **Frontend:** Vitest + Testing Library. Test component rendering, prop behavior, user interactions. See existing pattern in `src/components/chat/__tests__/`.
- **No shift data fallback:** When `shift_summaries` table is empty for a date, the API must return daily aggregates only (no `shift_breakdown`), and the UI must hide shift tabs or disable them gracefully.

### References

- [Source: _bmad-output/planning-artifacts/epic-17.md#Story 17.4] - Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/epic-17.md#Story 17.3] - Shift summaries data model (prerequisite)
- [Source: docs/architecture-api.md#Directory Structure] - API project structure and patterns
- [Source: docs/architecture-web.md#Directory Structure] - Frontend project structure and patterns
- [Source: docs/architecture-web.md#Component Architecture] - Component organization by domain
- [Source: docs/data-models.md#daily_summaries] - Daily summaries table schema
- [Source: docs/data-models.md#shift_targets] - Shift targets table schema
- [Source: docs/integration-architecture.md#Web to API Integration] - REST integration pattern
- [Source: apps/api/app/api/production.py] - Existing production API endpoint patterns
- [Source: apps/api/app/services/action_engine.py] - Action engine class and prioritization logic
- [Source: apps/api/app/schemas/action.py] - ActionItem, EvidenceRef, ActionListResponse schemas
- [Source: apps/web/src/components/action-engine/InsightSection.tsx] - Existing insight card component
- [Source: apps/web/src/components/action-engine/types.ts] - Frontend ActionItem type definition
- [Source: apps/web/src/components/production/index.ts] - Production component barrel exports

## Dev Agent Record

### Agent Model Used

<!-- To be filled by dev agent -->

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List
