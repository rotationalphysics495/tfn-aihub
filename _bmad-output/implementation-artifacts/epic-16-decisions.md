# Epic 16 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 16
**Started:** 2026-02-11 23:57:24

---


## DESIGN: 16-1-action-plans-data-model
**Timestamp:** 2026-02-12 00:00:55

DESIGN START
story_id: 16-1-action-plans-data-model

files_to_modify:
  - path: supabase/migrations/0034_action_plans.sql
    action: create
    purpose: Single migration file containing both tables (action_plans, action_plan_updates), all indexes, trigger, RLS policies, comments, and verification queries

patterns_to_use:
  - UUID primary keys with gen_random_uuid(): Consistent with all existing tables (0002, 0025, 0027, etc.)
  - TEXT with CHECK constraints for enums: Matches action_followups.status and action_followups.category pattern from 0025
  - TIMESTAMP WITH TIME ZONE DEFAULT NOW(): Standard timestamp pattern across all migrations
  - Reuse existing update_updated_at_column() trigger function: Created in 0002, reused in 0025 and 0027 — just CREATE TRIGGER referencing it
  - DROP TRIGGER IF EXISTS before CREATE TRIGGER: Idempotency pattern from 0002
  - DROP POLICY IF EXISTS before CREATE POLICY: Idempotency pattern from 0002 and 0012
  - CREATE TABLE IF NOT EXISTS: Idempotency pattern from 0002
  - CREATE INDEX IF NOT EXISTS: Idempotency pattern from 0002
  - Section headers with === delimiters: Documentation pattern from 0002
  - COMMENT ON TABLE/COLUMN: Documentation pattern from 0002
  - Verification queries as comments at bottom: Pattern from 0002
  - Two-tier RLS (authenticated + service_role): Pattern from 0002, 0025, 0027

dependencies:
  - supabase/migrations/0002_plant_object_model.sql: installed (provides update_updated_at_column() function and assets table)
  - supabase/migrations/0025_action_followups.sql: installed (provides action_followups table for source_followup_id FK)
  - auth.users: installed (Supabase built-in, provides auth.uid() and user FKs)

acceptance_criteria_mapping:
  - AC1: supabase/migrations/0034_action_plans.sql — CREATE TABLE IF NOT EXISTS action_plans with all 18 columns (id, title, description, asset_id, category, root_cause, corrective_action, preventive_action, source_followup_id, owner_id, status, priority, due_date, completed_at, verified_by, verified_at, created_at, updated_at), CHECK constraints on category/status/priority, FK constraints to assets(id) ON DELETE SET NULL, action_followups(id) ON DELETE SET NULL, auth.users(id) with appropriate ON DELETE behavior, and update_updated_at_column() trigger
  - AC2: supabase/migrations/0034_action_plans.sql — CREATE TABLE IF NOT EXISTS action_plan_updates with 5 columns (id, action_plan_id, author_id, update_text, status_change, created_at), FK to action_plans(id) ON DELETE CASCADE, FK to auth.users(id) ON DELETE CASCADE. No updated_at column (append-only table)
  - AC3: supabase/migrations/0034_action_plans.sql — ALTER TABLE ENABLE ROW LEVEL SECURITY on both tables. action_plans: authenticated SELECT all (USING true), INSERT with owner_id = auth.uid(), UPDATE with owner_id = auth.uid(), service_role full access. action_plan_updates: authenticated SELECT all (USING true), INSERT with author_id = auth.uid(), service_role full access
  - AC4: supabase/migrations/0034_action_plans.sql — CREATE INDEX IF NOT EXISTS for idx_action_plans_asset_id, idx_action_plans_status, idx_action_plans_owner_id, idx_action_plans_source_followup_id, idx_action_plan_updates_action_plan_id
  - AC5: supabase/migrations/0034_action_plans.sql — File exists at correct path, follows established patterns from 0025 and 0002, uses IF NOT EXISTS/DROP IF EXISTS for idempotency. NOTE: Migration number adjusted from story-specified 0031 to 0034 because 0031-0033 already exist on disk

risks:
  - Migration number conflict: Story specifies 0031 but 0031-0033 already exist on disk. MITIGATION: Use 0034 as the next available number. Document this deviation in the epic decision log.
  - FK to action_followups may fail if migrations 0026-0033 haven't run in order: MITIGATION: action_followups was created in 0025 which predates all existing migrations, so the FK target exists. No risk here.
  - RLS policy for INSERT on action_plans requires owner_id = auth.uid(): The INSERT policy uses WITH CHECK (owner_id = auth.uid()) which means the API/frontend must set owner_id to the current user's ID. This is standard and matches the action_followups pattern.
  - ON DELETE SET NULL for asset_id FK: If an asset is deleted, action_plans.asset_id becomes NULL. This is intentional (preserves plan history) but downstream queries must handle NULL asset_id gracefully (story 16.4/16.5 concern).
  - CASCADE DELETE on action_plan_updates: Deleting an action_plan removes all its updates. This is intentional for data cleanup but means the audit trail is lost. The story explicitly requires this behavior.

estimated_test_files:
  - No TypeScript/Python test files for this story: This is a pure SQL migration (data model only). Testing is done via SQL verification queries embedded as comments in the migration file, and manual verification steps documented in the story's Dev Notes.

implementation_order:
  1. Update epic-16 decision log to document migration number change from 0031 to 0034 (with rationale: migrations 0031-0033 already exist from Epic 15 implementation)
  2. Create supabase/migrations/0034_action_plans.sql with header comment referencing Story 16.1
  3. Write the action_plans CREATE TABLE IF NOT EXISTS statement with all 18 columns, inline CHECK constraints, and FK constraints (asset_id ON DELETE SET NULL, source_followup_id ON DELETE SET NULL, owner_id ON DELETE CASCADE, verified_by ON DELETE SET NULL)
  4. Write the action_plan_updates CREATE TABLE IF NOT EXISTS statement with 5 columns, FK to action_plans ON DELETE CASCADE, FK to auth.users ON DELETE CASCADE
  5. Add the 5 performance indexes using CREATE INDEX IF NOT EXISTS
  6. Add the update_updated_at_column() trigger for action_plans only (DROP TRIGGER IF EXISTS + CREATE TRIGGER)
  7. Enable RLS on both tables (ALTER TABLE ENABLE ROW LEVEL SECURITY)
  8. Create RLS policies for action_plans: DROP IF EXISTS + CREATE for authenticated SELECT (USING true), INSERT (WITH CHECK owner_id = auth.uid()), UPDATE (USING/WITH CHECK owner_id = auth.uid()), service_role ALL
  9. Create RLS policies for action_plan_updates: DROP IF EXISTS + CREATE for authenticated SELECT (USING true), INSERT (WITH CHECK author_id = auth.uid()), service_role ALL
  10. Add COMMENT ON TABLE and COMMENT ON COLUMN for both tables (key columns: status, category, priority enums, source_followup_id relationship)
  11. Add SQL verification queries as comments at the bottom of the migration file
DESIGN END

---

## TEST_SPEC: 16-1-action-plans-data-model
**Timestamp:** 2026-02-12 00:04:04

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

---

## DESIGN: 16-2-action-plans-crud-api
**Timestamp:** 2026-02-12 00:28:35

DESIGN START
story_id: 16-2-action-plans-crud-api

files_to_modify:
  - path: apps/api/app/schemas/action_plan.py
    action: create
    purpose: Pydantic schemas for action plan enums (ActionPlanCategory, ActionPlanStatus, ActionPlanPriority), request models (ActionPlanCreate, ActionPlanUpdate, ActionPlanUpdateCreate, ActionPlanVerifyRequest), response models (ActionPlanResponse, ActionPlanListResponse, ActionPlanUpdateResponse), and PRIORITY_SORT_MAP for sorting
  - path: apps/api/app/api/action_plans.py
    action: create
    purpose: APIRouter with 8 endpoints (POST /, GET /, GET /{id}, PATCH /{id}, POST /{id}/updates, GET /{id}/updates, POST /{id}/verify) plus _get_supabase_client() helper and Supabase data access helper functions (_create_action_plan, _get_action_plan_by_id, _list_action_plans, _update_action_plan, _create_update_record, _get_updates_for_plan)
  - path: apps/api/app/main.py
    action: modify
    purpose: Import action_plans module and register router with prefix="/api/v1/action-plans" and tags=["Action Plans"]
  - path: apps/api/tests/test_action_plans_api.py
    action: create
    purpose: Pytest test file with mocked Supabase client testing all 5 ACs (create, list with filters/sort, update with change logging, progress updates, verify)

patterns_to_use:
  - Two-client Supabase pattern: Service role client (settings.supabase_key) for existence checks; user-scoped client (credentials.credentials JWT token) for INSERT/UPDATE to enforce RLS. Follow exact pattern from actions.py:498-567 (PATCH /followups/{followup_id}). Import `security` from `app.core.security` and add `credentials: HTTPAuthorizationCredentials = Depends(security)` parameter.
  - _get_supabase_client() helper: Local helper returning Optional[Client] via create_client(settings.supabase_url, settings.supabase_key). Follow handoff.py pattern. Used for service-role operations (existence checks, reads).
  - str(Enum) pattern for database enums: `class ActionPlanStatus(str, Enum)` matching action.py:ActionCategory/PriorityLevel pattern. Values must match CHECK constraints in 0034_action_plans.sql exactly.
  - PRIORITY_SORT_MAP: Dict mapping ActionPlanPriority enum values to int (critical=0, high=1, medium=2, low=3) for Python-side sorting after Supabase fetch. Mirrors PRIORITY_RANK_MAP in schemas/action.py:37-42.
  - Pydantic BaseModel with ConfigDict: Field(...) for required, Field(None) for optional, Field(default, description=...) for documented fields. ConfigDict(extra="forbid") on request schemas. Follow schemas/action.py conventions.
  - Partial update with model_dump(exclude_unset=True): For PATCH endpoint, only send fields the client provided. Validate at least one field is present. Follow FollowUpUpdateRequest pattern.
  - Pagination with page/page_size: Convert to offset/limit internally. Use Supabase .range(offset, offset+limit-1). Get total count via separate count query with count="exact". Return ActionPlanListResponse with items, total_count, page, page_size.
  - Auth dependency: `current_user: CurrentUser = Depends(get_current_user)` on every endpoint. Import CurrentUser from app.models.user, get_current_user from app.core.security.
  - Error handling: HTTPException with 400 (validation/business logic), 403 (RLS denial / not authorized), 404 (not found), 422 (empty update), 500 (server error). Re-raise HTTPException in except block. Follow actions.py pattern.
  - Router registration in main.py: Import in the multi-module import line, add app.include_router() with story comment. Follow exact pattern of line 107 (followups registration).
  - Test mocking pattern: Mock `app.api.action_plans.create_client` with side_effect=[service_client, user_client]. Use conftest.py fixtures (client, mock_verify_jwt, valid_jwt_payload). Organize tests by AC in test classes.

dependencies:
  - fastapi: installed (core framework)
  - pydantic: installed (schema validation)
  - supabase: installed (database client, used in handoff.py and actions.py)
  - python-jose: installed (JWT handling in security.py)
  - pytest: installed (test runner)
  - httpx: installed (test client)
  - Story 16.1 migration (0034_action_plans.sql): installed (creates action_plans and action_plan_updates tables)

acceptance_criteria_mapping:
  - AC1 (POST / - create action plan): apps/api/app/api/action_plans.py::create_action_plan() — Validates ActionPlanCreate schema, sets owner_id=current_user.id, status='open', inserts via user-scoped client (RLS enforces owner_id=auth.uid()), returns ActionPlanResponse with 201 status. Schema: apps/api/app/schemas/action_plan.py::ActionPlanCreate (title required, description, category, root_cause, corrective_action, preventive_action, asset_id, priority, due_date, source_followup_id all optional per DB schema).
  - AC2 (GET / - list with filters + sort): apps/api/app/api/action_plans.py::list_action_plans() — Accepts Query params: status (ActionPlanStatus), asset_id (str), owner_id (str), priority (ActionPlanPriority), page (int, default 1), page_size (int, default 20). Builds Supabase query with .eq() filters, fetches via service-role client (all authenticated can read per RLS), applies Python-side sort using PRIORITY_SORT_MAP then due_date ascending (nulls last), applies pagination offset. Returns ActionPlanListResponse.
  - AC3 (PATCH /{id} - update with change logging): apps/api/app/api/action_plans.py::update_action_plan() — Two-client pattern: service-role SELECT to get existing record (404 if missing), user-scoped UPDATE (403 if RLS blocks). Compares old vs new values, auto-generates update_text describing changes, inserts action_plan_updates record via service-role client with author_id=current_user.id. If status changed, records "old -> new" in status_change field. Returns updated ActionPlanResponse.
  - AC4 (POST /{id}/updates - add progress update): apps/api/app/api/action_plans.py::add_progress_update() — Validates ActionPlanUpdateCreate (update_text required, status_change optional). Checks plan exists (404). Inserts into action_plan_updates. If status_change provided, also updates the plan's status via user-scoped client (403 if not authorized). Returns ActionPlanUpdateResponse with 201.
  - AC5 (POST /{id}/verify - verify completion): apps/api/app/api/action_plans.py::verify_action_plan() — Service-role SELECT to check plan exists and status=='completed' (400 if not completed, 404 if missing). Updates plan: status='verified', verified_by=current_user.id, verified_at=now via user-scoped client (403 if RLS blocks). Creates action_plan_updates record logging verification. Returns updated ActionPlanResponse.

risks:
  - Supabase-py sorting limitations: Supabase .order() doesn't support custom sort expressions for priority ranking (critical=0, high=1, etc.). MITIGATION: Fetch filtered results, apply Python-side sort using PRIORITY_SORT_MAP before pagination slicing. This means we fetch all matching rows then paginate in Python. For large datasets this could be slow; acceptable for MVP since action plans are bounded per plant. If needed later, can use .rpc() for a Postgres function.
  - RLS policy on action_plan_updates INSERT: The policy requires author_id=auth.uid(). When auto-generating change log entries in PATCH /{id}, we must use the user-scoped client for the insert (not service role) so RLS is satisfied, OR use service role which bypasses RLS. DECISION: Use service-role client for auto-generated change log inserts (the system is recording the change on behalf of the user, and the author_id is set explicitly). This is consistent with how the handoff audit log works.
  - RLS policy on action_plans UPDATE restricts to owner only: The verify endpoint (AC#5) allows any user to verify, but the UPDATE RLS policy restricts to owner_id=auth.uid(). MITIGATION: Use service-role client for the verify update since verification is a privileged action by a different user (verifier != owner). Set verified_by to current_user.id to maintain audit trail.
  - Pagination total_count with Python-side sorting: Since we sort in Python after fetching, we can use Supabase count="exact" on the filtered query for accurate total_count before applying Python-side pagination. The .select("*", count="exact") approach gives us both data and count in one call.
  - Status transition validation: The story doesn't specify strict state machine rules (e.g., can only go from 'open' to 'in_progress'). DECISION: Don't enforce strict transitions in this story — rely on the CHECK constraint in the DB to reject invalid status values. Future stories can add state machine logic if needed.
  - Empty PATCH body: If all optional fields are None, model_dump(exclude_unset=True) returns {}. MITIGATION: Check for empty update dict and return 422 before attempting DB update.

estimated_test_files:
  - apps/api/tests/test_action_plans_api.py: Tests all 5 ACs. Organized as test classes: TestCreateActionPlan (AC1: valid create, missing required fields, auth required), TestListActionPlans (AC2: no filters, with filters, priority sort, pagination), TestGetActionPlan (AC2-related: by id, 404), TestUpdateActionPlan (AC3: partial update, change log creation, owner-only RLS, 404), TestAddProgressUpdate (AC4: with/without status_change, plan status update, 404), TestVerifyActionPlan (AC5: successful verify, not-completed 400, 404, non-owner can verify). Uses conftest.py fixtures (client, mock_verify_jwt, valid_jwt_payload). Mocks create_client with side_effect for two-client pattern.

implementation_order:
  1. Create apps/api/app/schemas/action_plan.py with all enums (ActionPlanCategory, ActionPlanStatus, ActionPlanPriority), PRIORITY_SORT_MAP, request schemas (ActionPlanCreate, ActionPlanUpdate, ActionPlanUpdateCreate, ActionPlanVerifyRequest), and response schemas (ActionPlanResponse, ActionPlanListResponse, ActionPlanUpdateResponse)
  2. Create apps/api/app/api/action_plans.py with router = APIRouter(), _get_supabase_client() helper, and all 7 Supabase data access helper functions (_create_action_plan, _get_action_plan_by_id, _list_action_plans, _update_action_plan, _create_update_record, _get_updates_for_plan, plus _build_change_description for AC3 change logging)
  3. Implement POST / endpoint (AC1) — create_action_plan() with user-scoped client, status_code=201
  4. Implement GET / endpoint (AC2) — list_action_plans() with query filters, PRIORITY_SORT_MAP sorting, page/page_size pagination
  5. Implement GET /{id} endpoint — get_action_plan() with service-role client
  6. Implement PATCH /{id} endpoint (AC3) — update_action_plan() with two-client pattern, old-vs-new comparison, auto-generated action_plan_updates record
  7. Implement POST /{id}/updates endpoint (AC4) — add_progress_update() with plan existence check, optional status update propagation
  8. Implement GET /{id}/updates endpoint — list_plan_updates() with chronological ordering
  9. Implement POST /{id}/verify endpoint (AC5) — verify_action_plan() with status='completed' guard, service-role update for cross-user verification
  10. Modify apps/api/app/main.py — add action_plans to import line and register router with prefix="/api/v1/action-plans", tags=["Action Plans"]
  11. Create apps/api/tests/test_action_plans_api.py with test classes covering all 5 ACs, positive and negative cases, authorization checks, and validation tests
  12. Run tests with pytest apps/api/tests/test_action_plans_api.py to verify all pass
DESIGN END

---

## TEST_SPEC: 16-2-action-plans-crud-api
**Timestamp:** 2026-02-12 00:31:33

TEST SPEC START
story_id: 16-2-action-plans-crud-api
generated: 2026-02-12

test_specifications:

## AC1: Given an authenticated user calls POST /api/v1/action-plans, When the request includes title, description, category, root_cause, corrective_action, asset_id, priority, due_date, Then a new action plan is created with status='open' and the current user as owner, And the response includes the created plan with its ID

### 16-2-action-plans-crud-api-INT-001: Create action plan with all required fields returns 201
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with title, description, category='corrective', root_cause, corrective_action, asset_id, priority='high', due_date='2026-03-15'
- Then: Response status is 201, response body includes a generated UUID `id`, status='open', owner_id matches current user's ID, and all submitted fields are echoed back
- Data: Valid ActionPlanCreate payload with all fields populated; mock Supabase insert returning the created record with generated id and timestamps

### 16-2-action-plans-crud-api-INT-002: Create action plan sets status to 'open' regardless of input
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with a valid payload (status field is not accepted in create schema)
- Then: The created action plan has status='open', owner_id=current_user.id, and created_at/updated_at are populated
- Data: ActionPlanCreate payload without status field; verify the Supabase insert call includes status='open' and owner_id from JWT sub claim

### 16-2-action-plans-crud-api-INT-003: Create action plan with optional source_followup_id
- Priority: P1
- Type: integration
- Given: An authenticated user and an existing action_followup with a known UUID
- When: POST /api/v1/action-plans is called with a valid payload including source_followup_id
- Then: Response status is 201 and the created plan includes the source_followup_id linking it to the originating followup
- Data: Valid payload with source_followup_id set to a UUID; mock Supabase insert returning record with source_followup_id

### 16-2-action-plans-crud-api-INT-004: Create action plan with minimal fields (only required)
- Priority: P1
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with only the required field (title) and all optional fields omitted
- Then: Response status is 201, the plan is created with defaults (status='open', nullable fields are null)
- Data: Minimal payload with only title; mock Supabase insert returning record with nulls for optional fields

### 16-2-action-plans-crud-api-INT-005: Create action plan fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: POST /api/v1/action-plans is called with a valid payload
- Then: Response status is 401 with appropriate error message
- Data: Valid ActionPlanCreate payload; no Bearer token header

### 16-2-action-plans-crud-api-UNIT-001: ActionPlanCreate schema validates required fields
- Priority: P0
- Type: unit
- Given: An ActionPlanCreate schema instance is being constructed
- When: title is missing from the input data
- Then: Pydantic ValidationError is raised indicating title is required
- Data: Payload missing title field

### 16-2-action-plans-crud-api-UNIT-002: ActionPlanCreate schema validates enum values
- Priority: P1
- Type: unit
- Given: An ActionPlanCreate schema instance is being constructed
- When: category is set to 'invalid_category' (not in ActionPlanCategory enum)
- Then: Pydantic ValidationError is raised for invalid enum value
- Data: Payload with category='invalid_category'

### 16-2-action-plans-crud-api-UNIT-003: ActionPlanCreate schema validates priority enum
- Priority: P1
- Type: unit
- Given: An ActionPlanCreate schema instance is being constructed
- When: priority is set to 'urgent' (not in ActionPlanPriority enum: low, medium, high, critical)
- Then: Pydantic ValidationError is raised for invalid priority value
- Data: Payload with priority='urgent'

### 16-2-action-plans-crud-api-INT-006: Create action plan returns 500 on Supabase error
- Priority: P1
- Type: integration
- Given: An authenticated user, but the Supabase client raises an exception on insert
- When: POST /api/v1/action-plans is called with a valid payload
- Then: Response status is 500 with a descriptive error detail message
- Data: Valid payload; mock Supabase insert to raise an exception

### 16-2-action-plans-crud-api-INT-007: Create action plan uses user-scoped client for RLS enforcement
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with a valid payload
- Then: The Supabase client is created with the user's JWT token (not the service role key) so RLS policies enforce owner_id=auth.uid()
- Data: Valid payload; verify create_client is called with the user's Bearer token

## AC2: Given an authenticated user calls GET /api/v1/action-plans, When optional filters are provided (status, asset_id, owner_id, priority), Then matching action plans are returned sorted by priority (critical first) then due_date

### 16-2-action-plans-crud-api-INT-008: List action plans without filters returns all plans sorted
- Priority: P0
- Type: integration
- Given: An authenticated user and multiple action plans exist with varying priorities and due dates
- When: GET /api/v1/action-plans is called without any query parameters
- Then: Response status is 200, all plans are returned in ActionPlanListResponse format with items sorted by priority (critical=0, high=1, medium=2, low=3) then by due_date ascending
- Data: Mock Supabase returning 4 plans with priorities [low, critical, medium, high] and varied due_dates; verify output order is critical, high, medium, low

### 16-2-action-plans-crud-api-INT-009: List action plans filtered by status
- Priority: P0
- Type: integration
- Given: An authenticated user and action plans exist with statuses 'open', 'in_progress', 'completed'
- When: GET /api/v1/action-plans?status=open is called
- Then: Response status is 200, only plans with status='open' are returned
- Data: Mock Supabase .eq('status', 'open') returning filtered results; verify the .eq() call is made with correct parameters

### 16-2-action-plans-crud-api-INT-010: List action plans filtered by asset_id
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist linked to different assets
- When: GET /api/v1/action-plans?asset_id=asset-uuid-123 is called
- Then: Response status is 200, only plans for the specified asset are returned
- Data: Mock Supabase .eq('asset_id', 'asset-uuid-123') returning filtered results

### 16-2-action-plans-crud-api-INT-011: List action plans filtered by owner_id
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist owned by different users
- When: GET /api/v1/action-plans?owner_id=user-uuid-456 is called
- Then: Response status is 200, only plans owned by the specified user are returned
- Data: Mock Supabase .eq('owner_id', 'user-uuid-456') returning filtered results

### 16-2-action-plans-crud-api-INT-012: List action plans filtered by priority
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist with various priorities
- When: GET /api/v1/action-plans?priority=critical is called
- Then: Response status is 200, only plans with priority='critical' are returned
- Data: Mock Supabase .eq('priority', 'critical') returning filtered results

### 16-2-action-plans-crud-api-INT-013: List action plans with multiple filters combined
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist with various combinations of status, asset, owner, and priority
- When: GET /api/v1/action-plans?status=open&priority=high&asset_id=asset-uuid-123 is called
- Then: Response status is 200, only plans matching ALL filters are returned
- Data: Mock Supabase with chained .eq() calls for all three filters

### 16-2-action-plans-crud-api-INT-014: List action plans with pagination (page and page_size)
- Priority: P0
- Type: integration
- Given: An authenticated user and 25 action plans exist
- When: GET /api/v1/action-plans?page=2&page_size=10 is called
- Then: Response status is 200, ActionPlanListResponse contains items (up to 10), total_count=25, page=2, page_size=10
- Data: Mock Supabase returning 25 total records; verify Python-side pagination slices correctly (offset=10, limit=10)

### 16-2-action-plans-crud-api-INT-015: List action plans with default pagination
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist
- When: GET /api/v1/action-plans is called without page/page_size parameters
- Then: Response defaults to page=1, page_size=20
- Data: Mock Supabase returning results; verify pagination defaults applied

### 16-2-action-plans-crud-api-INT-016: List action plans sorts by priority then due_date
- Priority: P0
- Type: integration
- Given: An authenticated user and plans exist: Plan A (priority=medium, due_date=2026-03-01), Plan B (priority=critical, due_date=2026-04-01), Plan C (priority=medium, due_date=2026-02-15), Plan D (priority=high, due_date=2026-03-10)
- When: GET /api/v1/action-plans is called
- Then: Plans are returned in order: B (critical), D (high), C (medium, earlier date), A (medium, later date)
- Data: Mock Supabase returning 4 plans in arbitrary order; verify Python-side PRIORITY_SORT_MAP sorting with due_date as secondary sort

### 16-2-action-plans-crud-api-INT-017: List action plans with null due_date sorts last within priority
- Priority: P2
- Type: integration
- Given: An authenticated user and plans exist with same priority but some have null due_date
- When: GET /api/v1/action-plans is called
- Then: Plans with null due_date appear after plans with due_date within the same priority group
- Data: Mock Supabase returning plans with mixed null/non-null due_dates at same priority level

### 16-2-action-plans-crud-api-INT-018: List action plans returns empty list when no matches
- Priority: P1
- Type: integration
- Given: An authenticated user and no action plans match the filters
- When: GET /api/v1/action-plans?status=verified is called
- Then: Response status is 200, items=[], total_count=0
- Data: Mock Supabase returning empty data list

### 16-2-action-plans-crud-api-INT-019: List action plans fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: GET /api/v1/action-plans is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-UNIT-004: PRIORITY_SORT_MAP maps all enum values correctly
- Priority: P1
- Type: unit
- Given: The PRIORITY_SORT_MAP dictionary is defined in schemas
- When: All ActionPlanPriority enum values are looked up
- Then: critical=0, high=1, medium=2, low=3
- Data: Direct assertion on PRIORITY_SORT_MAP values

### 16-2-action-plans-crud-api-INT-020: List action plans validates page_size upper bound
- Priority: P2
- Type: integration
- Given: An authenticated user
- When: GET /api/v1/action-plans?page_size=200 is called (exceeds max of 100)
- Then: Response status is 422 (validation error from FastAPI Query constraint le=100)
- Data: page_size=200 exceeding the Query(ge=1, le=100) constraint

## AC2 (supplemental): GET /api/v1/action-plans/{id} - Get single action plan

### 16-2-action-plans-crud-api-INT-021: Get single action plan by ID
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with a known UUID
- When: GET /api/v1/action-plans/{id} is called with the plan's UUID
- Then: Response status is 200, the full ActionPlanResponse is returned with all fields
- Data: Mock Supabase select returning a single plan record

### 16-2-action-plans-crud-api-INT-022: Get action plan returns 404 for non-existent ID
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: GET /api/v1/action-plans/{id} is called with a UUID that does not exist
- Then: Response status is 404 with detail message indicating plan not found
- Data: Mock Supabase select returning empty data

### 16-2-action-plans-crud-api-INT-023: Get action plan fails without authentication
- Priority: P1
- Type: integration
- Given: No Authorization header is provided
- When: GET /api/v1/action-plans/{id} is called
- Then: Response status is 401
- Data: No Bearer token header

## AC3: Given an action plan owner calls PATCH /api/v1/action-plans/{id}, When the request includes updated fields, Then the plan is updated and an action_plan_updates record is created logging the change

### 16-2-action-plans-crud-api-INT-024: Update action plan with status change creates change log
- Priority: P0
- Type: integration
- Given: An authenticated user who owns an action plan with status='open'
- When: PATCH /api/v1/action-plans/{id} is called with {status: 'in_progress'}
- Then: Response status is 200, the plan's status is updated to 'in_progress', and an action_plan_updates record is created with update_text containing "Status changed from open to in_progress" and status_change="open -> in_progress"
- Data: Mock service-role client returning existing plan with status='open'; mock user-scoped client update succeeding; verify insert into action_plan_updates table

### 16-2-action-plans-crud-api-INT-025: Update action plan with multiple field changes logs all changes
- Priority: P0
- Type: integration
- Given: An authenticated user who owns an action plan
- When: PATCH /api/v1/action-plans/{id} is called with {status: 'in_progress', due_date: '2026-04-01', corrective_action: 'New corrective action'}
- Then: Response status is 200, all fields are updated, and the action_plan_updates record's update_text describes all changed fields
- Data: Mock existing plan with original values; verify the auto-generated update_text mentions all three changes

### 16-2-action-plans-crud-api-INT-026: Update action plan by non-owner returns 403
- Priority: P0
- Type: integration
- Given: An authenticated user who does NOT own the action plan (different owner_id)
- When: PATCH /api/v1/action-plans/{id} is called with updated fields
- Then: Response status is 403 indicating the user is not authorized to update this plan (RLS blocks the update via user-scoped client)
- Data: Mock service-role client returning plan with different owner_id; mock user-scoped client update returning empty data (RLS denial)

### 16-2-action-plans-crud-api-INT-027: Update action plan returns 404 for non-existent ID
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: PATCH /api/v1/action-plans/{id} is called with a non-existent UUID
- Then: Response status is 404 with detail message
- Data: Mock service-role client select returning empty data

### 16-2-action-plans-crud-api-INT-028: Update action plan with empty body returns 422
- Priority: P1
- Type: integration
- Given: An authenticated user who owns an action plan
- When: PATCH /api/v1/action-plans/{id} is called with an empty JSON body {} (no fields set)
- Then: Response status is 422 indicating at least one field must be provided for update
- Data: Empty update payload; model_dump(exclude_unset=True) returns {}

### 16-2-action-plans-crud-api-INT-029: Update action plan with only due_date change creates appropriate log
- Priority: P1
- Type: integration
- Given: An authenticated user who owns an action plan with due_date='2026-03-01'
- When: PATCH /api/v1/action-plans/{id} is called with {due_date: '2026-04-15'}
- Then: Response status is 200, due_date is updated, action_plan_updates record has update_text mentioning the date change and status_change is null (no status change occurred)
- Data: Mock existing plan with due_date='2026-03-01'; verify status_change field is null in the inserted update record

### 16-2-action-plans-crud-api-INT-030: Update action plan fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: PATCH /api/v1/action-plans/{id} is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-INT-031: Update action plan uses two-client pattern
- Priority: P1
- Type: integration
- Given: An authenticated user who owns an action plan
- When: PATCH /api/v1/action-plans/{id} is called with valid updates
- Then: create_client is called twice — once with service role key (for existence check) and once with user JWT token (for the update, enforcing RLS)
- Data: Valid update payload; verify create_client call args for both invocations

## AC4: Given a user calls POST /api/v1/action-plans/{id}/updates, When the request includes update_text and optional status_change, Then a progress update is recorded in action_plan_updates, And if status_change is provided, the plan's status is updated

### 16-2-action-plans-crud-api-INT-032: Add progress update without status change
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='open'
- When: POST /api/v1/action-plans/{id}/updates is called with {update_text: 'Investigation completed, root cause identified'}
- Then: Response status is 201, an action_plan_updates record is created with the update_text, author_id=current_user.id, and status_change is null; the plan's status remains 'open'
- Data: Mock plan existence check; mock insert into action_plan_updates; verify no update to action_plans table status

### 16-2-action-plans-crud-api-INT-033: Add progress update with status change updates plan status
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='open'
- When: POST /api/v1/action-plans/{id}/updates is called with {update_text: 'Started working on corrective action', status_change: 'in_progress'}
- Then: Response status is 201, action_plan_updates record is created with update_text and status_change='open -> in_progress', AND the action_plans table is updated with status='in_progress'
- Data: Mock plan existence check returning status='open'; mock both insert into action_plan_updates and update of action_plans.status

### 16-2-action-plans-crud-api-INT-034: Add progress update returns 404 for non-existent plan
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: POST /api/v1/action-plans/{id}/updates is called with a non-existent plan UUID
- Then: Response status is 404 with detail message
- Data: Mock Supabase select returning empty data for plan lookup

### 16-2-action-plans-crud-api-INT-035: Add progress update fails without update_text
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists
- When: POST /api/v1/action-plans/{id}/updates is called with {} (missing update_text)
- Then: Response status is 422 (Pydantic validation error for missing required field)
- Data: Empty or missing update_text in request body

### 16-2-action-plans-crud-api-INT-036: Add progress update fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: POST /api/v1/action-plans/{id}/updates is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-INT-037: Add progress update with status_change to invalid status returns 422
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists
- When: POST /api/v1/action-plans/{id}/updates is called with {update_text: 'text', status_change: 'invalid_status'}
- Then: Response status is 422 (Pydantic validation error for invalid enum value)
- Data: Payload with status_change set to an invalid ActionPlanStatus value

## AC4 (supplemental): GET /api/v1/action-plans/{id}/updates - List progress updates

### 16-2-action-plans-crud-api-INT-038: List progress updates for a plan returns chronological order
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan with multiple progress updates
- When: GET /api/v1/action-plans/{id}/updates is called
- Then: Response status is 200, updates are returned sorted chronologically (oldest first) by created_at
- Data: Mock Supabase returning multiple update records with varying created_at timestamps

### 16-2-action-plans-crud-api-INT-039: List progress updates returns 404 for non-existent plan
- Priority: P1
- Type: integration
- Given: An authenticated user
- When: GET /api/v1/action-plans/{id}/updates is called with a non-existent plan UUID
- Then: Response status is 404
- Data: Mock Supabase select returning empty data for plan lookup

### 16-2-action-plans-crud-api-INT-040: List progress updates returns empty list when no updates exist
- Priority: P2
- Type: integration
- Given: An authenticated user and an action plan exists but has no progress updates
- When: GET /api/v1/action-plans/{id}/updates is called
- Then: Response status is 200, returns empty list
- Data: Mock Supabase returning empty data for updates query

## AC5: Given a user calls POST /api/v1/action-plans/{id}/verify, When the user confirms the fix worked, Then the plan status is set to 'verified', verified_by and verified_at are recorded

### 16-2-action-plans-crud-api-INT-041: Verify completed action plan succeeds
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='completed'
- When: POST /api/v1/action-plans/{id}/verify is called (with optional verification_notes)
- Then: Response status is 200, plan status is set to 'verified', verified_by=current_user.id, verified_at is a valid timestamp, and an action_plan_updates record is created logging the verification
- Data: Mock service-role client returning plan with status='completed'; mock service-role update setting verified fields; mock insert into action_plan_updates

### 16-2-action-plans-crud-api-INT-042: Verify action plan returns 400 when status is not 'completed'
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='open'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 400 with detail message indicating plan must be in 'completed' status to verify
- Data: Mock service-role client returning plan with status='open'

### 16-2-action-plans-crud-api-INT-043: Verify action plan returns 400 when status is 'in_progress'
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists with status='in_progress'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 400 with detail message
- Data: Mock service-role client returning plan with status='in_progress'

### 16-2-action-plans-crud-api-INT-044: Verify action plan returns 404 for non-existent ID
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: POST /api/v1/action-plans/{id}/verify is called with a non-existent UUID
- Then: Response status is 404
- Data: Mock service-role client select returning empty data

### 16-2-action-plans-crud-api-INT-045: Verify action plan can be done by non-owner (cross-user verification)
- Priority: P0
- Type: integration
- Given: An authenticated user who is NOT the owner of the action plan, and the plan has status='completed'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 200, plan is verified with verified_by set to the current (non-owner) user's ID (uses service-role client to bypass owner-only RLS)
- Data: Mock service-role client returning plan with different owner_id than current user; verify service-role client used for update (not user-scoped)

### 16-2-action-plans-crud-api-INT-046: Verify action plan fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-INT-047: Verify action plan with verification_notes records notes
- Priority: P2
- Type: integration
- Given: An authenticated user and an action plan exists with status='completed'
- When: POST /api/v1/action-plans/{id}/verify is called with {verification_notes: 'Verified fix on production line 3'}
- Then: Response status is 200 and the action_plan_updates record includes the verification notes in its update_text
- Data: Mock service-role client returning completed plan; verify notes appear in the logged update record

### 16-2-action-plans-crud-api-INT-048: Verify already verified plan returns 400
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists with status='verified'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 400 with detail message indicating plan is already verified (or must be in 'completed' status)
- Data: Mock service-role client returning plan with status='verified'

## Schema Validation (Cross-cutting)

### 16-2-action-plans-crud-api-UNIT-005: ActionPlanCategory enum has correct values
- Priority: P1
- Type: unit
- Given: The ActionPlanCategory enum is defined
- When: Enum members are inspected
- Then: Values are exactly 'corrective', 'preventive', 'improvement' matching DB CHECK constraint
- Data: Direct enum value assertions

### 16-2-action-plans-crud-api-UNIT-006: ActionPlanStatus enum has correct values
- Priority: P1
- Type: unit
- Given: The ActionPlanStatus enum is defined
- When: Enum members are inspected
- Then: Values are exactly 'draft', 'open', 'in_progress', 'completed', 'verified' matching DB CHECK constraint
- Data: Direct enum value assertions

### 16-2-action-plans-crud-api-UNIT-007: ActionPlanPriority enum has correct values
- Priority: P1
- Type: unit
- Given: The ActionPlanPriority enum is defined
- When: Enum members are inspected
- Then: Values are exactly 'low', 'medium', 'high', 'critical' matching DB CHECK constraint
- Data: Direct enum value assertions

### 16-2-action-plans-crud-api-UNIT-008: ActionPlanResponse schema includes all expected fields
- Priority: P1
- Type: unit
- Given: The ActionPlanResponse schema is defined
- When: Schema model_fields are inspected
- Then: All fields are present: id, title, description, asset_id, category, root_cause, corrective_action, preventive_action, source_followup_id, owner_id, status, priority, due_date, completed_at, verified_by, verified_at, created_at, updated_at
- Data: Direct schema field inspection

### 16-2-action-plans-crud-api-UNIT-009: ActionPlanListResponse schema includes pagination fields
- Priority: P1
- Type: unit
- Given: The ActionPlanListResponse schema is defined
- When: Schema model_fields are inspected
- Then: Fields include items (list of ActionPlanResponse), total_count, page, page_size
- Data: Direct schema field inspection

### 16-2-action-plans-crud-api-UNIT-010: ActionPlanUpdate schema uses model_dump exclude_unset correctly
- Priority: P1
- Type: unit
- Given: An ActionPlanUpdate instance with only due_date set
- When: model_dump(exclude_unset=True) is called
- Then: Only the due_date field is in the resulting dict (other optional fields are excluded)
- Data: ActionPlanUpdate(due_date='2026-04-01'); verify dict has only 'due_date' key

## Router Registration

### 16-2-action-plans-crud-api-INT-049: Action plans router is registered at correct prefix
- Priority: P0
- Type: integration
- Given: The FastAPI application is initialized
- When: The app's routes are inspected
- Then: Routes exist under the /api/v1/action-plans prefix with all expected methods (GET, POST, PATCH)
- Data: Inspect app.routes for /api/v1/action-plans paths

edge_cases:
  - Action plan with due_date in the past is still accepted (no server-side future-date validation)
  - Concurrent updates to the same action plan (last write wins, no optimistic locking)
  - Very long update_text or description fields (DB TEXT type has no practical limit)
  - Unicode characters in title, description, and update_text fields
  - UUID format validation for asset_id, source_followup_id path parameters
  - Pagination beyond available results (page=100 when only 5 records exist) returns empty items with correct total_count
  - Updating a 'verified' plan back to a different status (no state machine enforcement in this story)

error_scenarios:
  - Supabase connection failure on any endpoint returns 500
  - Expired JWT token returns 401
  - Invalid JWT token returns 401
  - Malformed UUID in path parameter returns 422
  - Request body with extra fields rejected (ConfigDict extra="forbid") returns 422
  - RLS policy denial on update by non-owner returns 403
  - Empty PATCH body returns 422
  - Verify on non-completed plan returns 400
  - Non-existent plan ID on GET/PATCH/POST updates/verify returns 404

test_file_mapping:
  - 16-2-action-plans-crud-api-INT-*: apps/api/tests/test_action_plans_api.py
  - 16-2-action-plans-crud-api-UNIT-*: apps/api/tests/test_action_plans_api.py
  - 16-2-action-plans-crud-api-E2E-*: apps/api/tests/test_action_plans_api.py

TEST SPEC END

---

## DESIGN: 16-3-create-action-plan-from-followup
**Timestamp:** 2026-02-12 00:58:02

DESIGN START
story_id: 16-3-create-action-plan-from-followup

files_to_modify:
  - path: apps/web/src/hooks/useActionPlans.ts
    action: create
    purpose: Hook for creating action plans (POST /api/v1/action-plans) and querying action plans by source_followup_id. Follows useDailyActions.ts pattern with useState, useCallback, mountedRef, Supabase auth session for Bearer token.
  - path: apps/web/src/components/action-plans/ActionPlanForm.tsx
    action: create
    purpose: Dialog form component for creating action plans with pre-filled data from follow-up context. Follows AssignFollowUpDialog.tsx pattern exactly — Dialog/DialogContent/DialogHeader/DialogFooter with form state via useState, loading/error/success states, and auto-close on success.
  - path: apps/web/src/components/action-plans/index.ts
    action: create
    purpose: Barrel export for ActionPlanForm component, following action-engine/index.ts and action-list/index.ts patterns.
  - path: apps/web/src/components/action-list/FollowUpDetailDialog.tsx
    action: modify
    purpose: Add "Create Action Plan" button at the bottom of the dialog when followUp.status !== 'assigned' (AC#3). Show linked action plan link when an action plan already exists for this follow-up (AC#2, AC#5). Wire button to open ActionPlanForm dialog with pre-filled data. Add state management for ActionPlanForm dialog open/close and linked plan lookup.
  - path: apps/web/src/components/action-list/FollowUpEntry.tsx
    action: modify
    purpose: Minor addition — show a small "Action Plan" badge/indicator on the follow-up entry when a linked action plan exists, providing at-a-glance visibility before opening the detail dialog (AC#2).

patterns_to_use:
  - useDailyActions.ts hook pattern: 'use client' directive, custom TypeScript interfaces at top, API_BASE_URL from env with fallback, mountedRef for cleanup, useCallback for async operations, Supabase createClient() for auth.getSession(), fetch() with Bearer token, error handling with specific HTTP status codes (401/404/500), loading/error state management.
  - AssignFollowUpDialog.tsx dialog pattern: Props interface with open/onOpenChange/data, useState for form fields + loading + submitted + error, useEffect for resetting state on open, useCallback for submit handler, Dialog/DialogContent/DialogHeader/DialogFooter from @/components/ui/dialog, success state with CheckCircle2 icon, auto-close via setTimeout after 1500ms, Button with Loader2 spinner during submission.
  - Supabase direct client for asset lookup: createClient() from @/lib/supabase/client for querying assets table to resolve asset_name -> asset_id, following the same pattern as useFollowUps.ts where Supabase is used directly for table lookups.
  - API fetch pattern for action plan creation: POST to ${apiUrl}/api/v1/action-plans with Bearer token from session.access_token, matching the exact pattern in AssignFollowUpDialog.tsx lines 112-128.
  - Form components from existing UI library: Input from @/components/ui/input, Textarea from @/components/ui/textarea, Select/SelectTrigger/SelectContent/SelectItem from @/components/ui/select (Radix-based), Button from @/components/ui/button. Native <input type="date"> for date picker with cn() utility styling.
  - Test pattern from action-list/__tests__: vi.mock('next/navigation'), vi.mock for hooks, render/screen/fireEvent from @testing-library/react, describe/it/expect from vitest, fixture objects for mock data.

dependencies:
  - next: installed (App Router framework)
  - react: installed (UI library)
  - @supabase/ssr: installed (Supabase browser client via createBrowserClient)
  - @radix-ui/react-select: installed (Select component primitives)
  - @radix-ui/react-dialog: installed (Dialog component primitives)
  - lucide-react: installed (icons - ClipboardPlus, CheckCircle2, Loader2, ExternalLink)
  - vitest: installed (test runner)
  - @testing-library/react: installed (component testing)
  - Story 16.1 (0034_action_plans.sql migration): installed (action_plans table exists)
  - Story 16.2 (POST /api/v1/action-plans endpoint): installed (API endpoint exists in apps/api/app/api/action_plans.py)

acceptance_criteria_mapping:
  - AC1 (Pre-populated form from follow-up response): apps/web/src/components/action-plans/ActionPlanForm.tsx — accepts `prefill` prop with FollowUpItem data + response text from messages. On dialog open, resolves asset_id from followUp.asset_name via Supabase assets table lookup. Pre-fills form fields per the mapping table in story dev notes: title = "Action Plan: {action_summary}" truncated to 80 chars, description = action_summary + note, root_cause = response body text from inbound messages, category mapped from followUp.category (safety->corrective, oee->improvement, financial->corrective), priority mapped (safety->high, oee/financial->medium), source_followup_id = followUp.id. All fields editable by manager before save. apps/web/src/components/action-list/FollowUpDetailDialog.tsx — "Create Action Plan" button opens ActionPlanForm with pre-filled context extracted from the followUp and its messages.
  - AC2 (Linked action plan visible on follow-up detail): apps/web/src/hooks/useActionPlans.ts — provides getActionPlanByFollowUpId() function that queries GET /api/v1/action-plans?source_followup_id={id} or queries action_plans table via Supabase where source_followup_id = followUp.id. apps/web/src/components/action-list/FollowUpDetailDialog.tsx — on dialog open, checks for existing linked plan. If found, shows "Action Plan: {title}" link/badge with ExternalLink icon instead of the "Create Action Plan" button. Link navigates to /action-plans/{id}.
  - AC3 (Button hidden when no response): apps/web/src/components/action-list/FollowUpDetailDialog.tsx — conditionally renders "Create Action Plan" button only when followUp.status !== 'assigned'. The status check maps to the story requirement: 'assigned' means no response yet, 'in_progress' or 'resolved' means there has been engagement/response from the assignee. Additionally checks if messages contain any inbound (response) messages for extra safety.
  - AC4 (Submit with required fields via POST): apps/web/src/components/action-plans/ActionPlanForm.tsx — form validation requires title, category, priority, due_date before enabling submit. Submit handler calls POST /api/v1/action-plans with status='open' (backend sets this automatically per story 16.2 AC#1) and owner_id set server-side from JWT. Uses fetch() with Bearer token pattern matching AssignFollowUpDialog.tsx.
  - AC5 (Follow-up updates without full page reload): apps/web/src/components/action-list/FollowUpDetailDialog.tsx — after ActionPlanForm onSuccess callback fires, the dialog updates its local state to show the linked action plan immediately without re-rendering the page. Uses setState to switch from showing the "Create Action Plan" button to showing the linked plan link/badge. The onSuccess callback receives the created plan's id and title.

risks:
  - Asset ID resolution from asset_name: The action_followups table stores asset_name (TEXT), not asset_id (UUID). Need to look up asset_id from the assets table. MITIGATION: Query assets table with .eq('name', followUp.asset_name).single(). If no match, set asset_id to null (nullable in action_plans schema). Handle gracefully in UI by showing "Asset not found" or just omitting it.
  - Determining "has response" for AC#3: The story says button shows only when follow-up "has a response". MITIGATION: Use followUp.status !== 'assigned' as the primary check (status transitions to 'in_progress' or 'resolved' indicate engagement). Additionally can check if messages from useFollowUpMessages contain any inbound messages, but the status check is sufficient and simpler.
  - Source followup ID uniqueness: When checking if an action plan already exists for a follow-up (AC#2), we query action_plans where source_followup_id = followUp.id. Multiple plans could theoretically exist for the same follow-up. MITIGATION: Take the first/most-recent result for display purposes. The UI shows one link; if multiple exist, show the latest one.
  - Response text extraction for root_cause pre-fill: The assignee's investigation response comes through the messaging system (useFollowUpMessages hook) as inbound messages with message_type='response'. The FollowUpDetailDialog already uses useFollowUpMessages, so we can extract inbound message bodies for the pre-fill. MITIGATION: Concatenate all inbound message bodies with newlines for root_cause pre-fill, or use the latest inbound message body. Pass this data from FollowUpDetailDialog to ActionPlanForm via the prefill prop.
  - Select component vs native select: The existing AssignFollowUpDialog uses a native <select> element (line 191-207), while Shadcn Select component is also available. MITIGATION: Use the Radix-based Select from @/components/ui/select for category and priority dropdowns since it provides better styling consistency and is available in the project. This is a controlled component that works well in dialog forms.

estimated_test_files:
  - apps/web/src/components/action-plans/__tests__/ActionPlanForm.test.tsx: Tests ActionPlanForm component rendering with pre-filled data, required field validation (title/category/priority/due_date), successful submission calls API, error state display, form field editability, success state and auto-close.
  - apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx: Extend existing test file to add tests for "Create Action Plan" button visibility (shown when status !== 'assigned', hidden when status === 'assigned'), linked action plan display when plan exists, button opens ActionPlanForm dialog, post-creation update without page reload.
  - apps/web/src/hooks/__tests__/useActionPlans.test.ts: Tests for createActionPlan() function (API call with correct payload/headers), getLinkedActionPlan() function (query by source_followup_id), error handling (401/500), loading states.

implementation_order:
  1. Create apps/web/src/hooks/useActionPlans.ts — implement createActionPlan() function that POSTs to /api/v1/action-plans with Bearer token, and getLinkedActionPlan() that queries action_plans by source_followup_id (either via API GET with filter or direct Supabase query). Define TypeScript interfaces: ActionPlanCreateRequest (matching API schema: title, description, category, root_cause, corrective_action, preventive_action, asset_id, priority, due_date, source_followup_id), ActionPlanResponse (matching API response), UseActionPlansReturn.
  2. Create apps/web/src/components/action-plans/ActionPlanForm.tsx — Dialog form component accepting prefill prop (followUpId, actionSummary, assetName, note, responseText, category). On mount, resolve asset_id from asset_name via Supabase assets table. Build form with fields: title (Input, required), description (Textarea), category (Select: corrective/preventive/improvement, required), root_cause (Textarea), corrective_action (Textarea), preventive_action (Textarea), priority (Select: low/medium/high/critical, required), due_date (native date input, required), asset display (read-only text showing asset_name). Submit handler calls createActionPlan() from useActionPlans hook. Success/error/loading state management. onSuccess callback prop returning created plan data.
  3. Create apps/web/src/components/action-plans/index.ts — barrel export for ActionPlanForm.
  4. Modify apps/web/src/components/action-list/FollowUpDetailDialog.tsx — (a) Import ActionPlanForm and useActionPlans hook. (b) Add useState for actionPlanDialogOpen and linkedPlan. (c) On dialog open (useEffect), call getLinkedActionPlan(followUp.id) to check if plan already exists. (d) Add conditional rendering at bottom of dialog content: if linkedPlan exists, show "Action Plan: {title}" link with Badge; else if followUp.status !== 'assigned', show "Create Action Plan" button (ClipboardPlus icon). (e) Wire button onClick to open ActionPlanForm with prefill data including response text from messages (inbound messages). (f) On ActionPlanForm success, update linkedPlan state immediately (AC#5 no reload) and close the action plan form dialog.
  5. Modify apps/web/src/components/action-list/FollowUpEntry.tsx — Add optional linkedActionPlanId prop. When set, show a small visual indicator (e.g., ClipboardCheck icon or tiny badge) to indicate an action plan exists for this follow-up, providing at-a-glance visibility in the list view.
  6. Create apps/web/src/components/action-plans/__tests__/ActionPlanForm.test.tsx — Test pre-fill rendering, required field validation, submit API call, error/success states.
  7. Update apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx — Add test cases for: "Create Action Plan" button visibility by status, linked plan display, button opens form, post-creation state update.
DESIGN END

---

## DESIGN: 16-4-active-plans-badge-on-action-cards
**Timestamp:** 2026-02-12 01:53:29

DESIGN START
story_id: 16-4-active-plans-badge-on-action-cards

files_to_modify:
  - path: apps/web/src/hooks/useActiveActionPlans.ts
    action: create
    purpose: New hook to fetch active (open/in_progress) action plans for a given asset_id. Follows useDailyActions.ts pattern with useState, useCallback, useEffect, mountedRef, Supabase auth session for Bearer token. Calls GET /api/v1/action-plans?status=open&asset_id={id} and GET /api/v1/action-plans?status=in_progress&asset_id={id} (two calls since the backend status filter accepts a single ActionPlanStatus enum value, not comma-separated). Returns typed ActiveActionPlan[] with id, title, due_date, status. Handles loading, error, and empty states. Skips fetch when assetId is undefined.
  - path: apps/web/src/components/action-engine/ActivePlanBadge.tsx
    action: create
    purpose: Badge component that shows active action plan info on action cards. Single plan renders Badge variant="info" with "Plan: {title} (due {date})". Multiple plans renders Badge variant="info" with "{N} active plans" and a Tooltip listing plan titles (since no Popover/DropdownMenu exists in the UI library, Tooltip is the simplest available Radix primitive). No plans or only completed/verified plans renders null. Click navigates to /action-plans/{id} for single or /action-plans?asset_id={id} for multiple. Follows AssignmentBadge/RepeatOffenderBadge pattern with aria-label and role="link" semantics.
  - path: apps/web/src/components/action-engine/InsightSection.tsx
    action: modify
    purpose: Add assetId prop to InsightSectionProps. Import and render ActivePlanBadge in the context row div (line 134), placed between the timestamp div and the acknowledge button. Pass assetId to the badge. The badge self-manages its data fetching via useActiveActionPlans hook internally, so no upstream data plumbing needed beyond the assetId prop.
  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Pass item.asset.id as assetId prop to InsightSection (line 91-103). Minimal change — just add assetId={item.asset.id} to the InsightSection JSX.
  - path: apps/web/src/components/action-engine/index.ts
    action: modify
    purpose: Add ActivePlanBadge export to the barrel file, following the existing pattern of Subcomponents exports section.
  - path: apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx
    action: create
    purpose: Test file covering all 3 ACs — single plan badge rendering, multiple plans summary badge, no badge for empty/completed-only states, click navigation, loading state, error silence. Follows AssignmentBadge.test.tsx pattern with vi.mock for next/navigation and @/lib/supabase/client, mockFetch for API calls, createMockActionPlan fixture factory.

patterns_to_use:
  - useDailyActions.ts hook pattern: 'use client' directive, API_BASE_URL from env with fallback, mountedRef for cleanup, useCallback for async fetch, useEffect for auto-fetch with assetId dependency, useState for data/isLoading/error state. Supabase createClient() → getSession() → access_token for Bearer auth.
  - AssignmentBadge/RepeatOffenderBadge component pattern: Lookup table for status → variant mapping, conditional rendering with early null returns, Badge component from @/components/ui/badge with variant="info", cn() for conditional classes, aria-label for accessibility, lucide-react icons (ClipboardList for plan icon).
  - Two-request approach for multi-status filter: The backend GET /api/v1/action-plans accepts a single ActionPlanStatus enum value per query (line 166: `status: Optional[ActionPlanStatus]`). To fetch both "open" and "in_progress" plans, make two parallel requests (Promise.all) or make a single request without the status filter and filter client-side. DECISION: Make a single request without status filter and filter client-side to active statuses only, since the response will be small per asset. This avoids the need to modify the backend for comma-separated status support.
  - Tooltip for multiple plans display: No Popover or DropdownMenu component exists in the UI library. Use the existing Tooltip component (Radix-based) from @/components/ui/tooltip to show a hover list of plan titles when multiple plans exist. The badge itself navigates to the filtered plans view on click.
  - InsightSection prop threading: Add assetId as an optional prop to InsightSectionProps. InsightEvidenceCard already has access to item.asset.id and will pass it through. The ActivePlanBadge component calls useActiveActionPlans internally with this assetId.
  - Test pattern from AssignmentBadge.test.tsx: vi.mock next/navigation, vi.mock @/lib/supabase/client, mockFetch for API calls, createMock fixture factories, describe blocks organized by AC, Given/When/Then comments, dynamic import for integration tests.

dependencies:
  - next: installed (App Router framework, useRouter for navigation)
  - react: installed (hooks: useState, useEffect, useCallback, useRef, useMemo)
  - @radix-ui/react-tooltip: installed (Tooltip for multiple plans display)
  - lucide-react: installed (ClipboardList icon for plan badge)
  - @/components/ui/badge: installed (Badge component with info variant)
  - @/components/ui/tooltip: installed (Tooltip, TooltipTrigger, TooltipContent, TooltipProvider)
  - @/lib/supabase/client: installed (createClient for auth session)
  - vitest: installed (test runner)
  - @testing-library/react: installed (component testing)
  - Story 16.1 (action_plans table with indexes on asset_id, status): installed
  - Story 16.2 (GET /api/v1/action-plans endpoint with asset_id filter): installed

acceptance_criteria_mapping:
  - AC1 (single active plan → badge with title/date/status, click opens detail): apps/web/src/hooks/useActiveActionPlans.ts — fetches action plans for asset, filters to open/in_progress client-side. apps/web/src/components/action-engine/ActivePlanBadge.tsx — when plans.length === 1, renders Badge variant="info" with "Plan: {title} (due {formatted_date})" wrapped in a button/link that navigates to /action-plans/{id} via useRouter().push(). apps/web/src/components/action-engine/InsightSection.tsx — renders ActivePlanBadge in context row with assetId prop. apps/web/src/components/action-engine/InsightEvidenceCard.tsx — passes item.asset.id as assetId to InsightSection.
  - AC2 (multiple active plans → summary badge with dropdown/link): apps/web/src/hooks/useActiveActionPlans.ts — returns full array of active plans. apps/web/src/components/action-engine/ActivePlanBadge.tsx — when plans.length > 1, renders Badge variant="info" with "{N} active plans" text. Wrapped in TooltipProvider/Tooltip/TooltipTrigger showing plan titles on hover via TooltipContent. Click navigates to /action-plans?asset_id={id} to view all plans for the asset.
  - AC3 (no active plans or only completed/verified → no badge): apps/web/src/hooks/useActiveActionPlans.ts — returns empty array when no open/in_progress plans exist. apps/web/src/components/action-engine/ActivePlanBadge.tsx — when plans.length === 0, returns null (renders nothing). The client-side filter excludes draft/completed/verified statuses.

risks:
  - N+1 fetch problem (one API call per action card per asset): Each action card with a unique asset will trigger a separate fetch. For a typical morning report with 5-10 action items, this means 5-10 additional API calls. MITIGATION: Acceptable for MVP per story dev notes. The calls are lightweight (filtered by asset_id with small result sets). Future optimization could batch-fetch all asset plans at the InsightEvidenceCardList level and pass results down. For now, per-card fetch is acceptable.
  - Backend status filter does not support comma-separated values: The story tasks mention `status=open,in_progress` but the backend enum parser (FastAPI Query with ActionPlanStatus) only accepts a single value. MITIGATION: Rather than modifying the backend (which would be scope creep for this story), fetch without status filter and filter client-side. The result set per asset will be small (typically 0-3 plans). This avoids any backend changes in Task 4 — the existing asset_id filter + client-side status filter is sufficient. Document this decision.
  - No Popover or DropdownMenu component available: The story subtask 2.3 mentions using Popover or DropdownMenu for multiple plans, but neither exists in the UI library. MITIGATION: Use the existing Tooltip component for showing plan titles on hover, and make the badge click navigate to the filtered plans list page (/action-plans?asset_id={id}). This provides both quick-view (hover) and detailed navigation (click). If a Popover is added later, the badge can be upgraded.
  - No /action-plans route may exist yet: The badge click navigates to /action-plans/{id} or /action-plans?asset_id={id}, but the action plans page may not be built yet (it's in a later story). MITIGATION: Use router.push() for navigation so the URL updates. If the page doesn't exist, Next.js will show its default 404. This is acceptable since the badge functionality is self-contained and the route will be built in a future story.
  - Badge placement may affect layout on mobile: Adding an element to the context row (which uses flex-wrap) could cause reflow on small screens. MITIGATION: Badge uses same size classes as other context row elements (text-sm, inline-flex). The flex-wrap already handles overflow gracefully. Test on mobile viewport.
  - Asset ID could be empty string: The ActionItem.asset.id could theoretically be empty. MITIGATION: The hook skips fetch when assetId is undefined or empty string. ActivePlanBadge checks for valid assetId before rendering.

estimated_test_files:
  - apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx: Tests all 3 ACs. AC1: renders badge with title and due date for single active plan, click navigates to /action-plans/{id}. AC2: renders "{N} active plans" summary badge for multiple plans, tooltip shows plan titles on hover, click navigates to /action-plans?asset_id={id}. AC3: renders null when no plans, renders null when only completed/verified plans exist. Additional: handles loading state (no visual blocking), handles API error silently (renders null), barrel file exports ActivePlanBadge. Uses mockFetch to simulate API responses, vi.mock for next/navigation and supabase client.

implementation_order:
  1. Create apps/web/src/hooks/useActiveActionPlans.ts — New hook following useDailyActions.ts pattern. Accepts assetId: string parameter. Fetches GET /api/v1/action-plans?asset_id={id} with Bearer token auth. Filters response client-side to status in ['open', 'in_progress']. Returns { plans: ActiveActionPlan[], isLoading: boolean, error: string | null }. Uses mountedRef for cleanup, skips fetch when assetId is undefined/empty. Define ActiveActionPlan interface (id, title, due_date, status).
  2. Create apps/web/src/components/action-engine/ActivePlanBadge.tsx — Component accepting ActivePlanBadgeProps { assetId: string, className?: string }. Calls useActiveActionPlans(assetId) internally. Renders: null for 0 plans or loading/error states; Badge variant="info" with plan title + due date for 1 plan (clickable link to /action-plans/{id}); Badge variant="info" with "{N} active plans" for multiple plans wrapped in Tooltip showing list (clickable link to /action-plans?asset_id={id}). Uses useRouter for navigation, ClipboardList icon from lucide-react, formatDate helper for due_date display.
  3. Modify apps/web/src/components/action-engine/InsightSection.tsx — Add optional assetId?: string prop to InsightSectionProps interface (line 26-40). Import ActivePlanBadge. Render <ActivePlanBadge assetId={assetId} /> in the context row div (after timestamp div at line 159, before the acknowledge button div at line 162). Conditionally render only when assetId is truthy.
  4. Modify apps/web/src/components/action-engine/InsightEvidenceCard.tsx — Add assetId={item.asset.id} prop to the InsightSection JSX at line 91-103. Single line change.
  5. Modify apps/web/src/components/action-engine/index.ts — Add export { ActivePlanBadge } from './ActivePlanBadge' to the Subcomponents section.
  6. Create apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx — Write tests covering all ACs following AssignmentBadge.test.tsx patterns. Test: single plan badge rendering with correct title/date, multiple plans summary badge, null rendering for empty/completed states, click navigation, loading/error handling, barrel export, integration with InsightSection.
  7. Run tests with vitest to verify all pass.
DESIGN END

---

## TEST_SPEC: 16-4-active-plans-badge-on-action-cards
**Timestamp:** 2026-02-12 01:56:16

TEST SPEC START
story_id: 16-4-active-plans-badge-on-action-cards
generated: 2026-02-12
```

**28 test specifications** covering **3 acceptance criteria**:

| AC | Coverage | Test Count |
|---|---|---|
| **AC1** - Single active plan badge | Badge rendering, info variant, click navigation, aria-label, role semantics, hook fetch/auth, client-side filtering, skip-when-empty | 11 specs (UNIT-001 through UNIT-011) |
| **AC2** - Multiple active plans summary | Summary count text, 3+ count, tooltip on hover, click navigation, info variant, aria-label | 6 specs (UNIT-012 through UNIT-017) |
| **AC3** - No badge for empty/completed | No plans, completed-only, verified-only, draft-only, mixed inactive, mixed active+inactive | 6 specs (UNIT-018 through UNIT-023) |
| **Integration** | InsightSection integration, InsightEvidenceCard prop passing, layout preservation, barrel export | 4 specs (INT-001 through INT-004) |
| **Loading/Error** | Loading state, API 500, network error, auth error, unmount cleanup | 5 specs (UNIT-024 through UNIT-028) |

Plus **8 edge cases** and **7 error scenarios** documented.

All test specs map to: `apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx`

```json
{
  "status": "COMPLETE",
  "story_id": "16-4-active-plans-badge-on-action-cards",
  "summary": "Generated 28 test specifications for 3 acceptance criteria",
  "tests_added": 28
}
```

TEST SPEC COMPLETE: 16-4-active-plans-badge-on-action-cards - Generated 28 specifications

---

## DESIGN: 16-5-action-plans-dashboard
**Timestamp:** 2026-02-12 03:03:26

DESIGN START
story_id: 16-5-action-plans-dashboard

files_to_modify:
  - path: apps/web/src/components/action-plans/types.ts
    action: create
    purpose: TypeScript interfaces for ActionPlan, ActionPlanUpdate, ActionPlanListResponse, status/priority string literal types, and helper types (DueStatus, GroupedPlans) used across all dashboard components. Extends the existing ActionPlanResponse from useActionPlans.ts with additional fields (asset_name, owner_email, updates) needed by the dashboard display. NOTE: The story spec shows asset_name and owner_email in the response but the actual API ActionPlanResponse (from 16.2) does NOT include these fields — the DB only stores asset_id and owner_id. The types.ts will mirror the actual API shape, and the dashboard will display owner_id and resolve asset_name client-side or show "Unknown" if needed.

  - path: apps/web/src/hooks/useActionPlansDashboard.ts
    action: create
    purpose: New hook specifically for the dashboard listing/filtering use case. Cannot reuse/extend the existing useActionPlans.ts because that hook only provides createActionPlan() and getLinkedActionPlan() — it has no list-all, filter, or auto-fetch capabilities. This new hook follows the useDailyActions.ts pattern exactly: useState/useEffect/useCallback/mountedRef, Supabase auth session for Bearer token, auto-fetch on mount and when filter params change. Accepts filter params (status, asset_id, priority, owner_id), returns { plans, isLoading, error, refetch, grouped, totalCount }. Syncs filter state to/from URL search params using useSearchParams()/useRouter() from next/navigation (AC #4). Groups plans by status client-side for section rendering.

  - path: apps/web/src/components/action-plans/ActionPlanCard.tsx
    action: create
    purpose: Individual plan card component for the dashboard list. Displays: title, asset_id (or "Plant-wide" if null), priority badge, owner_id, due date, overdue/due-soon indicator. Uses Card from ui/card, Badge from ui/badge. Reuses color coding from PriorityBadge.tsx for priority display. Implements getDueStatus() helper for overdue logic (AC #2). Click handler opens ActionPlanDetail dialog (AC #3). Status badge with color coding per story spec.

  - path: apps/web/src/components/action-plans/ActionPlanDetail.tsx
    action: create
    purpose: Detail/edit dialog for a single action plan (AC #3). Follows AssignFollowUpDialog.tsx pattern — Dialog with sections: title header with status badge, full description, root cause, corrective action, preventive action, owner, dates, source follow-up link. Fetches plan updates via GET /api/v1/action-plans/{id}/updates. Renders UpdateTimeline component. Provides "Add Update" form (text input + optional status change dropdown, calls POST /api/v1/action-plans/{id}/updates). Status change action buttons ("Mark In Progress", "Mark Completed", "Verify") based on current status, calling PATCH /api/v1/action-plans/{id} or POST /api/v1/action-plans/{id}/verify as appropriate.

  - path: apps/web/src/components/action-plans/UpdateTimeline.tsx
    action: create
    purpose: Vertical timeline component rendering action_plan_updates in reverse chronological order (AC #3). Each entry shows: author_id, update text, status change (if any, as "Status: open -> in_progress"), relative timestamp via formatRelativeTime() utility. Uses simple CSS timeline pattern with Tailwind left-border + dot markers. No external timeline library.

  - path: apps/web/src/components/action-plans/index.ts
    action: modify
    purpose: Extend existing barrel exports to include ActionPlanCard, ActionPlanDetail, UpdateTimeline, and types re-export. Currently exports only ActionPlanForm and ActionPlanPrefill.

  - path: apps/web/src/app/(main)/action-plans/page.tsx
    action: create
    purpose: Dashboard page at /action-plans (AC #1, #4). CRITICAL: Must be inside (main) route group to get the AppShell layout with sidebar/header and authentication guard — all other authenticated pages (handoff, dashboard, morning-report, briefing, settings) are under (main). 'use client' page since it uses hooks (useSearchParams, useState). Page header with "Action Plans" title + count badge. Filter bar with Select dropdowns for status, priority, asset, owner. Grouped layout rendering ActionPlanCard items by status section with section headers ("Open (3)", "In Progress (5)"). Loading skeleton, empty state, error state with retry.

  - path: apps/web/src/components/navigation/AppSidebar.tsx
    action: modify
    purpose: Add "Action Plans" navigation link to the Operations nav group after "Shift Handoffs" (AC #1). Add Target icon import from lucide-react. The existing isActive() function already handles /action-plans via the generic pathname.startsWith(href) fallback for paths other than /dashboard and /morning-report, so no isActive() change needed.

  - path: apps/web/src/components/action-plans/__tests__/ActionPlanCard.test.tsx
    action: create
    purpose: Unit tests for ActionPlanCard component. Tests: renders title/priority/owner/due date, overdue highlighting (AC #2), due-soon amber indicator, click handler fires, status badge color coding, "Plant-wide" display for null asset_id.

  - path: apps/web/src/components/action-plans/__tests__/ActionPlanDetail.test.tsx
    action: create
    purpose: Unit tests for ActionPlanDetail dialog. Tests: renders all plan fields, timeline section, add update form submission, status change buttons visibility per current status, source follow-up link display.

  - path: apps/web/src/components/action-plans/__tests__/UpdateTimeline.test.tsx
    action: create
    purpose: Unit tests for UpdateTimeline. Tests: reverse chronological ordering, status change display, relative time formatting, empty timeline.

  - path: apps/web/src/components/action-plans/__tests__/ActionPlansDashboard.test.tsx
    action: create
    purpose: Integration tests for the dashboard page. Tests: grouped rendering, filter state URL sync, loading skeleton, empty state, error with retry, overdue highlighting across groups.

patterns_to_use:
  - useDailyActions.ts hook pattern: 'use client', useState/useEffect/useCallback/useRef(mountedRef), createClient() from @/lib/supabase/client for auth.getSession(), fetch() with Bearer token, ERROR_MESSAGES constants, auto-fetch on mount with dependency array, computed values from state. Applied in useActionPlansDashboard.ts for dashboard data fetching.
  - ActionListContainer loading/error/empty pattern: Skeleton loading when isLoading && !data, error state with AlertCircle icon + retry button + warning-amber styling, empty state with centered icon + message + description. Applied in the dashboard page component.
  - InsightEvidenceCardSkeleton skeleton pattern: Card with animate-pulse, bg-industrial-200 dark:bg-industrial-700 rounded placeholder divs for content areas. Applied in ActionPlanCard skeleton variant.
  - AssignFollowUpDialog dialog pattern: Dialog/DialogContent/DialogHeader/DialogFooter, useState for form fields + loading + submitted + error, useEffect to reset state on open, fetch with Supabase auth, success state with CheckCircle2 + auto-close, Loader2 spinner during submission. Applied in ActionPlanDetail.tsx for the update form and status change actions.
  - PriorityBadge color coding: Direct hex colors for priority (SAFETY=red #DC2626, FINANCIAL=amber #F59E0B, OEE=yellow #EAB308). For action plan priorities, use the story's color spec: critical=red, high=amber, medium=yellow, low=blue with Badge variant mappings.
  - URL search params sync: useSearchParams() to read current filters, useRouter().replace() to update URL when filters change without navigation. URLSearchParams for building/parsing query string. Applied in useActionPlansDashboard.ts for filter persistence (AC #4).
  - Two-client Supabase pattern for mutations: Service-role fetches via the backend API (all reads go through GET endpoints), user-scoped writes via PATCH/POST endpoints that enforce RLS server-side. The frontend only calls the REST API, not Supabase directly for action plan operations.
  - Test mocking pattern: vi.mock('next/navigation') for useRouter/useSearchParams/usePathname, vi.mock('@/lib/supabase/client') for createClient, mockFetch for API calls, vi.clearAllMocks in beforeEach. Applied in all __tests__ files.

dependencies:
  - next: installed (App Router, useRouter, useSearchParams, usePathname, Link)
  - react: installed (useState, useEffect, useCallback, useRef, useMemo)
  - lucide-react: installed (Target for nav, AlertCircle for error, RefreshCw for retry, ClipboardList for empty, Clock, User, Calendar, ChevronRight, CheckCircle2, Loader2, ExternalLink, Plus)
  - @/components/ui/badge: installed (Badge with info/warning/safety/success variants)
  - @/components/ui/card: installed (Card/CardContent with retrospective mode)
  - @/components/ui/dialog: installed (Dialog/DialogContent/DialogHeader/DialogFooter/DialogTitle/DialogDescription)
  - @/components/ui/button: installed (Button with variants: default/outline/ghost)
  - @/components/ui/select: installed (Select/SelectTrigger/SelectContent/SelectItem/SelectValue — Radix-based)
  - @/components/ui/textarea: installed (Textarea for update text input)
  - @/components/ui/scroll-area: installed (ScrollArea for long update timelines)
  - @/lib/supabase/client: installed (createClient for browser-side auth)
  - @/lib/utils: installed (cn() for conditional classnames)
  - vitest: installed (test runner)
  - @testing-library/react: installed (render, screen, fireEvent, waitFor)

acceptance_criteria_mapping:
  - AC1 (Dashboard page with plans grouped by status): apps/web/src/app/(main)/action-plans/page.tsx — page component rendering grouped sections; apps/web/src/hooks/useActionPlansDashboard.ts — fetches all plans via GET /api/v1/action-plans (paginated, potentially multiple pages or large page_size) and groups client-side into { open, in_progress, completed, verified } buckets; apps/web/src/components/action-plans/ActionPlanCard.tsx — renders individual plan with title, asset_id (displayed as-is or "Plant-wide"), priority badge, owner_id, due date, days-until-due; apps/web/src/components/navigation/AppSidebar.tsx — adds "Action Plans" link with Target icon in Operations group
  - AC2 (Overdue highlighting): apps/web/src/components/action-plans/ActionPlanCard.tsx — getDueStatus() helper function computes overdue/due-soon/on-track based on due_date and status. If status not in completed/verified and due_date < today, renders red "X days overdue" text with text-destructive class. If due within 3 days, renders amber "Due in X days" text.
  - AC3 (Detail view with updates and status changes): apps/web/src/components/action-plans/ActionPlanDetail.tsx — Dialog showing full plan details (description, root cause, corrective action, preventive action, owner, dates, source follow-up link if source_followup_id is set). Fetches updates via GET /api/v1/action-plans/{id}/updates. Renders UpdateTimeline component for progress updates timeline. "Add Update" form with Textarea + optional status change Select; submits via POST /api/v1/action-plans/{id}/updates. Status action buttons call PATCH /api/v1/action-plans/{id} (for "Mark In Progress", "Mark Completed") or POST /api/v1/action-plans/{id}/verify (for "Verify"). apps/web/src/components/action-plans/UpdateTimeline.tsx — renders timeline entries in reverse chronological order with author, text, status change, relative timestamp.
  - AC4 (URL filter persistence): apps/web/src/hooks/useActionPlansDashboard.ts — reads filter state from URL search params via useSearchParams() on mount. When user changes a filter, updates URL via router.replace(`/action-plans?${params.toString()}`). Filter params: status, priority, asset_id, owner_id. "all" or empty values remove the param from URL. Re-fetches data when search params change. apps/web/src/app/(main)/action-plans/page.tsx — passes filter state from URL to the hook and renders filter bar UI with Select dropdowns that call updateFilter().

risks:
  - API response shape mismatch with story spec: The story spec describes response fields asset_name, owner_email, and counts_by_status, but the actual API (Story 16.2 implemented) returns only asset_id, owner_id, and uses `items` (not `plans`) with no counts_by_status field. MITIGATION: The frontend types and hook will use the actual API shape (items, total_count, page, page_size). The dashboard will compute counts_by_status client-side from the grouped plans. For asset_name display, we'll show asset_id or "Plant-wide" for null — a future enhancement could resolve asset names via a separate lookup. For owner display, we'll show owner_id — resolving to email would require an additional API call or join that doesn't exist yet.
  - Pagination for large datasets: The API uses page/page_size (default 20, max 100). If there are >100 plans, a single fetch won't get them all for client-side grouping. MITIGATION: Use page_size=100 for the dashboard fetch (since action plans are bounded per plant, typically <100). If this is insufficient, can implement multi-page fetching or request a backend endpoint that returns all plans grouped. For MVP, page_size=100 is acceptable.
  - Route group placement: The story specifies `app/action-plans/page.tsx` but all authenticated pages are under `app/(main)/` which provides the AppShell layout with sidebar + header and the authentication guard (redirect to /login). MITIGATION: Create the page at `app/(main)/action-plans/page.tsx` instead. The URL route is still `/action-plans` since `(main)` is a route group (parenthesized, not part of the URL). This is consistent with all other authenticated pages.
  - No source_followup_id filter in API: The GET /api/v1/action-plans endpoint supports status, asset_id, owner_id, and priority filters but not source_followup_id. The existing useActionPlans.ts hook uses source_followup_id as a query param, which may work if the backend passes unrecognized params through to Supabase (it doesn't — it only applies known .eq() filters). MITIGATION: For the dashboard, source_followup_id filter is not needed (AC #4 only specifies asset, priority, owner, status). The "View Source Follow-Up" link in the detail view is a navigation link, not a filter.
  - Dialog scroll overflow: The ActionPlanDetail dialog may have long content (description, root cause, corrective action, preventive action, plus timeline). MITIGATION: Use DialogContent with max-h-[90vh] overflow-y-auto (same pattern as ActionPlanForm.tsx line 209) plus ScrollArea for the updates timeline section.
  - Status change via PATCH requires owner: The PATCH /api/v1/action-plans/{id} endpoint uses user-scoped RLS which restricts updates to owner_id=auth.uid(). Non-owners clicking "Mark Completed" etc. would get 403. MITIGATION: The POST /api/v1/action-plans/{id}/updates endpoint with status_change param can update the plan's status via service-role client (see action_plans.py:407). Use this endpoint for status changes from the detail view instead of PATCH. The verify endpoint (POST /api/v1/action-plans/{id}/verify) already uses service-role client. This means all status transitions from the UI will go through the updates endpoint, which is semantically correct (every status change should have an update entry).
  - No asset list endpoint for filter dropdown: The filter bar needs an asset dropdown but there's no dedicated API endpoint listing assets. MITIGATION: Query the Supabase assets table directly using createClient() from @/lib/supabase/client (same pattern as ActionPlanForm.tsx line 111-118 for asset lookup). Fetch all assets on mount for the filter dropdown.
  - No user list endpoint for owner filter dropdown: Similar to assets, there's no user list endpoint for the owner filter. MITIGATION: For MVP, omit the owner filter dropdown or show a text input for owner_id. The most practical approach is to skip the owner filter in the initial implementation — the story lists it but the other filters (status, priority, asset) cover the primary use cases. If needed, can add later when a team members endpoint exists (there is GET /api/v1/team/members used by AssignFollowUpDialog).

estimated_test_files:
  - apps/web/src/components/action-plans/__tests__/ActionPlanCard.test.tsx: Tests ActionPlanCard rendering (title, priority badge, status badge, due date, overdue red text, due-soon amber text, "Plant-wide" for null asset_id, click handler)
  - apps/web/src/components/action-plans/__tests__/ActionPlanDetail.test.tsx: Tests ActionPlanDetail dialog (all fields displayed, source follow-up link conditional, update timeline rendering, add update form submission, status change button visibility per status, verify button for completed plans)
  - apps/web/src/components/action-plans/__tests__/UpdateTimeline.test.tsx: Tests UpdateTimeline (reverse chronological order, status change display "Status: open -> in_progress", relative time formatting, empty state, author display)
  - apps/web/src/components/action-plans/__tests__/ActionPlansDashboard.test.tsx: Tests dashboard page (grouped section rendering with counts, filter dropdowns, filter URL sync, loading skeleton, error with retry, empty state message, overdue plans in correct section with red highlight)
  - apps/web/src/hooks/__tests__/useActionPlansDashboard.test.ts: Tests hook (fetch with auth, filter params sent to API, grouping logic, refetch, error handling, URL sync)

implementation_order:
  1. Create apps/web/src/components/action-plans/types.ts — Define ActionPlan interface (matching ActionPlanResponse from existing useActionPlans.ts but re-exported for clarity), ActionPlanUpdate interface (id, action_plan_id, author_id, update_text, status_change, created_at), ActionPlanListResponse (items, total_count, page, page_size), ActionPlanStatus and ActionPlanPriority literal union types, GroupedPlans type ({ open, in_progress, completed, verified } arrays), DueStatus helper type ({ label, variant }), getDueStatus() utility function, formatRelativeTime() utility function.
  2. Create apps/web/src/hooks/useActionPlansDashboard.ts — New hook following useDailyActions.ts pattern. Accepts no params (reads filters from URL). Uses useSearchParams() to read status/priority/asset_id/owner_id. Fetches GET /api/v1/action-plans with query params including page_size=100. Groups response items into { open, in_progress, completed, verified } client-side. Returns { plans, isLoading, error, refetch, grouped, totalCount, filters, updateFilter }. updateFilter() uses router.replace() to update URL search params.
  3. Create apps/web/src/components/action-plans/ActionPlanCard.tsx — Card component displaying plan summary. Uses Card/CardContent from ui/card, Badge from ui/badge. Priority badge with color coding (critical=safety variant, high=warning, medium=default, low=info). Status badge (open=info, in_progress=warning, completed=success, verified=success). getDueStatus() for overdue/due-soon rendering. onClick prop for opening detail view.
  4. Create apps/web/src/components/action-plans/UpdateTimeline.tsx — Vertical timeline with Tailwind CSS left-border + dot pattern. Maps ActionPlanUpdate[] in reverse chronological order. Each entry: left dot (colored if status_change), author_id, update text, status change string if present, formatRelativeTime(created_at).
  5. Create apps/web/src/components/action-plans/ActionPlanDetail.tsx — Dialog component fetching plan details (uses data passed from parent, not a separate API call for the plan itself since the list already has full data) and updates (GET /api/v1/action-plans/{id}/updates). Renders: header with title + status badge, sections for description/root_cause/corrective_action/preventive_action/owner/dates, source follow-up link (href="/followups/{source_followup_id}/respond" if set), UpdateTimeline for progress updates, "Add Update" form (Textarea for text, Select for optional status_change, Button to submit via POST /api/v1/action-plans/{id}/updates), status action buttons ("Mark In Progress" when open, "Mark Completed" when in_progress, "Verify" when completed) — status changes go through POST /api/v1/action-plans/{id}/updates with status_change or POST /api/v1/action-plans/{id}/verify for verification.
  6. Modify apps/web/src/components/action-plans/index.ts — Add exports for ActionPlanCard, ActionPlanDetail, UpdateTimeline, and re-export types from types.ts.
  7. Create apps/web/src/app/(main)/action-plans/page.tsx — 'use client' page. Uses useActionPlansDashboard hook. Page layout: header ("Action Plans" + count badge), filter bar (Select dropdowns for status, priority, asset — fetch assets via Supabase on mount for the asset dropdown; omit owner filter for MVP or use team/members endpoint), grouped sections (Open, In Progress, Completed, Verified with section headers showing count). Loading state: skeleton cards. Empty state: "No action plans found. Create action plans from follow-up investigations." Error state: AlertCircle + message + retry button. Each ActionPlanCard onClick opens ActionPlanDetail dialog. After status change in detail dialog, call refetch().
  8. Modify apps/web/src/components/navigation/AppSidebar.tsx — Add Target to lucide-react imports. Add { href: '/action-plans', label: 'Action Plans', icon: <Target className="w-5 h-5" /> } to the Operations nav group after "Shift Handoffs". No isActive() change needed — the existing generic startsWith fallback handles /action-plans.
  9. Create test files: ActionPlanCard.test.tsx (card rendering, overdue logic, priority colors, click handler), UpdateTimeline.test.tsx (ordering, status change display, relative time), ActionPlanDetail.test.tsx (dialog fields, update form, status buttons), ActionPlansDashboard.test.tsx (grouped rendering, filters, URL sync, loading/error/empty states).
  10. Run vitest to verify all tests pass, fix any issues.
DESIGN END

---

## TEST_SPEC: 16-5-action-plans-dashboard
**Timestamp:** 2026-02-12 03:07:29

TEST SPEC START
story_id: 16-5-action-plans-dashboard
generated: 2026-02-12

test_specifications:

## AC1: Given the user navigates to `/action-plans`, When the page loads, Then all action plans are displayed grouped by status (Open, In Progress, Completed, Verified) And each plan shows: title, asset name, priority, owner, due date, days until due (or overdue indicator).

### 16-5-action-plans-dashboard-UNIT-001: Dashboard page renders grouped sections with correct status headers
### 16-5-action-plans-dashboard-UNIT-002: ActionPlanCard renders title, priority badge, owner, due date, and days-until-due
### 16-5-action-plans-dashboard-UNIT-003: ActionPlanCard shows "Plant-wide" when asset_id is null
### 16-5-action-plans-dashboard-UNIT-004: ActionPlanCard renders correct status badge color per status
### 16-5-action-plans-dashboard-UNIT-005: ActionPlanCard renders correct priority badge colors
### 16-5-action-plans-dashboard-UNIT-006: Dashboard page header shows "Action Plans" title with total active count badge
### 16-5-action-plans-dashboard-UNIT-007: Dashboard renders loading skeleton cards while fetching
### 16-5-action-plans-dashboard-UNIT-008: Dashboard renders empty state when no plans exist
### 16-5-action-plans-dashboard-UNIT-009: Dashboard renders error state with retry button on API failure
### 16-5-action-plans-dashboard-UNIT-010: Dashboard handles auth error when session is expired
### 16-5-action-plans-dashboard-UNIT-011: Dashboard groups plans correctly when some status groups are empty
### 16-5-action-plans-dashboard-UNIT-012: ActionPlanCard due-soon indicator shows amber text for plans due within 3 days
### 16-5-action-plans-dashboard-UNIT-013: ActionPlanCard shows "Due in 1 day" (singular) when due tomorrow
### 16-5-action-plans-dashboard-INT-001: useActionPlansDashboard hook fetches with auth token and page_size=100
### 16-5-action-plans-dashboard-INT-002: useActionPlansDashboard hook groups plans by status client-side
### 16-5-action-plans-dashboard-INT-003: Navigation sidebar shows "Action Plans" link in Operations group
### 16-5-action-plans-dashboard-INT-004: Action Plans sidebar link highlights when on /action-plans route

## AC2: Overdue highlighting (7 specs)
### 16-5-action-plans-dashboard-UNIT-014 through UNIT-020

## AC3: Detail view with updates and status changes (18 specs)
### 16-5-action-plans-dashboard-UNIT-021 through UNIT-038, INT-005 through INT-006

## AC4: Filter persistence in URL params (6 unit + 4 integration specs)
### 16-5-action-plans-dashboard-UNIT-039 through UNIT-044, INT-007 through INT-010

TEST SPEC END

---
