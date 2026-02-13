TEST SPEC START
story_id: 13-4-assignment-badge-on-action-cards
generated: 2026-02-11

test_specifications:

## AC1: Given an action item has a follow-up assigned, When the action card renders, Then a badge shows on the card with the assignee's name and current status, And the badge is color-coded: blue (assigned), amber (in-progress), green (resolved).

### 13-4-assignment-badge-on-action-cards-UNIT-001: AssignmentBadge renders with blue info variant for "assigned" status
- Priority: P0
- Type: unit
- Given: A FollowUpData object with status "assigned" and assignee_email "john@example.com"
- When: The AssignmentBadge component renders with this follow-up data
- Then: A Badge component renders with the "info" variant (blue color), displays the assignee email "john@example.com" and status label "Assigned"
- Data: `{ id: 'fu-1', action_item_id: 'act-1', assigned_to: 'uuid-1', assignee_email: 'john@example.com', status: 'assigned', note: null, created_at: '2026-01-15T10:00:00Z', updated_at: '2026-01-15T10:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-002: AssignmentBadge renders with amber warning variant for "in_progress" status
- Priority: P0
- Type: unit
- Given: A FollowUpData object with status "in_progress" and assignee_email "jane@example.com"
- When: The AssignmentBadge component renders with this follow-up data
- Then: A Badge component renders with the "warning" variant (amber color), displays the assignee email "jane@example.com" and status label "In Progress"
- Data: `{ id: 'fu-2', action_item_id: 'act-2', assigned_to: 'uuid-2', assignee_email: 'jane@example.com', status: 'in_progress', note: 'Working on it', created_at: '2026-01-15T10:00:00Z', updated_at: '2026-01-15T11:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-003: AssignmentBadge renders with green success variant for "resolved" status
- Priority: P0
- Type: unit
- Given: A FollowUpData object with status "resolved" and assignee_email "bob@example.com"
- When: The AssignmentBadge component renders with this follow-up data
- Then: A Badge component renders with the "success" variant (green color), displays the assignee email "bob@example.com" and status label "Resolved"
- Data: `{ id: 'fu-3', action_item_id: 'act-3', assigned_to: 'uuid-3', assignee_email: 'bob@example.com', status: 'resolved', note: 'Fixed', created_at: '2026-01-15T10:00:00Z', updated_at: '2026-01-15T14:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-004: AssignmentBadge includes correct ARIA label for accessibility
- Priority: P0
- Type: unit
- Given: A FollowUpData object with assignee_email "john@example.com" and status "assigned"
- When: The AssignmentBadge component renders
- Then: The badge element has an aria-label attribute containing "Assigned to john@example.com, status: assigned"
- Data: Same as UNIT-001

### 13-4-assignment-badge-on-action-cards-UNIT-005: AssignmentBadge displays correct format with email and status label
- Priority: P0
- Type: unit
- Given: A FollowUpData object with assignee_email "alice@factory.com" and status "in_progress"
- When: The AssignmentBadge component renders
- Then: The rendered text contains both the assignee email "alice@factory.com" and a status label (e.g., "In Progress"), separated by a delimiter
- Data: `{ assignee_email: 'alice@factory.com', status: 'in_progress', ... }`

### 13-4-assignment-badge-on-action-cards-INT-001: InsightSection renders AssignmentBadge when followUp prop is provided
- Priority: P0
- Type: integration
- Given: An InsightSection component receives a valid followUp prop with status "assigned"
- When: The component renders
- Then: The AssignmentBadge is visible within the InsightSection, positioned between the priority badge row and the recommendation text
- Data: Full InsightSectionProps with followUp of status "assigned"

### 13-4-assignment-badge-on-action-cards-INT-002: InsightEvidenceCard passes followUp to InsightSection correctly
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard receives a followUp prop with status "in_progress" and assignee_email "worker@factory.com"
- When: The card renders
- Then: The AssignmentBadge appears in the InsightSection (left side) of the card showing "worker@factory.com" with amber/warning styling
- Data: Full ActionItem + FollowUpData with status "in_progress"

### 13-4-assignment-badge-on-action-cards-INT-003: InsightSection changes "Assign" button to "Reassign" when followUp exists
- Priority: P1
- Type: integration
- Given: An InsightSection component receives a valid followUp prop (any status)
- When: The component renders
- Then: The action button displays "Reassign" instead of "Assign", and the button still triggers the onAssign callback when clicked
- Data: InsightSectionProps with followUp and onAssign callback

### 13-4-assignment-badge-on-action-cards-UNIT-006: AssignmentBadge handles truncated UUID fallback for missing email
- Priority: P1
- Type: unit
- Given: A FollowUpData object where assignee_email is a truncated UUID format like "abc12345..."
- When: The AssignmentBadge component renders
- Then: The badge displays the truncated UUID as the assignee identifier without error
- Data: `{ assignee_email: 'abc12345...', status: 'assigned', ... }`

## AC2: Given an action item has no follow-up assigned, When the action card renders, Then no assignment badge is shown, And the "Assign Follow-Up" button remains prominent (existing behavior preserved).

### 13-4-assignment-badge-on-action-cards-UNIT-007: AssignmentBadge does not render when followUp prop is undefined
- Priority: P0
- Type: unit
- Given: An InsightSection component receives no followUp prop (undefined)
- When: The component renders
- Then: No AssignmentBadge element is present in the DOM
- Data: InsightSectionProps without followUp

### 13-4-assignment-badge-on-action-cards-UNIT-008: AssignmentBadge does not render when followUp prop is null
- Priority: P0
- Type: unit
- Given: An InsightSection component receives followUp as null
- When: The component renders
- Then: No AssignmentBadge element is present in the DOM
- Data: InsightSectionProps with followUp: null

### 13-4-assignment-badge-on-action-cards-INT-004: "Assign" button remains visible and labeled "Assign" when no follow-up exists
- Priority: P0
- Type: integration
- Given: An InsightSection component with an onAssign callback but no followUp prop
- When: The component renders
- Then: The "Assign" button is visible with the text "Assign" (not "Reassign"), and clicking it invokes the onAssign callback
- Data: InsightSectionProps with onAssign but without followUp

### 13-4-assignment-badge-on-action-cards-INT-005: Card renders identically to pre-story behavior when no follow-up exists
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard component with a standard ActionItem and no followUp prop
- When: The card renders
- Then: The card layout, priority badge, recommendation text, financial impact, evidence section, and "Assign" button all render exactly as before this story's changes
- Data: Standard ActionItem from createMockActionItem factory

### 13-4-assignment-badge-on-action-cards-UNIT-009: useFollowUps returns empty Map for action items without follow-ups
- Priority: P0
- Type: unit
- Given: The action_followups table returns an empty result set for the given reportDate
- When: The useFollowUps hook resolves
- Then: The returned followUps Map is empty (size === 0), isLoading is false, and error is null
- Data: Supabase mock returns `{ data: [], error: null }`

### 13-4-assignment-badge-on-action-cards-INT-006: ActionCardList passes undefined followUp to cards not in the followUps Map
- Priority: P1
- Type: integration
- Given: An ActionCardList receives a followUps Map containing an entry for "act-1" but not for "act-2"
- When: The list renders two action items with ids "act-1" and "act-2"
- Then: InsightEvidenceCard for "act-1" receives the followUp prop, and InsightEvidenceCard for "act-2" receives undefined (no badge shown)
- Data: Two ActionItems, followUps Map with single entry for "act-1"

## AC3: Given multiple follow-ups exist for the same action item (reassigned), When the card renders, Then the most recent active follow-up is shown (determined by created_at DESC, excluding resolved unless no active exists).

### 13-4-assignment-badge-on-action-cards-UNIT-010: useFollowUps selects most recent non-resolved follow-up when multiple exist
- Priority: P0
- Type: unit
- Given: The action_followups table returns 3 follow-ups for the same action_item_id: one "resolved" (oldest), one "assigned" (middle), one "in_progress" (newest)
- When: The useFollowUps hook processes the data
- Then: The returned Map contains a single entry for that action_item_id with the "in_progress" follow-up (most recent active)
- Data: Three follow-ups for "act-1" with created_at timestamps T1 < T2 < T3, statuses ["resolved", "assigned", "in_progress"]

### 13-4-assignment-badge-on-action-cards-UNIT-011: useFollowUps selects most recent resolved follow-up when all are resolved
- Priority: P0
- Type: unit
- Given: The action_followups table returns 2 follow-ups for the same action_item_id, both with status "resolved"
- When: The useFollowUps hook processes the data
- Then: The returned Map contains a single entry for that action_item_id with the most recently created resolved follow-up
- Data: Two follow-ups for "act-1" both with status "resolved", created_at T1 < T2

### 13-4-assignment-badge-on-action-cards-UNIT-012: useFollowUps prefers active over resolved even if resolved is newer
- Priority: P0
- Type: unit
- Given: The action_followups table returns 2 follow-ups for the same action_item_id: one "assigned" (older), one "resolved" (newer)
- When: The useFollowUps hook processes the data
- Then: The returned Map contains the "assigned" follow-up (active is preferred over resolved, regardless of created_at)
- Data: Two follow-ups for "act-1": `{ status: 'assigned', created_at: '2026-01-15T08:00:00Z' }`, `{ status: 'resolved', created_at: '2026-01-15T12:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-013: useFollowUps handles single follow-up per action item correctly
- Priority: P1
- Type: unit
- Given: The action_followups table returns exactly one follow-up for an action_item_id
- When: The useFollowUps hook processes the data
- Then: The returned Map contains that single follow-up, regardless of its status
- Data: Single follow-up for "act-1" with status "assigned"

### 13-4-assignment-badge-on-action-cards-UNIT-014: useFollowUps groups follow-ups correctly across different action items
- Priority: P0
- Type: unit
- Given: The action_followups table returns follow-ups for 3 different action_item_ids, some with multiple follow-ups
- When: The useFollowUps hook processes the data
- Then: The returned Map has exactly 3 entries, each keyed by the correct action_item_id with the most relevant follow-up for that item
- Data: 5 follow-ups total: 2 for "act-1" (one active, one resolved), 2 for "act-2" (both resolved), 1 for "act-3" (assigned)

### 13-4-assignment-badge-on-action-cards-INT-007: Card displays most recent active follow-up badge when reassigned
- Priority: P1
- Type: integration
- Given: An InsightEvidenceCard receives a followUp reflecting the most recent active follow-up (status "in_progress", recent email)
- When: The card renders
- Then: The badge shows the most recent assignee's email and "In Progress" status with amber styling, not the older resolved follow-up
- Data: FollowUpData with status "in_progress" and latest assignee email

## Hook Data Fetching & Integration

### 13-4-assignment-badge-on-action-cards-UNIT-015: useFollowUps fetches follow-ups filtered by reportDate
- Priority: P0
- Type: unit
- Given: A reportDate of "2026-01-15" is provided to useFollowUps
- When: The hook initializes and fetches data
- Then: The Supabase query includes `.eq('report_date', '2026-01-15')` and `.order('created_at', { ascending: false })`
- Data: Mock Supabase client verifying query chain

### 13-4-assignment-badge-on-action-cards-UNIT-016: useFollowUps resolves assigned_to UUIDs to emails via team members API
- Priority: P0
- Type: unit
- Given: Follow-ups contain assigned_to UUID "uuid-abc" and the team members API returns `{ members: [{ user_id: 'uuid-abc', email: 'alice@factory.com' }] }`
- When: The hook processes the data
- Then: The returned FollowUpData has assignee_email set to "alice@factory.com"
- Data: Mock follow-up with assigned_to "uuid-abc", mock fetch response for /api/v1/team/members

### 13-4-assignment-badge-on-action-cards-UNIT-017: useFollowUps falls back to truncated UUID when team member email not found
- Priority: P1
- Type: unit
- Given: Follow-ups contain assigned_to UUID "abcdef12-3456-7890-abcd-ef1234567890" but team members API does not include this user
- When: The hook processes the data
- Then: The returned FollowUpData has assignee_email set to a truncated format like "abcdef12..."
- Data: Mock follow-up with unresolvable UUID, mock team members without matching entry

### 13-4-assignment-badge-on-action-cards-UNIT-018: useFollowUps returns loading state during fetch
- Priority: P1
- Type: unit
- Given: The hook is initialized with a valid reportDate
- When: The Supabase query and team members fetch are in-flight
- Then: The hook returns `{ followUps: empty Map, isLoading: true, error: null }`
- Data: Pending mock promises

### 13-4-assignment-badge-on-action-cards-UNIT-019: useFollowUps handles Supabase query error gracefully
- Priority: P1
- Type: unit
- Given: The Supabase query for action_followups returns an error
- When: The hook processes the error
- Then: The hook returns `{ followUps: empty Map, isLoading: false, error: <error message> }`
- Data: Supabase mock returns `{ data: null, error: { message: 'Permission denied' } }`

### 13-4-assignment-badge-on-action-cards-UNIT-020: useFollowUps handles team members API failure gracefully
- Priority: P1
- Type: unit
- Given: The Supabase query succeeds but the /api/v1/team/members fetch fails (network error or non-200)
- When: The hook processes the data
- Then: The hook still returns follow-ups but with truncated UUID fallbacks for all assignee_email fields (does not fail entirely)
- Data: Successful Supabase mock, failing fetch mock

### 13-4-assignment-badge-on-action-cards-INT-008: InsightEvidenceCardList wires useFollowUps with reportDate from useDailyActions
- Priority: P0
- Type: integration
- Given: useDailyActions returns data with report_date "2026-01-15"
- When: InsightEvidenceCardList renders
- Then: useFollowUps is called with reportDate "2026-01-15", and the returned followUps Map is passed to ActionCardList
- Data: Mock useDailyActions with report_date, mock useFollowUps returning a Map with entries

## Barrel File & Exports

### 13-4-assignment-badge-on-action-cards-UNIT-021: AssignmentBadge is exported from barrel file
- Priority: P2
- Type: unit
- Given: The action-engine barrel file (index.ts) has been updated
- When: Importing AssignmentBadge from '@/components/action-engine'
- Then: The AssignmentBadge component is successfully imported and is a valid React component
- Data: Import verification

### 13-4-assignment-badge-on-action-cards-UNIT-022: FollowUpData type is exported from barrel file
- Priority: P2
- Type: unit
- Given: The action-engine barrel file (index.ts) has been updated
- When: Importing FollowUpData from '@/components/action-engine'
- Then: The FollowUpData type is successfully imported and usable for typing
- Data: Import verification

edge_cases:
  - Action item ID changes after cache rebuild (documented in 13-1 decisions) — follow-up keyed to old ID won't match; badge simply won't render (graceful degradation)
  - RLS policy limits visibility — Plant Manager who is neither assigned_to nor assigned_by will not see the follow-up badge for that action item
  - Team members API returns a user without an email field — fallback to truncated UUID display
  - Follow-up created while page is already loaded — badge won't appear until refetch/page refresh (matches existing staleness behavior)
  - Very long assignee email address — badge should truncate gracefully without breaking card layout
  - Action item is both acknowledged AND has a follow-up — both acknowledged visual state (opacity-60) and assignment badge should coexist
  - reportDate is undefined/null when useDailyActions data hasn't loaded yet — useFollowUps should not fetch and should return empty state

error_scenarios:
  - Supabase query returns permission denied error (RLS policy block) — hook returns error state, no badges rendered, no crash
  - Team members API returns 401 (expired session token) — hook falls back to truncated UUIDs for display names
  - Team members API returns 500 — hook falls back to truncated UUIDs, does not block follow-up display
  - Network timeout on Supabase query — hook returns error state after timeout
  - Supabase returns malformed data (missing required fields) — hook handles gracefully, skips malformed entries
  - Follow-up has assigned_to that is null or empty string — badge should either not render or show a sensible fallback

test_file_mapping:
  - 13-4-assignment-badge-on-action-cards-UNIT-001 to UNIT-006: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-UNIT-007 to UNIT-008: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-UNIT-009 to UNIT-020: apps/web/src/hooks/__tests__/useFollowUps.test.ts
  - 13-4-assignment-badge-on-action-cards-UNIT-021 to UNIT-022: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-001 to INT-003: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-004 to INT-006: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.badge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-007: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.badge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-008: apps/web/src/components/action-engine/__tests__/InsightEvidenceCardList.followups.test.tsx

TEST SPEC END
