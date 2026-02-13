TEST SPEC START
story_id: 14-5-downtime-pareto-chart-on-action-cards
generated: 2026-02-11

test_specifications:

## AC1: Given an action item is an OEE-miss or downtime-related item, When the action card renders and downtime Pareto data is available, Then a horizontal bar chart shows the top 3-5 reason codes sorted by duration, And each bar shows: reason code name, duration in minutes, percentage of total, And planned vs. unplanned downtime is visually distinguished (e.g., hatched vs. solid bars).

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-001: Hook returns loading state on initial mount
- Priority: P0
- Type: unit
- Given: The `useDowntimePareto` hook is called with valid `assetId` and `reportDate` and `enabled=true`
- When: The hook mounts and the fetch has not yet resolved
- Then: `isLoading` is `true`, `data` is `null`, and `error` is `null`
- Data: assetId = 'asset-001', reportDate = '2026-01-05'

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-002: Hook fetches Pareto data with correct URL and auth header
- Priority: P0
- Type: unit
- Given: Supabase session returns `access_token: 'mock-token-abc'`
- When: The `useDowntimePareto` hook triggers its fetch with `assetId='asset-001'` and `reportDate='2026-01-05'`
- Then: `fetch` is called with URL `{API_BASE_URL}/api/v1/downtime/pareto?asset_id=asset-001&start_date=2026-01-05` and headers include `Authorization: Bearer mock-token-abc` and `Content-Type: application/json`
- Data: Mock Supabase session with access_token, NEXT_PUBLIC_API_URL env var

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-003: Hook sets data on successful API response
- Priority: P0
- Type: unit
- Given: The API returns a valid `ParetoResponse` with 4 items sorted by `total_minutes` descending
- When: The fetch resolves successfully
- Then: `data` contains the parsed response with all 4 `ParetoItem` entries, `isLoading` is `false`, `error` is `null`
- Data: ParetoResponse with items: [{ reason_code: 'Mechanical', total_minutes: 180, percentage: 35.5, is_planned: false }, { reason_code: 'Changeover', total_minutes: 120, percentage: 23.6, is_planned: false }, { reason_code: 'Planned Maintenance', total_minutes: 90, percentage: 17.7, is_planned: true }, { reason_code: 'Material Shortage', total_minutes: 60, percentage: 11.8, is_planned: false }]

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-004: Hook handles network error gracefully
- Priority: P0
- Type: unit
- Given: The `useDowntimePareto` hook is called with valid params
- When: The fetch rejects with a network error
- Then: `error` is set to a descriptive error message, `data` is `null`, `isLoading` is `false`
- Data: `fetch` rejects with `Error('Network request failed')`

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-005: Hook handles 401 auth error
- Priority: P1
- Type: unit
- Given: The Supabase session is valid but the API returns HTTP 401
- When: The fetch resolves with status 401
- Then: `error` is set to an authentication error message, `data` is `null`, `isLoading` is `false`
- Data: Mock fetch returns `{ ok: false, status: 401 }`

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-006: Hook handles empty items array
- Priority: P1
- Type: unit
- Given: The API returns a valid `ParetoResponse` with `items: []` and `total_downtime_minutes: 0`
- When: The fetch resolves successfully
- Then: `data` is set with the empty response, `data.items` has length 0, `isLoading` is `false`, `error` is `null`
- Data: ParetoResponse with items: [], total_downtime_minutes: 0

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-007: Hook does not fetch when enabled is false
- Priority: P0
- Type: unit
- Given: The `useDowntimePareto` hook is called with `enabled=false`
- When: The hook mounts
- Then: `fetch` is never called, `isLoading` is `false`, `data` is `null`
- Data: assetId = 'asset-001', reportDate = '2026-01-05', enabled = false

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-008: Hook refetch triggers a new API call
- Priority: P1
- Type: unit
- Given: The hook has completed its initial fetch and returned data
- When: `refetch()` is called
- Then: `isLoading` momentarily becomes `true`, a new fetch is made to the same URL, and `data` is updated with the new response
- Data: Two sequential mock responses with different `last_updated` values

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-009: Hook prevents state updates after unmount
- Priority: P1
- Type: unit
- Given: The hook is called and a fetch is in progress
- When: The component unmounts before the fetch resolves
- Then: No state update occurs (no React warnings), the mountedRef pattern prevents `setState` calls
- Data: Slow-resolving fetch mock with component unmount before resolution

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-010: Hook handles missing Supabase session
- Priority: P1
- Type: unit
- Given: Supabase `getSession` returns `{ data: { session: null } }`
- When: The hook attempts to fetch
- Then: `error` is set to an authentication error, `fetch` is not called with a Bearer token, `isLoading` is `false`
- Data: Mock getSession returning null session

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-011: Component renders horizontal bars for 3-5 reason codes sorted by duration
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with 4 items sorted by `total_minutes` descending
- When: The component renders
- Then: A Recharts `BarChart` with `layout="vertical"` renders inside a `ResponsiveContainer`, and 4 bars are displayed corresponding to the 4 reason codes
- Data: 4 ParetoItems: Mechanical (180min, 35.5%), Changeover (120min, 23.6%), Planned Maintenance (90min, 17.7%), Material Shortage (60min, 11.8%)

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-012: Each bar shows reason code name, duration in minutes, and percentage of total
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with items containing reason_code, total_minutes, and percentage
- When: The component renders
- Then: Each bar's label area contains the reason code name, duration formatted as `{N}min`, and percentage formatted as `({N}%)`
- Data: ParetoItem with reason_code='Mechanical', total_minutes=180, percentage=35.5 → label shows "Mechanical", "180min", "(35.5%)"

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-013: Planned downtime bars are visually distinguished with hatched pattern
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives data with items where `is_planned=true` (e.g., 'Planned Maintenance')
- When: The component renders
- Then: Bars for planned items use a hatched/striped SVG pattern fill (identifiable via `data-testid` or fill URL referencing a pattern definition), while unplanned items use solid fill
- Data: Mix of planned (is_planned=true) and unplanned (is_planned=false) ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-014: Unplanned downtime bars render with solid fill
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives data with unplanned items (`is_planned=false`)
- When: The component renders
- Then: Unplanned bars use a solid color fill (not hatched pattern), using the Industrial Clarity color palette
- Data: ParetoItems with is_planned=false

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-015: Component limits display to top 5 reason codes when more are provided
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with 8 items
- When: The component renders
- Then: Only the top 5 items (by total_minutes descending) are displayed as bars
- Data: 8 ParetoItems with varying total_minutes

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-016: Component returns null when data is null
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives `data` as `null`
- When: The component renders
- Then: Nothing is rendered (returns null), no chart elements appear in the DOM
- Data: data = null

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-017: Component returns null when items array is empty
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with `items: []`
- When: The component renders
- Then: Nothing is rendered (returns null), no chart or empty state message appears
- Data: ParetoResponse with items: []

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-018: Component truncates long reason code names
- Priority: P2
- Type: unit
- Given: `DowntimePareto` receives items with a reason_code exceeding 15 characters (e.g., 'Electrical System Overload')
- When: The component renders
- Then: The displayed reason code name is truncated to 15 characters (e.g., 'Electrical Syst…')
- Data: ParetoItem with reason_code='Electrical System Overload' (26 chars)

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-019: Component uses compact height appropriate for inline rendering
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives data with 3-5 items
- When: The component renders
- Then: The `ResponsiveContainer` height is between 100-150px (compact, sparkline-sized), appropriate for embedding inside an evidence card without its own Card wrapper
- Data: 3-5 ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-020: Component supports dark mode via Tailwind dark: variants
- Priority: P2
- Type: unit
- Given: `DowntimePareto` renders in a dark mode context
- When: The component renders
- Then: Dark mode CSS classes (e.g., `dark:` prefixed Tailwind classes) are applied to text labels, background, and legend elements
- Data: Standard ParetoResponse data

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-021: Planned vs unplanned legend is rendered
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives data containing both planned and unplanned items
- When: The component renders
- Then: A compact inline legend is displayed showing the solid fill = unplanned and hatched fill = planned distinction
- Data: Mix of planned and unplanned ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-INT-001: EvidenceSection renders Pareto chart for OEE evidence with available data
- Priority: P0
- Type: integration
- Given: `EvidenceSection` receives evidence with `type='oee_deviation'`, `assetId='asset-001'`, `reportDate='2026-01-05'`, and `useDowntimePareto` returns Pareto data with 4 items
- When: The evidence section is expanded
- Then: The `DowntimePareto` chart component is rendered below the OEE evidence content, showing a "Downtime Breakdown" section header and the horizontal bar chart
- Data: OEEEvidence with targetOEE=85, actualOEE=72, deviation=13; ParetoResponse with 4 items

### 14-5-downtime-pareto-chart-on-action-cards-INT-002: InsightEvidenceCard passes assetId and reportDate to EvidenceSection
- Priority: P0
- Type: integration
- Given: An `InsightEvidenceCard` renders with an `ActionItem` that has `asset.id='asset-001'` and `timestamp='2026-01-05T14:30:00Z'`
- When: The card renders
- Then: `EvidenceSection` receives `assetId='asset-001'` and `reportDate='2026-01-05'` as props
- Data: ActionItem with asset.id and timestamp fields populated

### 14-5-downtime-pareto-chart-on-action-cards-INT-003: Pareto hook receives correct parameters from EvidenceSection
- Priority: P0
- Type: integration
- Given: `EvidenceSection` has `assetId='asset-001'`, `reportDate='2026-01-05'`, and evidence type is `'oee_deviation'`
- When: The component mounts
- Then: `useDowntimePareto` is called with `{ assetId: 'asset-001', reportDate: '2026-01-05', enabled: true }`
- Data: OEE evidence with asset and date props

## AC2: Given an action item is a safety-only or financial-only item (no downtime component), When the card renders, Then no Pareto chart is shown.

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-022: No Pareto chart rendered for safety evidence type
- Priority: P0
- Type: unit
- Given: `EvidenceSection` receives evidence with `type='safety_event'`, with `assetId` and `reportDate` props provided
- When: The component renders and the evidence section is expanded
- Then: No `DowntimePareto` component is rendered, no "Downtime Breakdown" section header appears, and `useDowntimePareto` is called with `enabled=false`
- Data: SafetyEvidence with eventId, detectedAt, reasonCode, severity, assetName fields

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-023: No Pareto chart rendered for financial evidence type
- Priority: P0
- Type: unit
- Given: `EvidenceSection` receives evidence with `type='financial_loss'`, with `assetId` and `reportDate` props provided
- When: The component renders and the evidence section is expanded
- Then: No `DowntimePareto` component is rendered, no "Downtime Breakdown" section header appears, and `useDowntimePareto` is called with `enabled=false`
- Data: FinancialEvidence with downtimeCost, wasteCost, totalLoss, breakdown fields

### 14-5-downtime-pareto-chart-on-action-cards-INT-004: Hook not enabled when assetId is missing
- Priority: P1
- Type: integration
- Given: `EvidenceSection` receives OEE evidence but `assetId` prop is `undefined`
- When: The component renders
- Then: `useDowntimePareto` is called with `enabled=false`, no API call is made, no Pareto chart is rendered
- Data: OEE evidence without assetId prop

### 14-5-downtime-pareto-chart-on-action-cards-INT-005: Hook not enabled when reportDate is missing
- Priority: P1
- Type: integration
- Given: `EvidenceSection` receives OEE evidence but `reportDate` prop is `undefined`
- When: The component renders
- Then: `useDowntimePareto` is called with `enabled=false`, no API call is made, no Pareto chart is rendered
- Data: OEE evidence without reportDate prop

## AC3: Given the Pareto data is loading, When the card renders, Then a skeleton loader placeholder is shown where the chart would be.

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-024: Skeleton loader renders with animate-pulse during loading
- Priority: P0
- Type: unit
- Given: `DowntimeParetoSkeleton` is rendered
- When: The component mounts
- Then: A container with `animate-pulse` class is rendered containing 3-4 horizontal bar placeholders at staggered widths, using `bg-industrial-200 dark:bg-industrial-700` classes
- Data: No data props required for skeleton

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-025: Skeleton loader matches chart dimensions
- Priority: P1
- Type: unit
- Given: `DowntimeParetoSkeleton` is rendered
- When: The component mounts
- Then: The skeleton placeholders are horizontal bars at varying widths (e.g., w-full, w-3/4, w-1/2, w-1/3) matching the expected chart layout, at approximately 120-150px total height
- Data: No data props required

### 14-5-downtime-pareto-chart-on-action-cards-INT-006: EvidenceSection shows skeleton while Pareto data is loading
- Priority: P0
- Type: integration
- Given: `EvidenceSection` receives OEE evidence with `assetId` and `reportDate`, and `useDowntimePareto` returns `{ isLoading: true, data: null, error: null }`
- When: The evidence section is expanded
- Then: `DowntimeParetoSkeleton` is rendered in place of the chart, below the OEE evidence content
- Data: OEE evidence; hook in loading state

### 14-5-downtime-pareto-chart-on-action-cards-INT-007: Skeleton transitions to chart when data loads
- Priority: P1
- Type: integration
- Given: `EvidenceSection` initially shows the skeleton while `useDowntimePareto` is loading
- When: The hook resolves with Pareto data
- Then: The skeleton is replaced by the `DowntimePareto` chart component showing the loaded data
- Data: OEE evidence; hook transitions from loading to loaded with 4 ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-INT-008: No chart or skeleton shown when hook returns error
- Priority: P1
- Type: integration
- Given: `EvidenceSection` receives OEE evidence and `useDowntimePareto` returns `{ isLoading: false, data: null, error: 'Network error' }`
- When: The evidence section is expanded
- Then: Neither `DowntimePareto` chart nor `DowntimeParetoSkeleton` is rendered; the OEE evidence content still displays normally without a Pareto section
- Data: OEE evidence; hook in error state

edge_cases:
  - Single reason code: ParetoResponse with only 1 item should still render a single horizontal bar correctly
  - All planned downtime: Every item has is_planned=true — all bars should show hatched pattern, legend should still display
  - All unplanned downtime: Every item has is_planned=false — all bars should show solid fill
  - Reason code with 0 minutes: A ParetoItem with total_minutes=0 and percentage=0 should render a zero-width bar or be excluded
  - Very large duration values: ParetoItem with total_minutes=9999 should not break chart layout
  - 100% single reason code: One item with percentage=100.0 and all others at 0%
  - Fallback planned detection: When is_planned field is absent or false for all items, check reason_code === 'Planned Maintenance' as fallback heuristic
  - Rapid expand/collapse of evidence section: Hook should not make redundant API calls when cached data exists
  - Multiple OEE cards rendering simultaneously: Each card's hook makes its own API call with its own assetId/date combination

error_scenarios:
  - API returns HTTP 500 server error: Hook sets error state, no chart rendered
  - API returns HTTP 401 unauthorized: Hook sets auth error, no chart rendered
  - API returns malformed JSON: Hook catches parse error, sets error state
  - Network timeout: Hook catches timeout error, sets error state
  - Supabase session expired: getSession returns null, hook sets auth error without calling fetch
  - API returns 200 but with unexpected schema: Hook handles missing fields gracefully
  - Component unmounts during active fetch: No React state update warnings (mountedRef pattern)

test_file_mapping:
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-001 to UNIT-010: apps/web/src/hooks/__tests__/useDowntimePareto.test.ts
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-011 to UNIT-021: apps/web/src/components/action-engine/__tests__/DowntimePareto.test.tsx
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-022 to UNIT-023: apps/web/src/components/action-engine/__tests__/EvidenceSection.pareto.test.tsx
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-024 to UNIT-025: apps/web/src/components/action-engine/__tests__/DowntimePareto.test.tsx
  - 14-5-downtime-pareto-chart-on-action-cards-INT-001 to INT-008: apps/web/src/components/action-engine/__tests__/EvidenceSection.pareto.test.tsx

TEST SPEC END
