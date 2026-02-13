# Epic 18 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 18
**Started:** 2026-02-12 08:00:59

---


## DESIGN: 18-1-meeting-mode-toggle-talking-points-view
**Timestamp:** 2026-02-12 08:05:49

DESIGN START
story_id: 18-1-meeting-mode-toggle-talking-points-view

files_to_modify:
  - path: apps/web/src/components/ui/toggle.tsx
    action: create
    purpose: Install Shadcn/UI Toggle primitive via CLI (`npx shadcn-ui@latest add toggle`). Provides the pressed/unpressed toggle button primitive used by MeetingModeToggle.

  - path: apps/web/src/components/report/MeetingModeToggle.tsx
    action: create
    purpose: Toggle button component that switches between normal and meeting mode. Uses Shadcn Toggle with Presentation (lucide) icon, "Meeting Mode" label, Industrial Clarity styling (18px+ text, high-contrast). Emits `onToggle(isMeeting: boolean)` callback. Accepts `pressed` prop for controlled state.

  - path: apps/web/src/components/report/MeetingModeView.tsx
    action: create
    purpose: Meeting mode layout component. Groups top 3-5 action items (sorted by priority, sliced) into three sections by category: "Safety" (category==='safety'), "Yesterday's Performance" (category==='oee'), "Today's Priorities" (category==='financial'). Renders section headers with large text and MeetingTalkingPoint cards. Shows "No items" text for empty sections (never hides the header). Receives transformed ActionItem[] + followUps Map + onAssign callback.

  - path: apps/web/src/components/action-list/MeetingTalkingPoint.tsx
    action: create
    purpose: Condensed action card for meeting mode. Large card showing: PriorityBadge, headline text (24px+, text-xl md:text-2xl), asset name, AssignmentBadge (if follow-up exists). No evidence section, no metrics row, no drill-down chevron. Prominent "Assign Follow-Up" Button with UserPlus icon always visible (not in menu). 4px left border via getPriorityBorderColor(). Uses role="article" and ARIA labels. Opens AssignFollowUpDialog on button click.

  - path: apps/web/src/app/(main)/morning-report/MorningReportClient.tsx
    action: modify
    purpose: Add meeting mode state management. (1) Read `mode` from searchParams and initialize `isMeetingMode` state. (2) Add `handleMeetingModeToggle` callback that updates URL with `?mode=meeting` while preserving existing `date` and `shift` params using URLSearchParams. (3) Add MeetingModeToggle to page header area. (4) Conditionally render MeetingModeView (when meeting mode) vs existing normal mode layout (MorningSummarySection + MyAssignmentsPanel + ShiftTabs + WorkcenterScorecard + ScheduleAttainment + InsightEvidenceCardList). (5) In meeting mode, still show SafetyAlertsSection and MorningSummarySection (for date navigation), but hide MyAssignmentsPanel, ShiftTabs, WorkcenterScorecard, ScheduleAttainment, and the full InsightEvidenceCardList. (6) Pass transformed action data and follow-ups to MeetingModeView using the same useDailyActions hook (no duplicate fetch).

  - path: apps/web/src/components/action-list/index.ts
    action: modify
    purpose: Add export for MeetingTalkingPoint component.

patterns_to_use:
  - URL search params state sync: Follow existing pattern in MorningReportClient where `date` and `shift` params are read from `useSearchParams()` on init, and updated via `router.push()` with `{ scroll: false }`. Use URLSearchParams to merge all params (`date`, `shift`, `mode`).
  - Data transformation: Use `transformAPIActionItems()` from `action-engine/transformers.ts` to convert useDailyActions API response to the Insight+Evidence ActionItem type, which has `.priority` (PriorityType), `.recommendation.text`, `.asset.name` etc.
  - Priority sorting: Reuse the PRIORITY_ORDER pattern from ActionCardList.tsx (SAFETY=0, FINANCIAL=1, OEE=2) then by priorityScore descending, then slice to top 3-5.
  - Follow-up data: Use existing `useFollowUps({ reportDate })` hook which returns `Map<string, FollowUpData>` keyed by action_item_id. Pass this map to MeetingModeView/MeetingTalkingPoint.
  - Assignment dialog: Reuse existing `AssignFollowUpDialog` component. Open it from MeetingTalkingPoint's "Assign Follow-Up" button click, same pattern as InsightEvidenceCard.
  - Priority styling: Reuse `PriorityBadge`, `getPriorityBorderColor()`, `getPriorityAccentBg()` from `action-engine/PriorityBadge.tsx`.
  - Assignment badges: Reuse `AssignmentBadge` from `action-engine/AssignmentBadge.tsx`.
  - Industrial Clarity: Headlines at text-xl md:text-2xl (24px+), body text at text-base/text-lg (18px+), safety-red exclusively for safety items.

dependencies:
  - @radix-ui/react-toggle: needs-install (installed via `npx shadcn-ui@latest add toggle` which will also create toggle.tsx)
  - lucide-react: installed (already used throughout — need `Presentation` icon)
  - next/navigation: installed (useSearchParams, useRouter, usePathname already in use)
  - All other deps (date-fns, @/components/ui/*, etc.): installed

acceptance_criteria_mapping:
  - AC1 (Toggle button switches to condensed layout with top 3-5 items, section headers, URL update):
    - MeetingModeToggle.tsx: renders toggle button in header, emits onToggle
    - MorningReportClient.tsx: handleMeetingModeToggle updates isMeetingMode state + URL (?mode=meeting), conditionally renders MeetingModeView vs normal view
    - MeetingModeView.tsx: groups items into "Safety" / "Yesterday's Performance" / "Today's Priorities" sections, limits to top 3-5 items
    - MeetingTalkingPoint.tsx: renders large card with headline, asset, priority, assigned-to; hides evidence detail
  - AC2 (Assign Follow-Up button prominent, assignment badges visible):
    - MeetingTalkingPoint.tsx: renders prominent Button with UserPlus icon always visible (not in overflow menu), opens AssignFollowUpDialog on click
    - MeetingTalkingPoint.tsx: renders AssignmentBadge from existing component when followUp data exists for the item
    - MeetingModeView.tsx: passes followUps map and onFollowUpAssigned callback through to each MeetingTalkingPoint
  - AC3 (Toggle back restores full report):
    - MorningReportClient.tsx: when isMeetingMode is false, renders existing normal mode layout unchanged (MorningSummarySection + MyAssignmentsPanel + ShiftTabs + WorkcenterScorecard + ScheduleAttainment + InsightEvidenceCardList)
  - AC4 (URL ?mode=meeting activates meeting mode on page load):
    - MorningReportClient.tsx: initializes isMeetingMode from `searchParams.get('mode') === 'meeting'` in useState initializer (same pattern as date/shift params)

risks:
  - Toggle primitive dependency: `npx shadcn-ui@latest add toggle` might fail or produce slightly different output depending on shadcn version. Mitigation: verify the CLI version matches project config in `components.json`, and fall back to manual creation of toggle.tsx from shadcn docs if needed.
  - Action item count < 3: If the daily action list has fewer than 3 items, meeting mode will show fewer cards than expected. Mitigation: this is acceptable — just show however many exist (1-5), the "3-5" is a max not a requirement.
  - Category mapping gaps: Action items with unexpected category values won't appear in any section. Mitigation: add a fallback — unmapped categories go into "Today's Priorities" section.
  - Data duplication: MorningReportClient already calls useDailyActions for empty state detection; InsightEvidenceCardList calls it again internally. In meeting mode, we'll need transformed data directly. Mitigation: lift data fetching — use the existing useDailyActions call in MorningReportClient and pass data down to both normal and meeting views, rather than having InsightEvidenceCardList fetch independently. InsightEvidenceCardList already accepts a `reportDate` prop and fetches internally, so for meeting mode we'll do the transform ourselves in MorningReportClient and pass to MeetingModeView.
  - URL param merging: Toggling meeting mode must preserve date and shift params. Mitigation: use URLSearchParams to read all current params, set/delete `mode`, and push the full query string.

estimated_test_files:
  - apps/web/src/components/report/__tests__/MeetingModeToggle.test.tsx: Tests toggle renders with Presentation icon and "Meeting Mode" label, pressed/unpressed states, calls onToggle with correct boolean, keyboard activation (Enter/Space), meets accessibility requirements (aria-pressed).
  - apps/web/src/components/action-list/__tests__/MeetingTalkingPoint.test.tsx: Tests card renders headline, asset name, PriorityBadge, 4px priority border; AssignmentBadge shown when followUp provided; "Assign Follow-Up" button always visible and prominent; evidence detail NOT rendered; role="article" and ARIA labels present; dark mode class compatibility.
  - apps/web/src/components/report/__tests__/MeetingModeView.test.tsx: Tests grouping into 3 sections (Safety/Yesterday's Performance/Today's Priorities); shows "No items" for empty sections; limits to top 5 items max; renders MeetingTalkingPoint for each item; section headers have correct text.
  - apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx: Tests meeting mode initializes from URL (?mode=meeting); toggle updates URL and view; toggling back restores normal mode; date and shift params preserved during toggle; conditional rendering of MeetingModeView vs normal view.

implementation_order:
  1. Install Shadcn Toggle primitive: run `npx shadcn-ui@latest add toggle` in apps/web to create components/ui/toggle.tsx and install @radix-ui/react-toggle dependency.
  2. Create MeetingModeToggle component (apps/web/src/components/report/MeetingModeToggle.tsx): controlled toggle button with Presentation icon, "Meeting Mode" label, Industrial Clarity styling, onToggle callback.
  3. Create MeetingTalkingPoint card component (apps/web/src/components/action-list/MeetingTalkingPoint.tsx): condensed card with priority border, PriorityBadge, headline (24px+), asset name, prominent "Assign Follow-Up" button, AssignmentBadge display. Integrates with AssignFollowUpDialog.
  4. Update action-list/index.ts to export MeetingTalkingPoint.
  5. Create MeetingModeView layout component (apps/web/src/components/report/MeetingModeView.tsx): accepts transformed items + followUps, sorts by priority, slices to top 5, groups by category into three sections with headers, renders MeetingTalkingPoint per item, shows "No items" for empty sections.
  6. Modify MorningReportClient.tsx: (a) add isMeetingMode state initialized from URL, (b) add handleMeetingModeToggle with URLSearchParams-based URL update preserving date+shift, (c) add MeetingModeToggle to page header, (d) add data transformation for meeting mode using transformAPIActionItems + useFollowUps, (e) conditionally render MeetingModeView vs existing normal layout.
  7. Write tests for MeetingModeToggle, MeetingTalkingPoint, MeetingModeView, and MorningReportClient meeting mode integration.
  8. Verify dark mode support, keyboard navigation, and accessibility for all new components.
DESIGN END

---

## TEST_SPEC: 18-1-meeting-mode-toggle-talking-points-view
**Timestamp:** 2026-02-12 08:09:32

TEST SPEC START
story_id: 18-1-meeting-mode-toggle-talking-points-view
generated: 2026-02-12

test_specifications:

## AC1: Given the morning report page is in normal mode, When the user clicks a "Meeting Mode" toggle button in the report header, Then the view switches to a condensed layout showing top 3-5 action items as large cards with headline, asset, priority, and who's assigned; evidence detail is hidden; clear section headers "Safety" / "Yesterday's Performance" / "Today's Priorities"; and the URL updates to include ?mode=meeting.

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-001: MeetingModeToggle renders with Presentation icon and label
- Priority: P0
- Type: unit
- Given: MeetingModeToggle component is rendered with `pressed={false}` and an `onToggle` callback
- When: The component mounts
- Then: A toggle button is visible with the text "Meeting Mode" AND a Presentation (lucide-react) icon is rendered AND the button has `aria-pressed="false"` AND text is at least 18px (text-base or text-lg class)
- Data: `{ pressed: false, onToggle: vi.fn() }`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-002: MeetingModeToggle emits onToggle(true) when clicked from unpressed state
- Priority: P0
- Type: unit
- Given: MeetingModeToggle is rendered with `pressed={false}` and an `onToggle` spy
- When: The user clicks the toggle button
- Then: The `onToggle` callback is called with `true`
- Data: `{ pressed: false, onToggle: vi.fn() }`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-003: MeetingModeToggle shows pressed state when pressed prop is true
- Priority: P0
- Type: unit
- Given: MeetingModeToggle is rendered with `pressed={true}`
- When: The component mounts
- Then: The toggle button has `aria-pressed="true"` AND has the active/pressed visual styling (data-state="on" or pressed variant class)
- Data: `{ pressed: true, onToggle: vi.fn() }`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-004: MeetingModeToggle is keyboard accessible via Enter and Space
- Priority: P1
- Type: unit
- Given: MeetingModeToggle is rendered with `pressed={false}` and an `onToggle` spy
- When: The user focuses the toggle and presses Enter, then presses Space
- Then: The `onToggle` callback is invoked on each keypress (Enter and Space both trigger the toggle)
- Data: `{ pressed: false, onToggle: vi.fn() }`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-005: MeetingTalkingPoint renders large card with headline, asset, and priority
- Priority: P0
- Type: unit
- Given: A MeetingTalkingPoint component is rendered with a transformed ActionItem containing `recommendation.text = "Replace worn bearing on Grinder-04"`, `asset.name = "Grinder-04"`, `priority = "SAFETY"`
- When: The component mounts
- Then: The headline "Replace worn bearing on Grinder-04" is displayed at 24px+ size (text-xl or text-2xl class) AND "Grinder-04" asset name is visible AND a PriorityBadge with SAFETY level is rendered AND the card has a 4px left border with the safety priority color AND the card has `role="article"` AND appropriate ARIA labels are present
- Data: ActionItem fixture with `priority: 'SAFETY'`, `recommendation: { text: 'Replace worn bearing on Grinder-04', summary: 'Replace bearing' }`, `asset: { id: 'a1', name: 'Grinder-04', area: 'Grinding' }`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-006: MeetingTalkingPoint hides evidence detail sections
- Priority: P0
- Type: unit
- Given: A MeetingTalkingPoint component is rendered with a complete ActionItem that includes evidence data
- When: The component mounts
- Then: No EvidenceSection content is rendered AND no metrics row is visible AND no drill-down chevron is present AND no evidence source references are shown
- Data: ActionItem fixture with full evidence object (`type: 'oee_deviation'`, `data: { targetOEE: 85, actualOEE: 72, deviation: -13, timeframe: '...' }`)

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-007: MeetingModeView groups items into three section headers
- Priority: P0
- Type: unit
- Given: MeetingModeView is rendered with action items spanning all three categories: 1 safety item, 1 oee item, 1 financial item
- When: The component mounts
- Then: Three section headers are rendered with text "Safety", "Yesterday's Performance", and "Today's Priorities" AND each section contains its corresponding action item card(s)
- Data: Array of 3 ActionItems with categories mapped as: safety → "Safety", oee → "Yesterday's Performance", financial → "Today's Priorities"

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-008: MeetingModeView limits display to top 3-5 items sorted by priority
- Priority: P0
- Type: unit
- Given: MeetingModeView is rendered with 10 action items of varying priority scores
- When: The component mounts
- Then: Only the top 5 items (by priority sort order: SAFETY first, then FINANCIAL, then OEE, then by priorityScore descending) are rendered as MeetingTalkingPoint cards AND items ranked 6-10 are not visible
- Data: Array of 10 ActionItems with mixed categories and priority scores

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-009: MeetingModeView shows "No items" for empty sections
- Priority: P1
- Type: unit
- Given: MeetingModeView is rendered with 2 oee items and 0 safety items and 0 financial items
- When: The component mounts
- Then: The "Safety" section header is still rendered AND displays "No items" text below it AND the "Today's Priorities" section header is still rendered AND displays "No items" text below it AND the "Yesterday's Performance" section renders its 2 items
- Data: Array of 2 ActionItems with `category: 'oee'` only

### 18-1-meeting-mode-toggle-talking-points-view-INT-001: Toggle activates meeting mode and updates URL
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered in normal mode (no `?mode=meeting` in URL) with mock daily actions data containing 3 action items
- When: The user clicks the "Meeting Mode" toggle button
- Then: The MeetingModeView layout is rendered (condensed cards visible) AND the normal report sections (InsightEvidenceCardList, WorkcenterScorecard, ScheduleAttainment) are hidden AND `router.push` is called with URL containing `mode=meeting` parameter
- Data: Mock useDailyActions returning 3 items (1 safety, 1 oee, 1 financial), mockSearchParamsGet returning null for 'mode'

### 18-1-meeting-mode-toggle-talking-points-view-INT-002: URL preserves existing date and shift params when toggling meeting mode
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered with URL params `?date=2026-02-05&shift=day` (no meeting mode)
- When: The user clicks the "Meeting Mode" toggle button
- Then: `router.push` is called with a URL containing `date=2026-02-05` AND `shift=day` AND `mode=meeting` (all three params preserved)
- Data: mockSearchParamsGet returning '2026-02-05' for 'date', 'day' for 'shift', null for 'mode'

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-010: MeetingModeView renders correctly with fewer than 3 items
- Priority: P1
- Type: unit
- Given: MeetingModeView is rendered with only 1 action item
- When: The component mounts
- Then: The single item is rendered as a MeetingTalkingPoint card AND the two empty sections show "No items" AND no errors are thrown
- Data: Array of 1 ActionItem with `category: 'safety'`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-011: MeetingModeView renders correctly with 0 items
- Priority: P1
- Type: unit
- Given: MeetingModeView is rendered with an empty action items array
- When: The component mounts
- Then: All three section headers ("Safety", "Yesterday's Performance", "Today's Priorities") are visible AND each shows "No items" text AND no MeetingTalkingPoint cards are rendered
- Data: Empty array `[]`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-012: MeetingTalkingPoint applies correct priority border color
- Priority: P1
- Type: unit
- Given: Three MeetingTalkingPoint cards rendered with priorities SAFETY, FINANCIAL, and OEE respectively
- When: The components mount
- Then: Each card has a 4px left border with the color matching `getPriorityBorderColor()` for its priority level (safety-red for SAFETY, amber for FINANCIAL, blue for OEE)
- Data: Three ActionItem fixtures with different `priority` values

## AC2: Given the meeting mode view is active, When the user views an action item, Then the "Assign Follow-Up" button is prominently visible (not in a menu) And assignment badges are visible by default showing who's already assigned.

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-013: MeetingTalkingPoint shows prominent Assign Follow-Up button
- Priority: P0
- Type: unit
- Given: A MeetingTalkingPoint is rendered with an action item that has no existing follow-up assignment
- When: The component mounts
- Then: A Button with text "Assign Follow-Up" is visible in the DOM (not hidden in a dropdown or overflow menu) AND the button includes a UserPlus icon AND the button is not within any collapsed, popover, or dropdown container
- Data: ActionItem fixture with no followUp data (followUp = undefined)

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-014: MeetingTalkingPoint displays assignment badge when follow-up exists
- Priority: P0
- Type: unit
- Given: A MeetingTalkingPoint is rendered with an action item AND a matching FollowUpData record with `assignee_email = "john.doe@factory.com"` and `status = "assigned"`
- When: The component mounts
- Then: An AssignmentBadge is visible showing the assignee information ("john.doe@factory.com" or derived display name) AND the badge has the correct status variant styling for "assigned"
- Data: ActionItem fixture + FollowUpData fixture `{ assignee_email: 'john.doe@factory.com', status: 'assigned' }`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-015: MeetingTalkingPoint Assign Follow-Up button opens assignment dialog
- Priority: P1
- Type: unit
- Given: A MeetingTalkingPoint is rendered with an action item and an `onAssign` callback
- When: The user clicks the "Assign Follow-Up" button
- Then: The AssignFollowUpDialog is opened (dialog becomes visible in the DOM) with the correct action item data pre-filled
- Data: ActionItem fixture, `onAssign: vi.fn()`

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-016: MeetingTalkingPoint shows assignment badge with in_progress status
- Priority: P2
- Type: unit
- Given: A MeetingTalkingPoint is rendered with a FollowUpData record with `status = "in_progress"`
- When: The component mounts
- Then: The AssignmentBadge displays the "in_progress" status variant (distinct visual styling from "assigned")
- Data: FollowUpData fixture with `{ status: 'in_progress', assignee_email: 'jane@factory.com' }`

### 18-1-meeting-mode-toggle-talking-points-view-INT-003: Meeting mode view passes follow-up data to talking point cards
- Priority: P0
- Type: integration
- Given: MeetingModeView is rendered with 3 action items AND a followUps Map containing entries for 2 of the 3 items
- When: The component mounts
- Then: The 2 items with follow-ups render AssignmentBadges AND the 1 item without a follow-up does not render an AssignmentBadge but does render the "Assign Follow-Up" button
- Data: 3 ActionItem fixtures, `Map<string, FollowUpData>` with 2 entries keyed by action_item_id

## AC3: Given the user clicks the toggle again, When switching back to normal mode, Then the full report view is restored with all evidence and detail sections.

### 18-1-meeting-mode-toggle-talking-points-view-INT-004: Toggle back to normal mode restores full report view
- Priority: P0
- Type: integration
- Given: MorningReportClient is rendered in meeting mode (isMeetingMode = true, URL has `?mode=meeting`)
- When: The user clicks the "Meeting Mode" toggle button again
- Then: The MeetingModeView is no longer rendered AND the normal mode components are restored (MorningSummarySection, InsightEvidenceCardList, WorkcenterScorecard, ScheduleAttainment, MyAssignmentsPanel are visible) AND `router.push` is called with URL that does NOT contain `mode=meeting`
- Data: Mock useDailyActions with standard data, mockSearchParamsGet returning 'meeting' for 'mode'

### 18-1-meeting-mode-toggle-talking-points-view-INT-005: Toggle back preserves date and shift params in URL
- Priority: P1
- Type: integration
- Given: MorningReportClient is in meeting mode with URL `?date=2026-02-05&shift=day&mode=meeting`
- When: The user clicks the toggle to switch back to normal mode
- Then: `router.push` is called with URL containing `date=2026-02-05` AND `shift=day` but NOT containing `mode=meeting`
- Data: mockSearchParamsGet returning '2026-02-05' for 'date', 'day' for 'shift', 'meeting' for 'mode'

### 18-1-meeting-mode-toggle-talking-points-view-UNIT-017: MeetingModeToggle emits onToggle(false) when clicked from pressed state
- Priority: P0
- Type: unit
- Given: MeetingModeToggle is rendered with `pressed={true}` and an `onToggle` spy
- When: The user clicks the toggle button
- Then: The `onToggle` callback is called with `false`
- Data: `{ pressed: true, onToggle: vi.fn() }`

### 18-1-meeting-mode-toggle-talking-points-view-INT-006: Normal mode data is not re-fetched on toggle back
- Priority: P1
- Type: integration
- Given: MorningReportClient is rendered, user toggles to meeting mode, then toggles back to normal mode
- When: The second toggle (back to normal) completes
- Then: `useDailyActions` is NOT called with new arguments (same data is reused, no duplicate fetch) AND the existing data from the initial load is used to render normal mode
- Data: Mock useDailyActions returning consistent data across renders

## AC4: Given the URL includes ?mode=meeting, When the page loads, Then meeting mode is activated automatically.

### 18-1-meeting-mode-toggle-talking-points-view-INT-007: Meeting mode activates from URL on initial page load
- Priority: P0
- Type: integration
- Given: The URL search params include `mode=meeting`
- When: MorningReportClient mounts
- Then: The MeetingModeView is rendered immediately (without requiring a toggle click) AND the MeetingModeToggle shows `pressed={true}` (aria-pressed="true") AND normal mode sections (InsightEvidenceCardList, WorkcenterScorecard, etc.) are not rendered
- Data: mockSearchParamsGet returning 'meeting' for 'mode'

### 18-1-meeting-mode-toggle-talking-points-view-INT-008: Meeting mode does not activate for non-matching mode param values
- Priority: P1
- Type: integration
- Given: The URL search params include `mode=presentation` (not "meeting")
- When: MorningReportClient mounts
- Then: Normal mode is rendered (MeetingModeView is NOT shown) AND MeetingModeToggle shows `pressed={false}`
- Data: mockSearchParamsGet returning 'presentation' for 'mode'

### 18-1-meeting-mode-toggle-talking-points-view-INT-009: Meeting mode activates from URL with combined date param
- Priority: P1
- Type: integration
- Given: The URL search params include `date=2026-02-05&mode=meeting`
- When: MorningReportClient mounts
- Then: Meeting mode is activated AND `useDailyActions` is called with `reportDate: '2026-02-05'` (both params honored simultaneously)
- Data: mockSearchParamsGet returning '2026-02-05' for 'date', 'meeting' for 'mode'

### 18-1-meeting-mode-toggle-talking-points-view-INT-010: Normal mode is default when no mode param exists
- Priority: P0
- Type: integration
- Given: The URL has no `mode` search parameter (standard morning report URL)
- When: MorningReportClient mounts
- Then: Normal mode is rendered AND MeetingModeToggle shows `pressed={false}` AND full report sections are visible
- Data: mockSearchParamsGet returning null for 'mode'

edge_cases:
  - Action items with unmapped category values (not 'safety', 'oee', or 'financial') should fall into "Today's Priorities" section as a default bucket
  - Exactly 5 items (boundary): all 5 should render; no truncation should occur at the limit
  - Exactly 6 items (boundary): only top 5 should render; 6th item is excluded
  - Action item with very long headline text should not break card layout (text should truncate or wrap gracefully)
  - Action item with no asset name (null or empty) should render without error and show placeholder or omit asset field
  - MeetingModeView with all items in a single category (e.g., 5 safety items) should render correctly with other sections showing "No items"
  - Rapid toggle clicks (debounce): toggling quickly between modes should not cause race conditions in URL updates
  - Dark mode support: all new components should render correctly with dark mode classes applied
  - Screen reader announces toggle state change via aria-pressed attribute update

error_scenarios:
  - useDailyActions returns error state: MeetingModeToggle should still be rendered but MeetingModeView should show an error state or empty state gracefully
  - useDailyActions returns loading state: meeting mode should show loading skeleton or spinner, not crash
  - Follow-up data fetch fails: MeetingTalkingPoint should render without assignment badge (graceful degradation, no crash)
  - Invalid URL mode param (e.g., mode=<script>): should be treated as non-meeting and not cause XSS or rendering issues
  - Action item with missing required fields (null recommendation or null asset): card should render gracefully without throwing

test_file_mapping:
  - 18-1-meeting-mode-toggle-talking-points-view-UNIT-001 to UNIT-004: apps/web/src/components/report/__tests__/MeetingModeToggle.test.tsx
  - 18-1-meeting-mode-toggle-talking-points-view-UNIT-005 to UNIT-006, UNIT-012 to UNIT-016: apps/web/src/components/action-list/__tests__/MeetingTalkingPoint.test.tsx
  - 18-1-meeting-mode-toggle-talking-points-view-UNIT-007 to UNIT-011: apps/web/src/components/report/__tests__/MeetingModeView.test.tsx
  - 18-1-meeting-mode-toggle-talking-points-view-UNIT-017: apps/web/src/components/report/__tests__/MeetingModeToggle.test.tsx
  - 18-1-meeting-mode-toggle-talking-points-view-INT-001 to INT-010: apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.meeting.test.tsx

TEST SPEC END

---

## DESIGN: 18-2-teams-webhook-configuration
**Timestamp:** 2026-02-12 08:57:26

DESIGN START
story_id: 18-2-teams-webhook-configuration

files_to_modify:
  - path: apps/api/app/core/config.py
    action: modify
    purpose: Add `teams_webhook_url: str = ""` field to Settings class and `teams_configured` property returning `bool(self.teams_webhook_url)`, following the exact pattern of `elevenlabs_configured` and `smtp_configured`.

  - path: apps/api/.env.example
    action: modify
    purpose: Add `TEAMS_WEBHOOK_URL=` entry with comment header for Teams integration, following the existing section pattern (e.g., the SMTP section).

  - path: apps/api/app/services/notifications/__init__.py
    action: create
    purpose: Empty barrel file for the notifications service package. Follows the pattern of `services/email/__init__.py`, `services/voice/__init__.py`, etc. Will export `TeamsWebhookClient` and a `get_teams_client()` singleton accessor.

  - path: apps/api/app/services/notifications/teams.py
    action: create
    purpose: `TeamsWebhookClient` class implementing `send_card(card_payload: dict) -> dict` and `send_test_message() -> dict` using `httpx.AsyncClient`. Follows the pattern established by `ElevenLabsClient` in `services/voice/elevenlabs.py` — uses `httpx`, `get_settings()`, structured logging, and error handling for timeout/HTTP errors/connection errors.

  - path: apps/api/app/api/notifications.py
    action: create
    purpose: FastAPI `APIRouter` with `POST /teams/test` endpoint. Follows the pattern in `api/followups.py` and `api/actions.py` — uses `Depends(get_current_user)` for auth, returns JSON response dict, raises `HTTPException(400)` when webhook not configured.

  - path: apps/api/app/main.py
    action: modify
    purpose: Import `notifications` router module and register it with `app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])`. Follows the exact pattern of the 20+ existing router registrations.

  - path: apps/api/tests/test_teams_config.py
    action: create
    purpose: Unit tests for `Settings.teams_configured` property — follows the exact pattern in `tests/test_config_smtp.py`. Tests: returns False when empty, returns True when set.

  - path: apps/api/tests/test_teams_webhook_client.py
    action: create
    purpose: Unit tests for `TeamsWebhookClient` — tests `send_card()` success (mocked httpx 200), `send_card()` failure cases (timeout, 4xx, 5xx, connection error), `send_test_message()` returns correct Adaptive Card structure, `is_configured` property. Uses `unittest.mock.patch` and `AsyncMock` to mock `httpx.AsyncClient`.

  - path: apps/api/tests/test_notifications_api.py
    action: create
    purpose: Integration tests for `POST /api/v1/notifications/teams/test` endpoint. Uses `conftest.py` fixtures (`client`, `mock_verify_jwt`). Tests: returns 400 when no webhook URL configured, returns 401 when unauthenticated, returns success response when webhook is configured and mocked httpx succeeds.

patterns_to_use:
  - pydantic-settings config pattern: Add `teams_webhook_url: str = ""` field and `@property teams_configured -> bool` to Settings class, matching the `elevenlabs_configured`, `smtp_configured`, `mem0_configured` pattern exactly (config.py lines 158-171).
  - Router registration pattern: Import module in main.py line 7 import block, add `app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])` with story comment, following the pattern at main.py lines 63-109.
  - Authentication dependency pattern: Use `current_user: CurrentUser = Depends(get_current_user)` as seen in `followups.py:48` and `actions.py` endpoints. Import `get_current_user` from `app.core.security` and `CurrentUser` from `app.models.user`.
  - Service package pattern: Create `services/notifications/` as a package with `__init__.py` barrel file, following `services/email/`, `services/voice/`, `services/agent/` package structure.
  - httpx async client pattern: Use `async with httpx.AsyncClient(timeout=self.timeout) as client:` with structured error handling (`HTTPStatusError`, `TimeoutException`, `ConnectError`), following the pattern in `services/voice/elevenlabs.py`.
  - Config test pattern: Direct `Settings()` instantiation with explicit field values in test methods, following `tests/test_config_smtp.py` test class structure.
  - API test pattern: Use `conftest.py` `client` fixture + `mock_verify_jwt` for authenticated endpoint tests, `patch` for service-layer mocks.

dependencies:
  - httpx: installed (requirements.txt line 6: `httpx>=0.26.0`)
  - pydantic-settings: installed (already used by config.py)
  - fastapi: installed (already used throughout)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (Admin can configure Teams Webhook URL and save):
    - `apps/api/app/core/config.py`: Add `teams_webhook_url: str = ""` field (read from `TEAMS_WEBHOOK_URL` env var via pydantic-settings) and `teams_configured` property.
    - `apps/api/.env.example`: Add `TEAMS_WEBHOOK_URL=` entry with documentation comment.
    - Note: "Save" means setting the env var on Railway — no database/UI settings needed per story scope.
  - AC2 (Admin clicks Test, message posted to Teams, success/failure displayed):
    - `apps/api/app/services/notifications/teams.py`: `TeamsWebhookClient.send_test_message()` posts an Adaptive Card to the webhook URL; `send_card()` returns `{"success": bool, "message": str, "status_code": int | None}`.
    - `apps/api/app/api/notifications.py`: `POST /api/v1/notifications/teams/test` endpoint calls `TeamsWebhookClient().send_test_message()` and returns the result dict. Returns 400 if not configured.
    - `apps/api/app/main.py`: Router registered at `/api/v1/notifications`.
  - AC3 (No webhook configured → no Teams notification sent, morning report continues):
    - `apps/api/app/core/config.py`: `teams_configured` returns `False` when `teams_webhook_url` is empty.
    - `apps/api/app/services/notifications/teams.py`: `TeamsWebhookClient.is_configured` returns `False` when URL is empty; `send_card()` returns early with `{"success": False, "message": "Teams webhook URL not configured", "status_code": None}` — no HTTP request is attempted.
    - Morning pipeline callers (Stories 18.3+) will check `is_configured` before sending — this story establishes the pattern.

risks:
  - Teams webhook URL in environment variable could be accidentally exposed in logs. Mitigation: Never log the webhook URL itself — only log success/failure outcomes and HTTP status codes. The story's TeamsWebhookClient already follows this pattern in the dev notes.
  - Teams webhook endpoint format may change or vary between Teams versions (classic webhooks vs Workflows connectors). Mitigation: Use the standard Adaptive Card v1.4 format which is the current recommended approach. The `send_card()` method wraps any card payload in the required `message.attachments` envelope, making it adaptable.
  - httpx.AsyncClient instantiation per-request (in `async with` block) has slight overhead. Mitigation: For the test endpoint this is fine — the user needs the result synchronously. For Stories 18.3-18.5 with fire-and-forget, callers will use `asyncio.create_task()`. A shared client could be added later if needed but is premature optimization now.
  - Test endpoint accessible to any authenticated user, not just admins. Mitigation: The story specifies "admin navigates to settings" but auth uses `get_current_user` (any authenticated user). This matches the existing pattern — role-based restrictions can be added in a future story if needed. The webhook URL is server-side only (env var), so a test POST is low risk.
  - Singleton pattern for TeamsWebhookClient: Unlike the email service which uses module-level singleton, the story dev notes show instantiation per-call (`TeamsWebhookClient()`). Mitigation: Keep per-call instantiation for simplicity since the client is stateless (just reads settings and makes one HTTP call). Add a `get_teams_client()` factory in `__init__.py` for consistency with `get_email_service()` pattern, but TeamsWebhookClient can also be instantiated directly.

estimated_test_files:
  - apps/api/tests/test_teams_config.py: Tests Settings.teams_configured returns False when teams_webhook_url is empty and True when set. Follows test_config_smtp.py pattern.
  - apps/api/tests/test_teams_webhook_client.py: Tests TeamsWebhookClient.send_card() with mocked httpx (success 200, timeout, 4xx, 5xx, connection error). Tests send_test_message() returns correct Adaptive Card structure. Tests is_configured property. Tests send_card() returns early when not configured.
  - apps/api/tests/test_notifications_api.py: Tests POST /api/v1/notifications/teams/test returns 400 when no webhook URL configured. Tests endpoint returns 401 when unauthenticated. Tests endpoint returns success when webhook is configured and mocked TeamsWebhookClient succeeds.

implementation_order:
  1. Add `teams_webhook_url` field and `teams_configured` property to Settings in `apps/api/app/core/config.py` (2 lines + property — smallest change, foundational for everything else).
  2. Add `TEAMS_WEBHOOK_URL=` entry to `apps/api/.env.example` with Teams integration section comment.
  3. Create `apps/api/app/services/notifications/__init__.py` with TeamsWebhookClient export and `get_teams_client()` factory function.
  4. Create `apps/api/app/services/notifications/teams.py` with `TeamsWebhookClient` class implementing `is_configured`, `send_card()`, and `send_test_message()`.
  5. Create `apps/api/app/api/notifications.py` with `POST /teams/test` endpoint using `get_current_user` dependency.
  6. Register notifications router in `apps/api/app/main.py` — add import and `include_router` call.
  7. Create `apps/api/tests/test_teams_config.py` — unit tests for `teams_configured` property.
  8. Create `apps/api/tests/test_teams_webhook_client.py` — unit tests for TeamsWebhookClient with mocked httpx.
  9. Create `apps/api/tests/test_notifications_api.py` — integration tests for the test endpoint.
  10. Run full test suite to verify no regressions.
DESIGN END

---

## DESIGN: 18-3-morning-summary-teams-card
**Timestamp:** 2026-02-12 09:24:34

DESIGN START
story_id: 18-3-morning-summary-teams-card

files_to_modify:
  - path: apps/api/app/services/notifications/teams.py
    action: modify
    purpose: Add `build_morning_summary_card()` and `build_all_clear_card()` static/class methods to `TeamsWebhookClient`. These methods produce Adaptive Card v1.4 JSON payloads for the morning summary (with title, category counts, top 3 bullet points, Open Report button) and the all-clear variant. The existing `send_card()` method already handles the outer `message.attachments` envelope, so these builders return only the inner `content` dict.

  - path: apps/api/app/services/notifications/__init__.py
    action: modify
    purpose: No structural changes needed — `get_teams_client()` and `TeamsWebhookClient` are already exported from 18-2. This file is unchanged.

  - path: apps/api/app/services/pipelines/morning_report.py
    action: modify
    purpose: Add `_trigger_teams_notification(target_date: date) -> None` async function following the exact pattern of `_trigger_smart_summary_generation()` (lines 469-513). Call it from `run_morning_report()` after the smart summary block (after line 464, before the `return result` at line 466). The function checks `settings.teams_configured`, queries action items via `get_action_engine().generate_action_list()`, builds the appropriate card (summary or all-clear), sends via `get_teams_client().send_card()`, and wraps everything in try/except that logs and returns (never raises).

  - path: apps/api/tests/services/__init__.py
    action: create
    purpose: Empty package init to support `tests/services/notifications/` test directory structure (if not already present).

  - path: apps/api/tests/services/notifications/__init__.py
    action: create
    purpose: Empty package init for notifications test subpackage.

  - path: apps/api/tests/services/notifications/test_morning_summary_card.py
    action: create
    purpose: Unit tests for `build_morning_summary_card()` and `build_all_clear_card()` — validates Adaptive Card JSON structure, correct title format, category count summary line, top 3 bullet points with asset name and headline, Open Report button URL, and the all-clear variant for zero items.

  - path: apps/api/tests/services/notifications/test_trigger_teams_notification.py
    action: create
    purpose: Integration tests for `_trigger_teams_notification()` — tests: skips silently when webhook not configured, builds summary card when action items exist, builds all-clear card when zero items, pipeline result is unaffected when Teams notification fails (mock httpx raising), send_card is called with correct payload.

patterns_to_use:
  - fire-and-forget async helper pattern: Follow `_trigger_smart_summary_generation()` (morning_report.py:469-513) exactly — lazy import at the top of the function body, full try/except wrapping with `logger.error()` that mentions "Pipeline result is not affected", return None on all paths.
  - settings guard pattern: Check `settings.teams_configured` (config.py:177-179) early in the function and `return` silently with an `logger.info()` if not configured. This matches the pattern used by email and voice services.
  - action engine data access: Use `get_action_engine().generate_action_list(target_date=target_date)` which returns `ActionListResponse` with `actions`, `total_count`, and `counts_by_category` dict (keys: "safety", "oee", "financial").
  - TeamsWebhookClient.send_card() usage: Pass the inner Adaptive Card dict (not the outer message envelope — `send_card()` already wraps it in `{"type": "message", "attachments": [...]}` at teams.py:40-47). Check `result["success"]` for logging.
  - Adaptive Card v1.4 structure: Card body uses `TextBlock` elements with `weight: "Bolder"`, `size: "Medium"` for title, `wrap: true` for content, and `Action.OpenUrl` for the button. Schema, type, version fields required.
  - app_base_url for link construction: Use `settings.app_base_url` (config.py:106, already exists from Story 15.2) to build the Open Report URL: `f"{settings.app_base_url}/morning-report?date={target_date.isoformat()}"`.
  - test mocking pattern: Use `unittest.mock.patch` with `AsyncMock` for `httpx.AsyncClient` and `get_action_engine`, following the patterns in `tests/test_teams_webhook_client.py` (530 lines of well-established mock patterns).

dependencies:
  - httpx: installed (requirements.txt: `httpx>=0.26.0`)
  - pydantic-settings: installed (used by config.py)
  - No new dependencies needed — all infrastructure exists from Story 18.2

acceptance_criteria_mapping:
  - AC1 (Morning summary card posted at 6:15 AM with title, counts, top 3 items, Open Report button):
    - `teams.py`: `build_morning_summary_card(action_list: ActionListResponse, report_date: date, base_url: str)` — constructs Adaptive Card with title "Morning Report -- {date}", summary line "{N} action items: {safety_count} safety, {oee_count} OEE misses, {financial_count} financial", top 3 items as "- {asset_name}: {recommendation_text}" bullet text block, and Action.OpenUrl button to `/morning-report?date={date}`.
    - `morning_report.py`: `_trigger_teams_notification(target_date)` — called from `run_morning_report()` after smart summary generation. Queries action items, calls `build_morning_summary_card()` when `total_count > 0`, sends via `get_teams_client().send_card()`.
  - AC2 (All-clear card when zero action items):
    - `teams.py`: `build_all_clear_card(report_date: date, base_url: str)` — constructs Adaptive Card with title "Morning Report -- {date}: All clear. No action items today." and still includes the Open Report Action.OpenUrl button.
    - `morning_report.py`: `_trigger_teams_notification()` — checks `action_list.total_count == 0` and calls `build_all_clear_card()` instead of `build_morning_summary_card()`.
  - AC3 (Webhook failure logged, morning report unaffected):
    - `morning_report.py`: `_trigger_teams_notification()` — entire function body wrapped in `try/except Exception` that calls `logger.error()` and returns (never re-raises). The `return result` line in `run_morning_report()` is always reached.
    - `teams.py`: `send_card()` (existing from 18-2) — already handles httpx.TimeoutException, HTTPStatusError, ConnectError, and generic Exception, returning `{"success": False, ...}` without raising.
    - Double protection: even if `send_card()` somehow raised, the outer try/except in `_trigger_teams_notification()` catches it.

risks:
  - Action engine `generate_action_list()` may be slow or fail if cache is cold. Mitigation: The fire-and-forget try/except wrapper ensures pipeline is unaffected. The action engine has its own cache (generate_action_list uses `use_cache=True` by default), so after the pipeline run, the cache should be warm from any prior API requests or the pipeline itself.
  - `app_base_url` defaulting to `http://localhost:3000` would produce a non-functional link in production. Mitigation: This is already an existing config field (Story 15.2, line 106) that should be set to the production URL in Railway env. The story does not need to modify this — just use it. Log a warning if it still contains "localhost" when sending a card.
  - `generate_action_list()` might return stale cached data from before the pipeline ran. Mitigation: Call it with `use_cache=True` (default) — the action engine cache is keyed by date and is regenerated during the pipeline. If concerned, could pass `use_cache=False`, but that adds latency. Default is fine since the pipeline populates fresh data.
  - Card builders as static methods vs standalone functions: Static methods on `TeamsWebhookClient` couples card building to the client. Mitigation: Make them standalone module-level functions in `teams.py` (e.g., `build_morning_summary_card()`) so they can be tested independently without instantiating the client. Export them from `__init__.py` for future reuse by Stories 18.4/18.5.
  - Top 3 bullet text may be very long if recommendation_text is verbose. Mitigation: Truncate each bullet to ~100 characters with "..." suffix in the card builder.

estimated_test_files:
  - apps/api/tests/services/notifications/test_morning_summary_card.py: Tests build_morning_summary_card() produces valid Adaptive Card JSON with: correct $schema/type/version, title "Morning Report -- 2026-02-10", summary line with correct category counts, top 3 items as bullet points with asset_name and headline, Action.OpenUrl with correct URL. Tests build_all_clear_card() produces card with "All clear" message and Open Report button. Tests edge cases: exactly 3 items (no truncation), more than 3 items (only top 3 shown), 1 item, items with long text (truncation).
  - apps/api/tests/services/notifications/test_trigger_teams_notification.py: Tests _trigger_teams_notification() skips when settings.teams_configured is False (no send_card call). Tests it calls build_morning_summary_card when total_count > 0. Tests it calls build_all_clear_card when total_count == 0. Tests pipeline is not blocked when send_card raises an exception. Tests pipeline is not blocked when generate_action_list raises an exception. Tests correct arguments passed to send_card.
  - apps/api/tests/test_morning_report_teams_integration.py: Integration test verifying run_morning_report() completes successfully and returns PipelineResult even when Teams notification fails (mock send_card to raise). Verifies run_morning_report() calls _trigger_teams_notification after smart summary generation.

implementation_order:
  1. Add card builder functions to `apps/api/app/services/notifications/teams.py`: implement `build_morning_summary_card(action_list: ActionListResponse, report_date: date, base_url: str) -> dict` and `build_all_clear_card(report_date: date, base_url: str) -> dict` as standalone module-level functions. These are pure functions with no side effects — easiest to implement and test first.
  2. Update `apps/api/app/services/notifications/__init__.py`: export `build_morning_summary_card` and `build_all_clear_card` from the package.
  3. Add `_trigger_teams_notification(target_date: date) -> None` async function to `apps/api/app/services/pipelines/morning_report.py`: implement the fire-and-forget wrapper that checks config, queries action items, builds the appropriate card, and sends it. Model after `_trigger_smart_summary_generation()`.
  4. Modify `run_morning_report()` in `morning_report.py`: insert `await _trigger_teams_notification(target_date or (date.today() - timedelta(days=1)))` after the smart summary block (after line 464) and before `return result` (line 466). Place it outside the `if generate_smart_summary` guard so it always fires on SUCCESS/PARTIAL (the function itself guards on `teams_configured`).
  5. Create test directory structure: `apps/api/tests/services/__init__.py` and `apps/api/tests/services/notifications/__init__.py` (empty package inits).
  6. Write unit tests in `apps/api/tests/services/notifications/test_morning_summary_card.py`: test card builder functions produce correct Adaptive Card JSON for all scenarios (normal summary, all-clear, edge cases).
  7. Write integration tests in `apps/api/tests/services/notifications/test_trigger_teams_notification.py`: test the `_trigger_teams_notification()` function with mocked dependencies (action engine, teams client, settings).
  8. Run full test suite to verify no regressions.
DESIGN END

---

## TEST_SPEC: 18-3-morning-summary-teams-card
**Timestamp:** 2026-02-12 09:27:27

TEST SPEC START
story_id: 18-3-morning-summary-teams-card
generated: 2026-02-12

test_specifications:

## AC1: Given the morning data pipeline has completed and action items are generated, When 6:15 AM arrives (or the morning cron triggers), Then a Teams Adaptive Card is posted to the configured webhook with: Title "Morning Report -- {date}", Summary "{N} action items: {safety_count} safety, {oee_count} OEE misses, {financial_count} financial", Top 3 action items as bullet points with asset name and headline, "Open Report" button linking to /morning-report?date={date}

### 18-3-morning-summary-teams-card-UNIT-001: build_morning_summary_card produces valid Adaptive Card JSON structure
- Priority: P0
- Type: unit
- Given: An ActionListResponse with 5 action items (1 safety, 2 OEE, 2 financial) and report_date=2026-02-10
- When: build_morning_summary_card(action_list, report_date, base_url) is called
- Then: The returned dict contains "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.4", a "body" array with 3 TextBlock elements, and an "actions" array with 1 Action.OpenUrl element
- Data: ActionListResponse with total_count=5, counts_by_category={"safety": 1, "oee": 2, "financial": 2}, 5 ActionItem objects with distinct asset_name and recommendation_text values

### 18-3-morning-summary-teams-card-UNIT-002: Card title uses correct format "Morning Report -- {date}"
- Priority: P0
- Type: unit
- Given: A report_date of 2026-02-10
- When: build_morning_summary_card() is called
- Then: The first TextBlock in body has text "Morning Report -- 2026-02-10", weight "Bolder", size "Medium"
- Data: Any valid ActionListResponse with total_count > 0

### 18-3-morning-summary-teams-card-UNIT-003: Summary line shows correct category counts
- Priority: P0
- Type: unit
- Given: An ActionListResponse with total_count=5, counts_by_category={"safety": 1, "oee": 2, "financial": 2}
- When: build_morning_summary_card() is called
- Then: The second TextBlock has text "5 action items: 1 safety, 2 OEE misses, 2 financial" and wrap=true
- Data: ActionListResponse with specific category counts

### 18-3-morning-summary-teams-card-UNIT-004: Top 3 action items rendered as bullet points with asset name and headline
- Priority: P0
- Type: unit
- Given: An ActionListResponse with 5 actions where the first 3 are: (Grinder 5, "Safety event detected"), (CAMA 2400, "OEE at 72%"), (Rychiger 101, "$1,200 financial loss")
- When: build_morning_summary_card() is called
- Then: The third TextBlock contains "- Grinder 5: Safety event detected\n- CAMA 2400: OEE at 72%\n- Rychiger 101: $1,200 financial loss" and wrap=true
- Data: 5 ActionItem objects; only the first 3 should appear in the bullet list

### 18-3-morning-summary-teams-card-UNIT-005: Open Report button uses correct URL with date parameter
- Priority: P0
- Type: unit
- Given: base_url="https://app.example.com" and report_date=2026-02-10
- When: build_morning_summary_card() is called
- Then: The actions array contains one Action.OpenUrl with title "Open Report" and url "https://app.example.com/morning-report?date=2026-02-10"
- Data: Valid ActionListResponse, base_url, report_date

### 18-3-morning-summary-teams-card-UNIT-006: Card with exactly 3 action items shows all 3 in bullets (no truncation)
- Priority: P1
- Type: unit
- Given: An ActionListResponse with exactly 3 action items
- When: build_morning_summary_card() is called
- Then: The bullet point TextBlock contains exactly 3 lines (one per action), each with "- {asset_name}: {recommendation_text}"
- Data: ActionListResponse with total_count=3, 3 ActionItem objects

### 18-3-morning-summary-teams-card-UNIT-007: Card with fewer than 3 action items shows only available items
- Priority: P1
- Type: unit
- Given: An ActionListResponse with 1 action item (1 safety, 0 OEE, 0 financial)
- When: build_morning_summary_card() is called
- Then: The summary line reads "1 action items: 1 safety, 0 OEE misses, 0 financial" and the bullet TextBlock contains exactly 1 bullet line
- Data: ActionListResponse with total_count=1, 1 ActionItem

### 18-3-morning-summary-teams-card-UNIT-008: Long recommendation text is truncated in bullet points
- Priority: P1
- Type: unit
- Given: An ActionListResponse where the first action has recommendation_text longer than 100 characters
- When: build_morning_summary_card() is called
- Then: The bullet text for that item is truncated to ~100 characters with "..." suffix
- Data: ActionItem with recommendation_text of 150+ characters

### 18-3-morning-summary-teams-card-UNIT-009: Summary line handles zero counts for some categories
- Priority: P1
- Type: unit
- Given: An ActionListResponse with counts_by_category={"safety": 0, "oee": 3, "financial": 0}
- When: build_morning_summary_card() is called
- Then: Summary line reads "3 action items: 0 safety, 3 OEE misses, 0 financial"
- Data: ActionListResponse with total_count=3, all OEE category

### 18-3-morning-summary-teams-card-INT-001: _trigger_teams_notification sends summary card after pipeline success
- Priority: P0
- Type: integration
- Given: settings.teams_configured returns True, the action engine returns an ActionListResponse with 5 action items, and the TeamsWebhookClient is mocked
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: get_teams_client().send_card() is called once with a dict containing the Adaptive Card payload built by build_morning_summary_card()
- Data: Mocked ActionListResponse with 5 items, mocked settings with teams_configured=True

### 18-3-morning-summary-teams-card-INT-002: run_morning_report calls _trigger_teams_notification after smart summary
- Priority: P0
- Type: integration
- Given: Pipeline returns SUCCESS, smart summary generation succeeds, teams_configured=True, action engine returns items
- When: run_morning_report(target_date=date(2026, 2, 10), generate_smart_summary=True) is called
- Then: _trigger_teams_notification is called after _trigger_smart_summary_generation, and the PipelineResult is returned correctly
- Data: Mocked pipeline, mocked smart summary service, mocked action engine, mocked teams client

### 18-3-morning-summary-teams-card-INT-003: _trigger_teams_notification queries action engine with correct date
- Priority: P1
- Type: integration
- Given: settings.teams_configured returns True
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: get_action_engine().generate_action_list() is called with report_date=date(2026, 2, 10)
- Data: Mocked action engine returning valid ActionListResponse

### 18-3-morning-summary-teams-card-INT-004: _trigger_teams_notification uses app_base_url from settings for Open Report link
- Priority: P1
- Type: integration
- Given: settings.app_base_url="https://prod.example.com", settings.teams_configured=True, action engine returns items
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The card payload passed to send_card() contains Action.OpenUrl with url "https://prod.example.com/morning-report?date=2026-02-10"
- Data: Mocked settings, mocked action engine, mocked teams client


## AC2: Given there are no action items for the day, When the cron triggers, Then a card is posted "Morning Report -- {date}: All clear. No action items today." And the "Open Report" link is still included.

### 18-3-morning-summary-teams-card-UNIT-010: build_all_clear_card produces correct all-clear message
- Priority: P0
- Type: unit
- Given: report_date=2026-02-10 and base_url="https://app.example.com"
- When: build_all_clear_card(report_date, base_url) is called
- Then: The returned dict is a valid Adaptive Card with body containing a TextBlock with text "Morning Report -- 2026-02-10: All clear. No action items today." with weight "Bolder" and size "Medium"
- Data: report_date=date(2026, 2, 10), base_url string

### 18-3-morning-summary-teams-card-UNIT-011: All-clear card includes Open Report button
- Priority: P0
- Type: unit
- Given: report_date=2026-02-10 and base_url="https://app.example.com"
- When: build_all_clear_card(report_date, base_url) is called
- Then: The actions array contains one Action.OpenUrl with title "Open Report" and url "https://app.example.com/morning-report?date=2026-02-10"
- Data: report_date and base_url

### 18-3-morning-summary-teams-card-UNIT-012: All-clear card has valid Adaptive Card structure
- Priority: P1
- Type: unit
- Given: report_date=2026-02-10 and base_url="https://app.example.com"
- When: build_all_clear_card(report_date, base_url) is called
- Then: The returned dict contains "$schema", "type": "AdaptiveCard", "version": "1.4", a "body" array, and an "actions" array
- Data: Valid date and base_url

### 18-3-morning-summary-teams-card-INT-005: _trigger_teams_notification sends all-clear card when zero action items
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, action engine returns ActionListResponse with total_count=0 and empty actions list
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: get_teams_client().send_card() is called with the all-clear card payload (not the summary card), containing "All clear. No action items today."
- Data: Mocked ActionListResponse with total_count=0, counts_by_category={"safety": 0, "oee": 0, "financial": 0}

### 18-3-morning-summary-teams-card-INT-006: run_morning_report posts all-clear card when pipeline succeeds with no action items
- Priority: P1
- Type: integration
- Given: Pipeline returns SUCCESS, action engine returns zero action items, teams_configured=True
- When: run_morning_report(target_date=date(2026, 2, 10)) is called
- Then: send_card() is called with the all-clear card payload, and PipelineResult with SUCCESS status is returned
- Data: Mocked pipeline, mocked action engine with empty results


## AC3: Given the Teams webhook fails (network error, invalid URL), When the notification is attempted, Then the failure is logged with error details And the morning report data is unaffected (fire-and-forget).

### 18-3-morning-summary-teams-card-UNIT-013: send_card handles httpx.TimeoutException gracefully
- Priority: P0
- Type: unit
- Given: A valid card payload and httpx.AsyncClient.post raises httpx.TimeoutException
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, ...} without raising an exception, and the error is logged
- Data: Any valid Adaptive Card dict, mocked httpx raising TimeoutException

### 18-3-morning-summary-teams-card-UNIT-014: send_card handles httpx.ConnectError gracefully
- Priority: P0
- Type: unit
- Given: A valid card payload and httpx.AsyncClient.post raises httpx.ConnectError (e.g., invalid URL, DNS failure)
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, ...} without raising, and the error is logged
- Data: Any valid Adaptive Card dict, mocked httpx raising ConnectError

### 18-3-morning-summary-teams-card-UNIT-015: send_card handles HTTP 4xx/5xx responses gracefully
- Priority: P0
- Type: unit
- Given: A valid card payload and the webhook returns HTTP 400 (Bad Request) or HTTP 500 (Server Error)
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, "status_code": 400 or 500, ...} without raising
- Data: Mocked httpx response with status_code=400 or 500

### 18-3-morning-summary-teams-card-UNIT-016: send_card returns early when webhook not configured
- Priority: P1
- Type: unit
- Given: TeamsWebhookClient instantiated with empty webhook_url=""
- When: send_card(card_payload) is called
- Then: The method returns {"success": False, "message": contains "not configured"} without attempting an HTTP request
- Data: Empty webhook URL, any card payload

### 18-3-morning-summary-teams-card-INT-007: _trigger_teams_notification skips silently when teams_configured is False
- Priority: P0
- Type: integration
- Given: settings.teams_configured returns False (teams_webhook_url is empty)
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: No call is made to get_action_engine() or send_card(), the function returns None without error
- Data: Mocked settings with teams_webhook_url=""

### 18-3-morning-summary-teams-card-INT-008: _trigger_teams_notification catches and logs send_card failure
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, action engine returns valid items, but send_card() returns {"success": False, "message": "Connection refused"}
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The failure is logged at ERROR level with error details, and the function returns None (does not raise)
- Data: Mocked action engine, mocked teams client returning failure result

### 18-3-morning-summary-teams-card-INT-009: _trigger_teams_notification catches exception from send_card if it raises
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, action engine returns valid items, but get_teams_client().send_card() raises an unexpected Exception
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The exception is caught, logged at ERROR level with "Pipeline result is not affected" message, and the function returns None
- Data: Mocked send_card raising RuntimeError("unexpected failure")

### 18-3-morning-summary-teams-card-INT-010: _trigger_teams_notification catches exception from generate_action_list
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, but get_action_engine().generate_action_list() raises an Exception
- When: _trigger_teams_notification(target_date=date(2026, 2, 10)) is called
- Then: The exception is caught, logged at ERROR level, and the function returns None without calling send_card()
- Data: Mocked action engine raising Exception("database error")

### 18-3-morning-summary-teams-card-INT-011: run_morning_report returns PipelineResult even when Teams notification fails
- Priority: P0
- Type: integration
- Given: Pipeline returns SUCCESS with valid PipelineResult, but _trigger_teams_notification raises an unhandled Exception (simulating catastrophic failure)
- When: run_morning_report(target_date=date(2026, 2, 10)) is called
- Then: The PipelineResult with SUCCESS status is returned to the caller, and no exception propagates
- Data: Mocked pipeline returning SUCCESS, mocked _trigger_teams_notification raising Exception

### 18-3-morning-summary-teams-card-INT-012: run_morning_report returns PipelineResult when PARTIAL status and notification fails
- Priority: P1
- Type: integration
- Given: Pipeline returns PARTIAL status, smart summary succeeds, but Teams notification fails
- When: run_morning_report(target_date=date(2026, 2, 10)) is called
- Then: PipelineResult with PARTIAL status is returned correctly
- Data: Mocked pipeline returning PARTIAL, mocked failing Teams notification


edge_cases:
  - Action items list has exactly 0 items (triggers all-clear card path)
  - Action items list has exactly 1 item (single bullet point, no truncation)
  - Action items list has exactly 3 items (all shown, no "more" indicator)
  - Action items list has more than 3 items (only top 3 shown in bullet points)
  - Action item recommendation_text exceeds 100 characters (truncation with "...")
  - counts_by_category has zero for all categories except one
  - counts_by_category keys may be missing (defensive access with .get())
  - target_date is None in run_morning_report (defaults to yesterday)
  - app_base_url contains trailing slash (URL construction should handle)
  - teams_webhook_url contains whitespace only (teams_configured should return False)
  - Date formatting uses ISO format (YYYY-MM-DD) in title and URL

error_scenarios:
  - httpx.TimeoutException during webhook POST
  - httpx.ConnectError (DNS failure, connection refused)
  - HTTP 400 Bad Request from webhook endpoint
  - HTTP 401 Unauthorized (expired or invalid webhook URL)
  - HTTP 500 Internal Server Error from Teams service
  - generate_action_list raises database connection error
  - generate_action_list raises unexpected exception
  - send_card raises unexpected RuntimeError
  - Webhook URL is malformed (not a valid URL)
  - Network completely unreachable

test_file_mapping:
  - 18-3-morning-summary-teams-card-UNIT-001 through UNIT-012: apps/api/tests/services/notifications/test_morning_summary_card.py
  - 18-3-morning-summary-teams-card-UNIT-013 through UNIT-016: apps/api/tests/services/notifications/test_morning_summary_card.py
  - 18-3-morning-summary-teams-card-INT-001 through INT-006: apps/api/tests/services/notifications/test_trigger_teams_notification.py
  - 18-3-morning-summary-teams-card-INT-007 through INT-012: apps/api/tests/services/notifications/test_trigger_teams_notification.py

TEST SPEC END

---

## DESIGN: 18-4-followup-assignment-teams-notification
**Timestamp:** 2026-02-12 09:54:38

DESIGN START
story_id: 18-4-followup-assignment-teams-notification

files_to_modify:
  - path: apps/api/app/services/notifications/teams.py
    action: modify
    purpose: Add `build_followup_assignment_card(followup_data: dict, base_url: str) -> dict` standalone function that produces an Adaptive Card v1.4 with header "Follow-Up Assigned", a FactSet with action summary, asset name, category, assigner name, and optional note, plus a "View in App" Action.OpenUrl button linking to `/morning-report?date={report_date}`. Follows the exact pattern of `build_morning_summary_card()` and `build_all_clear_card()` — a pure function that returns the inner card dict (not the message envelope).

  - path: apps/api/app/services/notifications/__init__.py
    action: modify
    purpose: Add `build_followup_assignment_card` to the imports and `__all__` exports, following the existing pattern for `build_morning_summary_card` and `build_all_clear_card`.

  - path: apps/api/app/api/followups.py
    action: modify
    purpose: In the `create_followup()` endpoint (line ~108-114), add a second `asyncio.create_task()` block that dispatches the Teams notification via `get_teams_client().send_card(build_followup_assignment_card(...))`. This sits alongside the existing email notification fire-and-forget block. Resolve the assigner display name from `current_user.email` (email local part before `@`). Resolve the assignee display name using the service-role Supabase client's `auth.admin.get_user_by_id()` to fetch the assigned_to user's email, then use the local part. Build the card data dict and dispatch asynchronously. Wrap in try/except so Teams failure never blocks the response (AC#4).

  - path: apps/api/tests/services/notifications/test_followup_assignment_card.py
    action: create
    purpose: Unit tests for `build_followup_assignment_card()` — validates Adaptive Card JSON structure, correct header text, FactSet with all required fields (action summary, asset name, category, assigner name, note), note fact omitted when note is None/empty, "View in App" button with correct URL. Follows the exact pattern of `test_morning_summary_card.py`.

  - path: apps/api/tests/test_followup_teams_notification.py
    action: create
    purpose: Integration tests for the Teams notification dispatch in `create_followup()` endpoint — tests: Teams notification dispatched as asyncio.create_task (fire-and-forget), Teams notification skipped when `teams_configured` is False with debug log, webhook POST failure does not roll back follow-up creation, API response returns immediately without waiting for webhook. Uses `conftest.py` fixtures (`client`, `mock_verify_jwt`) and mocks for Supabase and TeamsWebhookClient.

patterns_to_use:
  - Card builder function pattern: Follow the exact pattern of `build_morning_summary_card()` and `build_all_clear_card()` in `teams.py` — standalone module-level function, returns an Adaptive Card v1.4 dict (inner content only, not the message envelope), uses `base_url.rstrip("/")` for URL construction, imported and exported via `__init__.py`.
  - Fire-and-forget asyncio.create_task pattern: Follow the exact pattern at `followups.py:108-114` where email notification is dispatched — wrap `asyncio.create_task()` in a try/except that logs errors but never raises. The Teams dispatch will be a parallel block immediately after the email dispatch block.
  - Assigner display name resolution: Use `current_user.email` (already available from `get_current_user` dependency) and extract the local part before `@`. Pattern: `(current_user.email or "").split("@")[0] or "Unknown"`. This matches the existing `assigner_name` derivation at `followups.py:101`.
  - Assignee display name resolution: Use service-role Supabase client `auth.admin.get_user_by_id(assigned_to_uuid)` to fetch the assignee's email, then extract local part. Pattern from `team.py:99-107` and `followups.py:182-190`.
  - Settings guard pattern: Check `settings.teams_configured` before any Teams operations. If False, emit `logger.debug()` and skip. This matches the pattern in `morning_report.py:538-540`.
  - TeamsWebhookClient.send_card() usage: Call `get_teams_client().send_card(card)` which handles the message envelope wrapping and all error handling internally, returning `{"success": bool, ...}`.
  - Test mocking pattern: Use `unittest.mock.patch` + `AsyncMock` for async operations, `MagicMock` for sync operations. Mock `create_client` for Supabase interactions, `get_teams_client` for notification dispatch. Follow patterns in `test_teams_webhook_client.py` and `test_followup_update.py`.

dependencies:
  - httpx: installed (requirements.txt: `httpx>=0.26.0`)
  - asyncio: stdlib (already imported in followups.py)
  - All infrastructure exists from Stories 18.2/18.3 and 15.2 — no new dependencies needed

acceptance_criteria_mapping:
  - AC1 (Teams notification on follow-up assignment with Adaptive Card containing action summary, asset name, category, priority, assigner name, optional note, "View in App" button):
    - `apps/api/app/services/notifications/teams.py`: `build_followup_assignment_card(followup_data, base_url)` builds the Adaptive Card with header "Follow-Up Assigned", a FactSet with all required fields (action summary, asset name, category, assigner name, note — note fact omitted when None/empty), and Action.OpenUrl "View in App" button to `{base_url}/morning-report?date={report_date}`.
    - `apps/api/app/api/followups.py`: In `create_followup()`, after persisting the follow-up, build `followup_data` dict with all fields, call `get_teams_client().send_card(build_followup_assignment_card(followup_data, settings.app_base_url))` via `asyncio.create_task()`.
    - `apps/api/app/services/notifications/__init__.py`: Export `build_followup_assignment_card` for use by the endpoint.
  - AC2 (Graceful degradation when Teams not configured — assignment succeeds, debug log, no error):
    - `apps/api/app/api/followups.py`: Before dispatching the Teams task, check `settings.teams_configured`. If False, emit `logger.debug("Teams notification skipped: webhook not configured")` and skip the `asyncio.create_task()` call. The follow-up insert + return is unaffected since it happens before this block.
  - AC3 (Graceful failure on webhook error — logged, no rollback, API unaffected):
    - `apps/api/app/services/notifications/teams.py`: `TeamsWebhookClient.send_card()` already handles all httpx errors (TimeoutException, HTTPStatusError, ConnectError, generic Exception) and returns `{"success": False, ...}` without raising.
    - `apps/api/app/api/followups.py`: The `asyncio.create_task()` dispatches an async helper function that calls `send_card()` and logs the result. The helper wraps in try/except to catch any unexpected exceptions. Since the follow-up is already persisted before the task is created, no rollback occurs.
  - AC4 (Fire-and-forget delivery — API returns immediately, webhook POST is async):
    - `apps/api/app/api/followups.py`: Uses `asyncio.create_task()` to dispatch the Teams notification, same pattern as the existing email notification at lines 108-114. The `return FollowUpResponse(**record)` at line 116 executes immediately after task creation, without awaiting the webhook POST.

risks:
  - Assignee email resolution adds a Supabase auth.admin call to the endpoint: This adds latency to the create_followup response since it happens before the return. Mitigation: The `get_user_by_id` call is fast (single row lookup), and the same pattern is used in `team.py` without issues. Alternatively, move the resolution into the async task so it doesn't block the response — but this requires the service-role client to be created in the task. The simpler approach is to resolve in the endpoint since the overhead is minimal (~10-50ms).
  - Race condition: If the Teams webhook POST completes after the event loop shuts down (e.g., in tests or server shutdown), the task may be cancelled. Mitigation: This is acceptable for fire-and-forget — the follow-up is already persisted. The same risk exists for the email notification and is an accepted trade-off.
  - The story AC1 mentions "priority" in the card, but the `action_followups` table has `category` (safety/oee/financial), not a separate priority field. Mitigation: Use `category` as the closest equivalent. The story's FactSet example shows "Category:" not "Priority:", confirming category is the intended field. The story title mentions "priority" generically but the Adaptive Card JSON template uses category.
  - The story says "message: {assigner_name} assigned you a follow-up..." but Teams Incoming Webhooks don't support DMs — the card goes to the channel. Mitigation: The card is posted to the channel as specified. The text summary in the card header or a summary TextBlock will contain the assignment message. Users see it as a channel notification, not a personal DM. This is explicitly called out in the story dev notes.
  - `build_followup_assignment_card` is a new function that could be accidentally inconsistent with existing card builders. Mitigation: Follow the exact same structure as `build_morning_summary_card` — same Adaptive Card schema/version, same return format, same `base_url.rstrip("/")` pattern, tested with same test structure.

estimated_test_files:
  - apps/api/tests/services/notifications/test_followup_assignment_card.py: Unit tests for `build_followup_assignment_card()` — validates Adaptive Card structure ($schema, type, version), header TextBlock "Follow-Up Assigned" with Bolder/Medium styling, FactSet with all fields (action summary, asset name, category, assigner name, note), note fact omitted when note is None, "View in App" Action.OpenUrl with correct URL format, base_url trailing slash handling. ~8-10 tests.
  - apps/api/tests/test_followup_teams_notification.py: Integration tests for the Teams notification in `create_followup()` — tests: endpoint returns 201 and dispatches Teams notification when teams_configured=True (mock send_card), endpoint returns 201 and skips Teams notification when teams_configured=False (send_card not called), webhook failure (mocked send_card returning success=False) does not affect follow-up creation (record still returned), assigner display name extracted from email local part, assignee display name resolved via auth.admin.get_user_by_id, debug log emitted when Teams skipped. ~6-8 tests.

implementation_order:
  1. Add `build_followup_assignment_card(followup_data: dict, base_url: str) -> dict` function to `apps/api/app/services/notifications/teams.py`. Pure function — build Adaptive Card v1.4 with "Follow-Up Assigned" header TextBlock, FactSet with Action/Asset/Category/Assigned by/Note facts (omit Note fact when value is None or empty), and "View in App" Action.OpenUrl button. Follow existing card builder patterns.
  2. Update `apps/api/app/services/notifications/__init__.py` — add `build_followup_assignment_card` to imports and `__all__`.
  3. Modify `apps/api/app/api/followups.py` `create_followup()` endpoint:
     a. Add imports: `from app.services.notifications import get_teams_client, build_followup_assignment_card`
     b. After the email notification block (line ~114), add a Teams notification block:
        - Check `settings.teams_configured`; if False, `logger.debug(...)` and skip
        - Resolve assignee display name: use `get_service_role_client().auth.admin.get_user_by_id(body.assigned_to)` to get assignee email, extract local part. Wrap in try/except, fall back to "Unknown".
        - Extract assigner display name from `current_user.email` local part
        - Build `teams_followup_data` dict with: action_summary, asset_name, category, assigner_name, assigned_to_name, note, report_date
        - Define async helper `_send_teams_followup_notification(data, base_url)` that builds the card and calls `get_teams_client().send_card()`, with full try/except wrapping
        - Dispatch via `asyncio.create_task(_send_teams_followup_notification(teams_followup_data, settings.app_base_url))`
  4. Create `apps/api/tests/services/notifications/test_followup_assignment_card.py` — unit tests for `build_followup_assignment_card()`. Test card structure, all FactSet fields, note omission when empty, URL construction, edge cases.
  5. Create `apps/api/tests/test_followup_teams_notification.py` — integration tests for the endpoint's Teams dispatch. Mock Supabase insert, auth.admin.get_user_by_id, get_teams_client, settings. Test dispatch happens, test skip when not configured, test failure resilience, test fire-and-forget behavior.
  6. Run full test suite to verify no regressions.
DESIGN END

---

## TEST_SPEC: 18-4-followup-assignment-teams-notification
**Timestamp:** 2026-02-12 09:58:18

TEST SPEC START
story_id: 18-4-followup-assignment-teams-notification
generated: 2026-02-12

test_specifications:

## AC1: Teams notification on follow-up assignment
Given a plant manager assigns a follow-up to a team member, when the assignment is saved, then a Teams notification is posted to the configured webhook channel containing: message "{assigner_name} assigned you a follow-up: {action_summary} on {asset_name}", an Adaptive Card with action summary, asset name, category, priority, assigner name, optional note, and a "View in App" button linking to the morning report page.

### 18-4-followup-assignment-teams-notification-UNIT-001: build_followup_assignment_card produces valid Adaptive Card structure
- Priority: P0
- Type: unit
- Given: A followup_data dict with action_summary="Inspect belt tension", asset_name="Grinder 5", category="safety", assigner_name="john.doe", note="Check by EOD", report_date="2026-02-10" and base_url="https://app.example.com"
- When: build_followup_assignment_card(followup_data, base_url) is called
- Then: The returned dict contains $schema="http://adaptivecards.io/schemas/adaptive-card.json", type="AdaptiveCard", version="1.4", a body array, and an actions array
- Data: Standard followup_data dict with all fields populated

### 18-4-followup-assignment-teams-notification-UNIT-002: Card header TextBlock displays "Follow-Up Assigned"
- Priority: P0
- Type: unit
- Given: A followup_data dict with all required fields
- When: build_followup_assignment_card(followup_data, base_url) is called
- Then: The first element in body is a TextBlock with text="Follow-Up Assigned", weight="Bolder", size="Medium"
- Data: Standard followup_data dict

### 18-4-followup-assignment-teams-notification-UNIT-003: Card FactSet contains all required fields
- Priority: P0
- Type: unit
- Given: A followup_data dict with action_summary="Inspect belt tension", asset_name="Grinder 5", category="safety", assigner_name="john.doe", note="Check by EOD"
- When: build_followup_assignment_card(followup_data, base_url) is called
- Then: The card body contains a FactSet with facts for "Action:" (value="Inspect belt tension"), "Asset:" (value="Grinder 5"), "Category:" (value="safety"), "Assigned by:" (value="john.doe"), and "Note:" (value="Check by EOD")
- Data: followup_data with all fields including non-empty note

### 18-4-followup-assignment-teams-notification-UNIT-004: Note fact is omitted when note is None
- Priority: P1
- Type: unit
- Given: A followup_data dict with note=None
- When: build_followup_assignment_card(followup_data, base_url) is called
- Then: The FactSet does not contain a fact with title "Note:", and the remaining facts (Action, Asset, Category, Assigned by) are still present
- Data: followup_data with note=None

### 18-4-followup-assignment-teams-notification-UNIT-005: Note fact is omitted when note is empty string
- Priority: P1
- Type: unit
- Given: A followup_data dict with note=""
- When: build_followup_assignment_card(followup_data, base_url) is called
- Then: The FactSet does not contain a fact with title "Note:", and the remaining facts are still present
- Data: followup_data with note=""

### 18-4-followup-assignment-teams-notification-UNIT-006: View in App button has correct URL with report_date
- Priority: P0
- Type: unit
- Given: A followup_data dict with report_date="2026-02-10" and base_url="https://app.example.com"
- When: build_followup_assignment_card(followup_data, base_url) is called
- Then: The actions array contains one Action.OpenUrl with title="View in App" and url="https://app.example.com/morning-report?date=2026-02-10"
- Data: followup_data with report_date="2026-02-10", base_url="https://app.example.com"

### 18-4-followup-assignment-teams-notification-UNIT-007: base_url trailing slash is stripped before URL construction
- Priority: P1
- Type: unit
- Given: A followup_data dict with report_date="2026-02-10" and base_url="https://app.example.com/"
- When: build_followup_assignment_card(followup_data, base_url) is called
- Then: The "View in App" button URL is "https://app.example.com/morning-report?date=2026-02-10" (no double slash)
- Data: base_url with trailing slash

### 18-4-followup-assignment-teams-notification-INT-001: POST /followups creates follow-up and dispatches Teams notification
- Priority: P0
- Type: integration
- Given: A valid JWT-authenticated user, teams_configured=True, Supabase insert returns a created record, and get_teams_client().send_card() is mocked
- When: POST /api/v1/actions/followups is called with valid follow-up data
- Then: The endpoint returns 201 with the created follow-up, and asyncio.create_task is called with the Teams notification coroutine, and send_card is invoked with a dict containing Adaptive Card structure with correct followup fields
- Data: Valid FollowUpCreateRequest body, mock Supabase return data, mock Teams client

### 18-4-followup-assignment-teams-notification-INT-002: Assigner display name extracted from current_user email local part
- Priority: P1
- Type: integration
- Given: current_user.email="john.doe@company.com", teams_configured=True
- When: POST /api/v1/actions/followups is called
- Then: The followup_data passed to build_followup_assignment_card contains assigner_name="john.doe" (local part before @)
- Data: JWT payload with email="john.doe@company.com"

### 18-4-followup-assignment-teams-notification-INT-003: Assignee display name resolved via auth.admin.get_user_by_id
- Priority: P1
- Type: integration
- Given: assigned_to UUID corresponds to a user with email="jane.smith@company.com", teams_configured=True, Supabase auth.admin.get_user_by_id returns user record with that email
- When: POST /api/v1/actions/followups is called with assigned_to=<UUID>
- Then: The followup_data passed to build_followup_assignment_card contains assigned_to_name="jane.smith"
- Data: Mock Supabase auth.admin.get_user_by_id returning user with email="jane.smith@company.com"

## AC2: Graceful degradation when Teams not configured
Given Teams notifications are not configured (no TEAMS_WEBHOOK_URL), when a follow-up is assigned, then the assignment succeeds normally, and a debug-level log is emitted that Teams notification was skipped, and no error is raised.

### 18-4-followup-assignment-teams-notification-INT-004: Teams notification skipped when teams_configured is False
- Priority: P0
- Type: integration
- Given: settings.teams_configured=False (TEAMS_WEBHOOK_URL is empty), a valid JWT-authenticated user, Supabase insert succeeds
- When: POST /api/v1/actions/followups is called with valid follow-up data
- Then: The endpoint returns 201 with the created follow-up, get_teams_client().send_card() is NOT called, and no error is raised
- Data: Valid FollowUpCreateRequest body, mock settings with teams_configured=False

### 18-4-followup-assignment-teams-notification-INT-005: Debug log emitted when Teams notification is skipped
- Priority: P1
- Type: integration
- Given: settings.teams_configured=False
- When: POST /api/v1/actions/followups is called with valid follow-up data
- Then: A debug-level log message is emitted containing "Teams notification skipped" (or equivalent), and no error-level log is emitted for Teams
- Data: caplog fixture at DEBUG level

### 18-4-followup-assignment-teams-notification-UNIT-008: TeamsWebhookClient.send_card returns not-configured result when webhook URL is empty
- Priority: P1
- Type: unit
- Given: TeamsWebhookClient instantiated with webhook_url="" (is_configured=False)
- When: send_card(card_payload) is called
- Then: Returns {"success": False, "message": "Teams webhook URL not configured", "status_code": None} without making any HTTP request
- Data: Any valid card_payload dict

## AC3: Graceful failure on webhook error
Given the Teams webhook POST fails (network error, invalid URL, non-2xx response), when the notification is attempted, then the failure is logged with error details, and the follow-up assignment is NOT rolled back, and the API response is not delayed or affected.

### 18-4-followup-assignment-teams-notification-UNIT-009: Webhook timeout is logged and does not propagate
- Priority: P0
- Type: unit
- Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post raises httpx.TimeoutException
- When: send_card(card_payload) is called
- Then: Returns {"success": False, "message": "Request timed out", "status_code": None}, an error is logged containing "timed out", and no exception propagates
- Data: Mock httpx.AsyncClient to raise TimeoutException

### 18-4-followup-assignment-teams-notification-UNIT-010: Webhook HTTP error (non-2xx) is logged and does not propagate
- Priority: P0
- Type: unit
- Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post returns a 400 response that raises HTTPStatusError on raise_for_status()
- When: send_card(card_payload) is called
- Then: Returns {"success": False, "message": containing "HTTP 400", "status_code": 400}, an error is logged, and no exception propagates
- Data: Mock httpx response with status_code=400

### 18-4-followup-assignment-teams-notification-UNIT-011: Webhook connection error is logged and does not propagate
- Priority: P0
- Type: unit
- Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post raises httpx.ConnectError
- When: send_card(card_payload) is called
- Then: Returns {"success": False, "message": containing "Connection failed", "status_code": None}, an error is logged, and no exception propagates
- Data: Mock httpx.AsyncClient to raise ConnectError

### 18-4-followup-assignment-teams-notification-UNIT-012: Unexpected exception is caught and logged
- Priority: P1
- Type: unit
- Given: TeamsWebhookClient with a valid webhook_url, httpx.AsyncClient.post raises an unexpected RuntimeError
- When: send_card(card_payload) is called
- Then: Returns {"success": False, "message": containing "Unexpected error: RuntimeError", "status_code": None}, an error is logged, and no exception propagates
- Data: Mock httpx.AsyncClient to raise RuntimeError("something broke")

### 18-4-followup-assignment-teams-notification-INT-006: Webhook failure does not roll back follow-up creation
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, Supabase insert succeeds, get_teams_client().send_card() returns {"success": False, "message": "Request timed out", "status_code": None}
- When: POST /api/v1/actions/followups is called with valid data
- Then: The endpoint returns 201 with the created follow-up record (insert NOT rolled back), and an error may be logged for the Teams failure
- Data: Mock send_card returning failure result

### 18-4-followup-assignment-teams-notification-INT-007: Exception in Teams dispatch block does not affect API response
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, Supabase insert succeeds, get_teams_client() raises an unexpected Exception during instantiation
- When: POST /api/v1/actions/followups is called with valid data
- Then: The endpoint returns 201 with the created follow-up record, the exception is caught and logged, and the follow-up creation is not affected
- Data: Mock get_teams_client to raise RuntimeError

## AC4: Fire-and-forget delivery
Given a follow-up is being assigned, when the Teams notification is triggered, then the API response returns immediately with the created follow-up, and the Teams webhook POST happens asynchronously (does not block the response).

### 18-4-followup-assignment-teams-notification-INT-008: Teams notification dispatched via asyncio.create_task (fire-and-forget)
- Priority: P0
- Type: integration
- Given: settings.teams_configured=True, Supabase insert succeeds, Teams client is mocked
- When: POST /api/v1/actions/followups is called
- Then: asyncio.create_task() is called to dispatch the Teams notification (verified by mocking asyncio.create_task), and the endpoint returns the follow-up response without awaiting the task
- Data: Mock asyncio.create_task, verify it receives a coroutine

### 18-4-followup-assignment-teams-notification-INT-009: API response returns immediately regardless of webhook latency
- Priority: P1
- Type: integration
- Given: settings.teams_configured=True, Supabase insert succeeds, Teams send_card is mocked with AsyncMock
- When: POST /api/v1/actions/followups is called
- Then: The response is returned with status 201 and includes the created follow-up data, the response does not wait for the Teams webhook to complete
- Data: AsyncMock for send_card that simulates delayed response (asyncio.sleep in side_effect)

### 18-4-followup-assignment-teams-notification-INT-010: Both email and Teams notifications dispatched as separate fire-and-forget tasks
- Priority: P1
- Type: integration
- Given: settings.teams_configured=True, email notification service is mocked, Teams client is mocked, Supabase insert succeeds
- When: POST /api/v1/actions/followups is called
- Then: asyncio.create_task is called at least twice — once for email notification and once for Teams notification — and both are independent fire-and-forget tasks
- Data: Mock both notification services, verify both are dispatched

edge_cases:
  - Assigner email is None or empty: assigner_name should fall back to "Unknown" rather than crashing
  - Assignee user lookup fails (auth.admin.get_user_by_id raises exception): assigned_to_name should fall back to "Unknown", Teams notification should still attempt with fallback name
  - report_date is a string vs date object: build_followup_assignment_card should handle both formats for URL construction
  - Very long action_summary or note text in FactSet: verify card builds without truncation errors (Teams handles display truncation)
  - Category value edge cases: verify all valid category values (safety, oee, financial) render correctly in the card FactSet
  - Multiple rapid follow-up assignments: each should dispatch its own independent Teams notification task without interference

error_scenarios:
  - Teams webhook URL is malformed (not a valid URL): httpx raises an error, caught by send_card error handling
  - Supabase auth.admin.get_user_by_id returns no user (deleted user assigned): fallback to "Unknown" display name
  - asyncio.create_task fails (e.g., event loop closing during shutdown): caught by outer try/except, follow-up still returned
  - Teams webhook returns 429 Too Many Requests: handled as non-2xx HTTP error, logged, no retry
  - Network partition during webhook POST: handled as ConnectError or TimeoutException

test_file_mapping:
  - 18-4-followup-assignment-teams-notification-UNIT-001 to UNIT-007: apps/api/tests/services/notifications/test_followup_assignment_card.py
  - 18-4-followup-assignment-teams-notification-UNIT-008 to UNIT-012: apps/api/tests/services/notifications/test_followup_assignment_card.py
  - 18-4-followup-assignment-teams-notification-INT-001 to INT-010: apps/api/tests/test_followup_teams_notification.py

TEST SPEC END

---

## DESIGN: 18-5-escalation-nudge-notifications
**Timestamp:** 2026-02-12 10:29:03

DESIGN START
story_id: 18-5-escalation-nudge-notifications

files_to_modify:
  - path: apps/api/app/core/config.py
    action: modify
    purpose: Add escalation-related settings — `escalation_check_interval_minutes` (int, default 60), `escalation_safety_threshold_hours` (int, default 2), `escalation_followup_threshold_hours` (int, default 24), `escalation_cooldown_hours` (int, default 4). These follow the existing field pattern (e.g., `sql_query_timeout`, `cache_live_ttl`). No new property needed — `teams_configured` already exists.

  - path: apps/api/.env.example
    action: modify
    purpose: Add `ESCALATION_CHECK_INTERVAL_MINUTES=60`, `ESCALATION_SAFETY_THRESHOLD_HOURS=2`, `ESCALATION_FOLLOWUP_THRESHOLD_HOURS=24`, `ESCALATION_COOLDOWN_HOURS=4` entries under a new "# Escalation Nudge Configuration (Story 18.5)" section, after the Teams webhook section.

  - path: supabase/migrations/0036_escalation_nudge_log.sql
    action: create
    purpose: Create `escalation_nudge_log` table for persistent rate-limit tracking across process restarts. Schema: `id UUID PK DEFAULT gen_random_uuid()`, `item_type TEXT NOT NULL` ('safety_event' | 'followup'), `item_id TEXT NOT NULL`, `nudge_sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `channel TEXT NOT NULL DEFAULT 'teams'`. Index on `(item_type, item_id, nudge_sent_at DESC)` for fast recent-nudge lookups. RLS enabled with service_role-only full access policy.

  - path: apps/api/app/services/notifications/escalation.py
    action: create
    purpose: Core escalation check module. Contains `EscalationChecker` class with: `__init__()` (creates Supabase service-role client using `create_client(settings.supabase_url, settings.supabase_key)` pattern from morning_report.py), `check_unacknowledged_safety_items()` — queries `safety_events` where `is_resolved = FALSE` and `created_at < NOW() - {safety_threshold_hours}`, joins with `assets` to get `asset_name`, `check_stale_followups()` — queries `action_followups` where `status = 'assigned'` and `updated_at < NOW() - {followup_threshold_hours}`, `_was_recently_nudged(item_type, item_id)` — checks `escalation_nudge_log` for any row within the cooldown window, `_record_nudge(item_type, item_id)` — inserts into `escalation_nudge_log`. Also contains the module-level `run_escalation_check()` async function that serves as the scheduler entry point — it instantiates `EscalationChecker`, runs both checks, applies rate limiting, and dispatches cards via `get_teams_client().send_card()`, all wrapped in try/except that logs and never raises.

  - path: apps/api/app/services/notifications/teams.py
    action: modify
    purpose: Add two card builder functions: `build_safety_escalation_card(asset_name: str, hours_elapsed: float, severity: str, report_date: date, base_url: str) -> dict` — Adaptive Card with title "Escalation: Safety Alert Unacknowledged", message body "Safety alert on {asset_name} has been unacknowledged for {hours} hours. Please review.", severity info, and "Open Report" Action.OpenUrl. `build_followup_escalation_card(asset_name: str, assignee_name: str, hours_since_update: float, base_url: str, report_date: date) -> dict` — Adaptive Card with title "Escalation: Follow-Up Stale", message "Follow-up for {asset_name} assigned to {assignee_name} has had no update for {hours} hours.", and "Open Report" button. Both follow the exact pattern of `build_morning_summary_card()` and `build_followup_assignment_card()`.

  - path: apps/api/app/services/notifications/__init__.py
    action: modify
    purpose: Add imports and exports for the two new card builders (`build_safety_escalation_card`, `build_followup_escalation_card`) and the `run_escalation_check` entry point function. Add these to `__all__`.

  - path: apps/api/app/main.py
    action: modify
    purpose: In the `lifespan()` function, after `await scheduler.start()`, add the escalation check as a second job directly on `scheduler._scheduler` (the underlying `AsyncIOScheduler`). Import `run_escalation_check` from `app.services.notifications.escalation` and `IntervalTrigger` (already imported in scheduler.py but needed here). Register with `scheduler._scheduler.add_job(run_escalation_check, IntervalTrigger(minutes=settings.escalation_check_interval_minutes), id="escalation_check", name="Escalation Nudge Check", replace_existing=True, misfire_grace_time=120)`. Guard with try/except and a log warning on failure. This follows Option A from the dev notes (minimal scope — no PipelineScheduler class modification).

  - path: apps/api/tests/services/notifications/test_escalation.py
    action: create
    purpose: Unit and integration tests for `EscalationChecker` and `run_escalation_check()`. Tests: AC#1 — unacknowledged safety item >2h triggers card, AC#2 — stale follow-up >24h triggers card, AC#3 — recently updated follow-up does NOT trigger, AC#4 — no Teams configured skips with INFO log, AC#5 — rate limiting prevents duplicate nudge within 4h, plus edge cases (no items found, mixed items some nudged some not, Supabase query failure doesn't crash).

  - path: apps/api/tests/services/notifications/test_escalation_cards.py
    action: create
    purpose: Unit tests for `build_safety_escalation_card()` and `build_followup_escalation_card()`. Tests: valid Adaptive Card structure ($schema, type, version), correct title text, message body with interpolated values, "Open Report" button URL, severity rendering, assignee name rendering, edge cases (trailing slash in base_url, long asset names).

patterns_to_use:
  - Supabase service-role client pattern: Use `create_client(settings.supabase_url, settings.supabase_key)` — the service key provides full access bypassing RLS. Exactly as done in `morning_report.py:95-105` and `live_pulse.py:198`.
  - Settings guard pattern: Check `settings.teams_configured` early in `run_escalation_check()` and return with `logger.info(...)` if False. This is the exact pattern at `morning_report.py:547-549`.
  - Card builder standalone function pattern: Pure functions returning Adaptive Card v1.4 dicts (inner content only — `send_card()` wraps in the message envelope). Following `build_morning_summary_card()`, `build_all_clear_card()`, `build_followup_assignment_card()` in `teams.py`.
  - Fire-and-forget error isolation pattern: Entire `run_escalation_check()` body wrapped in `try/except Exception` that calls `logger.error()` and returns — never raises. This ensures the scheduler is never crashed by escalation failures. Follows `_trigger_smart_summary_generation()` at `morning_report.py:525-530`.
  - Direct scheduler job registration: Add job on `scheduler._scheduler` (the `AsyncIOScheduler` instance) after `scheduler.start()` in `lifespan()`. Uses `IntervalTrigger(minutes=...)` with `id`, `name`, `replace_existing=True`, `misfire_grace_time`. This avoids modifying `PipelineScheduler` class (Option A from dev notes).
  - Test data factory pattern: Follow `test_trigger_teams_notification.py` factory functions (`_make_action_item`, `_make_action_list_response`). Create factories for fake safety_events and followup records.
  - Test mocking pattern: Use `unittest.mock.patch` with `MagicMock` for Supabase client, `AsyncMock` for async `send_card()`. Mock `create_client` to return controlled responses. Follow patterns in `test_trigger_teams_notification.py`.
  - pydantic-settings config pattern: Add new int fields with defaults directly on the `Settings` class in `config.py`. No property needed — just plain fields. Follows `sql_query_timeout: int = 30` pattern at line 44.

dependencies:
  - httpx: installed (requirements.txt: `httpx>=0.26.0`)
  - supabase-py: installed (used throughout for database access)
  - apscheduler: installed (used by scheduler.py)
  - pydantic-settings: installed (used by config.py)
  - No new dependencies needed

acceptance_criteria_mapping:
  - AC1 (Safety item unacknowledged 2+ hours → Teams nudge with link):
    - `escalation.py`: `EscalationChecker.check_unacknowledged_safety_items()` queries `safety_events` WHERE `is_resolved = FALSE` AND `created_at < NOW() - 2 hours`, joins with `assets` for `asset_name`. Returns list of dicts with `id`, `asset_name`, `severity`, `created_at`, `hours_elapsed`.
    - `teams.py`: `build_safety_escalation_card()` builds Adaptive Card with "Safety alert on {asset_name} has been unacknowledged for {hours} hours. Please review." and "Open Report" Action.OpenUrl to `/morning-report?date={today}`.
    - `escalation.py`: `run_escalation_check()` orchestrates — checks rate limit, sends card via `get_teams_client().send_card()`, records nudge.
  - AC2 (Follow-up assigned 24+ hours with no update → Teams nudge):
    - `escalation.py`: `EscalationChecker.check_stale_followups()` queries `action_followups` WHERE `status = 'assigned'` AND `updated_at < NOW() - 24 hours`. Returns list of dicts with `id`, `asset_name`, `assigned_to` (UUID), `updated_at`, `hours_since_update`. Resolves assignee display name from `auth.users` email via Supabase admin API (or from a join/subquery on the assigned_to UUID).
    - `teams.py`: `build_followup_escalation_card()` builds Adaptive Card with "Follow-up for {asset_name} assigned to {assignee} has had no update for 24 hours."
  - AC3 (Recently updated follow-up → no nudge):
    - `escalation.py`: `check_stale_followups()` query includes `updated_at < NOW() - 24 hours` filter, so recently updated follow-ups are excluded at the database level. No additional code path needed — they simply don't appear in the result set.
  - AC4 (Teams not configured → no nudge, INFO log):
    - `escalation.py`: `run_escalation_check()` checks `settings.teams_configured` at the top. If False, logs `logger.info("Teams webhook not configured, skipping escalation check")` and returns immediately. No database queries, no card building, no send_card call.
  - AC5 (Rate limiting — max once per 4 hours per item):
    - `supabase/migrations/0036_escalation_nudge_log.sql`: Creates `escalation_nudge_log` table.
    - `escalation.py`: `EscalationChecker._was_recently_nudged(item_type, item_id)` queries `escalation_nudge_log` WHERE `item_type = ?` AND `item_id = ?` AND `nudge_sent_at > NOW() - {cooldown_hours}`, returns True if any row exists.
    - `escalation.py`: `EscalationChecker._record_nudge(item_type, item_id)` inserts a row into `escalation_nudge_log` after successful send.
    - `run_escalation_check()`: For each escalation candidate, calls `_was_recently_nudged()` before sending; skips if True. After successful `send_card()`, calls `_record_nudge()`.

risks:
  - Direct access to `scheduler._scheduler` (private attribute): This couples the escalation job registration to PipelineScheduler internals. Mitigation: The attribute is checked for None in the existing codebase (`PipelineSchedulerStatus.to_dict()` at line 73-74 also accesses `scheduler._scheduler`), so this is an established internal pattern. Add a code comment noting this is Option A per Story 18.5 dev notes.
  - Supabase service-role client in a background task: The client is created per-check (every ~60 min) and not shared. If credentials rotate or become invalid, the check will fail. Mitigation: The try/except wrapper in `run_escalation_check()` catches all exceptions and logs them. The scheduler will retry on the next interval. No restart needed.
  - `safety_events.created_at` vs `event_timestamp` for the 2-hour threshold: The story says "on the report for 2+ hours." The `created_at` field represents when the record was inserted into Supabase (pipeline ingestion time), which is the closest proxy for "on the report" time. `event_timestamp` is when the actual safety event occurred in MSSQL. Mitigation: Use `created_at` as it reflects when the system became aware of the event. Document this decision in a code comment.
  - Assignee display name resolution for stale follow-ups: The `action_followups` table has `assigned_to UUID` but no email/name. Resolving the name requires a Supabase `auth.admin.get_user_by_id()` call per assignee. Mitigation: Batch resolution — collect unique assigned_to UUIDs, resolve all at once. If resolution fails, fall back to "Unknown" rather than skipping the nudge. This matches the pattern in `followups.py`.
  - `escalation_nudge_log` table grows unbounded: Mitigation: This is acceptable for now — escalation checks run infrequently (1/hr) and only insert on nudge events (rare). Add a comment noting that a cleanup job (delete rows older than 30 days) could be added as a future optimization. The query uses an index on `(item_type, item_id, nudge_sent_at)` so even with growth, lookups remain fast.
  - Scheduler not started when adding the escalation job: If `scheduler.start()` fails, the `_scheduler` attribute will be None and `add_job` will fail. Mitigation: Guard the escalation job registration with a check `if scheduler._scheduler is not None and scheduler._scheduler.running:` before calling `add_job`. Log a warning if skipped.
  - Date for "Open Report" link in safety escalation: Safety events don't have a `report_date` field. Mitigation: Use `date.today()` (the current date when the check runs) for the report link URL, since the morning report defaults to the most recent date. This is a reasonable approximation.

estimated_test_files:
  - apps/api/tests/services/notifications/test_escalation_cards.py: Unit tests for `build_safety_escalation_card()` and `build_followup_escalation_card()` — validates Adaptive Card structure, title text, interpolated message body, severity field, assignee field, "Open Report" URL construction, base_url trailing slash handling, edge cases.
  - apps/api/tests/services/notifications/test_escalation.py: Unit and integration tests for `EscalationChecker` and `run_escalation_check()`. Tests: unacknowledged safety item >2h triggers escalation card (AC#1); stale follow-up >24h triggers escalation card (AC#2); recently updated follow-up excluded by query (AC#3); no Teams config skips with INFO log (AC#4); rate-limit prevents duplicate within 4h (AC#5); rate-limit allows after 4h; no items found → no cards sent; Supabase query failure caught and logged; send_card failure caught and logged; run_escalation_check orchestrates all checks correctly; _record_nudge inserts into DB; _was_recently_nudged returns correct boolean.

implementation_order:
  1. Add escalation config fields to `apps/api/app/core/config.py`: `escalation_check_interval_minutes: int = 60`, `escalation_safety_threshold_hours: int = 2`, `escalation_followup_threshold_hours: int = 24`, `escalation_cooldown_hours: int = 4`. Smallest change, foundational for all other code.
  2. Add env var entries to `apps/api/.env.example` under new "# Escalation Nudge Configuration (Story 18.5)" section.
  3. Create `supabase/migrations/0036_escalation_nudge_log.sql` with the `escalation_nudge_log` table, composite index, and RLS policy for service_role only.
  4. Add card builder functions to `apps/api/app/services/notifications/teams.py`: `build_safety_escalation_card()` and `build_followup_escalation_card()`. Pure functions, easy to implement and test in isolation.
  5. Create `apps/api/app/services/notifications/escalation.py` with `EscalationChecker` class implementing `check_unacknowledged_safety_items()`, `check_stale_followups()`, `_was_recently_nudged()`, `_record_nudge()`, and the module-level `run_escalation_check()` async function.
  6. Update `apps/api/app/services/notifications/__init__.py` — add exports for `build_safety_escalation_card`, `build_followup_escalation_card`, and `run_escalation_check`.
  7. Modify `apps/api/app/main.py` `lifespan()` — after `scheduler.start()`, register the escalation check job on `scheduler._scheduler` using `IntervalTrigger` with configurable interval. Guard with try/except.
  8. Create `apps/api/tests/services/notifications/test_escalation_cards.py` — unit tests for both escalation card builders.
  9. Create `apps/api/tests/services/notifications/test_escalation.py` — unit and integration tests for `EscalationChecker` and `run_escalation_check()`, covering all 5 ACs plus edge cases and error scenarios.
  10. Run full test suite to verify no regressions.
DESIGN END

---

## TEST_SPEC: 18-5-escalation-nudge-notifications
**Timestamp:** 2026-02-12 10:32:52

TEST SPEC START
story_id: 18-5-escalation-nudge-notifications
generated: 2026-02-12

test_specifications:

## AC1: Given a safety action item has been on the report for 2+ hours without acknowledgment, When the escalation check runs, Then a Teams notification is posted with the unacknowledged message and a direct link to the morning report.

### 18-5-escalation-nudge-notifications-UNIT-001: Safety escalation card contains correct title and message body
- Priority: P0
- Type: unit
- Given: A safety event with asset_name="Mixer-01", hours_elapsed=3.5, severity="high", report_date=2026-02-12
- When: `build_safety_escalation_card()` is called with those parameters and base_url="https://app.example.com"
- Then: The returned card contains title "Escalation: Safety Alert Unacknowledged" and body text "Safety alert on Mixer-01 has been unacknowledged for 3.5 hours. Please review."
- Data: asset_name="Mixer-01", hours_elapsed=3.5, severity="high", report_date=date(2026, 2, 12), base_url="https://app.example.com"

### 18-5-escalation-nudge-notifications-UNIT-002: Safety escalation card contains Open Report action button with correct URL
- Priority: P0
- Type: unit
- Given: A safety event with report_date=2026-02-12 and base_url="https://app.example.com"
- When: `build_safety_escalation_card()` is called
- Then: The card has an actions array with one Action.OpenUrl titled "Open Report" pointing to "https://app.example.com/morning-report?date=2026-02-12"
- Data: report_date=date(2026, 2, 12), base_url="https://app.example.com"

### 18-5-escalation-nudge-notifications-UNIT-003: Safety escalation card has valid Adaptive Card v1.4 structure
- Priority: P0
- Type: unit
- Given: Valid input parameters for a safety escalation card
- When: `build_safety_escalation_card()` is called
- Then: The returned dict contains "$schema"="http://adaptivecards.io/schemas/adaptive-card.json", "type"="AdaptiveCard", "version"="1.4", a non-empty "body" array, and a non-empty "actions" array
- Data: Any valid safety event parameters

### 18-5-escalation-nudge-notifications-UNIT-004: Safety escalation card includes severity information
- Priority: P1
- Type: unit
- Given: A safety event with severity="critical"
- When: `build_safety_escalation_card()` is called
- Then: The card body contains the severity value "critical" in one of the TextBlock elements
- Data: severity="critical"

### 18-5-escalation-nudge-notifications-INT-001: Unacknowledged safety event older than 2 hours triggers Teams notification
- Priority: P0
- Type: integration
- Given: A safety event exists in `safety_events` with `is_resolved=FALSE` and `created_at` = 3 hours ago, and Teams webhook is configured, and no prior nudge has been sent for this item
- When: `run_escalation_check()` is called
- Then: `send_card()` is called exactly once with a safety escalation Adaptive Card payload containing the asset name and hours elapsed, and a nudge record is written to `escalation_nudge_log`
- Data: Mock Supabase returning one safety_event row: {id: "evt-1", asset_name: "Press-A", severity: "high", created_at: now - 3h, is_resolved: false}

### 18-5-escalation-nudge-notifications-INT-002: Acknowledged (resolved) safety event does NOT trigger escalation
- Priority: P0
- Type: integration
- Given: A safety event exists in `safety_events` with `is_resolved=TRUE` and `created_at` = 5 hours ago
- When: `run_escalation_check()` is called
- Then: No safety escalation card is sent via `send_card()` (the query filters out resolved events)
- Data: Mock Supabase returning empty result for safety items query (resolved items excluded by WHERE clause)

### 18-5-escalation-nudge-notifications-INT-003: Safety event younger than 2 hours does NOT trigger escalation
- Priority: P0
- Type: integration
- Given: A safety event exists in `safety_events` with `is_resolved=FALSE` and `created_at` = 30 minutes ago
- When: `run_escalation_check()` is called
- Then: No safety escalation card is sent (event is within the 2-hour threshold)
- Data: Mock Supabase returning empty result (event too recent to match threshold query)

### 18-5-escalation-nudge-notifications-INT-004: Multiple unacknowledged safety events each get separate notifications
- Priority: P1
- Type: integration
- Given: Three safety events exist, all with `is_resolved=FALSE` and `created_at` > 2 hours ago, no prior nudges
- When: `run_escalation_check()` is called
- Then: `send_card()` is called three times, once per event, and three nudge records are written
- Data: Mock Supabase returning three safety_event rows with distinct asset names

### 18-5-escalation-nudge-notifications-UNIT-005: Safety escalation card handles trailing slash in base_url
- Priority: P2
- Type: unit
- Given: base_url="https://app.example.com/" (with trailing slash)
- When: `build_safety_escalation_card()` is called
- Then: The "Open Report" URL is "https://app.example.com/morning-report?date=2026-02-12" (no double slash)
- Data: base_url="https://app.example.com/", report_date=date(2026, 2, 12)


## AC2: Given a follow-up has been in "assigned" status for 24+ hours with no status update, When the escalation check runs, Then a Teams notification is posted with the stale follow-up message.

### 18-5-escalation-nudge-notifications-UNIT-006: Follow-up escalation card contains correct title and message body
- Priority: P0
- Type: unit
- Given: A stale follow-up with asset_name="Boiler-3", assignee_name="John Doe", hours_since_update=36
- When: `build_followup_escalation_card()` is called with base_url="https://app.example.com" and report_date=2026-02-12
- Then: The returned card contains title "Escalation: Follow-Up Stale" and body text "Follow-up for Boiler-3 assigned to John Doe has had no update for 36 hours."
- Data: asset_name="Boiler-3", assignee_name="John Doe", hours_since_update=36

### 18-5-escalation-nudge-notifications-UNIT-007: Follow-up escalation card contains Open Report action button
- Priority: P0
- Type: unit
- Given: A follow-up escalation card with report_date=2026-02-10 and base_url="https://app.example.com"
- When: `build_followup_escalation_card()` is called
- Then: The card has an Action.OpenUrl titled "Open Report" with URL "https://app.example.com/morning-report?date=2026-02-10"
- Data: report_date=date(2026, 2, 10), base_url="https://app.example.com"

### 18-5-escalation-nudge-notifications-UNIT-008: Follow-up escalation card has valid Adaptive Card v1.4 structure
- Priority: P0
- Type: unit
- Given: Valid input parameters for a follow-up escalation card
- When: `build_followup_escalation_card()` is called
- Then: The returned dict contains "$schema", "type"="AdaptiveCard", "version"="1.4", non-empty "body" and "actions" arrays
- Data: Any valid follow-up parameters

### 18-5-escalation-nudge-notifications-INT-005: Stale follow-up in assigned status for 24+ hours triggers Teams notification
- Priority: P0
- Type: integration
- Given: An action_followup exists with `status='assigned'` and `updated_at` = 30 hours ago, Teams is configured, no prior nudge
- When: `run_escalation_check()` is called
- Then: `send_card()` is called with a follow-up escalation card containing the asset name and assignee name, and a nudge record is written
- Data: Mock Supabase returning one action_followup row: {id: "fu-1", asset_name: "Oven-2", assigned_to: "user-uuid-1", status: "assigned", updated_at: now - 30h}

### 18-5-escalation-nudge-notifications-INT-006: Follow-up in "in_progress" status does NOT trigger escalation
- Priority: P1
- Type: integration
- Given: An action_followup exists with `status='in_progress'` and `updated_at` = 48 hours ago
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent (query only matches status='assigned')
- Data: Mock Supabase returning empty result for stale followups query

### 18-5-escalation-nudge-notifications-INT-007: Follow-up in "resolved" status does NOT trigger escalation
- Priority: P1
- Type: integration
- Given: An action_followup exists with `status='resolved'` and `updated_at` = 72 hours ago
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent
- Data: Mock Supabase returning empty result for stale followups query

### 18-5-escalation-nudge-notifications-INT-008: Multiple stale follow-ups each get separate notifications
- Priority: P1
- Type: integration
- Given: Two action_followups exist, both with `status='assigned'` and `updated_at` > 24 hours ago, no prior nudges
- When: `run_escalation_check()` is called
- Then: `send_card()` is called twice, once per follow-up
- Data: Mock Supabase returning two stale followup rows

### 18-5-escalation-nudge-notifications-UNIT-009: Follow-up escalation card handles unknown assignee gracefully
- Priority: P2
- Type: unit
- Given: Assignee name resolution fails and falls back to "Unknown"
- When: `build_followup_escalation_card()` is called with assignee_name="Unknown"
- Then: The card body text reads "Follow-up for {asset_name} assigned to Unknown has had no update for {hours} hours."
- Data: assignee_name="Unknown"


## AC3: Given a follow-up was recently updated (within 24 hours), When the escalation check runs, Then no nudge is sent for that follow-up.

### 18-5-escalation-nudge-notifications-INT-009: Recently updated follow-up is excluded by database query
- Priority: P0
- Type: integration
- Given: An action_followup exists with `status='assigned'` and `updated_at` = 6 hours ago (within 24h)
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent; `send_card()` is not called for follow-ups
- Data: Mock Supabase returning empty result for stale followups query (updated_at within threshold)

### 18-5-escalation-nudge-notifications-INT-010: Follow-up updated exactly at 24-hour boundary is NOT escalated
- Priority: P1
- Type: integration
- Given: An action_followup exists with `status='assigned'` and `updated_at` = exactly 24 hours ago
- When: `run_escalation_check()` is called
- Then: No follow-up escalation card is sent (boundary condition: 24h is the threshold, requires > 24h)
- Data: Mock Supabase returning empty result at exact boundary

### 18-5-escalation-nudge-notifications-INT-011: Mix of stale and recently-updated follow-ups — only stale ones trigger
- Priority: P1
- Type: integration
- Given: Two follow-ups: one with `updated_at` = 48 hours ago (stale), one with `updated_at` = 2 hours ago (recent), both `status='assigned'`
- When: `run_escalation_check()` is called
- Then: `send_card()` is called exactly once for the stale follow-up; the recently updated one is skipped
- Data: Mock Supabase returning only the stale followup (DB query filters out recent)


## AC4: Given Teams notifications are not configured (no TEAMS_WEBHOOK_URL), When escalation conditions are met, Then no nudge is sent and the system logs a notice at INFO level.

### 18-5-escalation-nudge-notifications-INT-012: Teams not configured — escalation check skips entirely with INFO log
- Priority: P0
- Type: integration
- Given: `TEAMS_WEBHOOK_URL` is empty ("") and escalation-eligible items exist in the database
- When: `run_escalation_check()` is called
- Then: No `send_card()` is called, no database queries are made for safety_events or action_followups, and an INFO-level log message is emitted containing "not configured" or similar
- Data: Mock settings with teams_configured=False; use `caplog` fixture to capture log output

### 18-5-escalation-nudge-notifications-INT-013: Teams not configured — no Supabase queries are executed
- Priority: P1
- Type: integration
- Given: `TEAMS_WEBHOOK_URL` is empty
- When: `run_escalation_check()` is called
- Then: The Supabase client is never instantiated or queried (early return before any DB access)
- Data: Verify `create_client` is never called

### 18-5-escalation-nudge-notifications-UNIT-010: Settings.teams_configured returns False for empty string
- Priority: P1
- Type: unit
- Given: `teams_webhook_url=""` in Settings
- When: `teams_configured` property is accessed
- Then: Returns False
- Data: Settings(teams_webhook_url="")

### 18-5-escalation-nudge-notifications-UNIT-011: Settings.teams_configured returns False for whitespace-only string
- Priority: P2
- Type: unit
- Given: `teams_webhook_url="   "` in Settings
- When: `teams_configured` property is accessed
- Then: Returns False
- Data: Settings(teams_webhook_url="   ")


## AC5: Given an escalation nudge was already sent for an item, When less than 4 hours have passed since the last nudge, Then no duplicate nudge is sent (rate limiting: max once per 4 hours per item).

### 18-5-escalation-nudge-notifications-INT-014: Rate limiting prevents duplicate nudge within 4-hour window
- Priority: P0
- Type: integration
- Given: A safety event is eligible for escalation AND an entry exists in `escalation_nudge_log` with `item_type='safety_event'`, `item_id='evt-1'`, and `nudge_sent_at` = 2 hours ago
- When: `run_escalation_check()` is called
- Then: No `send_card()` is called for that item (rate-limited)
- Data: Mock Supabase returning one safety_event row AND returning a recent nudge log entry for _was_recently_nudged()

### 18-5-escalation-nudge-notifications-INT-015: Rate limiting allows nudge after 4-hour cooldown expires
- Priority: P0
- Type: integration
- Given: A safety event is eligible for escalation AND an entry exists in `escalation_nudge_log` with `nudge_sent_at` = 5 hours ago (past the 4-hour cooldown)
- When: `run_escalation_check()` is called
- Then: `send_card()` IS called for that item AND a new nudge record is written to `escalation_nudge_log`
- Data: Mock Supabase returning one safety_event row AND returning no recent nudge log entry (past cooldown)

### 18-5-escalation-nudge-notifications-INT-016: Rate limiting applies independently per item
- Priority: P1
- Type: integration
- Given: Two safety events (evt-1 and evt-2) are eligible, evt-1 was nudged 1 hour ago, evt-2 has never been nudged
- When: `run_escalation_check()` is called
- Then: `send_card()` is called once for evt-2 only; evt-1 is rate-limited
- Data: Mock Supabase returning two safety_events AND nudge log entry for evt-1 only

### 18-5-escalation-nudge-notifications-INT-017: Rate limiting applies to follow-up items independently from safety events
- Priority: P1
- Type: integration
- Given: One safety event (evt-1) and one follow-up (fu-1) are eligible; evt-1 was nudged 1 hour ago; fu-1 has never been nudged
- When: `run_escalation_check()` is called
- Then: `send_card()` is called once for fu-1; evt-1 is rate-limited
- Data: item_type distinction in nudge log prevents cross-type interference

### 18-5-escalation-nudge-notifications-UNIT-012: _was_recently_nudged returns True when nudge is within cooldown
- Priority: P0
- Type: unit
- Given: `escalation_nudge_log` has an entry for item_type="safety_event", item_id="evt-1" with nudge_sent_at = 1 hour ago, cooldown = 4 hours
- When: `_was_recently_nudged("safety_event", "evt-1")` is called
- Then: Returns True
- Data: Mock Supabase query returning one matching row

### 18-5-escalation-nudge-notifications-UNIT-013: _was_recently_nudged returns False when no prior nudge exists
- Priority: P0
- Type: unit
- Given: `escalation_nudge_log` has no entries for item_type="safety_event", item_id="evt-new"
- When: `_was_recently_nudged("safety_event", "evt-new")` is called
- Then: Returns False
- Data: Mock Supabase query returning empty result

### 18-5-escalation-nudge-notifications-UNIT-014: _record_nudge inserts entry into escalation_nudge_log
- Priority: P1
- Type: unit
- Given: A successful escalation nudge was sent for item_type="followup", item_id="fu-1"
- When: `_record_nudge("followup", "fu-1")` is called
- Then: A row is inserted into `escalation_nudge_log` with item_type="followup", item_id="fu-1", channel="teams", and nudge_sent_at close to now
- Data: Verify Supabase insert call arguments

### 18-5-escalation-nudge-notifications-INT-018: Rate limiting at exact 4-hour boundary
- Priority: P2
- Type: integration
- Given: A safety event is eligible AND the last nudge was exactly 4 hours ago
- When: `run_escalation_check()` is called
- Then: The behavior depends on whether the query uses `<` or `<=` for the cooldown check; test documents the expected boundary behavior (nudge should be allowed at exactly 4h)
- Data: Mock nudge_sent_at = now - 4h exactly


## Cross-cutting: Error handling and orchestration

### 18-5-escalation-nudge-notifications-INT-019: run_escalation_check orchestrates safety and follow-up checks
- Priority: P0
- Type: integration
- Given: Both safety events and stale follow-ups exist, Teams is configured, no prior nudges
- When: `run_escalation_check()` is called
- Then: Both `check_unacknowledged_safety_items()` and `check_stale_followups()` are called, and `send_card()` is invoked for each eligible item
- Data: Mock Supabase returning items from both queries

### 18-5-escalation-nudge-notifications-INT-020: Supabase query failure does not crash the scheduler
- Priority: P0
- Type: integration
- Given: Teams is configured AND the Supabase client raises an exception during safety_events query
- When: `run_escalation_check()` is called
- Then: The exception is caught and logged at ERROR level; the function returns without raising; the scheduler continues to run
- Data: Mock Supabase `select().execute()` raising `Exception("Connection refused")`; verify via `caplog`

### 18-5-escalation-nudge-notifications-INT-021: send_card failure does not crash the scheduler or prevent subsequent checks
- Priority: P0
- Type: integration
- Given: Multiple eligible items exist AND `send_card()` fails (returns success=False) for the first item
- When: `run_escalation_check()` is called
- Then: The failure is logged, but subsequent items are still processed; the function does not raise
- Data: Mock send_card returning {"success": False, "message": "HTTP 500"} for first call, then succeeding

### 18-5-escalation-nudge-notifications-INT-022: No items found — no notifications sent, no errors
- Priority: P1
- Type: integration
- Given: No safety events are unacknowledged and no follow-ups are stale, Teams is configured
- When: `run_escalation_check()` is called
- Then: `send_card()` is never called; no errors are logged; function completes normally
- Data: Mock Supabase returning empty lists for both queries

### 18-5-escalation-nudge-notifications-INT-023: _record_nudge failure does not prevent notification delivery
- Priority: P1
- Type: integration
- Given: An eligible safety event exists, Teams is configured, send_card succeeds, but _record_nudge raises an exception
- When: `run_escalation_check()` is called
- Then: The notification is still sent (card was already delivered), the error is logged, and subsequent items continue processing
- Data: Mock _record_nudge raising Exception; verify send_card was still called

### 18-5-escalation-nudge-notifications-UNIT-015: EscalationChecker uses configurable threshold from settings
- Priority: P1
- Type: unit
- Given: Settings has `escalation_safety_threshold_hours=4` (non-default value)
- When: `check_unacknowledged_safety_items()` constructs its query
- Then: The query uses a 4-hour threshold instead of the default 2 hours
- Data: Mock settings with custom threshold; verify Supabase query includes correct interval

### 18-5-escalation-nudge-notifications-UNIT-016: EscalationChecker uses configurable follow-up threshold from settings
- Priority: P1
- Type: unit
- Given: Settings has `escalation_followup_threshold_hours=48` (non-default value)
- When: `check_stale_followups()` constructs its query
- Then: The query uses a 48-hour threshold instead of the default 24 hours
- Data: Mock settings with custom threshold

### 18-5-escalation-nudge-notifications-UNIT-017: EscalationChecker uses configurable cooldown from settings
- Priority: P1
- Type: unit
- Given: Settings has `escalation_cooldown_hours=8` (non-default value)
- When: `_was_recently_nudged()` constructs its query
- Then: The query checks for nudges within the last 8 hours instead of the default 4
- Data: Mock settings with custom cooldown


## Migration and schema

### 18-5-escalation-nudge-notifications-UNIT-018: escalation_nudge_log migration creates correct table schema
- Priority: P1
- Type: unit
- Given: The SQL migration file `0036_escalation_nudge_log.sql` exists
- When: The migration SQL is reviewed
- Then: It creates a table `escalation_nudge_log` with columns: id UUID PK, item_type TEXT NOT NULL, item_id TEXT NOT NULL, nudge_sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), channel TEXT NOT NULL DEFAULT 'teams'; it creates a composite index on (item_type, item_id, nudge_sent_at DESC); it enables RLS with service_role-only full access
- Data: Static SQL file review


edge_cases:
  - Safety event created exactly 2 hours ago (boundary condition for threshold)
  - Follow-up updated exactly 24 hours ago (boundary condition for staleness)
  - Nudge sent exactly 4 hours ago (boundary condition for rate limiting)
  - Very long asset_name or assignee_name in card text (potential rendering issues)
  - Multiple safety events for the same asset (each should get independent nudges)
  - Follow-up with NULL asset_name (column is nullable per schema)
  - Concurrent escalation check runs (scheduler fires overlapping executions)
  - Supabase returns partial failure (e.g., safety query succeeds but followup query fails)
  - Teams webhook returns HTTP 429 (rate limited by Teams itself)
  - System clock skew affecting threshold calculations

error_scenarios:
  - Supabase client creation fails (invalid URL or key)
  - Supabase query times out
  - Teams webhook URL is malformed
  - Teams webhook returns 500 Internal Server Error
  - Teams webhook connection refused
  - Teams webhook times out (>10s)
  - escalation_nudge_log insert fails (DB constraint violation)
  - escalation_nudge_log query fails during rate-limit check
  - Assignee UUID resolution fails (user deleted from auth.users)
  - Settings object cannot be loaded (configuration error)

test_file_mapping:
  - 18-5-escalation-nudge-notifications-UNIT-001 to UNIT-005: apps/api/tests/services/notifications/test_escalation_cards.py
  - 18-5-escalation-nudge-notifications-UNIT-006 to UNIT-009: apps/api/tests/services/notifications/test_escalation_cards.py
  - 18-5-escalation-nudge-notifications-UNIT-010 to UNIT-011: apps/api/tests/services/notifications/test_escalation_cards.py (or config test file)
  - 18-5-escalation-nudge-notifications-UNIT-012 to UNIT-018: apps/api/tests/services/notifications/test_escalation.py
  - 18-5-escalation-nudge-notifications-INT-001 to INT-023: apps/api/tests/services/notifications/test_escalation.py

TEST SPEC END

---
