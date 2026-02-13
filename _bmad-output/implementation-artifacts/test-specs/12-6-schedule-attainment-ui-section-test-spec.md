TEST SPEC START
story_id: 12-6-schedule-attainment-ui-section
generated: 2026-02-11

test_specifications:

## AC1: Given schedule attainment data exists for the report date, When the morning report loads, Then a "Schedule Attainment" section appears between the MorningSummarySection and the "Today's Action Items" section, And each workcenter shows: scheduled products, actual products, attainment % per product, And variance callouts are highlighted (wrong product runs, underproduction by SKU).

### 12-6-schedule-attainment-ui-section-UNIT-001: Section renders with correct heading when data exists
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns data with has_data=true and two workcenters ("Roasting", "Grinding") each with products and attainment percentages
- When: ScheduleAttainment component renders
- Then: A section element with aria-label="Schedule attainment" is present, containing an h2 heading with text "Schedule Attainment"
- Data: Mock hook return with 2 workcenters, 2-3 products each, overall_attainment_pct per workcenter

### 12-6-schedule-attainment-ui-section-UNIT-002: Each workcenter renders as a Card with mode retrospective
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns data with 3 workcenters
- When: ScheduleAttainment component renders
- Then: Three Card components render, each with mode="retrospective", each showing the workcenter name in the CardHeader
- Data: Mock data with workcenters "Roasting", "Grinding", "Packaging"

### 12-6-schedule-attainment-ui-section-UNIT-003: Per-product rows show product name, scheduled qty, actual qty, attainment %
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns a workcenter with products [{product_name: "Brazilian", scheduled_quantity: 1000, actual_quantity: 950, attainment_pct: 95.0}, {product_name: "Colombian", scheduled_quantity: 500, actual_quantity: 400, attainment_pct: 80.0}]
- When: ScheduleAttainment component renders
- Then: Product rows display "Brazilian", "1,000", "950", "95.0%" and "Colombian", "500", "400", "80.0%" with correct values visible
- Data: Workcenter with 2 products at different attainment levels

### 12-6-schedule-attainment-ui-section-UNIT-004: Overall workcenter attainment percentage is displayed
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns a workcenter with overall_attainment_pct of 87.5
- When: ScheduleAttainment component renders
- Then: The workcenter card header or summary area shows "87.5%" as the overall attainment
- Data: Single workcenter with overall_attainment_pct: 87.5

### 12-6-schedule-attainment-ui-section-UNIT-005: Attainment percentage color-coded green for >=95%
- Priority: P1
- Type: unit
- Given: A product has attainment_pct of 98.0
- When: ScheduleAttainment renders the product row
- Then: The attainment percentage text has success-green color class (e.g., text-success-green-dark or text-success-green)
- Data: Product with attainment_pct: 98.0

### 12-6-schedule-attainment-ui-section-UNIT-006: Attainment percentage color-coded amber for 80-94%
- Priority: P1
- Type: unit
- Given: A product has attainment_pct of 88.0
- When: ScheduleAttainment renders the product row
- Then: The attainment percentage text has warning-amber color class (e.g., text-warning-amber-dark or text-warning-amber)
- Data: Product with attainment_pct: 88.0

### 12-6-schedule-attainment-ui-section-UNIT-007: Attainment percentage color-coded red for <80%
- Priority: P1
- Type: unit
- Given: A product has attainment_pct of 72.0
- When: ScheduleAttainment renders the product row
- Then: The attainment percentage text has safety-red color class (e.g., text-safety-red)
- Data: Product with attainment_pct: 72.0

### 12-6-schedule-attainment-ui-section-UNIT-008: Variance callouts rendered within workcenter cards
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns a workcenter with variances array containing 2 callouts (one swap, one underproduction)
- When: ScheduleAttainment renders
- Then: Both variance callout messages are visible within the workcenter card, rendered via ProductVarianceCallout components
- Data: Workcenter with variances: [{variance_type: "product_swap", message: "Roaster 1 ran Colombian instead of scheduled Brazilian"}, {variance_type: "underproduction", message: "Grinder 2 produced 200 fewer units of Ethiopian"}]

### 12-6-schedule-attainment-ui-section-UNIT-009: Loading skeleton displayed while data is fetching
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns isLoading=true, data=null
- When: ScheduleAttainment component renders
- Then: Animated skeleton placeholders with animate-pulse class are visible, and no workcenter cards or data rows are displayed
- Data: Mock hook returning {isLoading: true, data: null, error: null}

### 12-6-schedule-attainment-ui-section-UNIT-010: Error state displays error message and retry button
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns error="Failed to load schedule attainment data", data=null
- When: ScheduleAttainment component renders
- Then: The error message text is visible, and a "Try Again" or "Retry" button is present that calls refetch when clicked
- Data: Mock hook returning {isLoading: false, data: null, error: "Failed to load schedule attainment data"}

### 12-6-schedule-attainment-ui-section-UNIT-011: Retry button triggers refetch on click
- Priority: P1
- Type: unit
- Given: ScheduleAttainment is in error state with a visible retry button
- When: User clicks the retry button
- Then: The refetch function from useScheduleAttainment is called exactly once
- Data: Mock hook in error state with mockRefetch spy

### 12-6-schedule-attainment-ui-section-INT-001: ScheduleAttainment positioned between WorkcenterScorecard and action items in morning report
- Priority: P0
- Type: integration
- Given: The morning report page renders with all sections (SafetyAlerts, MorningSummary, WorkcenterScorecard, ScheduleAttainment, InsightEvidenceCardList)
- When: The page loads
- Then: The ScheduleAttainment section (identified by aria-label="Schedule attainment") appears in the DOM after WorkcenterScorecard and before the action items section (aria-label="Action items with evidence"), verified via compareDocumentPosition
- Data: All mocked hooks returning valid data for each section

### 12-6-schedule-attainment-ui-section-UNIT-012: Workcenter with empty products array renders only variance callouts
- Priority: P1
- Type: unit
- Given: useScheduleAttainment returns a workcenter with products=[] and variances=[{variance_type: "unscheduled", message: "Unscheduled production on Roaster 1"}]
- When: ScheduleAttainment renders
- Then: No product rows are shown for that workcenter, but the variance callout is still rendered
- Data: Workcenter with empty products array and one variance callout

### 12-6-schedule-attainment-ui-section-UNIT-013: Section renders with className prop applied
- Priority: P2
- Type: unit
- Given: ScheduleAttainment component receives className="custom-class"
- When: Component renders
- Then: The custom-class is applied to the section's root element via cn() utility
- Data: className="custom-class"


## AC2: Given a product was swapped (different product produced than scheduled), When the attainment section renders, Then the swap is highlighted in amber/orange with text like "Ran Colombian instead of scheduled Brazilian".

### 12-6-schedule-attainment-ui-section-UNIT-014: Product swap callout renders with amber/orange styling
- Priority: P0
- Type: unit
- Given: A VarianceCallout with variance_type="product_swap" and message="Roaster 1 ran Colombian instead of scheduled Brazilian"
- When: ProductVarianceCallout component renders
- Then: The callout has amber/orange background (bg-warning-amber class pattern), amber left border (border-l-4 border-warning-amber), and the message text is visible
- Data: {variance_type: "product_swap", asset_name: "Roaster 1", message: "Roaster 1 ran Colombian instead of scheduled Brazilian"}

### 12-6-schedule-attainment-ui-section-UNIT-015: Product swap callout uses swap icon indicator
- Priority: P1
- Type: unit
- Given: A VarianceCallout with variance_type="product_swap"
- When: ProductVarianceCallout component renders
- Then: An ArrowRightLeft icon (or equivalent swap indicator) is rendered alongside the message
- Data: Swap-type variance callout

### 12-6-schedule-attainment-ui-section-UNIT-016: Underproduction callout renders with appropriate warning styling
- Priority: P0
- Type: unit
- Given: A VarianceCallout with variance_type="underproduction" and message="Grinder 2 produced 200 fewer units of Ethiopian"
- When: ProductVarianceCallout component renders
- Then: The callout renders with amber warning styling (similar to swap but with AlertTriangle icon) and the underproduction message text is visible
- Data: {variance_type: "underproduction", asset_name: "Grinder 2", message: "Grinder 2 produced 200 fewer units of Ethiopian"}

### 12-6-schedule-attainment-ui-section-UNIT-017: Unscheduled production callout renders with info-blue styling
- Priority: P1
- Type: unit
- Given: A VarianceCallout with variance_type="unscheduled" and message="Roaster 2 ran Decaf — not on schedule"
- When: ProductVarianceCallout component renders
- Then: The callout renders with info-blue background (bg-info-blue class pattern), info-blue text coloring, and the unscheduled message text is visible
- Data: {variance_type: "unscheduled", asset_name: "Roaster 2", message: "Roaster 2 ran Decaf — not on schedule"}

### 12-6-schedule-attainment-ui-section-UNIT-018: Multiple variance callouts render in order within a workcenter
- Priority: P1
- Type: unit
- Given: A workcenter has 3 variance callouts: one swap, one underproduction, one unscheduled
- When: ScheduleAttainment renders the workcenter card
- Then: All three callouts are visible in the order returned by the API, each with its appropriate styling
- Data: Workcenter with variances array of length 3 (mixed types)

### 12-6-schedule-attainment-ui-section-UNIT-019: Swap callout message text contains swap description
- Priority: P0
- Type: unit
- Given: ProductVarianceCallout receives message="Ran Colombian instead of scheduled Brazilian"
- When: Component renders
- Then: The exact text "Ran Colombian instead of scheduled Brazilian" is visible in the document
- Data: Swap callout with descriptive message


## AC3: Given no schedule data exists for the date, When the attainment section renders, Then a prompt appears: "No schedule uploaded for this date. Upload schedule ->" with a link to /settings/schedule-upload.

### 12-6-schedule-attainment-ui-section-UNIT-020: Empty state renders when has_data is false
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns data with has_data=false and message="No schedule data for this date"
- When: ScheduleAttainment component renders
- Then: A prompt is displayed with text containing "No schedule uploaded for this date" (or the API message), and no workcenter cards are shown
- Data: Mock hook returning {data: {has_data: false, message: "No schedule data for this date", workcenters: [], date: "2026-02-10"}}

### 12-6-schedule-attainment-ui-section-UNIT-021: Empty state contains link to schedule upload page
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns has_data=false
- When: ScheduleAttainment renders the empty state
- Then: A link with text "Upload schedule" (or similar with arrow) is present, and its href points to "/settings/schedule-upload"
- Data: Mock hook returning empty state

### 12-6-schedule-attainment-ui-section-UNIT-022: Empty state link uses Next.js Link for client-side navigation
- Priority: P1
- Type: unit
- Given: ScheduleAttainment renders the empty state with upload link
- When: The link element is inspected
- Then: The link is rendered as an anchor tag with href="/settings/schedule-upload" (Next.js Link renders as <a>)
- Data: Empty state rendered

### 12-6-schedule-attainment-ui-section-UNIT-023: Section heading still displays in empty state
- Priority: P1
- Type: unit
- Given: useScheduleAttainment returns has_data=false
- When: ScheduleAttainment renders
- Then: The "Schedule Attainment" section heading is still visible above the empty state prompt
- Data: Mock hook returning empty state

### 12-6-schedule-attainment-ui-section-UNIT-024: No bar chart rendered in empty state
- Priority: P1
- Type: unit
- Given: useScheduleAttainment returns has_data=false
- When: ScheduleAttainment renders
- Then: No Recharts BarChart or ProductMixChart component is rendered
- Data: Mock hook returning empty state


## AC4: Given the overall product mix is shown, When the user views the section, Then a simple bar comparison shows planned vs. actual mix percentages using Recharts BarChart.

### 12-6-schedule-attainment-ui-section-UNIT-025: Product mix bar chart renders when data exists
- Priority: P0
- Type: unit
- Given: useScheduleAttainment returns data with multiple products across workcenters
- When: ScheduleAttainment component renders
- Then: A ProductMixChart (Recharts BarChart) is rendered showing planned vs. actual mix percentages as grouped bars
- Data: 2 workcenters with 3 products total: Brazilian (sched: 1000, actual: 950), Colombian (sched: 500, actual: 600), Ethiopian (sched: 300, actual: 250)

### 12-6-schedule-attainment-ui-section-UNIT-026: Bar chart shows correct planned vs actual mix percentages
- Priority: P0
- Type: unit
- Given: ProductMixChart receives products with scheduled_quantity totals summing to 1800 and actual_quantity totals summing to 1800, where Brazilian is 1000/950, Colombian 500/600, Ethiopian 300/250
- When: Chart computes mix percentages
- Then: Planned percentages are approximately 55.6%, 27.8%, 16.7% and actual percentages are approximately 52.8%, 33.3%, 13.9% respectively
- Data: Products array with known quantities for percentage verification

### 12-6-schedule-attainment-ui-section-UNIT-027: Bar chart uses ResponsiveContainer for responsive sizing
- Priority: P1
- Type: unit
- Given: ProductMixChart component renders
- When: The chart container is inspected
- Then: The chart is wrapped in a ResponsiveContainer with width="100%" and height={250} (or similar responsive wrapper)
- Data: Any valid products data

### 12-6-schedule-attainment-ui-section-UNIT-028: Bar chart has legend distinguishing planned vs actual
- Priority: P1
- Type: unit
- Given: ProductMixChart renders with valid data
- When: The chart is fully rendered
- Then: A Legend component is present showing labels for "Planned" (or "Planned %") and "Actual" (or "Actual %") with distinct colors
- Data: Any valid products data

### 12-6-schedule-attainment-ui-section-UNIT-029: Bar chart handles empty products array gracefully
- Priority: P1
- Type: unit
- Given: ProductMixChart receives an empty products array
- When: Component renders
- Then: No error is thrown, and either an empty chart or a no-data message is displayed
- Data: products: []

### 12-6-schedule-attainment-ui-section-UNIT-030: Bar chart uses correct color tokens for planned and actual bars
- Priority: P2
- Type: unit
- Given: ProductMixChart renders with valid data
- When: The Bar elements are inspected
- Then: Planned bars use info-blue color (hsl(var(--info-blue)) or equivalent) and actual bars use success-green color (hsl(var(--success-green)) or equivalent)
- Data: Any valid products data

### 12-6-schedule-attainment-ui-section-UNIT-031: Bar chart renders below workcenter cards
- Priority: P1
- Type: unit
- Given: ScheduleAttainment renders with valid data including workcenters and products
- When: The full section is rendered
- Then: The ProductMixChart appears in the DOM after all workcenter cards (verified via document order)
- Data: 2 workcenters with products


## Hook: useScheduleAttainment data fetching and authentication

### 12-6-schedule-attainment-ui-section-UNIT-032: Hook fetches with Bearer token authentication
- Priority: P0
- Type: unit
- Given: Supabase auth returns a valid session with access_token="mock-token-123"
- When: useScheduleAttainment hook mounts and fetches data
- Then: fetch is called with Authorization header "Bearer mock-token-123"
- Data: Mock session with access_token, mock fetch response

### 12-6-schedule-attainment-ui-section-UNIT-033: Hook calls correct API endpoint with date parameter
- Priority: P0
- Type: unit
- Given: useScheduleAttainment is called with date="2026-02-10"
- When: The hook fetches data
- Then: fetch is called with URL matching /api/v1/production/schedule-attainment?date=2026-02-10
- Data: Date parameter "2026-02-10"

### 12-6-schedule-attainment-ui-section-UNIT-034: Hook defaults to T-1 date when no date provided
- Priority: P0
- Type: unit
- Given: useScheduleAttainment is called without a date parameter
- When: The hook fetches data
- Then: fetch is called with a date query parameter equal to yesterday's date (getYesterday())
- Data: No date param, verify URL contains yesterday's ISO date

### 12-6-schedule-attainment-ui-section-UNIT-035: Hook returns isLoading=true initially then false after fetch completes
- Priority: P0
- Type: unit
- Given: useScheduleAttainment hook is rendered
- When: The hook initializes and then the fetch resolves
- Then: isLoading is initially true, then transitions to false after data loads
- Data: Mock fetch that resolves with valid data

### 12-6-schedule-attainment-ui-section-UNIT-036: Hook returns parsed data on successful fetch
- Priority: P0
- Type: unit
- Given: API returns a valid ScheduleAttainmentResponse with 2 workcenters
- When: useScheduleAttainment hook completes fetching
- Then: data matches the API response shape with workcenters, date, has_data=true
- Data: Full mock response with workcenters, products, variances

### 12-6-schedule-attainment-ui-section-UNIT-037: Hook sets error on network failure
- Priority: P0
- Type: unit
- Given: fetch rejects with a network error (TypeError: Failed to fetch)
- When: useScheduleAttainment hook attempts to fetch
- Then: error is set to a descriptive error message, data is null, isLoading is false
- Data: Mock fetch that rejects

### 12-6-schedule-attainment-ui-section-UNIT-038: Hook sets error on 401 unauthorized response
- Priority: P1
- Type: unit
- Given: API returns 401 status
- When: useScheduleAttainment hook processes the response
- Then: error is set to an authentication-related error message, data is null
- Data: Mock fetch returning {ok: false, status: 401}

### 12-6-schedule-attainment-ui-section-UNIT-039: Hook sets error on 500 server error
- Priority: P1
- Type: unit
- Given: API returns 500 status
- When: useScheduleAttainment hook processes the response
- Then: error is set to a server error message, data is null
- Data: Mock fetch returning {ok: false, status: 500}

### 12-6-schedule-attainment-ui-section-UNIT-040: Hook handles null session gracefully
- Priority: P0
- Type: unit
- Given: Supabase auth getSession returns null session (user not logged in)
- When: useScheduleAttainment hook attempts to fetch
- Then: error is set to an auth-related message, fetch is NOT called
- Data: Mock getSession returning {data: {session: null}}

### 12-6-schedule-attainment-ui-section-UNIT-041: Hook refetch function triggers a new fetch
- Priority: P1
- Type: unit
- Given: useScheduleAttainment hook has completed initial fetch
- When: refetch() is called
- Then: fetch is called again with the same URL and auth headers
- Data: Mock fetch response, call refetch after initial load

### 12-6-schedule-attainment-ui-section-UNIT-042: Hook does not update state after unmount
- Priority: P1
- Type: unit
- Given: useScheduleAttainment hook is rendered and a slow fetch is in progress
- When: The component unmounts before the fetch resolves
- Then: No state update occurs (no "cannot update unmounted component" warning), verified via mountedRef pattern
- Data: Mock fetch with delayed resolution, unmount before resolution

### 12-6-schedule-attainment-ui-section-UNIT-043: Hook returns has_data false when API indicates no schedule
- Priority: P0
- Type: unit
- Given: API returns {has_data: false, workcenters: [], date: "2026-02-10", message: "No schedule data for this date"}
- When: useScheduleAttainment hook completes fetching
- Then: data.has_data is false, data.workcenters is empty, data.message contains the no-schedule text
- Data: API response with has_data=false


edge_cases:
  - Single product in a single workcenter (minimal data scenario)
  - Workcenter with 0% attainment (all products missed entirely)
  - Workcenter with >100% attainment (overproduction exceeds scheduled quantity)
  - Product with scheduled_quantity of 0 (division by zero guard in attainment % calculation)
  - Very long product names that may need truncation in the chart XAxis labels
  - Multiple workcenters where one has data and another has only variance callouts (no products)
  - API returns 404 status (should map to empty/no-data state, not generic error)
  - Extremely large quantity numbers (e.g., 1,000,000 units) formatted with toLocaleString
  - Attainment at exactly 95% boundary (verify green threshold, not amber)
  - Attainment at exactly 80% or 85% boundary (verify amber threshold, not red)
  - Dark mode rendering — amber/orange callouts use dark variant color tokens correctly
  - Date parameter at timezone boundary (e.g., UTC midnight vs. local time)
  - Workcenter with no variances at all (variances array is empty — no callout section rendered)
  - Single workcenter with many products (>10) — verify layout doesn't break

error_scenarios:
  - Network timeout during fetch — hook should set error state with descriptive message
  - Supabase session expired mid-request — 401 response handled with auth error message
  - API returns malformed JSON — hook should catch parse error gracefully
  - API returns 500 Internal Server Error — error state with retry button functional
  - API returns 404 Not Found — should map to empty state or specific error
  - Recharts fails to render (SSR context) — 'use client' directive guards against this
  - API returns unexpected response shape (missing fields) — graceful degradation without crash
  - Bearer token is empty string — should treat as auth error, not send empty auth header
  - Component renders while hook is still loading then data arrives — no flash of content

test_file_mapping:
  - 12-6-schedule-attainment-ui-section-UNIT-001 to UNIT-013: apps/web/src/components/production/__tests__/ScheduleAttainment.test.tsx
  - 12-6-schedule-attainment-ui-section-UNIT-014 to UNIT-019: apps/web/src/components/production/__tests__/ProductVarianceCallout.test.tsx
  - 12-6-schedule-attainment-ui-section-UNIT-020 to UNIT-024: apps/web/src/components/production/__tests__/ScheduleAttainment.test.tsx (empty state describe block)
  - 12-6-schedule-attainment-ui-section-UNIT-025 to UNIT-031: apps/web/src/components/production/__tests__/ProductMixChart.test.tsx
  - 12-6-schedule-attainment-ui-section-UNIT-032 to UNIT-043: apps/web/src/hooks/__tests__/useScheduleAttainment.test.ts
  - 12-6-schedule-attainment-ui-section-INT-001: apps/web/src/app/(main)/morning-report/__tests__/page.test.tsx

TEST SPEC END
