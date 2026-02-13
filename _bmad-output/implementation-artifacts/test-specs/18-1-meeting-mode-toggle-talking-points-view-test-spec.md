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
