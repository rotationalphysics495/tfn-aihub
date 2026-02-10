# Story 10.1: Safety Alerts Auth Fix

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **safety alerts to load correctly on the dashboard**,
so that **I can see active safety events without encountering 403 errors**.

## Acceptance Criteria

1. **Bearer Token Auth Pattern**
   - Given an authenticated user is viewing the dashboard
   - When the safety alerts component loads
   - Then the API request includes a `Bearer` token in the `Authorization` header (not `credentials: 'include'`)
   - And safety events are displayed without 403 errors

2. **Expired Session Handling**
   - Given the user's session has expired
   - When the safety alerts component attempts to fetch data
   - Then the request fails gracefully with an auth error message
   - And no confusing 403 error is shown to the user

3. **Acknowledge Endpoint Auth Fix**
   - Given an authenticated user acknowledges a safety alert
   - When the POST request is sent to `/api/safety/acknowledge/:id`
   - Then the request includes a `Bearer` token in the `Authorization` header
   - And the acknowledgement succeeds without 403 errors

4. **Consistency With Other Hooks**
   - The `useSafetyAlerts` hook follows the identical auth pattern used in `useDailyActions`, `useLivePulse`, and `useCostOfLoss`
   - Specifically: `createClient()` -> `getSession()` -> `Authorization: Bearer ${session.access_token}`
   - The `credentials: 'include'` option is removed from all fetch calls

## Tasks / Subtasks

- [ ] Task 1: Fix `fetchAlerts` auth pattern (AC: #1, #2, #4)
  - [ ] 1.1 Add `import { createClient } from '@/lib/supabase/client'` to `useSafetyAlerts.ts`
  - [ ] 1.2 In `fetchAlerts`, call `createClient()` and `supabase.auth.getSession()` to obtain the access token
  - [ ] 1.3 Add early return with auth error state if `!session?.access_token`
  - [ ] 1.4 Replace `credentials: 'include'` with `'Authorization': \`Bearer ${session.access_token}\`` in the fetch headers
  - [ ] 1.5 Remove the `credentials: 'include'` line entirely from the GET fetch call

- [ ] Task 2: Fix `acknowledge` auth pattern (AC: #3, #4)
  - [ ] 2.1 In `acknowledge`, call `createClient()` and `supabase.auth.getSession()` to obtain the access token
  - [ ] 2.2 Add early return (`return false`) if `!session?.access_token`
  - [ ] 2.3 Replace `credentials: 'include'` with `'Authorization': \`Bearer ${session.access_token}\`` in the POST fetch headers
  - [ ] 2.4 Remove the `credentials: 'include'` line entirely from the POST fetch call

- [ ] Task 3: Verify and test (AC: #1-4)
  - [ ] 3.1 Verify TypeScript compiles without errors (`npx tsc --noEmit` or build)
  - [ ] 3.2 Confirm no other files in the codebase use `credentials: 'include'` for API calls (search for stragglers)
  - [ ] 3.3 Verify the hook's public API (`UseSafetyAlertsReturn`) is unchanged -- no breaking changes to consumers

## Dev Notes

### Bug Analysis

**Root Cause:** The `useSafetyAlerts.ts` hook was implemented using `credentials: 'include'` (cookie-based auth) while the API expects JWT Bearer token authentication via the `Authorization` header. All other hooks in the application use the correct Bearer token pattern. This mismatch causes 403 Forbidden errors when the safety alerts component tries to load data.

**Scope:** Single-file fix in `apps/web/src/hooks/useSafetyAlerts.ts`. Two fetch calls need updating: `fetchAlerts` (GET) and `acknowledge` (POST).

### Architecture Patterns

- **Frontend Framework:** Next.js with React hooks (`'use client'` directive)
- **Auth Provider:** Supabase Auth via `@supabase/ssr`
- **Auth Pattern:** All API calls must use `Authorization: Bearer ${session.access_token}` -- NOT cookies
- **Supabase Client:** Import `createClient` from `@/lib/supabase/client` (uses `createBrowserClient` from `@supabase/ssr`)

### Correct Auth Pattern (Reference Implementation)

The exact pattern from `useDailyActions.ts` (lines 123-148) that MUST be replicated:

```typescript
import { createClient } from '@/lib/supabase/client'

// Inside the fetch callback:
const supabase = createClient()
const { data: { session } } = await supabase.auth.getSession()

if (!session?.access_token) {
  setState(prev => ({
    ...prev,
    isLoading: false,
    error: 'Authentication required',  // or appropriate error message
  }))
  return
}

const response = await fetch(url, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  },
})
```

### Current Broken Code (Lines 84-91 in useSafetyAlerts.ts)

```typescript
// BUG: Uses credentials: 'include' instead of Bearer token
const response = await fetch(`${apiUrl}/api/safety/active`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',  // WRONG - must use Authorization header
})
```

The same bug also exists in the `acknowledge` function (lines 123-130):

```typescript
// BUG: Same credentials: 'include' issue
const response = await fetch(`${apiUrl}/api/safety/acknowledge/${eventId}`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',  // WRONG - must use Authorization header
  body: JSON.stringify({}),
})
```

### Critical Guardrails

- **DO NOT** change any exported interfaces (`SafetyAlert`, `SafetyAlertsState`, `UseSafetyAlertsReturn`, etc.)
- **DO NOT** change the hook's public API, return type, or function signatures
- **DO NOT** modify the polling logic, the `useSafetyAlertCount` wrapper, or any other functionality
- **DO NOT** add new dependencies -- `@/lib/supabase/client` is already available in the project
- **DO** follow the exact same pattern as `useDailyActions.ts` for session retrieval and error handling
- **DO** remove `credentials: 'include'` from BOTH fetch calls (fetchAlerts and acknowledge)

### Project Structure Notes

```
apps/web/src/
  hooks/
    useSafetyAlerts.ts      # FIX - auth pattern (this story)
    useDailyActions.ts       # REFERENCE - correct auth pattern
    useLivePulse.ts          # REFERENCE - correct auth pattern
    useCostOfLoss.ts         # REFERENCE - correct auth pattern
  lib/
    supabase/
      client.ts              # Supabase browser client factory (already exists)
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `apps/web/src/hooks/useSafetyAlerts.ts` | MODIFY | Fix auth from `credentials: 'include'` to Bearer token pattern |

No new files need to be created. This is a single-file bug fix.

### Testing Guidance

**Manual Verification:**
1. Build the web app (`npm run build` or `npx next build` in apps/web) -- should compile with zero errors
2. Verify no TypeScript type errors in the modified file
3. Grep the codebase for any remaining `credentials: 'include'` patterns that should be fixed

**Automated Testing:**
- No new unit tests required for a bug fix of this scope
- The existing safety alerts component tests (if any) should continue to pass
- TypeScript compilation is the primary validation gate

### References

- [Source: _bmad-output/planning-artifacts/epic-10.md#Story 10.1] - Story requirements and acceptance criteria
- [Source: apps/web/src/hooks/useSafetyAlerts.ts] - File containing the bug (credentials: 'include' on lines 90, 129)
- [Source: apps/web/src/hooks/useDailyActions.ts#L123-L148] - Reference implementation of correct Bearer token auth pattern
- [Source: apps/web/src/hooks/useLivePulse.ts#L124-L142] - Another reference of correct auth pattern
- [Source: apps/web/src/hooks/useCostOfLoss.ts#L75-L97] - Another reference of correct auth pattern
- [Source: apps/web/src/lib/supabase/client.ts] - Supabase browser client factory

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
