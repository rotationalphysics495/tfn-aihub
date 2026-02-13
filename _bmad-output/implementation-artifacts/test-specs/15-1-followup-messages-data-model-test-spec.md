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
