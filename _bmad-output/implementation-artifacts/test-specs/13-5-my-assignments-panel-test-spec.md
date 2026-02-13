TEST SPEC START
story_id: 13-5-my-assignments-panel
generated: 2026-02-11

test_specifications:

## AC1: Panel shows follow-ups grouped by status with entry details

Given the manager has created follow-up assignments, When the "My Assignments" panel is visible on the morning report, Then it shows all follow-ups grouped by status (Assigned/blue, In Progress/amber, Resolved/green) And each entry shows: asset name, action summary, assignee name, time since assigned.

### 13-5-my-assignments-panel-INT-001: Backend returns follow-ups filtered by assigned_by=me
- Priority: P0
- Type: integration
- Given: The authenticated manager has created 3 follow-up assignments (1 assigned, 1 in_progress, 1 resolved) in the action_followups table
- When: GET /api/v1/actions/followups?assigned_by=me is called with a valid Bearer token
- Then: The response returns status 200 with all 3 follow-ups where assigned_by matches the current user's ID, and counts_by_status shows {"assigned": 1, "in_progress": 1, "resolved": 1}, and total_count is 3
- Data: 3 follow-up records with assigned_by=current_user_id, varying statuses; at least 1 follow-up assigned_by a different user (should NOT be returned)

### 13-5-my-assignments-panel-INT-002: Backend resolves assigned_to UUIDs to email addresses
- Priority: P0
- Type: integration
- Given: A follow-up exists with assigned_to pointing to a valid user UUID
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: Each follow-up in the response includes assigned_to_email with the resolved email address (e.g., "john@company.com"), not just the UUID
- Data: Follow-up record with assigned_to UUID, corresponding user record with email in auth.users

### 13-5-my-assignments-panel-INT-003: Backend filters by status parameter
- Priority: P0
- Type: integration
- Given: The manager has follow-ups in all 3 statuses (assigned, in_progress, resolved)
- When: GET /api/v1/actions/followups?assigned_by=me&status=active is called
- Then: Only follow-ups with status "assigned" or "in_progress" are returned; resolved follow-ups are excluded; counts_by_status reflects only the returned items
- Data: 3 follow-ups (1 per status)

### 13-5-my-assignments-panel-INT-004: Backend status filter for specific statuses
- Priority: P1
- Type: integration
- Given: The manager has follow-ups in all 3 statuses
- When: GET /api/v1/actions/followups?assigned_by=me&status=assigned is called
- Then: Only follow-ups with status "assigned" are returned
- Data: 3 follow-ups (1 per status)

### 13-5-my-assignments-panel-INT-005: Backend status filter for "all" returns all statuses
- Priority: P1
- Type: integration
- Given: The manager has follow-ups in all 3 statuses
- When: GET /api/v1/actions/followups?assigned_by=me&status=all is called
- Then: All 3 follow-ups are returned regardless of status
- Data: 3 follow-ups (1 per status)

### 13-5-my-assignments-panel-INT-006: Backend requires authentication
- Priority: P0
- Type: integration
- Given: No Bearer token is provided in the request
- When: GET /api/v1/actions/followups is called without Authorization header
- Then: The response returns status 401 Unauthorized
- Data: None

### 13-5-my-assignments-panel-INT-007: Backend response includes all required fields per schema
- Priority: P0
- Type: integration
- Given: A follow-up assignment exists with all fields populated
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: Each follow-up item in the response includes: id, action_item_id, action_summary, asset_name, category, assigned_to, assigned_to_email, assigned_by, note, status, report_date, created_at, updated_at
- Data: 1 fully-populated follow-up record

### 13-5-my-assignments-panel-INT-008: Backend supports pagination with limit and offset
- Priority: P1
- Type: integration
- Given: The manager has 10 follow-up assignments
- When: GET /api/v1/actions/followups?assigned_by=me&limit=3&offset=0 is called
- Then: The response returns exactly 3 follow-ups, total_count reflects the full count (10), and subsequent calls with offset=3 return the next 3 items
- Data: 10 follow-up records

### 13-5-my-assignments-panel-UNIT-001: FollowUpListItem schema includes assigned_to_email
- Priority: P0
- Type: unit
- Given: A FollowUpListItem Pydantic model is instantiated with all required fields including assigned_to_email
- When: The model is serialized to dict/JSON
- Then: The output includes the assigned_to_email field alongside all FollowUpResponse fields
- Data: Valid FollowUpListItem field values

### 13-5-my-assignments-panel-UNIT-002: FollowUpListResponse schema validates counts_by_status
- Priority: P1
- Type: unit
- Given: A FollowUpListResponse is constructed with followups list, total_count, and counts_by_status dict
- When: The model is validated
- Then: The schema accepts the structure with proper types; counts_by_status maps status strings to integers
- Data: Sample response with 2 assigned, 1 in_progress, 0 resolved

### 13-5-my-assignments-panel-UNIT-003: useMyFollowUps hook fetches and groups follow-ups on mount
- Priority: P0
- Type: unit
- Given: The Supabase session is authenticated and the API returns 3 follow-ups (1 assigned, 1 in_progress, 1 resolved)
- When: The useMyFollowUps hook is rendered
- Then: isLoading is initially true, then becomes false; grouped.assigned contains 1 item, grouped.in_progress contains 1 item, grouped.resolved contains 1 item; totalCount is 3; hasFollowUps is true
- Data: Mock API response with 3 follow-ups in different statuses

### 13-5-my-assignments-panel-UNIT-004: useMyFollowUps hook returns correct hasFollowUps=false when no follow-ups
- Priority: P0
- Type: unit
- Given: The Supabase session is authenticated and the API returns an empty followups array
- When: The useMyFollowUps hook is rendered
- Then: hasFollowUps is false, totalCount is 0, grouped.assigned/in_progress/resolved are all empty arrays
- Data: Mock API response with empty followups, total_count: 0

### 13-5-my-assignments-panel-UNIT-005: MyAssignmentsPanel renders status groups with correct color-coded badges
- Priority: P0
- Type: unit
- Given: The useMyFollowUps hook returns grouped follow-ups (2 assigned, 1 in_progress, 1 resolved)
- When: The MyAssignmentsPanel component renders
- Then: Three status group sections are visible; the "Assigned" section has a blue/info badge variant; the "In Progress" section has an amber/warning badge variant; the "Resolved" section has a green/success badge variant
- Data: 4 mock follow-up items across 3 status groups

### 13-5-my-assignments-panel-UNIT-006: MyAssignmentsPanel renders count badge in header
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns 5 total follow-ups
- When: The MyAssignmentsPanel component renders
- Then: The header shows "My Assignments" with a count badge displaying "5"
- Data: 5 mock follow-up items

### 13-5-my-assignments-panel-UNIT-007: FollowUpEntry renders asset name, action summary, assignee, and relative time
- Priority: P0
- Type: unit
- Given: A follow-up entry with asset_name="Grinder 5", action_summary="Investigate pressure anomaly on main valve", assigned_to_email="john@company.com", created_at=2 hours ago
- When: The FollowUpEntry component renders
- Then: The asset name "Grinder 5" is displayed; the action summary is displayed (possibly truncated); "john@company.com" is displayed as the assignee; "2h ago" is displayed as the relative time
- Data: Single FollowUpItem with all fields populated

### 13-5-my-assignments-panel-UNIT-008: FollowUpEntry truncates long action summaries
- Priority: P2
- Type: unit
- Given: A follow-up entry with action_summary exceeding 80+ characters
- When: The FollowUpEntry component renders
- Then: The action summary is truncated with ellipsis to fit the display area
- Data: Follow-up with a long action_summary string

### 13-5-my-assignments-panel-UNIT-009: formatRelativeTime utility returns correct relative times
- Priority: P1
- Type: unit
- Given: Various ISO timestamp strings representing different time differences
- When: formatRelativeTime is called with each timestamp
- Then: Returns "0m ago" for current time, "30m ago" for 30 minutes ago, "2h ago" for 2 hours ago, "1d ago" for 24 hours ago, "7d ago" for 7 days ago
- Data: Timestamps at 0min, 30min, 2hrs, 24hrs, 7days before now

### 13-5-my-assignments-panel-UNIT-010: MyAssignmentsPanel default expanded when follow-ups exist
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns hasFollowUps=true with some follow-ups
- When: The MyAssignmentsPanel component renders initially
- Then: The panel content (follow-up entries) is visible/expanded, not collapsed
- Data: At least 1 mock follow-up item

### 13-5-my-assignments-panel-UNIT-011: MyAssignmentsPanel default collapsed when no follow-ups
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns hasFollowUps=false
- When: The MyAssignmentsPanel component renders initially
- Then: The panel content is collapsed (only header visible with empty state message)
- Data: Empty follow-ups array

### 13-5-my-assignments-panel-UNIT-012: MyAssignmentsPanel expand/collapse toggle works
- Priority: P1
- Type: unit
- Given: The MyAssignmentsPanel is rendered with follow-ups (expanded by default)
- When: The user clicks the expand/collapse chevron button
- Then: The panel content collapses and is no longer visible; clicking again re-expands it
- Data: At least 1 mock follow-up item

### 13-5-my-assignments-panel-UNIT-013: MyAssignmentsPanel renders loading skeleton state
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns isLoading=true
- When: The MyAssignmentsPanel component renders
- Then: A loading skeleton/placeholder UI is displayed instead of follow-up entries
- Data: Hook in loading state

### 13-5-my-assignments-panel-UNIT-014: MyAssignmentsPanel renders error state with retry button
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns an error (e.g., network failure)
- When: The MyAssignmentsPanel component renders
- Then: An error message is displayed with a "Retry" button; clicking the retry button calls the refetch function
- Data: Hook in error state with error message

### 13-5-my-assignments-panel-UNIT-015: MyAssignmentsPanel hides empty status groups
- Priority: P2
- Type: unit
- Given: The useMyFollowUps hook returns follow-ups with only "assigned" status (no in_progress or resolved)
- When: The MyAssignmentsPanel component renders
- Then: Only the "Assigned" status group is rendered; empty groups for "In Progress" and "Resolved" are not shown (or shown collapsed)
- Data: 2 follow-ups all with status "assigned"

### 13-5-my-assignments-panel-E2E-001: Panel renders in correct position on morning report page
- Priority: P0
- Type: e2e
- Given: The manager is logged in and navigates to the morning report page, and has at least 1 follow-up assignment
- When: The morning report page fully loads
- Then: The MyAssignmentsPanel is positioned between MorningSummarySection and the action items section (WorkcenterScorecard/InsightEvidenceCardList)
- Data: At least 1 follow-up in the database for the current user

## AC2: Status group movement and "New update" indicator on refresh

Given a follow-up was recently updated by the assignee, When the panel refreshes, Then the follow-up moves to its new status group And a "New update" indicator appears if the manager hasn't viewed the update yet.

### 13-5-my-assignments-panel-UNIT-016: Follow-up moves to new status group after refetch
- Priority: P0
- Type: unit
- Given: A follow-up initially has status "assigned" and the hook has fetched data; the follow-up's status is then updated to "in_progress" on the server
- When: The refetch() function is called on useMyFollowUps
- Then: The follow-up moves from grouped.assigned to grouped.in_progress; grouped.assigned count decreases by 1; grouped.in_progress count increases by 1
- Data: Initial API response with 1 assigned follow-up; second API response with same follow-up now in_progress

### 13-5-my-assignments-panel-UNIT-017: "New update" dot indicator shows when updated_at > lastViewedTimestamp
- Priority: P0
- Type: unit
- Given: A follow-up has updated_at="2026-02-11T10:30:00Z" and localStorage key "followup-viewed-{id}" has value "2026-02-11T08:00:00Z" (earlier than updated_at)
- When: The FollowUpEntry component renders for this follow-up
- Then: A "New update" visual indicator (blue dot or similar) is visible on the entry
- Data: Follow-up with updated_at later than the localStorage timestamp

### 13-5-my-assignments-panel-UNIT-018: "New update" indicator does NOT show when already viewed
- Priority: P0
- Type: unit
- Given: A follow-up has updated_at="2026-02-11T10:30:00Z" and localStorage key "followup-viewed-{id}" has value "2026-02-11T11:00:00Z" (later than updated_at)
- When: The FollowUpEntry component renders for this follow-up
- Then: No "New update" indicator is visible on the entry
- Data: Follow-up with updated_at earlier than the localStorage timestamp

### 13-5-my-assignments-panel-UNIT-019: "New update" indicator shows when no localStorage entry exists
- Priority: P1
- Type: unit
- Given: A follow-up exists but no localStorage key "followup-viewed-{id}" has been set (first time viewing)
- When: The FollowUpEntry component renders for this follow-up
- Then: A "New update" indicator is visible (since the manager has never viewed it, any update should be flagged)
- Data: Follow-up without corresponding localStorage key

### 13-5-my-assignments-panel-UNIT-020: "New update" indicator clears when detail dialog is opened
- Priority: P0
- Type: unit
- Given: A follow-up has a "New update" indicator visible (updated_at > lastViewedTimestamp)
- When: The user clicks on the follow-up entry and the detail dialog opens
- Then: localStorage key "followup-viewed-{id}" is updated to the current timestamp; when the dialog closes and the entry re-renders, the "New update" indicator is no longer visible
- Data: Follow-up with updated_at later than localStorage value

### 13-5-my-assignments-panel-UNIT-021: useMyFollowUps refetch() triggers new API call
- Priority: P1
- Type: unit
- Given: The hook has completed initial fetch successfully
- When: The refetch() function is called
- Then: A new API call is made to GET /api/v1/actions/followups; the loading state may briefly be true; updated data is returned
- Data: Mock fetch that can be called multiple times with different responses

### 13-5-my-assignments-panel-UNIT-022: Backend returns updated_at reflecting latest status change
- Priority: P1
- Type: integration
- Given: A follow-up was created at T1 with status "assigned" and later updated to "in_progress" at T2
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: The follow-up's updated_at field reflects T2 (the time of the status change), not T1
- Data: Follow-up with updated_at > created_at

## AC3: Click follow-up entry opens detail view with full assignment context

Given the manager clicks on a follow-up entry, When the detail view opens, Then it shows the full assignment context: original action item, assigned note, assignee's status updates with timestamps.

### 13-5-my-assignments-panel-UNIT-023: FollowUpEntry click triggers detail dialog open
- Priority: P0
- Type: unit
- Given: A FollowUpEntry component is rendered with a follow-up item
- When: The user clicks on the entry
- Then: The onSelect callback is called with the follow-up's data (or ID), triggering the FollowUpDetailDialog to open
- Data: Single follow-up item

### 13-5-my-assignments-panel-UNIT-024: FollowUpDetailDialog renders original action item context
- Priority: P0
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up that has action_summary="Investigate pressure anomaly", category="safety", asset_name="Grinder 5"
- When: The dialog renders
- Then: The action summary text is displayed; the category is shown (with PriorityBadge if applicable); the asset name is displayed
- Data: Follow-up with action_summary, category, asset_name

### 13-5-my-assignments-panel-UNIT-025: FollowUpDetailDialog renders manager's assignment note
- Priority: P0
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up that has note="Please check by EOD and report back"
- When: The dialog renders
- Then: The manager's assignment note "Please check by EOD and report back" is visible in the dialog
- Data: Follow-up with a non-null note field

### 13-5-my-assignments-panel-UNIT-026: FollowUpDetailDialog renders current status badge
- Priority: P0
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up with status="in_progress"
- When: The dialog renders
- Then: A status badge is displayed showing "In Progress" with the amber/warning color variant
- Data: Follow-up with status "in_progress"

### 13-5-my-assignments-panel-UNIT-027: FollowUpDetailDialog renders timestamps for creation and last update
- Priority: P1
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up that has created_at="2026-02-09T08:30:00Z" and updated_at="2026-02-10T14:00:00Z"
- When: The dialog renders
- Then: Both timestamps are displayed in the timeline/detail section, showing when the assignment was created and when it was last updated
- Data: Follow-up with distinct created_at and updated_at values

### 13-5-my-assignments-panel-UNIT-028: FollowUpDetailDialog handles follow-up with no note gracefully
- Priority: P1
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up where note=null
- When: The dialog renders
- Then: The note section either shows a placeholder (e.g., "No note provided") or is omitted entirely; no error is thrown
- Data: Follow-up with note=null

### 13-5-my-assignments-panel-UNIT-029: FollowUpDetailDialog renders assignee email
- Priority: P1
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up with assigned_to_email="jane@company.com"
- When: The dialog renders
- Then: The assignee's email "jane@company.com" is displayed in the dialog
- Data: Follow-up with assigned_to_email

### 13-5-my-assignments-panel-UNIT-030: FollowUpDetailDialog opens and closes correctly
- Priority: P1
- Type: unit
- Given: The MyAssignmentsPanel is rendered with follow-ups
- When: The user clicks a follow-up entry to open the detail dialog, then clicks the close button or outside the dialog
- Then: The dialog opens with the correct follow-up data, and closes cleanly when dismissed, returning focus to the panel
- Data: At least 1 follow-up item

### 13-5-my-assignments-panel-UNIT-031: FollowUpDetailDialog updates localStorage on open to clear "New update"
- Priority: P0
- Type: unit
- Given: A follow-up has a "New update" indicator (updated_at > localStorage value)
- When: The FollowUpDetailDialog is opened for this follow-up
- Then: localStorage key "followup-viewed-{id}" is set to the current timestamp (Date.now()), marking the update as viewed
- Data: Follow-up with updated_at > existing localStorage timestamp

## AC4: Empty state when no open follow-ups

Given the manager has no open follow-ups, When the panel renders, Then it shows an empty state: "No open follow-ups. Assign actions from the report below."

### 13-5-my-assignments-panel-UNIT-032: Empty state renders exact message text
- Priority: P0
- Type: unit
- Given: The useMyFollowUps hook returns hasFollowUps=false with an empty followups array
- When: The MyAssignmentsPanel component renders
- Then: The text "No open follow-ups. Assign actions from the report below." is displayed verbatim
- Data: Empty API response (followups: [], total_count: 0)

### 13-5-my-assignments-panel-UNIT-033: Empty state renders when API returns zero follow-ups
- Priority: P0
- Type: unit
- Given: The API returns a valid response with followups=[], total_count=0, counts_by_status={assigned: 0, in_progress: 0, resolved: 0}
- When: The useMyFollowUps hook processes the response and MyAssignmentsPanel renders
- Then: The empty state is shown; no status group headers are rendered; hasFollowUps is false
- Data: Empty API response

### 13-5-my-assignments-panel-INT-009: Backend returns empty list for manager with no follow-ups
- Priority: P0
- Type: integration
- Given: The authenticated manager has not created any follow-up assignments
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: The response returns status 200 with followups=[], total_count=0, counts_by_status={"assigned": 0, "in_progress": 0, "resolved": 0}
- Data: No follow-up records with assigned_by matching current user

### 13-5-my-assignments-panel-E2E-002: Empty state displays on morning report when manager has no assignments
- Priority: P1
- Type: e2e
- Given: The manager is logged in and has no follow-up assignments in the database
- When: The morning report page loads
- Then: The MyAssignmentsPanel shows the empty state message "No open follow-ups. Assign actions from the report below."
- Data: No follow-up records for the current user

edge_cases:
  - Follow-up with null/missing asset_name: FollowUpEntry should handle gracefully (display fallback or omit asset field)
  - Follow-up with null/missing category: FollowUpDetailDialog should not crash when category is null
  - Very long assignee email address: FollowUpEntry should truncate or wrap without breaking layout
  - Manager has follow-ups only in one status (e.g., all "assigned"): Only one status group should render; others should be hidden or empty
  - Rapid refetch calls (double-click refresh): useMyFollowUps should debounce or handle concurrent requests without race conditions
  - localStorage unavailable (private browsing): "New update" indicator logic should handle gracefully without throwing errors
  - Follow-up with created_at very close to now (less than 1 minute): formatRelativeTime should return "0m ago" or similar, not negative values
  - Timestamps in different timezones: formatRelativeTime should correctly handle ISO strings with timezone offsets
  - Panel with large number of follow-ups (50+): ScrollArea should be used; rendering performance should be acceptable
  - Session expiry during panel interaction: useMyFollowUps should handle auth error gracefully and show error state

error_scenarios:
  - Network failure during follow-up fetch: useMyFollowUps returns error state; MyAssignmentsPanel shows error UI with retry button
  - Expired/invalid Supabase session: Hook detects auth error and surfaces user-friendly "AUTH_ERROR" message
  - API returns 500 server error: Hook detects server error and surfaces "SERVER_ERROR" message with retry
  - API returns malformed JSON: Hook should catch parse error and set error state
  - Backend Supabase service-role client fails to connect: GET /followups returns 500; frontend handles gracefully
  - Backend fails to resolve assigned_to email (user deleted): assigned_to_email should be null or "Unknown"; entry still renders

test_file_mapping:
  - 13-5-my-assignments-panel-INT-001 to INT-009: apps/api/tests/test_followups_list.py
  - 13-5-my-assignments-panel-UNIT-001 to UNIT-002: apps/api/tests/test_followups_list.py (schema validation section)
  - 13-5-my-assignments-panel-UNIT-003 to UNIT-004, UNIT-016, UNIT-021: apps/web/src/hooks/__tests__/useMyFollowUps.test.ts
  - 13-5-my-assignments-panel-UNIT-005 to UNIT-015, UNIT-032, UNIT-033: apps/web/src/components/action-list/__tests__/MyAssignmentsPanel.test.tsx
  - 13-5-my-assignments-panel-UNIT-007 to UNIT-009, UNIT-017 to UNIT-020: apps/web/src/components/action-list/__tests__/FollowUpEntry.test.tsx
  - 13-5-my-assignments-panel-UNIT-023 to UNIT-031: apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx
  - 13-5-my-assignments-panel-E2E-001 to E2E-002: apps/web/src/__tests__/my-assignments-panel.e2e.test.tsx (or integration-level test)

TEST SPEC END
