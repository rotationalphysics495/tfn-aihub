TEST SPEC START
story_id: 17-4-shift-breakdown-api-ui
generated: 2026-02-12

test_specifications:

## AC1: Given the workcenter summary endpoint is called with shift data available, When the response is returned, Then each workcenter entry includes a `shift_breakdown` array with per-shift metrics (shift name, actual output, target output, attainment %, OEE, downtime minutes) And the overall workcenter figures are the aggregation across shifts.

### 17-4-shift-breakdown-api-ui-INT-001: Workcenter summary returns shift_breakdown array when shift_summaries data exists
- Priority: P0
- Type: integration
- Given: The `shift_summaries` table has records for 3 shifts (morning, afternoon, night) for date 2026-02-10 linked to assets in the "Grinding" workcenter, and `daily_summaries` has the daily aggregate for the same date
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10` is called with a valid JWT
- Then: The response status is 200 and each `WorkcenterEntry` in `workcenters` contains a `shift_breakdown` array with 3 entries, each having fields: `shift` (string), `actual_output` (int), `target_output` (int), `attainment_pct` (float), `oee` (float), `downtime_minutes` (int)
- Data: 3 shift_summaries rows per asset (morning: 400 units, afternoon: 350 units, night: 300 units), daily_summaries showing 1050 total units, 2 assets in "Grinding" area

### 17-4-shift-breakdown-api-ui-INT-002: Overall workcenter figures equal aggregation of shift values
- Priority: P0
- Type: integration
- Given: The `shift_summaries` table has records for 3 shifts for 2 assets in the "Grinding" workcenter: morning (400 units, 45 min downtime), afternoon (350 units, 60 min downtime), night (300 units, 30 min downtime)
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10` is called with a valid JWT
- Then: The `WorkcenterEntry.total_actual` equals the sum of all shift `actual_output` values across assets, and `WorkcenterEntry` downtime and attainment figures are consistent with the aggregate of shift data
- Data: Shift records summing to 1050 units per asset, 2100 total for workcenter, target 2500

### 17-4-shift-breakdown-api-ui-INT-003: Shift filter parameter returns only that shift's data
- Priority: P0
- Type: integration
- Given: The `shift_summaries` table has records for all 3 shifts for date 2026-02-10
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10&shift=afternoon` is called with a valid JWT
- Then: The response returns workcenter entries with metrics from the afternoon shift only (not aggregated), and the `shift_breakdown` array is absent or empty since a single shift was requested
- Data: Afternoon shift: 350 units produced, 82% OEE, 60 min downtime per asset

### 17-4-shift-breakdown-api-ui-INT-004: Empty shift_breakdown when no shift_summaries data exists (backward compatibility)
- Priority: P0
- Type: integration
- Given: The `daily_summaries` table has data for date 2026-02-10 but the `shift_summaries` table has no records for that date
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10` is called with a valid JWT
- Then: The response status is 200, workcenter entries contain daily aggregate figures from `daily_summaries`, and `shift_breakdown` is an empty array or null for each entry
- Data: daily_summaries with 1050 units, 85% OEE; no shift_summaries rows

### 17-4-shift-breakdown-api-ui-INT-005: Date defaults to T-1 when not provided
- Priority: P1
- Type: integration
- Given: The `daily_summaries` and `shift_summaries` tables have data for yesterday's date
- When: `GET /api/v1/production/workcenter-summary` is called without a `date` parameter and with a valid JWT
- Then: The response `report_date` equals yesterday's date (T-1) and the data corresponds to yesterday
- Data: shift_summaries and daily_summaries for T-1 date

### 17-4-shift-breakdown-api-ui-INT-006: Invalid shift parameter handled gracefully
- Priority: P1
- Type: integration
- Given: A valid JWT and data exists for the requested date
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10&shift=invalid_shift` is called
- Then: The response returns a 422 validation error (Pydantic/FastAPI query param validation) or falls back to returning aggregate data without filtering
- Data: Valid daily_summaries and shift_summaries for 2026-02-10

### 17-4-shift-breakdown-api-ui-INT-007: Endpoint requires authentication
- Priority: P0
- Type: integration
- Given: No JWT token is provided in the request headers
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10` is called
- Then: The response status is 401 Unauthorized
- Data: None

### 17-4-shift-breakdown-api-ui-UNIT-001: ShiftBreakdown Pydantic model validates required fields
- Priority: P1
- Type: unit
- Given: A ShiftBreakdown model is instantiated with valid data
- When: The model is created with shift="morning", actual_output=400, target_output=500, attainment_pct=80.0, oee=82.5, downtime_minutes=45
- Then: The model is valid and all fields are accessible with correct types and values
- Data: Valid shift breakdown field values

### 17-4-shift-breakdown-api-ui-UNIT-002: ShiftBreakdown model rejects invalid values
- Priority: P2
- Type: unit
- Given: Invalid data for ShiftBreakdown (e.g., negative actual_output, missing required fields)
- When: The model is instantiated
- Then: A Pydantic ValidationError is raised
- Data: actual_output=-1, missing shift field

### 17-4-shift-breakdown-api-ui-UNIT-003: WorkcenterEntry shift_breakdown field is optional and defaults to empty
- Priority: P1
- Type: unit
- Given: A WorkcenterEntry model is created without providing shift_breakdown
- When: The model is instantiated with only the existing required fields
- Then: The shift_breakdown field defaults to an empty list or None, maintaining backward compatibility
- Data: Existing WorkcenterEntry fields only (workcenter, total_actual, total_target, etc.)


## AC2: Given the workcenter scorecard renders with shift data, When the user clicks a shift tab or toggle (Morning / Afternoon / Night / All), Then the scorecard filters to show only that shift's data And the action items below also filter to the selected shift.

### 17-4-shift-breakdown-api-ui-UNIT-004: ShiftTabs renders all four tab options
- Priority: P0
- Type: unit
- Given: The ShiftTabs component is rendered with default props
- When: The component mounts
- Then: Four tabs are visible: "All", "Morning", "Afternoon", "Night" and "All" is selected by default
- Data: No special data needed; default props

### 17-4-shift-breakdown-api-ui-UNIT-005: ShiftTabs emits correct value on tab click
- Priority: P0
- Type: unit
- Given: The ShiftTabs component is rendered with an `onValueChange` callback
- When: The user clicks the "Afternoon" tab
- Then: The `onValueChange` callback is called with `"afternoon"`
- Data: Mock onValueChange callback via vi.fn()

### 17-4-shift-breakdown-api-ui-UNIT-006: ShiftTabs respects controlled value prop
- Priority: P1
- Type: unit
- Given: The ShiftTabs component is rendered with `value="night"`
- When: The component mounts
- Then: The "Night" tab is visually selected/active
- Data: value="night" prop

### 17-4-shift-breakdown-api-ui-UNIT-007: ShiftTabs has accessible ARIA attributes
- Priority: P2
- Type: unit
- Given: The ShiftTabs component is rendered
- When: The component mounts
- Then: Tab elements have role="tab", the tab list has role="tablist", and the selected tab has aria-selected="true"
- Data: Default rendered component

### 17-4-shift-breakdown-api-ui-UNIT-008: WorkcenterScorecard passes shift param to useWorkcenterSummary when shift is selected
- Priority: P0
- Type: unit
- Given: The WorkcenterScorecard component is rendered with `selectedShift="morning"`
- When: The component mounts and calls useWorkcenterSummary
- Then: The useWorkcenterSummary hook is called with options including `shift: "morning"`
- Data: Mock useWorkcenterSummary hook, selectedShift="morning" prop

### 17-4-shift-breakdown-api-ui-UNIT-009: WorkcenterScorecard does not pass shift param when "all" is selected
- Priority: P0
- Type: unit
- Given: The WorkcenterScorecard component is rendered with `selectedShift="all"` or no selectedShift
- When: The component mounts and calls useWorkcenterSummary
- Then: The useWorkcenterSummary hook is called without a shift parameter (or shift is undefined/null)
- Data: Mock useWorkcenterSummary hook, selectedShift="all" prop

### 17-4-shift-breakdown-api-ui-UNIT-010: WorkcenterScorecard displays shift-filtered data correctly
- Priority: P1
- Type: unit
- Given: The WorkcenterScorecard component is rendered with `selectedShift="afternoon"` and the mock hook returns afternoon-only metrics (350 units, 82% OEE)
- When: The component renders
- Then: The scorecard displays "350" for actual output and "82%" for OEE (the afternoon shift's values, not the daily aggregate)
- Data: Mock useWorkcenterSummary returning afternoon-specific data

### 17-4-shift-breakdown-api-ui-INT-008: useWorkcenterSummary includes shift in API URL when provided
- Priority: P0
- Type: unit
- Given: The useWorkcenterSummary hook is called with `{ date: '2026-02-10', shift: 'morning' }`
- When: The hook triggers a fetch
- Then: The fetch URL includes `&shift=morning` as a query parameter
- Data: Mock fetch, mock supabase auth session

### 17-4-shift-breakdown-api-ui-INT-009: useWorkcenterSummary omits shift from URL when not provided
- Priority: P1
- Type: unit
- Given: The useWorkcenterSummary hook is called with `{ date: '2026-02-10' }` (no shift)
- When: The hook triggers a fetch
- Then: The fetch URL does NOT include a `shift` query parameter
- Data: Mock fetch, mock supabase auth session

### 17-4-shift-breakdown-api-ui-INT-010: useWorkcenterSummary refetches when shift changes
- Priority: P1
- Type: unit
- Given: The useWorkcenterSummary hook is rendered with `shift: 'morning'`
- When: The shift prop changes to `'afternoon'`
- Then: A new fetch call is made with `&shift=afternoon` in the URL
- Data: Mock fetch tracking call count and URLs

### 17-4-shift-breakdown-api-ui-INT-011: MorningReportClient syncs shift state with URL params
- Priority: P1
- Type: integration
- Given: The MorningReportClient is rendered with URL search param `?shift=afternoon`
- When: The component initializes
- Then: The ShiftTabs component shows "Afternoon" as selected and WorkcenterScorecard receives `selectedShift="afternoon"`
- Data: Mock useSearchParams returning 'afternoon' for shift, mock hooks

### 17-4-shift-breakdown-api-ui-INT-012: Shift tab change updates URL query parameter
- Priority: P1
- Type: integration
- Given: The MorningReportClient is rendered with ShiftTabs
- When: The user clicks the "Night" tab
- Then: The router pushes a URL update with `?shift=night` and the state updates accordingly
- Data: Mock router.push, mock ShiftTabs onValueChange callback


## AC3: Given an action item missed target primarily on one shift, When the action card renders, Then it shows shift attribution: e.g. "Grinder 5: 72 min downtime (afternoon shift -- 58 min mechanical)" And the recommendation targets the responsible shift.

### 17-4-shift-breakdown-api-ui-UNIT-011: _get_shift_attribution returns attribution when one shift exceeds 60% of total miss
- Priority: P0
- Type: unit
- Given: An asset has shift_summaries data where afternoon shift has 58 min downtime out of 80 min total (72.5% > 60% threshold)
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called
- Then: It returns a string like "afternoon shift — 58 min mechanical" attributing the miss to the afternoon shift
- Data: shift_summaries: morning=12min, afternoon=58min, night=10min downtime

### 17-4-shift-breakdown-api-ui-UNIT-012: _get_shift_attribution returns attribution based on output gap when downtime is not the primary metric
- Priority: P1
- Type: unit
- Given: An asset has shift_summaries data where morning shift accounts for >60% of the total output gap (target - actual)
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called
- Then: It returns a string attributing the miss to the morning shift with output context
- Data: shift_summaries: morning=200 actual/500 target (300 gap), afternoon=450/500 (50 gap), night=400/500 (100 gap); morning is 300/450 = 66.7% > 60%

### 17-4-shift-breakdown-api-ui-UNIT-013: shift_attribution field added to ActionItem schema is optional and nullable
- Priority: P0
- Type: unit
- Given: An ActionItem Pydantic model is created without providing shift_attribution
- When: The model is serialized to JSON
- Then: The `shift_attribution` field is present with value `null` (or absent), and existing fields are unchanged
- Data: Existing ActionItem fields only (no shift_attribution provided)

### 17-4-shift-breakdown-api-ui-UNIT-014: ActionItem with shift_attribution serializes correctly
- Priority: P1
- Type: unit
- Given: An ActionItem is created with `shift_attribution="afternoon shift — 58 min mechanical"`
- When: The model is serialized to JSON
- Then: The JSON includes `"shift_attribution": "afternoon shift — 58 min mechanical"`
- Data: Full ActionItem with shift_attribution string

### 17-4-shift-breakdown-api-ui-INT-013: generate_action_list enriches OEE actions with shift attribution
- Priority: P0
- Type: integration
- Given: An asset missed OEE target, and shift_summaries shows afternoon shift contributed >60% of total downtime
- When: `generate_action_list(target_date)` is called on the ActionEngine
- Then: The returned ActionItem for that asset has `shift_attribution` set to a descriptive string mentioning the afternoon shift
- Data: Mock daily_summaries with OEE miss, mock shift_summaries with skewed downtime distribution

### 17-4-shift-breakdown-api-ui-INT-014: Safety actions are NOT enriched with shift attribution
- Priority: P1
- Type: integration
- Given: A safety event action item exists in the generated action list
- When: `generate_action_list(target_date)` is called
- Then: The safety ActionItem has `shift_attribution` as None regardless of shift_summaries data
- Data: Mock safety event data, mock shift_summaries data

### 17-4-shift-breakdown-api-ui-UNIT-015: InsightSection renders shift attribution badge when prop is provided
- Priority: P0
- Type: unit
- Given: The InsightSection component is rendered with `shiftAttribution="afternoon shift — 58 min mechanical"`
- When: The component renders
- Then: A badge/pill element is visible containing the text "afternoon shift — 58 min mechanical" below the recommendation text
- Data: Standard InsightSection props plus shiftAttribution string

### 17-4-shift-breakdown-api-ui-UNIT-016: InsightEvidenceCard passes shiftAttribution from ActionItem to InsightSection
- Priority: P1
- Type: unit
- Given: An InsightEvidenceCard is rendered with an ActionItem that has `shiftAttribution="morning shift — 45 min downtime"`
- When: The component renders
- Then: The InsightSection child component receives the `shiftAttribution` prop
- Data: ActionItem with shiftAttribution, mock child component rendering

### 17-4-shift-breakdown-api-ui-UNIT-017: Frontend ActionItem type includes optional shiftAttribution field
- Priority: P1
- Type: unit
- Given: A TypeScript ActionItem object is constructed
- When: The shiftAttribution field is omitted
- Then: The type check passes (field is optional) and the object is valid
- Data: ActionItem without shiftAttribution

### 17-4-shift-breakdown-api-ui-UNIT-018: Transformer maps shift_attribution from API to shiftAttribution in frontend type
- Priority: P1
- Type: unit
- Given: An API response ActionItem has `shift_attribution: "afternoon shift — 58 min mechanical"`
- When: The `transformAPIActionItem` function processes the response
- Then: The transformed object has `shiftAttribution: "afternoon shift — 58 min mechanical"`
- Data: Mock API response with shift_attribution field


## AC4: Given all three shifts missed target (systemic issue), When the action card renders, Then it remains a daily-level item without shift attribution And the recommendation reflects a systemic rather than shift-specific issue.

### 17-4-shift-breakdown-api-ui-UNIT-019: _get_shift_attribution returns None when no shift exceeds 60% threshold (systemic)
- Priority: P0
- Type: unit
- Given: An asset has shift_summaries data where all three shifts contribute roughly equally to the miss: morning=35%, afternoon=35%, night=30%
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called
- Then: It returns `None` (no single shift dominates)
- Data: shift_summaries: morning=28min, afternoon=28min, night=24min downtime (total 80min, no shift >60%)

### 17-4-shift-breakdown-api-ui-UNIT-020: _get_shift_attribution returns None when shift_summaries data is absent
- Priority: P0
- Type: unit
- Given: No shift_summaries records exist for the given asset and date
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called with empty data
- Then: It returns `None`
- Data: Empty shift_data dict/list for the asset

### 17-4-shift-breakdown-api-ui-UNIT-021: _get_shift_attribution returns None at exactly 60% threshold (boundary test)
- Priority: P1
- Type: unit
- Given: An asset has shift_summaries data where one shift contributes exactly 60% of the total miss (not exceeding)
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called
- Then: It returns `None` because the threshold is >60% (strictly greater than)
- Data: shift_summaries: morning=48min, afternoon=20min, night=12min (total 80min, morning=60% exactly)

### 17-4-shift-breakdown-api-ui-UNIT-022: _get_shift_attribution returns attribution at 61% (just above threshold)
- Priority: P1
- Type: unit
- Given: An asset has shift_summaries data where one shift contributes 61% of the total miss
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called
- Then: It returns a non-None string attributing the miss to that shift
- Data: shift_summaries: morning=48.8min, afternoon=20min, night=11.2min (total 80min, morning=61%)

### 17-4-shift-breakdown-api-ui-INT-015: Systemic action items have None shift_attribution in API response
- Priority: P0
- Type: integration
- Given: An asset missed OEE target with all shifts contributing roughly equally to the miss
- When: `generate_action_list(target_date)` is called
- Then: The returned ActionItem has `shift_attribution` as `None` and the recommendation_text does not reference a specific shift
- Data: Mock daily_summaries with OEE miss, mock shift_summaries with even distribution

### 17-4-shift-breakdown-api-ui-UNIT-023: InsightSection does NOT render shift badge when shiftAttribution is undefined
- Priority: P0
- Type: unit
- Given: The InsightSection component is rendered without a `shiftAttribution` prop
- When: The component renders
- Then: No shift badge/pill element is visible; the card appears identical to the existing daily-level layout
- Data: Standard InsightSection props without shiftAttribution

### 17-4-shift-breakdown-api-ui-UNIT-024: InsightSection does NOT render shift badge when shiftAttribution is null
- Priority: P1
- Type: unit
- Given: The InsightSection component is rendered with `shiftAttribution={null}`
- When: The component renders
- Then: No shift badge/pill element is visible
- Data: Standard InsightSection props with shiftAttribution explicitly set to null


## Cross-cutting: Backward Compatibility & Edge Cases

### 17-4-shift-breakdown-api-ui-INT-016: "All" tab shows same data as current daily view (backward compatibility)
- Priority: P0
- Type: integration
- Given: The workcenter-summary endpoint has been enhanced with shift support and shift_summaries data exists
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10` is called without a shift parameter (equivalent to "All" tab)
- Then: The response `total_actual`, `total_target`, and `attainment_pct` on each WorkcenterEntry match the pre-existing daily aggregate values from daily_summaries
- Data: daily_summaries and shift_summaries for the same date; shift totals equal daily totals

### 17-4-shift-breakdown-api-ui-INT-017: Shift values sum to daily totals (data consistency)
- Priority: P0
- Type: integration
- Given: Both daily_summaries and shift_summaries exist for the same date and asset set
- When: The workcenter summary is queried without shift filter
- Then: For each asset, the sum of shift_breakdown[*].actual_output equals the asset's daily actual_output, and the sum of shift_breakdown[*].downtime_minutes equals the asset's daily downtime_minutes
- Data: Consistent seed data: 3 shifts summing to daily totals per asset

### 17-4-shift-breakdown-api-ui-INT-018: Partial shift data handled gracefully
- Priority: P1
- Type: integration
- Given: An asset has shift_summaries for only 2 of 3 shifts (e.g., morning and afternoon exist, night is missing)
- When: The workcenter summary is queried
- Then: The shift_breakdown array contains only 2 entries for that asset (the available shifts), and the aggregate figures still come from daily_summaries
- Data: shift_summaries with only morning and afternoon rows for one asset

### 17-4-shift-breakdown-api-ui-UNIT-025: ShiftTabs hidden or disabled when no shift data exists
- Priority: P1
- Type: unit
- Given: The WorkcenterScorecard receives data where all workcenters have empty shift_breakdown arrays
- When: The component renders in the MorningReportClient
- Then: The ShiftTabs component is either hidden or individual shift tabs (Morning/Afternoon/Night) are disabled, with "All" still functional
- Data: Mock useWorkcenterSummary returning workcenters with empty shift_breakdown arrays

### 17-4-shift-breakdown-api-ui-INT-019: Action engine handles shift_summaries query failure gracefully
- Priority: P1
- Type: integration
- Given: The shift_summaries table query throws an exception (e.g., network error)
- When: `generate_action_list(target_date)` is called
- Then: The action list is still returned successfully but all items have `shift_attribution` as None (graceful degradation)
- Data: Mock Supabase client that raises exception on shift_summaries query

### 17-4-shift-breakdown-api-ui-INT-020: Workcenter summary endpoint handles shift_summaries query failure gracefully
- Priority: P1
- Type: integration
- Given: The daily_summaries query succeeds but the shift_summaries table query fails
- When: `GET /api/v1/production/workcenter-summary?date=2026-02-10` is called
- Then: The response returns 200 with daily aggregate data and empty shift_breakdown arrays (graceful degradation, not 500 error)
- Data: Mock Supabase client: daily_summaries succeeds, shift_summaries throws

### 17-4-shift-breakdown-api-ui-UNIT-026: _get_shift_attribution handles zero total downtime (no division by zero)
- Priority: P1
- Type: unit
- Given: An asset has shift_summaries data where all shifts have 0 downtime minutes
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called
- Then: It returns `None` without raising a division by zero error
- Data: shift_summaries: morning=0min, afternoon=0min, night=0min downtime

### 17-4-shift-breakdown-api-ui-UNIT-027: _get_shift_attribution handles single shift data only
- Priority: P2
- Type: unit
- Given: An asset has shift_summaries for only 1 shift (e.g., morning only, with 100% of the miss)
- When: `_get_shift_attribution(asset_id, target_date, shift_data)` is called
- Then: It returns attribution to that single shift (100% > 60%)
- Data: shift_summaries: morning=80min only, no afternoon or night records


edge_cases:
  - Rapid shift tab switching causing race conditions in API calls (stale data prevention via mountedRef pattern)
  - Shift names with unexpected casing (e.g., "Morning" vs "morning") in URL params or API responses
  - Zero total downtime across all shifts preventing percentage calculation (division by zero guard)
  - Only 1 or 2 shifts having data instead of all 3 (partial shift coverage)
  - Shift_summaries data existing but daily_summaries missing for the same date
  - Very large numbers of assets per workcenter (performance of shift_breakdown aggregation)
  - URL ?shift= parameter with empty string vs absent parameter

error_scenarios:
  - Supabase shift_summaries query timeout or network failure during workcenter summary fetch
  - Supabase shift_summaries query failure during action engine enrichment
  - Invalid date format in workcenter-summary endpoint query parameter
  - Invalid shift value in query parameter (not morning/afternoon/night)
  - JWT expired or missing on workcenter-summary endpoint
  - Frontend fetch failure when shift param causes server error
  - Transformer receiving malformed shift_attribution value from API

test_file_mapping:
  - 17-4-shift-breakdown-api-ui-INT-001 to INT-007, INT-016 to INT-018, INT-020: apps/api/tests/test_shift_breakdown_api.py
  - 17-4-shift-breakdown-api-ui-UNIT-001 to UNIT-003: apps/api/tests/test_shift_breakdown_api.py
  - 17-4-shift-breakdown-api-ui-UNIT-011, UNIT-012, UNIT-019 to UNIT-022, UNIT-026, UNIT-027: apps/api/tests/test_shift_attribution.py
  - 17-4-shift-breakdown-api-ui-UNIT-013, UNIT-014: apps/api/tests/test_shift_attribution.py
  - 17-4-shift-breakdown-api-ui-INT-013 to INT-015, INT-019: apps/api/tests/test_shift_attribution.py
  - 17-4-shift-breakdown-api-ui-UNIT-004 to UNIT-007: apps/web/src/components/production/__tests__/ShiftTabs.test.tsx
  - 17-4-shift-breakdown-api-ui-UNIT-008 to UNIT-010, UNIT-025: apps/web/src/components/production/__tests__/WorkcenterScorecard.shift.test.tsx
  - 17-4-shift-breakdown-api-ui-INT-008 to INT-010: apps/web/src/hooks/__tests__/useWorkcenterSummary.shift.test.ts
  - 17-4-shift-breakdown-api-ui-INT-011, INT-012: apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.shift.test.tsx
  - 17-4-shift-breakdown-api-ui-UNIT-015 to UNIT-018, UNIT-023, UNIT-024: apps/web/src/components/action-engine/__tests__/InsightSection.shift.test.tsx

TEST SPEC END
