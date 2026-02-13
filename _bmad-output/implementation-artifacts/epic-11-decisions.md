# Epic 11 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 11
**Started:** 2026-02-11 08:36:23

---


## DESIGN: 11-1-workcenter-summary-api-endpoint
**Timestamp:** 2026-02-11 08:39:26

DESIGN START
story_id: 11-1-workcenter-summary-api-endpoint

files_to_modify:
  - path: apps/api/app/schemas/production.py
    action: create
    purpose: Define Pydantic response models (AssetDetail, WorkcenterEntry, WorkcenterSummaryResponse) for the workcenter summary endpoint
  - path: apps/api/app/api/production.py
    action: modify
    purpose: Add GET /workcenter-summary route handler with date query param, Supabase multi-query logic, Python-side aggregation by area
  - path: apps/api/app/main.py
    action: modify
    purpose: Add /api/v1/production versioned alias for production router (follows actions.router pattern on lines 63-65)
  - path: apps/api/tests/api/test_production_workcenter.py
    action: create
    purpose: Unit tests covering all 3 ACs — normal multi-workcenter response, empty data, date defaulting, edge cases, and auth

patterns_to_use:
  - Supabase multi-query + Python join: Follows get_throughput_data() pattern — 3 separate table queries (assets, daily_summaries, shift_targets) joined in Python by asset_id, then grouped by assets.area. Reuses existing get_supabase_client() helper.
  - JWT auth dependency: Uses existing `current_user: CurrentUser = Depends(get_current_user)` dependency already imported in production.py
  - Error handling try/except: Follows existing pattern — re-raise HTTPException, catch generic Exception with logger.error and 500 response
  - Schema in separate file: Follows action.py/summary.py pattern — Pydantic BaseModel classes with Field descriptions and json_schema_extra examples
  - Router versioned alias: Follows main.py lines 63-65 pattern — register production.router at both /api/production (existing) and /api/v1/production (new alias)
  - calculate_percentage reuse: Uses existing helper in production.py for attainment calculation, handles zero-target by returning 100.0
  - TestClient + mock pattern: Follows test_production_api.py — client fixture from conftest, mock_verify_jwt, mock_supabase_client patching get_supabase_client

dependencies:
  - fastapi: installed (already used in production.py)
  - pydantic: installed (already used in production.py)
  - supabase: installed (already used via get_supabase_client)
  - pytest: installed (already used in existing tests)

acceptance_criteria_mapping:
  - AC1 (workcenter-grouped response with aggregations): apps/api/app/api/production.py:get_workcenter_summary() — 3 Supabase queries (assets, daily_summaries filtered by date, shift_targets), Python join by asset_id, groupby area. Builds WorkcenterEntry per area with total_actual (sum units_produced), total_target (sum target_units across all shifts), attainment_pct (calculate_percentage), assets_hit/assets_missed counts, and assets[] array of AssetDetail. Response schema in apps/api/app/schemas/production.py (AssetDetail, WorkcenterEntry, WorkcenterSummaryResponse).
  - AC2 (empty data → 200 with message): apps/api/app/api/production.py:get_workcenter_summary() — after daily_summaries query returns empty data, return WorkcenterSummaryResponse(workcenters=[], report_date=date, message="No data available for {date}")
  - AC3 (date defaults to T-1): apps/api/app/api/production.py:get_workcenter_summary() — date parameter typed as Optional[date] with default None; when None, compute as date.today() - timedelta(days=1)

risks:
  - Supabase query chain mocking complexity: The 3 separate .table().select().eq().execute() calls need careful mock setup with side_effect ordering. Mitigation — follow the exact mock chaining pattern from test_production_api.py, use side_effect list for sequential table calls, and also test with .eq() chain for daily_summaries date filter.
  - shift_targets has multiple rows per asset (one per shift): Must sum all target_units per asset_id. Mitigation — build a dict[asset_id → total_target] by iterating all shift_target rows and accumulating.
  - Assets with NULL area: Could cause KeyError during groupby. Mitigation — skip assets with area=None/empty or group under "Unassigned" workcenter, per story dev notes.
  - Division by zero on attainment: When total_target=0 for a workcenter. Mitigation — reuse existing calculate_percentage() which returns 100.0 for zero target.
  - Supabase .eq() filter on date column: The daily_summaries date filter uses .eq("date", str(report_date)). Need to ensure date is passed as ISO string "YYYY-MM-DD". Mitigation — explicitly convert date to isoformat string.
  - Versioned alias registration may duplicate OpenAPI paths: Both /api/production/workcenter-summary and /api/v1/production/workcenter-summary will appear. This is acceptable and matches the actions pattern.

estimated_test_files:
  - apps/api/tests/api/test_production_workcenter.py: Tests for (1) normal response with 2+ workcenters and multiple assets per workcenter — validates grouping, totals, attainment, hit/miss counts, per-asset breakdown; (2) empty daily_summaries returns 200 with empty workcenters array and message; (3) no date param defaults to yesterday T-1; (4) explicit date param is respected in query; (5) zero target edge case — attainment=100.0; (6) 401 without auth token; (7) assets with NULL area excluded from response; (8) partial data — asset with summary but no target, or target but no summary

implementation_order:
  1. Create apps/api/app/schemas/production.py with AssetDetail, WorkcenterEntry, and WorkcenterSummaryResponse Pydantic models (with Field descriptions, ge=0 constraints, json_schema_extra examples)
  2. Modify apps/api/app/api/production.py — add imports (date, timedelta, Optional from typing, schema imports), add GET /workcenter-summary endpoint with: Optional[date] query param defaulting to T-1, 3 Supabase queries, Python join/groupby logic, empty-data handling, error handling
  3. Modify apps/api/app/main.py — add `app.include_router(production.router, prefix="/api/v1/production", tags=["Production V1"])` after line 68
  4. Create apps/api/tests/api/test_production_workcenter.py with all test cases (auth, normal, empty, date default, date param, zero target, null area, partial data)
  5. Run tests to verify all pass
DESIGN END

---

## DESIGN: 11-2-workcenter-scorecard-ui-component
**Timestamp:** 2026-02-11 09:08:32

DESIGN START
story_id: 11-2-workcenter-scorecard-ui-component

files_to_modify:
  - path: apps/web/src/hooks/useWorkcenterSummary.ts
    action: create
    purpose: Data fetching hook for GET /api/v1/production/workcenter-summary endpoint with Bearer token auth, loading/error/empty state management, date defaulting to T-1
  - path: apps/web/src/components/production/WorkcenterScorecard.tsx
    action: create
    purpose: Container component handling loading skeleton, error with retry, empty state, and rendering list of WorkcenterRow components with section header
  - path: apps/web/src/components/production/WorkcenterRow.tsx
    action: create
    purpose: Expandable row component displaying workcenter name, actual/target, attainment % with color coding, asset hit/miss count, and click-to-expand toggle for AssetDetailTable
  - path: apps/web/src/components/production/AssetDetailTable.tsx
    action: create
    purpose: Table component showing per-asset breakdown (name, actual/target, OEE %, downtime minutes) with green/red row color coding
  - path: apps/web/src/components/production/index.ts
    action: modify
    purpose: Add barrel exports for WorkcenterScorecard, WorkcenterRow, AssetDetailTable
  - path: apps/web/src/app/(main)/morning-report/page.tsx
    action: modify
    purpose: Import WorkcenterScorecard and render it between MorningSummarySection and the action items section

patterns_to_use:
  - Bearer token auth via Supabase session: Follow useDailyActions.ts exactly — createClient() -> getSession() -> Authorization Bearer header. Use mountedRef for cleanup, useCallback for fetch, autoFetch useEffect on mount.
  - Container loading/error/empty pattern: Follow ActionListContainer.tsx — early returns for isLoading (skeleton), error (AlertCircle + retry Button), empty state, then success rendering.
  - Card with mode="retrospective": Follow MorningSummarySection.tsx — use Card mode="retrospective" since this is historical (T-1) production data, not live data.
  - Color coding from ThroughputCard.tsx: Use text-success-green-dark dark:text-success-green for green, text-warning-amber-dark dark:text-warning-amber for yellow, text-safety-red for red. For asset row backgrounds use bg-success-green-light/20 and bg-safety-red-light/20.
  - Number formatting with toLocaleString(): Use num.toLocaleString() for comma-separated integers (4,200 / 5,000) and toFixed(1) for percentages (95.2%).
  - Simple React state toggle for expand/collapse: Option A from dev notes — useState boolean toggle, conditional render of AssetDetailTable, no new dependency needed.
  - Error messages at module level: Define ERROR_MESSAGES constant object matching useDailyActions pattern.
  - cn() utility for conditional classes: Import from @/lib/utils for merging Tailwind classes.

dependencies:
  - react: installed (useState, useEffect, useCallback, useRef)
  - @/lib/supabase/client: installed (createClient for auth)
  - @/components/ui/card: installed (Card, CardHeader, CardTitle, CardContent)
  - @/components/ui/button: installed (Button for retry)
  - @/components/ui/badge: installed (Badge for status indicators)
  - lucide-react: installed (RefreshCw, AlertCircle, ChevronDown/ChevronRight icons)
  - @/lib/utils: installed (cn utility)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (scorecard renders one row per workcenter with name, actual/target, attainment %, asset count): useWorkcenterSummary.ts fetches data from /api/v1/production/workcenter-summary?date={date}. WorkcenterScorecard.tsx renders Card container with "Production Scorecard" header. WorkcenterRow.tsx renders each workcenter with: workcenter name (bold), actual/target formatted as "4,200 / 5,000", attainment_pct with getAttainmentColor() returning green/yellow/red classes, and "{assets_hit} of {total_assets} assets on target" text. Positioned in morning-report/page.tsx between MorningSummarySection and action items section.
  - AC2 (click/expand shows per-asset breakdown): WorkcenterRow.tsx uses useState<boolean> for isExpanded toggle on click. When expanded, renders AssetDetailTable.tsx which maps over workcenter.assets array displaying: asset_name, actual_output/target_output formatted, oee with one decimal (or "N/A"), downtime_minutes (or "N/A"). Each row gets bg-success-green-light/20 if hit_target===true, bg-safety-red-light/20 if false.
  - AC3 (empty state when no data): useWorkcenterSummary.ts returns data with empty workcenters array (API returns message field). WorkcenterScorecard.tsx checks workcenters.length === 0 and renders empty state Card with message text from API response or default "No production data available for this date."
  - AC4 (tablet glanceability — readable from 3 feet): WorkcenterRow.tsx uses text-3xl font-bold tabular-nums for attainment percentage. Workcenter name uses text-lg font-semibold. Actual/target uses text-base tabular-nums. Card padding generous at p-4 md:p-6. Expand/collapse touch target minimum 44px via min-h-[44px] min-w-[44px]. AssetDetailTable uses text-base for readability.

risks:
  - API endpoint not yet deployed or returning unexpected shape: The hook must gracefully handle 404 (endpoint not found) by treating as empty state. Mitigation — check response.status === 404 and return empty workcenters array with appropriate message, matching the story dev notes requirement.
  - API response field names differ from story spec: The actual API schema (from Story 11.1 implementation) uses slightly different field names than the story spec (e.g., workcenter vs workcenter_name, attainment_pct vs attainment_percentage, assets_hit/assets_missed vs assets_on_target/assets_missed, actual_output/target_output vs actual/target). Mitigation — TypeScript interfaces in the hook MUST match the actual Pydantic schema: WorkcenterEntry has workcenter (not workcenter_name), attainment_pct, assets_hit, assets_missed, total_actual, total_target. AssetDetail has asset_name, actual_output, target_output, attainment_pct, oee (Optional), downtime_minutes (Optional), hit_target. WorkcenterSummaryResponse has workcenters[], report_date, message (Optional).
  - total_assets not in API response: The API schema WorkcenterEntry does not have a total_assets field. Mitigation — compute it as assets_hit + assets_missed in the component, or use the assets.length property.
  - oee and downtime_minutes may be null: The AssetDetail schema marks these as Optional. Mitigation — display "N/A" or "—" when null, never call toFixed() on null.
  - Color tokens must match existing Tailwind config: Mitigation — use exact tokens from tailwind.config.ts: success-green, success-green-light, success-green-dark, warning-amber, warning-amber-dark, safety-red, safety-red-light.
  - Server component importing client component: The morning-report page is a server component. Mitigation — WorkcenterScorecard.tsx has 'use client' directive at top, which is the standard Next.js App Router pattern for client components imported into server components.

estimated_test_files:
  - apps/web/src/components/production/__tests__/WorkcenterScorecard.test.tsx: Tests for (1) renders all workcenter rows from mock data with correct names and values; (2) correct color coding — green at 95%+, yellow at 85-94%, red at <85%; (3) clicking a row expands to show AssetDetailTable with per-asset data; (4) clicking again collapses the detail; (5) empty state when workcenters array is empty; (6) loading skeleton displayed when isLoading=true; (7) error state with retry button displayed on error; (8) retry button calls refetch; (9) number formatting — commas in integers, one decimal in percentages; (10) asset rows colored green when hit_target=true, red when false; (11) handles null oee and downtime_minutes gracefully

implementation_order:
  1. Create apps/web/src/hooks/useWorkcenterSummary.ts — Define TypeScript interfaces matching actual API schema (WorkcenterSummaryResponse, WorkcenterEntry, AssetDetail with exact field names from apps/api/app/schemas/production.py). Implement hook following useDailyActions.ts pattern: createClient(), getSession(), Bearer auth, fetch to /api/v1/production/workcenter-summary?date={date}, error handling for 401/404/500, mountedRef cleanup, useCallback, autoFetch useEffect. State: data (WorkcenterSummaryResponse | null), isLoading, error, lastUpdated. Return refetch function and hasData computed boolean.
  2. Create apps/web/src/components/production/AssetDetailTable.tsx — Presentational component receiving assets: AssetDetail[] prop. Renders HTML table with columns: Asset, Actual / Target, OEE %, Downtime. Each row color-coded with bg-success-green-light/20 or bg-safety-red-light/20 based on hit_target. Format numbers with toLocaleString(), oee with toFixed(1)+'%' or '—', downtime as '{n} min' or '—'. Use text-base for glanceability, tabular-nums for alignment.
  3. Create apps/web/src/components/production/WorkcenterRow.tsx — Receives workcenter: WorkcenterEntry prop. Displays: workcenter name (text-lg font-semibold), actual/target as "N,NNN / N,NNN", attainment_pct (text-3xl font-bold tabular-nums) with color from getAttainmentColor() helper, and "{assets_hit} of {assets_hit + assets_missed} assets on target". useState for isExpanded, onClick toggles it. ChevronDown/ChevronRight icon for expand indicator. When expanded, renders AssetDetailTable with workcenter.assets. Uses Card component for structure. Min touch target 44px on expand button.
  4. Create apps/web/src/components/production/WorkcenterScorecard.tsx — 'use client' container component. Uses useWorkcenterSummary() hook. Handles 4 states: (1) loading — render skeleton placeholder cards; (2) error — AlertCircle icon + error message + retry Button; (3) empty (data.workcenters.length === 0) — message from API or default empty text; (4) success — section header "Production Scorecard" (section-header class) + map workcenters to WorkcenterRow components. Takes optional className prop.
  5. Modify apps/web/src/components/production/index.ts — Add three export lines: export WorkcenterScorecard, WorkcenterRow, AssetDetailTable from their respective files.
  6. Modify apps/web/src/app/(main)/morning-report/page.tsx — Import WorkcenterScorecard from @/components/production. Add <WorkcenterScorecard /> between <MorningSummarySection /> and the action items <section>. No other changes needed since WorkcenterScorecard is a 'use client' component that self-manages its data fetching.
  7. Create apps/web/src/components/production/__tests__/WorkcenterScorecard.test.tsx — Vitest + Testing Library tests. Mock useWorkcenterSummary hook. Test all states (loading, error, empty, success), color coding thresholds, expand/collapse interaction, number formatting, asset row coloring, null field handling.
DESIGN END

---

## TEST_SPEC: 11-2-workcenter-scorecard-ui-component
**Timestamp:** 2026-02-11 09:12:08

TEST SPEC START
story_id: 11-2-workcenter-scorecard-ui-component
generated: 2026-02-11

test_specifications:

## AC1: Given the morning report page loads with workcenter summary data, When the scorecard section renders, Then it displays one row per workcenter showing: workcenter name, actual output vs. target output (e.g., "4,200 / 5,000"), attainment percentage with color coding (green >= 95%, yellow 85-94%, red < 85%), and count of assets hit vs. missed (e.g., "3 of 4 assets on target"). The scorecard appears above the action items section.

### 11-2-workcenter-scorecard-ui-component-UNIT-001: Renders one WorkcenterRow per workcenter entry
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns data with 3 workcenter entries (Grinding, Assembly, Packaging)
- When: WorkcenterScorecard renders
- Then: exactly 3 workcenter rows are displayed, each containing the corresponding workcenter name
- Data: Mock WorkcenterSummaryResponse with 3 WorkcenterEntry items: { workcenter: "Grinding", total_actual: 4200, total_target: 5000, attainment_pct: 84.0, assets_hit: 2, assets_missed: 2, assets: [...] }, { workcenter: "Assembly", total_actual: 9500, total_target: 10000, attainment_pct: 95.0, assets_hit: 3, assets_missed: 1, assets: [...] }, { workcenter: "Packaging", total_actual: 7800, total_target: 8500, attainment_pct: 91.8, assets_hit: 2, assets_missed: 1, assets: [...] }

### 11-2-workcenter-scorecard-ui-component-UNIT-002: Displays workcenter name in each row
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns data with workcenter entry { workcenter: "Grinding" }
- When: WorkcenterRow renders
- Then: the text "Grinding" is visible and rendered with font-semibold class
- Data: Single WorkcenterEntry with workcenter: "Grinding"

### 11-2-workcenter-scorecard-ui-component-UNIT-003: Displays actual vs target with comma formatting
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with total_actual: 4200 and total_target: 5000
- When: WorkcenterRow renders
- Then: the output displays "4,200 / 5,000" (comma-separated integers)
- Data: WorkcenterEntry with total_actual: 4200, total_target: 5000

### 11-2-workcenter-scorecard-ui-component-UNIT-004: Displays attainment percentage with one decimal
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 95.2
- When: WorkcenterRow renders
- Then: the text "95.2%" is visible in the row
- Data: WorkcenterEntry with attainment_pct: 95.2

### 11-2-workcenter-scorecard-ui-component-UNIT-005: Green color coding for attainment >= 95%
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 95.0
- When: WorkcenterRow renders the attainment percentage
- Then: the percentage element has CSS class text-success-green-dark (light mode) / dark:text-success-green (dark mode)
- Data: WorkcenterEntry with attainment_pct: 95.0

### 11-2-workcenter-scorecard-ui-component-UNIT-006: Green color coding for attainment at exactly 95%
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 95.0 (boundary value)
- When: WorkcenterRow renders the attainment percentage
- Then: the percentage element has green color classes (>= 95% threshold is inclusive)
- Data: WorkcenterEntry with attainment_pct: 95.0

### 11-2-workcenter-scorecard-ui-component-UNIT-007: Yellow color coding for attainment 85-94%
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 91.8
- When: WorkcenterRow renders the attainment percentage
- Then: the percentage element has CSS class text-warning-amber-dark (light mode) / dark:text-warning-amber (dark mode)
- Data: WorkcenterEntry with attainment_pct: 91.8

### 11-2-workcenter-scorecard-ui-component-UNIT-008: Yellow color coding at exactly 85% boundary
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 85.0
- When: WorkcenterRow renders the attainment percentage
- Then: the percentage element has yellow/amber color classes (85% is the lower boundary of yellow range)
- Data: WorkcenterEntry with attainment_pct: 85.0

### 11-2-workcenter-scorecard-ui-component-UNIT-009: Red color coding for attainment < 85%
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 72.5
- When: WorkcenterRow renders the attainment percentage
- Then: the percentage element has CSS class text-safety-red
- Data: WorkcenterEntry with attainment_pct: 72.5

### 11-2-workcenter-scorecard-ui-component-UNIT-010: Red color coding at 84.9% (just below yellow boundary)
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 84.9
- When: WorkcenterRow renders the attainment percentage
- Then: the percentage element has red color class text-safety-red (84.9 < 85 threshold)
- Data: WorkcenterEntry with attainment_pct: 84.9

### 11-2-workcenter-scorecard-ui-component-UNIT-011: Displays asset hit/miss count in readable format
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with assets_hit: 3, assets_missed: 1
- When: WorkcenterRow renders
- Then: the text "3 of 4 assets on target" is visible (total computed as assets_hit + assets_missed)
- Data: WorkcenterEntry with assets_hit: 3, assets_missed: 1

### 11-2-workcenter-scorecard-ui-component-UNIT-012: Section header displays "Production Scorecard"
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns valid data
- When: WorkcenterScorecard renders
- Then: a heading or section title with text "Production Scorecard" is visible
- Data: Any valid WorkcenterSummaryResponse

### 11-2-workcenter-scorecard-ui-component-INT-001: Scorecard positioned between MorningSummarySection and action items
- Priority: P0
- Type: integration
- Given: the morning report page renders with all sections
- When: the DOM is inspected for section ordering
- Then: WorkcenterScorecard appears after MorningSummarySection and before the action items section in the DOM hierarchy
- Data: Mock all data hooks (useDailyActions, useWorkcenterSummary, etc.)

### 11-2-workcenter-scorecard-ui-component-UNIT-013: Loading skeleton displayed while fetching data
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns isLoading: true, data: null
- When: WorkcenterScorecard renders
- Then: skeleton placeholder elements are visible (not workcenter rows, not error, not empty state)
- Data: Hook mocked to return { isLoading: true, data: null, error: null }

### 11-2-workcenter-scorecard-ui-component-UNIT-014: Error state with retry button on fetch failure
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns error: "Failed to load workcenter data"
- When: WorkcenterScorecard renders
- Then: an error message is visible, an AlertCircle icon is present, and a retry/try-again button is available
- Data: Hook mocked to return { isLoading: false, data: null, error: "Failed to load workcenter data" }

### 11-2-workcenter-scorecard-ui-component-UNIT-015: Retry button calls refetch
- Priority: P1
- Type: unit
- Given: WorkcenterScorecard is in error state with a retry button
- When: the user clicks the retry button
- Then: the refetch function from useWorkcenterSummary is called exactly once
- Data: Hook mocked with error state; refetch as vi.fn()

### 11-2-workcenter-scorecard-ui-component-UNIT-016: Large numbers formatted with commas
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with total_actual: 12500 and total_target: 15000
- When: WorkcenterRow renders
- Then: the output displays "12,500 / 15,000" (not "12500 / 15000")
- Data: WorkcenterEntry with total_actual: 12500, total_target: 15000

### 11-2-workcenter-scorecard-ui-component-UNIT-017: Zero values displayed correctly
- Priority: P2
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with total_actual: 0 and total_target: 5000, attainment_pct: 0.0
- When: WorkcenterRow renders
- Then: the output displays "0 / 5,000" and "0.0%" with red color coding
- Data: WorkcenterEntry with total_actual: 0, total_target: 5000, attainment_pct: 0.0

### 11-2-workcenter-scorecard-ui-component-UNIT-018: 100% attainment renders with green color
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 100.0
- When: WorkcenterRow renders
- Then: "100.0%" is visible with green color coding classes
- Data: WorkcenterEntry with attainment_pct: 100.0, total_actual: 5000, total_target: 5000

### 11-2-workcenter-scorecard-ui-component-UNIT-019: Attainment above 100% renders with green color
- Priority: P2
- Type: unit
- Given: useWorkcenterSummary returns a workcenter with attainment_pct: 112.5
- When: WorkcenterRow renders
- Then: "112.5%" is visible with green color coding classes (above 95% threshold)
- Data: WorkcenterEntry with attainment_pct: 112.5, total_actual: 5625, total_target: 5000


## AC2: Given a workcenter row is clicked or expanded, When the detail view opens, Then it shows per-asset breakdown: asset name, actual vs. target, OEE %, downtime minutes. Each asset row is color-coded green (hit target) or red (missed).

### 11-2-workcenter-scorecard-ui-component-UNIT-020: Clicking a workcenter row expands the asset detail table
- Priority: P0
- Type: unit
- Given: WorkcenterRow renders in collapsed state with 3 assets
- When: the user clicks on the workcenter row (expand toggle)
- Then: the AssetDetailTable becomes visible showing all 3 asset rows
- Data: WorkcenterEntry with assets: [{ asset_name: "Grinder 1", actual_output: 1200, target_output: 1300, attainment_pct: 92.3, oee: 85.2, downtime_minutes: 45, hit_target: false }, { asset_name: "Grinder 2", actual_output: 1500, target_output: 1400, attainment_pct: 107.1, oee: 92.0, downtime_minutes: 10, hit_target: true }, { asset_name: "Grinder 3", actual_output: 1500, target_output: 1300, attainment_pct: 115.4, oee: 88.5, downtime_minutes: 20, hit_target: true }]

### 11-2-workcenter-scorecard-ui-component-UNIT-021: Clicking an expanded row collapses the detail view
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded showing AssetDetailTable
- When: the user clicks on the workcenter row (collapse toggle) again
- Then: the AssetDetailTable is no longer visible
- Data: Same WorkcenterEntry as UNIT-020

### 11-2-workcenter-scorecard-ui-component-UNIT-022: Asset detail table shows asset name column
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with assets
- When: AssetDetailTable renders
- Then: each asset name is displayed (e.g., "Grinder 1", "Grinder 2", "Grinder 3")
- Data: Assets array with 3 named assets

### 11-2-workcenter-scorecard-ui-component-UNIT-023: Asset detail table shows actual vs target per asset
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with an asset having actual_output: 1200, target_output: 1300
- When: AssetDetailTable renders
- Then: the actual vs target is displayed as "1,200 / 1,300" (comma-formatted)
- Data: AssetDetail with actual_output: 1200, target_output: 1300

### 11-2-workcenter-scorecard-ui-component-UNIT-024: Asset detail table shows OEE percentage
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with an asset having oee: 85.2
- When: AssetDetailTable renders
- Then: the OEE is displayed as "85.2%" (one decimal place)
- Data: AssetDetail with oee: 85.2

### 11-2-workcenter-scorecard-ui-component-UNIT-025: Asset detail table shows downtime minutes
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with an asset having downtime_minutes: 45
- When: AssetDetailTable renders
- Then: the downtime is displayed (e.g., "45 min" or "45")
- Data: AssetDetail with downtime_minutes: 45

### 11-2-workcenter-scorecard-ui-component-UNIT-026: Asset row green background when hit_target is true
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with an asset where hit_target: true
- When: AssetDetailTable renders that asset row
- Then: the row has a green background tint class (e.g., bg-success-green-light/20 or similar success-green token)
- Data: AssetDetail with hit_target: true, actual_output: 1500, target_output: 1400

### 11-2-workcenter-scorecard-ui-component-UNIT-027: Asset row red background when hit_target is false
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with an asset where hit_target: false
- When: AssetDetailTable renders that asset row
- Then: the row has a red background tint class (e.g., bg-safety-red-light/20 or similar safety-red token)
- Data: AssetDetail with hit_target: false, actual_output: 1200, target_output: 1300

### 11-2-workcenter-scorecard-ui-component-UNIT-028: Handles null OEE gracefully
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with an asset where oee: null
- When: AssetDetailTable renders
- Then: the OEE column displays a fallback value ("—" or "N/A"), not a crash or "null%"
- Data: AssetDetail with oee: null

### 11-2-workcenter-scorecard-ui-component-UNIT-029: Handles null downtime_minutes gracefully
- Priority: P0
- Type: unit
- Given: WorkcenterRow is expanded with an asset where downtime_minutes: null
- When: AssetDetailTable renders
- Then: the downtime column displays a fallback value ("—" or "N/A"), not a crash or "null"
- Data: AssetDetail with downtime_minutes: null

### 11-2-workcenter-scorecard-ui-component-UNIT-030: Expand/collapse icon changes state
- Priority: P1
- Type: unit
- Given: WorkcenterRow renders in collapsed state
- When: the user clicks to expand
- Then: the expand icon changes from ChevronRight to ChevronDown (or equivalent visual indicator of expanded state)
- Data: Any valid WorkcenterEntry

### 11-2-workcenter-scorecard-ui-component-UNIT-031: Multiple workcenters can be expanded independently
- Priority: P1
- Type: unit
- Given: WorkcenterScorecard renders with 2 workcenter rows, both collapsed
- When: the user clicks the first workcenter row to expand it
- Then: only the first workcenter's AssetDetailTable is visible; the second remains collapsed
- Data: Mock data with 2 WorkcenterEntry items each having assets

### 11-2-workcenter-scorecard-ui-component-UNIT-032: Asset detail table with both null OEE and downtime
- Priority: P1
- Type: unit
- Given: WorkcenterRow is expanded with an asset having oee: null AND downtime_minutes: null
- When: AssetDetailTable renders
- Then: both columns show fallback values without errors
- Data: AssetDetail with oee: null, downtime_minutes: null, hit_target: true


## AC3: Given no workcenter data is available for the date, When the scorecard section renders, Then it shows an appropriate empty state message.

### 11-2-workcenter-scorecard-ui-component-UNIT-033: Empty state when workcenters array is empty
- Priority: P0
- Type: unit
- Given: useWorkcenterSummary returns data with workcenters: [] and message: "No production data available for this date."
- When: WorkcenterScorecard renders
- Then: the empty state message "No production data available for this date." is displayed instead of workcenter rows
- Data: WorkcenterSummaryResponse with workcenters: [], message: "No production data available for this date."

### 11-2-workcenter-scorecard-ui-component-UNIT-034: Empty state uses API message when provided
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns data with workcenters: [] and message: "No data found for 2026-02-09"
- When: WorkcenterScorecard renders
- Then: the displayed message matches the API-provided message text "No data found for 2026-02-09"
- Data: WorkcenterSummaryResponse with workcenters: [], message: "No data found for 2026-02-09"

### 11-2-workcenter-scorecard-ui-component-UNIT-035: Empty state fallback message when API message is null
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns data with workcenters: [] and message: null
- When: WorkcenterScorecard renders
- Then: a default empty state message is displayed (e.g., "No production data available for this date.")
- Data: WorkcenterSummaryResponse with workcenters: [], message: null

### 11-2-workcenter-scorecard-ui-component-UNIT-036: No workcenter rows rendered in empty state
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary returns data with workcenters: []
- When: WorkcenterScorecard renders in empty state
- Then: no WorkcenterRow components are present in the DOM
- Data: WorkcenterSummaryResponse with workcenters: []


## AC4: Given the page is viewed on a tablet, When the scorecard renders, Then text and numbers are readable from 3 feet away (NFR-I1 glanceability requirement).

### 11-2-workcenter-scorecard-ui-component-UNIT-037: Attainment percentage uses large font size
- Priority: P0
- Type: unit
- Given: WorkcenterRow renders with attainment data
- When: the attainment percentage element is inspected
- Then: it has a font size class of at least text-2xl (preferably text-3xl) and font-bold
- Data: WorkcenterEntry with attainment_pct: 95.0

### 11-2-workcenter-scorecard-ui-component-UNIT-038: Attainment uses tabular-nums for alignment
- Priority: P1
- Type: unit
- Given: WorkcenterRow renders with attainment data
- When: the attainment percentage element is inspected
- Then: it has the tabular-nums CSS class for uniform number width
- Data: WorkcenterEntry with attainment_pct: 95.0

### 11-2-workcenter-scorecard-ui-component-UNIT-039: Workcenter name uses bold readable font
- Priority: P1
- Type: unit
- Given: WorkcenterRow renders with workcenter: "Grinding"
- When: the workcenter name element is inspected
- Then: it has font-semibold class and at least text-lg size class
- Data: WorkcenterEntry with workcenter: "Grinding"

### 11-2-workcenter-scorecard-ui-component-UNIT-040: Expand/collapse touch target meets minimum 44px
- Priority: P1
- Type: unit
- Given: WorkcenterRow renders with an expand/collapse button
- When: the clickable area element is inspected
- Then: it has a minimum height/width of 44px (via min-h-[44px] min-w-[44px] or equivalent sizing)
- Data: Any valid WorkcenterEntry

### 11-2-workcenter-scorecard-ui-component-UNIT-041: Actual/target output uses tabular-nums
- Priority: P2
- Type: unit
- Given: WorkcenterRow renders with actual and target output numbers
- When: the output text element is inspected
- Then: it uses the tabular-nums class for aligned number columns
- Data: WorkcenterEntry with total_actual: 4200, total_target: 5000


## Hook Tests (useWorkcenterSummary)

### 11-2-workcenter-scorecard-ui-component-UNIT-042: Hook fetches with Bearer token auth
- Priority: P0
- Type: unit
- Given: Supabase session exists with access_token "mock-token-123"
- When: useWorkcenterSummary hook mounts and autoFetches
- Then: fetch is called with Authorization header "Bearer mock-token-123"
- Data: Mock createClient to return session with access_token: "mock-token-123"

### 11-2-workcenter-scorecard-ui-component-UNIT-043: Hook defaults date to T-1 (yesterday)
- Priority: P0
- Type: unit
- Given: no date parameter is provided to useWorkcenterSummary
- When: the hook makes the API call
- Then: the URL includes date parameter set to yesterday's date (T-1) in YYYY-MM-DD format
- Data: Mock today's date; verify fetch URL contains correct yesterday date

### 11-2-workcenter-scorecard-ui-component-UNIT-044: Hook returns data on successful fetch
- Priority: P0
- Type: unit
- Given: API returns 200 with valid WorkcenterSummaryResponse
- When: useWorkcenterSummary hook completes fetching
- Then: hook returns data with workcenters array, isLoading: false, error: null
- Data: Mock fetch to resolve with valid JSON response

### 11-2-workcenter-scorecard-ui-component-UNIT-045: Hook handles null session (no auth)
- Priority: P0
- Type: unit
- Given: Supabase getSession returns null session
- When: useWorkcenterSummary hook attempts to fetch
- Then: hook returns error "Authentication required" and does NOT call fetch
- Data: Mock getSession to return { data: { session: null } }

### 11-2-workcenter-scorecard-ui-component-UNIT-046: Hook handles 404 response as empty state
- Priority: P0
- Type: unit
- Given: API returns 404 (endpoint not found or no data)
- When: useWorkcenterSummary hook processes the response
- Then: hook returns data with empty workcenters array (treats 404 as empty, not error)
- Data: Mock fetch to resolve with status 404

### 11-2-workcenter-scorecard-ui-component-UNIT-047: Hook handles 401 unauthorized response
- Priority: P1
- Type: unit
- Given: API returns 401 Unauthorized
- When: useWorkcenterSummary hook processes the response
- Then: hook returns appropriate authentication error message
- Data: Mock fetch to resolve with status 401

### 11-2-workcenter-scorecard-ui-component-UNIT-048: Hook handles 500 server error response
- Priority: P1
- Type: unit
- Given: API returns 500 Internal Server Error
- When: useWorkcenterSummary hook processes the response
- Then: hook returns error state with server error message
- Data: Mock fetch to resolve with status 500

### 11-2-workcenter-scorecard-ui-component-UNIT-049: Hook handles network failure
- Priority: P1
- Type: unit
- Given: fetch throws a network error (e.g., ERR_NETWORK)
- When: useWorkcenterSummary hook processes the error
- Then: hook returns error state with appropriate network error message
- Data: Mock fetch to reject with TypeError("Failed to fetch")

### 11-2-workcenter-scorecard-ui-component-UNIT-050: Hook refetch function triggers new fetch
- Priority: P1
- Type: unit
- Given: useWorkcenterSummary has completed initial fetch
- When: refetch function is called
- Then: a new fetch call is made to the API endpoint
- Data: Track fetch call count before and after refetch()

### 11-2-workcenter-scorecard-ui-component-UNIT-051: Hook does not update state after unmount
- Priority: P2
- Type: unit
- Given: useWorkcenterSummary hook is mounted and fetch is in-flight
- When: the component unmounts before fetch completes
- Then: no state updates occur (mountedRef pattern prevents memory leak warning)
- Data: Mock fetch with delayed resolution; unmount hook before resolution


edge_cases:
  - Workcenter with all assets hitting target (assets_missed: 0) — should display "4 of 4 assets on target" and green attainment
  - Workcenter with no assets hitting target (assets_hit: 0) — should display "0 of 3 assets on target" and red attainment
  - Workcenter with very large numbers (total_actual: 1500000, total_target: 2000000) — comma formatting for millions
  - Workcenter with attainment_pct exactly at boundary values (0.0, 85.0, 94.9, 95.0, 100.0, >100)
  - Single workcenter in list (only one row rendered)
  - Workcenter with empty assets array (expand shows no detail rows)
  - AssetDetail with oee: 0.0 (should render "0.0%" not fallback)
  - AssetDetail with downtime_minutes: 0 (should render "0" not fallback)
  - API response with report_date different from requested date
  - Hook called with explicit date parameter overriding T-1 default
  - Very long workcenter name (text truncation or wrapping behavior)

error_scenarios:
  - API returns 404 (endpoint not deployed yet from Story 11.1) — treated as empty state, not error
  - API returns 401 Unauthorized (expired or invalid token) — error state with auth message
  - API returns 500 Internal Server Error — error state with retry button
  - Network failure (offline, DNS failure) — error state with retry button
  - Supabase session is null (user not logged in) — error with "Authentication required"
  - API returns malformed JSON — error state with parse error message
  - API returns unexpected schema (missing fields) — graceful degradation or error
  - Fetch timeout (very slow API response) — loading state persists, eventual error or timeout handling

test_file_mapping:
  - 11-2-workcenter-scorecard-ui-component-UNIT-001 to UNIT-041: apps/web/src/components/production/__tests__/WorkcenterScorecard.test.tsx
  - 11-2-workcenter-scorecard-ui-component-UNIT-042 to UNIT-051: apps/web/src/hooks/__tests__/useWorkcenterSummary.test.ts
  - 11-2-workcenter-scorecard-ui-component-INT-001: apps/web/src/components/production/__tests__/WorkcenterScorecard.test.tsx

TEST SPEC END

---

## DESIGN: 11-3-workcenter-seed-data
**Timestamp:** 2026-02-11 09:43:30

DESIGN START
story_id: 11-3-workcenter-seed-data

files_to_modify:
  - path: _bmad/scripts/seed-data.mjs
    action: modify
    purpose: Add missing daily_summaries for 6 assets (Roaster 3, Grinder 4, Filler Line B T-3 to T-7, Filler Line C, Packaging Line 2 T-3 to T-7, Packaging Line 3), add shift_targets upsert block for all 14 assets, fix target_output alignment in daily_summaries for Roaster 1 and Roaster 2 existing entries
  - path: supabase/migrations/0021_seed_data.sql
    action: modify
    purpose: Add missing daily_summaries rows for same 6 assets, fix shift_targets mismatches (Roaster 1/2/3, Grinder 3/4, Filler B/C, Packaging 2/3 all need afternoon shifts added or adjusted), fix Roaster 2 missing daily_summaries for T-4 through T-7, align target_output values between daily_summaries and shift_target sums

patterns_to_use:
  - daysAgo(N) date generation: All new daily_summaries in .mjs use existing daysAgo() helper for relative date offsets (T-1 through T-7)
  - upsert with onConflict: New daily_summaries use existing .upsert(data, { onConflict: 'asset_id,report_date' }) pattern for idempotency
  - shift_targets insert with delete-first: Since shift_targets has NO unique constraint, the .mjs script should delete existing shift_targets before re-inserting to prevent duplicates on repeated runs (matching the cleanup pattern used for live_snapshots and safety_events at line 42-43)
  - ON CONFLICT DO NOTHING in SQL: SQL migration shift_targets continue using existing ON CONFLICT DO NOTHING pattern; daily_summaries use ON CONFLICT (asset_id, report_date) DO NOTHING
  - Consistent asset ID UUIDs: Reuse exact UUID strings from existing assets array (a0000001-0000-0000-0000-000000000001 through ...0014)
  - Performance variation by story guidelines: Roasting ~88%, Grinding ~83%, Filling ~80%, Packaging ~88% workcenter attainment, with per-asset variation (at least 1 hit + 1 miss per workcenter)

dependencies:
  - @supabase/supabase-js: installed (already used in seed-data.mjs)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (all 4 workcenters have data for T-1): _bmad/scripts/seed-data.mjs daily_summaries — ensure Roaster 3, Grinder 4, Filler Line C, and Packaging Line 3 each have a T-1 (daysAgo(1)) daily_summary row. supabase/migrations/0021_seed_data.sql — same rows added with CURRENT_DATE - 1. After running, SELECT a.area, COUNT(DISTINCT ds.asset_id) FROM daily_summaries ds JOIN assets a ON a.id = ds.asset_id WHERE ds.report_date = CURRENT_DATE - 1 GROUP BY a.area should return 4 rows: Roasting(3), Grinding(5), Filling(3), Packaging(3).
  - AC2 (2-4 assets per workcenter with varied performance): In both seed files, daily_summaries for T-1 include: Roasting — Roaster 1 (87.5% OEE, misses target), Roaster 2 (96.1%, hits), Roaster 3 (new, ~89%, hits target); Grinding — Grinder 1 (91.2%, hits), Grinder 2 (95.8%, hits), Grinder 3 (84.2%, misses), Grinder 4 (new, ~88%, misses), Grinder 5 (82.5%, misses); Filling — Filler A (72.5%, misses), Filler B (89.2%, hits), Filler C (new, ~91%, hits); Packaging — Pack 1 (89.5%, hits), Pack 2 (88.9%, hits), Pack 3 (new, ~85%, misses).
  - AC3 (attainment ~70-100% range across workcenters): Performance targets per the story guidelines — Roasting: target ~88% (2 of 3 hit → actual sum ~399 vs target ~429), Grinding: target ~83% (2 of 5 hit, Grinder 5 and 3 drag down), Filling: target ~80% (Filler A drags, B and C solid), Packaging: target ~88% (2 of 3 hit, Pack 3 slightly misses).
  - AC4 (all 14 assets assigned to correct workcenter): Already correct in both files — Roasting: 3 (IDs ...0001/0002/0003), Grinding: 5 (IDs ...0004/0005/0006/0007/0014), Filling: 3 (IDs ...0008/0009/0010), Packaging: 3 (IDs ...0011/0012/0013). No changes needed for asset area assignments.
  - AC5 (every asset has at least one shift_target): _bmad/scripts/seed-data.mjs — add new shift_targets upsert block (currently absent) covering all 14 assets with correct per-shift values. supabase/migrations/0021_seed_data.sql — fix incomplete shift_targets: add missing afternoon shifts for Grinder 3, Grinder 4, Filler B, Filler C, Packaging 2, Packaging 3; fix Roaster 1/2/3 targets to sum correctly to daily target of 143.
  - AC6 (daily_summaries.target_output aligns with sum of shift_targets): Fix the Roaster mismatch: Roaster 1 shift_targets currently sum to 133 (48+45+40) but daily_summaries.target_output = 143. Resolution: adjust Roaster 1 shift_targets to morning=50, afternoon=48, night=45 (sum=143). Roaster 2 currently sums to 93 (48+45) — add night shift of 50 (sum=143). Roaster 3 currently sums to 84 (42+42) — change to morning=50, afternoon=48, night=45 (sum=143). Fix Grinder 3: only has morning=900 — add afternoon=1050 (sum=1950). Fix Grinder 4: only has morning=850 — add afternoon=1100 (sum=1950). New daily_summaries.target_output for Grinder 4 = 1950. Fix Filler B: only has morning=2400 — add afternoon=2200 (sum=4600). New daily_summaries.target_output for Filler B = 4600. Fix Filler C: only has morning=2000 — add afternoon=2000 (sum=4000). New daily_summaries.target_output for Filler C = 4000. Fix Packaging 2: only has morning=3200 — add afternoon=3000 (sum=6200). Fix Packaging 3: only has morning=2800 — add afternoon=2800 (sum=5600). New daily_summaries.target_output for Packaging 3 = 5600.

risks:
  - API column name mismatch with actual schema: The Story 11.1 API endpoint at production.py:398 queries daily_summaries with column names `units_produced`, `oee`, and `date` — but the actual schema defines columns `actual_output`, `oee_percentage`, and `report_date`. Similarly, shift_targets.target_units is queried but the column is `target_output`. This means the API endpoint will return empty data even with correct seed data. **Mitigation**: This is a pre-existing bug from Story 11.1 implementation, NOT a seed data issue. Document it and ensure seed data uses the correct schema column names. The API fix is out of scope for this story but should be flagged.
  - shift_targets has NO unique constraint: Re-running seed-data.mjs will insert duplicate rows. **Mitigation**: In .mjs, add a delete-then-insert pattern for shift_targets (delete all rows for known asset IDs first, then insert). In SQL, the ON CONFLICT DO NOTHING is already used but with no conflict target — this only works because the PK (id) is auto-generated, so it will always insert new rows. Accept this for SQL migrations since they run only on db reset. For the .mjs script, explicit cleanup is essential.
  - Roaster daily_summaries.target_output = 143 doesn't have an obvious shift split: The story notes say roaster shifts produce ~40-50 batches per 8-hour shift. With target=143 across 3 shifts, we get roughly 50+48+45=143. This is reasonable. For 2-shift roasters (if any), 143 won't split evenly — but all roasters should use 3 shifts to match the existing Roaster 1 pattern.
  - Filler Line C and Packaging Line 3 target_output values are new: Filler C daily target=4000 (vs Filler A/B at 4600) and Packaging 3 daily target=5600 (vs Pack 1 at 6200) reflect slightly lower-capacity lines. This creates natural variation. Ensure these smaller targets still produce realistic attainment percentages per the story guidelines.
  - Both seed mechanisms must stay in sync: Any data added to seed-data.mjs must also be added to 0021_seed_data.sql. **Mitigation**: Modify both files in the same implementation step, using a checklist cross-reference.
  - Existing Roaster 2 SQL data only has 3 days (T-1 to T-3): The .mjs has 7 days for Roaster 2 but the SQL only has T-1, T-2, T-3. Need to add T-4 through T-7 in SQL to match .mjs.
  - Existing Grinder 1 SQL data only has 5 days (T-1 to T-5): The .mjs has 7 days for Grinder 1 but the SQL only has T-1 through T-5. Need to add T-6 and T-7 in SQL to match .mjs.
  - Existing Grinder 2 SQL only has 3 days (T-1 to T-3): Need to add T-4 through T-7 in SQL.
  - Existing Filler A SQL only has 4 days (T-1 to T-4): Need to add T-5 through T-7 in SQL.
  - Existing Packaging Line 1 SQL only has 4 days (T-1 to T-4): Need to add T-5 through T-7 in SQL.
  - downtime_reasons column may not exist: The .mjs already strips downtime_reasons before insert (line 901). New data should follow the same pattern — include downtime_reasons in the data definition but strip them before upsert.

estimated_test_files:
  - No new automated test files: This is a seed data story. Validation is done by running the seed script and executing verification SQL queries (Task 6 in the story). The verification queries are documented in the story's Task 6 subtasks and will be run manually after implementation.

implementation_order:
  1. Fix shift_targets in 0021_seed_data.sql — Update Roaster 1 to morning=50, afternoon=48, night=45 (sum=143). Update Roaster 2 to morning=50, afternoon=48, night=45 (sum=143). Update Roaster 3 to morning=50, afternoon=48, night=45 (sum=143). Add Grinder 3 afternoon=1050. Add Grinder 4 afternoon=1100. Add Filler B afternoon=2200. Add Filler C afternoon=2000. Add Packaging 2 afternoon=3000. Add Packaging 3 afternoon=2800. This ensures every asset has enough shift targets to sum to its daily target.
  2. Add missing daily_summaries to 0021_seed_data.sql — Add Roaster 3 (7 days T-1 to T-7, target=143, OEE~89%, mid-performer). Add Grinder 4 (7 days, target=1950, OEE~88%, moderate). Add Filler Line B T-3 through T-7 (5 more days, target=4600). Add Filler Line C (7 days, target=4000, OEE~91%, solid performer). Add Packaging Line 2 T-3 through T-7 (5 more days, target=6200). Add Packaging Line 3 (7 days, target=5600, OEE~85%, slightly misses). Also backfill: Roaster 2 T-4 through T-7, Grinder 1 T-6 and T-7, Grinder 2 T-4 through T-7, Filler A T-5 through T-7, Packaging 1 T-5 through T-7.
  3. Add shift_targets upsert block to seed-data.mjs — Add cleanup: `await supabase.from('shift_targets').delete().neq('id', '00000000-0000-0000-0000-000000000000')` in the initial cleanup section. Add new shift_targets array with all 14 assets matching the values from step 1. Insert using `supabase.from('shift_targets').insert(shiftTargets)`.
  4. Add missing daily_summaries to seed-data.mjs — Add Roaster 3 daily summaries for T-1 through T-7 (target_output=143, varied OEE with ~89% workcenter attainment contribution). Add Grinder 4 daily summaries for T-1 through T-7 (target_output=1950, ~88% OEE). Add Filler Line B T-3 through T-7 (target_output=4600). Add Filler Line C T-1 through T-7 (target_output=4000, ~91% OEE). Add Packaging Line 2 T-3 through T-7 (target_output=6200). Add Packaging Line 3 T-1 through T-7 (target_output=5600, ~85% OEE). Data values should match corresponding SQL entries.
  5. Verify target alignment — Cross-check every asset: sum of shift_targets per asset must equal the target_output used in daily_summaries for that asset. Specifically verify: Roaster 1 (50+48+45=143 ✓), Roaster 2 (50+48+45=143 ✓), Roaster 3 (50+48+45=143 ✓), Grinder 1 (1000+950=1950 ✓), Grinder 2 (1000+950=1950 ✓), Grinder 3 (900+1050=1950 ✓), Grinder 4 (850+1100=1950 ✓), Grinder 5 (1000+950=1950 ✓), Filler A (2400+2200=4600 ✓), Filler B (2400+2200=4600 ✓), Filler C (2000+2000=4000 ✓), Pack 1 (3200+3000=6200 ✓), Pack 2 (3200+3000=6200 ✓), Pack 3 (2800+2800=5600 ✓).
  6. Run seed-data.mjs and execute validation queries — Run `node _bmad/scripts/seed-data.mjs`. Then verify with Task 6 queries: (6.2) area counts, (6.3) T-1 workcenter coverage, (6.4) attainment ranges, (6.5) shift_target coverage. Flag any API column name issues found for follow-up.
DESIGN END

---

## TEST_SPEC: 11-3-workcenter-seed-data
**Timestamp:** 2026-02-11 09:47:18

TEST SPEC START
story_id: 11-3-workcenter-seed-data
generated: 2026-02-11

test_specifications:

## AC1: Given the seed script runs successfully, When the workcenter summary endpoint is called for yesterday's date, Then data exists for all 4 workcenters (Roasting, Grinding, Filling, Packaging).

### 11-3-workcenter-seed-data-INT-001: All 4 workcenters have daily_summaries for T-1 after seed-data.mjs runs
- Priority: P0
- Type: integration
- Given: A clean database with schema migrations applied and seed-data.mjs has been executed successfully
- When: daily_summaries are queried joined with assets, filtered by report_date = CURRENT_DATE - 1, grouped by area
- Then: Exactly 4 distinct area values are returned: "Roasting", "Grinding", "Filling", "Packaging"
- Data: All 14 assets must have at least one daily_summary row for T-1

### 11-3-workcenter-seed-data-INT-002: All 4 workcenters have daily_summaries for T-1 after 0021_seed_data.sql runs
- Priority: P0
- Type: integration
- Given: A clean database with schema migrations applied via `supabase db reset` (which runs 0021_seed_data.sql)
- When: daily_summaries are queried joined with assets, filtered by report_date = CURRENT_DATE - 1, grouped by area
- Then: Exactly 4 distinct area values are returned: "Roasting", "Grinding", "Filling", "Packaging"
- Data: All 14 assets must have at least one daily_summary row for T-1

### 11-3-workcenter-seed-data-UNIT-001: seed-data.mjs generates daily_summaries entries for all 14 asset IDs
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The daily_summaries data array is inspected
- Then: All 14 asset UUIDs (a0000001-...-000000000001 through ...0014) appear in daily_summaries entries with at least a T-1 (daysAgo(1)) row each
- Data: Asset IDs: Roasters (0001, 0002, 0003), Grinders (0004, 0005, 0006, 0007, 0014), Fillers (0008, 0009, 0010), Packaging (0011, 0012, 0013)

### 11-3-workcenter-seed-data-UNIT-002: 0021_seed_data.sql generates daily_summaries INSERT statements for all 14 asset IDs at T-1
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is loaded for analysis
- When: The INSERT INTO daily_summaries statements are parsed
- Then: All 14 asset UUIDs appear in daily_summaries inserts with at least one row using CURRENT_DATE - 1
- Data: Same 14 asset UUIDs as UNIT-001

### 11-3-workcenter-seed-data-E2E-001: Workcenter summary API endpoint returns data for all 4 workcenters after seeding
- Priority: P0
- Type: e2e
- Given: The database has been seeded via seed-data.mjs and the API server is running
- When: GET /api/v1/production/workcenter-summary?date=<yesterday> is called with valid authentication
- Then: The response contains a "workcenters" array with exactly 4 entries, one each for "Roasting", "Grinding", "Filling", and "Packaging", and report_date matches yesterday
- Data: Authentication via valid JWT; date parameter = yesterday's date in ISO format

### 11-3-workcenter-seed-data-INT-003: No workcenter is missing from T-1 data (negative check)
- Priority: P1
- Type: integration
- Given: The seed script has run successfully
- When: The set of distinct area values from daily_summaries for T-1 is compared against the expected set {"Roasting", "Grinding", "Filling", "Packaging"}
- Then: The symmetric difference is empty (no missing workcenters, no extra workcenters)
- Data: Expected exactly 4 workcenters, no more, no less


## AC2: Given the seed script runs successfully, When the data is queried per workcenter, Then each workcenter has 2-4 assets with varied performance (some hit target, some miss).

### 11-3-workcenter-seed-data-INT-004: Roasting workcenter has exactly 3 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Roasting'
- Then: COUNT(DISTINCT asset_id) = 3
- Data: Roaster 1 (0001), Roaster 2 (0002), Roaster 3 (0003)

### 11-3-workcenter-seed-data-INT-005: Grinding workcenter has exactly 5 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Grinding'
- Then: COUNT(DISTINCT asset_id) = 5
- Data: Grinder 1 (0004), Grinder 2 (0005), Grinder 3 (0006), Grinder 4 (0007), Grinder 5 (0014)

### 11-3-workcenter-seed-data-INT-006: Filling workcenter has exactly 3 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Filling'
- Then: COUNT(DISTINCT asset_id) = 3
- Data: Filler A (0008), Filler B (0009), Filler C (0010)

### 11-3-workcenter-seed-data-INT-007: Packaging workcenter has exactly 3 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Packaging'
- Then: COUNT(DISTINCT asset_id) = 3
- Data: Packaging 1 (0011), Packaging 2 (0012), Packaging 3 (0013)

### 11-3-workcenter-seed-data-INT-008: Each workcenter has at least one asset that hits target on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: For each workcenter, daily_summaries for T-1 are queried and actual_output >= target_output is evaluated per asset
- Then: Every workcenter (Roasting, Grinding, Filling, Packaging) has at least 1 asset where actual_output >= target_output
- Data: Expected hit-target assets: Roaster 2, Grinder 1 or 2, Filler B or C, Packaging 1 or 2

### 11-3-workcenter-seed-data-INT-009: Each workcenter has at least one asset that misses target on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: For each workcenter, daily_summaries for T-1 are queried and actual_output < target_output is evaluated per asset
- Then: Every workcenter (Roasting, Grinding, Filling, Packaging) has at least 1 asset where actual_output < target_output
- Data: Expected miss-target assets: Roaster 1, Grinder 3 or 5, Filler A, Packaging 3

### 11-3-workcenter-seed-data-UNIT-003: seed-data.mjs daily_summaries data array contains varied actual_output vs target_output for T-1
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The daily_summaries entries for daysAgo(1) are examined per workcenter
- Then: Within each workcenter grouping, at least one asset has actual_output >= target_output and at least one has actual_output < target_output
- Data: Verify variation exists in the data definitions, not just in runtime behavior


## AC3: Given the seed data populates all workcenters, When attainment is calculated per workcenter, Then attainment ranges from ~70% to ~100% across workcenters to show realistic variation.

### 11-3-workcenter-seed-data-INT-010: Roasting workcenter attainment is approximately 88% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Roasting assets on T-1
- Then: Attainment is between 82% and 95% (centered around ~88%)
- Data: Roaster 1 ~87.5% OEE (misses target), Roaster 2 ~96% (hits), Roaster 3 ~89% (hits)

### 11-3-workcenter-seed-data-INT-011: Grinding workcenter attainment is approximately 83% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Grinding assets on T-1
- Then: Attainment is between 75% and 90% (centered around ~83%)
- Data: Grinder 2 excellent (95%+), Grinder 3 and 5 drag average, Grinder 1 decent, Grinder 4 moderate

### 11-3-workcenter-seed-data-INT-012: Filling workcenter attainment is approximately 80% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Filling assets on T-1
- Then: Attainment is between 70% and 88% (centered around ~80%)
- Data: Filler A problem child (~72%), Filler B and C solid performers

### 11-3-workcenter-seed-data-INT-013: Packaging workcenter attainment is approximately 88% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Packaging assets on T-1
- Then: Attainment is between 82% and 95% (centered around ~88%)
- Data: Packaging 1 and 2 solid, Packaging 3 slightly misses

### 11-3-workcenter-seed-data-INT-014: Cross-workcenter attainment spread covers ~70% to ~100% range
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: Attainment percentages are calculated for all 4 workcenters on T-1
- Then: The minimum workcenter attainment is <= 85% AND the maximum workcenter attainment is >= 85%, demonstrating meaningful spread. No workcenter is below 70% or above 100%.
- Data: Expected ordering approximately: Filling (~80%) < Grinding (~83%) < Roasting (~88%) ≈ Packaging (~88%)

### 11-3-workcenter-seed-data-UNIT-004: No individual asset attainment is unrealistically extreme
- Priority: P1
- Type: unit
- Given: Seed data is loaded
- When: actual_output / target_output is calculated for each of the 14 assets on T-1
- Then: No asset has attainment below 50% or above 110% (guarding against data entry errors in seed data)
- Data: All 14 assets checked individually


## AC4: Given the existing seed data assets already have area assignments, When the seed data is reviewed, Then all 14 assets are assigned to their correct workcenter area (Roasting: 3, Grinding: 5, Filling: 3, Packaging: 3).

### 11-3-workcenter-seed-data-UNIT-005: seed-data.mjs assets array assigns correct area to all 14 assets
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The assets array is inspected for area field assignments
- Then: Roasting has exactly 3 assets (Roaster 1, 2, 3), Grinding has exactly 5 assets (Grinder 1, 2, 3, 4, 5), Filling has exactly 3 assets (Filler A, B, C), Packaging has exactly 3 assets (Packaging 1, 2, 3)
- Data: Asset count per area: Roasting=3, Grinding=5, Filling=3, Packaging=3, total=14

### 11-3-workcenter-seed-data-UNIT-006: 0021_seed_data.sql assets INSERT assigns correct area to all 14 assets
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is analyzed
- When: The INSERT INTO assets statements are parsed for area values
- Then: Area assignments match: Roasting=3, Grinding=5, Filling=3, Packaging=3, total=14 assets
- Data: Same distribution as UNIT-005; UUIDs must match between .mjs and .sql

### 11-3-workcenter-seed-data-INT-015: Database query confirms correct asset counts per workcenter area
- Priority: P0
- Type: integration
- Given: Seed data has been loaded via either mechanism
- When: SELECT area, COUNT(*) FROM assets GROUP BY area is executed
- Then: Result set contains exactly: Roasting=3, Grinding=5, Filling=3, Packaging=3
- Data: Total asset count should be exactly 14

### 11-3-workcenter-seed-data-UNIT-007: Asset UUIDs are consistent between seed-data.mjs and 0021_seed_data.sql
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: The set of asset UUIDs in seed-data.mjs is compared with those in 0021_seed_data.sql
- Then: The UUID sets are identical (same 14 UUIDs) and each UUID maps to the same asset name and area in both files
- Data: UUID format a0000001-0000-0000-0000-000000000001 through ...0014

### 11-3-workcenter-seed-data-UNIT-008: No asset has a NULL or empty area assignment
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: All asset entries are inspected for the area field
- Then: Every asset has a non-null, non-empty area value that is one of: "Roasting", "Grinding", "Filling", "Packaging"
- Data: Check all 14 assets in both files


## AC5: Given all assets exist in the assets table with area values, When shift_targets are queried, Then every asset has at least one shift target record so the workcenter scorecard can compute attainment.

### 11-3-workcenter-seed-data-INT-016: Every asset has at least one shift_target record after seeding
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SELECT a.id, a.name, COUNT(st.id) as target_count FROM assets a LEFT JOIN shift_targets st ON a.id = st.asset_id GROUP BY a.id, a.name is executed
- Then: Every asset (14 total) has target_count >= 1; no asset has 0 shift_target records
- Data: All 14 asset IDs must appear with at least one shift_target

### 11-3-workcenter-seed-data-UNIT-009: seed-data.mjs contains a shift_targets upsert/insert block
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The script is searched for shift_targets data insertion code
- Then: A shift_targets insert or upsert block exists that covers all 14 asset UUIDs
- Data: Previously this block was completely absent from seed-data.mjs; story 11.3 must add it

### 11-3-workcenter-seed-data-UNIT-010: 0021_seed_data.sql contains shift_targets INSERT for all 14 assets
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is analyzed
- When: The INSERT INTO shift_targets statements are parsed for distinct asset_id values
- Then: All 14 asset UUIDs appear in shift_targets INSERT statements
- Data: Each asset needs at least one row (morning, afternoon, and/or night shift)

### 11-3-workcenter-seed-data-INT-017: All workcenters have shift_target coverage
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SELECT a.area, COUNT(DISTINCT st.asset_id) FROM shift_targets st JOIN assets a ON a.id = st.asset_id GROUP BY a.area is executed
- Then: Roasting=3, Grinding=5, Filling=3, Packaging=3 (all assets in each workcenter have targets)
- Data: Same distribution as asset counts per workcenter

### 11-3-workcenter-seed-data-INT-018: shift_targets have valid target_output values (> 0)
- Priority: P1
- Type: integration
- Given: Seed data has been loaded
- When: SELECT * FROM shift_targets WHERE target_output <= 0 is executed
- Then: Zero rows returned (all shift targets have positive target_output values)
- Data: target_output column is INTEGER NOT NULL, but values must also be positive

### 11-3-workcenter-seed-data-UNIT-011: seed-data.mjs handles shift_targets cleanup to prevent duplicates on re-run
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The shift_targets insertion section is inspected
- Then: A delete-before-insert or equivalent idempotency pattern exists for shift_targets (since the table has no unique constraint for upsert)
- Data: Pattern should match existing cleanup approach used for live_snapshots and safety_events

### 11-3-workcenter-seed-data-INT-019: Running seed-data.mjs twice does not create duplicate shift_target rows
- Priority: P0
- Type: integration
- Given: seed-data.mjs has been run once successfully
- When: seed-data.mjs is run a second time
- Then: The total number of shift_target rows is the same as after the first run (no duplicates created)
- Data: COUNT(*) FROM shift_targets should be identical after both runs


## AC6: Given daily_summaries and shift_targets exist for all assets, When the target_output in daily_summaries is compared to shift_targets.target_output, Then the values are aligned so that the workcenter summary API endpoint (Story 11.1) can use either source consistently without conflicting numbers.

### 11-3-workcenter-seed-data-INT-020: daily_summaries.target_output equals sum of shift_targets.target_output for each asset
- Priority: P0
- Type: integration
- Given: Seed data has been loaded with both daily_summaries and shift_targets
- When: For each asset, daily_summaries.target_output (for T-1) is compared against SUM(shift_targets.target_output) for that asset
- Then: The values are equal for all 14 assets (daily target = sum of all shift targets for that asset)
- Data: Roaster 1/2/3: 143 = 50+48+45; Grinder 1/2: 1950 = 1000+950; Grinder 3: 1950 = 900+1050; Grinder 4: 1950 = 850+1100; Grinder 5: 1950 = 1000+950; Filler A: 4600 = 2400+2200; Filler B: 4600 = 2400+2200; Filler C: 4000 = 2000+2000; Pack 1: 6200 = 3200+3000; Pack 2: 6200 = 3200+3000; Pack 3: 5600 = 2800+2800

### 11-3-workcenter-seed-data-UNIT-012: Roaster shift_targets sum to 143 in seed-data.mjs (previously mismatched)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The shift_targets entries for Roaster 1, 2, and 3 are inspected
- Then: Each roaster's shift_targets sum to exactly 143 (matching daily_summaries.target_output = 143)
- Data: Expected: morning=50, afternoon=48, night=45 (sum=143) for each roaster. Previously Roasters summed to 93 (48+45) -- a known mismatch

### 11-3-workcenter-seed-data-UNIT-013: Roaster shift_targets sum to 143 in 0021_seed_data.sql (previously mismatched)
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is analyzed
- When: The INSERT INTO shift_targets for Roaster 1, 2, and 3 are parsed and their target_output values summed
- Then: Each roaster's shift_targets sum to exactly 143
- Data: Same expected values as UNIT-012

### 11-3-workcenter-seed-data-UNIT-014: All Grinder shift_targets sum to their respective daily targets
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: Shift target values for Grinders 1-5 are summed per asset
- Then: Each grinder's shift_targets sum to 1950 (matching daily_summaries.target_output)
- Data: Grinder 1: 1000+950=1950, Grinder 2: 1000+950=1950, Grinder 3: 900+1050=1950, Grinder 4: 850+1100=1950, Grinder 5: 1000+950=1950

### 11-3-workcenter-seed-data-UNIT-015: All Filler shift_targets sum to their respective daily targets
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: Shift target values for Fillers A, B, C are summed per asset
- Then: Filler A: sum=4600, Filler B: sum=4600, Filler C: sum=4000 (matching respective daily_summaries.target_output)
- Data: Filler A: 2400+2200, Filler B: 2400+2200, Filler C: 2000+2000

### 11-3-workcenter-seed-data-UNIT-016: All Packaging shift_targets sum to their respective daily targets
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: Shift target values for Packaging 1, 2, 3 are summed per asset
- Then: Pack 1: sum=6200, Pack 2: sum=6200, Pack 3: sum=5600 (matching respective daily_summaries.target_output)
- Data: Pack 1: 3200+3000, Pack 2: 3200+3000, Pack 3: 2800+2800

### 11-3-workcenter-seed-data-UNIT-017: target_output values are consistent across all 7 days per asset in seed-data.mjs
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: daily_summaries entries for each asset across T-1 through T-7 are inspected
- Then: The target_output value is the same for every day for a given asset (targets don't change day-to-day)
- Data: Each asset uses a fixed daily target: Roasters=143, Grinders=1950, Filler A/B=4600, Filler C=4000, Pack 1/2=6200, Pack 3=5600

### 11-3-workcenter-seed-data-INT-021: Alignment query returns zero mismatches
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: A query compares daily_summaries.target_output for T-1 against the SUM of shift_targets.target_output for each asset: SELECT a.name, ds.target_output as daily_target, SUM(st.target_output) as shift_sum FROM daily_summaries ds JOIN assets a ON a.id = ds.asset_id JOIN shift_targets st ON st.asset_id = ds.asset_id WHERE ds.report_date = CURRENT_DATE - 1 GROUP BY a.name, ds.target_output HAVING ds.target_output != SUM(st.target_output)
- Then: Zero rows returned (no mismatches)
- Data: All 14 assets should have perfectly aligned targets

### 11-3-workcenter-seed-data-UNIT-018: Both seed files use identical target_output values for the same assets
- Priority: P0
- Type: unit
- Given: Both seed-data.mjs and 0021_seed_data.sql are analyzed
- When: The daily_summaries.target_output and shift_targets.target_output values are extracted from both files for each asset
- Then: The values match exactly between the two files for every asset
- Data: Cross-reference all 14 assets' target values across both files


## Additional Coverage: Data Completeness (7-day coverage)

### 11-3-workcenter-seed-data-INT-022: All 14 assets have daily_summaries for T-1 through T-7
- Priority: P1
- Type: integration
- Given: Seed data has been loaded
- When: SELECT a.name, COUNT(ds.id) as day_count FROM assets a LEFT JOIN daily_summaries ds ON a.id = ds.asset_id WHERE ds.report_date >= CURRENT_DATE - 7 AND ds.report_date <= CURRENT_DATE - 1 GROUP BY a.name is executed
- Then: Every asset has day_count = 7 (full 7-day coverage)
- Data: Previously missing: Roaster 3 (0 days), Grinder 4 (0 days), Filler C (0 days), Packaging 3 (0 days), Filler B (only 2), Packaging 2 (only 2)

### 11-3-workcenter-seed-data-INT-023: seed-data.mjs executes without errors
- Priority: P0
- Type: integration
- Given: A running Supabase instance with schema migrations applied
- When: `node scripts/seed-data.mjs` (or `node _bmad/scripts/seed-data.mjs`) is executed
- Then: The script completes with exit code 0 and no error output
- Data: Requires SUPABASE_URL and SUPABASE_KEY environment variables


edge_cases:
  - Running seed-data.mjs multiple times in succession produces identical data (idempotency) -- covered by INT-019
  - Asset with no shift_targets should not cause division-by-zero in attainment calculation (prevented by AC5)
  - Filler C and Packaging 3 have different target_output values than their workcenter peers (4000 vs 4600 and 5600 vs 6200) -- ensure attainment calculations handle non-uniform targets correctly
  - Roaster 3 shift_targets previously summed to 84 (42+42) which didn't match any known daily target -- must be corrected to sum to 143
  - The daily_summaries unique constraint on (asset_id, report_date) means duplicate inserts should be handled gracefully via upsert
  - SQL migration uses CURRENT_DATE - N which shifts with time, so test assertions should use relative dates not absolute dates
  - shift_targets table has NO unique constraint -- repeated inserts will create duplicates unless explicitly handled

error_scenarios:
  - Seed script runs against database missing schema migrations (assets table doesn't exist) -- should fail with clear error, not silently skip
  - Seed script runs with invalid/missing Supabase credentials -- should fail with authentication error
  - Partial seed failure mid-execution (e.g., first 7 assets seed, then connection drops) -- on re-run, upsert should recover gracefully for daily_summaries; shift_targets delete-then-insert should also recover
  - Database has stale seed data from previous schema version (e.g., column renamed) -- script should fail with clear column mismatch error rather than inserting into wrong columns
  - shift_targets insert attempted for an asset_id that doesn't exist yet (foreign key violation) -- seed ordering must ensure assets are inserted before shift_targets

test_file_mapping:
  - 11-3-workcenter-seed-data-E2E-*: apps/api/tests/api/test_workcenter_seed_e2e.py
  - 11-3-workcenter-seed-data-UNIT-*: supabase/tests/seed-data-validation.test.ts
  - 11-3-workcenter-seed-data-INT-*: supabase/tests/seed-data-integration.test.ts

TEST SPEC END

---
