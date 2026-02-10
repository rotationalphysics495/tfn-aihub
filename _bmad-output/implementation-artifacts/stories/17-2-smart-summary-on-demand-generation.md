# Story 17.2: Smart Summary On-Demand Generation for Historical Dates

Status: ready-for-dev

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
