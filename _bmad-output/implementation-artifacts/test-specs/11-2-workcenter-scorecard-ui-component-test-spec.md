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
