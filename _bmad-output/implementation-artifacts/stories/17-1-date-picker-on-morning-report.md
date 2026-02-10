# Story 17.1: Date Picker on Morning Report

Status: ready-for-dev

## Story

As a Plant Manager,
I want a date picker on the morning report page that lets me navigate to any past date,
so that I can review historical reports for weekly meetings or incident comparisons.

## Acceptance Criteria

1. **Date picker placement:** A date picker appears next to the "T-1 Data" badge in the MorningSummarySection header, defaulting to yesterday's date.

2. **Date change reloads all data:** When the user selects a different date, all report sections (workcenter scorecard, action items, smart summary) reload with data for the selected date. The URL updates to `/morning-report?date=YYYY-MM-DD`. The "T-1 Data" badge updates to reflect the selected date (e.g., "Feb 5 Data").

3. **Prev/next day arrows:** Prev/next day arrow buttons are displayed alongside the date picker. Clicking them increments/decrements the date by one day and reloads the report. The "next" arrow is disabled when viewing yesterday (cannot navigate to today or future dates).

4. **URL-driven date on load:** When a URL with a `date` query parameter is loaded directly (e.g., `/morning-report?date=2026-02-05`), the report shows data for the specified date and the date picker reflects the URL date.

5. **Empty state for missing data:** When the selected date has no `daily_summaries` records, an empty state is shown: "No production data available for {date}". The date picker and navigation arrows remain functional.

## Tasks / Subtasks

- [ ] Task 1: Install Shadcn Calendar + Popover components and react-day-picker dependency (AC: #1)
  - [ ] 1.1: Run `npx shadcn-ui@latest add calendar popover` in `apps/web/` to install Calendar and Popover Shadcn components
  - [ ] 1.2: Verify `react-day-picker` is added to `package.json` dependencies (Shadcn Calendar depends on it)
  - [ ] 1.3: Confirm new files exist: `src/components/ui/calendar.tsx`, `src/components/ui/popover.tsx`
- [ ] Task 2: Create DateNavigation component (AC: #1, #3)
  - [ ] 2.1: Create `apps/web/src/components/report/DateNavigation.tsx`
  - [ ] 2.2: Implement date picker using Shadcn `Calendar` + `Popover` pattern
  - [ ] 2.3: Add prev/next day `ChevronLeft`/`ChevronRight` arrow buttons using `lucide-react` icons
  - [ ] 2.4: Disable "next" arrow when selected date >= yesterday
  - [ ] 2.5: Disable future dates in the Calendar component via `disabled` prop
  - [ ] 2.6: Props interface: `{ date: Date; onDateChange: (date: Date) => void }`
  - [ ] 2.7: Display formatted date in the trigger button (e.g., "Feb 5, 2026")
  - [ ] 2.8: Create barrel export at `apps/web/src/components/report/index.ts`
- [ ] Task 3: Convert morning report page to Client Component with date state + URL sync (AC: #2, #4)
  - [ ] 3.1: Create new Client Component wrapper: `apps/web/src/app/(main)/morning-report/MorningReportClient.tsx`
  - [ ] 3.2: Use `useSearchParams()` to read `date` from URL on mount
  - [ ] 3.3: Use `useRouter()` + `router.push` with `{ scroll: false }` for shallow URL updates on date change
  - [ ] 3.4: Maintain `selectedDate` state initialized from URL param or default to yesterday
  - [ ] 3.5: Validate date param: if invalid/future, fall back to yesterday
  - [ ] 3.6: Keep `page.tsx` as Server Component that renders `MorningReportClient` (preserves metadata export)
- [ ] Task 4: Thread selected date through to all data hooks (AC: #2)
  - [ ] 4.1: Add `reportDate` prop to `MorningSummarySection` and pass to `useDailyActions({ reportDate })` and `useSmartSummary({ reportDate })`
  - [ ] 4.2: Add `reportDate` prop to `InsightEvidenceCardList` and pass to `useDailyActions({ reportDate })`
  - [ ] 4.3: Format date as `YYYY-MM-DD` string before passing to hooks (hooks already accept this format)
- [ ] Task 5: Update MorningSummarySection header with DateNavigation and dynamic badge (AC: #1, #2)
  - [ ] 5.1: Replace hardcoded "Yesterday's Performance" label with dynamic text based on selected date
  - [ ] 5.2: Replace static `<Badge>T-1 Data</Badge>` with dynamic badge showing selected date (e.g., "Feb 5 Data") or "T-1 Data" when yesterday is selected
  - [ ] 5.3: Integrate `DateNavigation` component into the header area alongside the badge
- [ ] Task 6: Handle empty state when no data exists for selected date (AC: #5)
  - [ ] 6.1: In `MorningReportClient`, detect when `useDailyActions` returns empty/null data for a date
  - [ ] 6.2: Show empty state message: "No production data available for {formatted date}"
  - [ ] 6.3: Ensure date picker and navigation arrows remain interactive during empty state
- [ ] Task 7: Write tests for DateNavigation component and date URL sync (AC: #1-5)
  - [ ] 7.1: Unit tests for DateNavigation: renders picker, prev/next arrows, disables future navigation
  - [ ] 7.2: Integration test: date change triggers hook refetch with correct date param
  - [ ] 7.3: Test URL param parsing: valid date, invalid date, missing date, future date

## Dev Notes

### Architecture & Patterns

- **Framework:** Next.js 14 App Router with TypeScript. This project uses a `(main)` route group with a layout that enforces auth and provides `AppShell` navigation.
- **UI Library:** Shadcn/UI + Radix UI primitives + Tailwind CSS. All new UI components MUST use Shadcn patterns.
- **Design System:** "Industrial Clarity" - high contrast, Inter font, `mode="retrospective"` on Cards for morning report (cool colors).
- **Hooks pattern:** Existing hooks (`useDailyActions`, `useSmartSummary`) already accept `reportDate?: string` option in YYYY-MM-DD format. DO NOT modify the hook internals. Just pass the date parameter.
- **Testing:** Vitest + Testing Library. Test files go in `__tests__/` directories adjacent to the component.

### Critical: Server Component vs Client Component Strategy

The current `page.tsx` is a **Server Component** that exports `metadata`. To add client-side date state and URL sync, you MUST:

1. Keep `page.tsx` as a Server Component (so `metadata` export works).
2. Create a new `MorningReportClient.tsx` Client Component (with `'use client'` directive) that contains all the date logic and renders child components.
3. `page.tsx` renders `<MorningReportClient />` which handles everything else.

**DO NOT** add `'use client'` to `page.tsx` directly - this would break the `metadata` export.

### Critical: Existing Hook API Already Supports Date Parameter

Both hooks already support date parameters - this is a KEY finding that prevents unnecessary rework:

```typescript
// useDailyActions - already accepts reportDate
useDailyActions({ reportDate: '2026-02-05' })

// useSmartSummary - already accepts reportDate
useSmartSummary({ reportDate: '2026-02-05' })
```

The hooks default to yesterday when no `reportDate` is provided. You only need to thread the selected date down as a prop.

### Critical: Components That Need Date Prop Added

These components currently call hooks with no date param and need a `reportDate` prop added:

1. **`MorningSummarySection`** (`apps/web/src/components/action-list/MorningSummarySection.tsx`):
   - Currently: `useDailyActions()` and `useSmartSummary()` with no options
   - Change to: `useDailyActions({ reportDate })` and `useSmartSummary({ reportDate })`
   - Add `reportDate?: string` to component props interface

2. **`InsightEvidenceCardList`** (`apps/web/src/components/action-engine/InsightEvidenceCardList.tsx`):
   - Currently: `useDailyActions()` with no options
   - Change to: `useDailyActions({ reportDate })`
   - Add `reportDate?: string` to component props interface

### URL Sync Pattern

Use Next.js App Router patterns for URL state:

```typescript
'use client'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'

// Read date from URL
const searchParams = useSearchParams()
const dateParam = searchParams.get('date')

// Update URL on date change (shallow - no server re-render)
const router = useRouter()
const pathname = usePathname()
const handleDateChange = (newDate: Date) => {
  const formatted = newDate.toISOString().split('T')[0]
  router.push(`${pathname}?date=${formatted}`, { scroll: false })
}
```

### Date Picker Component Pattern (Shadcn)

Use the standard Shadcn Calendar + Popover composition:

```tsx
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { CalendarIcon, ChevronLeft, ChevronRight } from 'lucide-react'
import { format } from 'date-fns' // Comes with react-day-picker

<div className="flex items-center gap-1">
  <Button variant="ghost" size="icon" onClick={handlePrevDay} disabled={false}>
    <ChevronLeft className="h-4 w-4" />
  </Button>

  <Popover>
    <PopoverTrigger asChild>
      <Button variant="outline" className="gap-2">
        <CalendarIcon className="h-4 w-4" />
        {format(selectedDate, 'MMM d, yyyy')}
      </Button>
    </PopoverTrigger>
    <PopoverContent className="w-auto p-0" align="start">
      <Calendar
        mode="single"
        selected={selectedDate}
        onSelect={handleDateSelect}
        disabled={(date) => date > yesterday || date < someMinDate}
        initialFocus
      />
    </PopoverContent>
  </Popover>

  <Button variant="ghost" size="icon" onClick={handleNextDay} disabled={isYesterday}>
    <ChevronRight className="h-4 w-4" />
  </Button>
</div>
```

### Dynamic Badge Logic

```typescript
function getDateBadgeText(selectedDate: Date): string {
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  yesterday.setHours(0, 0, 0, 0)

  const selected = new Date(selectedDate)
  selected.setHours(0, 0, 0, 0)

  if (selected.getTime() === yesterday.getTime()) {
    return 'T-1 Data'
  }
  return format(selectedDate, 'MMM d') + ' Data'
}
```

### Dependency Installation

The Shadcn Calendar component requires `react-day-picker` and `date-fns` as peer dependencies. Run:

```bash
cd apps/web
npx shadcn-ui@latest add calendar popover
```

This will:
- Create `src/components/ui/calendar.tsx` (wraps react-day-picker)
- Create `src/components/ui/popover.tsx` (wraps @radix-ui/react-popover - already installed)
- Add `react-day-picker` and `date-fns` to package.json

Note: `@radix-ui/react-popover` (v1.1.6) is already in `package.json`. Shadcn may create the wrapper regardless.

### Project Structure Notes

- **New files:**
  - `apps/web/src/components/report/DateNavigation.tsx` - Date picker + prev/next arrows
  - `apps/web/src/components/report/index.ts` - Barrel export
  - `apps/web/src/app/(main)/morning-report/MorningReportClient.tsx` - Client wrapper
  - `apps/web/src/components/ui/calendar.tsx` - Shadcn Calendar (auto-generated)
  - `apps/web/src/components/ui/popover.tsx` - Shadcn Popover (auto-generated)

- **Modified files:**
  - `apps/web/src/app/(main)/morning-report/page.tsx` - Render MorningReportClient instead of inline JSX
  - `apps/web/src/components/action-list/MorningSummarySection.tsx` - Accept `reportDate` prop, pass to hooks, dynamic badge
  - `apps/web/src/components/action-engine/InsightEvidenceCardList.tsx` - Accept `reportDate` prop, pass to hook
  - `apps/web/package.json` - New deps: react-day-picker, date-fns (via shadcn add)

- **Path pattern:** Components in `apps/web/src/components/report/` for report-specific UI. This is a new domain folder following the existing pattern (e.g., `components/chat/`, `components/action-engine/`, `components/action-list/`).

### Backward Compatibility

- When no `date` query parameter is in the URL, default to yesterday. This preserves the current behavior exactly.
- The `useDailyActions` and `useSmartSummary` hooks already default to yesterday when no `reportDate` is provided. The new prop is optional.
- The "T-1 Data" badge text remains the default when viewing yesterday.
- All existing deep links to `/morning-report` (without date param) continue working unchanged.

### References

- [Source: _bmad-output/planning-artifacts/epic-17.md#Story 17.1]
- [Source: _bmad-output/planning-artifacts/epics-improvements.md#FR-I10, NFR-I7]
- [Source: docs/architecture-web.md#Directory Structure]
- [Source: docs/architecture-web.md#Technology Stack]
- [Source: apps/web/src/hooks/useDailyActions.ts#UseDailyActionsOptions]
- [Source: apps/web/src/hooks/useSmartSummary.ts#UseSmartSummaryOptions]
- [Source: apps/web/src/components/action-list/MorningSummarySection.tsx]
- [Source: apps/web/src/components/action-engine/InsightEvidenceCardList.tsx]
- [Source: apps/web/src/app/(main)/morning-report/page.tsx]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
