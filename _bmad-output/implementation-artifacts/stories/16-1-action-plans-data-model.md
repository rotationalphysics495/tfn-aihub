# Story 16.1: Action Plans Data Model

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **database tables for action plans and their progress updates**,
so that **the system can track corrective and preventive actions from investigation to completion, closing the loop from issue to root cause to verified fix**.

## Acceptance Criteria

1. **AC1: `action_plans` Table Created**
   - GIVEN the migration runs successfully
   - WHEN the database is queried
   - THEN the `action_plans` table exists with columns:
     - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
     - `title` TEXT NOT NULL (e.g., "Replace worn bearing on Grinder 5")
     - `description` TEXT (full context, root cause analysis)
     - `asset_id` UUID FK -> assets(id), nullable (for plant-wide plans)
     - `category` TEXT CHECK (category IN ('corrective', 'preventive', 'improvement'))
     - `root_cause` TEXT
     - `corrective_action` TEXT
     - `preventive_action` TEXT (what changes to prevent recurrence)
     - `source_followup_id` UUID FK -> action_followups(id), nullable
     - `owner_id` UUID NOT NULL FK -> auth.users(id)
     - `status` TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'open', 'in_progress', 'completed', 'verified'))
     - `priority` TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical'))
     - `due_date` DATE
     - `completed_at` TIMESTAMPTZ
     - `verified_by` UUID FK -> auth.users(id), nullable
     - `verified_at` TIMESTAMPTZ
     - `created_at` TIMESTAMPTZ DEFAULT NOW()
     - `updated_at` TIMESTAMPTZ DEFAULT NOW()
   - AND the `update_updated_at_column()` trigger is attached

2. **AC2: `action_plan_updates` Table Created**
   - GIVEN the `action_plans` table exists
   - WHEN the database is queried
   - THEN the `action_plan_updates` table exists with columns:
     - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
     - `action_plan_id` UUID NOT NULL FK -> action_plans(id) ON DELETE CASCADE
     - `author_id` UUID NOT NULL FK -> auth.users(id)
     - `update_text` TEXT NOT NULL
     - `status_change` TEXT (nullable, e.g., "open -> in_progress")
     - `created_at` TIMESTAMPTZ DEFAULT NOW()
   - AND the cascade delete ensures updates are removed when a plan is deleted

3. **AC3: Row Level Security Enabled**
   - GIVEN both tables are created
   - WHEN RLS is checked
   - THEN RLS is enabled on `action_plans` and `action_plan_updates`
   - AND for `action_plans`:
     - Owners can SELECT, INSERT, UPDATE their own plans (owner_id = auth.uid())
     - All authenticated users can SELECT all plans (read access for visibility)
     - Service role has full access
   - AND for `action_plan_updates`:
     - Authenticated users can SELECT all updates (for timeline visibility)
     - Authenticated users can INSERT updates (author_id = auth.uid())
     - Service role has full access

4. **AC4: Performance Indexes Created**
   - GIVEN both tables exist
   - WHEN indexes are checked
   - THEN the following indexes exist:
     - `idx_action_plans_asset_id` on action_plans(asset_id)
     - `idx_action_plans_status` on action_plans(status)
     - `idx_action_plans_owner_id` on action_plans(owner_id)
     - `idx_action_plans_source_followup_id` on action_plans(source_followup_id)
     - `idx_action_plan_updates_action_plan_id` on action_plan_updates(action_plan_id)

5. **AC5: Migration File Created**
   - GIVEN the migration is needed
   - WHEN the migrations folder is checked
   - THEN `supabase/migrations/0031_action_plans.sql` exists
   - AND it follows established migration patterns from `0025_action_followups.sql` and `0002_plant_object_model.sql`
   - AND it can run idempotently (uses CREATE TABLE IF NOT EXISTS, DROP TRIGGER IF EXISTS, DROP POLICY IF EXISTS)

## Tasks / Subtasks

- [ ] Task 1: Create migration file `supabase/migrations/0031_action_plans.sql` (AC: 1-5)
  - [ ] Subtask 1.1: Add migration header comment with story reference and date
  - [ ] Subtask 1.2: Create `action_plans` table with all specified columns, CHECK constraints, and FK constraints
  - [ ] Subtask 1.3: Create `action_plan_updates` table with FK constraints (CASCADE DELETE on action_plan_id)
  - [ ] Subtask 1.4: Add `update_updated_at_column()` trigger to `action_plans` table

- [ ] Task 2: Configure Row Level Security (AC: 3)
  - [ ] Subtask 2.1: Enable RLS on both tables
  - [ ] Subtask 2.2: Create RLS policies for `action_plans` (owner CRUD + authenticated read)
  - [ ] Subtask 2.3: Create RLS policies for `action_plan_updates` (authenticated read + insert)
  - [ ] Subtask 2.4: Create service_role full access policies for both tables

- [ ] Task 3: Create performance indexes (AC: 4)
  - [ ] Subtask 3.1: Add indexes on `action_plans` (asset_id, status, owner_id, source_followup_id)
  - [ ] Subtask 3.2: Add index on `action_plan_updates` (action_plan_id)

- [ ] Task 4: Add table and column comments for documentation (AC: 1-2)
  - [ ] Subtask 4.1: Add COMMENT ON TABLE for both tables
  - [ ] Subtask 4.2: Add COMMENT ON COLUMN for key columns (especially status, category, priority enums)

- [ ] Task 5: Add verification queries as comments (AC: 5)
  - [ ] Subtask 5.1: Include SQL verification queries at bottom of migration file

## Dev Notes

### Technical Requirements

**Database Platform:** Supabase PostgreSQL (version 15+)

**Table Relationships:**
```
assets (1) ------< (N) action_plans (nullable FK -- plant-wide plans have no asset)
action_followups (1) ------< (N) action_plans (nullable FK -- not all plans come from followups)
auth.users (1) ------< (N) action_plans (owner_id, NOT NULL)
auth.users (1) ------< (N) action_plans (verified_by, nullable)
action_plans (1) ------< (N) action_plan_updates (CASCADE DELETE)
auth.users (1) ------< (N) action_plan_updates (author_id)
```

**Data Types Rationale:**
- `UUID` for primary keys: Consistent with all existing tables (gen_random_uuid())
- `TEXT` for string columns: Consistent with newer migrations (0025_action_followups.sql uses TEXT throughout)
- `TEXT CHECK (...)` for enum-like columns: Matches pattern from `action_followups.status` and `action_followups.category`
- `DATE` for `due_date`: Simple date without timezone (daily granularity, matches production_schedule pattern)
- `TIMESTAMPTZ` for timestamps: Consistent with all existing tables

### Architecture Compliance

**Migration Naming Convention:**
- Existing migrations: `0001` through `0025` (on disk), planned `0026`-`0030` (in stories)
- Epic specifies: `0031_action_plans.sql`
- File path: `supabase/migrations/0031_action_plans.sql`

**Migration Pattern (from `0025_action_followups.sql` -- the closest reference):**
1. Header comment with purpose
2. `CREATE TABLE` with inline column constraints and CHECK constraints
3. Index creation with `CREATE INDEX`
4. Trigger creation with `CREATE TRIGGER` (reference existing `update_updated_at_column()`)
5. RLS enable with `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
6. RLS policies with `CREATE POLICY`
7. Service role full access policy

**RLS Pattern (from `0025_action_followups.sql`):**
The `action_followups` table uses owner-based RLS:
- SELECT: `assigned_to = auth.uid() OR assigned_by = auth.uid()`
- INSERT: `assigned_by = auth.uid()`
- UPDATE: `assigned_by = auth.uid()`
- Service role: full access

For `action_plans`, adapt this pattern:
- SELECT for all authenticated (wider read access since plans are shared visibility)
- INSERT/UPDATE restricted to owner (owner_id = auth.uid())
- Service role: full access

**FK Reference for `action_followups`:**
The `action_followups` table already exists (migration `0025`). The FK from `action_plans.source_followup_id` references `action_followups(id)`. Use `ON DELETE SET NULL` (not CASCADE) since deleting a followup should not delete its resulting action plan.

**FK Reference for `assets`:**
The `assets` table exists (migration `0002`). The FK from `action_plans.asset_id` references `assets(id)`. Use `ON DELETE SET NULL` since deleting an asset should not destroy its action plan history.

**FK Reference for `auth.users`:**
- `owner_id` -> `auth.users(id)`: Use `ON DELETE CASCADE` (matches `action_followups` pattern)
- `verified_by` -> `auth.users(id)`: Use `ON DELETE SET NULL` (verification attribution is secondary)
- `action_plan_updates.author_id` -> `auth.users(id)`: Use `ON DELETE CASCADE` (matches action_followups pattern)

**Trigger Pattern:**
- Reuse the existing `update_updated_at_column()` function (created in `0002`)
- Do NOT recreate the function -- just reference it in CREATE TRIGGER
- Use `DROP TRIGGER IF EXISTS` before `CREATE TRIGGER` for idempotency
- Only `action_plans` needs the updated_at trigger (action_plan_updates has only created_at)

### Existing Schema Context

**The `action_followups` table** (migration `0025`) is the direct dependency:
```sql
action_followups (
    id UUID PK,
    action_item_id TEXT NOT NULL,
    action_summary TEXT NOT NULL,
    asset_name TEXT,
    category TEXT CHECK ('safety', 'oee', 'financial'),
    assigned_to UUID FK -> auth.users,
    assigned_by UUID FK -> auth.users,
    note TEXT,
    status TEXT CHECK ('assigned', 'in_progress', 'resolved'),
    report_date DATE NOT NULL,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
```

**The `assets` table** (migration `0002`) provides the asset FK:
- `id` UUID PK, `name` VARCHAR(255), `source_id` VARCHAR(255), `area` VARCHAR(100)

**Epic 13 Context:** Stories 13.1-13.5 extend the action_followups system with acknowledgments, status updates, and assignment badges. Story 16.1 builds the next layer on top: converting followup findings into structured action plans.

### File Structure Requirements

```
supabase/
  migrations/
    0001_enable_extensions.sql          # Existing
    0002_plant_object_model.sql         # Reference pattern (assets, triggers)
    ...
    0025_action_followups.sql           # Direct dependency (source_followup_id FK target)
    0026_products_and_schedule.sql      # Story 12.1 (planned)
    0027_action_acknowledgments.sql     # Story 13.1 (planned)
    0028_followup_assignee_rls.sql      # Story 13.3 (planned)
    ...
    0030_followup_messages.sql          # Story 15.1 (planned)
    0031_action_plans.sql               # THIS STORY - New migration
```

**Single file:** Both tables (`action_plans` and `action_plan_updates`), indexes, triggers, and RLS policies in one migration file. This matches the pattern from `0025` which creates one table per migration, but since `action_plan_updates` is a child table tightly coupled to `action_plans`, they belong together (similar to how `0002` creates multiple related tables).

### Testing Requirements

**SQL Verification Queries (include as comments in migration):**
```sql
-- Check action_plans table columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'action_plans'
ORDER BY ordinal_position;

-- Check action_plan_updates table columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'action_plan_updates'
ORDER BY ordinal_position;

-- Check foreign keys on action_plans
SELECT tc.constraint_name, kcu.column_name,
       ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'action_plans' AND tc.constraint_type = 'FOREIGN KEY';

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('action_plans', 'action_plan_updates');

-- Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('action_plans', 'action_plan_updates');

-- Check RLS policies
SELECT policyname, cmd, qual
FROM pg_policies
WHERE tablename IN ('action_plans', 'action_plan_updates');

-- Check triggers
SELECT tgname
FROM pg_trigger
WHERE tgrelid IN ('action_plans'::regclass);
```

**Manual Verification:**
1. Run migration against Supabase (dashboard SQL editor or `supabase db push`)
2. Verify both tables appear in Supabase Table Editor
3. Insert an action plan as authenticated user with owner_id = auth.uid() -- should succeed
4. Attempt INSERT as authenticated user with owner_id != auth.uid() -- should be denied by RLS
5. SELECT as any authenticated user -- should return all plans (shared visibility)
6. Insert an action_plan_update referencing a valid action_plan_id -- should succeed
7. Delete an action_plan -- cascade should remove its action_plan_updates
8. Delete a followup referenced by source_followup_id -- action plan should remain with source_followup_id set to NULL

### Anti-Pattern Prevention

- **DO NOT** recreate the `update_updated_at_column()` function. It already exists from migration `0002`. Just reference it in the CREATE TRIGGER statement.
- **DO NOT** use `uuid_generate_v4()`. The project uses `gen_random_uuid()` for UUID generation (established in `0002`).
- **DO NOT** add `ON DELETE CASCADE` from `action_plans.source_followup_id` to `action_followups`. Use `ON DELETE SET NULL` -- deleting a followup must NOT destroy the resulting action plan.
- **DO NOT** add `ON DELETE CASCADE` from `action_plans.asset_id` to `assets`. Use `ON DELETE SET NULL` -- deleting an asset must NOT destroy its action plan history.
- **DO NOT** create Pydantic models, API endpoints, or frontend components in this story. Those are separate stories (16.2 for API, 16.3+ for frontend).
- **DO NOT** add columns not specified in the epic (e.g., `tags`, `attachments`, `estimated_cost`). Keep the schema minimal for MVP.
- **DO NOT** add an `updated_at` trigger to `action_plan_updates`. That table is append-only (insert-only log) -- it has only `created_at`, no `updated_at`.
- **DO NOT** use `VARCHAR` -- use `TEXT` consistently, matching the `0025_action_followups.sql` pattern.

### Project Structure Notes

- This is the first story in Epic 16 (Action Plans & Continuous Improvement)
- Epic 16 depends on Epic 13 (action_followups table must exist)
- Story 16.2 (Action Plans CRUD API) depends on these tables for endpoints
- Story 16.3 (Create Action Plan from Follow-Up) links plans back to followups via `source_followup_id`
- Story 16.4 (Active Plans Badge) queries `action_plans` by `asset_id` and `status`
- Story 16.5 (Action Plans Dashboard) groups plans by status with filters
- Story 16.6 (AI Summary Context) queries active plans for assets in today's action items
- The `action_plan_updates` table serves as an audit trail for all plan changes (NFR-I3 compliance)

### References

- [Source: _bmad-output/planning-artifacts/epic-16.md#Story 16.1]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: docs/data-models.md#Row Level Security]
- [Source: docs/architecture-api.md#Database Connections]
- [Source: supabase/migrations/0025_action_followups.sql] -- Direct dependency and RLS pattern reference
- [Source: supabase/migrations/0002_plant_object_model.sql] -- Trigger function and migration pattern reference
- [Source: supabase/migrations/0012_rls_policies.sql] -- Advanced RLS pattern reference
- [Source: _bmad-output/planning-artifacts/epic-16.md#Overview] -- NFR-I3 (Audit Trail), NFR-I8 (RLS Compliance)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
