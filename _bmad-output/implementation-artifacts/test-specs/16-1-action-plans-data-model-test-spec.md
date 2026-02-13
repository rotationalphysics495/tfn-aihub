TEST SPEC START
story_id: 16-1-action-plans-data-model
generated: 2026-02-12

test_specifications:

## AC1: `action_plans` Table Created

### 16-1-action-plans-data-model-UNIT-001: Migration file exists and is non-empty
- Priority: P0
- Type: unit
- Given: The migration file 0034_action_plans.sql has been created
- When: The file system is checked for the migration file at supabase/migrations/0034_action_plans.sql
- Then: The file exists at the expected path and has non-empty content
- Data: File path: supabase/migrations/0034_action_plans.sql

### 16-1-action-plans-data-model-UNIT-002: Migration creates action_plans table with CREATE TABLE IF NOT EXISTS
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE TABLE statement
- Then: The migration contains `CREATE TABLE IF NOT EXISTS action_plans` (idempotent per AC5)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-003: Table has id column as UUID PK with gen_random_uuid() default
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the id column definition within the action_plans CREATE TABLE block
- Then: The column is defined as `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-004: Table has title column as TEXT NOT NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the title column definition
- Then: The column is defined as `title TEXT NOT NULL`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-005: Table has description column as nullable TEXT
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the description column definition in the action_plans CREATE TABLE block
- Then: The column is defined as `description TEXT` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-006: Table has asset_id column as nullable UUID FK to assets(id) ON DELETE SET NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the asset_id column definition
- Then: The column is defined as `asset_id UUID REFERENCES assets(id) ON DELETE SET NULL` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-007: Table has category column with CHECK constraint for corrective/preventive/improvement
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the category column definition
- Then: The column is defined as `category TEXT CHECK (category IN ('corrective', 'preventive', 'improvement'))`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-008: Table has root_cause column as nullable TEXT
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the root_cause column definition in the action_plans CREATE TABLE block
- Then: The column is defined as `root_cause TEXT` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-009: Table has corrective_action column as nullable TEXT
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the corrective_action column definition
- Then: The column is defined as `corrective_action TEXT` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-010: Table has preventive_action column as nullable TEXT
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the preventive_action column definition
- Then: The column is defined as `preventive_action TEXT` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-011: Table has source_followup_id column as nullable UUID FK to action_followups(id) ON DELETE SET NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the source_followup_id column definition
- Then: The column is defined as `source_followup_id UUID REFERENCES action_followups(id) ON DELETE SET NULL` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-012: source_followup_id FK does NOT use ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for CASCADE behavior on source_followup_id
- Then: No `ON DELETE CASCADE` appears in conjunction with `action_followups(id)` in the action_plans table
- Data: N/A

### 16-1-action-plans-data-model-UNIT-013: Table has owner_id column as UUID NOT NULL FK to auth.users(id) ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the owner_id column definition
- Then: The column is defined as `owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-014: Table has status column with DEFAULT 'draft' and CHECK constraint
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the status column definition in the action_plans CREATE TABLE block
- Then: The column is defined as `status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'open', 'in_progress', 'completed', 'verified'))`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-015: Table has priority column with DEFAULT 'medium' and CHECK constraint
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the priority column definition
- Then: The column is defined as `priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical'))`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-016: Table has due_date column as DATE
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the due_date column definition
- Then: The column is defined as `due_date DATE` (simple date without timezone)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-017: Table has completed_at column as nullable TIMESTAMPTZ
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the completed_at column definition
- Then: The column is defined as `completed_at TIMESTAMPTZ` (or `TIMESTAMP WITH TIME ZONE`) without NOT NULL and without DEFAULT
- Data: N/A

### 16-1-action-plans-data-model-UNIT-018: Table has verified_by column as nullable UUID FK to auth.users(id) ON DELETE SET NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the verified_by column definition
- Then: The column is defined as `verified_by UUID REFERENCES auth.users(id) ON DELETE SET NULL` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-019: Table has verified_at column as nullable TIMESTAMPTZ
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the verified_at column definition
- Then: The column is defined as `verified_at TIMESTAMPTZ` (or `TIMESTAMP WITH TIME ZONE`) without NOT NULL and without DEFAULT
- Data: N/A

### 16-1-action-plans-data-model-UNIT-020: Table has created_at column as TIMESTAMPTZ with DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the created_at column definition in the action_plans CREATE TABLE block
- Then: The column is defined as `created_at TIMESTAMPTZ DEFAULT NOW()` (or `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-021: Table has updated_at column as TIMESTAMPTZ with DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the updated_at column definition in the action_plans CREATE TABLE block
- Then: The column is defined as `updated_at TIMESTAMPTZ DEFAULT NOW()` (or `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-022: update_updated_at_column() trigger is attached to action_plans
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for trigger creation on action_plans
- Then: A `CREATE TRIGGER` statement exists that attaches `update_updated_at_column()` to the `action_plans` table with BEFORE UPDATE FOR EACH ROW
- Data: N/A

### 16-1-action-plans-data-model-UNIT-023: Trigger uses DROP TRIGGER IF EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for trigger idempotency pattern
- Then: A `DROP TRIGGER IF EXISTS` statement appears before the `CREATE TRIGGER` for action_plans
- Data: N/A

### 16-1-action-plans-data-model-UNIT-024: Migration does NOT recreate update_updated_at_column() function
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for function creation statements
- Then: No `CREATE FUNCTION` or `CREATE OR REPLACE FUNCTION update_updated_at_column` exists (function already exists from migration 0002)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-025: Table has exactly 18 columns
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The action_plans CREATE TABLE statement is parsed for column definitions
- Then: Exactly 18 columns are defined: id, title, description, asset_id, category, root_cause, corrective_action, preventive_action, source_followup_id, owner_id, status, priority, due_date, completed_at, verified_by, verified_at, created_at, updated_at
- Data: N/A

### 16-1-action-plans-data-model-UNIT-026: asset_id FK does NOT use ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for CASCADE behavior on asset_id FK
- Then: No `ON DELETE CASCADE` appears in conjunction with `assets(id)` in the action_plans table
- Data: N/A

## AC2: `action_plan_updates` Table Created

### 16-1-action-plans-data-model-UNIT-027: Migration creates action_plan_updates table
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the action_plan_updates CREATE TABLE statement
- Then: The migration contains `CREATE TABLE IF NOT EXISTS action_plan_updates` (idempotent per AC5)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-028: action_plan_updates has id column as UUID PK with gen_random_uuid() default
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the id column within the action_plan_updates CREATE TABLE block
- Then: The column is defined as `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-029: action_plan_updates has action_plan_id column as UUID NOT NULL FK to action_plans(id) ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the action_plan_id column definition
- Then: The column is defined as `action_plan_id UUID NOT NULL REFERENCES action_plans(id) ON DELETE CASCADE`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-030: action_plan_updates has author_id column as UUID NOT NULL FK to auth.users(id) ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the author_id column definition in action_plan_updates
- Then: The column is defined as `author_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-031: action_plan_updates has update_text column as TEXT NOT NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the update_text column definition
- Then: The column is defined as `update_text TEXT NOT NULL`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-032: action_plan_updates has status_change column as nullable TEXT
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the status_change column definition
- Then: The column is defined as `status_change TEXT` without NOT NULL constraint
- Data: N/A

### 16-1-action-plans-data-model-UNIT-033: action_plan_updates has created_at column as TIMESTAMPTZ with DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the created_at column in the action_plan_updates CREATE TABLE block
- Then: The column is defined as `created_at TIMESTAMPTZ DEFAULT NOW()` (or `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-034: action_plan_updates does NOT have updated_at column (append-only)
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The action_plan_updates CREATE TABLE block is searched for an updated_at column
- Then: No `updated_at` column definition exists in the action_plan_updates CREATE TABLE statement
- Data: N/A

### 16-1-action-plans-data-model-UNIT-035: action_plan_updates does NOT have an updated_at trigger (append-only)
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for triggers on action_plan_updates
- Then: No `CREATE TRIGGER` statement references the `action_plan_updates` table
- Data: N/A

### 16-1-action-plans-data-model-UNIT-036: action_plan_updates has exactly 6 columns
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The action_plan_updates CREATE TABLE statement is parsed for column definitions
- Then: Exactly 6 columns are defined: id, action_plan_id, author_id, update_text, status_change, created_at
- Data: N/A

### 16-1-action-plans-data-model-INT-001: Cascade delete removes action_plan_updates when action_plan is deleted
- Priority: P0
- Type: integration
- Given: An action_plan exists with id X, and 3 action_plan_updates exist with action_plan_id = X
- When: The action_plan with id X is deleted from `action_plans`
- Then: All 3 action_plan_updates rows with action_plan_id = X are also deleted, and the query returns 0 rows
- Data: Requires a running Supabase instance with service_role access to insert and delete test data

### 16-1-action-plans-data-model-INT-002: Deleting a followup sets source_followup_id to NULL (ON DELETE SET NULL)
- Priority: P0
- Type: integration
- Given: An action_followup exists with id F, and an action_plan exists with source_followup_id = F
- When: The action_followup with id F is deleted from `action_followups`
- Then: The action_plan still exists but its source_followup_id is now NULL
- Data: Requires service_role access to insert into action_followups and action_plans, then delete the followup

### 16-1-action-plans-data-model-INT-003: Deleting an asset sets asset_id to NULL (ON DELETE SET NULL)
- Priority: P0
- Type: integration
- Given: An asset exists with id A, and an action_plan exists with asset_id = A
- When: The asset with id A is deleted from `assets`
- Then: The action_plan still exists but its asset_id is now NULL
- Data: Requires service_role access to insert into assets and action_plans, then delete the asset

## AC3: Row Level Security Enabled

### 16-1-action-plans-data-model-UNIT-037: Migration enables RLS on action_plans
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for RLS enablement on action_plans
- Then: The statement `ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY` exists
- Data: N/A

### 16-1-action-plans-data-model-UNIT-038: Migration enables RLS on action_plan_updates
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for RLS enablement on action_plan_updates
- Then: The statement `ALTER TABLE action_plan_updates ENABLE ROW LEVEL SECURITY` exists
- Data: N/A

### 16-1-action-plans-data-model-UNIT-039: action_plans has SELECT policy for all authenticated users (USING true)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the SELECT RLS policy on action_plans
- Then: A policy exists FOR SELECT TO authenticated on action_plans with USING (true) for shared visibility
- Data: N/A

### 16-1-action-plans-data-model-UNIT-040: action_plans has INSERT policy restricting owner_id = auth.uid()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the INSERT RLS policy on action_plans
- Then: A policy exists FOR INSERT TO authenticated on action_plans with WITH CHECK containing `owner_id = auth.uid()`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-041: action_plans has UPDATE policy restricting owner_id = auth.uid()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the UPDATE RLS policy on action_plans
- Then: A policy exists FOR UPDATE TO authenticated on action_plans with USING and/or WITH CHECK containing `owner_id = auth.uid()`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-042: action_plans has service_role full access policy
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the service_role policy on action_plans
- Then: A policy exists FOR ALL TO service_role on action_plans with USING (true) and WITH CHECK (true)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-043: action_plan_updates has SELECT policy for all authenticated users (USING true)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the SELECT RLS policy on action_plan_updates
- Then: A policy exists FOR SELECT TO authenticated on action_plan_updates with USING (true) for timeline visibility
- Data: N/A

### 16-1-action-plans-data-model-UNIT-044: action_plan_updates has INSERT policy restricting author_id = auth.uid()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the INSERT RLS policy on action_plan_updates
- Then: A policy exists FOR INSERT TO authenticated on action_plan_updates with WITH CHECK containing `author_id = auth.uid()`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-045: action_plan_updates has service_role full access policy
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the service_role policy on action_plan_updates
- Then: A policy exists FOR ALL TO service_role on action_plan_updates with USING (true) and WITH CHECK (true)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-046: action_plans RLS policies use DROP POLICY IF EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for DROP POLICY IF EXISTS statements for action_plans
- Then: Each CREATE POLICY on action_plans is preceded by a corresponding `DROP POLICY IF EXISTS` statement
- Data: N/A

### 16-1-action-plans-data-model-UNIT-047: action_plan_updates RLS policies use DROP POLICY IF EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for DROP POLICY IF EXISTS statements for action_plan_updates
- Then: Each CREATE POLICY on action_plan_updates is preceded by a corresponding `DROP POLICY IF EXISTS` statement
- Data: N/A

### 16-1-action-plans-data-model-INT-004: Authenticated user can SELECT all action_plans (shared visibility)
- Priority: P0
- Type: integration
- Given: User A owns an action_plan and User B owns another action_plan
- When: User A queries all action_plans via authenticated client
- Then: User A can see both their own plan and User B's plan (shared read access)
- Data: Requires two authenticated users with separate action plans inserted via service_role

### 16-1-action-plans-data-model-INT-005: Owner can INSERT an action_plan with owner_id = auth.uid()
- Priority: P0
- Type: integration
- Given: User A is authenticated
- When: User A inserts an action_plan with owner_id = User A's uid
- Then: The insert succeeds and the row is persisted
- Data: Requires an authenticated user context

### 16-1-action-plans-data-model-INT-006: Authenticated user cannot INSERT an action_plan with owner_id != auth.uid()
- Priority: P0
- Type: integration
- Given: User A is authenticated
- When: User A attempts to insert an action_plan with owner_id = User B's uid
- Then: The insert fails or is denied by RLS policy
- Data: Requires two user UUIDs

### 16-1-action-plans-data-model-INT-007: Owner can UPDATE their own action_plan
- Priority: P0
- Type: integration
- Given: User A owns an action_plan with id X
- When: User A updates the title of action_plan X via authenticated client
- Then: The update succeeds
- Data: Requires an authenticated user with an existing action plan

### 16-1-action-plans-data-model-INT-008: Non-owner cannot UPDATE another user's action_plan
- Priority: P0
- Type: integration
- Given: User A owns an action_plan with id X
- When: User B attempts to update the title of action_plan X via authenticated client
- Then: The update fails or affects 0 rows (RLS blocks the operation)
- Data: Requires two authenticated users

### 16-1-action-plans-data-model-INT-009: Authenticated user can SELECT all action_plan_updates (timeline visibility)
- Priority: P0
- Type: integration
- Given: Updates exist for action_plans owned by various users
- When: Any authenticated user queries action_plan_updates
- Then: All updates are visible (shared read access for timeline)
- Data: Requires action_plan_updates inserted via service_role

### 16-1-action-plans-data-model-INT-010: Authenticated user can INSERT action_plan_update with author_id = auth.uid()
- Priority: P0
- Type: integration
- Given: An action_plan exists and User A is authenticated
- When: User A inserts an action_plan_update with author_id = User A's uid
- Then: The insert succeeds and the row is persisted
- Data: Requires an authenticated user and an existing action plan

### 16-1-action-plans-data-model-INT-011: Authenticated user cannot INSERT action_plan_update with author_id != auth.uid()
- Priority: P0
- Type: integration
- Given: An action_plan exists and User A is authenticated
- When: User A attempts to insert an action_plan_update with author_id = User B's uid
- Then: The insert fails or is denied by RLS policy
- Data: Requires two user UUIDs and an existing action plan

### 16-1-action-plans-data-model-INT-012: Service role has full CRUD access on both tables
- Priority: P0
- Type: integration
- Given: The service_role connection is used
- When: The service role performs INSERT, SELECT, UPDATE, and DELETE on action_plans and action_plan_updates
- Then: All operations succeed without RLS restrictions
- Data: Requires service_role key and test data

## AC4: Performance Indexes Created

### 16-1-action-plans-data-model-UNIT-048: Migration creates index idx_action_plans_asset_id
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_action_plans_asset_id` is created on `action_plans(asset_id)`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-049: Migration creates index idx_action_plans_status
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_action_plans_status` is created on `action_plans(status)`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-050: Migration creates index idx_action_plans_owner_id
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_action_plans_owner_id` is created on `action_plans(owner_id)`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-051: Migration creates index idx_action_plans_source_followup_id
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_action_plans_source_followup_id` is created on `action_plans(source_followup_id)`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-052: Migration creates index idx_action_plan_updates_action_plan_id
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_action_plan_updates_action_plan_id` is created on `action_plan_updates(action_plan_id)`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-053: All five required indexes are present
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: All CREATE INDEX statements targeting action_plans and action_plan_updates are counted
- Then: At least 5 CREATE INDEX statements exist across both tables (4 on action_plans, 1 on action_plan_updates)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-054: Indexes use CREATE INDEX IF NOT EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE INDEX statements
- Then: All index creation statements use `CREATE INDEX IF NOT EXISTS` for idempotency
- Data: N/A

## AC5: Migration File Created

### 16-1-action-plans-data-model-UNIT-055: Migration file exists at correct path
- Priority: P0
- Type: unit
- Given: The migration is needed for story 16.1
- When: The migrations folder is checked
- Then: `supabase/migrations/0034_action_plans.sql` exists (adjusted from story-specified 0031 because 0031-0033 already exist)
- Data: File path: supabase/migrations/0034_action_plans.sql

### 16-1-action-plans-data-model-UNIT-056: Migration file follows naming convention with correct sequence number
- Priority: P0
- Type: unit
- Given: The migration directory contains existing migrations up to 0033
- When: The file name is validated against the sequence
- Then: The migration file is named `0034_action_plans.sql` and its number (0034) follows after the existing highest migration
- Data: N/A

### 16-1-action-plans-data-model-UNIT-057: Migration uses CREATE TABLE IF NOT EXISTS for idempotency
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE TABLE statements
- Then: Both `CREATE TABLE IF NOT EXISTS action_plans` and `CREATE TABLE IF NOT EXISTS action_plan_updates` are used
- Data: N/A

### 16-1-action-plans-data-model-UNIT-058: Migration has header comment with story reference
- Priority: P2
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for header comments
- Then: A comment referencing Story 16.1 or action plans exists at the top of the file
- Data: N/A

### 16-1-action-plans-data-model-UNIT-059: Both tables are created in a single migration file
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The file is checked for both CREATE TABLE statements
- Then: Both `CREATE TABLE IF NOT EXISTS action_plans` and `CREATE TABLE IF NOT EXISTS action_plan_updates` exist in the same file (0034_action_plans.sql)
- Data: N/A

### 16-1-action-plans-data-model-UNIT-060: No other files are created by this story (pure SQL migration)
- Priority: P1
- Type: unit
- Given: The story specifies this is a pure migration story
- When: The migration file is the only artifact
- Then: Only `supabase/migrations/0034_action_plans.sql` is created; no API code, frontend code, or Pydantic models
- Data: N/A

### 16-1-action-plans-data-model-UNIT-061: Migration does NOT use VARCHAR (uses TEXT consistently)
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for VARCHAR usage
- Then: No `VARCHAR` type appears in the migration; all string columns use `TEXT`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-062: Migration does NOT use uuid_generate_v4() (uses gen_random_uuid())
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for uuid_generate_v4()
- Then: No `uuid_generate_v4()` appears; only `gen_random_uuid()` is used
- Data: N/A

## SQL Syntax Validation (cross-cutting)

### 16-1-action-plans-data-model-UNIT-063: Migration SQL has balanced parentheses
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: Open and close parentheses are counted
- Then: The count of `(` equals the count of `)`
- Data: N/A

### 16-1-action-plans-data-model-UNIT-064: All SQL statements end with semicolons
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: CREATE TABLE, CREATE INDEX, ALTER TABLE, CREATE POLICY, and CREATE TRIGGER statements are parsed
- Then: Each statement is properly terminated with a semicolon
- Data: N/A

## Constraint Validation (integration)

### 16-1-action-plans-data-model-INT-013: CHECK constraint rejects invalid category value
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role with category = 'invalid_category'
- Then: The insert fails with a CHECK constraint violation error
- Data: category: 'invalid_category'

### 16-1-action-plans-data-model-INT-014: CHECK constraint rejects invalid status value
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role with status = 'invalid_status'
- Then: The insert fails with a CHECK constraint violation error
- Data: status: 'invalid_status'

### 16-1-action-plans-data-model-INT-015: CHECK constraint rejects invalid priority value
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role with priority = 'invalid_priority'
- Then: The insert fails with a CHECK constraint violation error
- Data: priority: 'invalid_priority'

### 16-1-action-plans-data-model-INT-016: NOT NULL constraint rejects null title
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role with title = NULL
- Then: The insert fails with a NOT NULL violation error
- Data: title: null

### 16-1-action-plans-data-model-INT-017: NOT NULL constraint rejects null owner_id
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role with owner_id = NULL
- Then: The insert fails with a NOT NULL violation error
- Data: owner_id: null

### 16-1-action-plans-data-model-INT-018: NOT NULL constraint rejects null update_text in action_plan_updates
- Priority: P1
- Type: integration
- Given: The action_plan_updates table exists and an action_plan exists
- When: An action_plan_update is inserted via service_role with update_text = NULL
- Then: The insert fails with a NOT NULL violation error
- Data: update_text: null

### 16-1-action-plans-data-model-INT-019: FK constraint rejects invalid action_plan_id in action_plan_updates
- Priority: P1
- Type: integration
- Given: No action_plan exists with a specific UUID
- When: An action_plan_update is inserted via service_role with action_plan_id = non-existent UUID
- Then: The insert fails with a foreign key constraint violation
- Data: action_plan_id: '00000000-0000-0000-0000-000000000000' (non-existent)

### 16-1-action-plans-data-model-INT-020: Default gen_random_uuid() generates unique id on insert for both tables
- Priority: P1
- Type: integration
- Given: Both tables exist
- When: Two action_plans and two action_plan_updates are inserted without specifying id
- Then: All inserts succeed and each row has a unique, non-null UUID id value
- Data: Inserts without explicit id

### 16-1-action-plans-data-model-INT-021: Default status 'draft' is applied when not specified
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role without specifying status
- Then: The status column defaults to 'draft'
- Data: Insert without explicit status

### 16-1-action-plans-data-model-INT-022: Default priority 'medium' is applied when not specified
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role without specifying priority
- Then: The priority column defaults to 'medium'
- Data: Insert without explicit priority

### 16-1-action-plans-data-model-INT-023: Default NOW() populates created_at and updated_at on insert for action_plans
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role without specifying created_at or updated_at
- Then: Both created_at and updated_at are automatically populated with the current timestamp (within a few seconds of the insert time)
- Data: Insert without explicit timestamps

### 16-1-action-plans-data-model-INT-024: update_updated_at trigger automatically updates updated_at on UPDATE
- Priority: P0
- Type: integration
- Given: An action_plan exists with a known updated_at timestamp
- When: The action_plan's title is updated via service_role after a brief delay
- Then: The updated_at column is automatically changed to a more recent timestamp than the original value
- Data: Requires an existing action_plan and an UPDATE operation

### 16-1-action-plans-data-model-INT-025: Nullable columns accept NULL values (asset_id, description, root_cause, etc.)
- Priority: P1
- Type: integration
- Given: The action_plans table exists
- When: An action_plan is inserted via service_role with only required fields (title, owner_id) and all nullable fields set to NULL
- Then: The insert succeeds with NULL values for description, asset_id, category, root_cause, corrective_action, preventive_action, source_followup_id, due_date, completed_at, verified_by, verified_at
- Data: Minimal insert with only required fields

edge_cases:
  - Action plan inserted with asset_id = NULL (plant-wide plan with no specific asset) — validates nullable FK design
  - Action plan inserted with source_followup_id = NULL (plan not originating from a followup) — validates nullable FK design
  - Action plan with all nullable fields NULL — validates minimal insert with only title and owner_id
  - Very long description and root_cause text (10,000+ characters) — validates no implicit length restriction on TEXT columns
  - Action plan with status progressing through all states: draft -> open -> in_progress -> completed -> verified
  - Action plan update with status_change = NULL (simple progress note, no status transition)
  - Multiple action_plan_updates for the same action_plan — validates one-to-many relationship
  - Action plan with due_date in the past — validates no constraint preventing historical dates
  - Deleting a verified_by user sets verified_by to NULL (ON DELETE SET NULL) without deleting the plan

error_scenarios:
  - Insert with invalid category value ('emergency') — CHECK constraint violation
  - Insert with invalid status value ('cancelled') — CHECK constraint violation
  - Insert with invalid priority value ('urgent') — CHECK constraint violation
  - Insert with null title — NOT NULL violation
  - Insert with null owner_id — NOT NULL violation
  - Insert action_plan_update with null update_text — NOT NULL violation
  - Insert action_plan_update with null action_plan_id — NOT NULL violation
  - Insert action_plan_update with non-existent action_plan_id — FK constraint violation
  - Insert action_plan with non-existent asset_id — FK constraint violation
  - Insert action_plan with non-existent source_followup_id — FK constraint violation
  - Authenticated user attempts INSERT with owner_id != auth.uid() — RLS policy denial
  - Non-owner attempts UPDATE on another user's plan — RLS policy denial
  - Authenticated user attempts INSERT action_plan_update with author_id != auth.uid() — RLS policy denial

test_file_mapping:
  - 16-1-action-plans-data-model-UNIT-*: supabase/tests/action-plans-schema.test.ts
  - 16-1-action-plans-data-model-INT-*: supabase/tests/action-plans-integration.test.ts

TEST SPEC END
