TEST SPEC START
story_id: 15-3-response-capture-via-token-link
generated: 2026-02-11

test_specifications:

## AC1: Response page renders via token link
Given the assignee receives the notification email, when they click the "Respond" link, then they are taken to `{app_url}/followups/{id}/respond?token={one_time_token}` and the page shows the original action item context (recommendation, evidence summary, financial impact, who assigned it, the manager's note) and a text response field.

### 15-3-response-capture-via-token-link-UNIT-001: TokenService.generate_token produces UUID and stores in followup_messages
- Priority: P0
- Type: unit
- Given: A valid followup_id (UUID) and assignee_email="assignee@plant.com" exist, and the Supabase client is mocked
- When: TokenService.generate_token(followup_id, assignee_email) is called
- Then: A UUID v4 string is returned, and a followup_messages record is inserted with response_token set to the generated UUID, token_expires_at set to approximately now + 72 hours, token_used_at=None, direction='outbound', message_type='assignment', and sender_email=assignee_email
- Data: followup_id="uuid-followup-1", assignee_email="assignee@plant.com"

### 15-3-response-capture-via-token-link-UNIT-002: TokenService.generate_token sets token_expires_at to 72 hours from now
- Priority: P0
- Type: unit
- Given: The current time is known (mocked via datetime), and Supabase client is mocked
- When: TokenService.generate_token() is called
- Then: The token_expires_at value in the inserted record is exactly 72 hours after the current time (within a small tolerance)
- Data: Mocked current time, expected expiry = now + 72h

### 15-3-response-capture-via-token-link-UNIT-003: TokenService.validate_token returns valid result for fresh token
- Priority: P0
- Type: unit
- Given: A followup_messages record exists with response_token="valid-uuid-token", token_expires_at in the future, and token_used_at=None; Supabase client is mocked to return this record
- When: TokenService.validate_token("valid-uuid-token") is called
- Then: A TokenValidationResult is returned with is_valid=True, followup_id matching the record, assignee_email matching the record's sender_email, and error_reason=None
- Data: response_token="valid-uuid-token", token_expires_at=now+24h, token_used_at=None

### 15-3-response-capture-via-token-link-UNIT-004: TokenService.validate_token returns expired for token past 72h
- Priority: P0
- Type: unit
- Given: A followup_messages record exists with response_token="expired-token", token_expires_at in the past (e.g., 73 hours ago), and token_used_at=None; Supabase is mocked
- When: TokenService.validate_token("expired-token") is called
- Then: A TokenValidationResult is returned with is_valid=False and error_reason='expired'
- Data: response_token="expired-token", token_expires_at=now-1h

### 15-3-response-capture-via-token-link-UNIT-005: TokenService.validate_token returns used for already-consumed token
- Priority: P0
- Type: unit
- Given: A followup_messages record exists with response_token="used-token", token_expires_at in the future, and token_used_at set to a past timestamp; Supabase is mocked
- When: TokenService.validate_token("used-token") is called
- Then: A TokenValidationResult is returned with is_valid=False and error_reason='expired' (used tokens show same message as expired)
- Data: response_token="used-token", token_used_at="2026-02-10T12:00:00Z"

### 15-3-response-capture-via-token-link-UNIT-006: TokenService.validate_token returns invalid for nonexistent token
- Priority: P0
- Type: unit
- Given: No followup_messages record exists with response_token="nonexistent-token"; Supabase query returns empty data
- When: TokenService.validate_token("nonexistent-token") is called
- Then: A TokenValidationResult is returned with is_valid=False and error_reason='invalid'
- Data: response_token="nonexistent-token"

### 15-3-response-capture-via-token-link-UNIT-007: TokenService.mark_token_used sets token_used_at timestamp
- Priority: P0
- Type: unit
- Given: A followup_messages record exists with response_token="token-to-use" and token_used_at=None; Supabase is mocked
- When: TokenService.mark_token_used("token-to-use") is called
- Then: The Supabase update is called on the followup_messages record setting token_used_at to the current timestamp (not None)
- Data: response_token="token-to-use"

### 15-3-response-capture-via-token-link-INT-001: GET /api/v1/followups/{id}/context returns followup context for valid token
- Priority: P0
- Type: integration
- Given: A valid token exists in followup_messages with associated followup_id, the action_followups record exists with action_summary, asset_name, category, assigned_by, note, report_date; Supabase client is mocked to return these records
- When: GET /api/v1/followups/{id}/context?token={valid_token} is called (no Authorization header)
- Then: The endpoint returns 200 with a JSON body containing action_summary, asset_name, category, assigned_by_email, assigned_by_name, note, and report_date
- Data: followup_id="uuid-followup-1", token="valid-token", action_summary="Replace bearing", asset_name="Pump-101", category="safety"

### 15-3-response-capture-via-token-link-INT-002: GET /api/v1/followups/{id}/context does not require authentication
- Priority: P0
- Type: integration
- Given: A valid token exists for the requested followup_id; Supabase is mocked
- When: GET /api/v1/followups/{id}/context?token={valid_token} is called WITHOUT any Authorization header
- Then: The endpoint returns 200 (not 401 or 403) — this is a public endpoint where the token IS the auth
- Data: No auth header, valid token in query parameter

### 15-3-response-capture-via-token-link-INT-003: GET /api/v1/followups/{id}/context returns assigner details
- Priority: P1
- Type: integration
- Given: A valid token, the action_followups record has assigned_by="uuid-manager-1", and auth.users has this user with email="manager@plant.com"; Supabase is mocked
- When: GET /api/v1/followups/{id}/context?token={valid_token} is called
- Then: The response includes assigned_by_email="manager@plant.com" and assigned_by_name (resolved from user metadata or email)
- Data: assigned_by UUID resolves to manager@plant.com

### 15-3-response-capture-via-token-link-E2E-001: Clicking token link in email loads response page with context
- Priority: P0
- Type: e2e
- Given: A follow-up has been assigned and a notification email sent with a valid token URL `{app_url}/followups/{id}/respond?token={token}`
- When: The assignee navigates to this URL in a browser (not logged in)
- Then: The page renders showing: (1) the action item recommendation text, (2) evidence summary, (3) financial impact if present, (4) who assigned it (assigner name/email), (5) the manager's note, and (6) a text response textarea field with a submit button
- Data: Full follow-up with all context fields populated

### 15-3-response-capture-via-token-link-E2E-002: Response page works on mobile browser
- Priority: P1
- Type: e2e
- Given: A valid token link exists for a follow-up
- When: The assignee opens the link on a mobile device (small viewport, e.g., 375x812)
- Then: The page is responsive — context card and form are readable, textarea is usable, submit button is tappable, no horizontal scrolling required
- Data: Mobile viewport dimensions

## AC2: Response submission creates message record
Given the assignee submits a response via the form, when the response is submitted, then a record is created in followup_messages with direction='inbound', message_type='response', sender_email set to the assignee's email from the token, and body containing the response text. The follow-up status in action_followups is updated to 'in_progress' (if currently 'assigned'). A success confirmation is shown.

### 15-3-response-capture-via-token-link-UNIT-008: TokenResponseRequest validates response_text is non-empty
- Priority: P0
- Type: unit
- Given: A TokenResponseRequest Pydantic model
- When: Constructed with token="valid-token" and response_text="" (empty string)
- Then: A ValidationError is raised indicating response_text must not be empty
- Data: response_text=""

### 15-3-response-capture-via-token-link-UNIT-009: TokenResponseRequest validates response_text max length (5000 chars)
- Priority: P1
- Type: unit
- Given: A TokenResponseRequest Pydantic model
- When: Constructed with response_text containing 5001 characters
- Then: A ValidationError is raised indicating response_text exceeds maximum length
- Data: response_text="x" * 5001

### 15-3-response-capture-via-token-link-UNIT-010: TokenResponseRequest accepts valid payload
- Priority: P1
- Type: unit
- Given: A TokenResponseRequest Pydantic model
- When: Constructed with token="valid-uuid" and response_text="I will fix the bearing tomorrow"
- Then: The model is constructed without errors, token and response_text match inputs
- Data: token="valid-uuid", response_text="I will fix the bearing tomorrow"

### 15-3-response-capture-via-token-link-INT-004: POST /api/v1/followups/respond creates inbound message record with valid token
- Priority: P0
- Type: integration
- Given: A valid token exists in followup_messages linked to a followup with status='assigned', assignee_email="assignee@plant.com"; Supabase is mocked for both read and write operations
- When: POST /api/v1/followups/respond is called with { "token": "valid-token", "response_text": "I fixed the bearing" }
- Then: A new followup_messages record is inserted with direction='inbound', message_type='response', sender_email="assignee@plant.com" (from token lookup), body="I fixed the bearing", and the endpoint returns { "success": true, "message": "Response recorded" }
- Data: token="valid-token", response_text="I fixed the bearing"

### 15-3-response-capture-via-token-link-INT-005: POST /api/v1/followups/respond updates status from 'assigned' to 'in_progress'
- Priority: P0
- Type: integration
- Given: A valid token exists, and the linked action_followups record has status='assigned'; Supabase is mocked
- When: POST /api/v1/followups/respond is called with valid token and response text
- Then: The action_followups record is updated with status='in_progress' via a conditional UPDATE WHERE status='assigned'
- Data: Current status='assigned'

### 15-3-response-capture-via-token-link-INT-006: POST /api/v1/followups/respond does NOT regress status from 'in_progress'
- Priority: P0
- Type: integration
- Given: A valid token exists, and the linked action_followups record already has status='in_progress'; Supabase is mocked
- When: POST /api/v1/followups/respond is called with valid token and response text
- Then: The action_followups.status remains 'in_progress' — the conditional UPDATE WHERE status='assigned' has no effect, and the response message is still created successfully
- Data: Current status='in_progress'

### 15-3-response-capture-via-token-link-INT-007: POST /api/v1/followups/respond does NOT regress status from 'resolved'
- Priority: P0
- Type: integration
- Given: A valid token exists, and the linked action_followups record has status='resolved'; Supabase is mocked
- When: POST /api/v1/followups/respond is called with valid token and response text
- Then: The action_followups.status remains 'resolved' — the conditional UPDATE WHERE status='assigned' has no effect, and the response message is still created successfully
- Data: Current status='resolved'

### 15-3-response-capture-via-token-link-INT-008: POST /api/v1/followups/respond marks token as used after success
- Priority: P0
- Type: integration
- Given: A valid, unused token exists; Supabase is mocked
- When: POST /api/v1/followups/respond is called with the token and valid response text
- Then: TokenService.mark_token_used() is called with the token, setting token_used_at to a timestamp on the followup_messages record
- Data: token="valid-token"

### 15-3-response-capture-via-token-link-INT-009: POST /api/v1/followups/respond does not require authentication
- Priority: P0
- Type: integration
- Given: A valid token exists; Supabase is mocked
- When: POST /api/v1/followups/respond is called WITHOUT any Authorization header
- Then: The endpoint returns 200 (not 401 or 403) — this is a public endpoint where the token IS the auth
- Data: No auth header, valid token in request body

### 15-3-response-capture-via-token-link-INT-010: POST /api/v1/followups/respond returns 422 for missing response_text
- Priority: P1
- Type: integration
- Given: A request body with token="valid-token" but no response_text field
- When: POST /api/v1/followups/respond is called
- Then: The endpoint returns 422 Unprocessable Entity with validation error details
- Data: { "token": "valid-token" }

### 15-3-response-capture-via-token-link-INT-011: POST /api/v1/followups/respond returns 422 for empty response_text
- Priority: P1
- Type: integration
- Given: A request body with token="valid-token" and response_text=""
- When: POST /api/v1/followups/respond is called
- Then: The endpoint returns 422 Unprocessable Entity with validation error
- Data: { "token": "valid-token", "response_text": "" }

### 15-3-response-capture-via-token-link-E2E-003: Submitting response shows success confirmation
- Priority: P0
- Type: e2e
- Given: The response page is rendered with a valid token, context card is visible, and textarea is populated with "I will address this by Friday"
- When: The user clicks the Submit button
- Then: (1) A success confirmation is shown with a green checkmark and message "Your response has been recorded", (2) The submit button becomes disabled to prevent double-submit, (3) The textarea is no longer editable
- Data: response_text="I will address this by Friday"

### 15-3-response-capture-via-token-link-E2E-004: Double-submit is prevented on frontend
- Priority: P1
- Type: e2e
- Given: The user has already submitted a response and sees the success confirmation
- When: The user attempts to click the submit button again (even if they manipulate DOM to re-enable it)
- Then: The button remains disabled and no second POST request is sent; server-side, the token is already marked used so any repeated API call would also fail
- Data: Previously submitted token

### 15-3-response-capture-via-token-link-INT-012: Full flow — token generation to response submission to message creation
- Priority: P0
- Type: integration
- Given: TokenService.generate_token() has been called and returns a token, the followup_messages outbound record exists with the token
- When: (1) GET /api/v1/followups/{id}/context?token={token} fetches context successfully, then (2) POST /api/v1/followups/respond is called with the token and response_text="Completed the repair"
- Then: (1) A new followup_messages record is created with direction='inbound', message_type='response', body="Completed the repair", sender_email from the original token record, (2) The action_followups.status is updated to 'in_progress' if it was 'assigned', (3) The token is marked as used (token_used_at is set), (4) Success response is returned
- Data: Full flow with real token generation and consumption

## AC3: Expired token shows expiry message
Given the response token has already been used or is expired (>72 hours), when the assignee clicks the link, then a message is shown: "This link has expired. Please log in to the app to respond." No form is rendered.

### 15-3-response-capture-via-token-link-INT-013: GET /api/v1/followups/{id}/context returns 400 for expired token
- Priority: P0
- Type: integration
- Given: A followup_messages record exists with response_token where token_expires_at is in the past; Supabase is mocked
- When: GET /api/v1/followups/{id}/context?token={expired_token} is called
- Then: The endpoint returns 400 with a response body containing error_reason='expired'
- Data: token with token_expires_at = now - 1 hour

### 15-3-response-capture-via-token-link-INT-014: GET /api/v1/followups/{id}/context returns 400 for already-used token
- Priority: P0
- Type: integration
- Given: A followup_messages record exists with response_token where token_used_at is set (already consumed); Supabase is mocked
- When: GET /api/v1/followups/{id}/context?token={used_token} is called
- Then: The endpoint returns 400 with a response body containing error_reason='expired' (used tokens treated same as expired for user messaging)
- Data: token with token_used_at = "2026-02-10T12:00:00Z"

### 15-3-response-capture-via-token-link-INT-015: POST /api/v1/followups/respond returns 400 for expired token
- Priority: P0
- Type: integration
- Given: A followup_messages record exists with an expired token (token_expires_at < now); Supabase is mocked
- When: POST /api/v1/followups/respond is called with { "token": "expired-token", "response_text": "My response" }
- Then: The endpoint returns 400 with detail "Token expired", no followup_messages inbound record is created, no status update occurs
- Data: Expired token, valid response text

### 15-3-response-capture-via-token-link-INT-016: POST /api/v1/followups/respond returns 400 for already-used token
- Priority: P0
- Type: integration
- Given: A followup_messages record exists with token_used_at already set (previously consumed); Supabase is mocked
- When: POST /api/v1/followups/respond is called with { "token": "used-token", "response_text": "Trying again" }
- Then: The endpoint returns 400 with detail "Token expired", no new message record is created
- Data: Used token, valid response text

### 15-3-response-capture-via-token-link-E2E-005: Expired token link shows expiry message with no form
- Priority: P0
- Type: e2e
- Given: A token link where the token has expired (>72 hours since creation)
- When: The assignee clicks the link and navigates to `/followups/{id}/respond?token={expired_token}`
- Then: The page displays "This link has expired. Please log in to the app to respond." and no textarea or submit button is rendered
- Data: Expired token URL

### 15-3-response-capture-via-token-link-E2E-006: Already-used token link shows expiry message with no form
- Priority: P0
- Type: e2e
- Given: A token link where the token has already been used (response previously submitted)
- When: The assignee clicks the link again
- Then: The page displays "This link has expired. Please log in to the app to respond." and no textarea or submit button is rendered
- Data: Previously used token URL

## AC4: Invalid token shows error
Given the response token is invalid (malformed, nonexistent), when the link is accessed, then a 404 or "Invalid link" message is shown. No form is rendered.

### 15-3-response-capture-via-token-link-INT-017: GET /api/v1/followups/{id}/context returns 404 for nonexistent token
- Priority: P0
- Type: integration
- Given: No followup_messages record exists with the given response_token; Supabase query returns empty data
- When: GET /api/v1/followups/{id}/context?token=nonexistent-token-uuid is called
- Then: The endpoint returns 404 with a response body containing error_reason='invalid'
- Data: token="nonexistent-token-uuid"

### 15-3-response-capture-via-token-link-INT-018: GET /api/v1/followups/{id}/context returns 404 for malformed token
- Priority: P1
- Type: integration
- Given: The token parameter is a random string that doesn't match any record; Supabase query returns empty data
- When: GET /api/v1/followups/{id}/context?token=not-a-real-token is called
- Then: The endpoint returns 404 with error_reason='invalid'
- Data: token="not-a-real-token"

### 15-3-response-capture-via-token-link-INT-019: GET /api/v1/followups/{id}/context returns error when token is missing from query
- Priority: P1
- Type: integration
- Given: No token query parameter is provided
- When: GET /api/v1/followups/{id}/context is called without a token parameter
- Then: The endpoint returns 422 (missing required query parameter) or 400
- Data: No token query param

### 15-3-response-capture-via-token-link-INT-020: POST /api/v1/followups/respond returns 404 for nonexistent token
- Priority: P0
- Type: integration
- Given: No followup_messages record exists with the given response_token; Supabase query returns empty data
- When: POST /api/v1/followups/respond is called with { "token": "fake-uuid-token", "response_text": "My response" }
- Then: The endpoint returns 404 with detail "Invalid link", no message record is created
- Data: token="fake-uuid-token"

### 15-3-response-capture-via-token-link-INT-021: POST /api/v1/followups/respond returns 404 for malformed token
- Priority: P1
- Type: integration
- Given: The token field contains a random/malformed string; no matching record exists
- When: POST /api/v1/followups/respond is called with { "token": "abc123garbage", "response_text": "My response" }
- Then: The endpoint returns 404 with detail "Invalid link"
- Data: token="abc123garbage"

### 15-3-response-capture-via-token-link-E2E-007: Invalid token link shows error message with no form
- Priority: P0
- Type: e2e
- Given: A URL with a completely invalid/nonexistent token: `/followups/{id}/respond?token=invalid-uuid`
- When: The user navigates to this URL
- Then: The page displays "Invalid link" (or a 404 message), no textarea or submit button is rendered
- Data: Invalid token URL

### 15-3-response-capture-via-token-link-E2E-008: Missing token parameter shows error
- Priority: P1
- Type: e2e
- Given: A URL without a token parameter: `/followups/{id}/respond`
- When: The user navigates to this URL
- Then: The page displays an error message and no form is rendered
- Data: URL without token query param

## Cross-Cutting: Token Integration with Email Flow

### 15-3-response-capture-via-token-link-UNIT-011: render_assignment_email includes token in Respond URL when provided
- Priority: P0
- Type: unit
- Given: render_assignment_email() is called with response_token="abc-uuid-token" and followup_id="uuid-123" and app_base_url="https://plant.example.com"
- When: The email template is rendered
- Then: The HTML body Respond link href includes the full URL with token: "https://plant.example.com/followups/uuid-123/respond?token=abc-uuid-token"
- Data: response_token="abc-uuid-token", followup_id="uuid-123"

### 15-3-response-capture-via-token-link-UNIT-012: render_assignment_email works without token (backward compatibility)
- Priority: P1
- Type: unit
- Given: render_assignment_email() is called with response_token=None (default)
- When: The email template is rendered
- Then: The HTML body Respond link href does NOT contain "?token=" — the URL is just "https://plant.example.com/followups/{id}/respond" without a token query parameter
- Data: response_token=None

### 15-3-response-capture-via-token-link-UNIT-013: get_token_service factory returns singleton
- Priority: P1
- Type: unit
- Given: The email service module is initialized
- When: get_token_service() is called multiple times
- Then: The same TokenService instance is returned each time
- Data: None

### 15-3-response-capture-via-token-link-UNIT-014: TokenService uses service_role Supabase client
- Priority: P1
- Type: unit
- Given: TokenService is instantiated with a Supabase client
- When: Any token operation is performed (generate, validate, mark_used)
- Then: The Supabase service_role client is used (not a user-scoped JWT client), ensuring RLS is bypassed since the public endpoints have no authenticated user
- Data: Service role key vs user JWT

### 15-3-response-capture-via-token-link-INT-022: Notification service generates token and includes in email during assignment
- Priority: P0
- Type: integration
- Given: SMTP is configured, a follow-up is being assigned, TokenService.generate_token is available; Supabase is mocked
- When: send_assignment_notification() is called with follow-up data
- Then: (1) TokenService.generate_token() is called with the followup_id and resolved assignee email, (2) The generated token is passed to render_assignment_email(), (3) The respond URL in the email HTML includes ?token={generated_token}
- Data: Standard follow-up data with all required fields

## Cross-Cutting: Database Migration

### 15-3-response-capture-via-token-link-INT-023: Migration 0032 adds token columns to followup_messages
- Priority: P0
- Type: integration
- Given: The followup_messages table exists from migrations 0030 and 0031
- When: Migration 0032_response_tokens.sql is applied
- Then: The followup_messages table has three new columns: response_token (TEXT, nullable), token_expires_at (TIMESTAMPTZ, nullable), and token_used_at (TIMESTAMPTZ, nullable)
- Data: SQL migration file

### 15-3-response-capture-via-token-link-INT-024: Migration 0032 creates unique partial index on response_token
- Priority: P0
- Type: integration
- Given: The followup_messages table has the response_token column
- When: Migration 0032_response_tokens.sql is applied
- Then: A unique index idx_followup_messages_response_token is created on response_token WHERE response_token IS NOT NULL, enabling fast token lookups while allowing multiple NULL values
- Data: Index definition in migration

## Cross-Cutting: Error Handling and Security

### 15-3-response-capture-via-token-link-INT-025: POST /api/v1/followups/respond handles Supabase errors gracefully
- Priority: P1
- Type: integration
- Given: Token is valid but Supabase insert for the inbound message raises an exception
- When: POST /api/v1/followups/respond is called
- Then: The endpoint returns 500 with a generic error message, the error is logged, and no partial state is left (token is NOT marked as used if message insert fails)
- Data: Mocked Supabase insert failure

### 15-3-response-capture-via-token-link-UNIT-015: TokenService handles database errors in validate_token gracefully
- Priority: P1
- Type: unit
- Given: Supabase client raises an exception during the token lookup query
- When: TokenService.validate_token() is called
- Then: The error is propagated as an appropriate exception (not silently swallowed), allowing the API endpoint to return a 500 error
- Data: Mocked Supabase query failure

### 15-3-response-capture-via-token-link-INT-026: POST /api/v1/followups/respond with response_text at max length (5000 chars) succeeds
- Priority: P2
- Type: integration
- Given: A valid token exists; response_text is exactly 5000 characters long
- When: POST /api/v1/followups/respond is called with the token and 5000-char response
- Then: The endpoint returns success, the message record body contains the full 5000-character response
- Data: response_text = "a" * 5000

edge_cases:
  - Token lookup returns multiple rows (should not happen due to unique index, but validate gracefully)
  - Response text contains special characters, Unicode, or HTML markup (should be stored as-is, no XSS in response rendering)
  - Token is valid but the linked followup_id no longer exists in action_followups (CASCADE delete scenario)
  - Token generated just before the 72h boundary — concurrent request during expiry transition
  - Multiple assignment emails for the same follow-up (resend) — each gets its own independent token
  - Response submitted from a different IP/device than the one that received the email (valid — token is the auth)
  - Very long assigner name or note in the context response (frontend should handle graceful truncation)
  - Concurrent responses to the same follow-up from different tokens (each token is independent)
  - Frontend navigates to the response page with a valid token but the API server is unreachable
  - Browser back-button after successful submission (should show success state, not re-submit)

error_scenarios:
  - Supabase unavailable during token generation (generate_token failure)
  - Supabase unavailable during token validation (validate_token failure)
  - Supabase unavailable during message insert (response submission failure)
  - Supabase unavailable during status update (partial success — message created but status not updated)
  - Network timeout on GET /context from frontend
  - Network timeout on POST /respond from frontend
  - Token validation passes but followup_id references a deleted action_followup (FK cascade)
  - Concurrent token mark_used race condition (two requests with same token simultaneously)
  - API returns unexpected response format (frontend error handling)
  - Frontend JavaScript disabled (form should still have basic HTML form action or show graceful degradation)

test_file_mapping:
  - 15-3-response-capture-via-token-link-UNIT-001 to UNIT-007, UNIT-013 to UNIT-015: apps/api/app/tests/services/email_service/test_tokens.py
  - 15-3-response-capture-via-token-link-UNIT-008 to UNIT-010: apps/api/app/tests/schemas/test_followup_schemas.py
  - 15-3-response-capture-via-token-link-UNIT-011 to UNIT-012: apps/api/app/tests/services/email_service/test_templates.py
  - 15-3-response-capture-via-token-link-INT-001 to INT-003, INT-009 to INT-026: apps/api/app/tests/api/test_followups_respond.py
  - 15-3-response-capture-via-token-link-INT-004 to INT-008, INT-010 to INT-012: apps/api/app/tests/api/test_followups_respond.py
  - 15-3-response-capture-via-token-link-INT-022: apps/api/app/tests/services/email_service/test_notification_service.py
  - 15-3-response-capture-via-token-link-INT-023 to INT-024: apps/api/app/tests/migrations/test_response_tokens_migration.py
  - 15-3-response-capture-via-token-link-E2E-001 to E2E-008: apps/web/src/app/followups/__tests__/respond-page.test.tsx

TEST SPEC END
