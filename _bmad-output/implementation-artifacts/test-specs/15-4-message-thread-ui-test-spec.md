TEST SPEC START
story_id: 15-4-message-thread-ui
generated: 2026-02-11

test_specifications:

## AC1: Chronological message thread display — Given a follow-up has messages (outbound notification + inbound response), When the manager views the follow-up detail, Then a chronological message thread is displayed showing assignment notification, response, and status updates with sender and timestamp info.

### 15-4-message-thread-ui-UNIT-001: MessageThread renders outbound assignment message right-aligned
- Priority: P0
- Type: unit
- Given: A MessageThread component receives a messages array containing one outbound message with direction="outbound", message_type="assignment", sender_email="manager@plant.com", subject="Follow-up: Replace bearing", body="Please inspect the bearing on Pump-101", sent_at="2026-02-10T08:00:00Z"
- When: The component renders
- Then: The outbound message is displayed right-aligned with muted background (bg-industrial-100), showing "Sent to {assignee}" label, the timestamp, the message body, and a blue "Assignment" badge
- Data: Single outbound message fixture with all fields populated

### 15-4-message-thread-ui-UNIT-002: MessageThread renders inbound response message left-aligned
- Priority: P0
- Type: unit
- Given: A MessageThread component receives a messages array containing one inbound message with direction="inbound", message_type="response", sender_email="assignee@plant.com", body="Bearing replaced and tested", sent_at="2026-02-10T14:30:00Z"
- When: The component renders
- Then: The inbound message is displayed left-aligned with card background, showing "{assignee} replied at {time}" label, the response body, and a green "Response" badge
- Data: Single inbound message fixture

### 15-4-message-thread-ui-UNIT-003: MessageThread renders full chronological thread with multiple message types
- Priority: P0
- Type: unit
- Given: A MessageThread component receives messages containing: (1) outbound assignment at 08:00, (2) status_update "in_progress" at 10:00, (3) inbound response at 14:30
- When: The component renders
- Then: All three messages are displayed in chronological order (top-to-bottom), outbound right-aligned, inbound left-aligned, status update shows "{assignee} marked as in-progress at {time}" with gray "Status Update" badge
- Data: Array of 3 messages with different directions and message_types

### 15-4-message-thread-ui-UNIT-004: MessageThread displays sender name/email and relative timestamps
- Priority: P1
- Type: unit
- Given: A MessageThread component receives messages with sender_email and sent_at timestamps
- When: The component renders
- Then: Each message shows the sender email and a relative timestamp (e.g., "2h ago") for each message
- Data: Messages with known sent_at values relative to test time

### 15-4-message-thread-ui-UNIT-005: MessageThread renders message type badges with correct colors
- Priority: P1
- Type: unit
- Given: A MessageThread component receives messages with message_type values "assignment", "response", "status_update", and "escalation"
- When: The component renders
- Then: Assignment badge is blue, Response badge is green, Status Update badge is gray, Escalation badge has appropriate styling
- Data: Array of 4 messages, one of each message_type

### 15-4-message-thread-ui-UNIT-006: MessageThread has correct accessibility attributes
- Priority: P1
- Type: unit
- Given: A MessageThread component receives messages
- When: The component renders
- Then: The message container has role="log" and appropriate aria-label, individual messages have aria-labels describing sender and time
- Data: Standard messages fixture

### 15-4-message-thread-ui-INT-001: FollowUpDetailDialog renders MessageThread when opened with a follow-up that has messages
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is rendered with open=true and a followUpId, and the useFollowUpMessages hook returns a populated messages array (1 outbound + 1 inbound)
- When: The dialog opens
- Then: The MessageThread component renders inside the dialog showing the chronological message thread below the existing header/metadata section
- Data: Mock useFollowUpMessages returning 2 messages, mock follow-up item with id, action_summary, assignee info

### 15-4-message-thread-ui-INT-002: useFollowUpMessages hook fetches messages from API with auth token
- Priority: P0
- Type: integration
- Given: A Supabase session exists with a valid access token, and useFollowUpMessages is called with followUpId="fu-123"
- When: The hook initializes and fetches data
- Then: A GET request is made to /api/v1/followups/fu-123/messages with Authorization: Bearer {token}, and the hook returns the typed messages array, loading transitions from true to false
- Data: Mock fetch response matching FollowUpMessageListResponse schema

## AC2: Unread indicator on follow-up entry — Given a response has come in that the manager hasn't viewed, When the My Assignments panel shows, Then an unread indicator (badge/dot) appears on the follow-up entry.

### 15-4-message-thread-ui-UNIT-007: FollowUpEntry shows blue dot when has_unread is true
- Priority: P0
- Type: unit
- Given: A FollowUpEntry component receives a follow-up item with has_unread=true
- When: The component renders
- Then: A blue dot indicator (data-testid="new-update-indicator") is visible on the entry, positioned to draw attention to unread content
- Data: Follow-up fixture with has_unread: true

### 15-4-message-thread-ui-UNIT-008: FollowUpEntry hides blue dot when has_unread is false
- Priority: P0
- Type: unit
- Given: A FollowUpEntry component receives a follow-up item with has_unread=false
- When: The component renders
- Then: No blue dot indicator is present on the entry
- Data: Follow-up fixture with has_unread: false

### 15-4-message-thread-ui-UNIT-009: FollowUpEntry hides blue dot when has_unread is undefined (backward compat)
- Priority: P1
- Type: unit
- Given: A FollowUpEntry component receives a follow-up item without the has_unread property (undefined)
- When: The component renders
- Then: Falls back to existing localStorage-based unread detection behavior
- Data: Follow-up fixture without has_unread field

### 15-4-message-thread-ui-INT-003: FollowUpDetailDialog calls markViewed on open to clear unread status
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is rendered with open=true and a followUpId, and useFollowUpMessages returns has_unread=true
- When: The dialog open prop transitions from false to true
- Then: The markViewed() function from useFollowUpMessages is called, which sends PATCH /api/v1/followups/{id}/viewed
- Data: Mock useFollowUpMessages with markViewed spy function

### 15-4-message-thread-ui-INT-004: PATCH /api/v1/followups/{id}/viewed updates last_viewed_at server-side
- Priority: P0
- Type: integration
- Given: An authenticated manager user, a follow-up "fu-abc" assigned to or by the user, last_viewed_at is null
- When: PATCH /api/v1/followups/fu-abc/viewed is called with valid Bearer token
- Then: Response 200 with { "success": true, "last_viewed_at": "<current ISO datetime>" }, and the action_followups row is updated with last_viewed_at = NOW()
- Data: Mocked Supabase update chain returning updated record

### 15-4-message-thread-ui-INT-005: GET /api/v1/actions/followups returns has_unread per follow-up item
- Priority: P1
- Type: integration
- Given: An authenticated user with two follow-ups: one with inbound messages newer than last_viewed_at, one with no inbound messages
- When: GET /api/v1/actions/followups is called
- Then: The response includes has_unread=true for the first follow-up and has_unread=false for the second
- Data: Mocked Supabase query returning follow-ups with computed has_unread flags

### 15-4-message-thread-ui-INT-006: useMyFollowUps hook passes has_unread from API to FollowUpEntry
- Priority: P1
- Type: integration
- Given: The useMyFollowUps hook fetches follow-ups from the API, and the API response includes has_unread fields
- When: The hook returns data to the consuming component
- Then: Each FollowUpItem in the returned array includes the has_unread boolean field
- Data: Mock API response with has_unread values

## AC3: Empty state when no responses — Given a follow-up has no responses yet, When the thread view is opened, Then only the outbound notification is shown and a note appears: "Awaiting response from {assignee_name}".

### 15-4-message-thread-ui-UNIT-010: MessageThread shows empty state with "Awaiting response" when no inbound messages
- Priority: P0
- Type: unit
- Given: A MessageThread component receives messages containing only one outbound assignment message and assignee_name="John Smith"
- When: The component renders
- Then: The outbound message is displayed, AND below it a centered empty state shows "Awaiting response from John Smith" with a Clock icon
- Data: Single outbound message, assignee_name="John Smith"

### 15-4-message-thread-ui-UNIT-011: MessageThread does NOT show "Awaiting response" when inbound messages exist
- Priority: P1
- Type: unit
- Given: A MessageThread component receives messages containing one outbound and one inbound message
- When: The component renders
- Then: The "Awaiting response" empty state text is NOT displayed
- Data: Array with outbound + inbound messages

### 15-4-message-thread-ui-UNIT-012: MessageThread shows loading skeleton state
- Priority: P1
- Type: unit
- Given: A MessageThread component receives loading=true
- When: The component renders
- Then: A loading skeleton is displayed instead of message content or empty state
- Data: loading=true, empty messages array

### 15-4-message-thread-ui-INT-007: GET /api/v1/followups/{id}/messages returns assignee_name in response for empty state label
- Priority: P1
- Type: integration
- Given: An authenticated user, follow-up "fu-xyz" exists with assignee_name="Jane Doe" and only one outbound message
- When: GET /api/v1/followups/fu-xyz/messages is called
- Then: Response includes assignee_name="Jane Doe" in the wrapper and the messages array contains only the outbound message
- Data: Mocked Supabase query returning follow-up with joined assignee info, one outbound message

## AC4: Messages API returns chronological messages with correct fields — Given the messages API endpoint is called, When a valid follow-up ID is provided, Then messages are returned in chronological order with sender info, direction, message type, subject, body, and timestamps.

### 15-4-message-thread-ui-INT-008: GET /messages returns messages in chronological order (sent_at ascending)
- Priority: P0
- Type: integration
- Given: An authenticated manager user, follow-up "fu-123" has 3 messages at sent_at 08:00, 10:00, 14:30
- When: GET /api/v1/followups/fu-123/messages is called with valid auth
- Then: Response 200 with messages array sorted by sent_at ascending, message at index 0 has the earliest timestamp, message at index 2 has the latest
- Data: Mocked Supabase query returning 3 messages with .order("sent_at", desc=False)

### 15-4-message-thread-ui-INT-009: GET /messages returns all required fields per message
- Priority: P0
- Type: integration
- Given: An authenticated user, follow-up "fu-123" has messages in the followup_messages table
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Each message in the response contains: id (UUID), direction ("outbound"|"inbound"), message_type ("assignment"|"response"|"escalation"|"status_update"), sender_email (string), subject (string), body (string), sent_at (ISO datetime)
- Data: Mocked Supabase returning message records with all columns

### 15-4-message-thread-ui-INT-010: GET /messages returns follow-up context in wrapper
- Priority: P0
- Type: integration
- Given: An authenticated user, follow-up "fu-123" exists with action_summary="Replace bearing", assignee_name="John", assignee_email="john@plant.com", status="in_progress"
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response includes wrapper fields: followup_id, action_summary, assignee_name, assignee_email, status, has_unread (boolean), last_viewed_at (nullable datetime)
- Data: Mocked Supabase query with joined action_followups data

### 15-4-message-thread-ui-INT-011: GET /messages computes has_unread correctly (inbound newer than last_viewed_at)
- Priority: P0
- Type: integration
- Given: An authenticated user, follow-up "fu-123" has last_viewed_at="2026-02-10T12:00:00Z" and an inbound message with sent_at="2026-02-10T14:30:00Z"
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response has has_unread=true because inbound message sent_at > last_viewed_at
- Data: Mocked follow-up with last_viewed_at, mocked messages with inbound sent_at after it

### 15-4-message-thread-ui-INT-012: GET /messages returns has_unread=false when no inbound messages exist
- Priority: P1
- Type: integration
- Given: An authenticated user, follow-up "fu-123" has only outbound messages, no inbound
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response has has_unread=false
- Data: Mocked messages with only outbound direction

### 15-4-message-thread-ui-INT-013: GET /messages returns has_unread=true when last_viewed_at is null and inbound exists
- Priority: P1
- Type: integration
- Given: An authenticated user, follow-up "fu-123" has last_viewed_at=null and an inbound message exists
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response has has_unread=true (null treated as epoch via COALESCE)
- Data: Mocked follow-up with last_viewed_at=None, one inbound message

### 15-4-message-thread-ui-INT-014: GET /messages requires authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response is 401 Unauthorized
- Data: No auth headers

### 15-4-message-thread-ui-INT-015: PATCH /viewed requires authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: PATCH /api/v1/followups/fu-123/viewed is called
- Then: Response is 401 Unauthorized
- Data: No auth headers

### 15-4-message-thread-ui-INT-016: GET /messages returns 404 for non-existent follow-up ID
- Priority: P1
- Type: integration
- Given: An authenticated user, no follow-up with id="fu-nonexistent" exists in the database
- When: GET /api/v1/followups/fu-nonexistent/messages is called
- Then: Response is 404 Not Found
- Data: Mocked Supabase returning empty result for action_followups query

### 15-4-message-thread-ui-INT-017: GET /messages returns empty messages array for follow-up with no messages
- Priority: P1
- Type: integration
- Given: An authenticated user who is the assigner of follow-up "fu-123", the followup_messages table has no records for this follow-up ID
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response 200 with messages=[] (empty array), wrapper still includes followup context (assignee_name, status, etc.)
- Data: Mocked Supabase returning follow-up record but empty messages

## AC5: RLS enforcement for unauthorized access — Given the user does not have access to the follow-up (neither assigner nor assignee), When the messages endpoint is called, Then an empty result or 403 is returned (RLS enforced).

### 15-4-message-thread-ui-INT-018: GET /messages returns 404 when user is neither assigner nor assignee
- Priority: P0
- Type: integration
- Given: An authenticated user with id="user-outsider", follow-up "fu-123" has assigned_by="user-manager" and assigned_to="user-technician" (neither matches the current user)
- When: GET /api/v1/followups/fu-123/messages is called with the outsider's Bearer token
- Then: Response is 404 (application-level defense-in-depth, follow-up treated as not found)
- Data: Mocked JWT with sub="user-outsider", mocked follow-up with different assigned_by and assigned_to

### 15-4-message-thread-ui-INT-019: GET /messages succeeds when user is the assigner
- Priority: P0
- Type: integration
- Given: An authenticated user with id="user-manager", follow-up "fu-123" has assigned_by="user-manager"
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response is 200 with the messages array
- Data: Mocked JWT with sub="user-manager", mocked follow-up with matching assigned_by

### 15-4-message-thread-ui-INT-020: GET /messages succeeds when user is the assignee
- Priority: P0
- Type: integration
- Given: An authenticated user with id="user-technician", follow-up "fu-123" has assigned_to="user-technician"
- When: GET /api/v1/followups/fu-123/messages is called
- Then: Response is 200 with the messages array
- Data: Mocked JWT with sub="user-technician", mocked follow-up with matching assigned_to

### 15-4-message-thread-ui-INT-021: PATCH /viewed returns 404 when user is neither assigner nor assignee
- Priority: P0
- Type: integration
- Given: An authenticated user with id="user-outsider", follow-up "fu-123" has assigned_by="user-manager" and assigned_to="user-technician"
- When: PATCH /api/v1/followups/fu-123/viewed is called with the outsider's Bearer token
- Then: Response is 404
- Data: Mocked JWT with sub="user-outsider", mocked follow-up with different assigned_by and assigned_to

edge_cases:
  - Follow-up with many messages (50+): Verify ScrollArea is scrollable and performance is acceptable
  - Message body with very long text (1000+ chars): Ensure text wraps properly without breaking layout
  - Message body with special characters, HTML, or markdown: Ensure XSS protection, body is rendered as plain text
  - Concurrent PATCH /viewed and new inbound message arriving: has_unread race condition — acceptable for MVP but worth documenting
  - Follow-up status transitions: Thread should display correctly regardless of status (assigned, in_progress, resolved)
  - Multiple rapid dialog open/close: markViewed should not fire redundant PATCH requests
  - Null/undefined assignee_name: Empty state should gracefully handle missing assignee_name (show email fallback)
  - Network error during message fetch: Hook should expose error state, MessageThread should show error message
  - Session expired during markViewed call: Should not crash, error handled gracefully

error_scenarios:
  - API returns 500 internal server error for GET /messages: useFollowUpMessages hook should set error state, MessageThread should display error UI
  - API returns 500 for PATCH /viewed: markViewed should fail silently or show non-blocking toast, thread display should not be affected
  - Supabase query timeout on large message set: API should return 500, frontend should show error state
  - Invalid UUID format for followup_id path parameter: API should return 422 validation error
  - Expired JWT token when fetching messages: API returns 401, hook surfaces AUTH_ERROR to component
  - Network connectivity lost while thread is open: Refetch should retry gracefully, existing messages should remain visible

test_file_mapping:
  - 15-4-message-thread-ui-UNIT-001 to UNIT-006: apps/web/src/components/action-list/__tests__/MessageThread.test.tsx
  - 15-4-message-thread-ui-UNIT-007 to UNIT-009: apps/web/src/components/action-list/__tests__/FollowUpEntry.test.tsx (modify existing)
  - 15-4-message-thread-ui-UNIT-010 to UNIT-012: apps/web/src/components/action-list/__tests__/MessageThread.test.tsx
  - 15-4-message-thread-ui-INT-001 to INT-003: apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx (modify existing)
  - 15-4-message-thread-ui-INT-002: apps/web/src/hooks/__tests__/useFollowUpMessages.test.ts (new)
  - 15-4-message-thread-ui-INT-004 to INT-005, INT-007 to INT-021: apps/api/app/tests/api/test_followups_messages.py (new)
  - 15-4-message-thread-ui-INT-006: apps/web/src/hooks/__tests__/useMyFollowUps.test.ts (modify existing)

TEST SPEC END
