TEST SPEC START
story_id: 15-2-email-notification-service
generated: 2026-02-11

test_specifications:

## AC1: Email sent on follow-up assignment
Given a follow-up is created via the Assign Follow-Up dialog, when the assignment is saved to the database, then an email is sent to the assignee within 60 seconds containing the correct subject, body with action details, and a followup_messages record is created with direction='outbound', message_type='assignment'.

### 15-2-email-notification-service-UNIT-001: SMTPEmailProvider sends email successfully via aiosmtplib
- Priority: P0
- Type: unit
- Given: SMTP credentials are configured and aiosmtplib connection is mocked to succeed
- When: SMTPEmailProvider.send() is called with a valid recipient, subject, HTML body, and plain text body
- Then: aiosmtplib.send() is called with the correctly constructed email.message.EmailMessage (multipart/alternative with text/plain and text/html parts), and SendResult is returned with success=True, error=None, and sent_at populated with current timestamp
- Data: recipient="assignee@example.com", subject="[Action Required] safety - Pump-101: Replace bearing", html_body="<html>...</html>", text_body="Plain text version"

### 15-2-email-notification-service-UNIT-002: SMTPEmailProvider sets correct email headers and From address
- Priority: P1
- Type: unit
- Given: SMTP is configured with smtp_from="noreply@plant.com"
- When: SMTPEmailProvider.send() is called
- Then: The constructed EmailMessage has From set to smtp_from, To set to recipient, Subject set to the provided subject, and MIME type is multipart/alternative
- Data: smtp_from="noreply@plant.com", recipient="user@example.com"

### 15-2-email-notification-service-UNIT-003: SMTPEmailProvider connects with TLS when smtp_use_tls is True
- Priority: P1
- Type: unit
- Given: smtp_use_tls=True in settings and aiosmtplib is mocked
- When: SMTPEmailProvider.send() is called
- Then: aiosmtplib SMTP connection is created with use_tls=True or STARTTLS is initiated, and the connection uses the configured smtp_host and smtp_port
- Data: smtp_host="smtp.office365.com", smtp_port=587, smtp_use_tls=True

### 15-2-email-notification-service-UNIT-004: SMTPEmailProvider connects without TLS when smtp_use_tls is False
- Priority: P2
- Type: unit
- Given: smtp_use_tls=False in settings and aiosmtplib is mocked
- When: SMTPEmailProvider.send() is called
- Then: aiosmtplib SMTP connection is created without TLS/STARTTLS
- Data: smtp_use_tls=False

### 15-2-email-notification-service-UNIT-005: SMTPEmailProvider respects connection timeout
- Priority: P1
- Type: unit
- Given: aiosmtplib is mocked and configured with a 10s default timeout
- When: SMTPEmailProvider.send() is called
- Then: The SMTP connection is opened with timeout=10 (or the configured timeout value)
- Data: timeout=10

### 15-2-email-notification-service-UNIT-006: SMTPEmailProvider returns failure SendResult on SMTP error
- Priority: P0
- Type: unit
- Given: aiosmtplib.send() is mocked to raise an aiosmtplib.SMTPException("Connection refused")
- When: SMTPEmailProvider.send() is called
- Then: SendResult is returned with success=False, error containing "Connection refused", and sent_at=None; no exception is propagated
- Data: Mocked SMTPException

### 15-2-email-notification-service-UNIT-007: SMTPEmailProvider returns failure SendResult on network timeout
- Priority: P1
- Type: unit
- Given: aiosmtplib connection is mocked to raise asyncio.TimeoutError
- When: SMTPEmailProvider.send() is called
- Then: SendResult is returned with success=False, error describing the timeout, and sent_at=None
- Data: Mocked TimeoutError

### 15-2-email-notification-service-UNIT-008: render_assignment_email produces correct subject line format
- Priority: P0
- Type: unit
- Given: Follow-up data with category="safety", asset_name="Pump-101", action_summary="Replace bearing"
- When: render_assignment_email() is called with this data
- Then: The returned subject equals "[Action Required] safety - Pump-101: Replace bearing"
- Data: category="safety", asset_name="Pump-101", action_summary="Replace bearing"

### 15-2-email-notification-service-UNIT-009: render_assignment_email HTML body contains all required fields
- Priority: P0
- Type: unit
- Given: Follow-up data with recommendation="Replace worn bearing immediately", evidence_summary="Vibration levels exceeded threshold 3x in past week", financial_impact="$15,000 estimated repair cost", assigner_name="John Manager", note="Please prioritize this week", followup_id="uuid-123", category="safety", asset_name="Pump-101"
- When: render_assignment_email() is called with this data
- Then: The returned HTML body contains all of: recommendation text, evidence summary, financial impact, assigner name ("Assigned by John Manager"), the optional note, category, asset name, and a "Respond" button/link with href containing "/followups/uuid-123/respond"
- Data: All fields listed above

### 15-2-email-notification-service-UNIT-010: render_assignment_email includes Respond button with correct URL
- Priority: P0
- Type: unit
- Given: app_base_url="https://plant.example.com" and followup_id="abc-123-def"
- When: render_assignment_email() is called
- Then: The HTML body contains an anchor tag or button with href="https://plant.example.com/followups/abc-123-def/respond"
- Data: app_base_url="https://plant.example.com", followup_id="abc-123-def"

### 15-2-email-notification-service-UNIT-011: render_assignment_email produces plain-text fallback
- Priority: P1
- Type: unit
- Given: Follow-up data with all required fields populated
- When: render_assignment_email() is called
- Then: The returned result includes a plain-text version containing the action details (recommendation, evidence, financial impact, assigner, note) in readable text format without HTML tags
- Data: Same as UNIT-009

### 15-2-email-notification-service-UNIT-012: render_assignment_email uses Industrial Clarity color scheme
- Priority: P2
- Type: unit
- Given: Follow-up data with required fields
- When: render_assignment_email() is called
- Then: The HTML body includes inline styles with dark background header (#1a1a2e), white content area (#ffffff or white), and blue CTA button (#3b82f6)
- Data: Standard follow-up data

### 15-2-email-notification-service-UNIT-013: render_assignment_email handles missing optional fields gracefully
- Priority: P1
- Type: unit
- Given: Follow-up data with note=None and financial_impact=None
- When: render_assignment_email() is called
- Then: The HTML body renders without errors, does not show "None" text for missing fields, and still includes all required fields (recommendation, evidence, assigner, Respond link)
- Data: note=None, financial_impact=None, all other required fields present

### 15-2-email-notification-service-UNIT-014: FollowUpNotificationService creates followup_messages record on successful send
- Priority: P0
- Type: unit
- Given: EmailProvider.send() is mocked to return SendResult(success=True, sent_at=<timestamp>), and Supabase client is mocked
- When: send_assignment_notification() is called with valid follow-up data
- Then: A record is inserted into followup_messages with: followup_id matching the created follow-up, direction='outbound', message_type='assignment', sender_id=assigner's UUID, sender_email=assigner's email, subject matching the rendered subject, sent_at=<timestamp>, and failed_at=None
- Data: followup_id="uuid-followup-1", sender_id="uuid-assigner-1", sender_email="manager@plant.com"

### 15-2-email-notification-service-UNIT-015: FollowUpNotificationService resolves assignee email from auth.users
- Priority: P0
- Type: unit
- Given: assigned_to="uuid-user-456" and Supabase service role client is mocked to return user with email="assignee@plant.com"
- When: send_assignment_notification() is called
- Then: The email is sent to "assignee@plant.com" (resolved from auth.users by UUID), not to any hardcoded or passed-in email
- Data: assigned_to UUID="uuid-user-456", resolved email="assignee@plant.com"

### 15-2-email-notification-service-UNIT-016: FollowUpNotificationService never raises exceptions
- Priority: P0
- Type: unit
- Given: An unexpected exception (e.g., RuntimeError) occurs during email send or followup_messages insert
- When: send_assignment_notification() is called
- Then: The exception is caught and logged, the method completes without raising, and the calling code is not affected
- Data: Mocked RuntimeError during send

### 15-2-email-notification-service-INT-001: POST /api/v1/followups creates follow-up record and returns it
- Priority: P0
- Type: integration
- Given: An authenticated user with valid JWT, Supabase client mocked for action_followups insert, and notification service mocked
- When: POST /api/v1/followups is called with valid body containing action_item_id, action_summary, asset_name, category, assigned_to, note, report_date
- Then: The endpoint returns 201 with the created follow-up record including id, status="assigned", created_at, and all submitted fields; the action_followups insert is called with assigned_by set to the authenticated user's ID
- Data: { "action_item_id": "AI-001", "action_summary": "Replace bearing", "asset_name": "Pump-101", "category": "safety", "assigned_to": "uuid-assignee", "note": "Priority this week", "report_date": "2026-02-10" }

### 15-2-email-notification-service-INT-002: POST /api/v1/followups triggers async email notification
- Priority: P0
- Type: integration
- Given: An authenticated user, Supabase insert succeeds, and FollowUpNotificationService.send_assignment_notification is mocked
- When: POST /api/v1/followups is called with valid data
- Then: asyncio.create_task() is called to dispatch the notification asynchronously (fire-and-forget), and the API response is returned without waiting for email delivery
- Data: Standard valid follow-up creation payload

### 15-2-email-notification-service-INT-003: POST /api/v1/followups requires authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: POST /api/v1/followups is called
- Then: The endpoint returns 401 Unauthorized
- Data: No auth header

### 15-2-email-notification-service-INT-004: POST /api/v1/followups validates required fields
- Priority: P1
- Type: integration
- Given: An authenticated user
- When: POST /api/v1/followups is called with missing required fields (e.g., missing action_item_id or assigned_to)
- Then: The endpoint returns 422 Unprocessable Entity with validation error details
- Data: { "note": "Missing required fields" } (incomplete payload)

### 15-2-email-notification-service-INT-005: POST /api/v1/followups validates category enum
- Priority: P1
- Type: integration
- Given: An authenticated user
- When: POST /api/v1/followups is called with category="invalid_category"
- Then: The endpoint returns 422 with validation error indicating invalid category value
- Data: { ...valid fields, "category": "invalid_category" }

### 15-2-email-notification-service-E2E-001: Full assignment flow creates follow-up, sends email, and logs message
- Priority: P0
- Type: e2e
- Given: SMTP is configured, an authenticated user exists, an assignee user exists in auth.users with a valid email, and the database is accessible
- When: A follow-up assignment is created via POST /api/v1/followups with all required fields
- Then: (1) A record is created in action_followups with status='assigned', (2) An email is sent to the assignee with subject "[Action Required] {category} - {asset_name}: {action_summary}" and body containing action details, assigner name, note, and Respond link, (3) A record is created in followup_messages with direction='outbound', message_type='assignment', sent_at populated, and failed_at=NULL, (4) The email is dispatched within 60 seconds of the API call
- Data: Full follow-up data with all fields including category="oee", asset_name="Conveyor-7", action_summary="Adjust belt tension"

## AC2: Graceful degradation when SMTP not configured
Given the email provider is not configured (no SMTP credentials), when a follow-up is assigned, then the assignment is still saved successfully, and a warning is logged that email notification could not be sent, and the system does not block the assignment.

### 15-2-email-notification-service-UNIT-017: smtp_configured returns False when SMTP fields are empty
- Priority: P0
- Type: unit
- Given: Settings instance with smtp_host="", smtp_port=0, smtp_user="", smtp_password=""
- When: The smtp_configured property is accessed
- Then: It returns False
- Data: All SMTP env vars unset or empty strings

### 15-2-email-notification-service-UNIT-018: smtp_configured returns True when all SMTP fields are populated
- Priority: P0
- Type: unit
- Given: Settings instance with smtp_host="smtp.office365.com", smtp_port=587, smtp_user="user@plant.com", smtp_password="secret", smtp_from="noreply@plant.com"
- When: The smtp_configured property is accessed
- Then: It returns True
- Data: All required SMTP fields populated

### 15-2-email-notification-service-UNIT-019: smtp_configured returns False when partial SMTP fields are set
- Priority: P1
- Type: unit
- Given: Settings instance with smtp_host="smtp.office365.com" but smtp_password="" (partially configured)
- When: The smtp_configured property is accessed
- Then: It returns False (all required fields must be non-empty)
- Data: smtp_host set, smtp_password empty

### 15-2-email-notification-service-UNIT-020: FollowUpNotificationService logs warning and returns early when SMTP not configured
- Priority: P0
- Type: unit
- Given: smtp_configured returns False and logger is mocked
- When: send_assignment_notification() is called with valid follow-up data
- Then: A warning is logged containing message about email notification not being sent due to SMTP not configured, the method returns without attempting to send email, and no followup_messages record is created
- Data: Standard follow-up data, SMTP unconfigured

### 15-2-email-notification-service-INT-006: POST /api/v1/followups succeeds and saves follow-up when SMTP is not configured
- Priority: P0
- Type: integration
- Given: An authenticated user, SMTP is not configured (smtp_configured=False), and Supabase insert is mocked to succeed
- When: POST /api/v1/followups is called with valid follow-up data
- Then: The endpoint returns 201 with the created follow-up record, the assignment is persisted in action_followups, and the response is not blocked by the email notification failure; a warning is logged
- Data: Standard valid follow-up payload

### 15-2-email-notification-service-E2E-002: Follow-up assignment succeeds without email when SMTP credentials are absent
- Priority: P0
- Type: e2e
- Given: No SMTP environment variables are configured (smtp_host, smtp_user, smtp_password are all empty), an authenticated user and assignee exist
- When: A follow-up is assigned via POST /api/v1/followups
- Then: (1) The follow-up is saved in action_followups with status='assigned', (2) No email is sent, (3) A warning-level log entry is created indicating email could not be sent, (4) The API response is 201 with the created follow-up, (5) No followup_messages record is created for the notification
- Data: Standard follow-up data, no SMTP config

## AC3: Graceful failure on send error
Given the email send fails (network error, invalid address), when the notification is attempted, then the failure is logged with error details, and the follow-up assignment is not rolled back, and the followup_messages record is created with a failed_at indicator.

### 15-2-email-notification-service-UNIT-021: FollowUpNotificationService creates followup_messages with failed_at on email send failure
- Priority: P0
- Type: unit
- Given: EmailProvider.send() is mocked to return SendResult(success=False, error="Connection refused", sent_at=None), and Supabase client is mocked
- When: send_assignment_notification() is called with valid follow-up data
- Then: A record is inserted into followup_messages with: direction='outbound', message_type='assignment', sent_at=None, and failed_at set to a current timestamp (not None)
- Data: followup_id="uuid-followup-2", mocked email failure

### 15-2-email-notification-service-UNIT-022: FollowUpNotificationService logs error details on send failure
- Priority: P0
- Type: unit
- Given: EmailProvider.send() returns SendResult(success=False, error="Invalid recipient address"), and logger is mocked
- When: send_assignment_notification() is called
- Then: An error-level log entry is created containing the error details ("Invalid recipient address"), the followup_id, and the recipient email address
- Data: Mocked email failure with error="Invalid recipient address"

### 15-2-email-notification-service-UNIT-023: FollowUpNotificationService does not propagate send failure to caller
- Priority: P0
- Type: unit
- Given: EmailProvider.send() raises an unexpected exception (e.g., ConnectionResetError)
- When: send_assignment_notification() is called
- Then: The method catches the exception, logs it, and returns without raising; the calling code (API endpoint) is unaffected
- Data: Mocked ConnectionResetError during email send

### 15-2-email-notification-service-UNIT-024: FollowUpNotificationService handles followup_messages insert failure gracefully
- Priority: P1
- Type: unit
- Given: Email send succeeds but the Supabase insert into followup_messages raises an exception
- When: send_assignment_notification() is called
- Then: The exception is caught and logged, and the method does not raise; the follow-up assignment (already persisted) is not affected
- Data: Mocked Supabase insert failure

### 15-2-email-notification-service-INT-007: POST /api/v1/followups does not roll back follow-up when email fails
- Priority: P0
- Type: integration
- Given: An authenticated user, Supabase action_followups insert succeeds, but FollowUpNotificationService encounters an email send failure
- When: POST /api/v1/followups is called with valid data
- Then: The endpoint returns 201 with the created follow-up record, the action_followups record is persisted (not rolled back), and the email failure is handled asynchronously without affecting the response
- Data: Standard follow-up payload, mocked email failure

### 15-2-email-notification-service-INT-008: followup_messages record has failed_at when email send errors
- Priority: P0
- Type: integration
- Given: SMTP is configured, Supabase is mocked, EmailProvider.send() returns failure
- When: The notification service processes an assignment notification
- Then: A followup_messages record is created with direction='outbound', message_type='assignment', sent_at=NULL, failed_at=<current timestamp>, and the error is logged
- Data: Mocked SMTP failure scenario

### 15-2-email-notification-service-E2E-003: Email failure preserves follow-up and creates failed message record
- Priority: P0
- Type: e2e
- Given: SMTP is configured but the SMTP server is unreachable (connection refused or timeout), an authenticated user and assignee exist
- When: A follow-up is assigned via POST /api/v1/followups
- Then: (1) The follow-up is saved in action_followups with status='assigned', (2) A followup_messages record is created with direction='outbound', message_type='assignment', sent_at=NULL, failed_at set to failure timestamp, (3) The error is logged with details, (4) The API response is 201 with the created follow-up (not rolled back)
- Data: Standard follow-up data, SMTP configured but server unreachable

## Cross-Cutting: Data Model and Schema Validations

### 15-2-email-notification-service-UNIT-025: SendResult dataclass correctly represents success
- Priority: P1
- Type: unit
- Given: A successful email send scenario
- When: SendResult is constructed with success=True, error=None, sent_at=datetime.utcnow()
- Then: success is True, error is None, sent_at is a valid datetime
- Data: success=True

### 15-2-email-notification-service-UNIT-026: SendResult dataclass correctly represents failure
- Priority: P1
- Type: unit
- Given: A failed email send scenario
- When: SendResult is constructed with success=False, error="Connection timeout", sent_at=None
- Then: success is False, error is "Connection timeout", sent_at is None
- Data: success=False, error="Connection timeout"

### 15-2-email-notification-service-UNIT-027: get_email_service factory returns singleton
- Priority: P1
- Type: unit
- Given: The email service module is initialized
- When: get_email_service() is called multiple times
- Then: The same SMTPEmailProvider instance is returned each time (singleton pattern)
- Data: None

### 15-2-email-notification-service-UNIT-028: get_notification_service factory returns singleton
- Priority: P1
- Type: unit
- Given: The email service module is initialized
- When: get_notification_service() is called multiple times
- Then: The same FollowUpNotificationService instance is returned each time
- Data: None

### 15-2-email-notification-service-UNIT-029: FollowUpCreateRequest schema validates category enum
- Priority: P1
- Type: unit
- Given: A FollowUpCreateRequest Pydantic model
- When: Constructed with category="invalid"
- Then: A ValidationError is raised indicating category must be one of 'safety', 'oee', 'financial'
- Data: category="invalid"

### 15-2-email-notification-service-UNIT-030: FollowUpCreateRequest schema accepts valid payload
- Priority: P1
- Type: unit
- Given: A FollowUpCreateRequest Pydantic model
- When: Constructed with all valid fields: action_item_id="AI-001", action_summary="Replace bearing", asset_name="Pump-101", category="safety", assigned_to="uuid", report_date="2026-02-10"
- Then: The model is constructed without errors and all fields match the inputs
- Data: Complete valid payload

### 15-2-email-notification-service-UNIT-031: SMTPEmailProvider handles authentication with username/password
- Priority: P1
- Type: unit
- Given: SMTP is configured with smtp_user="user@plant.com" and smtp_password="secret", aiosmtplib is mocked
- When: SMTPEmailProvider.send() is called
- Then: The SMTP connection authenticates with the configured username and password via login()
- Data: smtp_user="user@plant.com", smtp_password="secret"

### 15-2-email-notification-service-UNIT-032: FollowUpNotificationService handles assignee not found in auth.users
- Priority: P1
- Type: unit
- Given: assigned_to UUID does not exist in auth.users (Supabase returns None/empty)
- When: send_assignment_notification() is called
- Then: An error is logged indicating the assignee could not be found, no email is sent, and the method returns without raising
- Data: assigned_to="nonexistent-uuid"

### 15-2-email-notification-service-INT-009: POST /api/v1/followups sets assigned_by from JWT
- Priority: P0
- Type: integration
- Given: An authenticated user with JWT sub="uuid-manager-123"
- When: POST /api/v1/followups is called
- Then: The action_followups insert includes assigned_by="uuid-manager-123" extracted from the authenticated user's JWT
- Data: JWT sub="uuid-manager-123"

### 15-2-email-notification-service-INT-010: Migration 0031 adds failed_at column to followup_messages
- Priority: P0
- Type: integration
- Given: The followup_messages table exists from migration 0030
- When: Migration 0031_followup_messages_failed_at.sql is applied
- Then: The followup_messages table has a new failed_at column of type TIMESTAMPTZ, nullable, defaulting to NULL
- Data: SQL migration file

edge_cases:
  - Assignee email is empty or malformed in auth.users (should not crash, log error)
  - Very long action_summary or recommendation text in email body (should not truncate or crash)
  - Unicode/special characters in note, asset_name, or action_summary fields
  - Concurrent follow-up assignments to the same user (each should generate independent emails)
  - SMTP server accepts connection but rejects email (e.g., relay denied, mailbox full)
  - app_base_url has trailing slash vs no trailing slash (Respond link should be well-formed either way)
  - Follow-up with NULL asset_name (schema allows NULL) — subject line and email should render gracefully
  - Follow-up with NULL note — email should not show a "Note:" section
  - SMTP configured but smtp_from is empty — should be caught by smtp_configured check

error_scenarios:
  - SMTP connection timeout (server unreachable)
  - SMTP authentication failure (wrong credentials)
  - SMTP TLS/STARTTLS handshake failure
  - DNS resolution failure for SMTP host
  - Invalid recipient email address (SMTP rejection)
  - Supabase service unavailable during followup_messages insert
  - Supabase auth.users lookup returns error
  - aiosmtplib raises unexpected exception type
  - asyncio.create_task() called after event loop closed (edge case during shutdown)
  - Email body rendering raises template error (missing required template variable)

test_file_mapping:
  - 15-2-email-notification-service-UNIT-001 to UNIT-007, UNIT-025 to UNIT-027, UNIT-031: apps/api/app/tests/services/email/test_provider.py
  - 15-2-email-notification-service-UNIT-008 to UNIT-013: apps/api/app/tests/services/email/test_templates.py
  - 15-2-email-notification-service-UNIT-014 to UNIT-016, UNIT-020 to UNIT-024, UNIT-028, UNIT-032: apps/api/app/tests/services/email/test_notification_service.py
  - 15-2-email-notification-service-UNIT-017 to UNIT-019: apps/api/tests/test_config_smtp.py
  - 15-2-email-notification-service-UNIT-029 to UNIT-030: apps/api/tests/models/test_followup_schemas.py
  - 15-2-email-notification-service-INT-001 to INT-009: apps/api/app/tests/api/test_followups.py
  - 15-2-email-notification-service-INT-010: apps/api/app/tests/services/email/test_migration.py
  - 15-2-email-notification-service-E2E-001 to E2E-003: apps/api/app/tests/api/test_followups_e2e.py

TEST SPEC END
