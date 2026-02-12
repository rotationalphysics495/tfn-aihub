# Story 17.2: Smart Summary On-Demand Generation for Historical Dates

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Plant Manager,
I want to generate a smart summary for a historical date that doesn't have one,
so that I can get AI analysis even when reviewing past reports.

## Acceptance Criteria

1. **Given** the user navigates to a historical date that has production data but no saved smart summary, **When** the summary section loads, **Then** a prompt is shown: "No summary exists for this date. Generate one?" and a "Generate Summary" button is displayed.

2. **Given** the user clicks "Generate Summary", **When** the summary generation API is called, **Then** a loading indicator shows while the summary is being generated, **And** once complete the summary appears in the normal summary section, **And** the summary is saved for future viewing of this date.

3. **Given** a summary already exists for the selected historical date, **When** the report loads, **Then** the existing summary is displayed immediately (no generation prompt).

4. **Given** a "Regenerate" option is available on existing summaries, **When** the user clicks "Regenerate", **Then** the summary is re-generated from current data and replaces the prior version.

5. **Given** the summary generation fails (e.g., no production data, API error), **When** the error occurs, **Then** a user-friendly error message is displayed with a retry option, **And** the page remains functional.

## Tasks / Subtasks

- [ ] Task 1: Update `useSmartSummary` hook to support on-demand generation mode (AC: #1, #2, #5)
  - [ ] 1.1 Add `autoGenerate` option (default `true` for yesterday, `false` for historical dates)
  - [ ] 1.2 Expose new `generate()` method for manual trigger alongside existing `regenerate()`
  - [ ] 1.3 Add `hasSummary`, `hasProductionData`, and `canGenerate` computed booleans
  - [ ] 1.4 Handle 404 response without auto-generating when `autoGenerate` is `false`
  - [ ] 1.5 Track `isGenerating` state separately from `isLoading` for proper UI feedback
- [ ] Task 2: Update `MorningSummarySection` to show generation prompt for historical dates (AC: #1, #2, #3)
  - [ ] 2.1 Accept optional `date` prop and pass it to `useSmartSummary({ reportDate: date })`
  - [ ] 2.2 Add "no summary" state with "Generate Summary" button when `!hasSummary && !isLoading`
  - [ ] 2.3 Show loading/generating animation when `isGenerating` is true
  - [ ] 2.4 Display existing summary immediately when `hasSummary` is true (existing behavior)
  - [ ] 2.5 Ensure "Regenerate" button remains visible for existing summaries (AC: #4)
- [ ] Task 3: Wire date from page-level state into MorningSummarySection (AC: #1, #3)
  - [ ] 3.1 Update `MorningSummarySection` to accept `reportDate?: string` prop
  - [ ] 3.2 Pass `reportDate` to both `useDailyActions({ reportDate })` and `useSmartSummary({ reportDate })`
  - [ ] 3.3 Ensure hook re-fetches when `reportDate` changes (dependency array)
- [ ] Task 4: Error handling and edge cases (AC: #5)
  - [ ] 4.1 Handle generation failure with clear error message and retry button
  - [ ] 4.2 Handle "no production data" case (date exists but no `daily_summaries` records)
  - [ ] 4.3 Handle network errors during generation with appropriate messaging
  - [ ] 4.4 Ensure component remains interactive during and after errors
- [ ] Task 5: Testing (AC: all)
  - [ ] 5.1 Unit test `useSmartSummary` with `autoGenerate: false` (historical mode)
  - [ ] 5.2 Unit test `useSmartSummary` manual `generate()` flow
  - [ ] 5.3 Component test: "Generate Summary" button renders when no summary exists
  - [ ] 5.4 Component test: loading state during generation
  - [ ] 5.5 Component test: error state with retry functionality

## Dev Notes

### Context: Dependency on Story 17.1

This story is designed to work alongside Story 17.1 (Date Picker on Morning Report). Story 17.1 introduces the date picker and URL-based `date` parameter that feeds into this story. However, this story's changes are **self-contained** to the summary section and hook layer -- the `useSmartSummary` hook already accepts a `reportDate` option, and `MorningSummarySection` just needs to receive and pass it through.

If Story 17.1 is not yet implemented, this story's changes will still work correctly for yesterday's date (the default behavior). The `reportDate` prop on `MorningSummarySection` simply won't be passed until the date picker exists.

### Key Behavioral Change

**Current behavior:** When `useSmartSummary` gets a 404 (no cached summary), it immediately auto-triggers generation via `POST /api/summaries/generate`. This is correct for yesterday's date (T-1) since the morning report should always have a summary.

**New behavior for historical dates:** When viewing a historical date, a 404 should NOT auto-trigger generation. Instead, it should surface the "no summary" state and let the user decide whether to generate one. This is because generating summaries has a cost (LLM tokens) and historical dates may not always warrant automatic generation.

**Implementation approach:** Add an `autoGenerate` option to `useSmartSummary`. When `autoGenerate: false`, a 404 response sets `hasSummary: false` without triggering generation. The component then shows the generation prompt. When the user clicks "Generate Summary", it calls the exposed `generate()` method which hits `POST /api/summaries/generate`.

### Backend: No Changes Needed

The backend already fully supports this story:
- `GET /api/summaries/smart/{date}` -- returns cached summary or 404 if none exists
- `GET /api/summaries/smart/{date}?regenerate=true` -- force regenerates
- `POST /api/summaries/generate` -- generates summary for a given date with `{ target_date, regenerate }` body

All three endpoints accept arbitrary dates and are protected with JWT auth. No backend modifications are required.

### Project Structure Notes

- All changes are frontend-only in the `apps/web/` package
- Follow existing hook pattern in `apps/web/src/hooks/useSmartSummary.ts` (already uses `useState`, `useCallback`, `useRef` for mounted checks, Supabase auth for JWT)
- Follow existing component pattern in `apps/web/src/components/action-list/MorningSummarySection.tsx`
- Use existing UI primitives: `Button` from `@/components/ui/button`, `Card`/`CardContent` from `@/components/ui/card`
- Use existing Lucide icons already imported: `Sparkles`, `RefreshCw`, `AlertCircle`
- Add `Play` or `Wand2` icon from lucide-react for the "Generate Summary" button

### Technical Requirements

| Requirement | Detail |
|-------------|--------|
| **Framework** | Next.js 14+ with App Router, TypeScript 5.x |
| **UI Library** | Shadcn/UI + Radix UI primitives |
| **Styling** | Tailwind CSS 3.4+ utility classes |
| **Auth** | JWT Bearer token via Supabase `session.access_token` |
| **API URL** | `process.env.NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) |
| **State** | React hooks (`useState`, `useCallback`, `useRef`) -- no external state library |
| **Testing** | Vitest + React Testing Library |

### Architecture Compliance

- **Auth pattern:** Use `createClient()` from `@/lib/supabase/client` to get session, pass `Authorization: Bearer ${token}` header. Never use cookie-based auth (`credentials: 'include'`).
- **API calls:** Use native `fetch()` with explicit headers (matches existing pattern in both hooks).
- **Component pattern:** `'use client'` directive at top of file. Export named function component.
- **Error handling:** Graceful degradation with user-friendly messages. Never expose raw API errors.
- **Mounted ref pattern:** Use `useRef(true)` with cleanup in `useEffect` return to prevent state updates on unmounted components (already implemented in both hooks).

### Existing Code to Reuse (DO NOT Reinvent)

| What | Location | Notes |
|------|----------|-------|
| `useSmartSummary` hook | `apps/web/src/hooks/useSmartSummary.ts` | **Modify** -- do not create a new hook |
| `MorningSummarySection` | `apps/web/src/components/action-list/MorningSummarySection.tsx` | **Modify** -- add generation prompt UI |
| `SmartSummaryData` type | `apps/web/src/hooks/useSmartSummary.ts` (lines 16-33) | Reuse as-is |
| `UseSmartSummaryReturn` type | `apps/web/src/hooks/useSmartSummary.ts` (lines 51-58) | **Extend** with `generate()` and `canGenerate` |
| Auth pattern | `useSmartSummary.ts` lines 90-100 | Copy exactly |
| Loading skeleton | `SummarySkeleton` from `./ActionListSkeleton` | Reuse for loading state |
| `cleanSummaryText()` | `MorningSummarySection.tsx` lines 51-56 | Reuse for summary display |
| `ReactMarkdown` + `remarkGfm` | Already imported in `MorningSummarySection.tsx` | Reuse for summary rendering |
| `Button` component | `@/components/ui/button` | Use for "Generate Summary" button |
| `cn()` utility | `@/lib/utils` | Use for conditional class names |

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `apps/web/src/hooks/useSmartSummary.ts` | **Modify** | Add `autoGenerate` option, expose `generate()` method, add `canGenerate` boolean |
| `apps/web/src/components/action-list/MorningSummarySection.tsx` | **Modify** | Accept `reportDate` prop, show generation prompt when no summary exists, wire up generate button |

### Specific Implementation Guidance

#### useSmartSummary.ts Changes

1. Add to `UseSmartSummaryOptions`:
   ```typescript
   /** Auto-generate if no cached summary (default: true for T-1, set false for historical) */
   autoGenerate?: boolean
   ```

2. Add `generate` method (similar to `regenerateSummary` but calls `POST /api/summaries/generate`):
   ```typescript
   const generateSummary = useCallback(async () => {
     // Same auth pattern as fetchSummary
     // POST to /api/summaries/generate with { target_date: date, regenerate: false }
     // Update state on success
   }, [apiUrl, reportDate])
   ```

3. Modify `fetchSummary` -- in the 404 handler (line ~121), check `autoGenerate`:
   ```typescript
   if (response.status === 404) {
     if (autoGenerate !== false) {
       // Current behavior: auto-trigger generation
     } else {
       // New behavior: just set state to indicate no summary
       setState(prev => ({ ...prev, isLoading: false, isGenerating: false, error: null }))
       return
     }
   }
   ```

4. Extend return type:
   ```typescript
   return {
     ...state,
     refetch: fetchSummary,
     regenerate: regenerateSummary,
     generate: generateSummary,  // NEW
     hasSummary: state.data !== null,
     canGenerate: !state.data && !state.isLoading && !state.isGenerating,  // NEW
   }
   ```

#### MorningSummarySection.tsx Changes

1. Update props interface:
   ```typescript
   interface MorningSummarySectionProps {
     className?: string
     reportDate?: string  // NEW: YYYY-MM-DD format
   }
   ```

2. Pass `reportDate` to hooks:
   ```typescript
   const { data, isLoading, summary } = useDailyActions({ reportDate })
   const { data: smartSummary, isLoading: isSummaryLoading, isGenerating, error: summaryError, refetch: refetchSummary, regenerate: regenerateSummary, generate: generateSummary, hasSummary, canGenerate } = useSmartSummary({ reportDate, autoGenerate: !reportDate })
   ```

3. Add new UI state between the error state and the "no summary" fallback (around line 263):
   ```tsx
   {/* On-demand generation prompt for historical dates */}
   {!isSummaryLoading && !isGenerating && !summaryError && !hasSummary && canGenerate && (
     <div className="text-center py-3">
       <p className="text-sm text-muted-foreground mb-2">
         No summary exists for this date.
       </p>
       <Button
         variant="outline"
         size="sm"
         onClick={() => generateSummary()}
         className="gap-2"
       >
         <Wand2 className="w-4 h-4" />
         Generate Summary
       </Button>
     </div>
   )}
   ```

### Testing Requirements

- **Vitest** for unit tests, **React Testing Library** for component tests
- Test files go in `apps/web/src/hooks/__tests__/` and `apps/web/src/components/action-list/__tests__/`
- Mock `fetch` and `createClient` from `@/lib/supabase/client`
- Key test scenarios:
  - Hook returns `hasSummary: false, canGenerate: true` on 404 with `autoGenerate: false`
  - Hook auto-generates on 404 when `autoGenerate: true` (existing behavior preserved)
  - `generate()` calls `POST /api/summaries/generate` with correct date and headers
  - Component shows "Generate Summary" button when `canGenerate` is true
  - Component shows loading indicator during generation
  - Component shows error with retry on failure

### References

- [Source: _bmad-output/planning-artifacts/epic-17.md#Story 17.2] - Story requirements and acceptance criteria
- [Source: apps/web/src/hooks/useSmartSummary.ts] - Existing hook with auto-generation on 404
- [Source: apps/web/src/components/action-list/MorningSummarySection.tsx] - Existing component with summary display states
- [Source: apps/api/app/api/summaries.py] - Backend endpoints for smart summary (GET, POST, DELETE)
- [Source: apps/web/src/hooks/useDailyActions.ts] - Date parameter passing pattern
- [Source: docs/architecture-web.md] - Frontend architecture, component organization, tech stack
- [Source: docs/architecture-api.md] - Backend architecture, API patterns, auth pattern
- [Source: docs/api-contracts.md] - API endpoint contracts and response formats
- [Source: _bmad-output/planning-artifacts/epics-improvements.md#FR-I10] - FR-I10 Report History requirement

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Implementation Summary

Added on-demand smart summary generation for historical dates. When a user navigates to a historical date that has no cached summary, instead of auto-triggering generation (which costs LLM tokens), the UI shows a "Generate Summary" prompt with a button. Clicking the button manually triggers generation via POST /api/summaries/generate. Existing T-1 (yesterday) behavior is preserved — auto-generation on 404 still works by default.

### Files Created
- `apps/web/src/hooks/__tests__/useSmartSummary.test.ts` — 11 unit tests for hook: autoGenerate behavior, generate() method, error handling, unmount safety
- `apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx` — 10 component tests: generation prompt UI, loading states, error handling with retry, existing summary display

### Files Modified
- `apps/web/src/hooks/useSmartSummary.ts` — Added `autoGenerate` option (default: true), `generate()` method for manual on-demand generation, `canGenerate` computed boolean. Modified 404 handler to skip auto-generation when `autoGenerate: false`.
- `apps/web/src/components/action-list/MorningSummarySection.tsx` — Added Wand2 icon and Button imports, destructured `generate`/`canGenerate` from hook, passes `autoGenerate: false` when `reportDate` is provided, added on-demand generation prompt UI with "Generate Summary" button, updated error retry to use `generate()` vs `refetch()` depending on `canGenerate` state.

### Key Decisions
- `autoGenerate` defaults to `true` in the hook, preserving existing T-1 behavior. The component sets it to `false` only when a `reportDate` prop is explicitly passed (indicating historical date navigation from Story 17.1).
- The `generate()` method is a separate useCallback from `regenerate()` — generate POSTs to `/api/summaries/generate` with `regenerate: false`, while regenerate GETs with `?regenerate=true`. This maintains the existing API contract.
- Error retry in the component checks `canGenerate` to decide whether to call `generateSummary()` or `refetchSummary()` — this ensures that if a generation fails, the retry button triggers generation again rather than just re-fetching (which would still 404).
- The "no summary" fallback (previously always shown) is now split into two states: `canGenerate` (shows generation prompt) and `!canGenerate` (shows generic "No AI summary available" text).

### Tests Added
- `apps/web/src/hooks/__tests__/useSmartSummary.test.ts` — Tests: Bearer token auth, hasSummary on 200, auto-generate on 404 (default), no auto-generate on 404 with autoGenerate=false, generate() POST call, generate() success state update, generate() error handling, generate() network error, generate() expired session, regenerate() still works, unmount safety
- `apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx` — Tests: generate button renders when canGenerate, no generate button when hasSummary, autoGenerate=false passed with reportDate, no autoGenerate when no reportDate, clicking generate calls function, loading state during generation, existing summary display, regenerate button visible, error retry calls generate vs refetch

### Notes for Reviewer
- Pre-existing test failures exist in `src/__tests__/action-list.test.tsx` (cleanSummaryText receives undefined summary_text) — confirmed these failures exist on the base branch before this story's changes.
- No backend changes needed — all three endpoints (`GET /smart/{date}`, `GET /smart/{date}?regenerate=true`, `POST /generate`) already support arbitrary dates.
- No new npm dependencies added — Wand2 icon is available in existing lucide-react v0.312.0.

### Test Results
```
 ✓ src/hooks/__tests__/useSmartSummary.test.ts  (11 tests) 547ms
 ✓ src/components/action-list/__tests__/MorningSummarySection.test.tsx  (10 tests) 74ms

 Test Files  2 passed (2)
      Tests  21 passed (21)
```

### Acceptance Criteria Status
- [x] AC1 - Historical date with no summary shows generation prompt — implemented in MorningSummarySection.tsx (generation prompt UI) and useSmartSummary.ts (autoGenerate=false skips auto-generation on 404)
- [x] AC2 - Generate button triggers API, shows loading, saves result — implemented in useSmartSummary.ts (generate() method POSTs to /api/summaries/generate) and MorningSummarySection.tsx (button onClick, existing isGenerating loading block)
- [x] AC3 - Existing summary displayed immediately — existing behavior preserved in MorningSummarySection.tsx (hasSummary=true renders summary, no generation prompt)
- [x] AC4 - Regenerate option on existing summaries — already implemented, no changes needed (regenerate button at MorningSummarySection.tsx)
- [x] AC5 - Error handling with retry — implemented in useSmartSummary.ts (generate() catches errors) and MorningSummarySection.tsx (retry button calls generate or refetch based on canGenerate state)

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-12
**Diff Size**: 922 lines (+922, -10)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | `response.ok \|\| response.status === 201` is redundant (`ok` already includes 201) — pre-existing pattern copied forward | LOW | Documented |
| 2 | Auth boilerplate duplicated across `fetchSummary`, `regenerateSummary`, `generateSummary` — pre-existing pattern, not introduced by this story | LOW | Documented |
| 3 | "Generate Summary" button not `disabled` during `isGenerating`, allowing potential double-click race | MEDIUM | Fixed |
| 4 | `generateSummary` missing 401 status handling (unlike `fetchSummary`) — user would see generic error instead of "Session expired" | MEDIUM | Fixed |
| 5 | No test for double-click / concurrent generation guard | LOW | Documented |
| 6 | `reportDate` not validated as YYYY-MM-DD before API URL interpolation | LOW | Documented |
| 7 | Component line 84 is 230+ chars, hard to read | LOW | Documented |

**Totals**: 0 HIGH, 2 MEDIUM (fixed), 5 LOW (documented)

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 3 | Added `disabled={isGenerating}` prop to Generate Summary Button in MorningSummarySection.tsx | Tests pass (21/21) |
| 4 | Added `if (response.status === 401) throw new Error('Session expired...')` to `generateSummary` in useSmartSummary.ts | Tests pass (21/21) |

### Remaining Issues (Low Severity)
- Issue #1: Redundant `response.ok || response.status === 201` check — pre-existing pattern, consider cleanup in tech-debt sprint
- Issue #2: Auth boilerplate duplication — consider extracting shared auth helper when touching these functions next
- Issue #5: Missing double-click guard test — could be added in future test improvements
- Issue #6: Date format validation — backend validates, low risk for internal calls
- Issue #7: Long line in component — cosmetic, no functional impact

### Final Status
Approved with fixes

## Test Quality Review

**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 21 (11 unit + 10 component)
**Reviewer**: Test Architect Agent
**Date**: 2026-02-12

### Files Reviewed
- `apps/web/src/hooks/__tests__/useSmartSummary.test.ts` (461 lines, 11 tests)
- `apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx` (328 lines, 10 tests)

### Criteria Results

| # | Criterion | useSmartSummary.test | MorningSummarySection.test |
|---|-----------|---------------------|---------------------------|
| 1 | BDD Format | PASS | PASS |
| 2 | Test IDs | WARN — no formal IDs | WARN — no formal IDs |
| 3 | Hard Waits | PASS | PASS |
| 4 | Determinism | PASS | PASS |
| 5 | Isolation & Cleanup | PASS | PASS |
| 6 | Explicit Assertions | PASS | PASS |
| 7 | Test Length | WARN — 461 lines | PASS — 328 lines |
| 8 | Test Duration | PASS — 549ms | PASS — 69ms |
| 9 | Fixture Patterns | PASS — excellent | PASS — excellent |
| 10 | Data Factories | PASS — with overrides | PASS — with overrides |
| 11 | Network-First | N/A (mocked) | N/A (mocked) |
| 12 | Flakiness | PASS | PASS |

### Issues Found
- 0 Critical
- 0 High (test IDs missing but offset by excellent BDD naming)
- 0 Medium
- 2 Low: Missing formal test IDs (e.g., `17-2-UNIT-001`) — documented for future convention adoption

### Strengths
- Excellent factory pattern with override support in both files
- Perfect mock isolation with `beforeEach`/`afterEach` cleanup
- Well-organized describe blocks mapping to acceptance criteria
- Unmount safety test in hook tests (prevents memory leaks)
- Error and edge case coverage (network errors, expired sessions, retry flows)

### Fixes Applied
None required — no critical or high issues identified.
