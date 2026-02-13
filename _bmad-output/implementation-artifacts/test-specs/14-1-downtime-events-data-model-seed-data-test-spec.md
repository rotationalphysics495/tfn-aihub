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
