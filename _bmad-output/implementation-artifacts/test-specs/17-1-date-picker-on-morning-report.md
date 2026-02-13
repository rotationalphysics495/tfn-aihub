TEST SPEC START
story_id: 17-1-date-picker-on-morning-report
generated: 2026-02-12

test_specifications:

## AC1: Date picker placement — A date picker appears next to the "T-1 Data" badge in the MorningSummarySection header, defaulting to yesterday's date.

### 17-1-date-picker-on-morning-report-UNIT-001: DateNavigation renders calendar trigger button with formatted yesterday's date
- Priority: P0
- Type: unit
- Given: DateNavigation component is rendered with `date` prop set to yesterday
- When: The component mounts
- Then: A button is visible displaying the formatted date (e.g., "Feb 11, 2026") and a calendar icon. The date shown matches yesterday's date.
- Data: `date = new Date()` minus 1 day

### 17-1-date-picker-on-morning-report-UNIT-002: DateNavigation opens calendar popover on trigger click
- Priority: P0
- Type: unit
- Given: DateNavigation component is rendered with a valid date
- When: The user clicks the date trigger button
- Then: A calendar popover opens showing a month view with the selected date highlighted
- Data: `date = new Date('2026-02-11')`

### 17-1-date-picker-on-morning-report-UNIT-003: DateNavigation disables future dates in the calendar
- Priority: P0
- Type: unit
- Given: DateNavigation component is rendered and the calendar popover is open
- When: The user views the calendar
- Then: All dates from today onwards are disabled (not selectable). Yesterday and earlier dates remain selectable.
- Data: `date = yesterday`, calendar rendered with `disabled` prop filtering future dates

### 17-1-date-picker-on-morning-report-INT-001: DateNavigation is positioned next to the badge in MorningSummarySection header
- Priority: P0
- Type: integration
- Given: MorningSummarySection is rendered with `reportDate` set to yesterday and a `onDateChange` callback
- When: The component mounts
- Then: The DateNavigation component (date picker trigger + arrows) appears in the header area alongside the data badge. Both the badge and the date picker are visible in the header row.
- Data: `reportDate = '2026-02-11'`, mock `useDailyActions` and `useSmartSummary` returning valid data

### 17-1-date-picker-on-morning-report-UNIT-004: DateNavigation defaults display to yesterday when given yesterday's date
- Priority: P1
- Type: unit
- Given: DateNavigation is rendered with `date` set to yesterday
- When: The component mounts
- Then: The trigger button shows yesterday's formatted date (e.g., "Feb 11, 2026")
- Data: `date = yesterday`


## AC2: Date change reloads all data — When the user selects a different date, all report sections reload with data for the selected date. The URL updates to `/morning-report?date=YYYY-MM-DD`. The "T-1 Data" badge updates to reflect the selected date.

### 17-1-date-picker-on-morning-report-INT-002: Selecting a date in the calendar calls onDateChange with the selected date
- Priority: P0
- Type: integration
- Given: DateNavigation is rendered with `date = 2026-02-11` and an `onDateChange` spy
- When: The user opens the calendar popover and clicks on February 5
- Then: `onDateChange` is called with a Date object representing 2026-02-05
- Data: `onDateChange = vi.fn()`

### 17-1-date-picker-on-morning-report-INT-003: Date change updates URL with date query parameter
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered at `/morning-report` (no date param, defaults to yesterday)
- When: The user selects a different date (e.g., 2026-02-05) via the date picker
- Then: `router.push` is called with `/morning-report?date=2026-02-05` and `{ scroll: false }`
- Data: Mock `useRouter` with `push` spy, mock `useSearchParams` returning null initially

### 17-1-date-picker-on-morning-report-INT-004: Date change threads reportDate to MorningSummarySection
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with a selected date of 2026-02-05
- When: The component renders its children
- Then: `useDailyActions` is called with `{ reportDate: '2026-02-05' }` and `useSmartSummary` is called with `{ reportDate: '2026-02-05' }` inside MorningSummarySection
- Data: Mock hooks to verify call arguments

### 17-1-date-picker-on-morning-report-INT-005: Date change threads reportDate to InsightEvidenceCardList
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with a selected date of 2026-02-05
- When: The component renders its children
- Then: `useDailyActions` inside InsightEvidenceCardList is called with `{ reportDate: '2026-02-05' }`
- Data: Mock `useDailyActions` to verify call arguments

### 17-1-date-picker-on-morning-report-UNIT-005: Badge shows "T-1 Data" when selected date is yesterday
- Priority: P0
- Type: unit
- Given: MorningSummarySection is rendered with `reportDate` set to yesterday's date string
- When: The component mounts
- Then: The badge displays "T-1 Data"
- Data: `reportDate = yesterday in YYYY-MM-DD format`

### 17-1-date-picker-on-morning-report-UNIT-006: Badge shows formatted date when selected date is NOT yesterday
- Priority: P0
- Type: unit
- Given: MorningSummarySection is rendered with `reportDate = '2026-02-05'` (not yesterday)
- When: The component mounts
- Then: The badge displays "Feb 5 Data" (not "T-1 Data")
- Data: `reportDate = '2026-02-05'`

### 17-1-date-picker-on-morning-report-INT-006: Date change threads reportDate to WorkcenterScorecard and ScheduleAttainment
- Priority: P1
- Type: integration
- Given: MorningReportClient is rendered with a selected date of 2026-02-05
- When: The component renders its children
- Then: WorkcenterScorecard and ScheduleAttainment components receive `reportDate='2026-02-05'` as a prop, and their underlying hooks are called with the correct date parameter
- Data: Mock `useWorkcenterSummary` and `useScheduleAttainment` to verify call arguments


## AC3: Prev/next day arrows — Prev/next day arrow buttons are displayed alongside the date picker. Clicking them increments/decrements the date by one day and reloads the report. The "next" arrow is disabled when viewing yesterday.

### 17-1-date-picker-on-morning-report-UNIT-007: Prev and next arrow buttons are rendered alongside the date picker
- Priority: P0
- Type: unit
- Given: DateNavigation component is rendered with a valid date
- When: The component mounts
- Then: Two icon buttons (prev/left arrow and next/right arrow) are visible flanking the date picker trigger button
- Data: `date = new Date('2026-02-05')`

### 17-1-date-picker-on-morning-report-UNIT-008: Clicking prev arrow decrements date by one day
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered with `date = 2026-02-10` and an `onDateChange` spy
- When: The user clicks the prev (left) arrow button
- Then: `onDateChange` is called with a Date object representing 2026-02-09
- Data: `onDateChange = vi.fn()`

### 17-1-date-picker-on-morning-report-UNIT-009: Clicking next arrow increments date by one day
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered with `date = 2026-02-05` and an `onDateChange` spy
- When: The user clicks the next (right) arrow button
- Then: `onDateChange` is called with a Date object representing 2026-02-06
- Data: `onDateChange = vi.fn()`

### 17-1-date-picker-on-morning-report-UNIT-010: Next arrow is disabled when viewing yesterday's date
- Priority: P0
- Type: unit
- Given: DateNavigation is rendered with `date` set to yesterday
- When: The component mounts
- Then: The next (right) arrow button has `disabled` attribute and is not clickable. Clicking it does NOT call `onDateChange`.
- Data: `date = yesterday`, `onDateChange = vi.fn()`

### 17-1-date-picker-on-morning-report-UNIT-011: Next arrow is enabled when viewing a date older than yesterday
- Priority: P1
- Type: unit
- Given: DateNavigation is rendered with `date = 2026-02-05` (several days before yesterday)
- When: The component mounts
- Then: The next (right) arrow button is enabled and does NOT have the `disabled` attribute
- Data: `date = new Date('2026-02-05')`

### 17-1-date-picker-on-morning-report-UNIT-012: Prev arrow is always enabled (no minimum date restriction unless implemented)
- Priority: P2
- Type: unit
- Given: DateNavigation is rendered with a date far in the past (e.g., 2025-01-01)
- When: The component mounts
- Then: The prev (left) arrow button is enabled
- Data: `date = new Date('2025-01-01')`


## AC4: URL-driven date on load — When a URL with a `date` query parameter is loaded directly, the report shows data for the specified date and the date picker reflects the URL date.

### 17-1-date-picker-on-morning-report-INT-007: URL with valid date param initializes report to that date
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with URL search params containing `date=2026-02-05`
- When: The component mounts
- Then: The date picker shows "Feb 5, 2026", the badge shows "Feb 5 Data", and all data hooks are called with `reportDate: '2026-02-05'`
- Data: Mock `useSearchParams` to return `{ get: () => '2026-02-05' }`

### 17-1-date-picker-on-morning-report-INT-008: URL with no date param defaults to yesterday
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with URL search params containing no `date` key
- When: The component mounts
- Then: The date picker shows yesterday's formatted date, the badge shows "T-1 Data", and all data hooks are called with `reportDate` set to yesterday's YYYY-MM-DD string
- Data: Mock `useSearchParams` to return `{ get: () => null }`

### 17-1-date-picker-on-morning-report-INT-009: URL with invalid date param falls back to yesterday
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with URL search params containing `date=not-a-date`
- When: The component mounts
- Then: The invalid date is ignored, the date picker shows yesterday's date, and hooks receive yesterday's date as `reportDate`
- Data: Mock `useSearchParams` to return `{ get: () => 'not-a-date' }`

### 17-1-date-picker-on-morning-report-INT-010: URL with future date param falls back to yesterday
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with URL search params containing `date=2027-01-01` (a future date)
- When: The component mounts
- Then: The future date is rejected, the date picker shows yesterday's date, and hooks receive yesterday's date as `reportDate`
- Data: Mock `useSearchParams` to return `{ get: () => '2027-01-01' }`

### 17-1-date-picker-on-morning-report-INT-011: URL with today's date falls back to yesterday
- Priority: P1
- Type: integration
- Given: MorningReportClient is rendered with URL search params containing `date=` set to today's date (today is not navigable)
- When: The component mounts
- Then: Today's date is rejected (only T-1 and earlier are valid), the date picker shows yesterday's date
- Data: Mock `useSearchParams` to return today's date string


## AC5: Empty state for missing data — When the selected date has no `daily_summaries` records, an empty state is shown: "No production data available for {date}". The date picker and navigation arrows remain functional.

### 17-1-date-picker-on-morning-report-INT-012: Empty state message shown when no data exists for selected date
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with a selected date of 2025-01-15, and `useDailyActions` returns null/empty data for that date
- When: The component finishes loading
- Then: The text "No production data available for January 15, 2025" (or equivalent formatted date) is displayed
- Data: Mock `useDailyActions` returning `{ data: null, isLoading: false, error: null, hasActions: false }`

### 17-1-date-picker-on-morning-report-INT-013: Date picker remains functional during empty state
- Priority: P0
- Type: integration
- Given: MorningReportClient is showing the empty state for a date with no data
- When: The user clicks the date picker trigger
- Then: The calendar popover opens and allows date selection. Selecting a new date triggers data reload.
- Data: Empty data state, `onDateChange` or `router.push` spy

### 17-1-date-picker-on-morning-report-INT-014: Navigation arrows remain functional during empty state
- Priority: P0
- Type: integration
- Given: MorningReportClient is showing the empty state for date 2025-01-15
- When: The user clicks the prev arrow button
- Then: The date decrements to 2025-01-14 and a data reload is triggered (URL updates)
- Data: Empty data state, mock router.push spy

### 17-1-date-picker-on-morning-report-INT-015: Empty state message uses correctly formatted date
- Priority: P1
- Type: integration
- Given: MorningReportClient is rendered and `useDailyActions` returns no data for 2026-02-05
- When: The empty state is displayed
- Then: The message reads "No production data available for February 5, 2026" (or the project's chosen date format) — the date in the message matches the selected date, not yesterday.
- Data: `reportDate = '2026-02-05'`, empty hook response


edge_cases:
  - Timezone boundary: Date calculations near midnight could yield incorrect yesterday date depending on timezone. Test that date logic uses local dates consistently (date-fns `subDays` preferred over manual `Date.now() - 86400000`).
  - Rapid date changes: User clicks prev arrow multiple times quickly. Each click should produce the correct sequential date without race conditions in URL or state updates.
  - Calendar month boundary navigation: Selecting a date in a different month (e.g., going from Feb 5 to Jan 31) should work correctly through the calendar popover.
  - Very old dates: Selecting a date years in the past (e.g., 2020-01-01) should still function — the calendar should allow navigation and the empty state should handle gracefully.
  - Date format edge case in URL: Dates like `2026-2-5` (without zero-padding) vs `2026-02-05` — the parser should handle both or only accept the canonical YYYY-MM-DD format.
  - Server Component metadata preservation: After refactoring page.tsx to render MorningReportClient, the `metadata` export must still work (page.tsx remains a Server Component).

error_scenarios:
  - Invalid date string in URL (e.g., `?date=abc`, `?date=2026-13-45`, `?date=`) should fall back to yesterday without errors.
  - Future date in URL (`?date=2027-01-01`) should fall back to yesterday.
  - Network error while loading data for a selected date — the date picker and arrows should remain functional even if hooks return an error state.
  - Partial date in URL (e.g., `?date=2026-02`) should be treated as invalid and fall back to yesterday.

test_file_mapping:
  - 17-1-date-picker-on-morning-report-UNIT-*: apps/web/src/components/report/__tests__/DateNavigation.test.tsx
  - 17-1-date-picker-on-morning-report-INT-001: apps/web/src/components/action-list/__tests__/MorningSummarySection.date.test.tsx
  - 17-1-date-picker-on-morning-report-INT-002: apps/web/src/components/report/__tests__/DateNavigation.test.tsx
  - 17-1-date-picker-on-morning-report-INT-003 through INT-015: apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx

TEST SPEC END
