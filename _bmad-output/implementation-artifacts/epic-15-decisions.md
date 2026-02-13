# Epic 15 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 15
**Started:** 2026-02-11 21:04:12

---


## DESIGN: 15-1-followup-messages-data-model
**Timestamp:** 2026-02-11 21:07:42

DESIGN START
story_id: 15-1-followup-messages-data-model

files_to_modify:
  - path: supabase/migrations/0030_followup_messages.sql
    action: create
    purpose: Create the followup_messages table, indexes, and RLS policies in a single migration file

patterns_to_use:
  - UUID PK with gen_random_uuid(): Same pattern as 0025_action_followups.sql and 0011_handoff_acknowledgments.sql
  - ON DELETE CASCADE FK: Same pattern as action_followups.assigned_to/assigned_by FKs
  - CHECK constraint for enum columns: Same pattern as action_followups.status and action_followups.category
  - Single-column indexes: Same naming convention as idx_action_followups_assigned_to etc.
  - EXISTS subquery RLS: Same pattern as 0011_handoff_acknowledgments.sql acknowledgments_select policy (cross-table access check via EXISTS)
  - Service role FOR ALL policy: Same pattern as 0025_action_followups.sql
  - No DELETE/UPDATE policies for authenticated: Append-only audit trail, same concept as audit_logs in 0011
  - Standard CREATE TABLE (no IF NOT EXISTS): Consistent with 0025_action_followups.sql which uses plain CREATE TABLE

dependencies:
  - supabase/migrations/0025_action_followups.sql: must-run-first (provides action_followups table as FK target)
  - auth.users: built-in Supabase table (FK target for sender_id)
  - gen_random_uuid(): provided by pgcrypto or pg extension enabled in 0001_enable_extensions.sql

acceptance_criteria_mapping:
  - AC1: supabase/migrations/0030_followup_messages.sql — CREATE TABLE statement with all 10 columns (id, followup_id, sender_id, sender_email, direction, message_type, subject, body, sent_at, created_at), proper types, defaults, FK constraints, and CHECK constraints
  - AC2: supabase/migrations/0030_followup_messages.sql — Three CREATE INDEX statements: idx_followup_messages_followup_id, idx_followup_messages_direction, idx_followup_messages_sent_at
  - AC3: supabase/migrations/0030_followup_messages.sql — ALTER TABLE ENABLE ROW LEVEL SECURITY + 3 policies: SELECT (EXISTS on action_followups checking assigned_to/assigned_by), INSERT (same EXISTS check), service_role FOR ALL. No DELETE or UPDATE policies for authenticated.
  - AC4: supabase/migrations/0030_followup_messages.sql — followup_id column definition includes REFERENCES action_followups(id) ON DELETE CASCADE
  - AC5: supabase/migrations/0030_followup_messages.sql — File named 0030_followup_messages.sql (next after 0029), uses standard CREATE TABLE without IF NOT EXISTS, matching 0025 pattern

risks:
  - Migration ordering: 0030 is the next available number after 0029_downtime_events.sql — confirmed no conflict. If another story creates 0030 concurrently, a renumber will be needed.
  - RLS performance on EXISTS subquery: The SELECT/INSERT policies join to action_followups on followup_id. The FK index on followup_messages.followup_id plus the PK index on action_followups.id make this efficient. No mitigation needed.
  - sender_id FK to auth.users without ON DELETE CASCADE: If a Supabase auth user is deleted, messages with that sender_id will fail the FK constraint. This is acceptable — user deletion should be rare and messages should persist. The nullable FK means the constraint only applies when sender_id IS NOT NULL.
  - No UPDATE policy means message corrections require service_role: This is intentional per the story (append-only audit trail). If a message needs correction, a new message should be sent. No mitigation needed — this is by design.

estimated_test_files:
  - No test files: This is a pure SQL migration story. Verification is done via SQL comments at the end of the migration file (following 0012 pattern) and manual/CI migration run. Stories 15.2-15.4 will add application-level tests that exercise this table.

implementation_order:
  1. Create file supabase/migrations/0030_followup_messages.sql with header comment block (story reference, date, purpose)
  2. Write CREATE TABLE followup_messages with all 10 columns: id (UUID PK DEFAULT gen_random_uuid()), followup_id (UUID NOT NULL REFERENCES action_followups(id) ON DELETE CASCADE), sender_id (UUID REFERENCES auth.users(id) — nullable), sender_email (TEXT NOT NULL), direction (TEXT NOT NULL CHECK IN ('outbound','inbound')), message_type (TEXT NOT NULL CHECK IN ('assignment','response','escalation','status_update')), subject (TEXT), body (TEXT), sent_at (TIMESTAMPTZ), created_at (TIMESTAMPTZ DEFAULT NOW())
  3. Write three CREATE INDEX statements: idx_followup_messages_followup_id on (followup_id), idx_followup_messages_direction on (direction), idx_followup_messages_sent_at on (sent_at)
  4. Write ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY
  5. Write SELECT policy using EXISTS subquery joining action_followups on followup_id checking assigned_to = auth.uid() OR assigned_by = auth.uid()
  6. Write INSERT policy using same EXISTS subquery pattern as SELECT
  7. Write service_role FOR ALL policy with USING (true) WITH CHECK (true)
  8. Add verification SQL comments at the end of the file (table exists, column types, indexes exist, RLS enabled, policies exist)
DESIGN END

---

## TEST_SPEC: 15-1-followup-messages-data-model
**Timestamp:** 2026-02-11 21:10:29

TEST SPEC START
story_id: 15-1-followup-messages-data-model
generated: 2026-02-11

test_specifications:

## AC1: Table exists with correct schema

### 15-1-followup-messages-data-model-UNIT-001: Migration file exists and is non-empty
- Priority: P0
- Type: unit
- Given: The migration file 0030_followup_messages.sql has been created
- When: The file system is checked for the migration file at supabase/migrations/0030_followup_messages.sql
- Then: The file exists at the expected path and has non-empty content
- Data: File path: supabase/migrations/0030_followup_messages.sql

### 15-1-followup-messages-data-model-UNIT-002: Migration creates followup_messages table with standard CREATE TABLE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE TABLE statement
- Then: The migration contains `CREATE TABLE followup_messages` (without IF NOT EXISTS, per AC5)
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-003: Table has id column as UUID PK with gen_random_uuid() default
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the id column definition
- Then: The column is defined as `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-004: Table has followup_id column as UUID NOT NULL FK to action_followups(id) ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the followup_id column definition
- Then: The column is defined as `followup_id UUID NOT NULL REFERENCES action_followups(id) ON DELETE CASCADE`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-005: Table has sender_id column as nullable UUID FK to auth.users(id)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the sender_id column definition
- Then: The column is defined as `sender_id UUID REFERENCES auth.users(id)` without NOT NULL constraint
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-006: Table has sender_email column as TEXT NOT NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the sender_email column definition
- Then: The column is defined as `sender_email TEXT NOT NULL`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-007: Table has direction column with CHECK constraint for outbound/inbound
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the direction column definition
- Then: The column is defined as `direction TEXT NOT NULL CHECK (direction IN ('outbound', 'inbound'))`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-008: Table has message_type column with CHECK constraint for valid types
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the message_type column definition
- Then: The column is defined as `message_type TEXT NOT NULL CHECK (message_type IN ('assignment', 'response', 'escalation', 'status_update'))`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-009: Table has subject column as nullable TEXT
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the subject column definition
- Then: The column is defined as `subject TEXT` without NOT NULL constraint
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-010: Table has body column as nullable TEXT
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the body column definition
- Then: The column is defined as `body TEXT` without NOT NULL constraint
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-011: Table has sent_at column as TIMESTAMPTZ without default
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the sent_at column definition
- Then: The column is defined as `sent_at TIMESTAMPTZ` (or `TIMESTAMP WITH TIME ZONE`) without a DEFAULT
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-012: Table has created_at column as TIMESTAMPTZ with DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the created_at column definition
- Then: The column is defined as `created_at TIMESTAMPTZ DEFAULT NOW()` (or `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`)
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-013: Table does NOT have updated_at column (append-only)
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for an updated_at column
- Then: No `updated_at` column definition exists in the followup_messages CREATE TABLE statement
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-014: Table does NOT have a status or read_at column
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for status or read_at columns in the followup_messages table
- Then: Neither `status` nor `read_at` appear as column definitions in the followup_messages CREATE TABLE block
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-015: Table has exactly 10 columns
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The CREATE TABLE statement is parsed for column definitions
- Then: Exactly 10 columns are defined: id, followup_id, sender_id, sender_email, direction, message_type, subject, body, sent_at, created_at
- Data: N/A

## AC2: Indexes exist for query performance

### 15-1-followup-messages-data-model-UNIT-016: Migration creates index on followup_id
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_followup_messages_followup_id` is created on `followup_messages(followup_id)`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-017: Migration creates index on direction
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_followup_messages_direction` is created on `followup_messages(direction)`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-018: Migration creates index on sent_at
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_followup_messages_sent_at` is created on `followup_messages(sent_at)`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-019: All three required indexes are present
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: All CREATE INDEX statements targeting followup_messages are counted
- Then: At least 3 CREATE INDEX statements exist for the followup_messages table
- Data: N/A

## AC3: RLS policies enforce access control

### 15-1-followup-messages-data-model-UNIT-020: Migration enables RLS on followup_messages
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for RLS enablement
- Then: The statement `ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY` exists
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-021: SELECT policy uses EXISTS subquery joining action_followups
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the SELECT RLS policy
- Then: A policy exists FOR SELECT TO authenticated with a USING clause containing an EXISTS subquery that joins action_followups on followup_id and checks `assigned_to = auth.uid() OR assigned_by = auth.uid()`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-022: INSERT policy uses EXISTS subquery joining action_followups
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the INSERT RLS policy
- Then: A policy exists FOR INSERT TO authenticated with a WITH CHECK clause containing an EXISTS subquery that joins action_followups on followup_id and checks `assigned_to = auth.uid() OR assigned_by = auth.uid()`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-023: Service role has full access policy
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the service_role policy
- Then: A policy exists FOR ALL TO service_role with USING (true) and WITH CHECK (true)
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-024: No DELETE policy exists for authenticated users
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for DELETE policies targeting authenticated role
- Then: No policy contains `FOR DELETE` with `TO authenticated`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-025: No UPDATE policy exists for authenticated users
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for UPDATE policies targeting authenticated role
- Then: No policy contains `FOR UPDATE` with `TO authenticated`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-026: RLS policies are in the same migration file as table creation
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The file is checked for both CREATE TABLE and CREATE POLICY statements
- Then: Both CREATE TABLE followup_messages and all CREATE POLICY statements exist in the same file (0030_followup_messages.sql)
- Data: N/A

## AC4: Foreign key cascades

### 15-1-followup-messages-data-model-UNIT-027: followup_id FK uses ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the followup_id foreign key constraint
- Then: The followup_id column definition includes `REFERENCES action_followups(id) ON DELETE CASCADE`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-028: followup_id FK does NOT use ON DELETE SET NULL
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for SET NULL behavior on followup_id
- Then: No `ON DELETE SET NULL` appears in conjunction with `action_followups(id)`
- Data: N/A

### 15-1-followup-messages-data-model-INT-001: Cascade delete removes associated messages when follow-up is deleted
- Priority: P0
- Type: integration
- Given: A follow-up exists in `action_followups` with id X, and 3 messages exist in `followup_messages` with followup_id = X
- When: The follow-up with id X is deleted from `action_followups`
- Then: All 3 followup_messages rows with followup_id = X are also deleted, and the query returns 0 rows
- Data: Requires a running Supabase instance with service_role access to insert and delete test data

## AC5: Migration is idempotent-safe

### 15-1-followup-messages-data-model-UNIT-029: Migration file uses standard CREATE TABLE (not IF NOT EXISTS)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the CREATE TABLE statement
- Then: The statement is `CREATE TABLE followup_messages` without `IF NOT EXISTS`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-030: Migration file follows naming convention with correct sequence number
- Priority: P0
- Type: unit
- Given: The migration directory is checked for existing migration files
- When: The file name 0030_followup_messages.sql is validated against the sequence
- Then: The migration file is named `0030_followup_messages.sql` and its number (0030) follows after the existing highest migration (0029_downtime_events.sql)
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-031: No other file is created by this story
- Priority: P1
- Type: unit
- Given: The story specifies this is a pure migration story
- When: The migration file is the only artifact
- Then: Only `supabase/migrations/0030_followup_messages.sql` is created; no API code, frontend code, or Pydantic models
- Data: N/A

## SQL Syntax Validation (cross-cutting)

### 15-1-followup-messages-data-model-UNIT-032: Migration SQL has balanced parentheses
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: Open and close parentheses are counted
- Then: The count of `(` equals the count of `)`
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-033: All SQL statements end with semicolons
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: CREATE TABLE, CREATE INDEX, ALTER TABLE, and CREATE POLICY statements are parsed
- Then: Each statement is properly terminated with a semicolon
- Data: N/A

### 15-1-followup-messages-data-model-UNIT-034: Migration does NOT contain updated_at trigger
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for CREATE TRIGGER statements
- Then: No trigger for updating updated_at exists, confirming the append-only design
- Data: N/A

## RLS Integration Tests (require running Supabase)

### 15-1-followup-messages-data-model-INT-002: Assigner can SELECT messages for their follow-up
- Priority: P0
- Type: integration
- Given: User A created a follow-up (assigned_by = User A, assigned_to = User B) and messages exist for that follow-up
- When: User A queries followup_messages filtered by that followup_id
- Then: User A can see all messages in the thread
- Data: Requires two authenticated users, a follow-up record, and message records inserted via service_role

### 15-1-followup-messages-data-model-INT-003: Assignee can SELECT messages for their follow-up
- Priority: P0
- Type: integration
- Given: User A created a follow-up (assigned_by = User A, assigned_to = User B) and messages exist for that follow-up
- When: User B queries followup_messages filtered by that followup_id
- Then: User B can see all messages in the thread
- Data: Requires two authenticated users, a follow-up record, and message records inserted via service_role

### 15-1-followup-messages-data-model-INT-004: Unrelated user cannot SELECT messages for a follow-up
- Priority: P0
- Type: integration
- Given: User A created a follow-up (assigned_by = User A, assigned_to = User B) and messages exist for that follow-up
- When: User C (not assigned_to or assigned_by) queries followup_messages filtered by that followup_id
- Then: User C receives 0 rows (RLS blocks access)
- Data: Requires three authenticated users, a follow-up record, and message records

### 15-1-followup-messages-data-model-INT-005: Assigner can INSERT messages for their follow-up
- Priority: P0
- Type: integration
- Given: User A created a follow-up (assigned_by = User A, assigned_to = User B)
- When: User A inserts a message with followup_id pointing to that follow-up
- Then: The insert succeeds and the message is persisted
- Data: Requires an authenticated user context and an existing follow-up

### 15-1-followup-messages-data-model-INT-006: Assignee can INSERT messages for their follow-up
- Priority: P0
- Type: integration
- Given: User A created a follow-up (assigned_by = User A, assigned_to = User B)
- When: User B inserts a message with followup_id pointing to that follow-up
- Then: The insert succeeds and the message is persisted
- Data: Requires an authenticated user context and an existing follow-up

### 15-1-followup-messages-data-model-INT-007: Unrelated user cannot INSERT messages for a follow-up
- Priority: P0
- Type: integration
- Given: User A created a follow-up (assigned_by = User A, assigned_to = User B)
- When: User C (not assigned_to or assigned_by) attempts to insert a message with that followup_id
- Then: The insert fails or the row is not visible (RLS blocks the operation)
- Data: Requires three authenticated users and an existing follow-up

### 15-1-followup-messages-data-model-INT-008: Authenticated user cannot DELETE messages
- Priority: P0
- Type: integration
- Given: Messages exist in followup_messages for a follow-up assigned to User A
- When: User A attempts to DELETE a message from followup_messages
- Then: The delete fails or affects 0 rows (no DELETE policy exists for authenticated)
- Data: Requires an authenticated user and existing message records

### 15-1-followup-messages-data-model-INT-009: Authenticated user cannot UPDATE messages
- Priority: P0
- Type: integration
- Given: Messages exist in followup_messages for a follow-up assigned to User A
- When: User A attempts to UPDATE the body of a message in followup_messages
- Then: The update fails or affects 0 rows (no UPDATE policy exists for authenticated)
- Data: Requires an authenticated user and existing message records

### 15-1-followup-messages-data-model-INT-010: Service role has full CRUD access
- Priority: P0
- Type: integration
- Given: The service_role connection is used
- When: The service role performs INSERT, SELECT, UPDATE, and DELETE on followup_messages
- Then: All operations succeed without RLS restrictions
- Data: Requires service_role key and test message data

## Constraint Validation (integration)

### 15-1-followup-messages-data-model-INT-011: CHECK constraint rejects invalid direction value
- Priority: P1
- Type: integration
- Given: A valid follow-up exists in action_followups
- When: A message is inserted via service_role with direction = 'invalid_direction'
- Then: The insert fails with a CHECK constraint violation error
- Data: direction: 'invalid_direction'

### 15-1-followup-messages-data-model-INT-012: CHECK constraint rejects invalid message_type value
- Priority: P1
- Type: integration
- Given: A valid follow-up exists in action_followups
- When: A message is inserted via service_role with message_type = 'invalid_type'
- Then: The insert fails with a CHECK constraint violation error
- Data: message_type: 'invalid_type'

### 15-1-followup-messages-data-model-INT-013: NOT NULL constraint rejects null sender_email
- Priority: P1
- Type: integration
- Given: A valid follow-up exists in action_followups
- When: A message is inserted via service_role with sender_email = NULL
- Then: The insert fails with a NOT NULL violation error
- Data: sender_email: null

### 15-1-followup-messages-data-model-INT-014: Nullable sender_id allows insert with null sender_id
- Priority: P1
- Type: integration
- Given: A valid follow-up exists in action_followups
- When: A message is inserted via service_role with sender_id = NULL and a valid sender_email
- Then: The insert succeeds, confirming sender_id is nullable for non-app-user email replies
- Data: sender_id: null, sender_email: 'external@example.com'

### 15-1-followup-messages-data-model-INT-015: FK constraint rejects invalid followup_id
- Priority: P1
- Type: integration
- Given: No follow-up exists with a specific UUID
- When: A message is inserted via service_role with followup_id = non-existent UUID
- Then: The insert fails with a foreign key constraint violation
- Data: followup_id: '00000000-0000-0000-0000-000000000000' (non-existent)

### 15-1-followup-messages-data-model-INT-016: NOT NULL constraint rejects null followup_id
- Priority: P1
- Type: integration
- Given: The followup_messages table exists
- When: A message is inserted via service_role with followup_id = NULL
- Then: The insert fails with a NOT NULL violation error
- Data: followup_id: null

### 15-1-followup-messages-data-model-INT-017: Default gen_random_uuid() generates unique id on insert
- Priority: P1
- Type: integration
- Given: A valid follow-up exists in action_followups
- When: Two messages are inserted via service_role without specifying id
- Then: Both inserts succeed and each row has a unique, non-null UUID id value
- Data: Two message inserts without explicit id

### 15-1-followup-messages-data-model-INT-018: Default NOW() populates created_at on insert
- Priority: P1
- Type: integration
- Given: A valid follow-up exists in action_followups
- When: A message is inserted via service_role without specifying created_at
- Then: The created_at column is automatically populated with the current timestamp (within a few seconds of the insert time)
- Data: Message insert without explicit created_at

edge_cases:
  - Message inserted with sender_id = NULL (external email responder, non-app-user) — validates nullable FK design
  - Message inserted with subject = NULL and body = NULL — validates that both content fields are truly optional
  - Message inserted with sent_at = NULL — validates that sent_at can be null (draft/queued messages not yet sent)
  - Very long body text (10,000+ characters) — validates no implicit length restriction on TEXT columns
  - Multiple messages for the same follow-up with different directions — validates thread ordering capability
  - Follow-up deleted while messages are being queried — validates cascade behavior under concurrent access

error_scenarios:
  - Insert with invalid direction value ('reply') — CHECK constraint violation
  - Insert with invalid message_type value ('notification') — CHECK constraint violation
  - Insert with non-existent followup_id — FK constraint violation
  - Insert with null sender_email — NOT NULL violation
  - Insert with null direction — NOT NULL violation
  - Insert with null message_type — NOT NULL violation
  - Authenticated user attempts DELETE — RLS policy denial (append-only)
  - Authenticated user attempts UPDATE — RLS policy denial (append-only)
  - Unrelated user attempts SELECT on another user's follow-up messages — RLS returns 0 rows
  - Unrelated user attempts INSERT on another user's follow-up — RLS policy denial

test_file_mapping:
  - 15-1-followup-messages-data-model-UNIT-*: supabase/tests/followup-messages-schema.test.ts
  - 15-1-followup-messages-data-model-INT-*: supabase/tests/followup-messages-integration.test.ts

TEST SPEC END

---

## DESIGN: 15-2-email-notification-service
**Timestamp:** 2026-02-11 21:33:31

DESIGN START
story_id: 15-2-email-notification-service

files_to_modify:
  - path: apps/api/app/core/config.py
    action: modify
    purpose: Add SMTP configuration fields (smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, smtp_use_tls) and smtp_configured property, plus app_base_url setting

  - path: apps/api/requirements.txt
    action: modify
    purpose: Add aiosmtplib>=2.0 dependency for async SMTP

  - path: apps/api/app/services/email/__init__.py
    action: create
    purpose: Package init with get_email_service() and get_notification_service() factory functions following voice/__init__.py pattern

  - path: apps/api/app/services/email/provider.py
    action: create
    purpose: EmailProvider Protocol + SMTPEmailProvider implementation using aiosmtplib with SendResult dataclass

  - path: apps/api/app/services/email/templates.py
    action: create
    purpose: render_assignment_email() function producing HTML + plain text email content with Industrial Clarity design

  - path: apps/api/app/services/email/notification_service.py
    action: create
    purpose: FollowUpNotificationService class with send_assignment_notification() orchestrating template rendering, email sending, and followup_messages record creation

  - path: apps/api/app/api/followups.py
    action: create
    purpose: New API router with POST /api/v1/followups endpoint that inserts follow-up and triggers email notification via fire-and-forget asyncio.create_task()

  - path: apps/api/app/schemas/followup.py
    action: create
    purpose: Pydantic request/response models for the new followups endpoint (FollowUpCreateRequest, FollowUpCreateResponse)

  - path: apps/api/app/main.py
    action: modify
    purpose: Import and register the new followups router at prefix="/api/v1/followups"

  - path: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx
    action: modify
    purpose: Replace direct Supabase .from('action_followups').insert() with fetch() call to POST /api/v1/followups API endpoint

  - path: supabase/migrations/0031_followup_messages_failed_at.sql
    action: create
    purpose: Add failed_at TIMESTAMPTZ column to followup_messages table (AC#3 requirement, not in Story 15.1 schema)

  - path: apps/api/app/tests/services/email/__init__.py
    action: create
    purpose: Test package init

  - path: apps/api/app/tests/services/email/test_provider.py
    action: create
    purpose: Unit tests for SMTPEmailProvider.send() with mocked aiosmtplib

  - path: apps/api/app/tests/services/email/test_templates.py
    action: create
    purpose: Unit tests for render_assignment_email() HTML output validation

  - path: apps/api/app/tests/services/email/test_notification_service.py
    action: create
    purpose: Unit tests for FollowUpNotificationService covering success, failure, and SMTP-not-configured scenarios

  - path: apps/api/app/tests/api/test_followups.py
    action: create
    purpose: Integration tests for POST /api/v1/followups endpoint

patterns_to_use:
  - Settings *_configured property: Add smtp_configured property to Settings class following exact pattern of elevenlabs_configured and mssql_configured (returns bool, checks required fields are non-empty)
  - Service factory singleton: Create get_email_service() and get_notification_service() in services/email/__init__.py with global _instance + None check, following get_elevenlabs_client() pattern in services/voice/elevenlabs.py
  - Protocol-based provider abstraction: Define EmailProvider as a Protocol class with async send() method, allowing future swap from SMTP to SendGrid/SES SDK without touching notification_service.py
  - Router with auth dependency: Create router = APIRouter() with Depends(get_current_user) and Depends(security) for JWT extraction, following actions.py update_followup pattern
  - Service-role Supabase client: Use create_client(settings.supabase_url, settings.supabase_key) for inserting followup_messages records and resolving assignee emails from auth.users, following team.py's supabase.auth.admin.get_user_by_id() pattern
  - User-scoped Supabase client: Use create_client(settings.supabase_url, user_token) for inserting into action_followups to respect RLS (assigned_by = auth.uid()), same dual-client pattern as actions.py update_followup
  - Fire-and-forget asyncio.create_task(): Dispatch email notification after database insert without awaiting, wrapping in try/except to never propagate email failures to API response
  - Test pattern with mocks: Follow test_voice_tts.py pattern — MagicMock for service dependencies, @pytest.mark.asyncio for async tests, fixture-based service instantiation

dependencies:
  - aiosmtplib: needs-install (add >=2.0 to requirements.txt)
  - supabase: installed (used for database operations)
  - fastapi: installed (API router)
  - pydantic: installed (request/response schemas)
  - Story 15.1 migration 0030_followup_messages.sql: already implemented (provides followup_messages table)

acceptance_criteria_mapping:
  - AC1 (Email sent on follow-up assignment):
    - apps/api/app/api/followups.py — POST endpoint accepts follow-up data, inserts into action_followups, fires async email task
    - apps/api/app/services/email/templates.py — render_assignment_email() builds subject "[Action Required] {category} - {asset_name}: {action_summary}" and HTML body with all required fields
    - apps/api/app/services/email/notification_service.py — send_assignment_notification() orchestrates template rendering, email send, and followup_messages record creation with direction='outbound', message_type='assignment'
    - apps/api/app/services/email/provider.py — SMTPEmailProvider.send() delivers the email via aiosmtplib
    - apps/web/src/components/action-engine/AssignFollowUpDialog.tsx — updated to POST to API instead of direct Supabase insert

  - AC2 (Graceful degradation when SMTP not configured):
    - apps/api/app/core/config.py — smtp_configured property returns False when SMTP credentials missing
    - apps/api/app/services/email/notification_service.py — send_assignment_notification() checks smtp_configured, logs warning via logger.warning(), returns early without blocking
    - apps/api/app/api/followups.py — follow-up insert succeeds regardless; email notification is fire-and-forget

  - AC3 (Graceful failure on send error):
    - apps/api/app/services/email/notification_service.py — catches email send exceptions, logs error details, creates followup_messages record with failed_at=datetime.utcnow() and sent_at=NULL
    - apps/api/app/services/email/provider.py — SMTPEmailProvider.send() returns SendResult(success=False, error=str(e)) on network/SMTP errors
    - supabase/migrations/0031_followup_messages_failed_at.sql — adds failed_at column to followup_messages
    - apps/api/app/api/followups.py — follow-up insert is NOT rolled back; fire-and-forget pattern isolates email failures from API response

risks:
  - failed_at column not in Story 15.1 schema: The followup_messages table (0030) does not have a failed_at column. Mitigation: Create migration 0031_followup_messages_failed_at.sql to ALTER TABLE ADD COLUMN. This is safe since 15.1 is already implemented.
  - aiosmtplib compatibility: aiosmtplib must be compatible with Python 3.11+ and the existing asyncio event loop. Mitigation: aiosmtplib 2.x is actively maintained and supports Python 3.8+. Pin to >=2.0.
  - Frontend-backend transition: Changing AssignFollowUpDialog from direct Supabase insert to API call changes the data flow. If the API endpoint is down, follow-up creation fails entirely. Mitigation: The frontend already has error handling and displays error messages. The API endpoint should be simple and reliable.
  - RLS impact on user-scoped insert: The action_followups INSERT policy requires assigned_by = auth.uid(). Using the user's JWT token for the Supabase client ensures this RLS check passes naturally. Mitigation: Use the exact dual-client pattern from actions.py.
  - Email delivery timing: AC1 says "within 60 seconds." The fire-and-forget asyncio.create_task() dispatches immediately after DB insert; actual delivery depends on SMTP server latency. Mitigation: Configure 10s SMTP timeout; log timing for monitoring.
  - Migration numbering collision: 0031 might conflict if another story creates a migration between now and implementation. Mitigation: Check migration directory at implementation time and adjust numbering if needed.
  - Respond link without token: Story 15.3 adds token-based response. For now, the "Respond" button links to {app_base_url}/followups/{followup_id}/respond without a token. This is documented in the story as acceptable for MVP.

estimated_test_files:
  - apps/api/app/tests/services/email/test_provider.py: Unit tests for SMTPEmailProvider.send() — mocked aiosmtplib connection, success/failure SendResult, TLS handling, timeout behavior
  - apps/api/app/tests/services/email/test_templates.py: Unit tests for render_assignment_email() — validates HTML contains subject, body fields (category, asset_name, recommendation, evidence, financial_impact, assigner, note, respond link), plain-text fallback
  - apps/api/app/tests/services/email/test_notification_service.py: Unit tests for FollowUpNotificationService — success path creates followup_messages with sent_at; failure path creates with failed_at; smtp_not_configured logs warning and returns; never raises exceptions
  - apps/api/app/tests/api/test_followups.py: Integration tests for POST /api/v1/followups — creates follow-up record, triggers notification, returns created follow-up; email failure doesn't roll back insert

implementation_order:
  1. Add aiosmtplib>=2.0 to apps/api/requirements.txt (Task 7)
  2. Add SMTP configuration fields and smtp_configured property to apps/api/app/core/config.py, plus app_base_url setting (Task 1)
  3. Create migration supabase/migrations/0031_followup_messages_failed_at.sql adding failed_at TIMESTAMPTZ column (prerequisite for AC#3)
  4. Create apps/api/app/services/email/provider.py with EmailProvider Protocol, SendResult dataclass, and SMTPEmailProvider implementation (Task 2)
  5. Create apps/api/app/services/email/templates.py with render_assignment_email() function producing HTML+plaintext (Task 3)
  6. Create apps/api/app/services/email/notification_service.py with FollowUpNotificationService class (Task 4 + Task 6)
  7. Create apps/api/app/services/email/__init__.py with factory functions (Task 2.1)
  8. Create apps/api/app/schemas/followup.py with FollowUpCreateRequest and FollowUpCreateResponse Pydantic models
  9. Create apps/api/app/api/followups.py with POST /api/v1/followups endpoint (Task 5.2)
  10. Register followups router in apps/api/app/main.py (Task 5.3)
  11. Update apps/web/src/components/action-engine/AssignFollowUpDialog.tsx to call the new API endpoint (Task 5.4)
  12. Create test files: test_provider.py, test_templates.py, test_notification_service.py, test_followups.py (Task 8)
  13. Run tests and verify all pass
DESIGN END

---

## DESIGN: 15-3-response-capture-via-token-link
**Timestamp:** 2026-02-11 22:19:19

DESIGN START
story_id: 15-3-response-capture-via-token-link

files_to_modify:
  - path: supabase/migrations/0032_response_tokens.sql
    action: create
    purpose: Add response_token (TEXT), token_expires_at (TIMESTAMPTZ), and token_used_at (TIMESTAMPTZ) columns to followup_messages table. Create unique partial index on response_token WHERE response_token IS NOT NULL for fast token lookup.

  - path: apps/api/app/services/email/tokens.py
    action: create
    purpose: TokenService class with generate_token(followup_id, assignee_email), validate_token(token), and mark_token_used(token). Uses UUID v4 tokens stored on outbound followup_messages records. Validates expiry (72h), used status, and existence. Uses service_role Supabase client since token operations are unauthenticated.

  - path: apps/api/app/api/followups.py
    action: modify
    purpose: Add two PUBLIC endpoints (no auth dependency) to the existing router: POST /respond (accepts {token, response_text}, validates token, creates inbound followup_messages record, updates action_followups status to 'in_progress' if currently 'assigned', marks token used) and GET /{id}/context (accepts token query param, validates token, returns followup context for the frontend form). These endpoints use service_role client.

  - path: apps/api/app/schemas/action.py
    action: modify
    purpose: Add Pydantic models for the public response endpoints: TokenResponseRequest (token: str, response_text: str with max_length=5000 validation), TokenContextResponse (action_summary, asset_name, category, assigned_by_email, assigned_by_name, note, report_date), and TokenResponseResult (success: bool, message: str).

  - path: apps/api/app/services/email/templates.py
    action: modify
    purpose: Update render_assignment_email() to accept an optional response_token parameter. When provided, append ?token={response_token} to the respond_url in both HTML and plain text output. Signature change: add response_token: Optional[str] = None parameter.

  - path: apps/api/app/services/email/notification_service.py
    action: modify
    purpose: Integrate token generation into send_assignment_notification() flow. After resolving assignee email, call TokenService.generate_token(followup_id, assignee_email) to get a token. Pass the token to render_assignment_email() and store it in the followup_messages record's response_token column when creating the outbound message.

  - path: apps/api/app/services/email/__init__.py
    action: modify
    purpose: Export TokenService and add get_token_service() factory function following the existing singleton pattern (global _token_service_instance, lazy-init with service_role Supabase client).

  - path: apps/web/src/app/followups/[id]/respond/page.tsx
    action: create
    purpose: Standalone public page (NOT inside (main) layout, so no auth required). State machine: loading → error-invalid / error-expired / ready → submitting → success. On mount, fetches context from GET /api/v1/followups/{id}/context?token={token}. On submit, POSTs to /api/v1/followups/respond. Uses Shadcn Card, Badge, Textarea, Button, Alert components. Mobile-responsive. Includes TFN branding header. No navigation/sidebar. Disables submit after success to prevent double-submit.

  - path: apps/api/app/tests/services/email_service/test_tokens.py
    action: create
    purpose: Unit tests for TokenService — generate_token returns UUID string and stores in DB, validate_token with valid/expired/used/nonexistent tokens, mark_token_used sets token_used_at. All DB calls mocked.

  - path: apps/api/app/tests/api/test_followups_respond.py
    action: create
    purpose: Unit tests for the public response endpoints — POST /respond with valid token creates message and updates status, expired/invalid/used tokens return correct errors, missing response_text returns 422. GET /context with valid token returns followup context, invalid token returns error. Tests use TestClient with mocked Supabase.

patterns_to_use:
  - Service-role Supabase client for public endpoints: Public endpoints (POST /respond, GET /{id}/context) use create_client(settings.supabase_url, settings.supabase_key) since the user is unauthenticated. Token IS the auth. Follows the service_client pattern from actions.py:526.
  - Singleton factory in __init__.py: get_token_service() follows get_email_service() and get_notification_service() pattern — global _instance variable, lazy init with settings and service_role client. (apps/api/app/services/email/__init__.py:18-49)
  - Router endpoint pattern without auth: The two new public endpoints omit Depends(get_current_user) and Depends(security). This is unique to this story — all other endpoints require auth. Token validation replaces JWT auth.
  - Pydantic request/response models: Follow FollowUpCreateRequest pattern (ConfigDict(extra="forbid"), Field(...) with descriptions, @field_validator for validation). New models in schemas/action.py alongside existing follow-up schemas.
  - Error handling pattern: try/except HTTPException: raise; except Exception: logger.error + raise HTTPException(500). Same pattern as update_followup in actions.py:556-563.
  - Next.js public page routing: Place page.tsx at apps/web/src/app/followups/[id]/respond/page.tsx — outside the (main) route group, so it is NOT wrapped by the auth-requiring MainLayout. The root layout.tsx provides ThemeProvider and basic HTML structure without auth checks.
  - API_BASE_URL pattern: Use process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000' following the established hook pattern (useScheduleUpload.ts:60, useActionAcknowledgment.ts:6, etc.)
  - Migration column addition: ALTER TABLE followup_messages ADD COLUMN pattern following 0031_followup_messages_failed_at.sql precedent.

dependencies:
  - uuid (Python stdlib): installed (used for uuid4() token generation)
  - supabase-py: installed (create_client for DB operations)
  - fastapi: installed (APIRouter, HTTPException, Query, Path)
  - pydantic: installed (BaseModel, Field, field_validator, ConfigDict)
  - aiosmtplib: installed (Story 15.2 dependency, already in requirements.txt)
  - react/next: installed (frontend page)
  - @/components/ui/*: installed (Shadcn UI components: Card, Badge, Textarea, Button, Alert)

acceptance_criteria_mapping:
  - AC1 (Response page renders via token link):
    - apps/web/src/app/followups/[id]/respond/page.tsx — extracts id from route params and token from searchParams, calls GET /api/v1/followups/{id}/context?token={token} on mount, renders context card (action_summary, asset_name, category badge, assigned_by name, note, report_date) and textarea form when token is valid
    - apps/api/app/api/followups.py — GET /{id}/context endpoint validates token via TokenService.validate_token(), fetches action_followups record + assigner details via service_role client, returns context payload
    - apps/api/app/services/email/tokens.py — TokenService.validate_token() checks existence, expiry, and used status
    - supabase/migrations/0032_response_tokens.sql — provides response_token, token_expires_at, token_used_at columns for token storage

  - AC2 (Response submission creates message record):
    - apps/api/app/api/followups.py — POST /respond endpoint: validates token, creates followup_messages record with direction='inbound', message_type='response', sender_email from token lookup, body from request; updates action_followups.status to 'in_progress' if currently 'assigned' (conditional UPDATE with WHERE status='assigned'); marks token used; returns success response
    - apps/api/app/schemas/action.py — TokenResponseRequest model validates token and response_text (non-empty, max 5000 chars)
    - apps/api/app/services/email/tokens.py — TokenService.mark_token_used() sets token_used_at timestamp
    - apps/web/src/app/followups/[id]/respond/page.tsx — submit handler calls POST, shows success confirmation with green checkmark, disables submit button

  - AC3 (Expired token shows expiry message):
    - apps/api/app/services/email/tokens.py — validate_token() returns is_valid=False, error_reason='expired' when token_expires_at < NOW() or token_used_at IS NOT NULL
    - apps/api/app/api/followups.py — GET /{id}/context returns 400 with error_reason='expired'; POST /respond returns 400 with "Token expired" message
    - apps/web/src/app/followups/[id]/respond/page.tsx — renders "This link has expired. Please log in to the app to respond." message with no form when error_reason is 'expired' or 'used'

  - AC4 (Invalid token shows error):
    - apps/api/app/services/email/tokens.py — validate_token() returns is_valid=False, error_reason='invalid' when no row found for token
    - apps/api/app/api/followups.py — GET /{id}/context returns 404 with error_reason='invalid'; POST /respond returns 404 with "Invalid link" message
    - apps/web/src/app/followups/[id]/respond/page.tsx — renders "Invalid link" message with no form when error_reason is 'invalid'

risks:
  - Migration numbering collision: 0032 is the next available after 0031_followup_messages_failed_at.sql. If another concurrent story creates 0032, renumber at implementation time. Mitigation: check migration directory before creating file.
  - Public endpoint security: POST /respond and GET /{id}/context are unauthenticated. Token brute-force is mitigated by UUID v4 (128 bits randomness), 72h expiry, and single-use. Rate limiting is not implemented for MVP but should be added later. Mitigation: document rate limiting as a future enhancement.
  - Token stored on outbound message row: The token is stored on the followup_messages row with direction='outbound', message_type='assignment'. This means there's one token per assignment email. If multiple emails are sent for the same followup (e.g., resend), each has its own token. This is correct behavior.
  - Email template modification: render_assignment_email() signature changes to add response_token parameter. Existing callers (notification_service.py) must be updated simultaneously. Mitigation: parameter is Optional[str] with default None, so existing calls without a token still work during transition.
  - ChatSidebar in root layout: The root layout includes ChatSidebar which may attempt to use auth. The public followup page should not break if ChatSidebar gracefully handles unauthenticated state. Mitigation: verify ChatSidebar handles missing auth gracefully (it likely does since it's wrapped in providers). If not, the followup page can use a separate minimal layout.
  - Status transition logic: The POST /respond endpoint updates action_followups.status to 'in_progress' only if currently 'assigned'. This must be a conditional update (WHERE status='assigned') to prevent regressing from 'in_progress' or 'resolved'. Mitigation: use service_role client with explicit WHERE clause.
  - Double-submit prevention: Frontend disables button after success, but a user could bypass this. Server-side, the token is marked used after first successful response, so subsequent submissions fail with "Token expired" message. This is correct behavior.

estimated_test_files:
  - apps/api/app/tests/services/email_service/test_tokens.py: Unit tests for TokenService — generate_token produces UUID and stores in followup_messages with token_expires_at = now+72h; validate_token returns valid result for fresh token; validate_token returns expired for token with token_expires_at < now; validate_token returns used for token with token_used_at set; validate_token returns invalid for nonexistent token; mark_token_used updates token_used_at timestamp. Uses mocked Supabase client.
  - apps/api/app/tests/api/test_followups_respond.py: Integration tests for public endpoints — POST /respond with valid token creates followup_messages record with correct direction/message_type/sender_email/body; POST /respond updates action_followups.status to 'in_progress' when currently 'assigned'; POST /respond does NOT change status when already 'in_progress' or 'resolved'; POST /respond with expired token returns 400; POST /respond with invalid token returns 404; POST /respond with used token returns 400; POST /respond with empty response_text returns 422; GET /{id}/context with valid token returns context; GET /{id}/context with invalid token returns 404; GET /{id}/context with expired token returns 400. Uses TestClient with mocked Supabase.

implementation_order:
  1. Create migration supabase/migrations/0032_response_tokens.sql — ALTER TABLE followup_messages ADD COLUMN response_token TEXT, token_expires_at TIMESTAMPTZ, token_used_at TIMESTAMPTZ; CREATE UNIQUE INDEX idx_followup_messages_response_token ON followup_messages(response_token) WHERE response_token IS NOT NULL (Task 6)
  2. Create apps/api/app/services/email/tokens.py with TokenService class — generate_token(), validate_token(), mark_token_used() methods. Uses service_role Supabase client. TokenValidationResult dataclass with followup_id, assignee_email, is_valid, error_reason fields (Task 1)
  3. Update apps/api/app/services/email/__init__.py — add TokenService import, get_token_service() factory, update __all__ (Task 1)
  4. Add Pydantic request/response models to apps/api/app/schemas/action.py — TokenResponseRequest, TokenContextResponse, TokenResponseResult (Task 2)
  5. Add public endpoints to apps/api/app/api/followups.py — POST /respond and GET /{id}/context endpoints, both without auth dependencies, using service_role client and TokenService (Tasks 2, 3)
  6. Update apps/api/app/services/email/templates.py — add response_token: Optional[str] = None parameter to render_assignment_email(), append ?token={response_token} to respond_url when token provided (Task 5)
  7. Update apps/api/app/services/email/notification_service.py — in send_assignment_notification(), call TokenService.generate_token() after resolving assignee email, pass token to render_assignment_email(), include response_token in the followup_messages insert dict (Task 5)
  8. Create apps/web/src/app/followups/[id]/respond/page.tsx — standalone public response form page with state machine (loading/error/ready/submitting/success), context card, textarea, submit button, error/success messages (Task 4)
  9. Create apps/api/app/tests/services/email_service/test_tokens.py — unit tests for TokenService (Task 7)
  10. Create apps/api/app/tests/api/test_followups_respond.py — endpoint tests for POST /respond and GET /{id}/context (Task 7)
  11. Run all tests and verify no regressions in existing 15.2 tests (test_followups.py, test_notification_service.py, test_templates.py)
DESIGN END

---

## DESIGN: 15-4-message-thread-ui
**Timestamp:** 2026-02-11 23:02:24

DESIGN START
story_id: 15-4-message-thread-ui

files_to_modify:
  - path: supabase/migrations/0033_followup_last_viewed.sql
    action: create
    purpose: Add `last_viewed_at TIMESTAMPTZ DEFAULT NULL` column to `action_followups` table for server-side unread tracking (replacing client-side localStorage approach)

  - path: apps/api/app/schemas/action.py
    action: modify
    purpose: Add Pydantic response models — `FollowUpMessageResponse` (single message), `FollowUpMessageListResponse` (thread wrapper with followup context, messages array, has_unread, last_viewed_at), and `FollowUpViewedResponse` (success + timestamp)

  - path: apps/api/app/api/followups.py
    action: modify
    purpose: Add two authenticated endpoints — `GET /{followup_id}/messages` (returns chronological messages with sender info, has_unread computation, followup context) and `PATCH /{followup_id}/viewed` (updates last_viewed_at to NOW()). Both use Depends(get_current_user) + service_role client for queries since RLS on followup_messages table already enforces access via EXISTS subquery on action_followups

  - path: apps/web/src/hooks/useFollowUpMessages.ts
    action: create
    purpose: React hook following useDailyActions.ts/useMyFollowUps.ts pattern — fetches from GET /api/v1/followups/{id}/messages, returns typed messages array, loading state, error state, refetch, hasUnread, and a markViewed() function that calls PATCH /api/v1/followups/{id}/viewed

  - path: apps/web/src/components/action-list/MessageThread.tsx
    action: create
    purpose: Chat-style chronological message thread component. Outbound messages right-aligned with muted background, inbound messages left-aligned with card background. Message type badges (Assignment=blue, Response=green, Status Update=gray). Empty state shows "Awaiting response from {assignee_name}" with Clock icon. Loading skeleton state. Uses ScrollArea, Card, Badge from shadcn/ui. ARIA role="log"

  - path: apps/web/src/components/action-list/FollowUpDetailDialog.tsx
    action: modify
    purpose: Integrate MessageThread component into the existing detail dialog. Replace the static read-only view with the message thread below the existing header/metadata. Call useFollowUpMessages hook on open. Call markViewed() on dialog open to update server-side last_viewed_at. Keep existing dialog structure (DialogHeader with asset name + status badge)

  - path: apps/web/src/components/action-list/FollowUpEntry.tsx
    action: modify
    purpose: Replace localStorage-based unread detection with server-side `has_unread` flag. Add has_unread as an optional prop from parent (MyAssignmentsPanel) or compute from the follow-up list data. The existing blue dot indicator UI stays the same but driven by server data instead of localStorage

  - path: apps/web/src/hooks/useMyFollowUps.ts
    action: modify
    purpose: Extend FollowUpItem interface to include optional `has_unread: boolean` field. Update the API endpoint call to include has_unread data if returned by the backend (or add a separate lightweight endpoint call). The existing `/api/v1/actions/followups` endpoint may need extension on the backend side

  - path: apps/api/app/api/actions.py
    action: modify
    purpose: Extend the existing `GET /api/v1/actions/followups` endpoint response to include `has_unread` boolean per follow-up item by joining with followup_messages to check for inbound messages with sent_at > COALESCE(last_viewed_at, '1970-01-01')

  - path: apps/web/src/components/action-list/index.ts
    action: modify
    purpose: Add barrel export for new MessageThread component

  - path: apps/api/app/tests/api/test_followups_messages.py
    action: create
    purpose: Pytest tests for GET /api/v1/followups/{id}/messages and PATCH /api/v1/followups/{id}/viewed endpoints

  - path: apps/web/src/components/action-list/__tests__/MessageThread.test.tsx
    action: create
    purpose: Vitest + Testing Library tests for MessageThread component — renders messages, empty state, loading skeleton, correct alignment by direction

  - path: apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx
    action: modify
    purpose: Add tests for message thread integration in the detail dialog — thread renders on open, markViewed called on open

patterns_to_use:
  - Hook auth pattern (useDailyActions.ts): createClient() → getSession() → Bearer token in Authorization header, mountedRef for unmount safety, error message mapping (401→AUTH_ERROR, 404→NO_DATA), auto-fetch with useEffect
  - API router auth pattern (followups.py): Depends(get_current_user) + Depends(security) for authenticated endpoints, get_service_role_client() for DB queries, try/except HTTPException: raise / except Exception: logger.error + 500
  - Component layout pattern (ActionItemCard.tsx): cn() for conditional classnames, lucide-react icons, Card/Badge/ScrollArea from @/components/ui/, ARIA roles and keyboard accessibility
  - Existing FollowUpEntry indicator pattern: Blue dot 8px circle with data-testid="new-update-indicator", positioned absolute in parent container
  - Dialog integration pattern (FollowUpDetailDialog.tsx): useEffect on `open` prop to trigger side effects, Dialog/DialogContent/DialogHeader from shadcn/ui
  - Test pattern (test_followups.py): TestClient with mocked Supabase (patch create_client), mock_verify_jwt fixture, class-based test grouping by AC
  - Frontend test pattern (FollowUpEntry.test.tsx): vi.mock for next/navigation, Testing Library render/screen/fireEvent, data-testid selectors, mock fixture factories
  - Supabase query pattern (followups.py): service_client.table("table_name").select("...").eq("col", val).order("col").execute()
  - Pydantic schema pattern (action.py): BaseModel with ConfigDict, Field(...) with descriptions, Optional fields with defaults

dependencies:
  - fastapi: installed (API router, HTTPException, Depends)
  - pydantic: installed (BaseModel, Field, ConfigDict)
  - supabase-py: installed (create_client for DB queries)
  - react: installed (hooks, components)
  - @/components/ui/*: installed (Card, Badge, ScrollArea, Dialog)
  - lucide-react: installed (MessageSquare, Send, Clock, Eye, Mail icons)
  - vitest: installed (frontend testing)
  - @testing-library/react: installed (frontend testing)
  - pytest: installed (backend testing)

acceptance_criteria_mapping:
  - AC1 (Chronological message thread display):
    - apps/api/app/api/followups.py — GET /{followup_id}/messages returns messages sorted by sent_at ascending with sender info, direction, message_type, subject, body, timestamps
    - apps/api/app/schemas/action.py — FollowUpMessageResponse and FollowUpMessageListResponse define the response shape
    - apps/web/src/hooks/useFollowUpMessages.ts — fetches and provides typed message data to components
    - apps/web/src/components/action-list/MessageThread.tsx — renders outbound messages right-aligned ("Sent to {assignee} at {time}"), inbound messages left-aligned ("{assignee} replied at {time}"), status updates with timestamps
    - apps/web/src/components/action-list/FollowUpDetailDialog.tsx — integrates MessageThread into the existing detail dialog view

  - AC2 (Unread indicator on follow-up entry):
    - supabase/migrations/0033_followup_last_viewed.sql — adds last_viewed_at column to action_followups
    - apps/api/app/api/followups.py — PATCH /{followup_id}/viewed updates last_viewed_at; GET /{followup_id}/messages computes has_unread server-side
    - apps/api/app/api/actions.py — extends GET /api/v1/actions/followups to include has_unread per item
    - apps/web/src/components/action-list/FollowUpEntry.tsx — displays blue dot when has_unread is true (replacing localStorage-based detection)
    - apps/web/src/hooks/useMyFollowUps.ts — passes has_unread from API response through to components
    - apps/web/src/components/action-list/FollowUpDetailDialog.tsx — calls markViewed() on open to clear unread status

  - AC3 (Empty state when no responses):
    - apps/web/src/components/action-list/MessageThread.tsx — when no inbound messages exist, shows "Awaiting response from {assignee_name}" with Clock icon below the outbound assignment message
    - apps/api/app/api/followups.py — GET /{followup_id}/messages returns messages array (may be only outbound), includes assignee_name in response wrapper for the empty-state label

  - AC4 (Messages API returns chronological messages with correct fields):
    - apps/api/app/api/followups.py — GET /{followup_id}/messages queries followup_messages table joined with action_followups, orders by sent_at ascending, returns id, direction, message_type, sender_email, subject, body, sent_at per message
    - apps/api/app/schemas/action.py — FollowUpMessageResponse model with all required fields; FollowUpMessageListResponse includes followup_id, action_summary, assignee_name, assignee_email, status, messages array, has_unread, last_viewed_at

  - AC5 (RLS enforcement for unauthorized access):
    - apps/api/app/api/followups.py — uses service_role client but validates the current_user is either assigner or assignee before returning data (defense-in-depth alongside DB-level RLS)
    - supabase/migrations/0030_followup_messages.sql — existing RLS SELECT policy on followup_messages already limits access to assigner/assignee via EXISTS subquery
    - apps/api/app/tests/api/test_followups_messages.py — tests that unauthorized users receive 404

risks:
  - Migration numbering collision with 0033: The story spec says 0031, but 0031 and 0032 already exist from stories 15.1-15.3. The next available number is 0033. Mitigation: Use 0033_followup_last_viewed.sql.
  - FollowUpEntry unread transition from localStorage to server-side: The existing FollowUpEntry uses localStorage for "new update" detection. Switching to server-side has_unread requires the parent (MyAssignmentsPanel) to pass the flag. The existing tests in FollowUpEntry.test.tsx mock localStorage — these will need updating. Mitigation: Add has_unread as an optional prop, keep localStorage as fallback for backward compatibility until server data is available.
  - actions.py followups endpoint extension: The GET /api/v1/actions/followups endpoint in actions.py needs to compute has_unread per follow-up by checking followup_messages. This requires an additional subquery or join. Mitigation: Use a LEFT JOIN or correlated subquery on followup_messages checking direction='inbound' AND sent_at > COALESCE(last_viewed_at, '1970-01-01'). If the query becomes complex, compute has_unread client-side by comparing messages data, but server-side is preferred for the list view badge.
  - RLS vs service_role client: The GET /messages endpoint uses service_role client (bypasses RLS) for flexibility in joins. This means access control must be enforced in application code — verify current_user.id matches assigned_to or assigned_by on the action_followups row. Mitigation: Explicit application-level check with 404 response if unauthorized, tested in pytest.
  - FollowUpDetailDialog scope change: The existing FollowUpDetailDialog is a simple read-only display. Adding MessageThread and the useFollowUpMessages hook significantly increases its complexity. Mitigation: MessageThread is a self-contained component; the dialog just renders it and passes the followup_id. Complexity is encapsulated in the hook and thread component.
  - PATCH /viewed race condition: If the user opens a thread, then a new message arrives before the PATCH completes, the new message may be marked as "read" without the user seeing it. Mitigation: Acceptable for MVP — the timing window is very small and the user is actively viewing the thread.

estimated_test_files:
  - apps/api/app/tests/api/test_followups_messages.py: Backend tests — GET /messages returns chronological messages for valid followup_id (AC4), returns 404 for inaccessible followup (AC5), returns empty messages array with assignee info when no messages exist (AC3), returns has_unread=true when inbound messages newer than last_viewed_at (AC2), PATCH /viewed updates last_viewed_at and returns success (AC2), PATCH /viewed requires authentication, GET /messages requires authentication
  - apps/web/src/components/action-list/__tests__/MessageThread.test.tsx: Frontend tests — renders outbound messages right-aligned (AC1), renders inbound messages left-aligned (AC1), shows message type badges (AC1), shows sender and timestamp per message (AC1), shows "Awaiting response" empty state when no inbound messages (AC3), shows loading skeleton, renders role="log" for accessibility
  - apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx: Updated tests — message thread renders when dialog opens with a followup that has messages (AC1), markViewed is called on dialog open (AC2)

implementation_order:
  1. Create migration supabase/migrations/0033_followup_last_viewed.sql — ALTER TABLE action_followups ADD COLUMN last_viewed_at TIMESTAMPTZ DEFAULT NULL (Task 6)
  2. Add Pydantic schemas to apps/api/app/schemas/action.py — FollowUpMessageResponse (id, direction, message_type, sender_email, subject, body, sent_at), FollowUpMessageListResponse (followup_id, action_summary, assignee_name, assignee_email, status, messages list, has_unread, last_viewed_at), FollowUpViewedResponse (success, last_viewed_at) (Task 1.2)
  3. Add GET /{followup_id}/messages endpoint to apps/api/app/api/followups.py — authenticated, queries followup_messages + action_followups, validates user is assigner/assignee, computes has_unread from inbound messages vs last_viewed_at, returns FollowUpMessageListResponse (Tasks 1.1, 1.3, 1.4, 1.5, 1.6)
  4. Add PATCH /{followup_id}/viewed endpoint to apps/api/app/api/followups.py — authenticated, updates last_viewed_at=NOW() on action_followups, returns FollowUpViewedResponse (Task 6.2)
  5. Extend GET /api/v1/actions/followups in apps/api/app/api/actions.py — add has_unread boolean per followup item by checking followup_messages for inbound messages newer than last_viewed_at (Task 4.3)
  6. Create backend tests apps/api/app/tests/api/test_followups_messages.py — test both new endpoints for auth, access control, chronological ordering, has_unread computation, empty state (Task 7.1, 7.2)
  7. Create apps/web/src/hooks/useFollowUpMessages.ts — hook following useMyFollowUps.ts pattern, fetches GET /api/v1/followups/{id}/messages, exposes messages, loading, error, refetch, hasUnread, markViewed() (Task 2)
  8. Create apps/web/src/components/action-list/MessageThread.tsx — chat-style component with ScrollArea, outbound right-aligned, inbound left-aligned, message type badges, empty state, loading skeleton, ARIA role="log" (Task 3)
  9. Modify apps/web/src/components/action-list/FollowUpDetailDialog.tsx — integrate MessageThread below existing metadata, call useFollowUpMessages on open, call markViewed on open (Task 5.2)
  10. Modify apps/web/src/components/action-list/FollowUpEntry.tsx — accept optional has_unread prop, prefer server-side flag over localStorage when available (Task 4)
  11. Modify apps/web/src/hooks/useMyFollowUps.ts — extend FollowUpItem with has_unread field, pass through from API response (Task 4)
  12. Update apps/web/src/components/action-list/index.ts — add MessageThread export (Task 5.1)
  13. Create frontend tests apps/web/src/components/action-list/__tests__/MessageThread.test.tsx (Task 7.3)
  14. Update frontend tests apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx (Task 7.4)
  15. Run all tests (backend pytest + frontend vitest) and verify no regressions
DESIGN END

---

## TEST_SPEC: 15-4-message-thread-ui
**Timestamp:** 2026-02-11 23:05:42

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

---
