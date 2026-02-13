# Epic 10 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 10
**Started:** 2026-02-11 05:41:34

---


## DESIGN: 10-1-safety-alerts-auth-fix
**Timestamp:** 2026-02-11 05:57:20

DESIGN START
story_id: 10-1-safety-alerts-auth-fix

files_to_modify:
  - path: apps/web/src/hooks/useSafetyAlerts.ts
    action: modify
    purpose: Replace cookie-based auth (credentials: 'include') with Bearer token auth pattern in both fetchAlerts and acknowledge functions

patterns_to_use:
  - Supabase Bearer Token Auth: createClient() -> getSession() -> Authorization header, exactly as used in useDailyActions.ts (lines 123-148). Applied to both fetchAlerts (GET) and acknowledge (POST) functions.
  - Graceful Auth Error Handling: Early return with error state when session is missing (same pattern as useDailyActions.ts lines 126-133). fetchAlerts sets error state; acknowledge returns false.

dependencies:
  - @/lib/supabase/client: installed (apps/web/src/lib/supabase/client.ts already exists)
  - @supabase/ssr: installed (already used by client.ts)

acceptance_criteria_mapping:
  - AC1 (Bearer Token Auth Pattern): fetchAlerts in useSafetyAlerts.ts — add createClient/getSession, replace credentials:'include' with Authorization header on lines 84-91
  - AC2 (Expired Session Handling): fetchAlerts in useSafetyAlerts.ts — add early return with 'Authentication required' error state when !session?.access_token (before fetch call)
  - AC3 (Acknowledge Endpoint Auth Fix): acknowledge in useSafetyAlerts.ts — same auth pattern change on lines 123-130, early return false when no session
  - AC4 (Consistency With Other Hooks): Both functions follow the identical createClient() -> getSession() -> Bearer header pattern used in useDailyActions.ts, useLivePulse.ts, and useCostOfLoss.ts

risks:
  - Risk: createClient() called inside useCallback may create new client on each invocation — Mitigation: This is the same pattern used by useDailyActions.ts (line 123) which works correctly; createBrowserClient from @supabase/ssr handles singleton caching internally.
  - Risk: Other files also use credentials:'include' (users/page.tsx, audit/page.tsx, assignments/page.tsx, useHandoffQA.ts, CitationPanel.tsx, eod/page.tsx) — Mitigation: Out of scope for this story. Noted for future cleanup. Only useSafetyAlerts.ts is modified per story guardrails.
  - Risk: Polling calls fetchAlerts every 30s, which now calls getSession() each time — Mitigation: This is acceptable; getSession() reads from local storage/memory and is lightweight. Same pattern works in other hooks.

estimated_test_files:
  - No new test files required: This is a single-file auth pattern fix. Validation is via TypeScript compilation (npx tsc --noEmit or next build) and manual verification that exports/interfaces are unchanged.

implementation_order:
  1. Add import statement: `import { createClient } from '@/lib/supabase/client'` at top of useSafetyAlerts.ts (after React imports, line 3)
  2. Fix fetchAlerts auth pattern (lines 84-91): Insert createClient()/getSession() calls after the isLoading setState, add early-return with auth error if no session, replace credentials:'include' with Authorization Bearer header
  3. Fix acknowledge auth pattern (lines 122-130): Insert createClient()/getSession() calls at start of try block, add early-return false if no session, replace credentials:'include' with Authorization Bearer header
  4. Verify TypeScript compiles: Run `npx tsc --noEmit` from apps/web to confirm no type errors
  5. Verify public API unchanged: Confirm exported interfaces (SafetyAlert, SafetyAlertsState, UseSafetyAlertsReturn) and function signatures are untouched
  6. Grep codebase for remaining credentials:'include' occurrences and note them (informational, not to fix in this story)
DESIGN END

---

## TEST_SPEC: 10-1-safety-alerts-auth-fix
**Timestamp:** 2026-02-11 05:59:13

TEST SPEC START
story_id: 10-1-safety-alerts-auth-fix
generated: 2026-02-11

test_specifications:

## AC1: Bearer Token Auth Pattern
Given an authenticated user is viewing the dashboard, when the safety alerts component loads, then the API request includes a Bearer token in the Authorization header (not credentials: 'include') and safety events are displayed without 403 errors.

### 10-1-safety-alerts-auth-fix-UNIT-001: fetchAlerts sends Bearer token in Authorization header
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid Supabase session (access_token: 'mock-token-abc')
- When: The `useSafetyAlerts` hook mounts and `fetchAlerts` is invoked
- Then: The `fetch` call to `${apiUrl}/api/safety/active` includes header `Authorization: Bearer mock-token-abc`
- And: The `fetch` call does NOT include `credentials: 'include'` in the request options
- Data: Mock `createClient().auth.getSession()` to return `{ data: { session: { access_token: 'mock-token-abc' } } }`; mock `fetch` to return `{ ok: true, json: () => ({ events: [], count: 0, last_updated: '2026-02-11T00:00:00Z' }) }`

### 10-1-safety-alerts-auth-fix-UNIT-002: fetchAlerts returns safety events on successful auth
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid session and the API returns 2 safety events
- When: `fetchAlerts` completes successfully
- Then: `state.alerts` contains the 2 returned events, `state.activeCount` equals 2, `state.error` is null, `state.isLoading` is false
- Data: Mock fetch response: `{ events: [{ id: 'evt-1', ... }, { id: 'evt-2', ... }], count: 2, last_updated: '2026-02-11T12:00:00Z' }`

### 10-1-safety-alerts-auth-fix-UNIT-003: fetchAlerts does not use credentials include
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid session
- When: `fetchAlerts` executes a fetch call
- Then: The fetch call options object does NOT contain a `credentials` property
- Data: Inspect `global.fetch` mock call arguments to verify `credentials` key is absent

## AC2: Expired Session Handling
Given the user's session has expired, when the safety alerts component attempts to fetch data, then the request fails gracefully with an auth error message and no confusing 403 error is shown.

### 10-1-safety-alerts-auth-fix-UNIT-004: fetchAlerts handles null session gracefully
- Priority: P0
- Type: unit
- Given: The user's session has expired (getSession returns `{ data: { session: null } }`)
- When: `fetchAlerts` is invoked
- Then: `state.error` is set to 'Authentication required' (or equivalent auth error message), `state.isLoading` is false
- And: `global.fetch` is NOT called (early return before network request)
- Data: Mock `createClient().auth.getSession()` to return `{ data: { session: null } }`

### 10-1-safety-alerts-auth-fix-UNIT-005: fetchAlerts handles missing access_token gracefully
- Priority: P0
- Type: unit
- Given: The session exists but `access_token` is undefined/null
- When: `fetchAlerts` is invoked
- Then: `state.error` is set to an auth error message, `state.isLoading` is false
- And: `global.fetch` is NOT called
- Data: Mock `createClient().auth.getSession()` to return `{ data: { session: { access_token: null } } }`

### 10-1-safety-alerts-auth-fix-UNIT-006: No 403 error message exposed to user on expired session
- Priority: P1
- Type: unit
- Given: The user's session has expired
- When: `fetchAlerts` is invoked
- Then: The error message in state does NOT contain '403' or 'Forbidden'
- And: The error message is user-friendly (e.g., 'Authentication required')
- Data: Mock session as null

## AC3: Acknowledge Endpoint Auth Fix
Given an authenticated user acknowledges a safety alert, when the POST request is sent to `/api/safety/acknowledge/:id`, then the request includes a Bearer token in the Authorization header and the acknowledgement succeeds without 403 errors.

### 10-1-safety-alerts-auth-fix-UNIT-007: acknowledge sends Bearer token in Authorization header
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid session (access_token: 'mock-token-xyz')
- When: `acknowledge('evt-123')` is called
- Then: The `fetch` call to `${apiUrl}/api/safety/acknowledge/evt-123` includes `Authorization: Bearer mock-token-xyz`
- And: The fetch method is 'POST'
- And: The `credentials` option is NOT present in the request
- Data: Mock session with access_token 'mock-token-xyz'; mock fetch to return `{ ok: true, json: () => ({ success: true }) }`

### 10-1-safety-alerts-auth-fix-UNIT-008: acknowledge returns false on expired session
- Priority: P0
- Type: unit
- Given: The user's session has expired (getSession returns null session)
- When: `acknowledge('evt-456')` is called
- Then: The function returns `false`
- And: `global.fetch` is NOT called
- Data: Mock `createClient().auth.getSession()` to return `{ data: { session: null } }`

### 10-1-safety-alerts-auth-fix-UNIT-009: acknowledge updates local state on success
- Priority: P1
- Type: unit
- Given: A user is authenticated and state contains alert with id 'evt-789' (acknowledged: false)
- When: `acknowledge('evt-789')` is called and the API returns `{ success: true }`
- Then: The function returns `true`
- And: The alert with id 'evt-789' in state has `acknowledged: true` and `acknowledged_at` is set
- And: `activeCount` is decremented by 1
- Data: Pre-populate state with alerts including evt-789; mock successful API response

### 10-1-safety-alerts-auth-fix-UNIT-010: acknowledge does not use credentials include
- Priority: P0
- Type: unit
- Given: A user is authenticated with a valid session
- When: `acknowledge('evt-any')` is called
- Then: The fetch call options object does NOT contain a `credentials` property
- Data: Inspect `global.fetch` mock call arguments for the POST request

## AC4: Consistency With Other Hooks
The useSafetyAlerts hook follows the identical auth pattern used in useDailyActions, useLivePulse, and useCostOfLoss: createClient() -> getSession() -> Authorization: Bearer ${session.access_token}. The credentials: 'include' option is removed from all fetch calls.

### 10-1-safety-alerts-auth-fix-UNIT-011: fetchAlerts calls createClient and getSession before fetch
- Priority: P0
- Type: unit
- Given: A user is authenticated
- When: `fetchAlerts` is invoked
- Then: `createClient()` is called first, then `supabase.auth.getSession()` is called, then `fetch` is called with the session token
- And: The call order is createClient -> getSession -> fetch (sequential)
- Data: Use spies on createClient and getSession to verify call order

### 10-1-safety-alerts-auth-fix-UNIT-012: acknowledge calls createClient and getSession before fetch
- Priority: P0
- Type: unit
- Given: A user is authenticated
- When: `acknowledge('evt-id')` is invoked
- Then: `createClient()` is called, then `supabase.auth.getSession()` is called, then `fetch` is called with the token
- Data: Use spies on createClient and getSession to verify call order

### 10-1-safety-alerts-auth-fix-UNIT-013: No credentials include in any fetch call from hook
- Priority: P1
- Type: unit
- Given: The hook is mounted and authenticated
- When: Both `fetchAlerts` and `acknowledge` have been invoked
- Then: No call to `global.fetch` across the entire test includes `credentials: 'include'` in the options argument
- Data: Examine all `global.fetch` mock calls

### 10-1-safety-alerts-auth-fix-UNIT-014: Public API (UseSafetyAlertsReturn) is unchanged
- Priority: P1
- Type: unit
- Given: The `useSafetyAlerts` hook is rendered
- When: The hook returns its result
- Then: The return object contains exactly: `alerts`, `activeCount`, `isLoading`, `error`, `lastUpdated`, `refetch`, `acknowledge`, `hasActiveAlerts`
- And: `refetch` is a function, `acknowledge` is a function accepting a string and returning Promise<boolean>
- Data: renderHook(() => useSafetyAlerts()) and inspect result.current keys

### 10-1-safety-alerts-auth-fix-UNIT-015: useSafetyAlertCount public API is unchanged
- Priority: P1
- Type: unit
- Given: The `useSafetyAlertCount` hook is rendered
- When: The hook returns its result
- Then: The return object contains exactly: `count`, `isLoading`, `refetch`
- Data: renderHook(() => useSafetyAlertCount()) and inspect result.current keys

## Edge Cases

### 10-1-safety-alerts-auth-fix-UNIT-016: fetchAlerts handles network error during getSession
- Priority: P2
- Type: unit
- Given: `createClient().auth.getSession()` throws a network error
- When: `fetchAlerts` is invoked
- Then: The error is caught, `state.error` is set to an error message, `state.isLoading` is false
- And: `global.fetch` is NOT called
- Data: Mock `getSession` to throw `new Error('Network error')`

### 10-1-safety-alerts-auth-fix-UNIT-017: acknowledge handles network error during getSession
- Priority: P2
- Type: unit
- Given: `createClient().auth.getSession()` throws a network error
- When: `acknowledge('evt-id')` is invoked
- Then: The function returns `false`
- And: `global.fetch` is NOT called
- Data: Mock `getSession` to throw

### 10-1-safety-alerts-auth-fix-UNIT-018: Polling continues to work with auth pattern
- Priority: P1
- Type: unit
- Given: The hook is mounted with `pollingInterval: 1000` and user is authenticated
- When: 1 second elapses (advance timers)
- Then: `fetchAlerts` is called again with proper Bearer token auth (createClient -> getSession -> fetch)
- Data: Use `vi.useFakeTimers()` and `vi.advanceTimersByTime(1000)`

### 10-1-safety-alerts-auth-fix-UNIT-019: fetchAlerts handles API 500 error with Bearer token
- Priority: P2
- Type: unit
- Given: User is authenticated, but the API returns a 500 Internal Server Error
- When: `fetchAlerts` completes
- Then: `state.error` contains the error message (e.g., 'Failed to fetch safety alerts: 500'), `state.isLoading` is false
- Data: Mock fetch to return `{ ok: false, status: 500 }`

### 10-1-safety-alerts-auth-fix-UNIT-020: Content-Type header is preserved alongside Authorization
- Priority: P2
- Type: unit
- Given: User is authenticated
- When: `fetchAlerts` or `acknowledge` makes a fetch call
- Then: Both `Content-Type: application/json` AND `Authorization: Bearer <token>` are present in the headers
- Data: Inspect fetch mock call arguments for both headers

edge_cases:
  - getSession() returns a session object but with an empty string access_token — should treat as unauthenticated
  - createClient() is called inside useCallback — verify it doesn't cause unnecessary re-renders or stale closures
  - Rapid polling (multiple concurrent fetchAlerts calls) — each call should get its own fresh session token
  - Component unmounts between getSession() resolving and fetch() being called — mountedRef should prevent state update

error_scenarios:
  - getSession() rejects with an exception (Supabase client error)
  - fetch() rejects after successful auth (network failure mid-request)
  - API returns 401 with Bearer token (token expired between getSession and fetch)
  - API returns 403 even with correct Bearer token (permissions issue, not auth issue)
  - JSON parse error on API response after successful auth

test_file_mapping:
  - 10-1-safety-alerts-auth-fix-UNIT-*: apps/web/src/hooks/__tests__/useSafetyAlerts.test.ts

TEST SPEC END

---

## DESIGN: 10-1-safety-alerts-auth-fix
**Timestamp:** 2026-02-11 07:11:38

DESIGN START
story_id: 10-1-safety-alerts-auth-fix

files_to_modify:
  - path: apps/web/src/hooks/useSafetyAlerts.ts
    action: modify
    purpose: Replace cookie-based auth (credentials: 'include') with Bearer token auth pattern in both fetchAlerts and acknowledge functions

patterns_to_use:
  - Supabase Bearer Token Auth: createClient() -> getSession() -> Authorization header, exactly as used in useDailyActions.ts (lines 123-148), useLivePulse.ts (lines 125-143), and useCostOfLoss.ts (lines 75-97). Applied to both fetchAlerts (GET) and acknowledge (POST) functions.
  - Graceful Auth Error Handling: Early return with error state when session is missing/expired. fetchAlerts sets state.error to 'Authentication required' and isLoading to false (matches useLivePulse.ts lines 128-133). acknowledge returns false (no state update needed, consistent with its existing error contract).

dependencies:
  - @/lib/supabase/client: installed (apps/web/src/lib/supabase/client.ts exists, exports createClient using createBrowserClient from @supabase/ssr)
  - @supabase/ssr: installed (already used by client.ts)
  - No new dependencies required

acceptance_criteria_mapping:
  - AC1 (Bearer Token Auth Pattern): Modify fetchAlerts in useSafetyAlerts.ts — add createClient()/getSession() call inside the try block (after isLoading setState, before fetch), replace fetch options from `credentials: 'include'` to `headers: { 'Authorization': 'Bearer ${session.access_token}', 'Content-Type': 'application/json' }` with no credentials property. Lines 84-91 change.
  - AC2 (Expired Session Handling): Add early return in fetchAlerts after getSession() — if !session?.access_token, set state to { isLoading: false, error: 'Authentication required' } and return before calling fetch. This prevents any 403 from the API and shows a clean error message. Covered inside the try block so getSession() exceptions are also caught.
  - AC3 (Acknowledge Endpoint Auth Fix): Modify acknowledge in useSafetyAlerts.ts — add createClient()/getSession() call at start of try block (lines 122-130), add early return false if !session?.access_token, replace fetch options from `credentials: 'include'` to `headers: { 'Authorization': 'Bearer ${session.access_token}', 'Content-Type': 'application/json' }` with no credentials property.
  - AC4 (Consistency With Other Hooks): Both functions follow the identical createClient() -> getSession() -> Bearer header pattern used in useDailyActions.ts, useLivePulse.ts, and useCostOfLoss.ts. The credentials: 'include' option is removed from all fetch calls in the file.

risks:
  - Risk: createClient() called inside useCallback creates a new client instance on each invocation — Mitigation: This is the exact pattern used by useDailyActions.ts (line 123), useLivePulse.ts (line 125), and useCostOfLoss.ts (line 75) which all work correctly. createBrowserClient from @supabase/ssr handles singleton caching internally, so no performance impact.
  - Risk: Other files in the codebase also use `credentials: 'include'` for API calls (found in prior analysis: users/page.tsx, audit/page.tsx, assignments/page.tsx, useHandoffQA.ts, CitationPanel.tsx, eod/page.tsx) — Mitigation: Out of scope for this story per guardrails. Only useSafetyAlerts.ts is modified. These should be logged as tech debt.
  - Risk: Polling calls fetchAlerts every 30s, which now calls getSession() each time — Mitigation: getSession() reads from local memory/storage (not a network call); same approach works correctly in all other hooks with polling. No performance concern.
  - Risk: Race condition if component unmounts between getSession() resolving and fetch being called — Mitigation: The existing mountedRef check at lines 80 and 99 already handles this correctly; getSession() is fast (local) so the window is negligible.
  - Risk: Breaking the public API (exported types/interfaces) — Mitigation: No changes to SafetyAlert, SafetyAlertsState, UseSafetyAlertsReturn interfaces. No changes to function signatures. No changes to useSafetyAlertCount. Test UNIT-014 and UNIT-015 explicitly verify this.

estimated_test_files:
  - apps/web/src/hooks/__tests__/useSafetyAlerts.test.ts: Already exists with 20 TDD tests (UNIT-001 through UNIT-020) covering all 4 ACs plus edge cases. These tests are designed to FAIL against the current broken code and PASS after the auth fix. No new test file creation needed.

implementation_order:
  1. Add import statement: Add `import { createClient } from '@/lib/supabase/client'` on line 4 of useSafetyAlerts.ts (after the React imports on line 3, before the JSDoc comment on line 5)
  2. Fix fetchAlerts auth pattern (lines 84-91): Inside the existing try block, before the fetch call, insert `const supabase = createClient()` and `const { data: { session } } = await supabase.auth.getSession()`. Add early-return with `setState(prev => ({ ...prev, isLoading: false, error: 'Authentication required' }))` if `!session?.access_token`. Replace the fetch call to remove `credentials: 'include'` and add `'Authorization': \`Bearer ${session.access_token}\`` to the headers object.
  3. Fix acknowledge auth pattern (lines 122-130): Inside the existing try block, before the fetch call, insert `const supabase = createClient()` and `const { data: { session } } = await supabase.auth.getSession()`. Add early-return `return false` if `!session?.access_token`. Replace the fetch call to remove `credentials: 'include'` and add `'Authorization': \`Bearer ${session.access_token}\`` to the headers object.
  4. Verify TypeScript compiles: Run `npx tsc --noEmit` from apps/web to confirm no type errors introduced
  5. Run existing test suite: Execute the 20 TDD tests in apps/web/src/hooks/__tests__/useSafetyAlerts.test.ts — all should now pass
  6. Verify public API unchanged: Confirm via tests UNIT-014 and UNIT-015 that exported interfaces (SafetyAlert, SafetyAlertsState, UseSafetyAlertsReturn) and function signatures are untouched
  7. Scan for remaining credentials:'include': Grep the codebase for any remaining `credentials: 'include'` occurrences and document them (informational only, not to fix in this story)
DESIGN END

---

## TEST_SPEC: 10-1-safety-alerts-auth-fix
**Timestamp:** 2026-02-11 07:13:36

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

---

## DESIGN: 10-2-live-pulse-schema-fix
**Timestamp:** 2026-02-11 07:40:07

DESIGN START
story_id: 10-2-live-pulse-schema-fix

files_to_modify:
  - path: apps/api/app/api/live_pulse.py
    action: modify
    purpose: Remove non-existent columns (oee_percentage, downtime_reason, downtime_minutes) from the Supabase select query on line 252-254 to fix the 500 error caused by PostgREST rejecting unknown column names

patterns_to_use:
  - Supabase select query pattern: `.table("live_snapshots").select("col1, col2, ...").order(...).execute()` — only reference columns that exist in the actual table schema per migrations 0003 and 0022
  - Safe field access via .get(): The existing pattern of `snapshot.get("field_name")` with None fallbacks is already used throughout the aggregation logic (lines 277-332) and will continue to work correctly when fields are absent from query results

dependencies:
  - supabase-py: installed (already used by the endpoint)
  - No new dependencies required

acceptance_criteria_mapping:
  - AC1 (Successful API Response): Fix the select string in `get_live_pulse_data()` at line 252-254 of `apps/api/app/api/live_pulse.py`. Remove `oee_percentage`, `downtime_reason`, `downtime_minutes` from the select. The corrected query will only request columns that exist in `live_snapshots`: `id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars`. This eliminates the PostgREST 400 error (column not found) that the generic exception handler converts to a 500.
  - AC2 (Correct Column References): Same file, same line change. After the fix, the select string references only: `id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars` — all of which exist per migration 0003 + 0022. Note: `output_variance` is a generated column that could optionally be included but is not referenced anywhere in the aggregation logic, so omitting it is correct. `created_at` is also not needed by the aggregation.
  - AC3 (OEE Calculation Graceful Handling): The existing OEE aggregation code at lines 290-294 already handles the absence of `oee_percentage` gracefully. When the column is not in the select, `snapshot.get("oee_percentage")` returns `None`, so `oee_count` stays 0, and `avg_oee` defaults to `0.0` (line 338-340). The `ProductionData.oee_percentage` field defaults to `0.0` in the response model (line 59). No code change needed in the aggregation section — the query fix alone achieves the desired behavior.
  - AC4 (Existing Tests Pass): The tests in `test_live_pulse_api.py` use MagicMock objects that bypass the actual Supabase query. The mock `table_side_effect` returns `SAMPLE_LIVE_SNAPSHOTS` directly (which includes `oee_percentage` in the dict). Changing the select string does not affect mock-based tests since mocks never validate column names. All 16 existing tests should continue to pass unchanged. One test (`test_oee_average_calculation` at line 556) asserts `80 < production["oee_percentage"] < 90` — this passes because the mock data still contains `oee_percentage` values and the aggregation code still reads them via `.get()`. A comment will be added to the test data noting the mock/production divergence.

risks:
  - Risk: The `test_oee_average_calculation` test (line 556) passes because mock data includes `oee_percentage` in `SAMPLE_LIVE_SNAPSHOTS`, but in production the field won't exist, so OEE will be 0.0. This is a test/production behavioral divergence. — Mitigation: This is acceptable per story scope. The story asks that existing tests continue to pass. A brief comment in the test data will note the divergence. Fixing the test to reflect production reality (OEE = 0.0) would require changing test assertions, which could be done but would alter the intent of the original test. The story dev notes explicitly say "this is fine for mock-based tests since mocks bypass actual DB queries."
  - Risk: Removing `downtime_reason` and `downtime_minutes` from the select means active_downtime will always be an empty list in production (the `.get()` calls at lines 311/315 return None, so the `if downtime_reason and downtime_reason.strip()` check at line 312 is never true). — Mitigation: This is the expected behavior per the story. The columns don't exist in the table, so they could never have had values. The response model's `active_downtime` list defaults to empty.
  - Risk: `output_variance` (a generated column) is not included in the new select string. — Mitigation: `output_variance` is not referenced anywhere in the aggregation logic (lines 277-436), so omitting it is correct and avoids potential issues with selecting generated columns.

estimated_test_files:
  - apps/api/tests/test_live_pulse_api.py: Existing test file with 16 tests. All tests should pass without modification. A comment will be added to SAMPLE_LIVE_SNAPSHOTS noting that `oee_percentage` and `downtime_reason` exist in mock data for backward compatibility but do not exist in the actual `live_snapshots` table.

implementation_order:
  1. Fix the Supabase select query string at line 252-254 in `apps/api/app/api/live_pulse.py`: Change from `"id, asset_id, snapshot_timestamp, current_output, target_output, oee_percentage, status, financial_loss_dollars, downtime_reason, downtime_minutes"` to `"id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars"`. This is the single change that fixes the root cause (PostgREST column-not-found error).
  2. Add a brief inline comment above the select query noting that OEE is in `daily_summaries` (not `live_snapshots`) and downtime columns don't exist in this table — this documents the schema reality for future developers and prevents re-introduction of the bug.
  3. Add a comment to `SAMPLE_LIVE_SNAPSHOTS` in `apps/api/tests/test_live_pulse_api.py` (above line 57) noting that `oee_percentage` and `downtime_reason` are included in mock data but do not exist in the actual `live_snapshots` table schema.
  4. Run `pytest apps/api/tests/test_live_pulse_api.py -v` to verify all 16 existing tests pass with the corrected query.
  5. Run `pytest apps/api/tests/ -v --timeout=30` to verify no regressions in other API tests.
DESIGN END

---

## DESIGN: 10-3-cost-of-loss-schema-fix
**Timestamp:** 2026-02-11 08:05:47

DESIGN START
story_id: 10-3-cost-of-loss-schema-fix

files_to_modify:
  - path: apps/api/app/api/financial.py
    action: modify
    purpose: Fix 2 Supabase SELECT strings (lines 307, 484) and 2 record.get() calls (lines 335, 495) to use "waste_count" instead of "waste" — matching the actual daily_summaries table schema
  - path: apps/api/app/services/financial.py
    action: modify
    purpose: Fix 1 Supabase SELECT string (line 352) and 1 record.get() call (line 369) to use "waste_count" instead of "waste" — matching the actual daily_summaries table schema
  - path: apps/api/tests/test_financial_api.py
    action: modify
    purpose: Update 4 mock data dictionary entries (lines 157, 158, 254, 370) from key "waste" to "waste_count" so mocks match the corrected query column name

patterns_to_use:
  - Supabase PostgREST select pattern: `.table("daily_summaries").select("col1, col2, ...")` — column names in the select string must exactly match the database schema. The column is `waste_count` per migration 0003_analytical_cache.sql line 30.
  - Safe field access via .get(): `record.get("waste_count") or 0` — the key in the .get() call must match the column name used in the select string so that the returned dict contains the expected key.
  - Consistent schema naming: The agent data source layer (supabase.py line 1138) already uses `waste_count` correctly. This fix aligns the older REST API endpoints (from Stories 2.7/2.8) with the same correct column name.

dependencies:
  - supabase-py: installed (already used by both financial.py files)
  - pytest: installed (already used for test suite)
  - No new dependencies required

acceptance_criteria_mapping:
  - AC1 (Daily Summary Query Uses Correct Column Name): `apps/api/app/api/financial.py` method `get_cost_of_loss()` — line 484 change SELECT string from `"asset_id, downtime_minutes, waste, financial_loss, oee_percentage, created_at"` to `"asset_id, downtime_minutes, waste_count, financial_loss, oee_percentage, created_at"`, and line 495 change `record.get("waste")` to `record.get("waste_count")`. This eliminates the 500 error (or silent null) when querying the non-existent `waste` column.
  - AC2 (Financial Summary Query Uses Correct Column Name): `apps/api/app/api/financial.py` method `get_financial_summary()` — line 307 change SELECT string from `"asset_id, downtime_minutes, waste, financial_loss"` to `"asset_id, downtime_minutes, waste_count, financial_loss"`, and line 335 change `record.get("waste")` to `record.get("waste_count")`. The aggregated `total_waste_count` calculation on line 338 already uses the local variable `waste` which is assigned from the .get() call, so the aggregation logic is correct once the .get() key is fixed.
  - AC3 (Financial Impact Service Uses Correct Column Name): `apps/api/app/services/financial.py` method `get_financial_impact()` — line 352 change SELECT string from `"asset_id, date, downtime_minutes, waste, financial_loss"` to `"asset_id, date, downtime_minutes, waste_count, financial_loss"`, and line 369 change `record.get("waste")` to `record.get("waste_count")`. The waste loss calculation downstream (`total_waste * cost_per_unit`) is already correct; only the data extraction key is wrong.
  - AC4 (Existing Tests Updated To Match Schema): `apps/api/tests/test_financial_api.py` — update mock data dictionaries at lines 157, 158, 254, and 370 to use key `"waste_count"` instead of `"waste"`. The test assertions (checking response fields like `total_loss`, `total_downtime_minutes`, `asset_count`, etc.) do not reference the column name directly and remain unchanged. All existing tests should pass after this update.
  - AC5 (Agent Data Source Remains Correct): `apps/api/app/services/agent/data_source/supabase.py` line 1138 already uses `waste_count` in its select — verified by reading the file. No changes needed. The tests in `test_cost_of_loss.py` and `test_financial_impact.py` reference "waste" as a category string (not a column key) and are unaffected.

risks:
  - Risk: PostgREST may silently ignore unknown columns in SELECT rather than throwing an error, meaning the bug manifests as null/0 values rather than a 500 error — Mitigation: Either way, the fix is the same (correct the column name). After the fix, the query will return actual `waste_count` data from the database.
  - Risk: Line numbers in the story may have drifted if prior story implementations modified financial.py — Mitigation: Verified by reading the actual file contents; all line numbers match exactly (307, 335, 484, 495 in financial.py API; 352, 369 in financial.py service; 157, 158, 254, 370 in test file). The 10-1 and 10-2 stories modified different files (useSafetyAlerts.ts and live_pulse.py respectively).
  - Risk: Test mock data uses `"waste"` as a dict key, and changing it to `"waste_count"` could break test assertions that check for the key — Mitigation: Verified by reading the test file; assertions check response-level fields (`total_loss`, `total_downtime_minutes`, `asset_count`), not the raw dict keys from mock data. The mock data is consumed by the endpoint code via `record.get()`, so only the endpoint code needs the key to match.
  - Risk: Other test files (`test_financial_impact.py`, `test_cost_of_loss.py`) may also need updates — Mitigation: Verified by grepping; their references to "waste" are category name strings in assertion text/breakdown categories, not database column keys. They are unaffected by this change.

estimated_test_files:
  - apps/api/tests/test_financial_api.py: Existing test file with mock data updates (lines 157, 158, 254, 370). All existing test assertions remain unchanged — only the mock dict keys change from "waste" to "waste_count". Run with `pytest apps/api/tests/test_financial_api.py -v`.
  - apps/api/tests/services/agent/tools/test_cost_of_loss.py: Existing test file — NO changes needed. Verify it still passes to confirm AC5 (agent data source unaffected). Run with `pytest apps/api/tests/services/agent/tools/test_cost_of_loss.py -v`.
  - apps/api/tests/services/agent/tools/test_financial_impact.py: Existing test file — NO changes needed. Verify it still passes as a regression check.

implementation_order:
  1. Fix `get_financial_summary()` in `apps/api/app/api/financial.py` (AC2): Line 307 change SELECT string `"asset_id, downtime_minutes, waste, financial_loss"` to `"asset_id, downtime_minutes, waste_count, financial_loss"`. Line 335 change `record.get("waste")` to `record.get("waste_count")`.
  2. Fix `get_cost_of_loss()` in `apps/api/app/api/financial.py` (AC1): Line 484 change SELECT string `"asset_id, downtime_minutes, waste, financial_loss, oee_percentage, created_at"` to `"asset_id, downtime_minutes, waste_count, financial_loss, oee_percentage, created_at"`. Line 495 change `record.get("waste")` to `record.get("waste_count")`.
  3. Fix `get_financial_impact()` in `apps/api/app/services/financial.py` (AC3): Line 352 change SELECT string `"asset_id, date, downtime_minutes, waste, financial_loss"` to `"asset_id, date, downtime_minutes, waste_count, financial_loss"`. Line 369 change `record.get("waste")` to `record.get("waste_count")`.
  4. Update test mock data in `apps/api/tests/test_financial_api.py` (AC4): Change `"waste": 5` to `"waste_count": 5` on line 157, `"waste": 10` to `"waste_count": 10` on line 158, `"waste": 10` to `"waste_count": 10` on line 254, `"waste": 20` to `"waste_count": 20` on line 370.
  5. Run financial API tests: `pytest apps/api/tests/test_financial_api.py -v` — verify all tests pass with the corrected column names.
  6. Run agent tool tests for regression check (AC5): `pytest apps/api/tests/services/agent/tools/test_cost_of_loss.py -v` and `pytest apps/api/tests/services/agent/tools/test_financial_impact.py -v` — verify no regressions.
  7. Run full API test suite: `pytest apps/api/tests/ -v --timeout=120` — verify no regressions across the entire backend.
  8. Grep verification: Confirm zero remaining references to `"waste"` (without `_count` suffix) as a column key in `apps/api/app/api/financial.py`, `apps/api/app/services/financial.py`, and `apps/api/tests/test_financial_api.py`.
DESIGN END

---

## TEST_SPEC: 10-3-cost-of-loss-schema-fix
**Timestamp:** 2026-02-11 08:08:39

TEST SPEC START
story_id: 10-3-cost-of-loss-schema-fix
generated: 2026-02-11

test_specifications:

## AC1: Daily Summary Query Uses Correct Column Name

### 10-3-cost-of-loss-schema-fix-UNIT-001: Cost-of-loss daily query SELECT references waste_count column
- Priority: P0
- Type: unit
- Given: An authenticated user and the `get_cost_of_loss` endpoint handler in `financial.py`
- When: The endpoint queries the `daily_summaries` table with `period=daily`
- Then: The Supabase `.select()` call includes `waste_count` in the column list (not `waste`)
- Data: Mock Supabase client; verify the string passed to `.select()` contains `waste_count`

### 10-3-cost-of-loss-schema-fix-UNIT-002: Cost-of-loss daily query extracts waste_count from record
- Priority: P0
- Type: unit
- Given: The `daily_summaries` query returns records with key `"waste_count"`
- When: The endpoint iterates over response data and calls `record.get()`
- Then: The value is extracted using key `"waste_count"` (not `"waste"`)
- And: The extracted value is passed to `calculate_waste_loss()` for cost computation
- Data: Mock response data: `[{"asset_id": "asset-1", "downtime_minutes": 60, "waste_count": 10, "financial_loss": 500.00, "oee_percentage": 75.0, "created_at": "2026-01-05T06:00:00Z"}]`

### 10-3-cost-of-loss-schema-fix-INT-001: Cost-of-loss daily endpoint returns 200 with correct waste cost
- Priority: P0
- Type: integration
- Given: An authenticated user and mock `daily_summaries` data with `waste_count: 10` and a cost center with `cost_per_unit: 20.00`
- When: `GET /api/financial/cost-of-loss?period=daily` is called
- Then: The response status is 200
- And: `breakdown.waste_cost` equals `10 * 20.00 = 200.00` (not 0)
- And: `total_loss` includes the waste cost contribution
- Data: Mock Supabase response with `{"asset_id": "asset-1", "downtime_minutes": 30, "waste_count": 10, "financial_loss": 500.00, "oee_percentage": 85.0, "created_at": "2026-02-10T06:00:00Z"}`; mock cost center `{"asset_id": "asset-1", "standard_hourly_rate": 100.00, "cost_per_unit": 20.00}`

### 10-3-cost-of-loss-schema-fix-INT-002: Cost-of-loss daily endpoint does not produce 500 error from wrong column
- Priority: P0
- Type: integration
- Given: An authenticated user and valid `daily_summaries` data in the database
- When: `GET /api/financial/cost-of-loss?period=daily` is called
- Then: The response status is 200 (not 500)
- And: No error is raised about a non-existent `waste` column
- Data: Standard mock daily_summaries data with `waste_count` key

### 10-3-cost-of-loss-schema-fix-UNIT-003: Cost-of-loss daily query handles null/zero waste_count gracefully
- Priority: P1
- Type: unit
- Given: A `daily_summaries` record where `waste_count` is `null` (returned as `None` by Supabase)
- When: The endpoint processes this record
- Then: `waste_count` defaults to 0 via `record.get("waste_count") or 0`
- And: `waste_cost` is calculated as 0.00
- And: No exception is raised
- Data: Mock response: `{"asset_id": "asset-1", "downtime_minutes": 30, "waste_count": null, "financial_loss": 100.00, "oee_percentage": 90.0, "created_at": "2026-02-10T06:00:00Z"}`

### 10-3-cost-of-loss-schema-fix-INT-003: Cost-of-loss with asset_id filter uses correct column
- Priority: P1
- Type: integration
- Given: An authenticated user requesting cost-of-loss filtered by `asset_id=asset-1`
- When: `GET /api/financial/cost-of-loss?period=daily&asset_id=asset-1` is called
- Then: The query still uses `waste_count` in the SELECT
- And: The response returns data only for the specified asset with correct waste calculations
- Data: Mock two assets; verify only the filtered asset appears with correct waste_cost

## AC2: Financial Summary Query Uses Correct Column Name

### 10-3-cost-of-loss-schema-fix-UNIT-004: Financial summary SELECT references waste_count column
- Priority: P0
- Type: unit
- Given: The `get_financial_summary` endpoint handler in `financial.py`
- When: The endpoint queries `daily_summaries` for the summary
- Then: The Supabase `.select()` call includes `waste_count` in the column list (not `waste`)
- Data: Mock Supabase client; verify the string passed to `.select()` contains `waste_count`

### 10-3-cost-of-loss-schema-fix-UNIT-005: Financial summary extracts waste_count and aggregates correctly
- Priority: P0
- Type: unit
- Given: Multiple `daily_summaries` records with `waste_count` values of 5, 10, and 15
- When: The endpoint aggregates `total_waste_count` across all records
- Then: `total_waste_count` equals 30 (sum of 5 + 10 + 15)
- And: The value is extracted using key `"waste_count"` (not `"waste"`)
- Data: Mock response: `[{"asset_id": "a1", "downtime_minutes": 30, "waste_count": 5, "financial_loss": 200.00}, {"asset_id": "a2", "downtime_minutes": 45, "waste_count": 10, "financial_loss": 300.00}, {"asset_id": "a3", "downtime_minutes": 60, "waste_count": 15, "financial_loss": 400.00}]`

### 10-3-cost-of-loss-schema-fix-INT-004: Financial summary endpoint returns correct total_waste_count
- Priority: P0
- Type: integration
- Given: An authenticated user and mock `daily_summaries` with known waste_count values
- When: `GET /api/financial/summary` is called
- Then: The response status is 200
- And: `total_waste_count` is the correct sum of all `waste_count` values
- And: `total_waste_loss` reflects the sum of calculated waste losses
- Data: Mock two records: `waste_count: 5` (cost_per_unit: 10.00) and `waste_count: 10` (cost_per_unit: 15.00); expected `total_waste_count: 15`, `total_waste_loss: 200.00`

### 10-3-cost-of-loss-schema-fix-UNIT-006: Financial summary handles empty daily_summaries response
- Priority: P1
- Type: unit
- Given: The `daily_summaries` query returns an empty list
- When: The endpoint aggregates waste data
- Then: `total_waste_count` is 0
- And: `total_waste_loss` is 0.00
- And: The response returns 200 with zeroed financial data
- Data: Mock response: `[]`

## AC3: Financial Impact Service Uses Correct Column Name

### 10-3-cost-of-loss-schema-fix-UNIT-007: Financial impact SELECT references waste_count column
- Priority: P0
- Type: unit
- Given: The `FinancialService.get_financial_impact()` method in `services/financial.py`
- When: It queries `daily_summaries` for an asset's date range
- Then: The Supabase `.select()` call includes `waste_count` in the column list (not `waste`)
- Data: Mock Supabase client; verify the string passed to `.select()` contains `waste_count`

### 10-3-cost-of-loss-schema-fix-UNIT-008: Financial impact extracts waste_count with correct key
- Priority: P0
- Type: unit
- Given: `daily_summaries` records containing `"waste_count": 23`
- When: `get_financial_impact()` processes the records via `record.get()`
- Then: The value is extracted using key `"waste_count"` (not `"waste"`)
- And: `total_waste` is summed correctly across all records
- Data: Mock response: `[{"asset_id": "asset-grd-005", "date": "2026-02-10", "downtime_minutes": 47, "waste_count": 23, "financial_loss": 500.00}]`

### 10-3-cost-of-loss-schema-fix-UNIT-009: Financial impact calculates waste_loss using waste_count * cost_per_unit
- Priority: P0
- Type: unit
- Given: A single `daily_summaries` record with `waste_count: 23` and a cost center with `cost_per_unit: 20.24`
- When: `get_financial_impact()` calculates the waste loss
- Then: `waste_loss` equals `23 * 20.24 = 465.52`
- And: `total_loss` includes both `downtime_loss` and `waste_loss`
- Data: Mock cost center: `{"standard_hourly_rate": 2393.62, "cost_per_unit": 20.24}`; mock record: `{"waste_count": 23, "downtime_minutes": 47}`

### 10-3-cost-of-loss-schema-fix-UNIT-010: Financial impact with multiple records sums waste_count correctly
- Priority: P1
- Type: unit
- Given: Three `daily_summaries` records with `waste_count` values of 10, 20, and 30
- When: `get_financial_impact()` aggregates waste data over the date range
- Then: `total_waste` equals 60
- And: `waste_loss` is calculated as `60 * cost_per_unit`
- Data: Mock three records across three consecutive dates; cost_per_unit: 15.00; expected waste_loss: 900.00

### 10-3-cost-of-loss-schema-fix-UNIT-011: Financial impact handles null waste_count in records
- Priority: P1
- Type: unit
- Given: A `daily_summaries` record where `waste_count` is `None`
- When: `get_financial_impact()` processes the record
- Then: `waste_count` defaults to 0
- And: `waste_loss` is 0.00 for that record
- And: No exception is raised
- Data: Mock record: `{"asset_id": "asset-1", "date": "2026-02-10", "downtime_minutes": 30, "waste_count": null, "financial_loss": 100.00}`

## AC4: Existing Tests Updated To Match Schema

### 10-3-cost-of-loss-schema-fix-UNIT-012: All test mock data uses waste_count key
- Priority: P0
- Type: unit
- Given: The test file `test_financial_api.py` with mock `daily_summaries` data
- When: A grep/search for `"waste"` (without `_count` suffix) is performed on mock data dictionaries
- Then: Zero matches are found — all mock data uses key `"waste_count"`
- Data: Grep pattern: `"waste"` excluding `"waste_count"`, `"waste_cost"`, `"waste_loss"`, `"total_waste_count"`, `"total_waste_loss"` in test files

### 10-3-cost-of-loss-schema-fix-INT-005: test_financial_summary_aggregates_data passes with waste_count mocks
- Priority: P0
- Type: integration
- Given: The `TestFinancialSummaryEndpoint.test_financial_summary_aggregates_data` test with updated mock data using `"waste_count"` keys
- When: The test is executed via `pytest apps/api/tests/test_financial_api.py::TestFinancialSummaryEndpoint::test_financial_summary_aggregates_data -v`
- Then: The test passes without any assertion failures
- And: The endpoint correctly reads `waste_count` from the mock data
- Data: Existing test data updated from `"waste": 5` to `"waste_count": 5`

### 10-3-cost-of-loss-schema-fix-INT-006: test_cost_of_loss_calculates_breakdown passes with waste_count mocks
- Priority: P0
- Type: integration
- Given: The `TestCostOfLossEndpoint.test_cost_of_loss_calculates_breakdown` test with updated mock data using `"waste_count"` keys
- When: The test is executed via `pytest apps/api/tests/test_financial_api.py::TestCostOfLossEndpoint -v`
- Then: All cost-of-loss tests pass without assertion failures
- And: `breakdown.waste_cost` is calculated correctly from the mock `waste_count` values
- Data: Existing test data updated from `"waste": 10` to `"waste_count": 10` and `"waste": 20` to `"waste_count": 20`

### 10-3-cost-of-loss-schema-fix-INT-007: Full financial API test suite passes with no regressions
- Priority: P0
- Type: integration
- Given: All changes applied (SELECT fixes, record.get() fixes, mock data fixes)
- When: `pytest apps/api/tests/test_financial_api.py -v` is executed
- Then: All tests pass (0 failures, 0 errors)
- And: No test assertions are broken by the column name change
- Data: Full test suite run

### 10-3-cost-of-loss-schema-fix-REG-001: Full API test suite has no regressions
- Priority: P0
- Type: integration
- Given: All code changes from this story are applied
- When: `pytest apps/api/tests/ -v --timeout=120` is executed
- Then: All API tests pass with 0 failures and 0 errors
- And: No tests outside `test_financial_api.py` are affected by the changes
- Data: Full API test suite

## AC5: Agent Data Source Remains Correct

### 10-3-cost-of-loss-schema-fix-UNIT-013: SupabaseDataSource.get_cost_of_loss() already uses waste_count
- Priority: P0
- Type: unit
- Given: The `SupabaseDataSource.get_cost_of_loss()` method in `apps/api/app/services/agent/data_source/supabase.py`
- When: The SELECT fields string is inspected
- Then: The select includes `waste_count` (confirmed at line 1138)
- And: No code changes have been made to this file as part of this story
- Data: Static code verification — grep for `waste_count` in supabase.py `get_cost_of_loss` method

### 10-3-cost-of-loss-schema-fix-INT-008: Agent cost-of-loss tool tests pass without changes
- Priority: P0
- Type: integration
- Given: No changes have been made to `supabase.py` or agent tool files
- When: `pytest apps/api/tests/services/agent/tools/test_cost_of_loss.py -v` is executed
- Then: All tests pass (0 failures, 0 errors)
- And: The `waste_count` field is correctly used throughout the agent data source layer
- Data: Full agent cost-of-loss test suite

### 10-3-cost-of-loss-schema-fix-INT-009: Agent financial impact tool tests pass without changes
- Priority: P1
- Type: integration
- Given: No changes have been made to agent tool files
- When: `pytest apps/api/tests/services/agent/tools/test_financial_impact.py -v` is executed
- Then: All tests pass (0 failures, 0 errors)
- Data: Full agent financial impact test suite

edge_cases:
  - Null/None waste_count value in daily_summaries record — should default to 0 via `or 0` pattern, not raise exception
  - Empty daily_summaries response (no records returned) — totals should all be 0.00
  - Mixed records where some have waste_count=0 and others have positive values — only positive values should contribute to totals
  - Large waste_count values (e.g., 999999) — should not overflow or cause precision issues in Decimal calculations
  - Records with waste_count but no matching cost_center (no cost_per_unit) — should use default rate, waste_loss should still calculate

error_scenarios:
  - Supabase query failure (connection error) — should return 500/503 with error message, not crash
  - Invalid period parameter (e.g., period=weekly) — should return 400 or fall through to default daily behavior
  - Unauthenticated request — should return 401 before any query is attempted
  - cost_per_unit is None/null for an asset — waste_loss should be 0.00 for that asset (defensive calculation)

test_file_mapping:
  - 10-3-cost-of-loss-schema-fix-UNIT-*: apps/api/tests/test_financial_api.py
  - 10-3-cost-of-loss-schema-fix-INT-*: apps/api/tests/test_financial_api.py
  - 10-3-cost-of-loss-schema-fix-REG-001: apps/api/tests/ (full suite)
  - 10-3-cost-of-loss-schema-fix-INT-008: apps/api/tests/services/agent/tools/test_cost_of_loss.py
  - 10-3-cost-of-loss-schema-fix-INT-009: apps/api/tests/services/agent/tools/test_financial_impact.py

TEST SPEC END

---
