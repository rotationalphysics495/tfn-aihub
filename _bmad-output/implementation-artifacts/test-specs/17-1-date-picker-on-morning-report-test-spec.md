TEST SPEC START
story_id: 17-1-date-picker-on-morning-report
generated: 2026-02-12

test_specifications:

## AC1: Date picker placement — A date picker appears next to the "T-1 Data" badge in the MorningSummarySection header, defaulting to yesterday's date.

### 17-1-date-picker-on-morning-report-UNIT-001: DateNavigation renders date picker trigger with formatted date
- Priority: P0
- Type: unit
- Given: A DateNavigation component is rendered with `date` set to 2026-02-05
- When: The component mounts
- Then: A button is visible displaying "Feb 5, 2026" text and a CalendarIcon
- Data: `{ date: new Date(2026, 1, 5), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-002: DateNavigation opens calendar popover on trigger click
- Priority: P0
- Type: unit
- Given: A DateNavigation component is rendered with a valid date
- When: The user clicks the date trigger button
- Then: A calendar popover appears showing the month of the selected date with day cells
- Data: `{ date: new Date(2026, 1, 5), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-003: DateNavigation defaults to yesterday's date when rendered
- Priority: P0
- Type: unit
- Given: The DateNavigation component is rendered with `date` set to yesterday
- When: The component mounts
- Then: The trigger button displays yesterday's date formatted as "MMM d, yyyy"
- Data: `{ date: subDays(new Date(), 1), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-INT-001: Date picker appears next to badge in MorningSummarySection header
- Priority: P0
- Type: integration
- Given: MorningSummarySection is rendered with `reportDate` set to yesterday and `onDateChange` callback provided
- When: The component mounts
- Then: The DateNavigation component is visible within the header area alongside the "T-1 Data" badge
- Data: Mock `useDailyActions` and `useSmartSummary` returning default data; `reportDate` as yesterday in YYYY-MM-DD format

### 17-1-date-picker-on-morning-report-INT-002: Date picker renders in MorningReportClient with yesterday as default
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with no `date` query parameter in the URL
- When: The component mounts
- Then: The DateNavigation component is present and shows yesterday's date; all hooks are called without a reportDate (or with yesterday's date)
- Data: Mock `useSearchParams().get('date')` returning null; mock all data hooks with default returns

## AC2: Date change reloads all data — When the user selects a different date, all report sections reload with data for the selected date. URL updates. Badge updates.

### 17-1-date-picker-on-morning-report-INT-003: Selecting a date in calendar calls onDateChange with correct Date
- Priority: P0
- Type: integration
- Given: DateNavigation is rendered with date 2026-02-05 and the popover calendar is open
- When: The user clicks on day "10" (February 10) in the calendar
- Then: `onDateChange` is called with a Date object representing 2026-02-10
- Data: `{ date: new Date(2026, 1, 5), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-INT-004: Date change updates URL to include date query parameter
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered; the current date is yesterday (default)
- When: The user selects 2026-02-05 from the date picker
- Then: `router.push` is called with `/morning-report?date=2026-02-05` and `{ scroll: false }`
- Data: Mock `useRouter` returning `{ push: vi.fn() }`; mock `usePathname` returning `/morning-report`

### 17-1-date-picker-on-morning-report-INT-005: Date change causes useDailyActions to be called with new reportDate
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered and hooks are mocked
- When: The user selects 2026-02-05 from the date picker
- Then: `useDailyActions` is called with `{ reportDate: '2026-02-05' }` (or an options object containing that date)
- Data: Mock `useDailyActions` as `vi.fn()` to verify call arguments

### 17-1-date-picker-on-morning-report-INT-006: Date change causes useSmartSummary to be called with new reportDate
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered and hooks are mocked
- When: The user selects 2026-02-05 from the date picker
- Then: `useSmartSummary` is called with `{ reportDate: '2026-02-05' }` (or an options object containing that date)
- Data: Mock `useSmartSummary` as `vi.fn()` to verify call arguments

### 17-1-date-picker-on-morning-report-INT-007: Date change causes useWorkcenterSummary to be called with new date
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered and hooks are mocked
- When: The user selects 2026-02-05 from the date picker
- Then: `useWorkcenterSummary` is called with `{ date: '2026-02-05' }` (or an options object containing that date)
- Data: Mock `useWorkcenterSummary` as `vi.fn()` to verify call arguments

### 17-1-date-picker-on-morning-report-INT-008: Date change causes useScheduleAttainment to be called with new date
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered and hooks are mocked
- When: The user selects 2026-02-05 from the date picker
- Then: `useScheduleAttainment` is called with `{ date: '2026-02-05' }` (or an options object containing that date)
- Data: Mock `useScheduleAttainment` as `vi.fn()` to verify call arguments

### 17-1-date-picker-on-morning-report-UNIT-004: Badge shows "T-1 Data" when yesterday is selected
- Priority: P0
- Type: unit
- Given: MorningSummarySection is rendered with `reportDate` set to yesterday's date in YYYY-MM-DD format
- When: The component mounts
- Then: A Badge component displays text "T-1 Data"
- Data: `reportDate` = yesterday formatted as YYYY-MM-DD

### 17-1-date-picker-on-morning-report-UNIT-005: Badge shows formatted date when a non-yesterday date is selected
- Priority: P0
- Type: unit
- Given: MorningSummarySection is rendered with `reportDate` set to "2026-02-05"
- When: The component mounts
- Then: A Badge component displays text "Feb 5 Data" (not "T-1 Data")
- Data: `reportDate` = '2026-02-05'

### 17-1-date-picker-on-morning-report-UNIT-006: Header label updates from "Yesterday's Performance" for non-yesterday dates
- Priority: P1
- Type: unit
- Given: MorningSummarySection is rendered with `reportDate` set to "2026-02-05"
- When: The component mounts
- Then: The header label displays a dynamic text reflecting the selected date instead of "Yesterday's Performance"
- Data: `reportDate` = '2026-02-05', mock hooks with data containing `report_date: '2026-02-05'`

## AC3: Prev/next day arrows — Prev/next day arrow buttons displayed alongside date picker. Next arrow disabled when viewing yesterday.

### 17-1-date-picker-on-morning-report-UNIT-007: Prev and next arrow buttons are rendered alongside the date picker
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered with a date set to 5 days ago
- When: The component mounts
- Then: Two arrow buttons (ChevronLeft for prev, ChevronRight for next) are visible flanking the date trigger button
- Data: `{ date: subDays(new Date(), 5), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-008: Clicking prev arrow decrements date by one day
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered with date 2026-02-08
- When: The user clicks the prev (ChevronLeft) arrow button
- Then: `onDateChange` is called with a Date object representing 2026-02-07
- Data: `{ date: new Date(2026, 1, 8), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-009: Clicking next arrow increments date by one day
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered with date 2026-02-08 (more than 1 day before yesterday)
- When: The user clicks the next (ChevronRight) arrow button
- Then: `onDateChange` is called with a Date object representing 2026-02-09
- Data: `{ date: new Date(2026, 1, 8), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-010: Next arrow is disabled when viewing yesterday's date
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered with `date` set to yesterday
- When: The component mounts
- Then: The next (ChevronRight) arrow button has the `disabled` attribute and is not clickable
- Data: `{ date: subDays(new Date(), 1), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-011: Next arrow is enabled when viewing a date older than yesterday
- Priority: P1
- Type: unit
- Given: DateNavigation is rendered with `date` set to 3 days ago
- When: The component mounts
- Then: The next (ChevronRight) arrow button does NOT have the `disabled` attribute
- Data: `{ date: subDays(new Date(), 3), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-012: Prev arrow is always enabled (no lower bound restriction in AC)
- Priority: P1
- Type: unit
- Given: DateNavigation is rendered with a date far in the past (e.g., 2025-01-01)
- When: The component mounts
- Then: The prev (ChevronLeft) arrow button does NOT have the `disabled` attribute
- Data: `{ date: new Date(2025, 0, 1), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-013: Future dates are disabled in the calendar picker
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered and the calendar popover is open
- When: The user views the calendar for the current month
- Then: Today's date and all future dates are visually disabled and not selectable; only yesterday and earlier are selectable
- Data: `{ date: subDays(new Date(), 1), onDateChange: vi.fn() }`

### 17-1-date-picker-on-morning-report-UNIT-014: Clicking disabled next arrow does not call onDateChange
- Priority: P1
- Type: unit
- Given: DateNavigation is rendered with date set to yesterday (next arrow is disabled)
- When: The user attempts to click the next arrow button
- Then: `onDateChange` is NOT called
- Data: `{ date: subDays(new Date(), 1), onDateChange: vi.fn() }`

## AC4: URL-driven date on load — When URL has `date` query param, report shows data for that date and picker reflects it.

### 17-1-date-picker-on-morning-report-INT-009: Valid date in URL initializes the report to that date
- Priority: P0
- Type: integration
- Given: The URL contains `?date=2026-02-05`
- When: MorningReportClient mounts
- Then: The date picker displays "Feb 5, 2026"; all hooks are called with reportDate/date '2026-02-05'; the badge shows "Feb 5 Data"
- Data: Mock `useSearchParams().get('date')` returning '2026-02-05'

### 17-1-date-picker-on-morning-report-INT-010: Missing date param defaults to yesterday
- Priority: P0
- Type: integration
- Given: The URL is `/morning-report` with no `date` query parameter
- When: MorningReportClient mounts
- Then: The date picker displays yesterday's date; hooks are called with yesterday's date (or no reportDate); badge shows "T-1 Data"
- Data: Mock `useSearchParams().get('date')` returning null

### 17-1-date-picker-on-morning-report-INT-011: Invalid date string in URL falls back to yesterday
- Priority: P0
- Type: integration
- Given: The URL contains `?date=not-a-date`
- When: MorningReportClient mounts
- Then: The date picker displays yesterday's date; hooks are called with yesterday's date; badge shows "T-1 Data"
- Data: Mock `useSearchParams().get('date')` returning 'not-a-date'

### 17-1-date-picker-on-morning-report-INT-012: Future date in URL falls back to yesterday
- Priority: P0
- Type: integration
- Given: The URL contains `?date=2027-06-15` (a future date)
- When: MorningReportClient mounts
- Then: The date picker displays yesterday's date; hooks are called with yesterday's date; badge shows "T-1 Data"
- Data: Mock `useSearchParams().get('date')` returning '2027-06-15'

### 17-1-date-picker-on-morning-report-INT-013: Today's date in URL falls back to yesterday
- Priority: P0
- Type: integration
- Given: The URL contains `?date=` set to today's date
- When: MorningReportClient mounts
- Then: The date picker displays yesterday's date; hooks are called with yesterday's date (today is not valid since data is T-1)
- Data: Mock `useSearchParams().get('date')` returning today's date in YYYY-MM-DD format

### 17-1-date-picker-on-morning-report-INT-014: Partially valid date format in URL falls back to yesterday
- Priority: P1
- Type: integration
- Given: The URL contains `?date=2026-2-5` (missing leading zeros)
- When: MorningReportClient mounts
- Then: If the date parses to a valid past date, it is accepted; otherwise it falls back to yesterday. The behavior depends on implementation — test that no crash occurs and a valid date is displayed.
- Data: Mock `useSearchParams().get('date')` returning '2026-2-5'

## AC5: Empty state for missing data — When no daily_summaries records exist, show empty state. Picker and arrows remain functional.

### 17-1-date-picker-on-morning-report-INT-015: Empty state message shown when no data exists for selected date
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with a valid past date; `useDailyActions` returns null/empty data with `isLoading: false` and `error: null`
- When: The component finishes loading
- Then: A message "No production data available for {formatted date}" is displayed (e.g., "No production data available for February 5, 2026")
- Data: Mock `useDailyActions` returning `{ data: null, isLoading: false, error: null, hasActions: false, summary: { totalActions: 0, safetyCount: 0, oeeCount: 0, financialCount: 0 } }`

### 17-1-date-picker-on-morning-report-INT-016: Date picker remains functional during empty state
- Priority: P0
- Type: integration
- Given: MorningReportClient is in empty state (no data for the selected date)
- When: The user clicks the date picker trigger button
- Then: The calendar popover opens and is interactive; the user can select a different date
- Data: Mock hooks returning empty/null data; verify calendar opens on click

### 17-1-date-picker-on-morning-report-INT-017: Navigation arrows remain functional during empty state
- Priority: P0
- Type: integration
- Given: MorningReportClient is in empty state showing "No production data available for {date}"
- When: The user clicks the prev arrow button
- Then: The date decrements by one day; `router.push` is called with the new date; hooks are re-invoked with the new date
- Data: Mock hooks returning empty/null data; verify onDateChange triggers URL update

### 17-1-date-picker-on-morning-report-INT-018: Empty state distinguishes from loading state
- Priority: P1
- Type: integration
- Given: MorningReportClient is rendered and hooks return `isLoading: true`
- When: The component is in loading state
- Then: A loading skeleton/indicator is shown, NOT the "No production data available" empty state message
- Data: Mock `useDailyActions` returning `{ data: null, isLoading: true, error: null }`

### 17-1-date-picker-on-morning-report-INT-019: Empty state distinguishes from error state
- Priority: P1
- Type: integration
- Given: MorningReportClient is rendered and `useDailyActions` returns an error
- When: The component finishes loading with error
- Then: An error state is shown (not the "No production data available" empty state message)
- Data: Mock `useDailyActions` returning `{ data: null, isLoading: false, error: 'Network error' }`

edge_cases:
  - Timezone boundary: User near midnight in a timezone where `new Date()` could yield a different local date than expected. Date arithmetic should use date-fns (local time) rather than `toISOString().split('T')[0]` (UTC).
  - Rapid date changes: User rapidly clicking prev/next arrows should not cause race conditions in hook fetches. Each date change should cancel/supersede previous in-flight requests.
  - Month boundary in calendar: Navigating from Feb 1 backward via prev arrow should correctly go to Jan 31 of the same year.
  - Year boundary in calendar: Navigating from Jan 1 backward via prev arrow should correctly go to Dec 31 of the previous year.
  - Very old date selection: Selecting a date many years in the past (e.g., 2020-01-01) should work without errors, though data may be empty.
  - Browser back/forward navigation: After changing dates via the picker (which updates URL), browser back button should restore the previous date state.
  - page.tsx metadata export preserved: After refactoring page.tsx to render MorningReportClient, the `metadata` export must still work (page.tsx remains a Server Component).
  - Suspense boundary: MorningReportClient using useSearchParams must be wrapped in a Suspense boundary in page.tsx to avoid deopting the page to full client rendering.

error_scenarios:
  - Invalid date format in URL (e.g., `?date=abc`, `?date=2026-13-45`, `?date=`) should all gracefully fall back to yesterday.
  - Future date in URL (today or beyond) should fall back to yesterday without error.
  - Hook fetch failure after date change: If useDailyActions or useSmartSummary returns an error after a date change, the error state should be shown, not the empty state, and the date picker/arrows should remain functional.
  - Calendar popover should close after a date is selected (standard Shadcn popover behavior).
  - Network timeout during data reload: Date picker and arrows should remain interactive regardless of hook loading/error states.

test_file_mapping:
  - 17-1-date-picker-on-morning-report-UNIT-001 through UNIT-014: apps/web/src/components/report/__tests__/DateNavigation.test.tsx
  - 17-1-date-picker-on-morning-report-UNIT-004 through UNIT-006: apps/web/src/components/action-list/__tests__/MorningSummarySection.date.test.tsx
  - 17-1-date-picker-on-morning-report-INT-001: apps/web/src/components/action-list/__tests__/MorningSummarySection.date.test.tsx
  - 17-1-date-picker-on-morning-report-INT-002 through INT-019: apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx

TEST SPEC END
