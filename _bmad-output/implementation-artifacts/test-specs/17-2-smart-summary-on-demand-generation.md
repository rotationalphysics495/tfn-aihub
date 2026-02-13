TEST SPEC START
story_id: 17-2-smart-summary-on-demand-generation
generated: 2026-02-12

test_specifications:

## AC1: Given the user navigates to a historical date that has production data but no saved smart summary, When the summary section loads, Then a prompt is shown: "No summary exists for this date. Generate one?" and a "Generate Summary" button is displayed.

### 17-2-smart-summary-on-demand-generation-UNIT-001: Hook returns canGenerate=true and hasSummary=false on 404 with autoGenerate=false
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is called with `{ autoGenerate: false, reportDate: '2026-01-15' }` and the GET `/api/summaries/smart/2026-01-15` returns 404
- When: The hook completes its initial fetch
- Then: `hasSummary` is `false`, `canGenerate` is `true`, `isLoading` is `false`, `isGenerating` is `false`, `error` is `null`, and `data` is `null`
- Data: Mock fetch returning `{ status: 404, ok: false }`, mock Supabase session with valid access_token

### 17-2-smart-summary-on-demand-generation-UNIT-002: Hook does NOT auto-trigger POST generation when autoGenerate=false and GET returns 404
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is called with `{ autoGenerate: false, reportDate: '2026-01-15' }` and GET returns 404
- When: The hook completes its initial fetch
- Then: `fetch` is called exactly once (the GET request only), and `POST /api/summaries/generate` is never called
- Data: Mock fetch for GET returning 404, mock Supabase session

### 17-2-smart-summary-on-demand-generation-UNIT-003: Hook preserves existing auto-generation behavior when autoGenerate is not set (default true)
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is called with `{ reportDate: '2026-01-15' }` (no `autoGenerate` option, defaulting to `true`) and GET returns 404
- When: The hook completes its initial fetch
- Then: `fetch` is called twice — first GET (404), then POST `/api/summaries/generate` with `{ target_date: '2026-01-15', regenerate: false }` — and the resulting summary data is set in state
- Data: Mock fetch: GET returns 404, POST returns 200 with SmartSummaryData fixture

### 17-2-smart-summary-on-demand-generation-COMP-001: Component shows generation prompt when canGenerate=true and no summary exists
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` is rendered with `reportDate="2026-01-15"` and `useSmartSummary` returns `{ hasSummary: false, canGenerate: true, isLoading: false, isGenerating: false, error: null, data: null }`
- When: The component renders
- Then: A text element containing "No summary exists for this date" is visible, and a button with text "Generate Summary" is displayed
- Data: Mocked `useSmartSummary` and `useDailyActions` hooks

### 17-2-smart-summary-on-demand-generation-COMP-002: Component does NOT show generation prompt for default (yesterday) date
- Priority: P1
- Type: unit (component)
- Given: `MorningSummarySection` is rendered without `reportDate` prop (defaults to yesterday/T-1 behavior)
- When: The component renders and the hook is called
- Then: `useSmartSummary` is called with `autoGenerate` NOT set to `false` (i.e., auto-generation is enabled), so no "Generate Summary" button appears — the hook auto-generates on 404 as before
- Data: Mocked hooks where `useSmartSummary` returns loading or has a summary

### 17-2-smart-summary-on-demand-generation-COMP-003: Component passes autoGenerate=false when reportDate prop is provided
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` is rendered with `reportDate="2026-01-15"`
- When: The component renders
- Then: `useSmartSummary` is called with options including `autoGenerate: false` (since a historical date was explicitly provided)
- Data: Spy on `useSmartSummary` to inspect called options

## AC2: Given the user clicks "Generate Summary", When the summary generation API is called, Then a loading indicator shows while the summary is being generated, And once complete the summary appears in the normal summary section, And the summary is saved for future viewing of this date.

### 17-2-smart-summary-on-demand-generation-UNIT-004: generate() calls POST /api/summaries/generate with correct payload and headers
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is initialized with `{ autoGenerate: false, reportDate: '2026-01-15' }` and GET returned 404 (hook is in `canGenerate: true` state)
- When: `generate()` is called
- Then: `fetch` is called with `POST` method to `{apiUrl}/api/summaries/generate`, body is `JSON.stringify({ target_date: '2026-01-15', regenerate: false })`, headers include `Authorization: Bearer {token}` and `Content-Type: application/json`
- Data: Mock fetch returning 200 with SmartSummaryData, mock Supabase session

### 17-2-smart-summary-on-demand-generation-UNIT-005: generate() sets isGenerating=true during API call and resolves with summary data
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is in the `canGenerate: true` state after a 404 response with `autoGenerate: false`
- When: `generate()` is called and the POST is in-flight
- Then: `isGenerating` transitions to `true` while the request is pending, and once the POST returns 200 with SmartSummaryData, `data` is set, `hasSummary` becomes `true`, `canGenerate` becomes `false`, `isGenerating` becomes `false`
- Data: Mock fetch with delayed resolution, SmartSummaryData fixture

### 17-2-smart-summary-on-demand-generation-UNIT-006: generate() handles 201 response as success
- Priority: P1
- Type: unit
- Given: `useSmartSummary` is in `canGenerate: true` state
- When: `generate()` is called and the POST returns status 201
- Then: The summary data is parsed from the response and `hasSummary` becomes `true`, `isGenerating` becomes `false`, `error` is `null`
- Data: Mock fetch returning `{ status: 201, ok: true }` with SmartSummaryData JSON body

### 17-2-smart-summary-on-demand-generation-COMP-004: Clicking Generate Summary button triggers generate() and shows loading state
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` renders with `reportDate="2026-01-15"` and hook returns `{ canGenerate: true, hasSummary: false }`
- When: User clicks the "Generate Summary" button
- Then: The `generate` function (from the hook) is called, and when `isGenerating` becomes true, a loading indicator with "Generating AI analysis..." text is displayed
- Data: Mocked hooks, spy on generate function

### 17-2-smart-summary-on-demand-generation-COMP-005: After generation completes, summary renders in normal AI summary block
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` renders and `useSmartSummary` returns `{ hasSummary: true, data: { summary_text: '**Plant performed well...**', ... }, canGenerate: false }`
- When: The component renders with the generated summary
- Then: The summary text is rendered via ReactMarkdown in the "Real AI summary" block, the "Generate Summary" button is no longer visible, and "Powered by AI analysis" footer text is shown
- Data: SmartSummaryData fixture with markdown summary_text

### 17-2-smart-summary-on-demand-generation-UNIT-007: generate() includes auth token from Supabase session
- Priority: P1
- Type: unit
- Given: Supabase `getSession()` returns a session with `access_token: 'jwt-token-xyz'`
- When: `generate()` is called
- Then: The `fetch` call includes `Authorization: Bearer jwt-token-xyz` header
- Data: Mock Supabase session, mock fetch

### 17-2-smart-summary-on-demand-generation-UNIT-008: generate() handles expired session gracefully
- Priority: P1
- Type: unit
- Given: Supabase `getSession()` returns `{ data: { session: null } }`
- When: `generate()` is called
- Then: `fetch` is NOT called, and `error` is set to 'Session expired. Please log in again.'
- Data: Mock Supabase session returning null

## AC3: Given a summary already exists for the selected historical date, When the report loads, Then the existing summary is displayed immediately (no generation prompt).

### 17-2-smart-summary-on-demand-generation-UNIT-009: Hook returns hasSummary=true when GET returns 200 with cached summary
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is called with `{ autoGenerate: false, reportDate: '2026-01-15' }` and GET returns 200 with SmartSummaryData
- When: The hook completes its initial fetch
- Then: `hasSummary` is `true`, `canGenerate` is `false`, `data` contains the returned SmartSummaryData, `isLoading` is `false`, `isGenerating` is `false`
- Data: Mock fetch returning 200 with SmartSummaryData fixture

### 17-2-smart-summary-on-demand-generation-COMP-006: Component displays existing summary immediately with no generation prompt
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` renders with `reportDate="2026-01-15"` and `useSmartSummary` returns `{ hasSummary: true, data: smartSummaryFixture, canGenerate: false }`
- When: The component renders
- Then: The AI summary text is displayed via ReactMarkdown, the "Generate Summary" button is NOT present, and the "No summary exists for this date" text is NOT present
- Data: SmartSummaryData fixture with summary_text

### 17-2-smart-summary-on-demand-generation-COMP-007: No generation prompt when hook is still loading
- Priority: P1
- Type: unit (component)
- Given: `MorningSummarySection` renders and `useSmartSummary` returns `{ isLoading: true, hasSummary: false, canGenerate: false }`
- When: The component renders during initial fetch
- Then: The loading skeleton/pulse animation is shown, and the "Generate Summary" button is NOT visible
- Data: Mocked hooks in loading state

## AC4: Given a "Regenerate" option is available on existing summaries, When the user clicks "Regenerate", Then the summary is re-generated from current data and replaces the prior version.

### 17-2-smart-summary-on-demand-generation-COMP-008: Regenerate button visible when hasSummary is true
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` renders with `useSmartSummary` returning `{ hasSummary: true, data: smartSummaryFixture }`
- When: The component renders
- Then: A button with title "Regenerate AI summary" (containing RefreshCw icon) is visible
- Data: Mocked hooks with existing summary

### 17-2-smart-summary-on-demand-generation-COMP-009: Clicking Regenerate calls regenerateSummary()
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` renders with `useSmartSummary` returning `{ hasSummary: true, regenerate: mockRegenerateFn }`
- When: User clicks the Regenerate button
- Then: `regenerateSummary()` is called once
- Data: Spy on the `regenerate` function returned from mocked hook

### 17-2-smart-summary-on-demand-generation-UNIT-010: regenerate() still calls GET with ?regenerate=true (existing behavior preserved)
- Priority: P1
- Type: unit
- Given: `useSmartSummary` has a loaded summary with `reportDate: '2026-01-15'`
- When: `regenerate()` is called
- Then: `fetch` is called with `GET` method to `{apiUrl}/api/summaries/smart/2026-01-15?regenerate=true` with Bearer auth header
- Data: Mock fetch returning 200 with updated SmartSummaryData

### 17-2-smart-summary-on-demand-generation-COMP-010: Regenerate button is NOT visible when no summary exists (canGenerate state)
- Priority: P1
- Type: unit (component)
- Given: `MorningSummarySection` renders with `useSmartSummary` returning `{ hasSummary: false, canGenerate: true }`
- When: The component renders showing the generation prompt
- Then: The Regenerate button (RefreshCw icon) is NOT visible — only the "Generate Summary" button is shown
- Data: Mocked hooks in canGenerate state

## AC5: Given the summary generation fails (e.g., no production data, API error), When the error occurs, Then a user-friendly error message is displayed with a retry option, And the page remains functional.

### 17-2-smart-summary-on-demand-generation-UNIT-011: generate() sets error state on API failure (500)
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is in `canGenerate: true` state
- When: `generate()` is called and POST returns 500
- Then: `error` is set to a user-friendly message (not raw error text), `isGenerating` is `false`, `isLoading` is `false`, `canGenerate` remains `true` (so user can retry)
- Data: Mock fetch returning `{ status: 500, ok: false }`

### 17-2-smart-summary-on-demand-generation-UNIT-012: generate() sets error state on network failure
- Priority: P0
- Type: unit
- Given: `useSmartSummary` is in `canGenerate: true` state
- When: `generate()` is called and `fetch` throws a `TypeError('Failed to fetch')` (network error)
- Then: `error` is set to a user-friendly message, `isGenerating` is `false`, `canGenerate` remains `true`
- Data: Mock fetch throwing TypeError

### 17-2-smart-summary-on-demand-generation-UNIT-013: generate() handles "no production data" error (404 from POST)
- Priority: P1
- Type: unit
- Given: `useSmartSummary` is in `canGenerate: true` state and the historical date has no daily_summaries records
- When: `generate()` is called and POST returns 404 (no production data available)
- Then: `error` is set to a message indicating no production data is available for this date, `canGenerate` remains `true`
- Data: Mock fetch returning `{ status: 404, ok: false }` from POST

### 17-2-smart-summary-on-demand-generation-COMP-011: Error state shows user-friendly message with retry button after generation failure
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` renders with `useSmartSummary` returning `{ error: 'Unable to generate AI summary.', hasSummary: false, canGenerate: true }`
- When: The component renders
- Then: The error message text is displayed, a retry/try-again button is visible, and the page remains interactive (metrics section is still visible and functional)
- Data: Mocked hooks in error state with canGenerate=true

### 17-2-smart-summary-on-demand-generation-COMP-012: Retry button after generation failure calls generate() (not refetch)
- Priority: P0
- Type: unit (component)
- Given: `MorningSummarySection` renders in error state after a failed generation attempt, with `canGenerate: true`
- When: User clicks the retry button
- Then: The `generate()` function is called (not `refetch()`), allowing the user to retry the specific generation action
- Data: Mocked hooks with error state, spy on generate function

### 17-2-smart-summary-on-demand-generation-COMP-013: Page metrics section remains functional during and after generation error
- Priority: P1
- Type: unit (component)
- Given: `MorningSummarySection` renders with `useDailyActions` returning valid metrics data and `useSmartSummary` returning an error state
- When: The component renders
- Then: The metrics cards (Total Actions, Safety Events, Financial Items) are still visible and display correct data — only the AI Summary section shows the error
- Data: Valid useDailyActions mock data, error state from useSmartSummary

### 17-2-smart-summary-on-demand-generation-UNIT-014: Hook does not update state after unmount (mountedRef guard on generate)
- Priority: P1
- Type: unit
- Given: `useSmartSummary` is rendered and `generate()` is called
- When: The component unmounts before the POST response arrives
- Then: No state update occurs (no React warning), and the hook gracefully discards the response
- Data: Mock fetch with delayed resolution, unmount hook before resolution

### 17-2-smart-summary-on-demand-generation-UNIT-015: Hook re-fetches when reportDate changes
- Priority: P1
- Type: unit
- Given: `useSmartSummary` is mounted with `{ autoGenerate: false, reportDate: '2026-01-15', autoFetch: true }`
- When: The `reportDate` prop changes to `'2026-01-16'`
- Then: A new GET request is made to `/api/summaries/smart/2026-01-16`, and state resets appropriately
- Data: Mock fetch for both dates

edge_cases:
  - User navigates to a historical date that IS yesterday (reportDate matches T-1): autoGenerate should be false when reportDate prop is explicitly passed, but GET will likely return cached summary since T-1 auto-generates on morning load
  - Rapid date switching: Multiple fetch calls may overlap; mountedRef and useCallback dependency array should prevent stale state updates
  - generate() called when already generating (double-click protection): Should either be a no-op or deduplicate the request
  - Empty string reportDate passed to hook: Should fall back to getYesterdayDate() behavior
  - Summary with is_fallback=true: Should still count as hasSummary=true and display normally with fallback badge
  - Very long summary text: Should render properly via ReactMarkdown without layout breaking
  - Summary with citation tags: cleanSummaryText() should strip them before display

error_scenarios:
  - POST /api/summaries/generate returns 500 (server error): Show user-friendly error with retry
  - POST /api/summaries/generate returns 404 (no production data): Show specific message about missing data
  - POST /api/summaries/generate returns 401 (token expired mid-session): Show session expired message
  - Network failure during generate (fetch throws): Show network error with retry
  - Supabase getSession() returns null session: Show session expired, do not call fetch
  - POST /api/summaries/generate returns 429 (rate limited): Show appropriate throttle message with retry
  - GET /api/summaries/smart/{date} returns non-404 error (e.g., 503): Show error without generation prompt

test_file_mapping:
  - 17-2-smart-summary-on-demand-generation-UNIT-*: apps/web/src/hooks/__tests__/useSmartSummary.test.ts
  - 17-2-smart-summary-on-demand-generation-COMP-*: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx

TEST SPEC END
