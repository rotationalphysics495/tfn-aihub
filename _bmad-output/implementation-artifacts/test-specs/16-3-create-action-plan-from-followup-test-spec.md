TEST SPEC START
story_id: 16-3-create-action-plan-from-followup
generated: 2026-02-12

test_specifications:

## AC1: Pre-populated Action Plan Form from Follow-Up Response

Given a follow-up has a response from the assignee with investigation findings, When the manager clicks "Create Action Plan" on the follow-up detail, Then an action plan creation form opens pre-populated with: asset_id from the original action item (looked up from asset_name in action_followups), description from the action item summary + assignee's response, root_cause from the assignee's response text, source_followup_id linking back to the follow-up, and the manager can edit any pre-filled field before saving.

### 16-3-create-action-plan-from-followup-INT-001: ActionPlanForm dialog renders with pre-filled data from follow-up context
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is open for a follow-up with status='in_progress', and the follow-up has an inbound response message with body "Root cause is worn bearing on pump shaft", and the follow-up has asset_name='Grinder 5', action_summary='Investigate pressure anomaly on main valve', category='safety'
- When: The manager clicks the "Create Action Plan" button
- Then: The ActionPlanForm dialog opens with title pre-filled as "Action Plan: Investigate pressure anomaly on main valve" (truncated to 80 chars), description containing the action_summary text, root_cause pre-filled with the assignee's response body "Root cause is worn bearing on pump shaft", category set to "corrective" (mapped from safety), priority set to "high" (mapped from safety), and source_followup_id set to the follow-up's id
- Data: MockFollowUpItem with status='in_progress', asset_name='Grinder 5', category='safety', action_summary='Investigate pressure anomaly on main valve'; mock inbound message with body text; mock Supabase assets query returning {id: 'asset-uuid-123'} for name='Grinder 5'

### 16-3-create-action-plan-from-followup-UNIT-001: ActionPlanForm renders all required form fields
- Priority: P0
- Type: unit
- Given: An ActionPlanForm component is rendered with a prefill prop containing follow-up context data
- When: The dialog renders
- Then: The form displays fields for: title (Input, editable), description (Textarea, editable), category (Select with options: corrective/preventive/improvement), root_cause (Textarea, editable), corrective_action (Textarea, empty), preventive_action (Textarea, empty), priority (Select with options: low/medium/high/critical), due_date (date input, empty), and a read-only asset name display showing "Grinder 5"
- Data: prefill prop with actionSummary='Investigate anomaly', assetName='Grinder 5', responseText='Worn bearing', category='safety', followUpId='fu-123'

### 16-3-create-action-plan-from-followup-UNIT-002: ActionPlanForm pre-fills title truncated to 80 characters
- Priority: P1
- Type: unit
- Given: An ActionPlanForm is rendered with a prefill containing a very long action_summary exceeding 80 characters
- When: The form renders
- Then: The title field value starts with "Action Plan: " followed by the action_summary text, truncated so the total length does not exceed approximately 80 characters
- Data: prefill with actionSummary='Investigate the root cause of the intermittent pressure fluctuations observed on the main hydraulic valve during the morning shift' (130+ chars)

### 16-3-create-action-plan-from-followup-UNIT-003: ActionPlanForm maps follow-up category to action plan category correctly
- Priority: P0
- Type: unit
- Given: ActionPlanForm is rendered with different follow-up categories
- When: The form renders with category='safety', then 'oee', then 'financial'
- Then: The category select is pre-filled as 'corrective' for safety, 'improvement' for oee, 'corrective' for financial
- Data: Three render scenarios with different category values in prefill

### 16-3-create-action-plan-from-followup-UNIT-004: ActionPlanForm maps follow-up category to priority correctly
- Priority: P0
- Type: unit
- Given: ActionPlanForm is rendered with different follow-up categories
- When: The form renders with category='safety', then 'oee', then 'financial'
- Then: The priority select is pre-filled as 'high' for safety, 'medium' for oee, 'medium' for financial
- Data: Three render scenarios with different category values in prefill

### 16-3-create-action-plan-from-followup-UNIT-005: ActionPlanForm resolves asset_id from asset_name via Supabase lookup
- Priority: P0
- Type: unit
- Given: An ActionPlanForm is rendered with prefill containing assetName='Grinder 5'
- When: The form initializes and performs the asset lookup
- Then: A Supabase query is made to the 'assets' table with .eq('name', 'Grinder 5').single(), and the resolved asset_id is stored for submission
- Data: Mock Supabase client returning {data: {id: 'asset-uuid-123'}, error: null} for the assets query

### 16-3-create-action-plan-from-followup-UNIT-006: ActionPlanForm handles asset_name not found in assets table gracefully
- Priority: P1
- Type: unit
- Given: An ActionPlanForm is rendered with prefill containing assetName='Unknown Machine 99'
- When: The Supabase assets lookup returns no match (data: null, error: {message: 'not found'})
- Then: The form still renders without error, asset_id is set to null, and the asset name display shows "Unknown Machine 99" as read-only text
- Data: Mock Supabase assets query returning null/error

### 16-3-create-action-plan-from-followup-UNIT-007: All pre-filled fields in ActionPlanForm are editable by the manager
- Priority: P0
- Type: unit
- Given: An ActionPlanForm is rendered with all pre-filled fields (title, description, root_cause, category, priority)
- When: The manager modifies the title to "Custom Title", changes category to 'preventive', changes priority to 'critical', and edits root_cause
- Then: All field values update to the manager's edits and the form state reflects the new values
- Data: prefill with all mapped fields; simulate user edits via fireEvent.change

### 16-3-create-action-plan-from-followup-UNIT-008: ActionPlanForm handles null asset_name in prefill
- Priority: P1
- Type: unit
- Given: An ActionPlanForm is rendered with prefill where assetName is null
- When: The form renders
- Then: No Supabase assets lookup is performed, the asset display shows a placeholder or is hidden, and the form does not throw an error
- Data: prefill with assetName=null

### 16-3-create-action-plan-from-followup-INT-002: FollowUpDetailDialog extracts response text from inbound messages for pre-fill
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is open and useFollowUpMessages returns messages including an inbound message with direction='inbound', message_type='response', body='Investigated and found worn bearing causing vibration'
- When: The manager clicks "Create Action Plan"
- Then: The ActionPlanForm opens with root_cause pre-filled with the inbound response message body text
- Data: Mock useFollowUpMessages returning messages array with at least one inbound response message

### 16-3-create-action-plan-from-followup-INT-003: Pre-fill handles multiple inbound messages by using latest response
- Priority: P2
- Type: integration
- Given: A follow-up has multiple inbound response messages (msg-1 at T1: "Initial findings", msg-2 at T2: "Final root cause confirmed: worn bearing")
- When: The manager clicks "Create Action Plan"
- Then: The root_cause field is pre-filled with the concatenation of inbound message bodies or the latest response body
- Data: Mock useFollowUpMessages with two inbound messages with different sent_at timestamps

## AC2: Linked Action Plan Visible on Follow-Up Detail

Given the action plan is created from a follow-up, When the follow-up detail is viewed later, Then a link to the created action plan is visible and the follow-up shows "Action plan created" status.

### 16-3-create-action-plan-from-followup-INT-004: Follow-up detail shows linked action plan when one exists
- Priority: P0
- Type: integration
- Given: A follow-up with id='fu-123' has a linked action plan (queried via getLinkedActionPlan where source_followup_id='fu-123'), and the action plan has id='ap-456' and title='Action Plan: Fix valve leak'
- When: The FollowUpDetailDialog opens for this follow-up
- Then: A link or badge displaying "Action Plan: Fix valve leak" is visible in the dialog, and the "Create Action Plan" button is NOT shown
- Data: Mock useActionPlans.getLinkedActionPlan returning {id: 'ap-456', title: 'Action Plan: Fix valve leak', status: 'open'}

### 16-3-create-action-plan-from-followup-INT-005: Linked action plan link navigates to action plan detail
- Priority: P1
- Type: integration
- Given: A FollowUpDetailDialog shows a linked action plan with id='ap-456'
- When: The manager clicks the action plan link
- Then: Navigation is triggered to '/action-plans/ap-456' (or the link element has href='/action-plans/ap-456')
- Data: Mock linked action plan data with id='ap-456'

### 16-3-create-action-plan-from-followup-UNIT-009: getLinkedActionPlan queries action_plans by source_followup_id
- Priority: P0
- Type: unit
- Given: The useActionPlans hook is initialized
- When: getLinkedActionPlan('fu-123') is called
- Then: A fetch request is made to GET /api/v1/action-plans with query parameter source_followup_id=fu-123 (or a Supabase query to action_plans table with .eq('source_followup_id', 'fu-123')), and the first matching result is returned
- Data: Mock API or Supabase response returning one action plan with source_followup_id='fu-123'

### 16-3-create-action-plan-from-followup-UNIT-010: getLinkedActionPlan returns null when no linked plan exists
- Priority: P1
- Type: unit
- Given: The useActionPlans hook is initialized
- When: getLinkedActionPlan('fu-no-plan') is called and no action plan has source_followup_id='fu-no-plan'
- Then: The function returns null, and the FollowUpDetailDialog shows the "Create Action Plan" button instead of a link
- Data: Mock API or Supabase response returning empty results

### 16-3-create-action-plan-from-followup-INT-006: Follow-up detail dialog shows both "Create Action Plan" button and linked plan correctly across states
- Priority: P1
- Type: integration
- Given: Two follow-ups exist: fu-1 has a linked action plan, fu-2 does not (but has a response)
- When: The detail dialog opens for fu-1, then closes and opens for fu-2
- Then: For fu-1, the linked plan link is shown and "Create Action Plan" is hidden; for fu-2, the "Create Action Plan" button is shown and no linked plan link is visible
- Data: Mock getLinkedActionPlan returning a plan for fu-1 and null for fu-2

## AC3: "Create Action Plan" Button Hidden When No Response

Given the "Create Action Plan" button, When the follow-up has no response yet (status is still 'assigned'), Then the button is not shown — it only appears on follow-ups with responses.

### 16-3-create-action-plan-from-followup-INT-007: "Create Action Plan" button is hidden when follow-up status is 'assigned'
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is open for a follow-up with status='assigned' (no response yet)
- When: The dialog renders
- Then: No "Create Action Plan" button is present in the dialog
- Data: MockFollowUpItem with status='assigned'

### 16-3-create-action-plan-from-followup-INT-008: "Create Action Plan" button is shown when follow-up status is 'in_progress'
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is open for a follow-up with status='in_progress' (has engagement from assignee), and no linked action plan exists
- When: The dialog renders
- Then: A "Create Action Plan" button is visible in the dialog
- Data: MockFollowUpItem with status='in_progress'; mock getLinkedActionPlan returning null

### 16-3-create-action-plan-from-followup-INT-009: "Create Action Plan" button is shown when follow-up status is 'resolved'
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is open for a follow-up with status='resolved', and no linked action plan exists
- When: The dialog renders
- Then: A "Create Action Plan" button is visible in the dialog
- Data: MockFollowUpItem with status='resolved'; mock getLinkedActionPlan returning null

### 16-3-create-action-plan-from-followup-INT-010: "Create Action Plan" button is hidden when linked plan already exists (regardless of status)
- Priority: P1
- Type: integration
- Given: A FollowUpDetailDialog is open for a follow-up with status='in_progress' and a linked action plan already exists
- When: The dialog renders
- Then: The "Create Action Plan" button is NOT shown; instead the linked action plan link/badge is displayed
- Data: MockFollowUpItem with status='in_progress'; mock getLinkedActionPlan returning a plan object

## AC4: Action Plan Created via POST with Required Fields

Given the action plan form is open, When the manager submits with required fields (title, category, priority, due_date), Then the plan is created via POST /api/v1/action-plans with status='open' and the current user as owner.

### 16-3-create-action-plan-from-followup-INT-011: Successful form submission calls POST /api/v1/action-plans with correct payload
- Priority: P0
- Type: integration
- Given: An ActionPlanForm is rendered with pre-filled data, and the manager has filled in all required fields (title='Fix valve leak', category='corrective', priority='high', due_date='2026-03-01'), and a valid Supabase session exists
- When: The manager clicks the submit button
- Then: A fetch POST request is sent to ${apiUrl}/api/v1/action-plans with headers including 'Authorization: Bearer mock-token' and 'Content-Type: application/json', and the body contains {title: 'Fix valve leak', category: 'corrective', priority: 'high', due_date: '2026-03-01', source_followup_id: 'fu-123', asset_id: 'asset-uuid-123', description: '...', root_cause: '...'}, and status is NOT included in the request body (set by server as 'open')
- Data: Mock session with access_token='mock-token'; mock fetch returning 201 with created plan response

### 16-3-create-action-plan-from-followup-UNIT-011: Form validation prevents submission without title
- Priority: P0
- Type: unit
- Given: An ActionPlanForm is rendered with pre-filled data but the manager clears the title field
- When: The manager attempts to submit the form
- Then: The form does not submit, and a validation error is shown for the title field (or the submit button is disabled)
- Data: prefill data; simulate clearing title input

### 16-3-create-action-plan-from-followup-UNIT-012: Form validation prevents submission without category
- Priority: P0
- Type: unit
- Given: An ActionPlanForm is rendered and the category field is not selected (cleared by manager)
- When: The manager attempts to submit the form
- Then: The form does not submit, and a validation message indicates category is required
- Data: prefill data with category cleared

### 16-3-create-action-plan-from-followup-UNIT-013: Form validation prevents submission without priority
- Priority: P0
- Type: unit
- Given: An ActionPlanForm is rendered and the priority field is not selected (cleared by manager)
- When: The manager attempts to submit the form
- Then: The form does not submit, and a validation message indicates priority is required
- Data: prefill data with priority cleared

### 16-3-create-action-plan-from-followup-UNIT-014: Form validation prevents submission without due_date
- Priority: P0
- Type: unit
- Given: An ActionPlanForm is rendered and the due_date field is empty
- When: The manager attempts to submit the form
- Then: The form does not submit, and a validation message indicates due_date is required
- Data: prefill data with due_date empty

### 16-3-create-action-plan-from-followup-UNIT-015: Submit button shows loading spinner during submission
- Priority: P1
- Type: unit
- Given: An ActionPlanForm is rendered with all required fields filled
- When: The manager clicks submit and the API request is in-flight
- Then: The submit button displays a Loader2 spinner icon and is disabled to prevent duplicate submissions
- Data: Mock fetch that returns a pending promise (never resolves during test)

### 16-3-create-action-plan-from-followup-UNIT-016: Form displays error message on API failure
- Priority: P0
- Type: unit
- Given: An ActionPlanForm is rendered with all required fields filled, and the POST /api/v1/action-plans endpoint returns a 500 error
- When: The manager submits the form
- Then: An error message is displayed in the form (e.g., "Failed to create action plan"), the form remains open, and the submit button is re-enabled
- Data: Mock fetch returning {ok: false, status: 500, json: {detail: 'Internal server error'}}

### 16-3-create-action-plan-from-followup-UNIT-017: Form displays error on 401 unauthorized
- Priority: P1
- Type: unit
- Given: An ActionPlanForm is rendered and the session has expired (no valid access_token)
- When: The manager submits the form
- Then: An authentication error message is displayed, and the form does not close
- Data: Mock Supabase getSession returning null session, or mock fetch returning 401

### 16-3-create-action-plan-from-followup-UNIT-018: Form shows success state with CheckCircle2 icon after successful creation
- Priority: P1
- Type: unit
- Given: An ActionPlanForm is rendered and submission succeeds (201 response)
- When: The API returns a successful response
- Then: The form transitions to a success state showing a CheckCircle2 icon and "Action Plan Created" message, then auto-closes after approximately 1500ms
- Data: Mock fetch returning {ok: true, status: 201, json: {id: 'ap-new', title: 'Fix valve leak', status: 'open'}}

### 16-3-create-action-plan-from-followup-UNIT-019: createActionPlan hook function constructs correct API call
- Priority: P0
- Type: unit
- Given: The useActionPlans hook is initialized with a valid session
- When: createActionPlan() is called with a CreateActionPlanRequest payload
- Then: fetch is called with method='POST', URL=${apiUrl}/api/v1/action-plans, headers include Authorization and Content-Type, and the body is JSON-stringified payload without status or owner_id fields
- Data: Mock session, mock fetch; payload with title, category, priority, due_date, source_followup_id, asset_id, description, root_cause

## AC5: Follow-Up Updates Without Full Page Reload After Action Plan Creation

Given the action plan is created successfully, When the form closes, Then the follow-up entry updates to show the linked action plan without a full page reload.

### 16-3-create-action-plan-from-followup-INT-012: Follow-up detail updates to show linked plan after successful creation without reload
- Priority: P0
- Type: integration
- Given: A FollowUpDetailDialog is open showing a "Create Action Plan" button (no linked plan exists), and the manager has opened and submitted the ActionPlanForm successfully, and the API returned the created plan with id='ap-new' and title='Action Plan: Fix valve leak'
- When: The ActionPlanForm success callback fires and the form auto-closes
- Then: The FollowUpDetailDialog immediately updates to show "Action Plan: Fix valve leak" as a link/badge, the "Create Action Plan" button is no longer visible, and no full page reload or navigation occurred
- Data: Mock successful creation response; verify state update via React re-render (not window.location change)

### 16-3-create-action-plan-from-followup-INT-013: ActionPlanForm onSuccess callback passes created plan data back to parent
- Priority: P0
- Type: integration
- Given: An ActionPlanForm is rendered with an onSuccess callback prop
- When: The form submission succeeds and the API returns {id: 'ap-new', title: 'Action Plan: Fix valve'}
- Then: The onSuccess callback is invoked with the created plan data ({id: 'ap-new', title: 'Action Plan: Fix valve'}), allowing the parent FollowUpDetailDialog to update its state
- Data: Mock onSuccess callback spy; mock successful API response

### 16-3-create-action-plan-from-followup-UNIT-020: FollowUpDetailDialog manages ActionPlanForm dialog state correctly
- Priority: P1
- Type: unit
- Given: A FollowUpDetailDialog is rendered with a follow-up that has status='in_progress' and no linked plan
- When: The manager clicks "Create Action Plan", then closes the ActionPlanForm without submitting
- Then: The ActionPlanForm dialog closes, the FollowUpDetailDialog remains open, and the "Create Action Plan" button is still visible
- Data: MockFollowUpItem with status='in_progress'; simulate open/close of nested dialog

edge_cases:
  - Follow-up with null category: ActionPlanForm should handle null category by leaving category and priority selects at default/empty, requiring manager to select
  - Follow-up with very long action_summary (200+ chars): Title pre-fill should truncate gracefully without breaking the input field
  - Follow-up with null asset_name and null category: Form renders with minimal pre-fill (only source_followup_id and description from action_summary)
  - Asset name exists in follow-up but has been deleted from assets table: asset_id resolves to null, form still submits successfully
  - Multiple action plans created for the same follow-up: getLinkedActionPlan returns the most recent one; UI shows one link
  - Network failure during asset lookup: Form still renders with asset_id=null, does not block form interaction
  - Follow-up messages are still loading when "Create Action Plan" is clicked: Pre-fill should use available data or wait for messages to load
  - Empty response body in inbound message: root_cause pre-fill should be empty string, not "undefined" or "null"

error_scenarios:
  - POST /api/v1/action-plans returns 400 (validation error from server): Form shows specific validation error from response body
  - POST /api/v1/action-plans returns 401 (expired token): Form shows authentication error, prompts re-login
  - POST /api/v1/action-plans returns 500 (server error): Form shows generic error message, allows retry
  - Network timeout during form submission: Form shows network error, re-enables submit button
  - Supabase assets table query fails: asset_id set to null, form continues to work
  - getLinkedActionPlan query fails on dialog open: Dialog still renders, shows "Create Action Plan" button (fails open, not closed)
  - Session is null when form attempts to submit: Shows "Please log in" error before attempting API call

test_file_mapping:
  - 16-3-create-action-plan-from-followup-INT-*: apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx (extend existing), apps/web/src/components/action-plans/__tests__/ActionPlanForm.test.tsx (new)
  - 16-3-create-action-plan-from-followup-UNIT-001 to UNIT-008: apps/web/src/components/action-plans/__tests__/ActionPlanForm.test.tsx
  - 16-3-create-action-plan-from-followup-UNIT-009 to UNIT-010: apps/web/src/hooks/__tests__/useActionPlans.test.ts
  - 16-3-create-action-plan-from-followup-UNIT-011 to UNIT-018: apps/web/src/components/action-plans/__tests__/ActionPlanForm.test.tsx
  - 16-3-create-action-plan-from-followup-UNIT-019: apps/web/src/hooks/__tests__/useActionPlans.test.ts
  - 16-3-create-action-plan-from-followup-UNIT-020: apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx
  - 16-3-create-action-plan-from-followup-E2E-*: (none specified — E2E would require full Supabase + API stack)

TEST SPEC END
