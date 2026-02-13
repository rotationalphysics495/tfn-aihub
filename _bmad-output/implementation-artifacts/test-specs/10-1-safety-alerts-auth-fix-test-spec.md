TEST SPEC START
story_id: 10-1-safety-alerts-auth-fix
generated: 2026-02-11

test_specifications:

## AC1: Bearer Token Auth Pattern
Given an authenticated user is viewing the dashboard, When the safety alerts component loads, Then the API request includes a Bearer token in the Authorization header (not credentials: 'include'), And safety events are displayed without 403 errors.

### 10-1-safety-alerts-auth-fix-UNIT-001: fetchAlerts sends Bearer token in Authorization header
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid Supabase session (access_token: 'mock-token-abc')
- When: The useSafetyAlerts hook mounts with autoFetch: true and fetchAlerts is invoked
- Then: The GET fetch call to `/api/safety/active` includes header `Authorization: Bearer mock-token-abc`
- And: The fetch options do NOT contain a `credentials` property
- Data: Mock session with access_token 'mock-token-abc'; mock fetch returning successful empty alerts response

### 10-1-safety-alerts-auth-fix-UNIT-002: fetchAlerts returns safety events on successful auth
- Priority: P0
- Type: unit
- Given: A user is authenticated and the API returns 2 safety events (evt-1: Grinder 5, evt-2: Mixer 3)
- When: fetchAlerts completes successfully with Bearer token auth
- Then: state.alerts contains exactly 2 events, state.activeCount is 2, state.error is null, state.isLoading is false
- Data: Two mock SafetyAlert objects; mock session with valid access_token; mock fetch returning 200 with events array

### 10-1-safety-alerts-auth-fix-UNIT-003: fetchAlerts does not use credentials include
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid session
- When: fetchAlerts executes a GET fetch call
- Then: The fetch call options object does NOT contain a `credentials` property (specifically, `credentials: 'include'` is absent)
- Data: Mock session with valid access_token; mock fetch returning successful response

## AC2: Expired Session Handling
Given the user's session has expired, When the safety alerts component attempts to fetch data, Then the request fails gracefully with an auth error message, And no confusing 403 error is shown to the user.

### 10-1-safety-alerts-auth-fix-UNIT-004: fetchAlerts handles null session gracefully
- Priority: P0
- Type: unit
- Given: The user's session has expired (supabase.auth.getSession() returns `{ data: { session: null } }`)
- When: fetchAlerts is invoked via hook mount with autoFetch: true
- Then: state.error is set to 'Authentication required', state.isLoading is false
- And: global.fetch is NOT called (early return before any network request)
- Data: Mock getSession returning null session; no fetch mock needed (should not be called)

### 10-1-safety-alerts-auth-fix-UNIT-005: fetchAlerts handles missing access_token gracefully
- Priority: P0
- Type: unit
- Given: Session object exists but access_token is null (`{ data: { session: { access_token: null } } }`)
- When: fetchAlerts is invoked via hook mount
- Then: state.error is truthy and contains the word 'Authentication' (case-insensitive), state.isLoading is false
- And: global.fetch is NOT called
- Data: Mock getSession returning session with null access_token

### 10-1-safety-alerts-auth-fix-UNIT-006: No 403 error message exposed to user on expired session
- Priority: P0
- Type: unit
- Given: The user's session has expired (getSession returns null session)
- When: fetchAlerts is invoked
- Then: The error message does NOT contain '403' or 'Forbidden' (case-insensitive)
- And: The error message is user-friendly and contains the word 'Authentication'
- Data: Mock getSession returning null session

## AC3: Acknowledge Endpoint Auth Fix
Given an authenticated user acknowledges a safety alert, When the POST request is sent to `/api/safety/acknowledge/:id`, Then the request includes a Bearer token in the Authorization header, And the acknowledgement succeeds without 403 errors.

### 10-1-safety-alerts-auth-fix-UNIT-007: acknowledge sends Bearer token in Authorization header
- Priority: P0
- Type: unit
- Given: A user is authenticated with access_token 'mock-token-xyz', initial fetchAlerts succeeds
- When: acknowledge('evt-123') is called
- Then: The POST fetch call to `/api/safety/acknowledge/evt-123` includes header `Authorization: Bearer mock-token-xyz`, method is 'POST'
- And: The fetch options do NOT contain a `credentials` property
- Data: Mock session with 'mock-token-xyz'; mock fetch for initial load (200 empty) then acknowledge (200 success)

### 10-1-safety-alerts-auth-fix-UNIT-008: acknowledge returns false on expired session
- Priority: P0
- Type: unit
- Given: Initial fetchAlerts succeeds (valid session), then session expires before acknowledge call (getSession returns null on second call)
- When: acknowledge('evt-456') is called with expired session
- Then: The function returns false
- And: global.fetch is NOT called for the POST request (no network request made)
- Data: Mock getSession: first call returns valid session, second call returns null session

### 10-1-safety-alerts-auth-fix-UNIT-009: acknowledge updates local state on success
- Priority: P1
- Type: unit
- Given: User is authenticated, state contains alert 'evt-789' with acknowledged: false
- When: acknowledge('evt-789') is called and API returns `{ success: true }`
- Then: The function returns true, the alert with id 'evt-789' has acknowledged: true and acknowledged_at is set (truthy)
- And: activeCount is decremented by 1 (from 1 to 0)
- Data: Mock safety event evt-789 (unacknowledged); mock acknowledge response with success: true

### 10-1-safety-alerts-auth-fix-UNIT-010: acknowledge does not use credentials include
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid session
- When: acknowledge('evt-any') is called and the POST fetch is made
- Then: The POST fetch options do NOT contain a `credentials` property
- Data: Mock session with valid token; mock fetch for initial load then acknowledge

## AC4: Consistency With Other Hooks
The useSafetyAlerts hook follows the identical auth pattern used in useDailyActions, useLivePulse, and useCostOfLoss. Specifically: createClient() -> getSession() -> Authorization: Bearer ${session.access_token}. The credentials: 'include' option is removed from all fetch calls.

### 10-1-safety-alerts-auth-fix-UNIT-011: fetchAlerts calls createClient and getSession before fetch
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid session, call order is tracked across createClient, getSession, and fetch
- When: fetchAlerts is invoked via hook mount with autoFetch: true
- Then: Call order is createClient -> getSession -> fetch (createClient index < getSession index < fetch index)
- Data: Mock session; mock fetch with call order tracking

### 10-1-safety-alerts-auth-fix-UNIT-012: acknowledge calls createClient and getSession before fetch
- Priority: P0
- Type: unit
- Given: A user is authenticated, initial fetch completes, call order tracking is reset
- When: acknowledge('evt-id') is invoked
- Then: Call order is createClient -> getSession -> fetch (createClient index < getSession index < fetch index)
- Data: Mock session; mock fetch with call order tracking; reset call order after initial load

### 10-1-safety-alerts-auth-fix-UNIT-013: No credentials include in any fetch call from hook
- Priority: P0
- Type: unit
- Given: The hook is mounted and authenticated, both fetchAlerts and acknowledge operations are exercised
- When: All fetch calls made by the hook are inspected
- Then: No call to global.fetch includes a `credentials` property in its options
- Data: Mock session; mock fetch for initial load and acknowledge

### 10-1-safety-alerts-auth-fix-UNIT-014: Public API (UseSafetyAlertsReturn) is unchanged
- Priority: P0
- Type: unit
- Given: The useSafetyAlerts hook is rendered with autoFetch: false
- When: The hook returns its result object
- Then: The return object contains exactly these keys (sorted): acknowledge, activeCount, alerts, error, hasActiveAlerts, isLoading, lastUpdated, refetch
- And: refetch and acknowledge are both functions
- Data: Mock session; mock fetch

### 10-1-safety-alerts-auth-fix-UNIT-015: useSafetyAlertCount public API is unchanged
- Priority: P0
- Type: unit
- Given: The useSafetyAlertCount hook is rendered with autoFetch: false
- When: The hook returns its result object
- Then: The return object contains exactly these keys (sorted): count, isLoading, refetch
- Data: Mock session; mock fetch

## Edge Cases

### 10-1-safety-alerts-auth-fix-UNIT-016: fetchAlerts handles network error during getSession
- Priority: P1
- Type: unit
- Given: supabase.auth.getSession() throws a network error ('Network error')
- When: fetchAlerts is invoked via hook mount
- Then: The error is caught by the try/catch, state.error is set (truthy), state.isLoading is false
- And: global.fetch is NOT called (no API request attempted)
- Data: Mock getSession rejecting with Error('Network error')

### 10-1-safety-alerts-auth-fix-UNIT-017: acknowledge handles network error during getSession
- Priority: P1
- Type: unit
- Given: Initial fetchAlerts succeeds with valid session, then getSession throws on the acknowledge call
- When: acknowledge('evt-id') is invoked
- Then: The function returns false
- And: global.fetch is NOT called for the POST request
- Data: Mock getSession: first resolve with valid session, second reject with Error('Network error')

### 10-1-safety-alerts-auth-fix-UNIT-018: Polling continues to work with auth pattern
- Priority: P1
- Type: unit
- Given: The hook is mounted with pollingInterval: 500ms and user is authenticated
- When: The polling interval elapses and fetchAlerts is called again
- Then: The subsequent fetch call includes `Authorization: Bearer mock-token-abc` header
- And: The fetch options do NOT contain a `credentials` property
- Data: Mock session; mock fetch; pollingInterval: 500; waitFor timeout: 3000ms

### 10-1-safety-alerts-auth-fix-UNIT-019: fetchAlerts handles API 500 error with Bearer token
- Priority: P1
- Type: unit
- Given: User is authenticated (Bearer token is sent), but API returns HTTP 500
- When: fetchAlerts completes
- Then: state.error contains '500', state.isLoading is false
- Data: Mock session; mock fetch returning { ok: false, status: 500 }

### 10-1-safety-alerts-auth-fix-UNIT-020: Content-Type header is preserved alongside Authorization
- Priority: P1
- Type: unit
- Given: User is authenticated with valid session
- When: Both fetchAlerts (GET) and acknowledge (POST) make fetch calls
- Then: Both GET and POST requests contain headers `Content-Type: application/json` AND `Authorization: Bearer mock-token-abc`
- Data: Mock session; mock fetch for initial load and acknowledge

edge_cases:
  - getSession() throws a network error mid-flow (covered by UNIT-016, UNIT-017)
  - Session exists but access_token is explicitly null (not just missing) (covered by UNIT-005)
  - Polling fires after session expires — subsequent poll should set auth error without crashing
  - Component unmounts between getSession() resolving and fetch() being called (handled by existing mountedRef guard; not explicitly tested as it's existing behavior)
  - API returns 500 after successful auth — error should reflect server error, not auth error (covered by UNIT-019)
  - Both Authorization and Content-Type headers coexist in all requests (covered by UNIT-020)

error_scenarios:
  - Expired/null session returns user-friendly 'Authentication required' error, never raw 403 (UNIT-004, UNIT-006)
  - Missing access_token (session object exists but token is null) triggers early return (UNIT-005)
  - Network failure during getSession() is caught and surfaces error state (UNIT-016)
  - Network failure during getSession() on acknowledge path returns false (UNIT-017)
  - API 500 response is handled gracefully with error state (UNIT-019)
  - Acknowledge with expired session returns false without making network call (UNIT-008)

test_file_mapping:
  - 10-1-safety-alerts-auth-fix-UNIT-*: apps/web/src/hooks/__tests__/useSafetyAlerts.test.ts

TEST SPEC END
