# Epic 17 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 17
**Started:** 2026-02-12 04:42:34

---


## DESIGN: 17-1-date-picker-on-morning-report
**Timestamp:** 2026-02-12 04:48:29

DESIGN START
story_id: 17-1-date-picker-on-morning-report

files_to_modify:
  - path: apps/web/src/components/ui/calendar.tsx
    action: create
    purpose: Shadcn Calendar component wrapping react-day-picker (generated via npx shadcn-ui add)

  - path: apps/web/src/components/ui/popover.tsx
    action: create
    purpose: Shadcn Popover component wrapping @radix-ui/react-popover (generated via npx shadcn-ui add)

  - path: apps/web/src/components/report/DateNavigation.tsx
    action: create
    purpose: Date picker + prev/next arrows component for navigating report dates

  - path: apps/web/src/components/report/index.ts
    action: create
    purpose: Barrel export for report components

  - path: apps/web/src/app/(main)/morning-report/MorningReportClient.tsx
    action: create
    purpose: Client component wrapper managing date state, URL sync, and threading reportDate to all child components

  - path: apps/web/src/app/(main)/morning-report/page.tsx
    action: modify
    purpose: Replace inline JSX with MorningReportClient component (keep as Server Component for metadata export)

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: Add reportDate prop, pass to useDailyActions/useSmartSummary hooks, add dynamic badge text, integrate DateNavigation

  - path: apps/web/src/components/action-engine/InsightEvidenceCardList.tsx
    action: modify
    purpose: Add reportDate prop, pass to useDailyActions hook

  - path: apps/web/src/components/action-list/index.ts
    action: modify
    purpose: No change needed — MorningSummarySection export already exists, props are additive

  - path: apps/web/package.json
    action: modify
    purpose: New dependencies react-day-picker and date-fns added via shadcn-ui CLI

  - path: apps/web/src/components/report/__tests__/DateNavigation.test.tsx
    action: create
    purpose: Unit tests for DateNavigation component

  - path: apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx
    action: create
    purpose: Integration tests for date URL sync and date threading

patterns_to_use:
  - Shadcn Calendar+Popover: Standard Shadcn composition pattern with Calendar inside Popover, matching existing Shadcn usage (Button, Card, Badge, Dialog, etc.)
  - Server/Client Component split: page.tsx stays Server Component (exports metadata), MorningReportClient.tsx is 'use client' wrapper — follows Next.js 14 App Router best practice. No existing wrapper pattern in codebase, but this is the standard Next.js approach.
  - URL state sync: useSearchParams() to read, useRouter().push() with { scroll: false } for shallow updates — same pattern as ActivePlanBadge tests mock (next/navigation)
  - Hook date threading: Existing hooks (useDailyActions, useSmartSummary, useWorkcenterSummary, useScheduleAttainment) all accept optional date params. Just pass the selected date down as props.
  - Barrel exports: New components/report/index.ts follows same pattern as components/action-list/index.ts and components/action-engine/index.ts
  - Vitest + Testing Library: Test files in __tests__/ directories adjacent to components, vi.mock for next/navigation, same structure as ActivePlanBadge.test.tsx

dependencies:
  - react-day-picker: needs-install (via npx shadcn-ui add calendar)
  - date-fns: needs-install (peer dependency of react-day-picker, installed by shadcn)
  - @radix-ui/react-popover: installed (v1.1.6 in package.json)
  - lucide-react: installed (v0.312.0 — has CalendarIcon, ChevronLeft, ChevronRight)

acceptance_criteria_mapping:
  - AC1 (Date picker placement): DateNavigation.tsx renders Calendar+Popover+arrows, integrated into MorningSummarySection header next to the badge. MorningSummarySection.tsx modified to accept reportDate, onDateChange props and render DateNavigation in the header div.
  - AC2 (Date change reloads all data): MorningReportClient.tsx maintains selectedDate state, passes formatted YYYY-MM-DD string as reportDate prop to MorningSummarySection, InsightEvidenceCardList, WorkcenterScorecard, and ScheduleAttainment. Each component passes date to its hook. URL updates via router.push with ?date= param. Badge in MorningSummarySection becomes dynamic — "T-1 Data" when yesterday, "Feb 5 Data" otherwise.
  - AC3 (Prev/next day arrows): DateNavigation.tsx includes ChevronLeft/ChevronRight buttons. onDateChange callback increments/decrements by 1 day. "Next" button disabled when selectedDate >= yesterday. Future dates disabled in Calendar via disabled prop.
  - AC4 (URL-driven date on load): MorningReportClient.tsx reads searchParams.get('date') on mount, validates format and range (not future, valid ISO date), initializes selectedDate state. Invalid/missing/future dates fall back to yesterday.
  - AC5 (Empty state for missing data): MorningReportClient.tsx checks if useDailyActions returns null/empty data (no actions and error indicates no data). Shows "No production data available for {formatted date}" message. DateNavigation and navigation arrows remain interactive since they're controlled by MorningReportClient state, not data availability.

risks:
  - Shadcn CLI version mismatch: The CLI command is `npx shadcn-ui@latest add calendar popover`. If the project uses a different shadcn setup or has custom component paths, the generated files may need manual adjustment. Mitigation: verify components.json or shadcn config exists in apps/web/.
  - WorkcenterScorecard and ScheduleAttainment date threading: The story explicitly says "all report sections" reload. These components use useWorkcenterSummary({ date }) and useScheduleAttainment({ date }) which already support date params, but the story tasks only mention MorningSummarySection and InsightEvidenceCardList. Both production components MUST also receive the date prop to satisfy AC#2 fully.
  - Suspense boundary for useSearchParams: Next.js 14 App Router requires useSearchParams() to be wrapped in a Suspense boundary to avoid the entire page becoming client-rendered. MorningReportClient uses useSearchParams, so page.tsx should wrap it in <Suspense>. Mitigation: add <Suspense fallback={<MorningReportLoading />}> in page.tsx.
  - date-fns bundle size: react-day-picker v8+ uses date-fns internally. Tree-shaking should handle it, but worth verifying build size doesn't spike. Mitigation: import only specific date-fns functions (format from 'date-fns').
  - Timezone handling: Date arithmetic using new Date() and toISOString().split('T')[0] could yield wrong dates near midnight depending on timezone. Mitigation: use date-fns format/subDays/addDays which handle local dates correctly, or use the same getYesterday() pattern already in the hooks.

estimated_test_files:
  - apps/web/src/components/report/__tests__/DateNavigation.test.tsx: Renders date picker trigger with formatted date, opens calendar popover on click, prev/next arrows work, next arrow disabled when date >= yesterday, future dates disabled in calendar, calls onDateChange with correct date
  - apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx: Reads date from URL param, defaults to yesterday when no param, handles invalid/future date params gracefully, updates URL on date change via router.push, threads reportDate to all child components, shows empty state when no data for selected date

implementation_order:
  1. Install Shadcn Calendar + Popover components (npx shadcn-ui@latest add calendar popover in apps/web/) — creates calendar.tsx, popover.tsx, installs react-day-picker + date-fns
  2. Create DateNavigation component (apps/web/src/components/report/DateNavigation.tsx) with Calendar+Popover+prev/next arrows, props interface { date: Date; onDateChange: (date: Date) => void }, disable future dates and next arrow when >= yesterday
  3. Create barrel export (apps/web/src/components/report/index.ts)
  4. Create MorningReportClient.tsx — 'use client' wrapper with date state from useSearchParams, URL sync via router.push, date validation, and date threading to all children
  5. Modify page.tsx — replace inline JSX with <Suspense><MorningReportClient /></Suspense>, keep metadata export
  6. Modify MorningSummarySection.tsx — add reportDate prop, pass to useDailyActions({ reportDate }) and useSmartSummary({ reportDate }), dynamic badge text (T-1 vs formatted date), integrate DateNavigation in header, accept onDateChange prop
  7. Modify InsightEvidenceCardList.tsx — add reportDate prop, pass to useDailyActions({ reportDate })
  8. Thread reportDate to WorkcenterScorecard and ScheduleAttainment (add reportDate prop, pass to useWorkcenterSummary({ date: reportDate }) and useScheduleAttainment({ date: reportDate }))
  9. Implement empty state in MorningReportClient — detect when data hooks return no results for selected date, show "No production data available for {date}" message while keeping date navigation functional
  10. Write unit tests for DateNavigation component
  11. Write integration tests for MorningReportClient (URL sync, date threading, empty state)
DESIGN END

---

## DESIGN: 17-1-date-picker-on-morning-report
**Timestamp:** 2026-02-12 05:46:11

DESIGN START
story_id: 17-1-date-picker-on-morning-report

files_to_modify:
  - path: apps/web/src/components/ui/calendar.tsx
    action: create
    purpose: Shadcn Calendar component wrapping react-day-picker (generated via npx shadcn@latest add calendar). react-day-picker v9.13.2 and date-fns v4.1.0 already in package.json.

  - path: apps/web/src/components/ui/popover.tsx
    action: create
    purpose: Shadcn Popover component wrapping @radix-ui/react-popover (generated via npx shadcn@latest add popover). @radix-ui/react-popover v1.1.15 already in package.json.

  - path: apps/web/src/components/report/DateNavigation.tsx
    action: create
    purpose: Date picker + prev/next arrow buttons component. Uses Shadcn Calendar+Popover composition. Props: { date: Date; onDateChange: (date: Date) => void }. Displays formatted date (e.g., "Feb 5, 2026") in trigger button, ChevronLeft/ChevronRight arrows, disables next arrow when date >= yesterday, disables future dates in Calendar.

  - path: apps/web/src/components/report/index.ts
    action: create
    purpose: Barrel export for report domain components (DateNavigation). Follows pattern from components/action-list/index.ts.

  - path: apps/web/src/app/(main)/morning-report/MorningReportClient.tsx
    action: create
    purpose: 'use client' wrapper component. Manages selectedDate state initialized from useSearchParams().get('date') or defaults to yesterday. Validates date param (rejects future dates, invalid formats). Syncs URL via router.push(`/morning-report?date=YYYY-MM-DD`, { scroll: false }). Passes formatted reportDate string to all child components. Detects empty data state and shows "No production data available for {date}". Renders the full morning report layout currently in page.tsx.

  - path: apps/web/src/app/(main)/morning-report/page.tsx
    action: modify
    purpose: Replace inline JSX with <Suspense fallback={<MorningReportLoading />}><MorningReportClient /></Suspense>. Keep as Server Component for metadata export. Import Suspense from react and MorningReportClient. Import skeleton components for fallback.

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: (1) Add reportDate?: string and onDateChange?: (date: Date) => void props. (2) Pass reportDate to useDailyActions({ reportDate }) and useSmartSummary({ reportDate }). (3) Replace static "T-1 Data" badge with dynamic text — "T-1 Data" when yesterday, "Feb 5 Data" (format(date, 'MMM d')) otherwise. (4) Replace "Yesterday's Performance" label with dynamic text. (5) Integrate DateNavigation component in header next to the badge.

  - path: apps/web/src/components/action-engine/InsightEvidenceCardList.tsx
    action: modify
    purpose: Add reportDate?: string prop. Pass to useDailyActions({ reportDate }). The useFollowUps hook already receives reportDate from the API response data.report_date, so it will automatically follow.

  - path: apps/web/src/components/production/WorkcenterScorecard.tsx
    action: modify
    purpose: Add date?: string prop. Pass to useWorkcenterSummary({ date }). Required by AC#2 — all report sections must reload with selected date.

  - path: apps/web/src/components/production/ScheduleAttainment.tsx
    action: modify
    purpose: Add date?: string prop. Pass to useScheduleAttainment({ date }). Required by AC#2 — all report sections must reload with selected date.

  - path: apps/web/src/components/report/__tests__/DateNavigation.test.tsx
    action: create
    purpose: Unit tests for DateNavigation component — renders picker trigger with formatted date, opens calendar on click, prev/next arrows work, next arrow disabled when date >= yesterday, future dates disabled in calendar, calls onDateChange with correct Date object.

  - path: apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx
    action: create
    purpose: Integration tests for MorningReportClient — reads date from URL param, defaults to yesterday when no param, falls back to yesterday for invalid/future dates, updates URL on date change, threads reportDate to child components (verify hooks called with date), shows empty state when no data.

patterns_to_use:
  - Shadcn Calendar+Popover composition: Standard Shadcn pattern — Calendar inside Popover with PopoverTrigger as a Button showing formatted date. Matches existing Shadcn usage (Button, Card, Badge, Dialog, etc.) in the codebase.
  - Server/Client Component split: page.tsx remains Server Component (exports metadata), new MorningReportClient.tsx uses 'use client'. page.tsx wraps it in <Suspense> for useSearchParams compatibility. Standard Next.js 14 App Router pattern.
  - URL state sync via useSearchParams+useRouter: Read date from searchParams.get('date'), update via router.push with { scroll: false }. Same navigation mock pattern as ActivePlanBadge.test.tsx and page.test.tsx.
  - Hook date threading: All hooks (useDailyActions, useSmartSummary, useWorkcenterSummary, useScheduleAttainment) already accept optional date params (reportDate or date). Components just need to accept and forward the prop. No hook internals modified.
  - Barrel exports: New components/report/index.ts follows components/action-list/index.ts and components/action-engine/index.ts pattern.
  - Vitest + Testing Library: Test files in __tests__/ adjacent to component. vi.mock for next/navigation (useSearchParams, useRouter, usePathname). vi.mock for hooks. Same structure as existing page.test.tsx and MyAssignmentsPanel.test.tsx.
  - date-fns formatting: Use format() from date-fns for locale-safe date display (e.g., format(date, 'MMM d, yyyy')). Use subDays/addDays for safe date arithmetic avoiding timezone bugs with manual Date manipulation.

dependencies:
  - react-day-picker: installed (^9.13.2 in package.json)
  - date-fns: installed (^4.1.0 in package.json)
  - @radix-ui/react-popover: installed (^1.1.15 in package.json)
  - lucide-react: installed (^0.312.0 — has CalendarIcon, ChevronLeft, ChevronRight)
  - Shadcn Calendar component: needs-install (npx shadcn@latest add calendar — generates calendar.tsx wrapper)
  - Shadcn Popover component: needs-install (npx shadcn@latest add popover — generates popover.tsx wrapper)

acceptance_criteria_mapping:
  - AC1 (Date picker placement): DateNavigation.tsx renders Calendar+Popover+arrows. MorningSummarySection.tsx modified to accept onDateChange prop and render <DateNavigation date={...} onDateChange={...} /> in the header div, positioned next to the dynamic badge. The trigger button shows the formatted selected date (e.g., "Feb 5, 2026").
  - AC2 (Date change reloads all data): MorningReportClient.tsx manages selectedDate state and formats it as YYYY-MM-DD string. Passes reportDate prop to MorningSummarySection (→ useDailyActions, useSmartSummary), InsightEvidenceCardList (→ useDailyActions), WorkcenterScorecard (→ useWorkcenterSummary), and ScheduleAttainment (→ useScheduleAttainment). URL updates via router.push(`/morning-report?date=${formatted}`, { scroll: false }). Badge in MorningSummarySection becomes dynamic — "T-1 Data" when yesterday, "Feb 5 Data" otherwise.
  - AC3 (Prev/next day arrows): DateNavigation.tsx includes ChevronLeft (prev) and ChevronRight (next) buttons flanking the date picker trigger. Clicking calls onDateChange with date ±1 day (using date-fns addDays/subDays). Next button has disabled prop when selectedDate >= yesterday. Calendar component disables dates > yesterday via disabled={(date) => date > yesterday}.
  - AC4 (URL-driven date on load): MorningReportClient.tsx reads searchParams.get('date') on mount and initializes selectedDate state. Validates: (1) valid ISO date format, (2) not in the future (> yesterday). Invalid/missing/future dates fall back to yesterday. Suspense boundary in page.tsx ensures useSearchParams doesn't force full client rendering.
  - AC5 (Empty state for missing data): MorningReportClient.tsx checks if useDailyActions returns null/empty data (data === null && !isLoading && !error, or data.actions.length === 0). Shows "No production data available for {formatted date}" message in a centered empty state container. DateNavigation and all navigation remain interactive since they're controlled by MorningReportClient state, independent of data availability.

risks:
  - Shadcn CLI version: components.json exists at apps/web/components.json with correct aliases. The CLI may be `npx shadcn@latest` (newer) vs `npx shadcn-ui@latest` (older). Check which works; the story says `shadcn-ui@latest` but the newer CLI dropped the `-ui` suffix. Mitigation: try `npx shadcn@latest add calendar popover` first; fall back to `npx shadcn-ui@latest`.
  - react-day-picker v9 API differences: v9.x has different API than v8.x (which older Shadcn templates target). The generated calendar.tsx may need adjustment for v9 imports (e.g., DayPicker instead of default export, different prop names). Mitigation: verify generated calendar.tsx compiles, adjust imports if needed.
  - WorkcenterScorecard and ScheduleAttainment date threading: Story tasks only mention MorningSummarySection and InsightEvidenceCardList, but AC#2 says "all report sections" reload. Both production components MUST also receive the date prop. Mitigation: explicitly included in implementation plan as step 7.
  - Suspense boundary for useSearchParams: Next.js 14 requires useSearchParams() inside a Suspense boundary to avoid deopting the entire page to client rendering. Mitigation: page.tsx wraps MorningReportClient in <Suspense fallback={<loading skeleton>}>.
  - Timezone handling near midnight: Using new Date() and toISOString().split('T')[0] could yield wrong date near midnight in non-UTC timezones. Mitigation: use date-fns subDays(new Date(), 1) and format(date, 'yyyy-MM-dd') which operate on local time.
  - Empty state detection: Need to distinguish "no data for this date" from "loading" and "error". The useDailyActions hook returns { data: null, isLoading: false, error: null } initially before fetching, which could be confused with "no data". Mitigation: track whether at least one fetch has completed (use a hasLoaded flag or check data !== null || error !== null after isLoading transitions from true to false).
  - Existing page.test.tsx: Currently imports MorningReportPage directly from '../page' and renders it. After refactoring page.tsx to render MorningReportClient, this test will need to also mock next/navigation (useSearchParams, useRouter, usePathname) since MorningReportClient uses them. Mitigation: update existing test file to add navigation mocks.

estimated_test_files:
  - apps/web/src/components/report/__tests__/DateNavigation.test.tsx: Renders trigger button with formatted date, opens popover/calendar on click, prev arrow decrements date by 1 day, next arrow increments date by 1 day, next arrow disabled when date >= yesterday, future dates disabled in calendar picker, calls onDateChange callback with correct Date object on selection, keyboard accessibility.
  - apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx: Reads ?date=YYYY-MM-DD from URL and initializes state, defaults to yesterday when no date param, falls back to yesterday for invalid date strings, falls back to yesterday for future dates, calls router.push with correct URL on date change, passes reportDate to MorningSummarySection/InsightEvidenceCardList/WorkcenterScorecard/ScheduleAttainment, shows empty state message when no data for selected date, date picker and arrows remain functional during empty state.
  - apps/web/src/app/(main)/morning-report/__tests__/page.test.tsx: Existing test — may need navigation mocks added after page.tsx refactor.

implementation_order:
  1. Install Shadcn Calendar + Popover wrapper components: run `npx shadcn@latest add calendar popover` in apps/web/. This generates calendar.tsx and popover.tsx in src/components/ui/. Verify the generated code works with react-day-picker v9.13.2 and date-fns v4.1.0 already in package.json. Fix any v9 API incompatibilities in the generated calendar.tsx.
  2. Create DateNavigation component (apps/web/src/components/report/DateNavigation.tsx): Implement Shadcn Calendar+Popover composition with prev/next ChevronLeft/ChevronRight arrow buttons. Props: { date: Date; onDateChange: (date: Date) => void }. Format trigger text with date-fns format(date, 'MMM d, yyyy'). Disable next arrow when date >= yesterday. Disable future dates in Calendar via disabled prop. Use date-fns addDays/subDays for date arithmetic.
  3. Create barrel export (apps/web/src/components/report/index.ts): Export DateNavigation.
  4. Create MorningReportClient.tsx (apps/web/src/app/(main)/morning-report/MorningReportClient.tsx): 'use client' wrapper. Use useSearchParams to read date param, validate (valid date, not future), default to yesterday. Maintain selectedDate state. Use useRouter().push for URL sync with { scroll: false }. Move the full page layout JSX from page.tsx into this component. Pass formatted reportDate (YYYY-MM-DD string) to all child components. Implement empty state detection and "No production data available for {date}" message.
  5. Modify page.tsx (apps/web/src/app/(main)/morning-report/page.tsx): Keep as Server Component with metadata export. Replace inline JSX with <Suspense fallback={<SummarySkeleton />}><MorningReportClient /></Suspense>. Import Suspense from 'react'.
  6. Modify MorningSummarySection.tsx: Add reportDate?: string and onDateChange?: (date: Date) => void props. Pass reportDate to useDailyActions({ reportDate }) and useSmartSummary({ reportDate }). Replace static "T-1 Data" Badge with dynamic getDateBadgeText(). Replace "Yesterday's Performance" with dynamic label. Render <DateNavigation> in header area when onDateChange is provided.
  7. Modify InsightEvidenceCardList.tsx: Add reportDate?: string prop. Pass to useDailyActions({ reportDate }).
  8. Modify WorkcenterScorecard.tsx: Add date?: string prop. Pass to useWorkcenterSummary({ date }).
  9. Modify ScheduleAttainment.tsx: Add date?: string prop. Pass to useScheduleAttainment({ date }).
  10. Update existing page.test.tsx: Add next/navigation mocks (useSearchParams, useRouter, usePathname) to support new MorningReportClient rendering.
  11. Write unit tests for DateNavigation (apps/web/src/components/report/__tests__/DateNavigation.test.tsx).
  12. Write integration tests for MorningReportClient (apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx): URL param parsing, date threading, empty state.
DESIGN END

---

## DESIGN: 17-2-smart-summary-on-demand-generation
**Timestamp:** 2026-02-12 06:32:49

DESIGN START
story_id: 17-2-smart-summary-on-demand-generation

files_to_modify:
  - path: apps/web/src/hooks/useSmartSummary.ts
    action: modify
    purpose: Add `autoGenerate` option to UseSmartSummaryOptions, expose `generate()` method for manual on-demand generation, add `canGenerate` computed boolean to return type, modify 404 handler to conditionally skip auto-generation when autoGenerate is false

  - path: apps/web/src/components/action-list/MorningSummarySection.tsx
    action: modify
    purpose: Destructure new `generate` and `canGenerate` from useSmartSummary, pass `autoGenerate: !reportDateProp` (false when a specific historical date is passed), add "Generate Summary" button UI for historical dates with no cached summary, import Wand2 icon and Button component

  - path: apps/web/src/hooks/__tests__/useSmartSummary.test.ts
    action: create
    purpose: Unit tests for useSmartSummary hook — autoGenerate=false suppresses auto-generation on 404, autoGenerate=true preserves existing behavior, generate() calls POST /api/summaries/generate with correct payload, error handling during generate, canGenerate/hasSummary computed booleans

  - path: apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx
    action: create
    purpose: Component tests — "Generate Summary" button renders when canGenerate is true and no summary exists, loading state during generation, error state with retry, existing summary displays immediately with no prompt, regenerate button visible for existing summaries

patterns_to_use:
  - mountedRef guard: Same useRef(true) pattern already in useSmartSummary.ts (line 82) and useDailyActions.ts (line 130) for preventing state updates on unmounted components
  - Supabase JWT auth: Copy exact auth pattern from useSmartSummary.ts lines 90-100 — createClient() → getSession() → Bearer token header
  - Native fetch with explicit headers: Matches existing fetch pattern in both hooks (no axios, no credentials: 'include')
  - useCallback for async methods: Same pattern as fetchSummary and regenerateSummary — wrap in useCallback with [apiUrl, reportDate] dependency array
  - Vitest + renderHook + waitFor: Same test pattern as useWorkcenterSummary.test.ts — vi.mock for supabase client, global.fetch mock, renderHook from @testing-library/react
  - Component test with vi.mock for hooks: Mock useSmartSummary and useDailyActions to control return values, test component rendering based on different hook states
  - Shadcn Button component: Use existing Button from @/components/ui/button with variant="outline" size="sm" for the generate button
  - Lucide icons: Import Wand2 from lucide-react for the generate button icon (already installed v0.312.0)

dependencies:
  - lucide-react: installed (v0.312.0 — Wand2 icon available)
  - @testing-library/react: installed (renderHook, waitFor, act)
  - vitest: installed (vi, describe, it, expect)
  - react-markdown: installed (already imported in MorningSummarySection)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (Historical date with no summary shows generation prompt): MorningSummarySection.tsx — new conditional block renders when `!isSummaryLoading && !isGenerating && !summaryError && !hasSummary && canGenerate`. Shows "No summary exists for this date. Generate one?" text and a "Generate Summary" button with Wand2 icon. useSmartSummary.ts — when `autoGenerate: false` and GET returns 404, sets `data: null` without triggering POST, making `hasSummary: false` and `canGenerate: true`.
  - AC2 (Generate button triggers API, shows loading, saves result): MorningSummarySection.tsx — Button onClick calls `generateSummary()`. useSmartSummary.ts — `generate()` method sets `isGenerating: true`, calls `POST /api/summaries/generate` with `{ target_date: date, regenerate: false }`, on success updates `data` with returned SmartSummaryData (which makes `hasSummary: true` and the normal summary rendering kicks in). The backend saves the generated summary for future GET requests. MorningSummarySection.tsx — existing `isGenerating` loading block (lines 241-248) handles the loading indicator.
  - AC3 (Existing summary displayed immediately): Already handled by existing code — when GET returns 200, `hasSummary: true` and the summary renders in the "Real AI summary" block (MorningSummarySection.tsx line 277). No generation prompt shown because `hasSummary` is true.
  - AC4 (Regenerate option on existing summaries): Already implemented — the regenerate button at MorningSummarySection.tsx lines 229-237 calls `regenerateSummary()` which hits `GET /api/summaries/smart/{date}?regenerate=true`. No changes needed for this AC.
  - AC5 (Error handling with retry): useSmartSummary.ts — `generate()` method catches errors and sets `error` state with user-friendly message. MorningSummarySection.tsx — existing error block (lines 252-273) handles error display with retry button that calls `refetchSummary()`. For generation-specific errors, add a new error state block that shows retry with `generateSummary()` instead of `refetchSummary()` so the user can retry the generation specifically. Also handle "no production data" case — if the POST returns 404 or specific error indicating no data, show "No production data available for this date" message.

risks:
  - Wand2 icon availability in lucide-react v0.312.0: The Wand2 icon was added in lucide-react v0.263.0, so it should be available. Mitigation: if import fails, fall back to `Sparkles` or `Play` icon which are already used in the codebase.
  - autoGenerate default behavior: The story says `autoGenerate` should default to `true` for T-1 (yesterday) and `false` for historical dates. The component determines this via `autoGenerate: !reportDateProp` — when no reportDate prop is passed, it defaults to yesterday (autoGenerate=true). When a reportDate is passed (historical date navigation), autoGenerate=false. Edge case: when reportDateProp happens to BE yesterday's date (user navigated to yesterday via date picker), autoGenerate will be false, but this is acceptable because the GET will likely return the cached summary anyway (since T-1 auto-generates on the default morning report load). Mitigation: could compare reportDateProp to yesterday's date to set autoGenerate=true in that case, but the story explicitly says `!reportDate` is the right heuristic.
  - Race condition on date change: If the user changes dates rapidly, multiple fetchSummary calls may overlap. The existing mountedRef pattern prevents stale updates on unmount, but within a single mount, later responses could overwrite earlier ones. Mitigation: the existing useCallback dependency on reportDate means each date change creates a new function reference, and the useEffect cleanup runs between renders. The hook already handles this correctly via the mountedRef pattern.
  - Error state after generate vs fetch: Currently the error block in MorningSummarySection shows a generic "retry" that calls `refetchSummary()` (which does a GET). If the error came from `generate()`, the retry should call `generate()` again. Mitigation: track whether the last operation was a fetch or generate (or check `canGenerate` — if still true, retry should call generate). Simplest approach: add a separate error UI block specifically for the "no summary, generation failed" state that retries with `generateSummary()`.
  - Component re-renders: Adding `autoGenerate` as a dependency could trigger unnecessary re-renders. Mitigation: `autoGenerate` is computed from `reportDateProp` which is a stable prop — changes only when the user navigates dates, which is expected.

estimated_test_files:
  - apps/web/src/hooks/__tests__/useSmartSummary.test.ts: (1) Hook fetches with Bearer token auth on mount when autoFetch=true, (2) Hook returns hasSummary=true when GET returns 200 with data, (3) Hook auto-generates on 404 when autoGenerate is not set (default true behavior preserved), (4) Hook does NOT auto-generate on 404 when autoGenerate=false — returns hasSummary=false canGenerate=true, (5) generate() calls POST /api/summaries/generate with correct target_date and headers, (6) generate() updates state with returned summary on success, (7) generate() sets error state on failure with canGenerate remaining true for retry, (8) regenerate() still works as before — calls GET with ?regenerate=true, (9) Hook does not update state after unmount (mountedRef pattern)
  - apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx: (1) Renders "Generate Summary" button when hook returns canGenerate=true and hasSummary=false, (2) Does NOT render generate button when hasSummary=true, (3) Shows loading/generating animation when isGenerating=true, (4) Shows error with retry when generation fails, (5) Renders regenerate button when hasSummary=true, (6) Clicking "Generate Summary" calls generate function, (7) Shows existing summary text when hasSummary=true with no generation prompt

implementation_order:
  1. Modify `apps/web/src/hooks/useSmartSummary.ts` — extend UseSmartSummaryOptions with `autoGenerate?: boolean`, extend UseSmartSummaryReturn with `generate: () => Promise<void>` and `canGenerate: boolean`, modify 404 handler in fetchSummary to check autoGenerate before triggering generation, add new generateSummary useCallback that POSTs to /api/summaries/generate
  2. Modify `apps/web/src/components/action-list/MorningSummarySection.tsx` — import Wand2 from lucide-react and Button from @/components/ui/button, destructure generate/canGenerate from useSmartSummary, pass autoGenerate: !reportDateProp to hook, add generation prompt UI block (between error and no-summary fallback), add generation-specific error retry block
  3. Create `apps/web/src/hooks/__tests__/useSmartSummary.test.ts` — unit tests for hook: autoGenerate=false on 404, autoGenerate=true on 404 (existing behavior), generate() method, error handling, canGenerate/hasSummary booleans
  4. Create `apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx` — component tests: generate button rendering, loading state, error with retry, existing summary display
  5. Manual verification — run `npx vitest run` in apps/web/ to confirm all tests pass, then manually test in browser with date picker (from story 17.1) navigating to a historical date without a cached summary
DESIGN END

---

## DESIGN: 17-3-shift-summaries-data-model
**Timestamp:** 2026-02-12 06:55:21

DESIGN START
story_id: 17-3-shift-summaries-data-model

files_to_modify:
  - path: supabase/migrations/0035_shift_summaries.sql
    action: create
    purpose: Create the `shift_summaries` table with all columns (id UUID PK, asset_id UUID FK, date DATE, shift TEXT CHECK, oee/availability/performance/quality DECIMAL(5,2), downtime_minutes INTEGER, units_produced INTEGER, created_at TIMESTAMPTZ), unique constraint on (asset_id, date, shift), indexes on asset_id, date, and composite (asset_id, date), RLS policies matching daily_summaries pattern (authenticated SELECT, service_role full access), table/column comments, and verification queries. Note: story spec says 0032 but 0032-0034 already exist, so using 0035 as the next available number.

  - path: _bmad/scripts/seed-data.mjs
    action: modify
    purpose: (1) Add shift_summaries clearing step alongside existing daily_summaries clear. (2) Add a shift distribution helper function that splits daily totals into 3 shifts with realistic variance. (3) After daily_summaries insertion, generate and insert shift_summaries records for ALL 14 assets that have daily_summaries data (7 days + today per asset), creating 3 records per asset per day (morning, afternoon, night). (4) Ensure shift units_produced sums approximately match daily actual_output and weighted-average shift OEE approximately matches daily oee_percentage.

patterns_to_use:
  - CREATE TABLE IF NOT EXISTS with gen_random_uuid(): Exact pattern from 0003_analytical_cache.sql line 22-36. UUID PK DEFAULT gen_random_uuid(), FK to assets(id) ON DELETE CASCADE, TIMESTAMPTZ DEFAULT NOW() for created_at. No updated_at column since shift data is immutable.
  - TEXT CHECK constraint: Pattern from 0003_analytical_cache.sql line 77 (live_snapshots.status) and 0025_action_followups.sql lines 9,13. Use `shift TEXT NOT NULL CHECK (shift IN ('morning', 'afternoon', 'night'))` — NOT PostgreSQL ENUM type.
  - Named UNIQUE constraint: Pattern from 0003_analytical_cache.sql line 35 (`CONSTRAINT daily_summaries_asset_report_date_unique UNIQUE (asset_id, report_date)`). Apply as `CONSTRAINT shift_summaries_asset_date_shift_unique UNIQUE (asset_id, date, shift)`.
  - Index naming with IF NOT EXISTS: Pattern from 0003_analytical_cache.sql lines 52-55. Name format: `idx_shift_summaries_<column(s)>`. Create single-column indexes on `asset_id` and `date`, plus composite on `(asset_id, date)`.
  - Idempotent RLS policy creation: Pattern from 0003_analytical_cache.sql lines 145-168. Enable RLS, DROP POLICY IF EXISTS, then CREATE POLICY. Two policies: authenticated SELECT (USING true) and service_role ALL (USING true WITH CHECK true).
  - COMMENT ON TABLE/COLUMN: Pattern from 0003_analytical_cache.sql lines 39-49. Comment every column for documentation.
  - Verification queries as SQL comments: Pattern from 0003_analytical_cache.sql lines 212-248. Include queries to verify table structure, constraints, indexes, RLS status, and policies.
  - Seed data clearing: Pattern from seed-data.mjs lines 42-49. Add `await supabase.from('shift_summaries').delete().neq('id', '...')` BEFORE daily_summaries delete (since shift_summaries FK to assets, same cascade logic).
  - Seed data insertion with upsert: Use `upsert` with `onConflict: 'asset_id,date,shift'` for idempotency, matching the daily_summaries pattern on line 1425.
  - Logging pattern: Use emoji-prefixed console.log for section headers and `✓` for success messages, matching existing seed script style.

dependencies:
  - @supabase/supabase-js: installed (used by seed script, no version change)
  - No new dependencies needed — this is a pure SQL migration + seed data modification

acceptance_criteria_mapping:
  - AC1 (Table exists with all specified columns): `supabase/migrations/0035_shift_summaries.sql` — CREATE TABLE IF NOT EXISTS shift_summaries with columns: id (UUID PK DEFAULT gen_random_uuid()), asset_id (UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE), date (DATE NOT NULL), shift (TEXT NOT NULL CHECK IN ('morning','afternoon','night')), oee (DECIMAL(5,2)), availability (DECIMAL(5,2)), performance (DECIMAL(5,2)), quality (DECIMAL(5,2)), downtime_minutes (INTEGER), units_produced (INTEGER), created_at (TIMESTAMPTZ DEFAULT NOW()).
  - AC2 (Unique constraint on (asset_id, date, shift)): `supabase/migrations/0035_shift_summaries.sql` — CONSTRAINT shift_summaries_asset_date_shift_unique UNIQUE (asset_id, date, shift) declared inline in CREATE TABLE statement.
  - AC3 (Indexes on asset_id, date, and composite (asset_id, date)): `supabase/migrations/0035_shift_summaries.sql` — Three CREATE INDEX IF NOT EXISTS statements: idx_shift_summaries_asset_id, idx_shift_summaries_date, idx_shift_summaries_asset_date.
  - AC4 (RLS enabled with policies matching daily_summaries): `supabase/migrations/0035_shift_summaries.sql` — ALTER TABLE shift_summaries ENABLE ROW LEVEL SECURITY, then two policies: "Allow authenticated read access on shift_summaries" (FOR SELECT TO authenticated USING true), "Allow service_role full access on shift_summaries" (FOR ALL TO service_role USING true WITH CHECK true). Idempotent with DROP POLICY IF EXISTS before each CREATE.
  - AC5 (3 shift records per asset per day for same date range as daily_summaries): `_bmad/scripts/seed-data.mjs` — New `generateShiftSummaries(dailySummaries)` function iterates over every daily_summaries record and produces 3 shift records (morning, afternoon, night) for each. All 14 assets with 7 days + today of daily_summaries data will get shift records (14 assets × 8 days × 3 shifts = 336 records).
  - AC6 (Shift units_produced sums ≈ daily actual_output, weighted-average OEE ≈ daily oee_percentage): `_bmad/scripts/seed-data.mjs` — The distribution function allocates daily actual_output across shifts (~35-40% morning, ~30-35% afternoon, ~25-30% night) with variance. After splitting, it adjusts the last shift's units to ensure exact sum match. OEE sub-components (availability, performance, quality) are generated per shift such that their product yields the shift OEE, and the weighted-average (by units_produced) of shift OEEs approximately matches the daily oee_percentage.
  - AC7 (Realistic variance across shifts): `_bmad/scripts/seed-data.mjs` — The distribution function applies ±5-15% random variance to base allocations. Afternoon shift has a 30% chance of distinctly lower performance (performance component drops 5-15%). Night shift gets more downtime_minutes allocation and slightly lower availability. The random seed uses a deterministic hash of (asset_id + date) for reproducible but varied data across runs.
  - AC8 (Existing daily_summaries unchanged): `supabase/migrations/0035_shift_summaries.sql` contains NO ALTER TABLE statements on daily_summaries. `_bmad/scripts/seed-data.mjs` — the daily_summaries upsert logic (line 1425) remains completely untouched. Shift summary generation is a new code block added AFTER the existing daily_summaries insertion. Migration creates a brand new table with no modifications to existing tables or views.

risks:
  - Migration number conflict: Story spec says 0032 but 0032_response_tokens.sql through 0034_action_plans.sql already exist. Using 0035 instead. Mitigation: verified via Glob that 0034 is the latest; 0035 is the correct next number.
  - Daily summaries data scope differs from story note: The story's Dev Notes say "only 8 of 14 assets have daily_summaries seed data" but the actual seed script has 7 days of data for ALL 14 assets (lines 110-1312), plus daysAgo(0) for 8 assets (lines 1314-1418). Mitigation: generate shift records for ALL daily_summaries records in the array, not just the 8 named in the story note. This is correct behavior per AC#5 ("each asset has 3 shift records per day for the same date range as existing daily_summaries seed data").
  - OEE component consistency: OEE = Availability × Performance × Quality / 10000. When generating sub-components, the product must match the target shift OEE. Mitigation: generate availability and quality first within realistic ranges, then back-calculate performance = (oee × 10000) / (availability × quality). Clamp performance to [0, 100] and accept minor rounding differences.
  - Seed script idempotency: The clearing step deletes shift_summaries before re-inserting. Since shift_summaries has FK to assets (ON DELETE CASCADE), and the clearing step already deletes daily_summaries, we need to ensure shift_summaries is cleared BEFORE daily_summaries to avoid FK constraint issues if there were a cascade chain. Mitigation: add shift_summaries delete line before the daily_summaries delete line. Also use upsert with onConflict for the insert operation.
  - Deterministic vs random seed data: Using Math.random() means seed data varies between runs, which could cause test flakiness. Mitigation: use a simple seeded PRNG (linear congruential) based on a hash of asset_id + date string to produce deterministic-but-varied data across assets and dates. This ensures the same values on every run while still having realistic variance.
  - Shift data for daysAgo(0) partial-day records: Today's records have partial actual_output (e.g., Grinder 5 has 890 vs target 1950). Splitting partial-day output into 3 shifts would be unrealistic (night shift hasn't happened yet). Mitigation: for daysAgo(0) records, still generate 3 shift records but weight heavily toward morning (60-70%) with afternoon getting the rest and night getting 0 or very small values. This simulates "today is still in progress" realism. Alternatively, given the story says "3 shift records per day," generate all 3 but with night shift values at 0 for today's data. The simpler approach: treat daysAgo(0) the same as historical days for the distribution since this is seed/test data and the exact split doesn't need to reflect real-time progress.

estimated_test_files:
  - No test files needed: This story creates a SQL migration file and modifies a seed script. There are no TypeScript/JavaScript application code changes that require unit tests. The migration is verified by: (1) running `supabase db reset` and confirming the table exists with correct schema, (2) the verification queries embedded as SQL comments in the migration file, and (3) running the seed script and verifying shift_summaries records exist with correct counts and approximate value matching. Story 17.4 will add the API endpoint and UI that will have proper test coverage.

implementation_order:
  1. Create `supabase/migrations/0035_shift_summaries.sql` — Write the full migration file following the 0003_analytical_cache.sql pattern: header comments with story reference, CREATE TABLE IF NOT EXISTS with all columns per AC#1, UNIQUE constraint per AC#2, three indexes per AC#3, RLS enable + idempotent policy creation per AC#4, table/column comments, and verification queries as SQL comments. Do NOT include updated_at column or update trigger. Use TEXT CHECK for shift column, not ENUM.
  2. Add shift_summaries clearing to `_bmad/scripts/seed-data.mjs` — Insert `await supabase.from('shift_summaries').delete().neq('id', '00000000-0000-0000-0000-000000000000');` into the clearing section (between line 48 downtime_events delete and line 49 daily_summaries delete). Update the console.log on line 50 to include shift_summaries in the list.
  3. Add seeded PRNG helper function to seed-data.mjs — Create a `seededRandom(seed)` function that returns a deterministic pseudo-random number generator. The seed will be derived from a simple hash of `asset_id + date + shift` string to ensure reproducible but varied data. Place near existing helper functions (after line 35).
  4. Add `generateShiftSummaries(dailySummaries)` function to seed-data.mjs — Create the distribution function that takes the dailySummaries array and returns a shift_summaries array. For each daily record: (a) allocate units_produced across 3 shifts with base percentages (morning 37%, afternoon 33%, night 30%) plus deterministic variance (±5-15%); (b) adjust last shift to ensure exact sum match; (c) allocate downtime_minutes weighted toward lower-performing shifts; (d) generate OEE sub-components (availability 85-98%, quality 95-100%, performance back-calculated from shift OEE); (e) apply afternoon-occasionally-lower-performance pattern (reduce performance on ~30% of afternoon records); (f) give night shift slightly more downtime. Place this function before the seed() function.
  5. Add shift_summaries insertion block to seed() function in seed-data.mjs — After the daily_summaries upsert (around line 1427), add: (a) call generateShiftSummaries(dailySummaries) to create the records, (b) console.log section header, (c) upsert with onConflict: 'asset_id,date,shift', (d) error/success logging with record count. This satisfies AC#5, AC#6, AC#7.
  6. Verify backward compatibility (AC#8) — Confirm by code review: (a) migration file contains zero ALTER TABLE statements on daily_summaries or any other existing table, (b) seed script's daily_summaries upsert logic at line 1425 is completely unchanged, (c) no modifications to any existing views or queries. This is a read-through verification step, not a code change.
DESIGN END

---

## DESIGN: 17-4-shift-breakdown-api-ui
**Timestamp:** 2026-02-12 07:19:33

DESIGN START
story_id: 17-4-shift-breakdown-api-ui

files_to_modify:
  - path: apps/api/app/schemas/production.py
    action: modify
    purpose: Add ShiftBreakdown Pydantic model for per-shift metrics (shift name, actual, target, attainment_pct, oee, downtime_minutes). Add optional shift_breakdown field to WorkcenterEntry. Add ShiftAssetDetail model extending AssetDetail with shift_breakdown. Keep existing models backward-compatible with new optional fields.

  - path: apps/api/app/schemas/action.py
    action: modify
    purpose: Add optional shift_attribution field (Optional[str], default None) to ActionItem model at line ~238 alongside trend_data. This is nullable for backward compatibility per NFR-I6.

  - path: apps/api/app/api/production.py
    action: modify
    purpose: Modify existing get_workcenter_summary endpoint to add optional shift query parameter (morning|afternoon|night). When no shift param: query shift_summaries table alongside daily_summaries and populate shift_breakdown arrays on WorkcenterEntry. When shift param provided: query shift_summaries filtered by that shift and return only that shift's data as the primary metrics (no shift_breakdown array). Follow existing Supabase query + in-memory grouping pattern at lines 395-505.

  - path: apps/api/app/services/action_engine.py
    action: modify
    purpose: (1) Add _load_shift_summaries(target_date, asset_ids) async method to batch-query shift_summaries for a date/asset set — returns Dict[str, List[dict]] grouped by asset_id. (2) Add _get_shift_attribution(asset_id, target_date, shift_data) method implementing >60% threshold logic. (3) In generate_action_list, after trend_data computation (line ~1104), batch-load shift_summaries for all asset_ids and enrich each OEE/financial action with shift_attribution. Safety actions excluded (shift attribution not meaningful for safety events).

  - path: apps/web/src/components/production/ShiftTabs.tsx
    action: create
    purpose: New shift selector component using Shadcn Tabs. Renders "All" (default), "Morning", "Afternoon", "Night" tabs. Props: value (string), onValueChange callback, className. Emits shift value or "all" string.

  - path: apps/web/src/components/production/WorkcenterScorecard.tsx
    action: modify
    purpose: Add selectedShift prop (optional string). When shift is selected and not "all", pass shift param to useWorkcenterSummary hook. When "all", show aggregate data (existing behavior). No structural changes to component layout — the hook response already drives what's shown.

  - path: apps/web/src/hooks/useWorkcenterSummary.ts
    action: modify
    purpose: Add optional shift parameter to UseWorkcenterSummaryOptions. Include shift in API URL query string when provided (e.g., &shift=morning). Add shift_breakdown to WorkcenterEntry and AssetDetail interfaces. Add shift to fetchData useCallback dependency array.

  - path: apps/web/src/components/action-engine/InsightSection.tsx
    action: modify
    purpose: Add optional shiftAttribution prop (string). When present, render a small badge/pill below the recommendation text showing the shift attribution text (e.g., "Afternoon Shift — 58 min mechanical"). Use existing cn() utility and Tailwind styling consistent with other badges.

  - path: apps/web/src/components/action-engine/types.ts
    action: modify
    purpose: Add optional shiftAttribution?: string field to ActionItem interface at line ~113.

  - path: apps/web/src/components/action-engine/transformers.ts
    action: modify
    purpose: In transformAPIActionItem function, map item.shift_attribution to the new shiftAttribution field on the transformed InsightActionItem.

  - path: apps/web/src/hooks/useDailyActions.ts
    action: modify
    purpose: Add optional shift_attribution?: string field to the ActionItem interface (line ~37) to match the new backend field.

  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Pass shiftAttribution from the ActionItem to InsightSection as a prop.

  - path: apps/web/src/components/production/index.ts
    action: modify
    purpose: Add export for new ShiftTabs component.

  - path: apps/web/src/app/(main)/morning-report/MorningReportClient.tsx
    action: modify
    purpose: (1) Add selectedShift state initialized from URL searchParams.get('shift') or 'all'. (2) Add handleShiftChange callback that updates state + URL param. (3) Render ShiftTabs above WorkcenterScorecard section. (4) Pass selectedShift to WorkcenterScorecard. (5) Optionally pass shift context to InsightEvidenceCardList for filtering display.

patterns_to_use:
  - Supabase batch query with in-memory grouping: Same pattern as production.py lines 395-505 — query shift_summaries with .eq("date"), build lookup map keyed by asset_id, merge with daily_summaries in Python.
  - Optional query parameter with default: Same pattern as production.py lines 371-375 — use FastAPI Query() with alias, default None, Optional type. Add shift parameter alongside existing date parameter.
  - ActionItem optional field extension: Same pattern as trend_data (action.py line 235-238) and acknowledgment (line 228-232) — add Optional[str] = Field(default=None, description=...) for backward compatibility.
  - ActionEngine batch loading: Same pattern as _load_trailing_summaries (action_engine.py lines 263-316) — async method using .in_("asset_id", asset_ids), returns Dict[str, List[dict]].
  - Frontend hook with optional param: Same pattern as useWorkcenterSummary date parameter — add to options interface, include in URL construction, add to useCallback deps.
  - URL state sync: Same pattern as MorningReportClient date handling (lines 34-49) — useState initialized from searchParams, useCallback for router.push with { scroll: false }.
  - Shadcn Tabs component: Use existing @radix-ui/react-tabs (already in package.json) via Shadcn Tabs primitive. Match styling pattern from existing Shadcn components.
  - Component prop threading: Same pattern as reportDate threading through MorningReportClient → WorkcenterScorecard — add prop, pass from parent, forward to hook.
  - Transformer extension: Same pattern as trendData mapping in transformers.ts lines 207-214 — add field mapping in transformAPIActionItem.
  - Vitest component testing with mock hooks: Same pattern as WorkcenterScorecard.test.tsx — vi.mock for hooks, mockReturnValue for different states, screen queries for assertions.
  - pytest with mock Supabase: Same pattern as test_production_workcenter.py — mock get_supabase_client, _make_table_mock helper, test with/without data scenarios.

dependencies:
  - @radix-ui/react-tabs: installed (already in package.json for Shadcn UI)
  - All other dependencies already installed — no new packages needed

acceptance_criteria_mapping:
  - AC1 (Workcenter endpoint returns shift_breakdown array): apps/api/app/schemas/production.py — new ShiftBreakdown model with shift, actual_output, target_output, attainment_pct, oee, downtime_minutes. WorkcenterEntry gets optional shift_breakdown: Optional[List[ShiftBreakdown]] field. apps/api/app/api/production.py — get_workcenter_summary modified to query shift_summaries table alongside daily_summaries. When no shift filter: each WorkcenterEntry includes shift_breakdown array populated from shift_summaries grouped by asset, then aggregated per workcenter. Overall workcenter figures remain the daily aggregate (from daily_summaries). When shift param provided: return only that shift's data as the primary metrics. apps/web/src/hooks/useWorkcenterSummary.ts — add shift_breakdown to WorkcenterEntry interface.

  - AC2 (Shift tab filtering on scorecard and action items): apps/web/src/components/production/ShiftTabs.tsx — new Shadcn Tabs component with "All"/"Morning"/"Afternoon"/"Night" tabs. apps/web/src/app/(main)/morning-report/MorningReportClient.tsx — manages selectedShift state via URL params (?shift=afternoon), renders ShiftTabs above WorkcenterScorecard, passes selectedShift to WorkcenterScorecard. apps/web/src/components/production/WorkcenterScorecard.tsx — accepts selectedShift prop, passes to useWorkcenterSummary({ date, shift }). apps/web/src/hooks/useWorkcenterSummary.ts — includes shift query param in API URL. When shift changes, useEffect triggers refetch showing that shift's data. Action items in InsightEvidenceCardList show shift attribution badges which effectively surfaces shift-specific context.

  - AC3 (Action card shows shift attribution for single-shift miss): apps/api/app/schemas/action.py — new optional shift_attribution: Optional[str] field on ActionItem (default None). apps/api/app/services/action_engine.py — new _load_shift_summaries() batch loader and _get_shift_attribution() method. For each OEE/financial action, queries shift_summaries for that asset+date. If one shift accounts for >60% of total downtime or output gap, sets shift_attribution to descriptive string (e.g., "afternoon shift — 58 min mechanical"). Called in generate_action_list after trend computation. apps/web/src/hooks/useDailyActions.ts — shift_attribution field on ActionItem interface. apps/web/src/components/action-engine/transformers.ts — maps shift_attribution through transformer. apps/web/src/components/action-engine/types.ts — shiftAttribution on frontend ActionItem. apps/web/src/components/action-engine/InsightSection.tsx — renders shift attribution badge/pill below recommendation when shiftAttribution prop is present. apps/web/src/components/action-engine/InsightEvidenceCard.tsx — passes shiftAttribution to InsightSection.

  - AC4 (Systemic issue remains daily-level without shift attribution): apps/api/app/services/action_engine.py — _get_shift_attribution() logic: when no single shift exceeds 60% of total miss, returns None. ActionItem.shift_attribution stays None (default). apps/web/src/components/action-engine/InsightSection.tsx — when shiftAttribution is absent/null, no shift badge renders, leaving the card as a daily-level item (existing behavior unchanged).

risks:
  - Existing workcenter-summary endpoint modification: The story says to create a new endpoint, but there's already a GET /api/production/workcenter-summary endpoint (production.py line 365). Modifying the existing endpoint is cleaner than creating a duplicate. Mitigation: Add shift parameter as optional (default None) so existing callers see no change. When shift_summaries has no data for a date, shift_breakdown will be an empty array — backward compatible.

  - shift_summaries table column naming vs daily_summaries: The shift_summaries table uses columns named `units_produced` and `oee` (from story 17-3 schema), while daily_summaries uses `units_produced` and `oee` (same names). However, the daily_summaries query in production.py (line 401) selects `oee` while the column in the DB might be `oee_percentage` (action_engine.py line 737 queries `oee_percentage`). Need to verify exact column names in daily_summaries vs shift_summaries. Mitigation: Read the migration files to confirm column names before implementation. The get_workcenter_summary endpoint already queries `oee` (line 401), so shift_summaries should use the same name.

  - Action engine cache invalidation: The ActionEngine caches action lists by date+category (line 1012). Adding shift_attribution enrichment after merge (like trend_data) means cached results will include shift attribution. This is correct since shift data is date-specific and doesn't change within a day. No cache key change needed.

  - ShiftTabs UI with no shift data: When shift_summaries has no data for a given date, the shift_breakdown arrays will be empty. The UI should still show tabs but "All" tab works normally and individual shift tabs may show empty states. Mitigation: When shift_breakdown is empty on all workcenters, consider hiding ShiftTabs entirely or showing a "No shift data" message. Implement by checking if any workcenter has non-empty shift_breakdown before rendering tabs.

  - API response size increase: Adding shift_breakdown arrays to every WorkcenterEntry increases response payload. For 5 workcenters × 3 shifts × 6 fields ≈ 90 additional data points. Mitigation: This is minimal overhead. The shift_breakdown field is Optional so responses without shift data stay compact.

  - Frontend refetch on shift change: Changing shift tab will trigger a new API call via useWorkcenterSummary. This is the correct behavior since the API returns different data per shift. However, rapid tab switching could cause flickering. Mitigation: The existing mountedRef pattern in useWorkcenterSummary prevents stale updates. The isLoading check at line 18 (`isLoading && !data`) means the scorecard shows stale data during refetch rather than loading skeleton — good UX.

  - Shift attribution 60% threshold edge cases: The >60% threshold for single-shift attribution might need tuning. Consider: 3 shifts where one has 55%, another 35%, third 10% — this would NOT trigger attribution despite one shift being clearly dominant. Mitigation: Start with 60% as specified in the story, add logging to track attribution decisions for future tuning. The threshold is encapsulated in _get_shift_attribution() for easy adjustment.

  - InsightEvidenceCard prop drilling: shiftAttribution needs to flow from InsightEvidenceCardList → InsightEvidenceCard → InsightSection. InsightEvidenceCard currently receives the full ActionItem from types.ts. Since we add shiftAttribution to that type, InsightEvidenceCard can access it directly and pass to InsightSection without additional prop plumbing at the list level. Mitigation: verified — InsightEvidenceCard receives the full item, destructures needed fields, and passes to InsightSection.

estimated_test_files:
  - apps/api/tests/test_shift_breakdown_api.py: Test the modified workcenter-summary endpoint with: (1) shift_breakdown populated when shift_summaries data exists, (2) empty shift_breakdown when no shift data, (3) shift filter param returns only that shift's data, (4) aggregate figures match sum of shift values, (5) date defaults to T-1, (6) invalid shift param handling.

  - apps/api/tests/test_shift_attribution.py: Test _get_shift_attribution logic: (1) single-shift miss >60% returns attribution string, (2) systemic miss (no shift >60%) returns None, (3) no shift_summaries data returns None, (4) attribution string format includes shift name + context, (5) integration test with _get_oee_actions verifying shift_attribution on ActionItem.

  - apps/web/src/components/production/__tests__/ShiftTabs.test.tsx: Test ShiftTabs component: (1) renders all four tabs (All/Morning/Afternoon/Night), (2) "All" selected by default, (3) clicking a tab calls onValueChange with correct value, (4) controlled value prop works, (5) accessible tab role and aria attributes.

  - apps/web/src/components/production/__tests__/WorkcenterScorecard.shift.test.tsx: Test shift integration on WorkcenterScorecard: (1) passes shift param to useWorkcenterSummary when selectedShift is not "all", (2) does not pass shift param when selectedShift is "all" or undefined, (3) displays shift-filtered data correctly.

  - apps/web/src/components/action-engine/__tests__/InsightSection.shift.test.tsx: Test shift attribution display: (1) renders shift badge when shiftAttribution prop is provided, (2) does not render shift badge when shiftAttribution is undefined/null, (3) badge text matches prop value.

implementation_order:
  1. Add ShiftBreakdown schema to apps/api/app/schemas/production.py — create ShiftBreakdown model, add optional shift_breakdown: Optional[List[ShiftBreakdown]] to WorkcenterEntry. This is pure schema work with no logic changes.

  2. Add shift_attribution field to apps/api/app/schemas/action.py — add shift_attribution: Optional[str] = Field(default=None, ...) to ActionItem model at ~line 238. Pure schema extension.

  3. Modify workcenter-summary endpoint in apps/api/app/api/production.py — add optional shift query parameter. Add shift_summaries query. When no shift filter: populate shift_breakdown arrays by querying shift_summaries, grouping by asset_id and shift, attaching to each WorkcenterEntry. When shift filter: query shift_summaries for that shift only and use as primary metrics. Maintain existing daily_summaries query for aggregate view.

  4. Write API tests for shift breakdown (apps/api/tests/test_shift_breakdown_api.py) — test endpoint with/without shift data, shift filter, aggregation consistency, empty state fallback.

  5. Add _load_shift_summaries and _get_shift_attribution to ActionEngine (apps/api/app/services/action_engine.py) — batch loader follows _load_trailing_summaries pattern. Attribution method: for a given asset+date, load all 3 shift records, calculate each shift's share of total downtime (or output gap), return attribution string if one shift >60%. In generate_action_list, after trend_data block (~line 1104), batch-load shift summaries and enrich OEE/financial actions.

  6. Write shift attribution tests (apps/api/tests/test_shift_attribution.py) — test single-shift miss, systemic miss, no data, attribution string format.

  7. Update frontend types — add shift_attribution to useDailyActions ActionItem (apps/web/src/hooks/useDailyActions.ts), add shiftAttribution to types.ts ActionItem (apps/web/src/components/action-engine/types.ts), update transformer (apps/web/src/components/action-engine/transformers.ts) to map shift_attribution → shiftAttribution.

  8. Update useWorkcenterSummary hook (apps/web/src/hooks/useWorkcenterSummary.ts) — add shift to options interface, add shift_breakdown to WorkcenterEntry type, include shift in fetch URL.

  9. Create ShiftTabs component (apps/web/src/components/production/ShiftTabs.tsx) — Shadcn Tabs with All/Morning/Afternoon/Night values. Export from production/index.ts.

  10. Write ShiftTabs tests (apps/web/src/components/production/__tests__/ShiftTabs.test.tsx).

  11. Modify WorkcenterScorecard (apps/web/src/components/production/WorkcenterScorecard.tsx) — add selectedShift prop, pass shift to useWorkcenterSummary when not "all".

  12. Add shift attribution display to InsightSection (apps/web/src/components/action-engine/InsightSection.tsx) — add shiftAttribution prop, render badge pill when present. Update InsightEvidenceCard.tsx to pass shiftAttribution through.

  13. Integrate into MorningReportClient (apps/web/src/app/(main)/morning-report/MorningReportClient.tsx) — add selectedShift state from URL, handleShiftChange callback, render ShiftTabs, pass selectedShift to WorkcenterScorecard.

  14. Write remaining frontend tests — WorkcenterScorecard shift test, InsightSection shift badge test.

  15. End-to-end verification — confirm "All" tab matches current daily view, shift tab filters scorecard data, action items show shift attribution, backward compatibility when no shift data exists.
DESIGN END

---
