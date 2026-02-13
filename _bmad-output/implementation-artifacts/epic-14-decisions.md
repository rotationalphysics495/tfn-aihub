# Epic 14 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 14
**Started:** 2026-02-11 17:31:09

---


## DESIGN: 14-1-downtime-events-data-model-seed-data
**Timestamp:** 2026-02-11 17:36:32

DESIGN START
story_id: 14-1-downtime-events-data-model-seed-data

files_to_modify:
  - path: supabase/migrations/0029_downtime_events.sql
    action: create
    purpose: Create downtime_events table with columns, indexes, trigger, RLS policies, and COMMENTs
  - path: _bmad/scripts/seed-data.mjs
    action: modify
    purpose: Add downtime_events clear step and seed data generation aligned to daily_summaries

patterns_to_use:
  - UUID PK with gen_random_uuid(): Same as 0002 assets table and 0025 action_followups
  - CREATE TABLE IF NOT EXISTS: Idempotent table creation (matches 0002 pattern)
  - CREATE INDEX IF NOT EXISTS idx_{table}_{column}: Idempotent index naming convention (matches 0002/0024)
  - Reuse update_updated_at_column() trigger: Created in 0002, only add trigger on new table (DO NOT recreate function)
  - DROP POLICY IF EXISTS then CREATE POLICY: Idempotent RLS policy creation
  - COMMENT ON TABLE/COLUMN: Documentation pattern from 0002
  - Seed clear pattern: delete().neq('id', '00000000-...') at top of seed() function (lines 41-48)
  - Seed insert pattern: Array of objects → supabase.from().insert() with error handling (matches existing patterns)
  - daysAgo() helper: Already exists at line 19 for date generation

dependencies:
  - @supabase/supabase-js: installed (used in seed-data.mjs)
  - supabase migrations: 0002 provides update_updated_at_column(), 0003 provides daily_summaries, 0024 provides downtime_reasons column

acceptance_criteria_mapping:
  - AC1 (Table creation): supabase/migrations/0029_downtime_events.sql — CREATE TABLE IF NOT EXISTS downtime_events with all 12 columns (id, asset_id, event_date, shift, reason_code, reason_detail, duration_minutes, is_planned, source_system, source_event_id, created_at, updated_at), FK to assets(id) ON DELETE CASCADE, CHECK constraint on shift
  - AC2 (Indexes): supabase/migrations/0029_downtime_events.sql — 4 indexes: idx_downtime_events_asset_id, idx_downtime_events_event_date, idx_downtime_events_reason_code, idx_downtime_events_asset_event_date (composite)
  - AC3 (RLS policies): supabase/migrations/0029_downtime_events.sql — ENABLE RLS + two policies: "Allow authenticated read access on downtime_events" (SELECT for authenticated USING true) and "Allow service_role full access on downtime_events" (ALL for service_role USING true WITH CHECK true)
  - AC4 (Seed aligns with daily_summaries): _bmad/scripts/seed-data.mjs — Generate downtime_events from daily_summaries.downtime_reasons JSONB data; SUM(duration_minutes) per asset/day matches daily_summaries.downtime_minutes exactly
  - AC5 (Standard reason codes): _bmad/scripts/seed-data.mjs — Map freeform reason keys to 6 standard codes (Mechanical, Changeover, Material Shortage, Quality Hold, Operator Unavailable, Planned Maintenance); set is_planned=true for Changeover and Planned Maintenance
  - AC6 (Coverage): _bmad/scripts/seed-data.mjs — Events for 8 assets (Grinder 1-3, Grinder 5, Roaster 1-2, Filler Line A, Packaging Line 1) across 8 days (daysAgo 0-7), 2-5 events per asset per day, distributed across morning/afternoon/night shifts

risks:
  - Risk: Migration number 0029 conflicts if another story creates a migration before this one runs. Mitigation: The story spec explicitly reserves 0029 for this migration; no gaps between 0028 and 0029.
  - Risk: Seed data duration sums don't exactly match daily_summaries.downtime_minutes. Mitigation: Cross-reference every downtime_reasons JSONB entry from the existing dailySummaries array in seed-data.mjs; the JSONB values already sum to downtime_minutes, so use those exact values for each event's duration_minutes.
  - Risk: Seed script currently strips downtime_reasons (line 1421). Mitigation: This is a separate concern — the downtime_events seed data reads from the in-memory dailySummaries array (which has downtime_reasons), not from the database. No change to the daily_summaries insert flow is needed.
  - Risk: Large seed data array makes the file unwieldy. Mitigation: Use a programmatic approach — iterate over the dailySummaries array, extract downtime_reasons, and generate events with a reason code mapping function and shift distribution logic, rather than hand-coding hundreds of objects.
  - Risk: Grinder 2 daysAgo(1) has 0 downtime_minutes and empty downtime_reasons {}. Mitigation: Skip generating events for days with 0 downtime (no events to create).
  - Risk: Some assets (Grinder 4, Roaster 3, Filler B/C, Packaging 2/3) are NOT in the required 8-asset list. Mitigation: Story spec requires at least 6 assets. We'll cover the 8 specified: Grinder 1-3, Grinder 5, Roaster 1-2, Filler Line A, Packaging Line 1. Other assets can be included if the programmatic approach naturally covers them.

estimated_test_files:
  - No test files: This is a data-layer-only story (migration + seed data). Verification is done by running the migration and seed script, then querying the database. The story explicitly states no API endpoints or frontend changes.

implementation_order:
  1. Create supabase/migrations/0029_downtime_events.sql with full table definition
     - CREATE TABLE IF NOT EXISTS with all 12 columns and constraints
     - FK reference to assets(id) ON DELETE CASCADE
     - CHECK constraint on shift column ('morning', 'afternoon', 'night')
     - COMMENT ON TABLE and COMMENT ON COLUMN for all columns
  2. Add indexes to the migration file
     - idx_downtime_events_asset_id on (asset_id)
     - idx_downtime_events_event_date on (event_date)
     - idx_downtime_events_reason_code on (reason_code)
     - idx_downtime_events_asset_event_date on (asset_id, event_date)
  3. Add updated_at trigger to the migration file
     - CREATE TRIGGER update_downtime_events_updated_at referencing existing update_updated_at_column()
  4. Add RLS policies to the migration file
     - ALTER TABLE ENABLE ROW LEVEL SECURITY
     - DROP POLICY IF EXISTS + CREATE POLICY for authenticated SELECT
     - DROP POLICY IF EXISTS + CREATE POLICY for service_role ALL
  5. Modify seed-data.mjs: Add downtime_events clear step in the clearing section (after line 47)
     - await supabase.from('downtime_events').delete().neq('id', '00000000-...')
  6. Modify seed-data.mjs: Add reason code mapping function and shift distribution logic
     - Create REASON_CODE_MAP object mapping freeform keys → { code, is_planned }
     - Create function to distribute events across shifts (morning primary, afternoon secondary, night for roasters)
  7. Modify seed-data.mjs: Add downtime events generation after daily summaries section (~line 1425)
     - Iterate over dailySummaries array
     - Filter to target 8 assets
     - For each entry with downtime_reasons, decompose JSONB into individual event objects
     - Map reason keys through REASON_CODE_MAP
     - Assign shifts and generate realistic reason_detail strings
     - Insert via supabase.from('downtime_events').insert()
  8. Verify: Run migration locally, run seed script, and confirm data integrity
     - Confirm table exists with correct schema
     - Confirm indexes exist
     - Confirm RLS policies work
     - Confirm SUM(duration_minutes) per asset/day matches daily_summaries.downtime_minutes
DESIGN END

---

## TEST_SPEC: 14-1-downtime-events-data-model-seed-data
**Timestamp:** 2026-02-11 17:39:35

TEST SPEC START
story_id: 14-1-downtime-events-data-model-seed-data
generated: 2026-02-11

test_specifications:

## AC1: Database Migration Creates Table

### 14-1-downtime-events-data-model-seed-data-UNIT-001: Migration file exists and is non-empty
- Priority: P0
- Type: unit
- Given: The migration file `supabase/migrations/0029_downtime_events.sql` has been created
- When: The file system is checked for the migration file
- Then: The file exists at the expected path and has non-empty content
- Data: File path `supabase/migrations/0029_downtime_events.sql`

### 14-1-downtime-events-data-model-seed-data-UNIT-002: Migration creates downtime_events table with CREATE TABLE IF NOT EXISTS
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE TABLE statement
- Then: The migration contains `CREATE TABLE IF NOT EXISTS downtime_events`
- Data: Static file content regex matching

### 14-1-downtime-events-data-model-seed-data-UNIT-003: Table has id column as UUID PK with gen_random_uuid()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `id` column definition
- Then: The column is defined as `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: Regex pattern matching `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`

### 14-1-downtime-events-data-model-seed-data-UNIT-004: Table has asset_id column as UUID FK to assets(id) ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `asset_id` column definition
- Then: The column is defined as `UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE`
- Data: Regex matching FK reference with cascade delete

### 14-1-downtime-events-data-model-seed-data-UNIT-005: Table has event_date column as DATE NOT NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `event_date` column definition
- Then: The column is defined as `DATE NOT NULL`
- Data: Regex pattern matching within CREATE TABLE block

### 14-1-downtime-events-data-model-seed-data-UNIT-006: Table has shift column with CHECK constraint
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `shift` column definition
- Then: The column is defined as `TEXT` with CHECK constraint allowing only `'morning'`, `'afternoon'`, `'night'`
- Data: Regex pattern matching CHECK constraint with all three shift values (lowercase)

### 14-1-downtime-events-data-model-seed-data-UNIT-007: Table has reason_code column as TEXT NOT NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `reason_code` column definition
- Then: The column is defined as `TEXT NOT NULL`
- Data: Regex pattern matching

### 14-1-downtime-events-data-model-seed-data-UNIT-008: Table has reason_detail column as nullable TEXT
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `reason_detail` column definition
- Then: The column is defined as `TEXT` (without NOT NULL constraint)
- Data: Regex pattern matching

### 14-1-downtime-events-data-model-seed-data-UNIT-009: Table has duration_minutes column as INTEGER NOT NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `duration_minutes` column definition
- Then: The column is defined as `INTEGER NOT NULL`
- Data: Regex pattern matching

### 14-1-downtime-events-data-model-seed-data-UNIT-010: Table has is_planned column as BOOLEAN DEFAULT false
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `is_planned` column definition
- Then: The column is defined as `BOOLEAN DEFAULT false`
- Data: Regex pattern matching (case-insensitive for false/FALSE)

### 14-1-downtime-events-data-model-seed-data-UNIT-011: Table has source_system column as TEXT DEFAULT 'manual'
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `source_system` column definition
- Then: The column is defined as `TEXT DEFAULT 'manual'`
- Data: Regex pattern matching

### 14-1-downtime-events-data-model-seed-data-UNIT-012: Table has source_event_id column as nullable TEXT
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the `source_event_id` column definition
- Then: The column is defined as `TEXT` (nullable, no NOT NULL)
- Data: Regex pattern matching

### 14-1-downtime-events-data-model-seed-data-UNIT-013: Table has created_at and updated_at TIMESTAMPTZ columns with DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for timestamp columns
- Then: Both `created_at` and `updated_at` are defined as `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`
- Data: Regex pattern matching for both columns

### 14-1-downtime-events-data-model-seed-data-UNIT-014: Migration uses updated_at trigger referencing existing function
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for trigger definition
- Then: A trigger named `update_downtime_events_updated_at` exists with `EXECUTE FUNCTION update_updated_at_column()`
- And: The migration does NOT contain `CREATE OR REPLACE FUNCTION update_updated_at_column` (must not recreate)
- Data: Regex pattern matching for trigger; negative match for function creation

### 14-1-downtime-events-data-model-seed-data-UNIT-015: Migration has table and column COMMENTs
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for COMMENT statements
- Then: `COMMENT ON TABLE downtime_events` exists
- And: `COMMENT ON COLUMN downtime_events.` exists for key columns (at least asset_id, event_date, reason_code, duration_minutes)
- Data: String content matching

### 14-1-downtime-events-data-model-seed-data-UNIT-016: Migration SQL has balanced parentheses
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: Open and close parentheses are counted
- Then: The count of `(` equals the count of `)`
- Data: Character counting

### 14-1-downtime-events-data-model-seed-data-INT-001: Table exists in database after migration
- Priority: P0
- Type: integration
- Given: The migration `0029_downtime_events.sql` has been applied to a running Supabase instance
- When: The database is queried for the `downtime_events` table existence
- Then: The table exists and can be queried via `supabase.from('downtime_events').select('id').limit(0)`
- Data: Requires running Supabase with SUPABASE_URL and SUPABASE_SERVICE_KEY

### 14-1-downtime-events-data-model-seed-data-INT-002: All 12 columns exist with correct types after migration
- Priority: P0
- Type: integration
- Given: The migration has been applied to a running Supabase instance
- When: A row is inserted and selected with all columns specified
- Then: All 12 columns (id, asset_id, event_date, shift, reason_code, reason_detail, duration_minutes, is_planned, source_system, source_event_id, created_at, updated_at) are returned
- Data: Test insert with valid data for a known asset_id, then verify select returns all fields

### 14-1-downtime-events-data-model-seed-data-INT-003: Shift CHECK constraint rejects invalid values
- Priority: P0
- Type: integration
- Given: The migration has been applied to a running Supabase instance
- When: An INSERT is attempted with shift = 'invalid_shift'
- Then: The insert fails with a CHECK constraint violation error
- Data: Insert with `shift: 'evening'` should fail; inserts with `'morning'`, `'afternoon'`, `'night'` should succeed

### 14-1-downtime-events-data-model-seed-data-INT-004: FK constraint enforced - invalid asset_id rejected
- Priority: P1
- Type: integration
- Given: The migration has been applied to a running Supabase instance
- When: An INSERT is attempted with a non-existent asset_id UUID
- Then: The insert fails with a foreign key constraint violation error
- Data: Insert with `asset_id: 'ffffffff-ffff-ffff-ffff-ffffffffffff'`

### 14-1-downtime-events-data-model-seed-data-INT-005: CASCADE delete removes downtime_events when parent asset is deleted
- Priority: P1
- Type: integration
- Given: A downtime_event row exists linked to a test asset
- When: The parent asset is deleted from the `assets` table
- Then: The associated downtime_events rows are automatically deleted
- Data: Create test asset, insert downtime_event referencing it, delete asset, verify event is gone

## AC2: Indexes Exist for Query Performance

### 14-1-downtime-events-data-model-seed-data-UNIT-017: Migration creates index on asset_id
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_downtime_events_asset_id` is created on `downtime_events(asset_id)`
- Data: Regex matching `CREATE INDEX.*idx_downtime_events_asset_id ON downtime_events\(asset_id\)`

### 14-1-downtime-events-data-model-seed-data-UNIT-018: Migration creates index on event_date
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_downtime_events_event_date` is created on `downtime_events(event_date)`
- Data: Regex matching `CREATE INDEX.*idx_downtime_events_event_date ON downtime_events\(event_date\)`

### 14-1-downtime-events-data-model-seed-data-UNIT-019: Migration creates index on reason_code
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for index creation statements
- Then: An index named `idx_downtime_events_reason_code` is created on `downtime_events(reason_code)`
- Data: Regex matching `CREATE INDEX.*idx_downtime_events_reason_code ON downtime_events\(reason_code\)`

### 14-1-downtime-events-data-model-seed-data-UNIT-020: Migration creates composite index on (asset_id, event_date)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for composite index creation
- Then: A composite index named `idx_downtime_events_asset_event_date` is created on `downtime_events(asset_id, event_date)`
- Data: Regex matching `CREATE INDEX.*idx_downtime_events_asset_event_date ON downtime_events\(asset_id,\s*event_date\)`

### 14-1-downtime-events-data-model-seed-data-UNIT-021: All indexes use IF NOT EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: All CREATE INDEX statements are parsed
- Then: Every CREATE INDEX statement includes `IF NOT EXISTS`
- Data: Regex matching all CREATE INDEX lines contain IF NOT EXISTS

## AC3: RLS Follows Existing Patterns

### 14-1-downtime-events-data-model-seed-data-UNIT-022: Migration enables RLS on downtime_events
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for RLS enablement
- Then: The statement `ALTER TABLE downtime_events ENABLE ROW LEVEL SECURITY` exists
- Data: String content matching

### 14-1-downtime-events-data-model-seed-data-UNIT-023: Migration creates authenticated read access policy
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for RLS policies
- Then: A policy named `"Allow authenticated read access on downtime_events"` exists
- And: It is `FOR SELECT` with `TO authenticated` and `USING (true)`
- Data: Regex matching policy name, SELECT, authenticated role, USING (true)

### 14-1-downtime-events-data-model-seed-data-UNIT-024: Migration creates service_role full access policy
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for RLS policies
- Then: A policy named `"Allow service_role full access on downtime_events"` exists
- And: It is `FOR ALL` with `TO service_role`, `USING (true)`, and `WITH CHECK (true)`
- Data: Regex matching policy name, ALL, service_role, USING (true), WITH CHECK (true)

### 14-1-downtime-events-data-model-seed-data-UNIT-025: Migration drops existing policies before creating (idempotency)
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for DROP POLICY statements
- Then: `DROP POLICY IF EXISTS "Allow authenticated read access on downtime_events"` appears before CREATE
- And: `DROP POLICY IF EXISTS "Allow service_role full access on downtime_events"` appears before CREATE
- Data: String matching with order verification

### 14-1-downtime-events-data-model-seed-data-INT-006: Authenticated user can SELECT from downtime_events
- Priority: P0
- Type: integration
- Given: RLS is enabled on `downtime_events` and seed data has been loaded
- When: An authenticated user (non-service-role) queries `downtime_events`
- Then: Rows are returned successfully (read access granted)
- Data: Requires Supabase instance with anon/authenticated key

### 14-1-downtime-events-data-model-seed-data-INT-007: Service role can INSERT, UPDATE, DELETE on downtime_events
- Priority: P0
- Type: integration
- Given: RLS is enabled on `downtime_events`
- When: The service_role client performs INSERT, UPDATE, and DELETE operations
- Then: All operations succeed without RLS errors
- Data: Service role key with test insert/update/delete cycle

### 14-1-downtime-events-data-model-seed-data-INT-008: Non-service-role cannot INSERT into downtime_events
- Priority: P1
- Type: integration
- Given: RLS is enabled on `downtime_events`
- When: An authenticated (non-service-role) user attempts to INSERT a row
- Then: The insert is rejected by RLS policy
- Data: Authenticated user key, test insert payload

## AC4: Seed Data Aligns with Existing daily_summaries

### 14-1-downtime-events-data-model-seed-data-UNIT-026: Seed script contains downtime_events generation logic
- Priority: P0
- Type: unit
- Given: The seed-data.mjs file content is loaded
- When: The file is parsed for downtime_events references
- Then: The file contains insertion logic for `downtime_events` table
- And: The file references `supabase.from('downtime_events')`
- Data: Static file content matching

### 14-1-downtime-events-data-model-seed-data-UNIT-027: Seed script clears downtime_events before inserting
- Priority: P0
- Type: unit
- Given: The seed-data.mjs file content is loaded
- When: The file is parsed for the clear/delete step
- Then: A delete statement for `downtime_events` exists (e.g., `.from('downtime_events').delete()`)
- And: The clear step appears before the insert step
- Data: Static file content matching with order verification

### 14-1-downtime-events-data-model-seed-data-INT-009: Downtime events exist for past 7 days after seed runs
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Downtime events are queried for `event_date` from daysAgo(7) to daysAgo(0)
- Then: Events exist with `event_date` covering at least 7 distinct days
- Data: Requires running Supabase instance with seeded data

### 14-1-downtime-events-data-model-seed-data-INT-010: Sum of event durations per asset per day approximately matches daily_summaries.downtime_minutes
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: For each asset and day, `SUM(duration_minutes)` from `downtime_events` is compared to `daily_summaries.downtime_minutes`
- Then: The sums match exactly (or within ±1 minute tolerance) for every asset/day combination
- Data: Cross-reference query joining downtime_events aggregation with daily_summaries; requires running Supabase

### 14-1-downtime-events-data-model-seed-data-INT-011: Assets with zero downtime_minutes in daily_summaries have no downtime_events
- Priority: P1
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Daily summaries with `downtime_minutes = 0` are identified
- Then: No corresponding `downtime_events` rows exist for those asset/day combinations
- Data: Query daily_summaries where downtime_minutes = 0, verify no matching events

### 14-1-downtime-events-data-model-seed-data-INT-012: Reason code distribution is realistic (Mechanical is most frequent)
- Priority: P1
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Downtime events are grouped by `reason_code` and counted
- Then: "Mechanical" has the highest count (or total duration)
- And: Multiple reason codes are represented
- Data: Aggregation query on reason_code

## AC5: Standard Reason Codes Used

### 14-1-downtime-events-data-model-seed-data-UNIT-028: Seed script defines reason code mapping
- Priority: P0
- Type: unit
- Given: The seed-data.mjs file content is loaded
- When: The file is parsed for reason code definitions
- Then: All 6 standard reason codes are referenced: "Mechanical", "Changeover", "Material Shortage", "Quality Hold", "Operator Unavailable", "Planned Maintenance"
- Data: Static file content matching for each reason code string

### 14-1-downtime-events-data-model-seed-data-UNIT-029: Seed script maps is_planned correctly in code
- Priority: P0
- Type: unit
- Given: The seed-data.mjs file content is loaded
- When: The file is parsed for `is_planned` assignments
- Then: "Planned Maintenance" and "Changeover" are associated with `is_planned: true`
- And: "Mechanical", "Material Shortage", "Quality Hold", "Operator Unavailable" are associated with `is_planned: false`
- Data: Static file content matching for reason-to-planned mapping

### 14-1-downtime-events-data-model-seed-data-INT-013: Only standard reason codes exist in seeded data
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: `SELECT DISTINCT reason_code FROM downtime_events` is queried
- Then: Only these values appear: "Mechanical", "Changeover", "Material Shortage", "Quality Hold", "Operator Unavailable", "Planned Maintenance"
- And: No other reason_code values exist
- Data: Requires running Supabase instance

### 14-1-downtime-events-data-model-seed-data-INT-014: is_planned is true for Planned Maintenance and Changeover, false for others
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Downtime events are queried grouped by `reason_code` and `is_planned`
- Then: All "Planned Maintenance" events have `is_planned = true`
- And: All "Changeover" events have `is_planned = true`
- And: All "Mechanical" events have `is_planned = false`
- And: All "Material Shortage" events have `is_planned = false`
- And: All "Quality Hold" events have `is_planned = false`
- And: All "Operator Unavailable" events have `is_planned = false`
- Data: Query with filter/group on reason_code and is_planned

### 14-1-downtime-events-data-model-seed-data-INT-015: No events have non-standard reason codes
- Priority: P1
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Events are queried where `reason_code NOT IN ('Mechanical', 'Changeover', 'Material Shortage', 'Quality Hold', 'Operator Unavailable', 'Planned Maintenance')`
- Then: Zero rows are returned
- Data: Negative query filter

## AC6: Seed Data Covers Multiple Assets and Days

### 14-1-downtime-events-data-model-seed-data-INT-016: Events exist for at least 6 distinct assets
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: `SELECT DISTINCT asset_id FROM downtime_events` is queried
- Then: At least 6 distinct asset IDs are returned
- Data: Count of distinct asset_id values

### 14-1-downtime-events-data-model-seed-data-INT-017: Events span at least 7 distinct days
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: `SELECT DISTINCT event_date FROM downtime_events` is queried
- Then: At least 7 distinct event_date values are returned
- Data: Count of distinct event_date values

### 14-1-downtime-events-data-model-seed-data-INT-018: Each asset has 2-5 events per day on average
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Events are grouped by `(asset_id, event_date)` and counted
- Then: Each group has between 1 and 8 events (allowing some flexibility)
- And: The average across all groups is between 2 and 5
- Data: Aggregation query with GROUP BY asset_id, event_date

### 14-1-downtime-events-data-model-seed-data-INT-019: Events are distributed across all three shifts
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: `SELECT DISTINCT shift FROM downtime_events` is queried
- Then: All three shift values appear: 'morning', 'afternoon', 'night'
- Data: Distinct query on shift column

### 14-1-downtime-events-data-model-seed-data-INT-020: Specific required assets are covered
- Priority: P0
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Downtime events are queried for the 8 required asset UUIDs
- Then: Events exist for Grinder 1 (a0000001-0000-0000-0000-000000000004), Grinder 2 (...0005), Grinder 3 (...0006), Grinder 5 (...0014), Roaster 1 (...0001), Roaster 2 (...0002), Filler Line A (...0008), and Packaging Line 1 (...0011)
- Data: Query filtering by each specific asset_id

### 14-1-downtime-events-data-model-seed-data-INT-021: source_system is 'manual' and source_event_id is NULL for all seed data
- Priority: P1
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: All downtime_events are queried
- Then: Every row has `source_system = 'manual'`
- And: Every row has `source_event_id IS NULL`
- Data: Filter query for non-manual or non-null source_event_id

### 14-1-downtime-events-data-model-seed-data-INT-022: Running seed script twice produces same row count (idempotency)
- Priority: P1
- Type: integration
- Given: The seed script has been executed once
- When: The count of downtime_events is recorded, and the seed script is run again
- Then: The total count of downtime_events remains the same (no duplicates)
- Data: Count before and after re-run

### 14-1-downtime-events-data-model-seed-data-INT-023: All events have positive duration_minutes
- Priority: P1
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Events are queried where `duration_minutes <= 0`
- Then: Zero rows are returned
- Data: Negative filter query

### 14-1-downtime-events-data-model-seed-data-INT-024: All events have non-null reason_detail descriptions
- Priority: P2
- Type: integration
- Given: Schema migrations and seed script have been executed
- When: Events are queried for `reason_detail`
- Then: All (or most) events have non-empty `reason_detail` values providing realistic descriptions
- Data: Query for NULL or empty reason_detail

edge_cases:
  - Shift column accepts NULL (nullable TEXT with CHECK): verify that NULL is a valid shift value or that it's rejected if the column is NOT NULL
  - Inserting a downtime event with duration_minutes = 0: should be allowed by schema (no CHECK constraint) but should not appear in seed data
  - Very large duration_minutes value (e.g., 1440 = full day): schema allows it, seed data should have realistic values
  - Inserting duplicate events with same asset_id + event_date + reason_code: no unique constraint prevents this, verify seed data doesn't create unintended duplicates
  - Event with event_date in the future: schema allows it, seed data should only use past dates
  - reason_detail with very long text: schema allows unlimited TEXT, seed data should have reasonable descriptions

error_scenarios:
  - INSERT with missing required field (reason_code = NULL): should fail with NOT NULL constraint violation
  - INSERT with missing required field (duration_minutes = NULL): should fail with NOT NULL constraint violation
  - INSERT with missing required field (event_date = NULL): should fail with NOT NULL constraint violation
  - INSERT with invalid shift value ('evening', 'Morning', 'NIGHT'): should fail with CHECK constraint violation (case-sensitive)
  - INSERT with non-existent asset_id: should fail with FK constraint violation
  - Migration running on database without assets table: should fail due to FK dependency
  - Migration running on database without update_updated_at_column() function: should fail when creating trigger

test_file_mapping:
  - 14-1-downtime-events-data-model-seed-data-UNIT-*: supabase/tests/downtime-events-schema.test.ts
  - 14-1-downtime-events-data-model-seed-data-INT-*: supabase/tests/downtime-events-integration.test.ts

TEST SPEC END

---

## DESIGN: 14-2-trend-data-api-endpoint
**Timestamp:** 2026-02-11 18:13:27

DESIGN START
story_id: 14-2-trend-data-api-endpoint

files_to_modify:
  - path: apps/api/app/schemas/action.py
    action: modify
    purpose: Add TrendData Pydantic model and optional trend_data field to ActionItem
  - path: apps/api/app/services/action_engine.py
    action: modify
    purpose: Add trend calculation methods (_load_trailing_summaries, _load_trailing_safety_events, _calculate_trend_data, _calculate_days_on_report, _calculate_consecutive_days) and integrate into generate_action_list() after merge step
  - path: apps/api/tests/test_action_engine.py
    action: modify
    purpose: Add test class TestTrendDataCalculation with tests for full history, partial history, first appearance, schema validation, batch queries, metric mapping, week-over-week change, and API response integration

patterns_to_use:
  - BaseModel with Field(...) and ConfigDict: Matches existing EvidenceRef/ActionItem patterns in action.py (lines 45-103, 129-218); use json_schema_extra for examples, Field descriptors with ge/le constraints
  - Optional field on ActionItem: Follow the acknowledgment pattern (line 192-195) — add `trend_data: Optional[TrendData] = Field(None, ...)` as a new optional field with default None for backward compatibility
  - Supabase batch query with .in_(): Use `client.table("daily_summaries").select(...).in_("asset_id", asset_ids).gte("report_date", ...).lte("report_date", ...).execute()` for a single batched trailing query matching the existing _load_assets()/_get_safety_actions() patterns
  - Async method pattern: Follow existing `async def _get_safety_actions(self, ...)` / `async def _load_assets(self, ...)` pattern with try/except returning empty dict/list on failure, with logger.error for diagnostics
  - In-memory dict caching: The existing _action_list_cache dict already caches the full ActionListResponse (line 87, 806); trend_data embedded in ActionItem is automatically cached. No separate cache needed.
  - pytest + MagicMock test pattern: Follow existing test fixtures (mock_supabase_client, sample_assets) and mock chaining patterns (mock_supabase_client.table.return_value.select.return_value...) from TestSafetyPriorityFilter/TestOEEGapFilter

dependencies:
  - supabase-py: installed (used throughout action_engine.py)
  - pydantic: installed (v2, used in action.py)
  - pytest: installed (used in test_action_engine.py)
  - pytest-asyncio: installed (used in existing async tests)

acceptance_criteria_mapping:
  - AC1 (trend_data field with 7-day array, days_on_report, consecutive_days, week_over_week_change):
    - Schema: apps/api/app/schemas/action.py — TrendData class with metric_values, days_on_report, consecutive_days, week_over_week_change fields; ActionItem.trend_data optional field
    - Engine: apps/api/app/services/action_engine.py — _calculate_trend_data() computes all fields per action item; _load_trailing_summaries() fetches daily_summaries for 7 days; _load_trailing_safety_events() fetches safety_events for 7 days; metric selection based on ActionCategory (OEE→oee_percentage, FINANCIAL→financial_loss_dollars, SAFETY→event count per day)
  - AC2 (fewer than 7 days of history):
    - Engine: _calculate_trend_data() — metric_values array sized to available days (padded with None for missing days); days_on_report and consecutive_days count only available data
  - AC3 (first appearance, no prior history):
    - Engine: _calculate_trend_data() — when only today's value exists: days_on_report=1, consecutive_days=1, week_over_week_change=None, metric_values=[None]*6 + [today_value]
  - AC4 (TrendData schema validates correctly):
    - Schema: TrendData Pydantic model with type constraints (List[Optional[float]], int ge=0 le=7, Optional[float]); tested via direct instantiation in test class
  - AC5 (batch queries, no N+1):
    - Engine: _load_trailing_summaries() makes ONE query for all asset_ids; _load_trailing_safety_events() makes ONE query for safety assets; called ONCE in generate_action_list() before iterating action items. Distribution per-asset happens in Python memory.
  - AC6 (cache TTL 15min):
    - Engine: Existing _action_list_cache caches the full ActionListResponse (which now includes trend_data). The existing 5-minute reference cache TTL plus the action_list_cache dict pattern both apply. The story notes confirm trend data is part of the cached ActionItem — no separate cache mechanism needed.

risks:
  - Risk: Supabase .in_() query with large asset_ids list may hit query size limits. Mitigation: Current system has ~15 assets in seed data; production would have <100. Supabase PostgreSQL handles IN clauses with hundreds of UUIDs without issue.
  - Risk: The ActionCategory enum has no DOWNTIME value — story says "downtime for downtime items" but the actual category is FINANCIAL (which uses financial_loss_dollars from daily_summaries). Mitigation: Map FINANCIAL category to financial_loss_dollars column per the Metric Mapping table in the story spec. No new category needed.
  - Risk: Mutating ActionItem objects after they're in the cached response could corrupt the cache for subsequent requests. Mitigation: Follow the same copy pattern used for acknowledgment enrichment (lines 810-821) — create shallow copies of ActionItem objects before setting trend_data, or set trend_data BEFORE caching since it's computed once per generation and doesn't vary per user (unlike acknowledgments).
  - Risk: The _get_safety_actions query filters by is_resolved=False and gte(event_timestamp, start_of_day), but trailing safety event queries need a broader date range. Mitigation: _load_trailing_safety_events() is a separate method with its own date range filter (target_date-6 to target_date end-of-day), independent of _get_safety_actions.
  - Risk: daily_summaries columns (oee_percentage, downtime_minutes, financial_loss_dollars) are nullable DECIMAL/INTEGER types. Mitigation: _calculate_trend_data() treats None/null values as None in the metric_values array and skips them for days_on_report/consecutive_days calculations.
  - Risk: week_over_week_change division by zero when the value 7 days ago is 0. Mitigation: Return None when the denominator (week_ago value) is 0 or None.

estimated_test_files:
  - apps/api/tests/test_action_engine.py: Extend with TestTrendDataSchema (AC4 — TrendData validation, serialization, edge cases), TestTrendDataCalculation (AC1,2,3,5 — full 7-day history, partial history, first appearance, batch loading, metric mapping per category, consecutive_days logic, days_on_report logic, week_over_week_change), TestTrendDataIntegration (AC1,6 — generate_action_list includes trend_data, cached response includes trend_data)

implementation_order:
  1. Add TrendData schema to apps/api/app/schemas/action.py
     - Define TrendData(BaseModel) with model_config, metric_values, days_on_report, consecutive_days, week_over_week_change fields
     - Place BEFORE ActionItem class definition (after AcknowledgmentInfo, around line 127)
     - Add `trend_data: Optional[TrendData] = Field(None, description="7-day trend data for this action item's asset+metric")` to ActionItem class
     - Import TrendData in action_engine.py
  2. Add _load_trailing_summaries() to ActionEngine class
     - Signature: async def _load_trailing_summaries(self, target_date: date, asset_ids: List[str], lookback_days: int = 7) -> Dict[str, List[dict]]
     - Single batched query: client.table("daily_summaries").select("id, asset_id, report_date, oee_percentage, downtime_minutes, financial_loss_dollars, actual_output, target_output").in_("asset_id", asset_ids).gte("report_date", (target_date - timedelta(days=lookback_days-1)).isoformat()).lte("report_date", target_date.isoformat()).execute()
     - Group results by asset_id, sort by report_date ascending
     - Return Dict[asset_id -> List[daily_summary_rows]]
  3. Add _load_trailing_safety_events() to ActionEngine class
     - Signature: async def _load_trailing_safety_events(self, target_date: date, asset_ids: List[str], lookback_days: int = 7) -> Dict[str, Dict[str, int]]
     - Single batched query: client.table("safety_events").select("asset_id, event_timestamp").in_("asset_id", asset_ids).gte("event_timestamp", start_of_lookback.isoformat()).lte("event_timestamp", end_of_target_day.isoformat()).eq("is_resolved", False).execute()
     - Group by asset_id and date, count events per day
     - Return Dict[asset_id -> Dict[date_str -> count]]
  4. Add _calculate_trend_data() method to ActionEngine class
     - Signature: def _calculate_trend_data(self, action: ActionItem, target_date: date, trailing_summaries: Dict[str, List[dict]], trailing_safety_counts: Dict[str, Dict[str, int]], config: ActionEngineConfig) -> TrendData
     - Select metric column based on action.category: SAFETY→safety event count from trailing_safety_counts, OEE→oee_percentage from trailing_summaries, FINANCIAL→financial_loss_dollars from trailing_summaries
     - Build 7-day metric_values array (index 0 = oldest = target_date-6, index 6 = target_date); None for missing days
     - Call _calculate_days_on_report() and _calculate_consecutive_days() helpers
     - Compute week_over_week_change: if metric_values[0] exists and != 0 and metric_values[6] exists: ((metric_values[6] - metric_values[0]) / metric_values[0]) * 100; else None
     - Return TrendData instance
  5. Add _calculate_days_on_report() helper
     - For OEE: count days where oee_percentage < config.target_oee_percentage
     - For FINANCIAL: count days where financial_loss_dollars > config.financial_loss_threshold
     - For SAFETY: count days with >0 unresolved safety events for that asset
  6. Add _calculate_consecutive_days() helper
     - Start from target_date, count backward while condition holds
     - Same per-category threshold logic as days_on_report
     - Minimum 1 (today counts since the item is on the action list)
  7. Integrate trend calculation into generate_action_list()
     - After `merged = self._merge_and_prioritize(...)` (line 777/781) and BEFORE counts/caching
     - Extract unique asset_ids from merged list
     - Call _load_trailing_summaries(target_date, asset_ids)
     - If any safety items exist, call _load_trailing_safety_events(target_date, safety_asset_ids)
     - For each action in merged: action.trend_data = self._calculate_trend_data(action, target_date, trailing_summaries, trailing_safety_counts, effective_config)
     - This happens BEFORE the response is cached, so trend_data is part of the cached ActionListResponse
  8. Write tests in apps/api/tests/test_action_engine.py
     - TestTrendDataSchema: TrendData validates with all fields, partial metric_values, edge values
     - TestTrendDataCalculation: Full 7-day OEE history, partial history (3 days), first appearance, SAFETY metric uses event counts, FINANCIAL uses financial_loss_dollars, consecutive_days stops at first non-triggering day, week_over_week_change with zero denominator returns None
     - TestTrendBatchLoading: _load_trailing_summaries returns grouped results, single query for multiple assets
     - TestTrendIntegration: generate_action_list result includes trend_data on each action item, cached response preserves trend_data
DESIGN END

---

## DESIGN: 14-3-downtime-pareto-api-endpoint
**Timestamp:** 2026-02-11 18:35:41

DESIGN START
story_id: 14-3-downtime-pareto-api-endpoint

files_to_modify:
  - path: apps/api/app/models/downtime.py
    action: modify
    purpose: Add is_planned field to ParetoItem; add planned_minutes and unplanned_minutes fields to ParetoResponse
  - path: apps/api/app/services/downtime_analysis.py
    action: modify
    purpose: Add get_downtime_from_events_table() method; extend calculate_pareto() to track is_planned and planned/unplanned splits
  - path: apps/api/app/api/downtime.py
    action: modify
    purpose: Add date query param to get_downtime_pareto(); add downtime_events-first logic with daily_summaries fallback; add TTLCache caching
  - path: apps/api/tests/test_downtime_pareto.py
    action: create
    purpose: Test Pareto endpoint with downtime_events data, area aggregation, empty results, planned/unplanned split, and daily_summaries fallback

patterns_to_use:
  - Supabase query chaining: Use self.client.table("downtime_events").select("*").eq("event_date", ...).eq("asset_id", ...).execute() — same pattern as get_downtime_from_daily_summaries() at line 184 of downtime_analysis.py
  - Area filter via assets_map: Post-fetch filtering by area using await self.get_assets_map() — identical to the pattern at lines 196-201 of downtime_analysis.py
  - Pydantic v2 BaseModel with ConfigDict: Add fields with Field(..., description="...") defaults for backward compatibility — matches existing ParetoItem/ParetoResponse at lines 86-135 of downtime.py
  - defaultdict aggregation in calculate_pareto: Extend the existing lambda at line 382-388 of downtime_analysis.py to include planned_minutes/unplanned_minutes accumulators
  - cachetools.TTLCache at module level: Use TTLCache(maxsize=100, ttl=900) — follows the pattern in app/core/security.py line 28 (_jwks_cache) and app/services/agent/cache.py line 102
  - try/except HTTPException pattern: Wrap endpoint body in try/except matching lines 251-301 of downtime.py
  - async def for all DB methods: All new service methods must be async — matches get_downtime_from_daily_summaries(), get_assets_map()

dependencies:
  - cachetools: installed (requirements.txt line 8, already used in security.py and agent/cache.py)
  - pydantic: installed (v2, used throughout models)
  - fastapi: installed (used in api/downtime.py)

acceptance_criteria_mapping:
  - AC1 (Pareto from downtime_events for a single asset on a given date):
    - Model: apps/api/app/models/downtime.py — add `is_planned: bool = Field(False)` to ParetoItem; add `planned_minutes: int = Field(0)` and `unplanned_minutes: int = Field(0)` to ParetoResponse
    - Service: apps/api/app/services/downtime_analysis.py — new `get_downtime_from_events_table(event_date, asset_id, area)` queries `downtime_events` table; extended `calculate_pareto()` tracks `is_planned` and `planned_minutes`/`unplanned_minutes` per aggregate and in totals
    - Endpoint: apps/api/app/api/downtime.py — `get_downtime_pareto()` gains `date` param, calls `get_downtime_from_events_table()` first; if data exists, transforms to DowntimeEvent list and runs `calculate_pareto()` returning enhanced ParetoResponse with `planned_minutes`/`unplanned_minutes`
    - Response includes: reason_code, total_minutes, percentage, event_count, is_planned per item; total_downtime_minutes, planned_minutes, unplanned_minutes at top level
  - AC2 (area parameter aggregates across all assets in workcenter):
    - Service: `get_downtime_from_events_table()` — when `area` is provided and `asset_id` is not, fetches all events for the date, then filters by area using `get_assets_map()` (same post-fetch pattern as daily_summaries at line 196-201)
    - Endpoint: existing `area` query param on the endpoint already passes through; the new service method handles it
  - AC3 (no downtime events returns empty array with total_minutes=0):
    - Service: `get_downtime_from_events_table()` returns empty list when no records found; `calculate_pareto([])` already returns `([], None)` at line 378-379
    - Endpoint: returns ParetoResponse with `items=[]`, `total_downtime_minutes=0`, `planned_minutes=0`, `unplanned_minutes=0` — the Field defaults handle this

risks:
  - Risk: The existing calculate_pareto() takes List[DowntimeEvent] (which has is_safety_related but NOT is_planned). We need to transform downtime_events table records into DowntimeEvent objects with the is_planned data preserved. Mitigation: Add a new `transform_downtime_events_to_events()` method that creates DowntimeEvent objects from downtime_events records, storing is_planned temporarily on the object. Alternatively, extend calculate_pareto() to accept a second parameter type (list of raw dicts) or add an `is_planned` field to DowntimeEvent. The cleanest approach is to add an optional `is_planned: bool = Field(False)` to DowntimeEvent and populate it during transformation, since the model already has is_safety_related for similar categorization.
  - Risk: Adding `is_planned` to ParetoItem and `planned_minutes`/`unplanned_minutes` to ParetoResponse changes the API contract. Mitigation: All new fields have defaults (False, 0, 0) making this backward-compatible — existing consumers get the new fields with sensible defaults.
  - Risk: Cache key collisions if the same endpoint is called with old params (start_date/end_date/source) vs new params (date). Mitigation: Include all relevant params in the cache key: `f"pareto:{date_val}:{asset_id}:{area}:{start_date}:{end_date}:{source}"`.
  - Risk: When downtime_events table has no data for a query but daily_summaries does, the fallback must seamlessly work. Mitigation: The fallback path reuses the existing code (lines 258-292 of downtime.py) exactly as-is. Only when downtime_events returns non-empty data does the new code path activate.
  - Risk: The `date` parameter conflicts conceptually with existing `start_date`/`end_date` params. Mitigation: When `date` is provided, it takes precedence — use it for the downtime_events query. If `date` is None and start_date/end_date are provided, fall through to the existing daily_summaries path. Document this precedence in the endpoint docstring.

estimated_test_files:
  - apps/api/tests/test_downtime_pareto.py: Tests for (1) Pareto with downtime_events data for single asset — verifying items sorted by duration, is_planned, planned/unplanned split (AC1); (2) Pareto with area aggregation (AC2); (3) Empty result set returns empty items with total_minutes=0 (AC3); (4) Fallback to daily_summaries when no downtime_events exist (AC1 fallback); (5) Cache behavior — second call with same params returns cached result (AC1 caching); (6) ParetoItem includes is_planned field; (7) ParetoResponse includes planned_minutes and unplanned_minutes

implementation_order:
  1. Extend ParetoItem model in apps/api/app/models/downtime.py
     - Add `is_planned: bool = Field(False, description="Whether this reason code is primarily planned downtime")` to ParetoItem class (after line 109, before the closing of the class)
     - Update the json_schema_extra example to include `"is_planned": False`
  2. Extend ParetoResponse model in apps/api/app/models/downtime.py
     - Add `planned_minutes: int = Field(0, ge=0, description="Total planned downtime minutes")` to ParetoResponse
     - Add `unplanned_minutes: int = Field(0, ge=0, description="Total unplanned downtime minutes")` to ParetoResponse
     - Update the json_schema_extra example to include the new fields
  3. Add is_planned field to DowntimeEvent model in apps/api/app/models/downtime.py
     - Add `is_planned: bool = Field(False, description="Whether this is planned downtime")` to DowntimeEvent (needed so calculate_pareto can access it)
  4. Add get_downtime_from_events_table() method to DowntimeAnalysisService in apps/api/app/services/downtime_analysis.py
     - Signature: `async def get_downtime_from_events_table(self, event_date: Optional[date] = None, asset_id: Optional[str] = None, area: Optional[str] = None) -> List[dict]`
     - Default event_date to yesterday if None
     - Build Supabase query: `self.client.table("downtime_events").select("*").eq("event_date", event_date.isoformat())`
     - If asset_id provided, add `.eq("asset_id", asset_id)`
     - Execute query, get records
     - If area provided, post-filter using get_assets_map() (same pattern as daily_summaries)
     - Return records list (empty list if no data)
  5. Add transform method for downtime_events records in DowntimeAnalysisService
     - New method: `async def transform_downtime_events_records(self, records: List[dict]) -> List[DowntimeEvent]`
     - For each record: look up asset_info from get_assets_map(), get cost_center for financial impact
     - Create DowntimeEvent with reason_code, duration_minutes, is_planned, event_timestamp from event_date, financial_impact
     - Filter out zero-duration records (though CHECK constraint prevents this)
     - Return List[DowntimeEvent]
  6. Extend calculate_pareto() in DowntimeAnalysisService to track is_planned
     - In the defaultdict lambda (line 382-388), add `"planned_minutes": 0, "unplanned_minutes": 0` accumulators
     - In the for loop (line 391-397), add: if event.is_planned: agg["planned_minutes"] += event.duration_minutes else: agg["unplanned_minutes"] += event.duration_minutes
     - When building ParetoItem (lines 408-418), set `is_planned=agg["planned_minutes"] > agg["unplanned_minutes"]` (a reason code is "planned" if majority of its minutes are planned)
     - Return type change: return a third value — tuple of (planned_total, unplanned_total) — OR compute these in the endpoint. Better approach: keep the return signature as `Tuple[List[ParetoItem], int]` and compute planned/unplanned totals in the endpoint from the items, since items now carry is_planned and we can also sum from the DowntimeEvent list directly. This avoids changing the return signature and breaking existing callers.
  7. Update get_downtime_pareto() endpoint in apps/api/app/api/downtime.py
     - Add `date: Optional[date] = Query(None, description="Single date for downtime_events query (defaults to yesterday)")` parameter
     - Add module-level cache: `from cachetools import TTLCache` and `_pareto_cache = TTLCache(maxsize=100, ttl=900)`
     - Add cache key function: `def _pareto_cache_key(date_val, asset_id, area, start_date, end_date, source): return f"pareto:{date_val}:{asset_id}:{area}:{start_date}:{end_date}:{source}"`
     - At start of endpoint handler: compute cache key, check _pareto_cache, return cached if hit
     - Logic flow: (a) Try downtime_events path — call service.get_downtime_from_events_table(date or yesterday, asset_id, area). (b) If records returned, transform via service.transform_downtime_events_records(), run calculate_pareto(), compute planned_minutes/unplanned_minutes from the events list. (c) If no records, fall back to existing daily_summaries/live_snapshots path (existing code lines 258-282). (d) Build ParetoResponse with planned_minutes and unplanned_minutes (default 0 for fallback path). (e) Store in cache, return response.
  8. Write tests in apps/api/tests/test_downtime_pareto.py
     - Fixtures: mock_supabase_client, mock_verify_jwt, sample_assets, sample_cost_centers, sample_downtime_events (list of downtime_events table records with reason_code, duration_minutes, is_planned, etc.)
     - TestParetoWithDowntimeEvents class:
       - test_returns_items_sorted_by_duration_desc: AC1 — verify items array sorted by total_minutes descending
       - test_items_include_is_planned_field: AC1 — verify each item has is_planned boolean
       - test_response_includes_planned_unplanned_split: AC1 — verify planned_minutes + unplanned_minutes == total_downtime_minutes
       - test_percentage_of_total_correct: AC1 — verify each item's percentage = (total_minutes / total_downtime_minutes) * 100
       - test_event_count_correct: AC1 — verify event_count matches number of events per reason code
     - TestParetoAreaAggregation class:
       - test_area_aggregates_across_assets: AC2 — provide multiple assets in same area, verify aggregation
     - TestParetoEmptyResults class:
       - test_empty_returns_zero_totals: AC3 — no downtime_events, verify items=[], total_downtime_minutes=0, planned_minutes=0, unplanned_minutes=0
     - TestParetoFallback class:
       - test_falls_back_to_daily_summaries: verify that when downtime_events returns empty, the endpoint falls through to daily_summaries path
     - TestParetoCaching class:
       - test_cache_returns_same_result: verify second call uses cache (mock DB called once)
DESIGN END

---

## TEST_SPEC: 14-3-downtime-pareto-api-endpoint
**Timestamp:** 2026-02-11 18:38:42

TEST SPEC START
story_id: 14-3-downtime-pareto-api-endpoint
generated: 2026-02-11

test_specifications:

## AC1: Given downtime events exist for an asset on a given date, When GET /api/v1/downtime/pareto?date={date}&asset_id={id} is called, Then the response includes an array of reason codes sorted by total duration (descending), each entry with reason_code, total_minutes, percentage, event_count, is_planned, total_downtime_minutes, and planned vs. unplanned split.

### 14-3-downtime-pareto-api-endpoint-E2E-001: Pareto endpoint returns items sorted by total_minutes descending
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains 3 reason codes for asset "asset-1" on date "2025-01-15": Mechanical (60min + 30min = 90min), Material Shortage (45min), Changeover (20min)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200; `items` array has 3 entries ordered [Mechanical(90), Material Shortage(45), Changeover(20)]; each item's `total_minutes` is >= the next item's `total_minutes`
- Data: 4 downtime_events records (2 Mechanical, 1 Material Shortage, 1 Changeover); mock assets and cost_centers tables

### 14-3-downtime-pareto-api-endpoint-E2E-002: Each Pareto item includes reason_code, total_minutes, percentage, event_count, and is_planned
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on "2025-01-15": Mechanical (60min, is_planned=False), Planned Maintenance (40min, is_planned=True)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Each item in `items` has all required fields: `reason_code` (string), `total_minutes` (int >=0), `percentage` (float 0-100), `event_count` (int >=1), `is_planned` (bool); the Mechanical item has `is_planned=False`; the Planned Maintenance item has `is_planned=True`
- Data: 2 downtime_events records with distinct is_planned values

### 14-3-downtime-pareto-api-endpoint-E2E-003: Response includes total_downtime_minutes matching sum of all item minutes
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events totaling 155 minutes for asset "asset-1" on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: `total_downtime_minutes` equals 155; the sum of all items' `total_minutes` equals 155
- Data: Multiple downtime_events records summing to 155 minutes

### 14-3-downtime-pareto-api-endpoint-E2E-004: Response includes planned_minutes and unplanned_minutes that sum to total
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on "2025-01-15": Planned Maintenance (40min, is_planned=True), Changeover (25min, is_planned=True), Mechanical (60min, is_planned=False), Material Shortage (30min, is_planned=False)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: `planned_minutes` equals 65; `unplanned_minutes` equals 90; `planned_minutes + unplanned_minutes` equals `total_downtime_minutes` (155)
- Data: 4 downtime_events with mixed is_planned values

### 14-3-downtime-pareto-api-endpoint-E2E-005: Percentage of each item equals (total_minutes / total_downtime_minutes) * 100
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on "2025-01-15" with total 150 minutes: Mechanical (90min), Material Shortage (45min), Safety Issue (15min)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Mechanical percentage ≈ 60.0%; Material Shortage ≈ 30.0%; Safety Issue ≈ 10.0%; all percentages sum to approximately 100% (within 0.1% tolerance)
- Data: 3 reason codes with clean percentage division

### 14-3-downtime-pareto-api-endpoint-E2E-006: event_count accurately reflects number of events per reason code
- Priority: P1
- Type: e2e
- Given: The `downtime_events` table contains 3 events for "Mechanical" (60min, 30min, 20min) and 1 event for "Changeover" (45min) for asset "asset-1" on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Mechanical item has `event_count=3`; Changeover item has `event_count=1`
- Data: 4 downtime_events records grouped into 2 reason codes

### 14-3-downtime-pareto-api-endpoint-E2E-007: Authentication is required for the Pareto endpoint
- Priority: P0
- Type: e2e
- Given: No authentication token is provided
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called without an Authorization header
- Then: Response status is 401 (Unauthorized)
- Data: None

### 14-3-downtime-pareto-api-endpoint-E2E-008: Date parameter defaults to yesterday when not provided
- Priority: P1
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on yesterday's date
- When: `GET /api/v1/downtime/pareto?asset_id=asset-1` is called (no `date` parameter) with a valid auth token
- Then: Response status is 200; the service queries `downtime_events` with `event_date` = yesterday; items from yesterday's data are returned
- Data: downtime_events records for yesterday's date

### 14-3-downtime-pareto-api-endpoint-E2E-009: is_planned is determined by majority of minutes within a reason code
- Priority: P1
- Type: e2e
- Given: The `downtime_events` table contains events for reason_code "Changeover" on asset "asset-1" on "2025-01-15": one event with 60min (is_planned=True) and one event with 20min (is_planned=False)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: The Changeover item has `is_planned=True` because the majority of its minutes (60 of 80) are planned
- Data: 2 downtime_events for same reason_code with different is_planned values

### 14-3-downtime-pareto-api-endpoint-UNIT-001: ParetoItem model includes is_planned field with default False
- Priority: P0
- Type: unit
- Given: A ParetoItem is instantiated with only required fields (reason_code, total_minutes)
- When: The `is_planned` field is accessed
- Then: `is_planned` is `False` (default value); the field is a boolean type
- Data: Minimal ParetoItem construction

### 14-3-downtime-pareto-api-endpoint-UNIT-002: ParetoResponse model includes planned_minutes and unplanned_minutes with defaults of 0
- Priority: P0
- Type: unit
- Given: A ParetoResponse is instantiated with only required fields (items, total_downtime_minutes, total_financial_impact, total_events, data_source, last_updated)
- When: The `planned_minutes` and `unplanned_minutes` fields are accessed
- Then: Both default to 0; both are integer types with ge=0 constraint
- Data: Minimal ParetoResponse construction

### 14-3-downtime-pareto-api-endpoint-UNIT-003: calculate_pareto tracks planned and unplanned minutes per reason code
- Priority: P0
- Type: unit
- Given: A list of DowntimeEvent objects with mixed is_planned values: [Mechanical 60min planned, Mechanical 30min unplanned, Material Shortage 45min unplanned]
- When: `calculate_pareto(events)` is called
- Then: Mechanical ParetoItem has `is_planned=True` (60 planned > 30 unplanned); Material Shortage has `is_planned=False` (0 planned < 45 unplanned)
- Data: 3 DowntimeEvent objects with is_planned field set

### 14-3-downtime-pareto-api-endpoint-UNIT-004: DowntimeEvent model supports is_planned field
- Priority: P1
- Type: unit
- Given: A DowntimeEvent is instantiated with `is_planned=True`
- When: The object is serialized/accessed
- Then: `is_planned` is `True`; default value when not provided is `False`
- Data: DowntimeEvent with and without is_planned

### 14-3-downtime-pareto-api-endpoint-INT-001: Service queries downtime_events table with correct filters
- Priority: P0
- Type: integration
- Given: A mock Supabase client is configured with downtime_events data for asset "asset-1" on "2025-01-15"
- When: `service.get_downtime_from_events_table(event_date=date(2025,1,15), asset_id="asset-1")` is called
- Then: The Supabase client calls `table("downtime_events").select("*").eq("event_date", "2025-01-15").eq("asset_id", "asset-1").execute()`; returned records match mock data
- Data: Mock Supabase client with chained query expectations

### 14-3-downtime-pareto-api-endpoint-INT-002: Caching returns cached response on second call with same parameters
- Priority: P1
- Type: integration
- Given: The Pareto endpoint has been called once for date="2025-01-15" and asset_id="asset-1", populating the cache
- When: The same endpoint is called again with identical parameters
- Then: The Supabase client is NOT called a second time for downtime_events; the response matches the first call's response; TTL is 15 minutes (900 seconds)
- Data: Mock Supabase client tracking call count

### 14-3-downtime-pareto-api-endpoint-INT-003: Cache key differentiates by date, asset_id, and area
- Priority: P2
- Type: integration
- Given: The Pareto endpoint is called for date="2025-01-15" and asset_id="asset-1"
- When: A second call is made for date="2025-01-16" and asset_id="asset-1"
- Then: The Supabase client IS called again (different cache key); the response reflects the different date's data
- Data: Mock Supabase client with different data for each date

## AC2: Given an area parameter is provided instead of asset_id, When the Pareto endpoint is called, Then downtime is aggregated across all assets in that workcenter area.

### 14-3-downtime-pareto-api-endpoint-E2E-010: Area parameter aggregates downtime across all assets in that workcenter
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events on "2025-01-15": asset-1 (area="Workcenter A", Mechanical 60min), asset-2 (area="Workcenter A", Mechanical 30min, Material Shortage 45min), asset-3 (area="Workcenter B", Mechanical 20min)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&area=Workcenter A` is called with a valid auth token
- Then: Response includes only assets from "Workcenter A"; Mechanical total_minutes = 90 (60+30); Material Shortage total_minutes = 45; total_downtime_minutes = 135; asset-3's events are excluded
- Data: 4 downtime_events across 3 assets in 2 areas; mock assets table with area assignments

### 14-3-downtime-pareto-api-endpoint-E2E-011: Area filter is case-insensitive
- Priority: P1
- Type: e2e
- Given: Assets have area="Workcenter A" in the database; downtime_events exist for those assets on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&area=workcenter a` is called (lowercase)
- Then: Response status is 200; events from "Workcenter A" assets are included in the aggregation
- Data: Assets with mixed-case area names; downtime_events for those assets

### 14-3-downtime-pareto-api-endpoint-INT-004: Service method filters events by area using assets_map lookup
- Priority: P0
- Type: integration
- Given: A mock Supabase client returns 5 downtime_events records for "2025-01-15" across multiple areas; assets_map maps asset IDs to areas
- When: `service.get_downtime_from_events_table(event_date=date(2025,1,15), area="Assembly")` is called
- Then: Only records whose asset_id maps to area "Assembly" are returned; other area records are filtered out
- Data: Mock assets table, mock downtime_events with assets in different areas

### 14-3-downtime-pareto-api-endpoint-E2E-012: Area with no matching assets returns empty result
- Priority: P1
- Type: e2e
- Given: No assets exist in area "Nonexistent Area"; downtime_events exist for other areas on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&area=Nonexistent Area` is called with a valid auth token
- Then: Response status is 200; `items` is an empty array; `total_downtime_minutes` is 0; `planned_minutes` is 0; `unplanned_minutes` is 0
- Data: downtime_events for other areas; no assets with the queried area

## AC3: Given no downtime events exist for the query, When the endpoint is called, Then the response returns an empty array with total_minutes = 0.

### 14-3-downtime-pareto-api-endpoint-E2E-013: No downtime events returns empty items and zero totals
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains no records for asset "asset-1" on "2025-01-15"; the `daily_summaries` table also contains no records for this query
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200; `items` is an empty array `[]`; `total_downtime_minutes` is 0; `planned_minutes` is 0; `unplanned_minutes` is 0; `total_events` is 0
- Data: Empty mock tables for both downtime_events and daily_summaries

### 14-3-downtime-pareto-api-endpoint-E2E-014: No downtime_events falls back to daily_summaries data
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table has no records for asset "asset-1" on "2025-01-15"; the `daily_summaries` table HAS records for asset "asset-1" in that date range with downtime data
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200; `items` are populated from `daily_summaries` data; `data_source` is "daily_summaries"; `planned_minutes` defaults to 0 (daily_summaries has no is_planned data); `unplanned_minutes` defaults to 0
- Data: Empty downtime_events; populated daily_summaries with reason codes and downtime minutes

### 14-3-downtime-pareto-api-endpoint-INT-005: Fallback queries daily_summaries when downtime_events returns empty
- Priority: P0
- Type: integration
- Given: A mock Supabase client returns empty data for `downtime_events` table query; returns populated data for `daily_summaries` query
- When: The Pareto endpoint handler executes the downtime_events-first strategy
- Then: The service first queries `downtime_events`; upon receiving empty results, falls through to query `daily_summaries`; the final response uses daily_summaries data
- Data: Mock Supabase client with empty downtime_events and populated daily_summaries

### 14-3-downtime-pareto-api-endpoint-E2E-015: Both tables empty returns valid empty response
- Priority: P1
- Type: e2e
- Given: Both `downtime_events` and `daily_summaries` tables have no records for asset "asset-1" on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200 (not 404); `items` is `[]`; all totals are 0; response is a valid ParetoResponse
- Data: Empty mock data for both tables

## Additional Specifications (Cross-cutting concerns)

### 14-3-downtime-pareto-api-endpoint-E2E-016: Endpoint handles database errors gracefully
- Priority: P1
- Type: e2e
- Given: The Supabase client raises an exception when querying `downtime_events`
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 500; response body contains an error message; the error is logged
- Data: Mock Supabase client configured to raise an exception

### 14-3-downtime-pareto-api-endpoint-UNIT-005: New ParetoResponse fields are backward compatible
- Priority: P1
- Type: unit
- Given: A ParetoResponse is constructed using only the fields that existed before this story (items, total_downtime_minutes, total_financial_impact, total_events, data_source, last_updated)
- When: The response is serialized to JSON
- Then: `planned_minutes` appears with default value 0; `unplanned_minutes` appears with default value 0; all ParetoItem objects have `is_planned` with default value False; existing fields remain unchanged
- Data: ParetoResponse with pre-story-14.3 field set only

### 14-3-downtime-pareto-api-endpoint-INT-006: Endpoint is async and uses async service methods
- Priority: P2
- Type: integration
- Given: The endpoint handler and new service methods are defined
- When: The code is inspected
- Then: `get_downtime_pareto()` is an async function; `get_downtime_from_events_table()` is an async method; `transform_downtime_events_records()` is an async method; all Supabase queries use `.execute()` (not blocking the event loop)
- Data: Code inspection / import verification

### 14-3-downtime-pareto-api-endpoint-INT-007: Data source is reported as "downtime_events" when events table is used
- Priority: P1
- Type: integration
- Given: The `downtime_events` table contains records for the query parameters
- When: The Pareto endpoint processes the request using the events table path
- Then: The response `data_source` field is "downtime_events" (not "daily_summaries" or "live_snapshots")
- Data: Populated downtime_events mock data

edge_cases:
  - Single reason code across all events: should return 1 ParetoItem with percentage=100%, cumulative_percentage=100%, threshold_80_index=0
  - All events have the same duration: ordering is stable; percentages are evenly distributed
  - Reason code appears for both planned and unplanned events: is_planned determined by majority of minutes
  - Very large number of distinct reason codes (e.g., 50): all returned, percentages still sum to ~100%
  - Reason code with exactly 50/50 planned vs unplanned minutes: is_planned=False (planned_minutes not > unplanned_minutes)
  - Date far in the past with no data: returns empty response, not an error
  - Both asset_id and area provided simultaneously: asset_id should take precedence or both filters should apply (verify behavior)
  - Downtime events with very large duration_minutes (e.g., 10000): no overflow, correct percentage calculation

error_scenarios:
  - Database connection failure on downtime_events query → 500 Internal Server Error
  - Database connection failure on fallback daily_summaries query → 500 Internal Server Error
  - Invalid date format in query parameter → 422 Validation Error (FastAPI auto-validates)
  - Invalid UUID for asset_id → 422 Validation Error or empty results (depending on validation)
  - Missing auth token → 401 Unauthorized
  - Expired auth token → 401 Unauthorized
  - Assets table query fails during area filtering → 500 Internal Server Error

test_file_mapping:
  - 14-3-downtime-pareto-api-endpoint-E2E-*: apps/api/tests/test_downtime_pareto.py
  - 14-3-downtime-pareto-api-endpoint-UNIT-*: apps/api/tests/test_downtime_pareto.py
  - 14-3-downtime-pareto-api-endpoint-INT-*: apps/api/tests/test_downtime_pareto.py

TEST SPEC END

---

## DESIGN: 14-4-trend-indicators-on-action-cards
**Timestamp:** 2026-02-11 19:07:31

DESIGN START
story_id: 14-4-trend-indicators-on-action-cards

files_to_modify:
  - path: apps/web/src/components/action-engine/types.ts
    action: modify
    purpose: Add TrendData interface and optional trendData field to ActionItem
  - path: apps/web/src/hooks/useDailyActions.ts
    action: modify
    purpose: Add trend_data snake_case field to the API-shaped ActionItem interface
  - path: apps/web/src/components/action-engine/transformers.ts
    action: modify
    purpose: Map API trend_data (snake_case) to component trendData (camelCase) in transformAPIActionItem()
  - path: apps/web/src/components/action-engine/TrendIndicator.tsx
    action: create
    purpose: New component rendering trend arrow (green/red/gray SVG), percentage change text, and 7-day Recharts sparkline with skeleton state
  - path: apps/web/src/components/action-engine/RepeatOffenderBadge.tsx
    action: create
    purpose: New component rendering "New" (info), "Nth day in a row" (warning), "X of 7 days" (warning), or "2nd day" (outline) badges using Shadcn Badge
  - path: apps/web/src/components/action-engine/InsightSection.tsx
    action: modify
    purpose: Accept optional trendData prop; render RepeatOffenderBadge inline with PriorityBadge; render TrendIndicator row between badge row and recommendation text
  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Pass item.trendData through to InsightSection
  - path: apps/web/src/components/action-engine/index.ts
    action: modify
    purpose: Export TrendIndicator, RepeatOffenderBadge components and TrendData type
  - path: apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx
    action: create
    purpose: Unit tests for trend arrow direction logic, sparkline rendering, skeleton state, and ARIA labels
  - path: apps/web/src/components/action-engine/__tests__/RepeatOffenderBadge.test.tsx
    action: create
    purpose: Unit tests for badge text/variant selection across consecutive_days and days_on_report combinations
  - path: apps/web/src/components/action-engine/__tests__/transformers.trend.test.tsx
    action: create
    purpose: Unit tests for trend_data mapping in transformAPIActionItem

patterns_to_use:
  - 'use client' directive: Both new components are interactive (conditionally render based on props). Matches InsightSection.tsx, PriorityBadge.tsx, AssignmentBadge.tsx pattern.
  - Shadcn Badge with variant prop: RepeatOffenderBadge uses <Badge variant="warning"> and <Badge variant="info"> from @/components/ui/badge, matching the AssignmentBadge.tsx pattern (line 26-35) where Badge wraps icon + text with gap-1.5 and ARIA label.
  - cn() utility for conditional classes: All Tailwind classes composed via cn() from @/lib/utils, matching every existing component.
  - Recharts minimal LineChart: Use LineChart + Line from 'recharts' with width=80, height=24, no axes/grid/tooltip/legend, dot=false, isAnimationActive=false. This follows the existing Recharts import pattern from ParetoChart.tsx/ProductMixChart.tsx but in a minimal sparkline configuration.
  - InsightSectionProps interface extension: Add optional trendData and isLoading props following the same pattern as followUp?: FollowUpData | null (line 34 of InsightSection.tsx).
  - vitest + @testing-library/react: Test mocking pattern with vi.mock('next/navigation') and render/screen from @testing-library/react, matching InsightEvidenceCard.badge.test.tsx.
  - createMockActionItem fixture factory: Extend the existing test fixture pattern with optional trendData field for test data creation.
  - Transformer snake_case→camelCase mapping: Follow the existing acknowledgment mapping pattern in transformAPIActionItem() (line 205: `acknowledgment: item.acknowledgment ?? null`).

dependencies:
  - recharts: installed (^3.6.0 in apps/web/package.json)
  - @/components/ui/badge: installed (Badge with warning and info variants confirmed at badge.tsx lines 39-41)
  - lucide-react: installed (used throughout existing components for icons)
  - class-variance-authority: installed (used by Badge component)
  - vitest: installed (used by all existing test files)
  - @testing-library/react: installed (used by all existing test files)

acceptance_criteria_mapping:
  - AC1 (Repeat offender badge when consecutive_days >= 3): RepeatOffenderBadge.tsx — renders Badge variant="warning" with text like "3rd day in a row". Logic: consecutive_days >= 3 shows ordinal suffix + "day in a row". Component receives trendData from InsightSection. Placed inline with PriorityBadge in InsightSection.tsx row 1.
  - AC2 (Trend arrow based on week_over_week_change): TrendIndicator.tsx — isImprovement() helper uses priority prop to determine direction: OEE positive=good (green down arrow means metric worsened, actually: OEE up=green up arrow, downtime up=red up arrow). Specifically: for OEE, change > 0 = improving = green UP arrow; for FINANCIAL, change < 0 = improving = green DOWN arrow; abs(change) < 2 = gray horizontal arrow; SAFETY = no arrow.
  - AC3 (7-day sparkline): TrendIndicator.tsx — Recharts LineChart (80x24px) with metric_values array mapped to {value} data points. Null values filtered or skipped. Stroke color matches trend direction (green/red/gray).
  - AC4 (New badge when first appearance): RepeatOffenderBadge.tsx — when trendData has consecutive_days=1 AND days_on_report=1, renders Badge variant="info" with text "New". When trendData is undefined/null, also shows nothing (graceful degradation per AC5).
  - AC5 (Loading/unavailable skeleton): TrendIndicator.tsx — accepts isLoading prop; when true or when trendData is undefined, renders compact skeleton placeholder (animated pulse div, ~80x24px for sparkline area, ~40x20px for arrow area). InsightSection passes loading state through.
  - AC6 (TypeScript types + transformer): types.ts — new TrendData interface with metricHistory (number|null)[], daysOnReport, consecutiveDays, weekOverWeekChange fields. ActionItem gains optional trendData?: TrendData. useDailyActions.ts ActionItem gains trend_data snake_case field. transformers.ts transformAPIActionItem() maps: trendData: item.trend_data ? { metricHistory: item.trend_data.metric_values, daysOnReport: item.trend_data.days_on_report, consecutiveDays: item.trend_data.consecutive_days, weekOverWeekChange: item.trend_data.week_over_week_change } : undefined.
  - AC7 (Tablet responsive layout): InsightSection.tsx — trend indicators placed in the existing flex-col gap-3 layout. Row 1: [PriorityBadge] [RepeatOffenderBadge] [Financial Impact]. New Row 2: [TrendArrow + % change] [Sparkline]. Both rows use flex-wrap to handle narrow viewports. Sparkline at 80x24px and arrow at ~16px are compact enough to fit within the md:p-6 card padding (which provides ~50% of card width on tablet).

risks:
  - Risk: Recharts 3.6 LineChart with very small dimensions (80x24) may have rendering issues or require responsive container. Mitigation: Use fixed width/height props directly on LineChart (not ResponsiveContainer), matching the story's explicit size recommendation. Test in browser at tablet viewport. If issues arise, fallback to a pure SVG polyline component.
  - Risk: TrendData may be null/undefined for all items if Story 14.2 backend is not yet deployed. Mitigation: All trend components handle undefined trendData gracefully — RepeatOffenderBadge renders nothing, TrendIndicator renders nothing (or skeleton if isLoading). The trendData field is optional (?) on ActionItem. Tested explicitly in AC5 tests.
  - Risk: metric_values array from API may contain null values (missing days), which Recharts may not handle well. Mitigation: Filter out null entries before passing to Recharts data array, preserving only non-null {value, index} pairs so the sparkline connects valid points. Document this behavior.
  - Risk: Trend direction logic is category-dependent and easy to get wrong. Mitigation: Centralize in a single isImprovement(change, priority) function with explicit mapping per PriorityType. SAFETY items skip trend arrows entirely. Unit test every combination.
  - Risk: Sparkline adds Recharts bundle weight to every card render. Mitigation: isAnimationActive={false} prevents animation overhead. Recharts is already in the bundle (used by ParetoChart, ProductMixChart). The LineChart + Line components are lightweight compared to full chart usage. No new dependency added.
  - Risk: The ordinal suffix generation for "3rd day in a row", "4th day in a row" etc. needs a small utility. Mitigation: Inline helper function (5 lines) in RepeatOffenderBadge.tsx — handles 1st/2nd/3rd + "th" default. No external dependency needed.

estimated_test_files:
  - apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx: Tests trend arrow direction for OEE (positive change = green), FINANCIAL (negative change = green), SAFETY (no arrow), stable range (<2% = gray), sparkline renders with valid data, skeleton state when loading, ARIA labels describe trend direction and percentage, handles null metric_values gracefully
  - apps/web/src/components/action-engine/__tests__/RepeatOffenderBadge.test.tsx: Tests "New" badge (info) when consecutive=1 & days_on_report=1, "3rd day in a row" (warning) when consecutive>=3, "4 of 7 days" (warning) when days_on_report>=3 but consecutive<3, "2nd day" (outline) when consecutive=2, no badge when trendData is undefined, correct ARIA labels for each state
  - apps/web/src/components/action-engine/__tests__/transformers.trend.test.tsx: Tests transformAPIActionItem maps trend_data snake_case to trendData camelCase, handles null trend_data (returns undefined trendData), handles partial trend_data fields

implementation_order:
  1. Add TrendData interface and extend ActionItem in apps/web/src/components/action-engine/types.ts
     - Define TrendData with metricHistory: (number | null)[], daysOnReport: number, consecutiveDays: number, weekOverWeekChange: number | null
     - Add optional trendData?: TrendData to ActionItem interface (after acknowledgment field, line 100)
  2. Add trend_data field to API ActionItem in apps/web/src/hooks/useDailyActions.ts
     - Add optional trend_data field to the ActionItem interface (after acknowledgment, line 54): trend_data?: { metric_values: (number | null)[], days_on_report: number, consecutive_days: number, week_over_week_change: number | null } | null
  3. Update transformers.ts to map trend_data
     - In transformAPIActionItem(), add trendData mapping after the acknowledgment line (line 205): map item.trend_data snake_case fields to camelCase TrendData, returning undefined when trend_data is null/undefined
     - Import TrendData type from ./types
  4. Create RepeatOffenderBadge.tsx component
     - 'use client' directive
     - Import Badge from @/components/ui/badge, cn from @/lib/utils
     - Accept props: trendData (optional TrendData), className
     - Implement ordinal suffix helper (getOrdinalSuffix)
     - Render logic: no trendData → null; consecutive=1 & days_on_report=1 → Badge variant="info" "New"; consecutive>=3 → Badge variant="warning" "{N}th day in a row"; days_on_report>=3 & consecutive<3 → Badge variant="warning" "{X} of 7 days"; consecutive=2 → Badge variant="outline" "2nd day"; else → null
     - Add ARIA labels for screen readers
  5. Create TrendIndicator.tsx component
     - 'use client' directive
     - Import LineChart, Line from 'recharts', cn from @/lib/utils
     - Accept props: trendData (optional TrendData), priority (PriorityType), isLoading (boolean), className
     - Implement isImprovement(change, priority) logic: OEE → change > 0 is good; FINANCIAL → change < 0 is good; SAFETY → return null (no arrow)
     - Implement getTrendDirection(): 'improving' | 'worsening' | 'stable' | null based on priority and absolute change threshold (2%)
     - Render trend arrow as inline SVG: green ArrowDown for improving (lower is better metric going down), green ArrowUp for improving OEE going up — actually use TrendingUp/TrendingDown from lucide-react for consistency
     - Render percentage change text next to arrow (e.g., "+3.1%" or "-2.5%")
     - Render sparkline: filter null values from metricHistory, map to [{value}], render LineChart 80x24 with colored Line
     - Skeleton state: when isLoading or no trendData and isLoading, render pulse-animated placeholder divs
     - ARIA labels: "Trend: improving, OEE up 3.1%" / "Trend: worsening, downtime up 5.2%" / "Trend: stable"
  6. Integrate into InsightSection.tsx
     - Add trendData?: TrendData and isLoading?: boolean to InsightSectionProps interface
     - Import TrendIndicator and RepeatOffenderBadge
     - In the badge row (line 94): add <RepeatOffenderBadge trendData={trendData} /> after <PriorityBadge priority={priority} />
     - After the badge row and before the recommendation h3 (line 117): add new row with <TrendIndicator trendData={trendData} priority={priority} isLoading={isLoading} />
     - Only render the TrendIndicator row if trendData exists or isLoading is true (avoid empty space)
  7. Wire InsightEvidenceCard.tsx to pass trendData
     - In the InsightSection JSX call (line 91-102): add trendData={item.trendData} prop
  8. Update barrel exports in index.ts
     - Add: export { TrendIndicator } from './TrendIndicator'
     - Add: export { RepeatOffenderBadge } from './RepeatOffenderBadge'
     - Add TrendData to the type exports from './types'
  9. Write unit tests for RepeatOffenderBadge
     - Create __tests__/RepeatOffenderBadge.test.tsx
     - Mock next/navigation (standard pattern)
     - Test all badge states: New, consecutive>=3, days_on_report>=3, consecutive=2, no data
     - Verify correct Badge variant (info/warning/outline) and text content
     - Verify ARIA accessibility
  10. Write unit tests for TrendIndicator
      - Create __tests__/TrendIndicator.test.tsx
      - Mock next/navigation (standard pattern)
      - Test OEE improving (positive change → green), OEE worsening (negative → red), stable (<2% → gray)
      - Test FINANCIAL improving (negative change → green), FINANCIAL worsening (positive → red)
      - Test SAFETY shows no trend arrow
      - Test sparkline renders (verify SVG/LineChart presence)
      - Test skeleton state when isLoading=true
      - Test graceful handling of all-null metricHistory
  11. Write unit tests for transformer mapping
      - Create __tests__/transformers.trend.test.tsx
      - Test transformAPIActionItem with trend_data present → trendData populated
      - Test transformAPIActionItem with trend_data null → trendData undefined
      - Test transformAPIActionItem with trend_data absent → trendData undefined
  12. Visual verification at tablet viewport
      - Manual check: render cards at 768px-1024px width
      - Confirm trend indicators fit within InsightSection without overflow
      - Verify dark mode colors for arrows and sparkline
      - Confirm graceful degradation when trendData is undefined
DESIGN END

---

## TEST_SPEC: 14-4-trend-indicators-on-action-cards
**Timestamp:** 2026-02-11 19:10:32

TEST SPEC START
story_id: 14-4-trend-indicators-on-action-cards
generated: 2026-02-11

test_specifications:

## AC1: Repeat offender badge displayed when consecutive_days >= 3

### 14-4-trend-indicators-on-action-cards-UNIT-001: Repeat offender badge renders with warning variant when consecutive_days >= 3
- Priority: P0
- Type: unit
- Given: An action item has trendData with consecutiveDays = 3 and daysOnReport = 5
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "3rd day in a row"
- Data: trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: -2.5 }

### 14-4-trend-indicators-on-action-cards-UNIT-002: Repeat offender badge shows correct ordinal suffix for higher consecutive counts
- Priority: P0
- Type: unit
- Given: An action item has trendData with consecutiveDays = 5
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "5th day in a row"
- Data: trendData = { consecutiveDays: 5, daysOnReport: 6, metricHistory: [...], weekOverWeekChange: -1.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-003: Repeat offender badge shows correct ordinal for 4th consecutive day
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 4
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "4th day in a row"
- Data: trendData = { consecutiveDays: 4, daysOnReport: 4, metricHistory: [...], weekOverWeekChange: 3.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-004: Frequency badge shown when days_on_report >= 3 but consecutive_days < 3
- Priority: P0
- Type: unit
- Given: An action item has trendData with daysOnReport = 4 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "4 of 7 days"
- Data: trendData = { consecutiveDays: 1, daysOnReport: 4, metricHistory: [...], weekOverWeekChange: -2.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-005: Second day badge shown with outline variant when consecutive_days = 2
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 2 and daysOnReport = 2
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="outline" is displayed containing text "2nd day"
- Data: trendData = { consecutiveDays: 2, daysOnReport: 2, metricHistory: [...], weekOverWeekChange: 1.5 }

### 14-4-trend-indicators-on-action-cards-UNIT-006: Repeat offender badge has correct ARIA label for accessibility
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 3
- When: The RepeatOffenderBadge component renders
- Then: The badge element has an appropriate aria-label describing the repeat status (e.g., "Repeat issue: 3rd day in a row")
- Data: trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [...], weekOverWeekChange: -3.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-007: Consecutive_days >= 3 takes precedence over days_on_report >= 3
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 3 AND daysOnReport = 5 (both conditions met)
- When: The RepeatOffenderBadge component renders
- Then: The "3rd day in a row" badge is shown (not "5 of 7 days") because consecutive takes precedence
- Data: trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [...], weekOverWeekChange: -1.0 }

## AC2: Trend arrow displayed based on week_over_week_change

### 14-4-trend-indicators-on-action-cards-UNIT-008: Green arrow shown when OEE metric improves (positive change)
- Priority: P0
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 3.1
- When: The TrendIndicator component renders
- Then: A green trend arrow (up/improving direction) is displayed with text "+3.1%"
- Data: priority = "OEE", trendData = { weekOverWeekChange: 3.1, metricHistory: [70,71,72,73,74,75,76], consecutiveDays: 2, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-009: Red arrow shown when OEE metric worsens (negative change)
- Priority: P0
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -4.2
- When: The TrendIndicator component renders
- Then: A red trend arrow (down/worsening direction) is displayed with text "-4.2%"
- Data: priority = "OEE", trendData = { weekOverWeekChange: -4.2, metricHistory: [76,75,74,73,72,71,70], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-010: Green arrow shown when FINANCIAL metric improves (negative change = loss decreased)
- Priority: P0
- Type: unit
- Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = -5.0
- When: The TrendIndicator component renders
- Then: A green trend arrow (improving direction) is displayed with text "-5.0%"
- Data: priority = "FINANCIAL", trendData = { weekOverWeekChange: -5.0, metricHistory: [100,95,90,85,80,75,70], consecutiveDays: 2, daysOnReport: 4 }

### 14-4-trend-indicators-on-action-cards-UNIT-011: Red arrow shown when FINANCIAL metric worsens (positive change = loss increased)
- Priority: P0
- Type: unit
- Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = 6.3
- When: The TrendIndicator component renders
- Then: A red trend arrow (worsening direction) is displayed with text "+6.3%"
- Data: priority = "FINANCIAL", trendData = { weekOverWeekChange: 6.3, metricHistory: [70,75,80,85,90,95,100], consecutiveDays: 3, daysOnReport: 5 }

### 14-4-trend-indicators-on-action-cards-UNIT-012: Gray horizontal arrow shown when change is stable (< 2% absolute)
- Priority: P0
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 1.5
- When: The TrendIndicator component renders
- Then: A gray horizontal arrow is displayed indicating stable trend
- Data: priority = "OEE", trendData = { weekOverWeekChange: 1.5, metricHistory: [72,73,72,73,72,73,72], consecutiveDays: 1, daysOnReport: 2 }

### 14-4-trend-indicators-on-action-cards-UNIT-013: Gray horizontal arrow for negative stable change (> -2%)
- Priority: P1
- Type: unit
- Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = -1.9
- When: The TrendIndicator component renders
- Then: A gray horizontal arrow is displayed indicating stable trend
- Data: priority = "FINANCIAL", trendData = { weekOverWeekChange: -1.9, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-014: Boundary test - exactly 2% absolute change shows directional arrow (not stable)
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 2.0
- When: The TrendIndicator component renders
- Then: A green arrow is displayed (2.0% is at the boundary, should show directional since stable is < 2%)
- Data: priority = "OEE", trendData = { weekOverWeekChange: 2.0, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-015: Boundary test - exactly -2% absolute change shows directional arrow
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -2.0
- When: The TrendIndicator component renders
- Then: A red arrow is displayed (exactly 2% absolute is not < 2%, so not stable)
- Data: priority = "OEE", trendData = { weekOverWeekChange: -2.0, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-016: No trend arrow for SAFETY priority items
- Priority: P0
- Type: unit
- Given: An action item has priority = "SAFETY" and trendData with weekOverWeekChange = -5.0
- When: The TrendIndicator component renders
- Then: No trend arrow is displayed (safety items do not show directional trend arrows)
- Data: priority = "SAFETY", trendData = { weekOverWeekChange: -5.0, metricHistory: [...], consecutiveDays: 3, daysOnReport: 5 }

### 14-4-trend-indicators-on-action-cards-UNIT-017: Trend arrow has correct ARIA label describing direction and percentage
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -3.1
- When: The TrendIndicator component renders
- Then: The trend indicator has an ARIA label like "Trend: worsening, OEE down 3.1%"
- Data: priority = "OEE", trendData = { weekOverWeekChange: -3.1, metricHistory: [...], consecutiveDays: 2, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-018: Zero week_over_week_change shows gray stable arrow
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 0
- When: The TrendIndicator component renders
- Then: A gray horizontal arrow is displayed indicating stable trend
- Data: priority = "OEE", trendData = { weekOverWeekChange: 0, metricHistory: [72,72,72,72,72,72,72], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-019: Null weekOverWeekChange does not render trend arrow
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = null
- When: The TrendIndicator component renders
- Then: No trend arrow is displayed (graceful handling of null)
- Data: priority = "OEE", trendData = { weekOverWeekChange: null, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

## AC3: 7-day sparkline chart displayed from trend_data

### 14-4-trend-indicators-on-action-cards-UNIT-020: Sparkline renders with 7-day metric history data
- Priority: P0
- Type: unit
- Given: An action item has trendData with metricHistory = [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5]
- When: The TrendIndicator component renders
- Then: A small sparkline chart (approximately 80px wide x 24px tall) is rendered next to the metric value showing the 7-day trend
- Data: trendData = { metricHistory: [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5], weekOverWeekChange: 0.0, consecutiveDays: 2, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-021: Sparkline stroke color matches trend direction (green for improving)
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 3.5 (improving)
- When: The TrendIndicator component renders
- Then: The sparkline line stroke color is green
- Data: priority = "OEE", trendData = { metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 3.5, consecutiveDays: 1, daysOnReport: 2 }

### 14-4-trend-indicators-on-action-cards-UNIT-022: Sparkline stroke color is red for worsening trend
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -4.0 (worsening)
- When: The TrendIndicator component renders
- Then: The sparkline line stroke color is red
- Data: priority = "OEE", trendData = { metricHistory: [76,75,74,73,72,71,70], weekOverWeekChange: -4.0, consecutiveDays: 2, daysOnReport: 4 }

### 14-4-trend-indicators-on-action-cards-UNIT-023: Sparkline stroke color is gray for stable trend
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 0.5 (stable)
- When: The TrendIndicator component renders
- Then: The sparkline line stroke color is gray
- Data: priority = "OEE", trendData = { metricHistory: [72,72.5,72,72.5,72,72.5,72], weekOverWeekChange: 0.5, consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-024: Sparkline handles null values in metricHistory gracefully
- Priority: P1
- Type: unit
- Given: An action item has trendData with metricHistory = [72.5, null, 68.3, null, 69.2, 73.8, 72.5]
- When: The TrendIndicator component renders
- Then: A sparkline is rendered connecting only the non-null data points without errors
- Data: trendData = { metricHistory: [72.5, null, 68.3, null, 69.2, 73.8, 72.5], weekOverWeekChange: 0.0, consecutiveDays: 1, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-025: Sparkline handles all-null metricHistory gracefully
- Priority: P1
- Type: unit
- Given: An action item has trendData with metricHistory = [null, null, null, null, null, null, null]
- When: The TrendIndicator component renders
- Then: No sparkline is rendered (graceful degradation) and no error is thrown
- Data: trendData = { metricHistory: [null, null, null, null, null, null, null], weekOverWeekChange: null, consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-026: Sparkline renders with empty metricHistory array
- Priority: P2
- Type: unit
- Given: An action item has trendData with metricHistory = []
- When: The TrendIndicator component renders
- Then: No sparkline is rendered (graceful degradation) and no error is thrown
- Data: trendData = { metricHistory: [], weekOverWeekChange: 2.0, consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-027: Sparkline renders without animation
- Priority: P2
- Type: unit
- Given: An action item has valid trendData with metricHistory
- When: The TrendIndicator component renders
- Then: The Recharts LineChart renders with isAnimationActive={false} for instant display
- Data: trendData = { metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 2.5, consecutiveDays: 1, daysOnReport: 1 }

## AC4: "New" badge shown for first-appearance items

### 14-4-trend-indicators-on-action-cards-UNIT-028: "New" badge shown when days_on_report = 1 and consecutive_days = 1
- Priority: P0
- Type: unit
- Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="info" is displayed containing text "New"
- Data: trendData = { consecutiveDays: 1, daysOnReport: 1, metricHistory: [72.5], weekOverWeekChange: null }

### 14-4-trend-indicators-on-action-cards-UNIT-029: "New" badge has info variant styling (blue background)
- Priority: P1
- Type: unit
- Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: The Badge uses the "info" variant which applies blue background styling
- Data: trendData = { consecutiveDays: 1, daysOnReport: 1, metricHistory: [72.5], weekOverWeekChange: null }

### 14-4-trend-indicators-on-action-cards-UNIT-030: "New" badge has appropriate ARIA label
- Priority: P1
- Type: unit
- Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: The badge has an ARIA label like "New issue"
- Data: trendData = { consecutiveDays: 1, daysOnReport: 1, metricHistory: [72.5], weekOverWeekChange: null }

### 14-4-trend-indicators-on-action-cards-UNIT-031: No badge rendered when trendData is undefined
- Priority: P0
- Type: unit
- Given: An action item has no trendData (trendData is undefined)
- When: The RepeatOffenderBadge component renders
- Then: No badge is rendered (returns null)
- Data: trendData = undefined

### 14-4-trend-indicators-on-action-cards-UNIT-032: No badge rendered when trendData is null
- Priority: P1
- Type: unit
- Given: An action item has trendData = null
- When: The RepeatOffenderBadge component renders
- Then: No badge is rendered (returns null)
- Data: trendData = null

## AC5: Skeleton placeholder when trend data is loading or unavailable

### 14-4-trend-indicators-on-action-cards-UNIT-033: Skeleton placeholder shown when isLoading is true
- Priority: P0
- Type: unit
- Given: The TrendIndicator component receives isLoading = true and no trendData
- When: The component renders
- Then: A compact skeleton placeholder is displayed (animated pulse divs) in place of the trend arrow and sparkline
- Data: isLoading = true, trendData = undefined, priority = "OEE"

### 14-4-trend-indicators-on-action-cards-UNIT-034: Card remains functional without trend data
- Priority: P0
- Type: integration
- Given: An action item has no trendData (undefined) and isLoading is false
- When: The InsightEvidenceCard renders
- Then: The card renders fully with PriorityBadge, recommendation text, asset name, timestamp, and action buttons; the trend indicator area is either empty or absent (no error)
- Data: ActionItem with trendData = undefined

### 14-4-trend-indicators-on-action-cards-UNIT-035: Skeleton placeholder has correct approximate dimensions
- Priority: P2
- Type: unit
- Given: The TrendIndicator component receives isLoading = true
- When: The component renders
- Then: The skeleton placeholder area is approximately the same size as the actual trend indicators (80x24px sparkline area, arrow area)
- Data: isLoading = true, trendData = undefined, priority = "OEE"

### 14-4-trend-indicators-on-action-cards-INT-001: InsightSection passes loading state to TrendIndicator
- Priority: P1
- Type: integration
- Given: InsightSection receives isLoading = true and trendData = undefined
- When: The component renders
- Then: The TrendIndicator within InsightSection shows a skeleton state
- Data: InsightSectionProps with isLoading = true, trendData = undefined

### 14-4-trend-indicators-on-action-cards-UNIT-036: TrendIndicator does not render when trendData is undefined and isLoading is false
- Priority: P1
- Type: unit
- Given: TrendIndicator receives trendData = undefined and isLoading = false
- When: The component renders
- Then: Nothing is rendered (no empty space, no skeleton, no indicators)
- Data: trendData = undefined, isLoading = false, priority = "OEE"

## AC6: TypeScript types and transformer mapping for trend_data

### 14-4-trend-indicators-on-action-cards-UNIT-037: TrendData interface has correct fields
- Priority: P0
- Type: unit
- Given: The TrendData interface is defined in types.ts
- When: A developer creates a TrendData object
- Then: The interface requires/allows: metricHistory: (number | null)[], daysOnReport: number, consecutiveDays: number, weekOverWeekChange: number | null
- Data: Type-level verification

### 14-4-trend-indicators-on-action-cards-UNIT-038: ActionItem type includes optional trendData field
- Priority: P0
- Type: unit
- Given: The ActionItem interface in types.ts
- When: A developer creates an ActionItem
- Then: The trendData field is optional (trendData?: TrendData) and the item can be created without it
- Data: Type-level verification

### 14-4-trend-indicators-on-action-cards-UNIT-039: Transformer maps API trend_data snake_case to component trendData camelCase
- Priority: P0
- Type: unit
- Given: An API response ActionItem has trend_data = { metric_values: [72.5, 74.1, 68.3], days_on_report: 4, consecutive_days: 3, week_over_week_change: -3.1 }
- When: transformAPIActionItem() processes the item
- Then: The result has trendData = { metricHistory: [72.5, 74.1, 68.3], daysOnReport: 4, consecutiveDays: 3, weekOverWeekChange: -3.1 }
- Data: API item with trend_data field populated

### 14-4-trend-indicators-on-action-cards-UNIT-040: Transformer handles null trend_data from API
- Priority: P0
- Type: unit
- Given: An API response ActionItem has trend_data = null
- When: transformAPIActionItem() processes the item
- Then: The result has trendData = undefined (not null)
- Data: API item with trend_data: null

### 14-4-trend-indicators-on-action-cards-UNIT-041: Transformer handles absent trend_data from API
- Priority: P0
- Type: unit
- Given: An API response ActionItem has no trend_data field at all
- When: transformAPIActionItem() processes the item
- Then: The result has trendData = undefined
- Data: API item without trend_data key

### 14-4-trend-indicators-on-action-cards-UNIT-042: Transformer preserves null values in metric_values array
- Priority: P1
- Type: unit
- Given: An API response has trend_data.metric_values = [72.5, null, 68.3, null, 69.2, 73.8, 72.5]
- When: transformAPIActionItem() processes the item
- Then: The result trendData.metricHistory = [72.5, null, 68.3, null, 69.2, 73.8, 72.5] (nulls preserved for component to handle)
- Data: API item with trend_data containing null metric values

### 14-4-trend-indicators-on-action-cards-UNIT-043: Transformer handles null week_over_week_change
- Priority: P1
- Type: unit
- Given: An API response has trend_data with week_over_week_change = null
- When: transformAPIActionItem() processes the item
- Then: The result trendData.weekOverWeekChange = null
- Data: API item with trend_data.week_over_week_change: null

## AC7: Responsive layout on tablet viewport

### 14-4-trend-indicators-on-action-cards-INT-002: Trend indicators render within InsightSection layout
- Priority: P0
- Type: integration
- Given: An InsightSection with trendData, priority, and all standard props
- When: The component renders
- Then: RepeatOffenderBadge appears inline with PriorityBadge in the first row AND TrendIndicator appears as a new row between the badge row and recommendation text
- Data: Full InsightSectionProps with trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 3.5 }, priority = "OEE"

### 14-4-trend-indicators-on-action-cards-INT-003: InsightEvidenceCard passes trendData to InsightSection
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard renders with an ActionItem that has trendData
- When: The card renders
- Then: The InsightSection child receives the trendData prop and renders trend indicators
- Data: ActionItem with trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 3.5 }

### 14-4-trend-indicators-on-action-cards-E2E-001: Trend indicators visible on tablet viewport without scrolling
- Priority: P0
- Type: e2e
- Given: The action items page is loaded with items containing trend data
- When: Viewed on a tablet viewport (768px-1024px width)
- Then: The trend arrow, sparkline, and repeat offender badge are all visible and readable within the card's left column without horizontal scrolling
- Data: Viewport width 768px, ActionItem with full trendData

### 14-4-trend-indicators-on-action-cards-E2E-002: Trend indicators render correctly on desktop viewport
- Priority: P1
- Type: e2e
- Given: The action items page is loaded with items containing trend data
- When: Viewed on a desktop viewport (1280px+ width)
- Then: Trend indicators are rendered inline and proportionally sized within the card layout
- Data: Viewport width 1280px, ActionItem with full trendData

### 14-4-trend-indicators-on-action-cards-INT-004: Layout does not overflow when all trend elements are present
- Priority: P1
- Type: integration
- Given: An InsightSection with a repeat offender badge (consecutiveDays=5), trend arrow, percentage change text, sparkline, AND a long recommendation text
- When: The component renders at md breakpoint
- Then: No horizontal overflow occurs; all elements wrap appropriately within the card boundaries
- Data: InsightSectionProps with long recommendation text (~100 chars) and full trendData

### 14-4-trend-indicators-on-action-cards-INT-005: TrendIndicator and RepeatOffenderBadge exported from barrel index
- Priority: P1
- Type: integration
- Given: The action-engine index.ts barrel export file
- When: A consumer imports TrendIndicator, RepeatOffenderBadge, or TrendData from the barrel
- Then: All three exports are available and correctly typed
- Data: Import verification from '@/components/action-engine'

edge_cases:
  - metricHistory array with fewer than 7 data points (e.g., 3 data points for a new item that has only been tracked 3 days)
  - metricHistory array with all identical values (perfectly flat sparkline)
  - Extremely large weekOverWeekChange values (e.g., +500% or -90%) - display should not overflow
  - consecutiveDays = 0 (invalid/unexpected data from API) - should render nothing or handle gracefully
  - daysOnReport = 0 (invalid/unexpected data from API) - should render nothing or handle gracefully
  - Very large consecutiveDays (e.g., 30) - ordinal suffix should still work ("30th day in a row")
  - Negative metricHistory values (edge case for financial data) - sparkline should still render
  - weekOverWeekChange = -0 (negative zero) - should be treated as stable
  - ActionItem with trendData but missing some nested fields (partial trendData object)

error_scenarios:
  - API returns malformed trend_data (e.g., metric_values is not an array) - transformer should handle without crashing
  - API returns trend_data with unexpected field names - transformer should still produce valid output (missing fields become undefined)
  - Recharts LineChart fails to render (e.g., invalid data) - component should catch error and show fallback
  - trendData.weekOverWeekChange is NaN - should be treated as unavailable, no arrow shown
  - trendData.consecutiveDays is negative - should be treated as no badge
  - Rapid re-renders with changing trendData (no animation means no stale state issues)

test_file_mapping:
  - 14-4-trend-indicators-on-action-cards-UNIT-001 to UNIT-007: apps/web/src/components/action-engine/__tests__/RepeatOffenderBadge.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-008 to UNIT-019: apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-020 to UNIT-027: apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-028 to UNIT-032: apps/web/src/components/action-engine/__tests__/RepeatOffenderBadge.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-033 to UNIT-036: apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-037 to UNIT-038: apps/web/src/components/action-engine/__tests__/types.test.ts (compile-time / type assertion tests)
  - 14-4-trend-indicators-on-action-cards-UNIT-039 to UNIT-043: apps/web/src/components/action-engine/__tests__/transformers.trend.test.tsx
  - 14-4-trend-indicators-on-action-cards-INT-001 to INT-005: apps/web/src/components/action-engine/__tests__/InsightSection.trend.test.tsx
  - 14-4-trend-indicators-on-action-cards-E2E-001 to E2E-002: apps/web/e2e/action-cards-trend.spec.ts (Playwright or Cypress)

TEST SPEC END

---

## DESIGN: 14-5-downtime-pareto-chart-on-action-cards
**Timestamp:** 2026-02-11 19:45:37

DESIGN START
story_id: 14-5-downtime-pareto-chart-on-action-cards

files_to_modify:
  - path: apps/web/src/hooks/useDowntimePareto.ts
    action: create
    purpose: Data-fetching hook for Pareto data from GET /api/v1/downtime/pareto; follows useDailyActions pattern with useState/useEffect/useCallback/mountedRef, Supabase auth, and { data, isLoading, error, refetch } return shape
  - path: apps/web/src/components/action-engine/DowntimePareto.tsx
    action: create
    purpose: Compact inline horizontal bar chart (120-150px height) showing top 3-5 reason codes with planned/unplanned visual distinction, plus DowntimeParetoSkeleton for loading state
  - path: apps/web/src/components/action-engine/EvidenceSection.tsx
    action: modify
    purpose: Add optional assetId and reportDate props to EvidenceSectionProps; call useDowntimePareto conditionally inside OEEEvidenceDisplay; render DowntimePareto/DowntimeParetoSkeleton below existing OEE bars
  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Pass item.asset.id and reportDate to EvidenceSection as new assetId and reportDate props
  - path: apps/web/src/components/action-engine/index.ts
    action: modify
    purpose: Export DowntimePareto and DowntimeParetoSkeleton from barrel
  - path: apps/web/src/hooks/__tests__/useDowntimePareto.test.ts
    action: create
    purpose: Unit tests for hook: loading state, success with data, error handling, empty data, auth failure, refetch
  - path: apps/web/src/components/action-engine/__tests__/DowntimePareto.test.tsx
    action: create
    purpose: Component tests for chart rendering with OEE data, null/empty handling, skeleton loader, planned vs unplanned distinction, and non-OEE suppression
  - path: apps/web/src/components/action-engine/__tests__/EvidenceSection.pareto.test.tsx
    action: create
    purpose: Integration test for EvidenceSection conditionally rendering Pareto chart for OEE items and not for safety/financial items

patterns_to_use:
  - useDailyActions hook pattern: useState/useEffect/useCallback/useRef(mountedRef) with createClient() from @/lib/supabase/client, Bearer token auth, API_BASE_URL from NEXT_PUBLIC_API_URL env var, error state management. Returns { data, isLoading, error, refetch }. See useDailyActions.ts lines 116-229.
  - 'use client' directive: Both new files (hook and component) are client-side. Matches all existing action-engine components.
  - Recharts BarChart horizontal layout: Import BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell from 'recharts'. Use layout="vertical" for horizontal bars. Fixed height 120-150px. No CartesianGrid, no Legend, no cumulative Line. isAnimationActive={false} for instant render.
  - CHART_COLORS palette: Reuse hsl(210, 50%, 50%) for unplanned (solid) bars; create hatched SVG pattern via inline <defs><pattern> for planned bars. Use hsl(0, 72%, 51%) (barSafety) only for safety-flagged items. Matches ParetoChart.tsx color scheme.
  - Skeleton loader with animate-pulse: Use div with className="animate-pulse" containing bg-industrial-200 dark:bg-industrial-700 rounded bars matching chart dimensions. Pattern from InsightEvidenceCardSkeleton lines 139-171.
  - cn() utility for conditional classes: All Tailwind classes composed via cn() from @/lib/utils.
  - Vitest + Testing Library: vi.mock for Supabase client and Recharts; renderHook for hook tests; render/screen for component tests. Mock pattern from useActionAcknowledgment.test.ts and TrendIndicator.test.tsx.
  - EvidenceSectionProps extension: Add optional assetId?: string and reportDate?: string props (same pattern as existing optional className and defaultExpanded).
  - Type-based conditional rendering: Only render Pareto when evidence.type === 'oee_deviation' — matches the existing discriminated union pattern in renderEvidenceContent() at EvidenceSection.tsx lines 208-222.

dependencies:
  - recharts: installed (^3.6.0 in apps/web/package.json — BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell)
  - @/lib/supabase/client: installed (createClient function for auth)
  - @/lib/utils: installed (cn utility)
  - vitest: installed (test framework)
  - @testing-library/react: installed (render, screen, renderHook, act, waitFor)

acceptance_criteria_mapping:
  - AC1 (Horizontal bar chart with top 3-5 reason codes, duration, percentage, planned vs unplanned):
    - Hook: apps/web/src/hooks/useDowntimePareto.ts — fetches ParetoResponse from GET /api/v1/downtime/pareto?date={date}&asset_id={assetId}; returns { data: ParetoResponse | null, isLoading, error, refetch }
    - Component: apps/web/src/components/action-engine/DowntimePareto.tsx — accepts ParetoResponse data; slices items to top 5 (data.items.slice(0, 5)); renders Recharts BarChart layout="vertical" with horizontal bars; each bar label shows reason_code name + duration in minutes + percentage of total; planned bars (item.is_planned === true) rendered with hatched SVG fill pattern, unplanned bars rendered solid; height ~130px, no Card wrapper
    - Integration: apps/web/src/components/action-engine/EvidenceSection.tsx — OEEEvidenceDisplay receives assetId+reportDate, calls useDowntimePareto, passes data to DowntimePareto component below OEE bar comparison
    - Prop threading: apps/web/src/components/action-engine/InsightEvidenceCard.tsx — passes item.asset.id as assetId and reportDate (already computed at line 56-58) to EvidenceSection
  - AC2 (No Pareto for safety-only or financial-only items):
    - Component: DowntimePareto.tsx — returns null when data is null/undefined or items array is empty (component never receives data for non-OEE items)
    - Integration: EvidenceSection.tsx — hook only called inside OEEEvidenceDisplay path; SafetyEvidenceDisplay and FinancialEvidenceDisplay never trigger Pareto rendering. The type-based dispatch in renderEvidenceContent() (lines 208-222) already gates this — only the 'targetOEE' in data path renders OEE content where Pareto will be added
  - AC3 (Skeleton loader during loading):
    - Component: DowntimePareto.tsx — exports DowntimeParetoSkeleton with animate-pulse bars matching chart layout (3-4 horizontal bar skeletons at varying widths)
    - Integration: EvidenceSection.tsx — when useDowntimePareto.isLoading is true, renders DowntimeParetoSkeleton in place of chart

risks:
  - Risk: Calling useDowntimePareto inside OEEEvidenceDisplay sub-component violates React hooks rules if OEEEvidenceDisplay is conditionally called. Mitigation: Move the hook call to the top-level EvidenceSection component (not inside a conditional render function), guard the API call with a conditional (only fetch when evidence.type resolves to OEE). The hook accepts an `enabled` parameter — when false, it skips the fetch but is still called unconditionally, satisfying the Rules of Hooks. Alternatively, restructure OEEEvidenceDisplay from an inline function to a standalone component that always renders and contains its own hook.
  - Risk: The ParetoItem from the API has is_planned as a boolean derived from majority-of-minutes logic (from story 14-3). If story 14-3 is not deployed, the is_planned field defaults to false for all items (from daily_summaries fallback), so planned/unplanned distinction will show all bars as unplanned. Mitigation: This is acceptable degradation — the chart still works with all-solid bars. As a secondary check, also match reason_code === 'Planned Maintenance' client-side as a fallback heuristic per story dev notes.
  - Risk: Evidence section is collapsible (isExpanded state). The hook should not make API calls when the section is collapsed and no Pareto data has been fetched yet. Mitigation: Use the existing isExpanded state plus an `enabled` flag on the hook — only fetch when expanded AND evidence type is OEE. Once data is fetched, cache it in hook state so collapsing/re-expanding doesn't re-fetch.
  - Risk: BarChart with layout="vertical" in very small height may truncate labels for 5 reason codes. Mitigation: Truncate reason_code names to 15 chars (same as ParetoChart.tsx line 67-69). Use small font (text-xs / fontSize 11). Render labels outside bars (position="right") showing duration + %. Use dynamic height = Math.max(120, items.length * 28) to ensure adequate space.
  - Risk: SVG hatched pattern for planned bars may not render consistently across browsers. Mitigation: Define the hatch pattern via an inline <svg> <defs><pattern> element within the component. Test in Chrome and Safari. Fallback: use opacity difference (planned bars at 0.5 opacity) if pattern rendering is problematic.
  - Risk: The hook makes an API call per card. If 10 OEE cards render, that's 10 simultaneous Pareto API calls. Mitigation: The backend has 15-minute TTL caching (from story 14-3 design). Additionally, most cards will have different asset_id/date combinations, so caching per key is appropriate. If perf becomes an issue, batch fetching can be added later but is out of scope for this story.
  - Risk: Coordinating with story 14-4 changes to InsightEvidenceCard.tsx and EvidenceSection.tsx. Mitigation: Story 14-4 modified InsightSection.tsx (left side of card, passing trendData) and InsightEvidenceCard.tsx (passing trendData to InsightSection). Story 14-5 modifies EvidenceSection.tsx (right side of card) and InsightEvidenceCard.tsx (passing assetId/reportDate to EvidenceSection). The changes are in different props and different JSX areas — low conflict risk. Check current state of InsightEvidenceCard.tsx before implementing.

estimated_test_files:
  - apps/web/src/hooks/__tests__/useDowntimePareto.test.ts: Tests hook loading state on mount, successful data fetch with correct API URL and Bearer token, error state on network failure, error state on 401 auth failure, empty data handling (items=[]), refetch function triggers new API call, does not fetch when enabled=false, cleanup prevents state updates after unmount
  - apps/web/src/components/action-engine/__tests__/DowntimePareto.test.tsx: Tests chart renders correct number of bars for 3-5 items, each bar displays reason_code name + duration + percentage, planned items render with hatched pattern (data-testid check), unplanned items render solid, returns null when data is null, returns null when items array is empty, skeleton loader renders animate-pulse placeholders with correct dimensions, items are sliced to top 5 if more provided, dark mode classes applied
  - apps/web/src/components/action-engine/__tests__/EvidenceSection.pareto.test.tsx: Tests Pareto chart renders inside OEEEvidenceDisplay when data is available, skeleton shows during loading, no Pareto chart for safety evidence type, no Pareto chart for financial evidence type, assetId and reportDate props are passed to hook

implementation_order:
  1. Create useDowntimePareto hook (apps/web/src/hooks/useDowntimePareto.ts)
     - Define DowntimeParetoItem interface matching ParetoItem from backend (reason_code, total_minutes, percentage, cumulative_percentage, financial_impact, event_count, is_safety_related, is_planned)
     - Define DowntimeParetoResponse interface matching ParetoResponse (items, total_downtime_minutes, total_financial_impact, total_events, data_source, last_updated, threshold_80_index, planned_minutes, unplanned_minutes)
     - Define UseDowntimeParetoOptions: { assetId: string, reportDate: string, enabled?: boolean, apiUrl?: string }
     - Implement hook with useState<DowntimeParetoResponse | null>, isLoading, error states
     - useRef(true) for mountedRef, cleanup on unmount
     - useCallback fetchData: createClient() → getSession() → Bearer token → fetch GET /api/v1/downtime/pareto?date={reportDate}&asset_id={assetId}
     - useEffect triggers fetchData only when enabled !== false
     - Return { data, isLoading, error, refetch }
  2. Create DowntimePareto.tsx component (apps/web/src/components/action-engine/DowntimePareto.tsx)
     - 'use client' directive
     - Import BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip from 'recharts'
     - Import cn from @/lib/utils
     - Import DowntimeParetoResponse type from hook
     - Define DowntimeParetoProps: { data: DowntimeParetoResponse, className?: string }
     - Define compact PARETO_COLORS: { unplanned: 'hsl(210, 50%, 50%)', planned: 'hsl(210, 50%, 70%)', safety: 'hsl(0, 72%, 51%)' }
     - Process data: slice items to top 5, truncate reason_code names to 15 chars
     - Render SVG <defs> with <pattern> for hatched fill (diagonal lines for planned)
     - Render BarChart layout="vertical" with ResponsiveContainer width="100%" height={items.length * 28 + 16}
     - YAxis type="category" dataKey="name" with tick fontSize 11
     - XAxis type="number" hide={true}
     - Bar dataKey="total_minutes" with Cell per item: planned items get hatched pattern fill (url(#hatch)), unplanned get solid fill
     - Custom bar label (position="right"): "{duration}min ({percentage}%)"
     - Simple legend showing solid = unplanned, hatched = planned (inline, 2 small indicators)
     - Return null if data is null/undefined or items.length === 0
     - Export DowntimeParetoSkeleton: animate-pulse div with 3-4 horizontal bar placeholders at staggered widths (w-full, w-3/4, w-1/2, w-1/3) using bg-industrial-200 dark:bg-industrial-700
  3. Modify EvidenceSection.tsx to integrate Pareto chart
     - Add assetId?: string and reportDate?: string to EvidenceSectionProps interface (line 37-41)
     - Import useDowntimePareto from @/hooks/useDowntimePareto
     - Import DowntimePareto, DowntimeParetoSkeleton from ./DowntimePareto
     - Determine if evidence is OEE type: const isOEE = 'targetOEE' in evidence.data && 'actualOEE' in evidence.data
     - Call useDowntimePareto at top level of EvidenceSection (unconditionally to satisfy hooks rules): { data: paretoData, isLoading: paretoLoading } = useDowntimePareto({ assetId: assetId || '', reportDate: reportDate || '', enabled: isOEE && !!assetId && !!reportDate })
     - Inside the expanded content div (line 259, after renderEvidenceContent()), add conditional Pareto section:
       if isOEE: render separator + section header "Downtime Breakdown" + (paretoLoading ? <DowntimeParetoSkeleton /> : paretoData ? <DowntimePareto data={paretoData} /> : null)
  4. Modify InsightEvidenceCard.tsx to pass assetId and reportDate
     - Add assetId={item.asset.id} and reportDate={reportDate} props to <EvidenceSection> JSX (line 108-111)
     - reportDate is already computed at line 56-58
  5. Update barrel exports in index.ts
     - Add: export { DowntimePareto, DowntimeParetoSkeleton } from './DowntimePareto'
  6. Write hook tests (apps/web/src/hooks/__tests__/useDowntimePareto.test.ts)
     - Mock @/lib/supabase/client with vi.mock (same pattern as useActionAcknowledgment.test.ts)
     - Mock global.fetch
     - Test: initial loading state is true, data is null
     - Test: successful fetch sets data, isLoading false, error null
     - Test: fetch sends correct URL with date and asset_id params
     - Test: fetch sends Authorization Bearer header
     - Test: 401 response sets auth error
     - Test: network failure sets error
     - Test: empty items array (valid response) sets data correctly
     - Test: enabled=false prevents fetch, isLoading stays false
     - Test: refetch triggers new API call
     - Test: unmount prevents state updates (mountedRef pattern)
  7. Write component tests (apps/web/src/components/action-engine/__tests__/DowntimePareto.test.tsx)
     - Mock recharts with simple div elements (same pattern as TrendIndicator.test.tsx)
     - Test: renders bars for 3 items
     - Test: renders max 5 bars when given more items
     - Test: each bar label shows duration and percentage
     - Test: planned item bars have hatched pattern identifier
     - Test: unplanned item bars have solid fill
     - Test: returns null for null data
     - Test: returns null for empty items
     - Test: skeleton has animate-pulse class
     - Test: skeleton renders multiple bar placeholders
  8. Write integration tests (apps/web/src/components/action-engine/__tests__/EvidenceSection.pareto.test.tsx)
     - Mock useDowntimePareto hook
     - Mock DowntimePareto and DowntimeParetoSkeleton
     - Test: OEE evidence with assetId and reportDate renders Pareto chart when hook returns data
     - Test: OEE evidence shows skeleton when hook returns isLoading=true
     - Test: Safety evidence does not call hook with enabled=true
     - Test: Financial evidence does not render Pareto chart
     - Test: OEE evidence without assetId does not enable hook
DESIGN END

---

## TEST_SPEC: 14-5-downtime-pareto-chart-on-action-cards
**Timestamp:** 2026-02-11 19:48:56

TEST SPEC START
story_id: 14-5-downtime-pareto-chart-on-action-cards
generated: 2026-02-11

test_specifications:

## AC1: Given an action item is an OEE-miss or downtime-related item, When the action card renders and downtime Pareto data is available, Then a horizontal bar chart shows the top 3-5 reason codes sorted by duration, And each bar shows: reason code name, duration in minutes, percentage of total, And planned vs. unplanned downtime is visually distinguished (e.g., hatched vs. solid bars).

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-001: Hook returns loading state on initial mount
- Priority: P0
- Type: unit
- Given: The `useDowntimePareto` hook is called with valid `assetId` and `reportDate` and `enabled=true`
- When: The hook mounts and the fetch has not yet resolved
- Then: `isLoading` is `true`, `data` is `null`, and `error` is `null`
- Data: assetId = 'asset-001', reportDate = '2026-01-05'

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-002: Hook fetches Pareto data with correct URL and auth header
- Priority: P0
- Type: unit
- Given: Supabase session returns `access_token: 'mock-token-abc'`
- When: The `useDowntimePareto` hook triggers its fetch with `assetId='asset-001'` and `reportDate='2026-01-05'`
- Then: `fetch` is called with URL `{API_BASE_URL}/api/v1/downtime/pareto?asset_id=asset-001&start_date=2026-01-05` and headers include `Authorization: Bearer mock-token-abc` and `Content-Type: application/json`
- Data: Mock Supabase session with access_token, NEXT_PUBLIC_API_URL env var

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-003: Hook sets data on successful API response
- Priority: P0
- Type: unit
- Given: The API returns a valid `ParetoResponse` with 4 items sorted by `total_minutes` descending
- When: The fetch resolves successfully
- Then: `data` contains the parsed response with all 4 `ParetoItem` entries, `isLoading` is `false`, `error` is `null`
- Data: ParetoResponse with items: [{ reason_code: 'Mechanical', total_minutes: 180, percentage: 35.5, is_planned: false }, { reason_code: 'Changeover', total_minutes: 120, percentage: 23.6, is_planned: false }, { reason_code: 'Planned Maintenance', total_minutes: 90, percentage: 17.7, is_planned: true }, { reason_code: 'Material Shortage', total_minutes: 60, percentage: 11.8, is_planned: false }]

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-004: Hook handles network error gracefully
- Priority: P0
- Type: unit
- Given: The `useDowntimePareto` hook is called with valid params
- When: The fetch rejects with a network error
- Then: `error` is set to a descriptive error message, `data` is `null`, `isLoading` is `false`
- Data: `fetch` rejects with `Error('Network request failed')`

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-005: Hook handles 401 auth error
- Priority: P1
- Type: unit
- Given: The Supabase session is valid but the API returns HTTP 401
- When: The fetch resolves with status 401
- Then: `error` is set to an authentication error message, `data` is `null`, `isLoading` is `false`
- Data: Mock fetch returns `{ ok: false, status: 401 }`

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-006: Hook handles empty items array
- Priority: P1
- Type: unit
- Given: The API returns a valid `ParetoResponse` with `items: []` and `total_downtime_minutes: 0`
- When: The fetch resolves successfully
- Then: `data` is set with the empty response, `data.items` has length 0, `isLoading` is `false`, `error` is `null`
- Data: ParetoResponse with items: [], total_downtime_minutes: 0

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-007: Hook does not fetch when enabled is false
- Priority: P0
- Type: unit
- Given: The `useDowntimePareto` hook is called with `enabled=false`
- When: The hook mounts
- Then: `fetch` is never called, `isLoading` is `false`, `data` is `null`
- Data: assetId = 'asset-001', reportDate = '2026-01-05', enabled = false

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-008: Hook refetch triggers a new API call
- Priority: P1
- Type: unit
- Given: The hook has completed its initial fetch and returned data
- When: `refetch()` is called
- Then: `isLoading` momentarily becomes `true`, a new fetch is made to the same URL, and `data` is updated with the new response
- Data: Two sequential mock responses with different `last_updated` values

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-009: Hook prevents state updates after unmount
- Priority: P1
- Type: unit
- Given: The hook is called and a fetch is in progress
- When: The component unmounts before the fetch resolves
- Then: No state update occurs (no React warnings), the mountedRef pattern prevents `setState` calls
- Data: Slow-resolving fetch mock with component unmount before resolution

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-010: Hook handles missing Supabase session
- Priority: P1
- Type: unit
- Given: Supabase `getSession` returns `{ data: { session: null } }`
- When: The hook attempts to fetch
- Then: `error` is set to an authentication error, `fetch` is not called with a Bearer token, `isLoading` is `false`
- Data: Mock getSession returning null session

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-011: Component renders horizontal bars for 3-5 reason codes sorted by duration
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with 4 items sorted by `total_minutes` descending
- When: The component renders
- Then: A Recharts `BarChart` with `layout="vertical"` renders inside a `ResponsiveContainer`, and 4 bars are displayed corresponding to the 4 reason codes
- Data: 4 ParetoItems: Mechanical (180min, 35.5%), Changeover (120min, 23.6%), Planned Maintenance (90min, 17.7%), Material Shortage (60min, 11.8%)

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-012: Each bar shows reason code name, duration in minutes, and percentage of total
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with items containing reason_code, total_minutes, and percentage
- When: The component renders
- Then: Each bar's label area contains the reason code name, duration formatted as `{N}min`, and percentage formatted as `({N}%)`
- Data: ParetoItem with reason_code='Mechanical', total_minutes=180, percentage=35.5 → label shows "Mechanical", "180min", "(35.5%)"

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-013: Planned downtime bars are visually distinguished with hatched pattern
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives data with items where `is_planned=true` (e.g., 'Planned Maintenance')
- When: The component renders
- Then: Bars for planned items use a hatched/striped SVG pattern fill (identifiable via `data-testid` or fill URL referencing a pattern definition), while unplanned items use solid fill
- Data: Mix of planned (is_planned=true) and unplanned (is_planned=false) ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-014: Unplanned downtime bars render with solid fill
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives data with unplanned items (`is_planned=false`)
- When: The component renders
- Then: Unplanned bars use a solid color fill (not hatched pattern), using the Industrial Clarity color palette
- Data: ParetoItems with is_planned=false

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-015: Component limits display to top 5 reason codes when more are provided
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with 8 items
- When: The component renders
- Then: Only the top 5 items (by total_minutes descending) are displayed as bars
- Data: 8 ParetoItems with varying total_minutes

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-016: Component returns null when data is null
- Priority: P0
- Type: unit
- Given: `DowntimePareto` receives `data` as `null`
- When: The component renders
- Then: Nothing is rendered (returns null), no chart elements appear in the DOM
- Data: data = null

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-017: Component returns null when items array is empty
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives a `ParetoResponse` with `items: []`
- When: The component renders
- Then: Nothing is rendered (returns null), no chart or empty state message appears
- Data: ParetoResponse with items: []

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-018: Component truncates long reason code names
- Priority: P2
- Type: unit
- Given: `DowntimePareto` receives items with a reason_code exceeding 15 characters (e.g., 'Electrical System Overload')
- When: The component renders
- Then: The displayed reason code name is truncated to 15 characters (e.g., 'Electrical Syst…')
- Data: ParetoItem with reason_code='Electrical System Overload' (26 chars)

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-019: Component uses compact height appropriate for inline rendering
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives data with 3-5 items
- When: The component renders
- Then: The `ResponsiveContainer` height is between 100-150px (compact, sparkline-sized), appropriate for embedding inside an evidence card without its own Card wrapper
- Data: 3-5 ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-020: Component supports dark mode via Tailwind dark: variants
- Priority: P2
- Type: unit
- Given: `DowntimePareto` renders in a dark mode context
- When: The component renders
- Then: Dark mode CSS classes (e.g., `dark:` prefixed Tailwind classes) are applied to text labels, background, and legend elements
- Data: Standard ParetoResponse data

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-021: Planned vs unplanned legend is rendered
- Priority: P1
- Type: unit
- Given: `DowntimePareto` receives data containing both planned and unplanned items
- When: The component renders
- Then: A compact inline legend is displayed showing the solid fill = unplanned and hatched fill = planned distinction
- Data: Mix of planned and unplanned ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-INT-001: EvidenceSection renders Pareto chart for OEE evidence with available data
- Priority: P0
- Type: integration
- Given: `EvidenceSection` receives evidence with `type='oee_deviation'`, `assetId='asset-001'`, `reportDate='2026-01-05'`, and `useDowntimePareto` returns Pareto data with 4 items
- When: The evidence section is expanded
- Then: The `DowntimePareto` chart component is rendered below the OEE evidence content, showing a "Downtime Breakdown" section header and the horizontal bar chart
- Data: OEEEvidence with targetOEE=85, actualOEE=72, deviation=13; ParetoResponse with 4 items

### 14-5-downtime-pareto-chart-on-action-cards-INT-002: InsightEvidenceCard passes assetId and reportDate to EvidenceSection
- Priority: P0
- Type: integration
- Given: An `InsightEvidenceCard` renders with an `ActionItem` that has `asset.id='asset-001'` and `timestamp='2026-01-05T14:30:00Z'`
- When: The card renders
- Then: `EvidenceSection` receives `assetId='asset-001'` and `reportDate='2026-01-05'` as props
- Data: ActionItem with asset.id and timestamp fields populated

### 14-5-downtime-pareto-chart-on-action-cards-INT-003: Pareto hook receives correct parameters from EvidenceSection
- Priority: P0
- Type: integration
- Given: `EvidenceSection` has `assetId='asset-001'`, `reportDate='2026-01-05'`, and evidence type is `'oee_deviation'`
- When: The component mounts
- Then: `useDowntimePareto` is called with `{ assetId: 'asset-001', reportDate: '2026-01-05', enabled: true }`
- Data: OEE evidence with asset and date props

## AC2: Given an action item is a safety-only or financial-only item (no downtime component), When the card renders, Then no Pareto chart is shown.

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-022: No Pareto chart rendered for safety evidence type
- Priority: P0
- Type: unit
- Given: `EvidenceSection` receives evidence with `type='safety_event'`, with `assetId` and `reportDate` props provided
- When: The component renders and the evidence section is expanded
- Then: No `DowntimePareto` component is rendered, no "Downtime Breakdown" section header appears, and `useDowntimePareto` is called with `enabled=false`
- Data: SafetyEvidence with eventId, detectedAt, reasonCode, severity, assetName fields

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-023: No Pareto chart rendered for financial evidence type
- Priority: P0
- Type: unit
- Given: `EvidenceSection` receives evidence with `type='financial_loss'`, with `assetId` and `reportDate` props provided
- When: The component renders and the evidence section is expanded
- Then: No `DowntimePareto` component is rendered, no "Downtime Breakdown" section header appears, and `useDowntimePareto` is called with `enabled=false`
- Data: FinancialEvidence with downtimeCost, wasteCost, totalLoss, breakdown fields

### 14-5-downtime-pareto-chart-on-action-cards-INT-004: Hook not enabled when assetId is missing
- Priority: P1
- Type: integration
- Given: `EvidenceSection` receives OEE evidence but `assetId` prop is `undefined`
- When: The component renders
- Then: `useDowntimePareto` is called with `enabled=false`, no API call is made, no Pareto chart is rendered
- Data: OEE evidence without assetId prop

### 14-5-downtime-pareto-chart-on-action-cards-INT-005: Hook not enabled when reportDate is missing
- Priority: P1
- Type: integration
- Given: `EvidenceSection` receives OEE evidence but `reportDate` prop is `undefined`
- When: The component renders
- Then: `useDowntimePareto` is called with `enabled=false`, no API call is made, no Pareto chart is rendered
- Data: OEE evidence without reportDate prop

## AC3: Given the Pareto data is loading, When the card renders, Then a skeleton loader placeholder is shown where the chart would be.

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-024: Skeleton loader renders with animate-pulse during loading
- Priority: P0
- Type: unit
- Given: `DowntimeParetoSkeleton` is rendered
- When: The component mounts
- Then: A container with `animate-pulse` class is rendered containing 3-4 horizontal bar placeholders at staggered widths, using `bg-industrial-200 dark:bg-industrial-700` classes
- Data: No data props required for skeleton

### 14-5-downtime-pareto-chart-on-action-cards-UNIT-025: Skeleton loader matches chart dimensions
- Priority: P1
- Type: unit
- Given: `DowntimeParetoSkeleton` is rendered
- When: The component mounts
- Then: The skeleton placeholders are horizontal bars at varying widths (e.g., w-full, w-3/4, w-1/2, w-1/3) matching the expected chart layout, at approximately 120-150px total height
- Data: No data props required

### 14-5-downtime-pareto-chart-on-action-cards-INT-006: EvidenceSection shows skeleton while Pareto data is loading
- Priority: P0
- Type: integration
- Given: `EvidenceSection` receives OEE evidence with `assetId` and `reportDate`, and `useDowntimePareto` returns `{ isLoading: true, data: null, error: null }`
- When: The evidence section is expanded
- Then: `DowntimeParetoSkeleton` is rendered in place of the chart, below the OEE evidence content
- Data: OEE evidence; hook in loading state

### 14-5-downtime-pareto-chart-on-action-cards-INT-007: Skeleton transitions to chart when data loads
- Priority: P1
- Type: integration
- Given: `EvidenceSection` initially shows the skeleton while `useDowntimePareto` is loading
- When: The hook resolves with Pareto data
- Then: The skeleton is replaced by the `DowntimePareto` chart component showing the loaded data
- Data: OEE evidence; hook transitions from loading to loaded with 4 ParetoItems

### 14-5-downtime-pareto-chart-on-action-cards-INT-008: No chart or skeleton shown when hook returns error
- Priority: P1
- Type: integration
- Given: `EvidenceSection` receives OEE evidence and `useDowntimePareto` returns `{ isLoading: false, data: null, error: 'Network error' }`
- When: The evidence section is expanded
- Then: Neither `DowntimePareto` chart nor `DowntimeParetoSkeleton` is rendered; the OEE evidence content still displays normally without a Pareto section
- Data: OEE evidence; hook in error state

edge_cases:
  - Single reason code: ParetoResponse with only 1 item should still render a single horizontal bar correctly
  - All planned downtime: Every item has is_planned=true — all bars should show hatched pattern, legend should still display
  - All unplanned downtime: Every item has is_planned=false — all bars should show solid fill
  - Reason code with 0 minutes: A ParetoItem with total_minutes=0 and percentage=0 should render a zero-width bar or be excluded
  - Very large duration values: ParetoItem with total_minutes=9999 should not break chart layout
  - 100% single reason code: One item with percentage=100.0 and all others at 0%
  - Fallback planned detection: When is_planned field is absent or false for all items, check reason_code === 'Planned Maintenance' as fallback heuristic
  - Rapid expand/collapse of evidence section: Hook should not make redundant API calls when cached data exists
  - Multiple OEE cards rendering simultaneously: Each card's hook makes its own API call with its own assetId/date combination

error_scenarios:
  - API returns HTTP 500 server error: Hook sets error state, no chart rendered
  - API returns HTTP 401 unauthorized: Hook sets auth error, no chart rendered
  - API returns malformed JSON: Hook catches parse error, sets error state
  - Network timeout: Hook catches timeout error, sets error state
  - Supabase session expired: getSession returns null, hook sets auth error without calling fetch
  - API returns 200 but with unexpected schema: Hook handles missing fields gracefully
  - Component unmounts during active fetch: No React state update warnings (mountedRef pattern)

test_file_mapping:
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-001 to UNIT-010: apps/web/src/hooks/__tests__/useDowntimePareto.test.ts
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-011 to UNIT-021: apps/web/src/components/action-engine/__tests__/DowntimePareto.test.tsx
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-022 to UNIT-023: apps/web/src/components/action-engine/__tests__/EvidenceSection.pareto.test.tsx
  - 14-5-downtime-pareto-chart-on-action-cards-UNIT-024 to UNIT-025: apps/web/src/components/action-engine/__tests__/DowntimePareto.test.tsx
  - 14-5-downtime-pareto-chart-on-action-cards-INT-001 to INT-008: apps/web/src/components/action-engine/__tests__/EvidenceSection.pareto.test.tsx

TEST SPEC END

---

## DESIGN: 14-6-ai-summary-with-trend-context
**Timestamp:** 2026-02-11 20:28:23

DESIGN START
story_id: 14-6-ai-summary-with-trend-context

files_to_modify:
  - path: apps/api/app/services/ai/context_builder.py
    action: modify
    purpose: Add trend_data, repeat_offenders, top_downtime_drivers Optional fields to SummaryContext; add fetch_trend_data(), fetch_repeat_offenders(), fetch_top_downtime_drivers() methods; integrate into build_context() with try/except isolation
  - path: apps/api/app/services/ai/prompts.py
    action: modify
    purpose: Add format_trend_context() function; add TREND CONTEXT section to DATA_TEMPLATE_DEFAULT; update render_data_prompt() to accept and format trend context; update SYSTEM_PROMPT_DEFAULT to instruct LLM to incorporate trend narrative
  - path: apps/api/app/services/ai/smart_summary.py
    action: modify
    purpose: Update _generate_with_llm() to pass trend fields to render_data_prompt(); update generate_fallback_summary() with week-over-week OEE line, Recurring Issues section, and Downtime Drivers section
  - path: apps/api/tests/test_smart_summary.py
    action: modify
    purpose: Add tests for trend context in context building, prompt formatting, fallback summary with trends, and fallback without trends; update sample_context fixture to optionally include trend fields

patterns_to_use:
  - SummaryContext Optional fields with defaults: New fields use Optional[Dict] = Field(default=None) and List[Dict] = Field(default_factory=list) — matching existing pattern of safety_events/cost_centers fields at lines 36-51 of context_builder.py. Existing code constructing SummaryContext without these fields is unaffected.
  - try/except error isolation in fetch methods: Each new fetch_* method wraps body in try/except returning empty/None on failure with logger.error — identical to fetch_daily_summaries() (lines 148-164), fetch_safety_events() (lines 178-204), fetch_cost_centers() (lines 216-233).
  - Supabase self._get_client() pattern: Reuse existing lazy client getter at line 118 for all new DB queries — no new client instances.
  - render_data_prompt signature extension: Add keyword arguments with defaults (trend_data=None, repeat_offenders=None, top_downtime_drivers=None) — backward compatible with all existing callers that don't pass these args.
  - format_* function pattern: New format_trend_context() follows format_safety_events(), format_oee_data(), format_financial_data() pattern — accepts data, returns formatted string, handles empty/None input gracefully.
  - DATA_TEMPLATE_DEFAULT section pattern: Add `=== TREND CONTEXT ===\n{trend_context}` after the ACTION ENGINE section — identical structure to existing sections.
  - Fallback summary section pattern: New sections follow the **Safety**, **Productivity**, **Financial Impact** pattern with conditional rendering via if-guard and lines.append().
  - pytest class-based test organization: Follow TestContextBuilder, TestPromptTemplates, TestSmartSummaryGeneration class pattern from test_smart_summary.py.
  - MagicMock Supabase chaining: Use mock_supabase_client.table.return_value.select.return_value.in_.return_value.gte.return_value.lte.return_value.execute.return_value pattern for mocking DB responses.

dependencies:
  - pydantic: installed (used for SummaryContext BaseModel)
  - supabase-py: installed (used for DB queries)
  - pytest: installed (test framework)
  - pytest-asyncio: installed (async test support)

acceptance_criteria_mapping:
  - AC1 (Summary includes week-over-week OEE comparison like "Overall plant OEE 81.2%, down 3.1 points from last week"):
    - context_builder.py: New `trend_data` field on SummaryContext (Optional[Dict[str, Any]]) with shape {plant_oee_current, plant_oee_previous_week, plant_oee_wow_change}; new `fetch_trend_data(target_date)` method queries daily_summaries for target_date and target_date - 7 days, computes plant-wide average OEE for each, returns diff
    - prompts.py: `format_trend_context()` renders "Week-over-Week OEE: Current {X}% vs Last Week {Y}% (change: {Z} points)" line; added to DATA_TEMPLATE_DEFAULT as `=== TREND CONTEXT ===` section
    - prompts.py: `render_data_prompt()` gains `trend_data` kwarg, passes to format_trend_context()
    - prompts.py: SYSTEM_PROMPT_DEFAULT updated to instruct LLM to "incorporate week-over-week trends and repeat offender patterns when trend data is provided"
    - smart_summary.py: `_generate_with_llm()` passes context.trend_data, context.repeat_offenders, context.top_downtime_drivers to render_data_prompt()
  - AC2 (Summary mentions 3+ consecutive day repeat offenders):
    - context_builder.py: New `repeat_offenders` field on SummaryContext (List[Dict[str, Any]]) with shape [{asset_name, consecutive_days, category}]; new `fetch_repeat_offenders(target_date)` method queries daily_summaries for trailing 7 days, identifies assets with OEE below target for 3+ consecutive days ending on target_date
    - prompts.py: `format_trend_context()` renders "Repeat Offenders (3+ consecutive days on report):" section listing each asset with consecutive count
    - smart_summary.py: data flows through _generate_with_llm → render_data_prompt → LLM prompt
  - AC3 (Summary includes top downtime driver):
    - context_builder.py: New `top_downtime_drivers` field on SummaryContext (List[Dict[str, Any]]) with shape [{reason_code, total_minutes, asset_count}]; new `fetch_top_downtime_drivers(target_date)` method queries downtime_events table for target_date, aggregates by reason_code with SUM(duration_minutes) and COUNT(DISTINCT asset_id), returns top 3
    - prompts.py: `format_trend_context()` renders "Top Downtime Drivers (yesterday):" section listing each reason code with total minutes and asset count
    - smart_summary.py: data flows through _generate_with_llm → render_data_prompt → LLM prompt
  - AC4 (Graceful omission when trend data unavailable):
    - context_builder.py: All three fetch methods wrapped in try/except returning None/empty list on failure; build_context() calls each method independently with error isolation
    - prompts.py: format_trend_context() returns "No trend data available." or "" when all three inputs are None/empty; DATA_TEMPLATE_DEFAULT renders the section regardless but with benign content
    - smart_summary.py: render_data_prompt() gracefully passes None/empty to format_trend_context() — no crash path
  - AC5 (Fallback summary includes trend lines):
    - smart_summary.py: generate_fallback_summary() enhanced with three new conditional blocks: (1) after opening paragraph — if context.trend_data exists, add "Overall plant OEE {X}%, {up/down} {Y} points from last week" line; (2) new **Recurring Issues** section — if context.repeat_offenders is non-empty, list each repeat offender; (3) new **Downtime Drivers** section — if context.top_downtime_drivers is non-empty, list top drivers. Each guarded with if-check so missing data is silently skipped.

risks:
  - Risk: The downtime_events table may not exist if story 14-1 migration hasn't run. Mitigation: fetch_top_downtime_drivers() wraps its query in try/except and returns empty list on any exception (including table-not-found errors). The feature gracefully degrades — AC#4 ensures this is the expected behavior.
  - Risk: Changing render_data_prompt() signature could break existing callers. Mitigation: All new parameters have default values (None, None, None). The existing call in _generate_with_llm() is the only caller and will be updated. The test at test_smart_summary.py:325 calls render_data_prompt with positional/keyword args and will still work since all new params are keyword-only with defaults.
  - Risk: DATA_TEMPLATE_DEFAULT change adds a new {trend_context} placeholder. If the env var SMART_SUMMARY_DATA_TEMPLATE is set by a user to an older template without this placeholder, format() will fail. Mitigation: render_data_prompt() will catch KeyError from format() and fall back to inserting trend_context as an appended section. However, this is unlikely in practice since the env override is not documented for production use.
  - Risk: Plant-wide average OEE calculation may differ from individual asset OEE in the action engine (story 14.2). Mitigation: The ContextBuilder's fetch_trend_data() computes a simple arithmetic mean across all assets for both the current date and 7 days prior — this is explicitly a plant-level aggregate, not per-asset.
  - Risk: fetch_repeat_offenders() logic must identify assets below OEE target for 3+ consecutive days, which requires querying 7 days of daily_summaries. This overlaps conceptually with ActionEngine._calculate_consecutive_days(). Mitigation: Per story dev notes, prefer direct Supabase queries in ContextBuilder to avoid coupling to ActionEngine internals. The query is straightforward: get all daily_summaries for trailing 7 days, group by asset, check consecutive day sequences.
  - Risk: Existing test test_fallback_includes_safety_events checks for "Safety Events" and "AI summary unavailable" in fallback text, but the actual fallback uses "**Safety**" format. Adding new sections must not break these assertions. Mitigation: New sections are appended in specific locations (after opening paragraph, before Productivity, after Productivity) and do not alter existing section content. Tests will be verified and updated if needed.

estimated_test_files:
  - apps/api/tests/test_smart_summary.py: Add TestTrendContextBuilder class (test_fetch_trend_data_with_history, test_fetch_trend_data_no_history, test_fetch_repeat_offenders_found, test_fetch_repeat_offenders_none, test_fetch_top_downtime_drivers, test_fetch_top_downtime_drivers_table_missing, test_build_context_includes_trend_fields, test_build_context_trend_failure_isolated); Add TestTrendPromptFormatting class (test_format_trend_context_all_data, test_format_trend_context_partial_data, test_format_trend_context_no_data, test_render_data_prompt_includes_trend_section); Add TestFallbackWithTrends class (test_fallback_with_wow_oee, test_fallback_with_repeat_offenders, test_fallback_with_downtime_drivers, test_fallback_without_trends_unchanged)

implementation_order:
  1. Extend SummaryContext in context_builder.py with three new Optional fields
     - Add `trend_data: Optional[Dict[str, Any]] = Field(default=None, description="Plant-level week-over-week trend data")` after line 55 (target_oee field)
     - Add `repeat_offenders: List[Dict[str, Any]] = Field(default_factory=list, description="Assets appearing on report 3+ consecutive days")`
     - Add `top_downtime_drivers: List[Dict[str, Any]] = Field(default_factory=list, description="Top downtime reason codes aggregated across plant")`
     - Verify has_data property is unaffected (these are supplementary, not core data)
  2. Add fetch_trend_data() method to ContextBuilder class
     - Signature: `async def fetch_trend_data(self, target_date: date_type) -> Optional[Dict[str, Any]]`
     - Query daily_summaries for target_date: SELECT oee_percentage WHERE report_date = target_date
     - Query daily_summaries for target_date - 7: SELECT oee_percentage WHERE report_date = target_date - 7
     - Compute plant-wide average OEE for both dates (arithmetic mean of all assets)
     - Return {"plant_oee_current": avg_current, "plant_oee_previous_week": avg_previous, "plant_oee_wow_change": avg_current - avg_previous}
     - Return None if no data for either date
     - Wrap in try/except → return None on failure
  3. Add fetch_repeat_offenders() method to ContextBuilder class
     - Signature: `async def fetch_repeat_offenders(self, target_date: date_type) -> List[Dict[str, Any]]`
     - Query daily_summaries for target_date - 6 through target_date (7 days), selecting asset_id, report_date, oee_percentage
     - Get target_oee from settings
     - For each asset, find the longest run of consecutive days (ending on target_date) where oee_percentage < target_oee
     - Filter to assets with consecutive_days >= 3
     - Enrich with asset names from self.fetch_assets() (or self._last_assets if already fetched in build_context)
     - Return list of {"asset_name": name, "consecutive_days": N, "category": "oee"}
     - Wrap in try/except → return [] on failure
  4. Add fetch_top_downtime_drivers() method to ContextBuilder class
     - Signature: `async def fetch_top_downtime_drivers(self, target_date: date_type) -> List[Dict[str, Any]]`
     - Query downtime_events for target_date: SELECT reason_code, duration_minutes, asset_id WHERE event_date = target_date
     - Aggregate in Python: group by reason_code, SUM duration_minutes, COUNT DISTINCT asset_id
     - Sort descending by total_minutes, return top 3
     - Return list of {"reason_code": code, "total_minutes": N, "asset_count": M}
     - Wrap in try/except → return [] on failure (handles missing downtime_events table)
  5. Integrate fetch methods into build_context()
     - After existing fetches (line 360, after action_items), add three calls:
       - trend_data = await self.fetch_trend_data(target_date)
       - repeat_offenders = await self.fetch_repeat_offenders(target_date) — pass assets dict for enrichment
       - top_downtime_drivers = await self.fetch_top_downtime_drivers(target_date)
     - Each in its own try/except block so failures are isolated
     - Pass all three to SummaryContext constructor (lines 374-382)
  6. Add format_trend_context() function to prompts.py
     - Signature: `def format_trend_context(trend_data: Optional[Dict] = None, repeat_offenders: Optional[List[Dict]] = None, top_downtime_drivers: Optional[List[Dict]] = None) -> str`
     - Build lines list:
       - If trend_data: "Week-over-Week OEE: Current {X:.1f}% vs Last Week {Y:.1f}% (change: {Z:+.1f} points)"
       - If repeat_offenders: "\nRepeat Offenders (3+ consecutive days on report):" + bullet for each
       - If top_downtime_drivers: "\nTop Downtime Drivers (yesterday):" + bullet for each
     - If all empty: return "No trend data available for this period."
  7. Update DATA_TEMPLATE_DEFAULT in prompts.py
     - Add after the ACTION ENGINE PRIORITIES section (before the final instruction paragraph):
       `\n=== TREND CONTEXT ===\n{trend_context}\n`
  8. Update SYSTEM_PROMPT_DEFAULT in prompts.py
     - Add to the CRITICAL REQUIREMENTS list: "7. When trend context is provided, incorporate week-over-week comparisons, highlight repeat offenders (3+ consecutive days), and mention top downtime drivers in your analysis"
  9. Update render_data_prompt() in prompts.py
     - Add keyword parameters: `trend_data: Optional[Dict[str, Any]] = None, repeat_offenders: Optional[List[Dict[str, Any]]] = None, top_downtime_drivers: Optional[List[Dict[str, Any]]] = None`
     - Add `trend_context=format_trend_context(trend_data, repeat_offenders, top_downtime_drivers)` to the template.format() call
  10. Update _generate_with_llm() in smart_summary.py
      - Update the render_data_prompt() call (lines 413-420) to pass three new kwargs from context:
        `trend_data=context.trend_data, repeat_offenders=context.repeat_offenders, top_downtime_drivers=context.top_downtime_drivers`
  11. Update generate_fallback_summary() in smart_summary.py
      - After opening paragraph (after line 286 `lines.append("")`): insert week-over-week OEE comparison if context.trend_data exists
        `if context.trend_data: wow_change = context.trend_data["plant_oee_wow_change"]; direction = "up" if wow_change >= 0 else "down"; lines.insert(-1, f"Overall plant OEE {context.trend_data['plant_oee_current']:.1f}%, {direction} {abs(wow_change):.1f} points from last week.")`
      - After Safety section, before Productivity section: insert **Recurring Issues** section if context.repeat_offenders is non-empty
        ```
        if context.repeat_offenders:
            lines.append("**Recurring Issues**")
            for offender in context.repeat_offenders:
                lines.append(f"- {offender['asset_name']} — {offender['consecutive_days']} consecutive days on report, consider escalating to maintenance planning")
            lines.append("")
        ```
      - After Productivity section, before Financial Impact section: insert **Downtime Drivers** section if context.top_downtime_drivers is non-empty
        ```
        if context.top_downtime_drivers:
            lines.append("**Downtime Drivers**")
            for driver in context.top_downtime_drivers:
                lines.append(f"- {driver['reason_code']}: {driver['total_minutes']} min across {driver['asset_count']} assets")
            lines.append("")
        ```
  12. Write unit tests: TestTrendContextBuilder
      - test_fetch_trend_data_with_history: Mock daily_summaries for two dates, verify plant_oee_current, plant_oee_previous_week, plant_oee_wow_change
      - test_fetch_trend_data_no_history: Mock empty daily_summaries, verify returns None
      - test_fetch_repeat_offenders_found: Mock 7 days of daily_summaries with an asset below target 4 consecutive days, verify it appears with consecutive_days=4
      - test_fetch_repeat_offenders_none: Mock data where no asset has 3+ consecutive below-target days, verify empty list
      - test_fetch_top_downtime_drivers: Mock downtime_events rows, verify aggregation (reason_code, total_minutes, asset_count) sorted descending
      - test_fetch_top_downtime_drivers_table_missing: Mock Supabase exception, verify returns empty list
      - test_build_context_includes_trend_fields: Mock all fetches, verify SummaryContext has trend_data, repeat_offenders, top_downtime_drivers populated
      - test_build_context_trend_failure_isolated: Mock trend fetches to raise exceptions, verify build_context still returns a valid SummaryContext with None/empty trend fields
  13. Write unit tests: TestTrendPromptFormatting
      - test_format_trend_context_all_data: Pass all three data types, verify output contains WoW OEE, repeat offenders, downtime drivers
      - test_format_trend_context_partial_data: Pass only trend_data (no repeat/downtime), verify only WoW section rendered
      - test_format_trend_context_no_data: Pass None/empty for all, verify "No trend data" message
      - test_render_data_prompt_includes_trend_section: Call render_data_prompt with trend args, verify "TREND CONTEXT" in output
  14. Write unit tests: TestFallbackWithTrends
      - test_fallback_with_wow_oee: Create SummaryContext with trend_data, generate fallback, verify "Overall plant OEE" and "points from last week" in text
      - test_fallback_with_repeat_offenders: Create SummaryContext with repeat_offenders, generate fallback, verify "Recurring Issues" section and asset name in text
      - test_fallback_with_downtime_drivers: Create SummaryContext with top_downtime_drivers, generate fallback, verify "Downtime Drivers" section
      - test_fallback_without_trends_unchanged: Create SummaryContext with no trend fields, generate fallback, verify output matches pre-14.6 format (no trend sections, no errors)
  15. Write integration test: test_smart_summary_includes_trend_narrative
      - Mock context builder to return SummaryContext with all trend data populated
      - Mock LLM to return a response containing "down 3.1 points" and "consecutive days"
      - Verify the generated SmartSummary.summary_text contains the trend narrative
      - Verify the prompt sent to the LLM included the TREND CONTEXT section
DESIGN END

---

## TEST_SPEC: 14-6-ai-summary-with-trend-context
**Timestamp:** 2026-02-11 20:32:10

TEST SPEC START
story_id: 14-6-ai-summary-with-trend-context
generated: 2026-02-11

test_specifications:

## AC1: Given the smart summary is generated for a date When trend data is available for the plant Then the summary includes a line like: "Overall plant OEE 81.2%, down 3.1 points from last week"

### 14-6-ai-summary-with-trend-context-UNIT-001: fetch_trend_data returns WoW OEE change when 7-day history exists
- Priority: P0
- Type: unit
- Given: daily_summaries table contains OEE data for target_date (2026-02-10) with 3 assets averaging 81.2% OEE, and for target_date - 7 (2026-02-03) with 3 assets averaging 84.3% OEE
- When: fetch_trend_data(target_date=date(2026, 2, 10)) is called on ContextBuilder
- Then: returns {"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}
- Data: Mock Supabase query for daily_summaries with report_date = 2026-02-10 returning [{"oee_percentage": 78.0}, {"oee_percentage": 82.6}, {"oee_percentage": 83.0}]; report_date = 2026-02-03 returning [{"oee_percentage": 84.0}, {"oee_percentage": 85.0}, {"oee_percentage": 83.9}]

### 14-6-ai-summary-with-trend-context-UNIT-002: SummaryContext trend_data field is Optional with None default
- Priority: P0
- Type: unit
- Given: SummaryContext is constructed with only existing required fields (target_date, daily_summaries)
- When: SummaryContext is instantiated without passing trend_data
- Then: context.trend_data is None, and context.has_data still returns True if daily_summaries is non-empty
- Data: Minimal SummaryContext with target_date=date(2026, 2, 10), daily_summaries=[{"oee_percentage": 80.0}]

### 14-6-ai-summary-with-trend-context-UNIT-003: build_context populates trend_data when historical data is available
- Priority: P0
- Type: unit
- Given: Supabase daily_summaries has data for both target_date and target_date - 7 days
- When: build_context(target_date=date(2026, 2, 10)) is called
- Then: the returned SummaryContext has trend_data populated with plant_oee_current, plant_oee_previous_week, and plant_oee_wow_change
- Data: Mock daily_summaries returning OEE records for both 2026-02-10 and 2026-02-03

### 14-6-ai-summary-with-trend-context-UNIT-004: format_trend_context renders WoW OEE comparison line
- Priority: P0
- Type: unit
- Given: trend_data = {"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}
- When: format_trend_context(trend_data=trend_data) is called
- Then: output contains "Week-over-Week OEE: Current 81.2% vs Last Week 84.3% (change: -3.1 points)"
- Data: trend_data dict as specified

### 14-6-ai-summary-with-trend-context-UNIT-005: render_data_prompt includes TREND CONTEXT section when trend data provided
- Priority: P0
- Type: unit
- Given: render_data_prompt is called with valid trend_data kwarg
- When: render_data_prompt(target_date=..., safety_events=[], daily_summaries=[], action_items=[], trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1})
- Then: the returned prompt string contains "TREND CONTEXT" section header AND the WoW OEE comparison text
- Data: Standard render_data_prompt args plus trend_data

### 14-6-ai-summary-with-trend-context-UNIT-006: _generate_with_llm passes trend_data from context to render_data_prompt
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}
- When: _generate_with_llm(context) is called with a mocked LLM client
- Then: render_data_prompt is called with trend_data kwarg matching context.trend_data
- Data: Mock LLM returning a valid response string; patch render_data_prompt to capture call args

### 14-6-ai-summary-with-trend-context-INT-001: End-to-end summary generation includes WoW OEE comparison in LLM prompt
- Priority: P0
- Type: integration
- Given: Supabase returns 7-day history of daily_summaries with OEE data, and LLM is mocked to echo back received data
- When: generate_smart_summary(target_date=date(2026, 2, 10)) is called
- Then: the prompt sent to the LLM contains "Week-over-Week OEE" and "change:" text, and the generated summary_text is non-empty
- Data: Full mock chain: Supabase daily_summaries for target_date and target_date - 7; mock LLM returning summary text containing "down 3.1 points from last week"

### 14-6-ai-summary-with-trend-context-UNIT-007: format_trend_context handles positive WoW change correctly
- Priority: P1
- Type: unit
- Given: trend_data = {"plant_oee_current": 87.5, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": 3.2}
- When: format_trend_context(trend_data=trend_data) is called
- Then: output contains "change: +3.2 points" (with plus sign for positive change)
- Data: Positive WoW change trend_data dict

### 14-6-ai-summary-with-trend-context-UNIT-008: fetch_trend_data computes correct plant-wide average across multiple assets
- Priority: P1
- Type: unit
- Given: daily_summaries for target_date has 5 assets with OEE values [72.0, 80.0, 85.0, 90.0, 78.0] (avg 81.0), and target_date - 7 has 5 assets with [75.0, 82.0, 88.0, 92.0, 80.0] (avg 83.4)
- When: fetch_trend_data(target_date) is called
- Then: returns plant_oee_current=81.0, plant_oee_previous_week=83.4, plant_oee_wow_change=-2.4
- Data: Mock Supabase returning 5 asset records for each date

### 14-6-ai-summary-with-trend-context-UNIT-009: SYSTEM_PROMPT_DEFAULT includes trend context instructions
- Priority: P1
- Type: unit
- Given: SYSTEM_PROMPT_DEFAULT is loaded (or get_system_prompt() called)
- When: the prompt text is inspected
- Then: it contains instructions to incorporate week-over-week trends, repeat offenders, and downtime drivers when available
- Data: None (static prompt inspection)


## AC2: Given an asset has been on the report for 3+ consecutive days When the smart summary is generated Then the summary mentions the pattern: "Grinder 5 has appeared on the report for 3 consecutive days -- consider escalating to maintenance planning"

### 14-6-ai-summary-with-trend-context-UNIT-010: fetch_repeat_offenders identifies asset below target for 3 consecutive days
- Priority: P0
- Type: unit
- Given: daily_summaries for trailing 7 days shows "Grinder 5" (asset-1) with OEE below target (85%) for the last 3 consecutive days ending on target_date
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns [{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}]
- Data: Mock Supabase with 7 days of daily_summaries: asset-1 has OEE [86, 87, 85, 88, 78, 72, 75] for dates 2/4-2/10 (last 3 days below 85 target); assets dict mapping asset-1 to "Grinder 5"

### 14-6-ai-summary-with-trend-context-UNIT-011: fetch_repeat_offenders identifies asset below target for 4+ consecutive days
- Priority: P0
- Type: unit
- Given: daily_summaries shows "CAMA 2400" (asset-2) with OEE below target for 4 consecutive days ending on target_date
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns entry with {"asset_name": "CAMA 2400", "consecutive_days": 4, "category": "oee"}
- Data: Mock asset-2 below target for 4 of last 7 days (the trailing 4)

### 14-6-ai-summary-with-trend-context-UNIT-012: fetch_repeat_offenders excludes asset below target for only 2 consecutive days
- Priority: P0
- Type: unit
- Given: daily_summaries shows an asset with OEE below target for only 2 consecutive days ending on target_date
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns empty list (asset does not meet 3-day threshold)
- Data: Mock asset with OEE below target only on 2/9 and 2/10

### 14-6-ai-summary-with-trend-context-UNIT-013: fetch_repeat_offenders handles non-consecutive below-target days
- Priority: P1
- Type: unit
- Given: daily_summaries shows an asset below target on days 2/5, 2/6, 2/8, 2/9, 2/10 but NOT 2/7 (gap breaks consecutive streak to 3 ending on target_date)
- When: fetch_repeat_offenders(target_date=date(2026, 2, 10)) is called
- Then: returns entry with consecutive_days=3 (counts only 2/8, 2/9, 2/10 streak ending on target_date)
- Data: Mock daily_summaries with gap on 2/7

### 14-6-ai-summary-with-trend-context-UNIT-014: format_trend_context renders repeat offenders section
- Priority: P0
- Type: unit
- Given: repeat_offenders = [{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}, {"asset_name": "CAMA 2400", "consecutive_days": 4, "category": "oee"}]
- When: format_trend_context(repeat_offenders=repeat_offenders) is called
- Then: output contains "Repeat Offenders (3+ consecutive days on report):" AND "Grinder 5: 3 consecutive days" AND "CAMA 2400: 4 consecutive days"
- Data: repeat_offenders list as specified

### 14-6-ai-summary-with-trend-context-UNIT-015: SummaryContext repeat_offenders field defaults to empty list
- Priority: P1
- Type: unit
- Given: SummaryContext is constructed without passing repeat_offenders
- When: SummaryContext is instantiated
- Then: context.repeat_offenders equals [] (empty list)
- Data: Minimal SummaryContext

### 14-6-ai-summary-with-trend-context-UNIT-016: build_context populates repeat_offenders when trailing data exists
- Priority: P0
- Type: unit
- Given: Supabase has 7 days of daily_summaries with an asset below OEE target for 3+ consecutive days
- When: build_context(target_date) is called
- Then: returned SummaryContext has repeat_offenders list containing at least one entry
- Data: Mock daily_summaries with appropriate trailing data

### 14-6-ai-summary-with-trend-context-UNIT-017: fetch_repeat_offenders returns multiple repeat offenders sorted by consecutive_days descending
- Priority: P2
- Type: unit
- Given: Two assets both qualify as repeat offenders with different consecutive day counts (3 and 5)
- When: fetch_repeat_offenders(target_date) is called
- Then: returns both assets in list, ordered by consecutive_days descending (5-day first)
- Data: Mock two assets with different streak lengths


## AC3: Given a downtime Pareto breakdown is available When the smart summary is generated Then the summary includes the top downtime driver: "Top downtime driver yesterday: Mechanical (187 min across 4 assets)"

### 14-6-ai-summary-with-trend-context-UNIT-018: fetch_top_downtime_drivers aggregates by reason_code correctly
- Priority: P0
- Type: unit
- Given: downtime_events table has 6 rows for target_date: [Mechanical/asset-1/60min, Mechanical/asset-2/45min, Mechanical/asset-3/40min, Mechanical/asset-4/42min, Changeover/asset-1/50min, Changeover/asset-5/45min]
- When: fetch_top_downtime_drivers(target_date=date(2026, 2, 10)) is called
- Then: returns [{"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4}, {"reason_code": "Changeover", "total_minutes": 95, "asset_count": 2}]
- Data: Mock Supabase downtime_events with 6 rows as described, grouped and aggregated

### 14-6-ai-summary-with-trend-context-UNIT-019: fetch_top_downtime_drivers returns top 3 only when more than 3 reason codes exist
- Priority: P1
- Type: unit
- Given: downtime_events table has rows with 5 distinct reason_codes for target_date
- When: fetch_top_downtime_drivers(target_date) is called
- Then: returns exactly 3 entries, sorted by total_minutes descending
- Data: Mock 5 reason codes with varying totals

### 14-6-ai-summary-with-trend-context-UNIT-020: fetch_top_downtime_drivers counts distinct assets per reason_code
- Priority: P1
- Type: unit
- Given: downtime_events has Mechanical reason with multiple events for the SAME asset (asset-1: 30min, asset-1: 25min) and one event for asset-2 (40min)
- When: fetch_top_downtime_drivers(target_date) is called
- Then: Mechanical entry has total_minutes=95 and asset_count=2 (not 3 — distinct assets only)
- Data: Mock with duplicate asset_id within same reason_code

### 14-6-ai-summary-with-trend-context-UNIT-021: format_trend_context renders top downtime drivers section
- Priority: P0
- Type: unit
- Given: top_downtime_drivers = [{"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4}, {"reason_code": "Changeover", "total_minutes": 95, "asset_count": 6}]
- When: format_trend_context(top_downtime_drivers=top_downtime_drivers) is called
- Then: output contains "Top Downtime Drivers (yesterday):" AND "Mechanical: 187 min across 4 assets" AND "Changeover: 95 min across 6 assets"
- Data: top_downtime_drivers list as specified

### 14-6-ai-summary-with-trend-context-UNIT-022: SummaryContext top_downtime_drivers field defaults to empty list
- Priority: P1
- Type: unit
- Given: SummaryContext is constructed without passing top_downtime_drivers
- When: SummaryContext is instantiated
- Then: context.top_downtime_drivers equals [] (empty list)
- Data: Minimal SummaryContext

### 14-6-ai-summary-with-trend-context-UNIT-023: build_context populates top_downtime_drivers when downtime_events data exists
- Priority: P0
- Type: unit
- Given: Supabase downtime_events table has rows for target_date
- When: build_context(target_date) is called
- Then: returned SummaryContext has top_downtime_drivers list with aggregated entries
- Data: Mock downtime_events with multiple reason codes

### 14-6-ai-summary-with-trend-context-UNIT-024: fetch_top_downtime_drivers returns empty list when no downtime events for target_date
- Priority: P1
- Type: unit
- Given: downtime_events table exists but has no rows for target_date
- When: fetch_top_downtime_drivers(target_date) is called
- Then: returns empty list []
- Data: Mock Supabase returning empty data for query


## AC4: Given trend data is not available (e.g., first day of operation) When the smart summary is generated Then the summary gracefully omits trend commentary without error and the rest of the summary is unaffected

### 14-6-ai-summary-with-trend-context-UNIT-025: fetch_trend_data returns None when no historical data exists
- Priority: P0
- Type: unit
- Given: daily_summaries table has no data for target_date - 7 (first day of operation)
- When: fetch_trend_data(target_date) is called
- Then: returns None
- Data: Mock Supabase returning empty data for the previous week query

### 14-6-ai-summary-with-trend-context-UNIT-026: fetch_trend_data returns None on Supabase exception
- Priority: P0
- Type: unit
- Given: Supabase client raises an exception (e.g., connection error) during query
- When: fetch_trend_data(target_date) is called
- Then: returns None (does not raise), and error is logged
- Data: Mock Supabase to raise Exception("connection error")

### 14-6-ai-summary-with-trend-context-UNIT-027: fetch_repeat_offenders returns empty list on Supabase exception
- Priority: P0
- Type: unit
- Given: Supabase client raises an exception during repeat offenders query
- When: fetch_repeat_offenders(target_date) is called
- Then: returns [] (does not raise), and error is logged
- Data: Mock Supabase to raise Exception

### 14-6-ai-summary-with-trend-context-UNIT-028: fetch_top_downtime_drivers returns empty list when table does not exist
- Priority: P0
- Type: unit
- Given: downtime_events table does not exist (Story 14.1 migration not yet run), Supabase raises a table-not-found error
- When: fetch_top_downtime_drivers(target_date) is called
- Then: returns [] (does not raise), and error is logged
- Data: Mock Supabase to raise exception simulating missing table

### 14-6-ai-summary-with-trend-context-UNIT-029: build_context succeeds with all trend fetches failing
- Priority: P0
- Type: unit
- Given: fetch_trend_data, fetch_repeat_offenders, and fetch_top_downtime_drivers all raise exceptions internally
- When: build_context(target_date) is called
- Then: returns a valid SummaryContext with trend_data=None, repeat_offenders=[], top_downtime_drivers=[], and core fields (daily_summaries, safety_events, action_items) are populated normally
- Data: Mock all trend fetches to raise; mock core fetches to return valid data

### 14-6-ai-summary-with-trend-context-UNIT-030: format_trend_context with all None/empty inputs returns graceful message
- Priority: P0
- Type: unit
- Given: trend_data=None, repeat_offenders=[], top_downtime_drivers=[]
- When: format_trend_context(trend_data=None, repeat_offenders=[], top_downtime_drivers=[]) is called
- Then: returns "No trend data available for this period." or equivalent benign string (not empty, not error)
- Data: All-empty inputs

### 14-6-ai-summary-with-trend-context-UNIT-031: render_data_prompt works without trend kwargs (backward compatible)
- Priority: P0
- Type: unit
- Given: render_data_prompt is called with only the existing positional/keyword args (no trend_data, no repeat_offenders, no top_downtime_drivers)
- When: render_data_prompt(target_date=..., safety_events=[], daily_summaries=[], action_items=[]) is called
- Then: returns a valid prompt string without errors; TREND CONTEXT section contains graceful "no data" text
- Data: Only pre-14.6 arguments

### 14-6-ai-summary-with-trend-context-INT-002: Full summary generation succeeds on first day of operation with no trend data
- Priority: P0
- Type: integration
- Given: Supabase has daily_summaries for target_date only (no prior history), no downtime_events data
- When: generate_smart_summary(target_date) is called with mocked LLM
- Then: summary is generated successfully, is_fallback=False, summary_text does not contain trend commentary, and no exceptions are raised
- Data: Mock only target_date data; LLM returns summary text without trend references

### 14-6-ai-summary-with-trend-context-UNIT-032: format_trend_context with partial data renders only available sections
- Priority: P1
- Type: unit
- Given: trend_data is populated but repeat_offenders=[] and top_downtime_drivers=[]
- When: format_trend_context(trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1}, repeat_offenders=[], top_downtime_drivers=[])
- Then: output contains "Week-over-Week OEE" but does NOT contain "Repeat Offenders" or "Top Downtime Drivers" sections
- Data: Only trend_data populated

### 14-6-ai-summary-with-trend-context-UNIT-033: build_context isolates trend fetch failure from repeat offender fetch
- Priority: P1
- Type: unit
- Given: fetch_trend_data raises an exception but fetch_repeat_offenders and fetch_top_downtime_drivers succeed
- When: build_context(target_date) is called
- Then: SummaryContext has trend_data=None but repeat_offenders and top_downtime_drivers are populated correctly
- Data: Mock trend_data to fail; mock repeat_offenders and downtime_drivers to succeed


## AC5: Given the fallback summary is triggered (LLM unavailable) When trend context data is available Then the fallback template also includes trend lines (week-over-week OEE change, repeat offenders, top downtime driver)

### 14-6-ai-summary-with-trend-context-UNIT-034: Fallback summary includes WoW OEE comparison when trend_data is present
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data={"plant_oee_current": 81.2, "plant_oee_previous_week": 84.3, "plant_oee_wow_change": -3.1} and valid daily_summaries
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "Overall plant OEE 81.2%" and "down 3.1 points from last week"
- Data: SummaryContext with trend_data and basic daily_summaries

### 14-6-ai-summary-with-trend-context-UNIT-035: Fallback summary includes positive WoW OEE with "up" direction
- Priority: P1
- Type: unit
- Given: SummaryContext has trend_data with plant_oee_wow_change=2.5 (positive)
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "up 2.5 points from last week"
- Data: SummaryContext with positive wow_change

### 14-6-ai-summary-with-trend-context-UNIT-036: Fallback summary includes Recurring Issues section when repeat_offenders exist
- Priority: P0
- Type: unit
- Given: SummaryContext has repeat_offenders=[{"asset_name": "Grinder 5", "consecutive_days": 3, "category": "oee"}]
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "**Recurring Issues**" section header AND "Grinder 5" AND "3 consecutive days" AND "consider escalating to maintenance planning"
- Data: SummaryContext with one repeat offender

### 14-6-ai-summary-with-trend-context-UNIT-037: Fallback summary includes Downtime Drivers section when top_downtime_drivers exist
- Priority: P0
- Type: unit
- Given: SummaryContext has top_downtime_drivers=[{"reason_code": "Mechanical", "total_minutes": 187, "asset_count": 4}]
- When: generate_fallback_summary(context) is called
- Then: the returned summary_text contains "**Downtime Drivers**" section header AND "Mechanical: 187 min across 4 assets"
- Data: SummaryContext with one downtime driver

### 14-6-ai-summary-with-trend-context-UNIT-038: Fallback summary includes all three trend sections simultaneously
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data, repeat_offenders (2 entries), and top_downtime_drivers (3 entries) all populated
- When: generate_fallback_summary(context) is called
- Then: summary_text contains WoW OEE line, **Recurring Issues** section with both offenders, and **Downtime Drivers** section with all 3 drivers; existing sections (**Safety**, **Productivity**) are also present and unaffected
- Data: Fully populated SummaryContext with all trend fields and existing fields

### 14-6-ai-summary-with-trend-context-UNIT-039: Fallback summary without trend data is unchanged from pre-14.6 behavior
- Priority: P0
- Type: unit
- Given: SummaryContext has trend_data=None, repeat_offenders=[], top_downtime_drivers=[] (no trend data), but has valid daily_summaries and safety_events
- When: generate_fallback_summary(context) is called
- Then: summary_text does NOT contain "Recurring Issues", "Downtime Drivers", or "points from last week"; existing sections are present and correctly formatted; output matches pre-14.6 format
- Data: SummaryContext with only pre-14.6 fields populated

### 14-6-ai-summary-with-trend-context-UNIT-040: Fallback summary with partial trend data includes only available sections
- Priority: P1
- Type: unit
- Given: SummaryContext has trend_data populated but repeat_offenders=[] and top_downtime_drivers=[]
- When: generate_fallback_summary(context) is called
- Then: summary_text contains WoW OEE line but does NOT contain "Recurring Issues" or "Downtime Drivers" sections
- Data: SummaryContext with only trend_data populated

### 14-6-ai-summary-with-trend-context-UNIT-041: Fallback summary is_fallback flag is True and model_used is "fallback_template"
- Priority: P1
- Type: unit
- Given: SummaryContext with all trend fields populated
- When: generate_fallback_summary(context) is called
- Then: returned SmartSummary has is_fallback=True and model_used="fallback_template" (trend data does not change these metadata fields)
- Data: SummaryContext with trend data


edge_cases:
  - fetch_trend_data when target_date has data but target_date - 7 returns empty (partial data) — should return None since comparison is incomplete
  - fetch_trend_data when only 1 asset has OEE on target_date but 10 assets on target_date - 7 — average should still be computed per-date independently
  - fetch_repeat_offenders when an asset is below target on days 1-3 and 5-7 (gap on day 4) — should report consecutive_days=3 for the trailing streak ending on target_date
  - fetch_repeat_offenders when asset has OEE exactly equal to target_oee — it should NOT count as below target (strictly less than)
  - fetch_top_downtime_drivers when all events have the same reason_code — should return single entry with total across all assets
  - fetch_top_downtime_drivers when duration_minutes varies widely (e.g., 1 min vs 500 min) — sort by total_minutes not event count
  - format_trend_context when plant_oee_wow_change is exactly 0.0 — should display "change: +0.0 points" or handle zero-change case gracefully
  - Fallback summary section ordering — Recurring Issues and Downtime Drivers appear in correct positions relative to existing Safety, Productivity, Financial Impact sections
  - Very large trend data (e.g., 50+ assets in daily_summaries) — ensure averaging is correct and no performance issues

error_scenarios:
  - Supabase connection timeout during fetch_trend_data — returns None, logged, does not block summary
  - Supabase connection timeout during fetch_repeat_offenders — returns [], logged, does not block summary
  - downtime_events table does not exist (14.1 not deployed) — fetch_top_downtime_drivers returns [], logged, does not block summary
  - Malformed data in daily_summaries (e.g., oee_percentage is null) — fetch_trend_data handles gracefully, skips null values or returns None
  - fetch_trend_data, fetch_repeat_offenders, and fetch_top_downtime_drivers all fail simultaneously — build_context still returns valid SummaryContext
  - render_data_prompt called with custom DATA_TEMPLATE_DEFAULT env override missing {trend_context} placeholder — should not crash (catch KeyError)
  - LLM receives trend context in prompt but returns summary without mentioning trends — system should not fail or retry (LLM output is best-effort)

test_file_mapping:
  - 14-6-ai-summary-with-trend-context-UNIT-*: apps/api/tests/test_smart_summary.py
  - 14-6-ai-summary-with-trend-context-INT-*: apps/api/tests/test_smart_summary.py
  - 14-6-ai-summary-with-trend-context-E2E-*: apps/api/tests/test_smart_summary.py

TEST SPEC END

---
