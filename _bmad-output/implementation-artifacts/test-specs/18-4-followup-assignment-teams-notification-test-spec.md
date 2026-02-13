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
