TEST SPEC START
story_id: 17-3-shift-summaries-data-model
generated: 2026-02-12

test_specifications:

## AC1: Given the migration runs successfully When the database is queried Then the `shift_summaries` table exists with all specified columns

### 17-3-shift-summaries-data-model-UNIT-001: Migration file exists at correct path and is non-empty
- Priority: P0
- Type: unit
- Given: The migration file 0035_shift_summaries.sql has been created
- When: The file system is checked for the migration file at `supabase/migrations/0035_shift_summaries.sql`
- Then: The file exists at the expected path and has non-empty content
- Data: File path `supabase/migrations/0035_shift_summaries.sql`

### 17-3-shift-summaries-data-model-UNIT-002: Migration creates shift_summaries table with CREATE TABLE IF NOT EXISTS
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE TABLE statement
- Then: The migration contains `CREATE TABLE IF NOT EXISTS shift_summaries` (idempotent pattern)
- Data: Regex match on migration SQL content

### 17-3-shift-summaries-data-model-UNIT-003: Table has id column as UUID PK with gen_random_uuid() default
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the id column definition
- Then: The column is defined as `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-004: Table has asset_id column as UUID NOT NULL FK to assets(id) ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the asset_id column definition
- Then: The column is defined as `asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE`
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-005: Table has date column as DATE NOT NULL
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the date column definition
- Then: The column is defined as `date DATE NOT NULL`
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-006: Table has shift column as TEXT NOT NULL with CHECK constraint for morning/afternoon/night
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the shift column definition
- Then: The column is defined as `shift TEXT NOT NULL CHECK (shift IN ('morning', 'afternoon', 'night'))`
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-007: Table has oee column as DECIMAL(5,2)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the oee column definition
- Then: The column is defined as `oee DECIMAL(5,2)` (or `NUMERIC(5,2)`)
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-008: Table has availability column as DECIMAL(5,2)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the availability column definition
- Then: The column is defined as `availability DECIMAL(5,2)` (or `NUMERIC(5,2)`)
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-009: Table has performance column as DECIMAL(5,2)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the performance column definition
- Then: The column is defined as `performance DECIMAL(5,2)` (or `NUMERIC(5,2)`)
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-010: Table has quality column as DECIMAL(5,2)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the quality column definition
- Then: The column is defined as `quality DECIMAL(5,2)` (or `NUMERIC(5,2)`)
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-011: Table has downtime_minutes column as INTEGER
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the downtime_minutes column definition
- Then: The column is defined as `downtime_minutes INTEGER`
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-012: Table has units_produced column as INTEGER
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the units_produced column definition
- Then: The column is defined as `units_produced INTEGER`
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-013: Table has created_at column as TIMESTAMPTZ with DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for the created_at column definition
- Then: The column is defined as `created_at TIMESTAMPTZ DEFAULT NOW()` (or `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`)
- Data: Regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-014: Table has exactly 11 columns
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is parsed for column definitions
- Then: Exactly 11 columns are defined: id, asset_id, date, shift, oee, availability, performance, quality, downtime_minutes, units_produced, created_at
- Data: Count of column definitions matching known column names in CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-015: Table does NOT have updated_at column (shift data is immutable)
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The shift_summaries CREATE TABLE block is searched for an updated_at column
- Then: No `updated_at` column definition exists in the shift_summaries CREATE TABLE statement
- Data: Negative regex match within CREATE TABLE block

### 17-3-shift-summaries-data-model-UNIT-016: Migration does NOT create update_updated_at trigger for shift_summaries
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for triggers on shift_summaries
- Then: No `CREATE TRIGGER` statement references the shift_summaries table
- Data: Negative regex match in full migration SQL

### 17-3-shift-summaries-data-model-UNIT-017: shift column uses TEXT CHECK, not ENUM type
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for CREATE TYPE or ENUM usage
- Then: No `CREATE TYPE` or `ENUM` keyword appears in the migration; shift uses TEXT with CHECK constraint
- Data: Negative regex match for CREATE TYPE and ENUM in full migration SQL

### 17-3-shift-summaries-data-model-UNIT-018: Migration uses gen_random_uuid() not uuid_generate_v4()
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for uuid_generate_v4()
- Then: No `uuid_generate_v4()` appears; only `gen_random_uuid()` is used
- Data: Negative regex match for uuid_generate_v4()

### 17-3-shift-summaries-data-model-UNIT-019: Migration has header comment with story reference
- Priority: P2
- Type: unit
- Given: The migration SQL file content is loaded
- When: The first 500 characters of the SQL are inspected for header comments
- Then: A comment referencing Story 17.3 or shift summaries exists at the top of the file
- Data: Regex match on first 500 chars of migration SQL

### 17-3-shift-summaries-data-model-UNIT-020: Migration has COMMENT ON TABLE and COMMENT ON COLUMN statements
- Priority: P2
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for documentation comments
- Then: A `COMMENT ON TABLE shift_summaries` statement exists and at least 5 `COMMENT ON COLUMN shift_summaries.` statements exist
- Data: Regex match and count in full migration SQL

### 17-3-shift-summaries-data-model-INT-001: shift_summaries table exists and accepts a valid row insert
- Priority: P0
- Type: integration
- Given: A running Supabase instance with migration 0035_shift_summaries.sql applied and at least one asset existing
- When: A valid shift_summaries row is inserted via service_role client with all columns populated (asset_id from existing asset, date '2026-01-01', shift 'morning', oee 85.50, availability 92.00, performance 95.00, quality 97.80, downtime_minutes 30, units_produced 500)
- Then: The insert succeeds with no error, the returned row has a valid UUID id and a created_at timestamp
- Data: Test asset UUID from seed data, valid shift_summaries row payload

### 17-3-shift-summaries-data-model-INT-002: CHECK constraint rejects invalid shift value
- Priority: P0
- Type: integration
- Given: The shift_summaries table exists in a running Supabase instance
- When: A shift_summaries row is inserted via service_role with shift = 'evening' (invalid value)
- Then: The insert fails with a CHECK constraint violation error message
- Data: Invalid payload with shift = 'evening'

### 17-3-shift-summaries-data-model-INT-003: CHECK constraint accepts all three valid shift values
- Priority: P0
- Type: integration
- Given: The shift_summaries table exists in a running Supabase instance with at least one asset
- When: Three shift_summaries rows are inserted via service_role for the same asset and date with shift values 'morning', 'afternoon', and 'night' respectively
- Then: All three inserts succeed with no errors
- Data: Valid payloads for each of the three shift values

### 17-3-shift-summaries-data-model-INT-004: FK constraint rejects non-existent asset_id
- Priority: P1
- Type: integration
- Given: The shift_summaries table exists in a running Supabase instance
- When: A shift_summaries row is inserted via service_role with asset_id = '00000000-0000-0000-0000-000000000000' (non-existent)
- Then: The insert fails with a foreign key constraint violation error
- Data: Non-existent UUID for asset_id

### 17-3-shift-summaries-data-model-INT-005: Default gen_random_uuid() generates unique id on insert
- Priority: P1
- Type: integration
- Given: The shift_summaries table exists in a running Supabase instance
- When: Two shift_summaries rows are inserted via service_role without specifying id (different dates or shifts to avoid unique constraint)
- Then: Both inserts succeed, each has a unique non-null UUID id, and both IDs match UUID pattern
- Data: Two valid payloads with different date or shift values

### 17-3-shift-summaries-data-model-INT-006: Default NOW() populates created_at on insert
- Priority: P1
- Type: integration
- Given: The shift_summaries table exists in a running Supabase instance
- When: A shift_summaries row is inserted via service_role without specifying created_at
- Then: The created_at column is automatically populated with a timestamp within 5 seconds of current time
- Data: Valid payload without created_at field

### 17-3-shift-summaries-data-model-INT-007: Cascade delete removes shift_summaries when asset is deleted
- Priority: P1
- Type: integration
- Given: A test asset exists with 3 shift_summaries rows (one per shift) in a running Supabase instance
- When: The test asset is deleted from the assets table
- Then: All 3 shift_summaries rows for that asset_id are also deleted (ON DELETE CASCADE behavior)
- Data: Test asset and 3 shift_summaries rows for morning/afternoon/night

### 17-3-shift-summaries-data-model-INT-008: DECIMAL(5,2) columns accept values in range 0.00-100.00
- Priority: P1
- Type: integration
- Given: The shift_summaries table exists in a running Supabase instance
- When: A shift_summaries row is inserted with oee=99.99, availability=100.00, performance=0.00, quality=50.50
- Then: The insert succeeds and values are stored exactly as provided
- Data: Valid payload with boundary DECIMAL values

## AC2: Given the migration runs successfully When the constraints are inspected Then a unique constraint exists on (asset_id, date, shift)

### 17-3-shift-summaries-data-model-UNIT-021: Migration defines unique constraint on (asset_id, date, shift)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for unique constraint definitions
- Then: A named UNIQUE constraint `shift_summaries_asset_date_shift_unique` exists on `(asset_id, date, shift)` (or equivalent inline UNIQUE constraint on those three columns)
- Data: Regex match for CONSTRAINT ... UNIQUE (asset_id, date, shift) in CREATE TABLE block or ALTER TABLE statement

### 17-3-shift-summaries-data-model-INT-009: Unique constraint prevents duplicate (asset_id, date, shift) combination
- Priority: P0
- Type: integration
- Given: A shift_summaries row exists with asset_id=X, date='2026-01-15', shift='morning' in a running Supabase instance
- When: A second row with the same asset_id=X, date='2026-01-15', shift='morning' is inserted
- Then: The insert fails with a unique constraint violation error
- Data: Two identical payloads for (asset_id, date, shift)

### 17-3-shift-summaries-data-model-INT-010: Unique constraint allows same asset and date with different shifts
- Priority: P0
- Type: integration
- Given: A shift_summaries row exists with asset_id=X, date='2026-01-16', shift='morning'
- When: Two more rows are inserted with the same asset_id=X and date='2026-01-16' but shift='afternoon' and shift='night'
- Then: Both inserts succeed, and the table contains exactly 3 rows for that asset and date
- Data: Three payloads with same asset_id and date, different shift values

### 17-3-shift-summaries-data-model-INT-011: Unique constraint allows same asset and shift on different dates
- Priority: P1
- Type: integration
- Given: A shift_summaries row exists with asset_id=X, date='2026-01-17', shift='morning'
- When: Another row is inserted with the same asset_id=X, shift='morning' but date='2026-01-18'
- Then: The insert succeeds (different date means different key)
- Data: Two payloads with same asset_id and shift, different dates

## AC3: Given the migration runs successfully When the indexes are inspected Then indexes exist on asset_id, date, and composite (asset_id, date)

### 17-3-shift-summaries-data-model-UNIT-022: Migration creates index on asset_id
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE INDEX statements
- Then: An index named `idx_shift_summaries_asset_id` is created on `shift_summaries(asset_id)` using `CREATE INDEX IF NOT EXISTS`
- Data: Regex match for CREATE INDEX IF NOT EXISTS idx_shift_summaries_asset_id ON shift_summaries(asset_id)

### 17-3-shift-summaries-data-model-UNIT-023: Migration creates index on date
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE INDEX statements
- Then: An index named `idx_shift_summaries_date` is created on `shift_summaries(date)` using `CREATE INDEX IF NOT EXISTS`
- Data: Regex match for CREATE INDEX IF NOT EXISTS idx_shift_summaries_date ON shift_summaries(date)

### 17-3-shift-summaries-data-model-UNIT-024: Migration creates composite index on (asset_id, date)
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for CREATE INDEX statements
- Then: An index named `idx_shift_summaries_asset_date` (or similar) is created on `shift_summaries(asset_id, date)` using `CREATE INDEX IF NOT EXISTS`
- Data: Regex match for CREATE INDEX IF NOT EXISTS ... ON shift_summaries(asset_id, date)

### 17-3-shift-summaries-data-model-UNIT-025: All three required indexes are present
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: All CREATE INDEX statements targeting shift_summaries are counted
- Then: At least 3 CREATE INDEX statements exist for the shift_summaries table
- Data: Regex match count for CREATE INDEX.*shift_summaries

### 17-3-shift-summaries-data-model-UNIT-026: All indexes use CREATE INDEX IF NOT EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: Every CREATE INDEX statement targeting shift_summaries is inspected
- Then: All use the `IF NOT EXISTS` clause
- Data: Regex match validation on each CREATE INDEX statement

## AC4: Given the migration runs successfully When RLS policies are inspected Then RLS is enabled on shift_summaries with policies matching the daily_summaries pattern

### 17-3-shift-summaries-data-model-UNIT-027: Migration enables RLS on shift_summaries
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for RLS enablement
- Then: The statement `ALTER TABLE shift_summaries ENABLE ROW LEVEL SECURITY` exists
- Data: Exact string match in migration SQL

### 17-3-shift-summaries-data-model-UNIT-028: Migration creates authenticated SELECT policy on shift_summaries
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the SELECT RLS policy
- Then: A policy exists `FOR SELECT TO authenticated` on shift_summaries with `USING (true)`
- Data: Regex match for CREATE POLICY...ON shift_summaries FOR SELECT...TO authenticated...USING (true)

### 17-3-shift-summaries-data-model-UNIT-029: Migration creates service_role full access policy on shift_summaries
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is parsed for the service_role policy
- Then: A policy exists `FOR ALL TO service_role` on shift_summaries with `USING (true)` and `WITH CHECK (true)`
- Data: Regex match for CREATE POLICY...ON shift_summaries FOR ALL...TO service_role...USING (true)...WITH CHECK (true)

### 17-3-shift-summaries-data-model-UNIT-030: RLS policies use DROP POLICY IF EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for DROP POLICY IF EXISTS statements for shift_summaries
- Then: Each CREATE POLICY on shift_summaries is preceded by a corresponding `DROP POLICY IF EXISTS` statement, and the count of DROPs >= count of CREATEs
- Data: Count comparison of DROP POLICY vs CREATE POLICY statements

### 17-3-shift-summaries-data-model-INT-012: Service role can INSERT, SELECT, UPDATE, and DELETE on shift_summaries
- Priority: P0
- Type: integration
- Given: A running Supabase instance with shift_summaries table and RLS policies applied, and at least one asset
- When: The service_role client performs INSERT, SELECT, UPDATE, and DELETE operations on shift_summaries
- Then: All four CRUD operations succeed without RLS restriction errors
- Data: Valid shift_summaries row for CRUD operations

### 17-3-shift-summaries-data-model-INT-013: Anonymous/unauthenticated user cannot INSERT into shift_summaries
- Priority: P1
- Type: integration
- Given: A running Supabase instance with shift_summaries table and RLS policies applied, using an anon key client
- When: An unauthenticated client attempts to INSERT a row into shift_summaries
- Then: The insert fails with an RLS policy violation error
- Data: Valid payload, anon key client (SUPABASE_ANON_KEY required)

### 17-3-shift-summaries-data-model-INT-014: Authenticated user can SELECT from shift_summaries
- Priority: P1
- Type: integration
- Given: A running Supabase instance with shift_summaries rows present and an authenticated user session
- When: The authenticated client performs a SELECT on shift_summaries
- Then: The query succeeds and returns rows (no RLS blocking)
- Data: Pre-seeded shift_summaries rows, authenticated client

## AC5: Given the seed script runs When shift summaries are queried Then each asset has 3 shift records per day (morning, afternoon, night) for the same date range as existing daily_summaries seed data

### 17-3-shift-summaries-data-model-UNIT-031: Seed script contains shift_summaries insertion logic
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The script is searched for shift_summaries data insertion code
- Then: A `shift_summaries` insert or upsert block exists using `supabase.from('shift_summaries')`
- Data: String/regex match in seed-data.mjs content

### 17-3-shift-summaries-data-model-UNIT-032: Seed script contains shift distribution helper function
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The script is searched for a shift distribution or generation function
- Then: A function that takes daily summaries and produces shift-level records exists (e.g., `generateShiftSummaries` or similar)
- Data: Function name regex match in seed-data.mjs content

### 17-3-shift-summaries-data-model-UNIT-033: Seed script generates records for all three shifts (morning, afternoon, night)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The shift generation logic is inspected
- Then: The strings 'morning', 'afternoon', and 'night' all appear in the shift_summaries generation context
- Data: String match for all three shift values in seed-data.mjs

### 17-3-shift-summaries-data-model-UNIT-034: Seed script includes shift_summaries cleanup in the clear section
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The clearing/cleanup section of the script is inspected
- Then: A `supabase.from('shift_summaries').delete()` call exists in the clearing section, positioned before daily_summaries delete
- Data: String match for shift_summaries delete in seed-data.mjs

### 17-3-shift-summaries-data-model-INT-015: Each asset has exactly 3 shift_summaries records per day for the last 7 days
- Priority: P0
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed, daily_summaries and shift_summaries populated
- When: shift_summaries are queried grouped by (asset_id, date) for dates T-1 through T-7
- Then: Each (asset_id, date) combination has exactly 3 records and the shifts are exactly {'morning', 'afternoon', 'night'}
- Data: All 14 asset IDs, date range T-1 to T-7

### 17-3-shift-summaries-data-model-INT-016: shift_summaries date range matches daily_summaries date range per asset
- Priority: P0
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: The set of distinct dates in shift_summaries for each asset is compared to the set of distinct dates (report_date) in daily_summaries for the same asset
- Then: The date sets are identical for every asset
- Data: Joined query comparing shift_summaries.date to daily_summaries.report_date per asset

### 17-3-shift-summaries-data-model-INT-017: Total shift_summaries record count matches expected (assets x days x 3 shifts)
- Priority: P1
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: COUNT(*) is queried from shift_summaries
- Then: The total count equals (number of assets with daily_summaries) * (number of days per asset) * 3
- Data: Expected count based on seed data coverage (14 assets x 8 days x 3 shifts = 336, or adjusted for actual asset/day coverage)

## AC6: Given the seed script runs When shift summary values are aggregated per asset per day Then the sum of shift units_produced approximately matches daily_summaries.actual_output and weighted-average shift OEE approximately matches daily_summaries.oee_percentage

### 17-3-shift-summaries-data-model-INT-018: Sum of shift units_produced approximately matches daily actual_output per asset per day
- Priority: P0
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed, both daily_summaries and shift_summaries populated
- When: For each (asset_id, date) pair, SUM(shift_summaries.units_produced) is compared to daily_summaries.actual_output
- Then: The shift sum is within 3% of the daily actual_output value (tolerance for rounding), or exactly equal
- Data: Join query across shift_summaries and daily_summaries grouped by (asset_id, date)

### 17-3-shift-summaries-data-model-INT-019: Weighted-average shift OEE approximately matches daily oee_percentage per asset per day
- Priority: P0
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: For each (asset_id, date) pair, the weighted average of shift OEE values (weighted by units_produced) is calculated and compared to daily_summaries.oee_percentage
- Then: The weighted-average shift OEE is within 5 percentage points of the daily oee_percentage value
- Data: Calculated weighted average vs daily_summaries.oee_percentage per (asset_id, date)

### 17-3-shift-summaries-data-model-INT-020: No asset-date pair has shift units_produced sum deviating more than 5% from daily actual_output
- Priority: P1
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: All (asset_id, date) pairs are evaluated for deviation between shift sum and daily total
- Then: Zero asset-date pairs have a deviation greater than 5%, confirming consistent seed data alignment
- Data: Aggregate deviation query across all records

## AC7: Given the seed script runs When individual shift records are examined Then shifts have realistic variance rather than uniform distribution

### 17-3-shift-summaries-data-model-INT-021: Morning shift produces approximately 35-40% of daily output
- Priority: P1
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: For a sample of asset-date pairs, morning shift units_produced is calculated as a percentage of the daily total (sum of all 3 shifts)
- Then: Morning shift percentage falls between 25% and 50% (with variance) for the majority of records
- Data: shift_summaries filtered by shift='morning', calculated as fraction of daily total

### 17-3-shift-summaries-data-model-INT-022: Night shift generally produces less output than morning shift
- Priority: P1
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: Across all asset-date pairs, the average units_produced for morning shift is compared to the average for night shift
- Then: Average morning shift units_produced is greater than average night shift units_produced
- Data: Aggregate AVG(units_produced) grouped by shift across all records

### 17-3-shift-summaries-data-model-INT-023: Shift OEE values are not identical across all three shifts for any asset-date
- Priority: P0
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: For each (asset_id, date), the set of distinct OEE values across the 3 shifts is examined
- Then: At least 80% of (asset_id, date) combinations have at least 2 distinct OEE values (i.e., not all three shifts have identical OEE)
- Data: Query distinct OEE values per (asset_id, date) and check for variance

### 17-3-shift-summaries-data-model-INT-024: Afternoon shift occasionally shows distinctly lower performance
- Priority: P1
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: Afternoon shift OEE values are compared to morning shift OEE values across all asset-date pairs
- Then: At least 15% of records show afternoon OEE that is 3+ percentage points lower than morning OEE for the same asset-date, indicating realistic shift disruption patterns
- Data: Paired comparison of morning vs afternoon OEE per (asset_id, date)

### 17-3-shift-summaries-data-model-INT-025: OEE sub-components are within realistic manufacturing ranges
- Priority: P1
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: All shift_summaries records are queried for availability, performance, and quality values
- Then: availability is between 75 and 100, performance is between 70 and 100, quality is between 90 and 100 for all records
- Data: Range validation query on availability, performance, quality columns

### 17-3-shift-summaries-data-model-INT-026: Night shift has more downtime_minutes than morning shift on average
- Priority: P2
- Type: integration
- Given: A running Supabase instance with seed-data.mjs executed
- When: Average downtime_minutes is calculated for morning vs night shifts across all records
- Then: Night shift average downtime_minutes is greater than or equal to morning shift average downtime_minutes
- Data: Aggregate AVG(downtime_minutes) grouped by shift

## AC8: Given the existing daily_summaries table and all views that query it When the migration and seed run Then existing daily views continue working unchanged

### 17-3-shift-summaries-data-model-UNIT-035: Migration does NOT contain ALTER TABLE statements on daily_summaries
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for ALTER TABLE daily_summaries statements
- Then: No `ALTER TABLE daily_summaries` statement exists in the migration file
- Data: Negative regex match for ALTER TABLE daily_summaries

### 17-3-shift-summaries-data-model-UNIT-036: Migration does NOT contain DROP or ALTER statements on any existing table or view
- Priority: P0
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for DROP TABLE, DROP VIEW, ALTER TABLE statements targeting tables other than shift_summaries
- Then: No destructive or modifying statements target any existing table (daily_summaries, assets, live_snapshots, etc.) - only shift_summaries is created/modified
- Data: Regex match for ALTER TABLE or DROP TABLE/VIEW statements, excluding shift_summaries and policy drops

### 17-3-shift-summaries-data-model-UNIT-037: Seed script daily_summaries upsert logic is unchanged
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The daily_summaries upsert block is inspected
- Then: The existing `supabase.from('daily_summaries').upsert()` call remains intact with its original onConflict clause and data array reference
- Data: String/regex match for daily_summaries upsert pattern in seed-data.mjs

### 17-3-shift-summaries-data-model-INT-027: daily_summaries table still returns expected data after migration runs
- Priority: P0
- Type: integration
- Given: A running Supabase instance with all migrations applied including 0035_shift_summaries.sql, and seed data loaded
- When: daily_summaries are queried for T-1 with a join to assets
- Then: All 14 assets have daily_summaries rows for T-1 with valid oee_percentage, actual_output, and target_output values (same as before migration)
- Data: Query daily_summaries joined with assets, filtered by T-1 date

### 17-3-shift-summaries-data-model-INT-028: Existing views that query daily_summaries still return results
- Priority: P1
- Type: integration
- Given: A running Supabase instance with all migrations applied including 0035_shift_summaries.sql
- When: Any existing database views (if present) that query daily_summaries are executed
- Then: The views return results without errors, confirming backward compatibility
- Data: Execute SELECT on known views referencing daily_summaries

## SQL Syntax Validation (cross-cutting)

### 17-3-shift-summaries-data-model-UNIT-038: Migration SQL has balanced parentheses
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: Open and close parentheses are counted
- Then: The count of `(` equals the count of `)`
- Data: Character count comparison in migration SQL

### 17-3-shift-summaries-data-model-UNIT-039: All SQL statements end with semicolons
- Priority: P1
- Type: unit
- Given: The migration SQL file content is loaded
- When: CREATE TABLE, CREATE INDEX, ALTER TABLE, CREATE POLICY, and DROP POLICY statements are parsed
- Then: Each statement is properly terminated with a semicolon
- Data: Regex match for each statement type followed by semicolon

### 17-3-shift-summaries-data-model-UNIT-040: Migration does NOT use VARCHAR (uses TEXT consistently)
- Priority: P2
- Type: unit
- Given: The migration SQL file content is loaded
- When: The SQL is searched for VARCHAR usage
- Then: No VARCHAR type appears in the migration
- Data: Negative regex match for VARCHAR (case-insensitive)

## Seed Data Idempotency

### 17-3-shift-summaries-data-model-UNIT-041: Seed script uses upsert with onConflict for shift_summaries
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The shift_summaries insertion code is inspected
- Then: The insertion uses `upsert` with `onConflict: 'asset_id,date,shift'` (or equivalent) for idempotency
- Data: String/regex match for upsert and onConflict pattern in seed-data.mjs

### 17-3-shift-summaries-data-model-INT-029: Running seed script twice produces same shift_summaries count (idempotency)
- Priority: P1
- Type: integration
- Given: A running Supabase instance with seed-data.mjs already executed once
- When: shift_summaries are queried for duplicate (asset_id, date, shift) combinations
- Then: Zero duplicate combinations exist (unique constraint would prevent this, but validates the upsert/clear pattern works)
- Data: Query for COUNT(*) grouped by (asset_id, date, shift) HAVING count > 1

edge_cases:
  - DECIMAL(5,2) column values at boundaries: oee=0.00, oee=100.00, availability=999.99 (should fail - exceeds 5,2 precision for percentages > 999)
  - NULL values for optional columns: oee, availability, performance, quality, downtime_minutes, units_produced should all be nullable unless otherwise constrained
  - Shift value case sensitivity: 'Morning' vs 'morning' - CHECK constraint should be case-sensitive, rejecting capitalized variants
  - Date edge cases: future dates should be insertable (no CHECK constraint on date range)
  - Large downtime_minutes value: e.g., 480 (full 8-hour shift) should be accepted as INTEGER
  - Negative values: downtime_minutes = -1 or units_produced = -1 - should these be rejected? (No CHECK constraint specified in AC, so they'd be accepted)
  - Asset deletion cascade with large number of shift_summaries: deleting an asset with 24+ shift records (8 days x 3 shifts) should cascade-delete all of them

error_scenarios:
  - Migration applied to database missing the assets table (FK dependency failure)
  - Seed script run before migration applied (shift_summaries table doesn't exist)
  - Seed script run without daily_summaries data (nothing to generate shift records from)
  - Supabase service key not configured (seed script should fail gracefully or skip)
  - Database connection timeout during large batch insert of shift_summaries records
  - Concurrent inserts violating unique constraint (race condition in parallel seed runs)

test_file_mapping:
  - 17-3-shift-summaries-data-model-UNIT-*: supabase/tests/shift-summaries-schema.test.ts
  - 17-3-shift-summaries-data-model-INT-*: supabase/tests/shift-summaries-integration.test.ts

TEST SPEC END
