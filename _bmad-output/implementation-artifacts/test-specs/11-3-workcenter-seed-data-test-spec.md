TEST SPEC START
story_id: 11-3-workcenter-seed-data
generated: 2026-02-11

test_specifications:

## AC1: Given the seed script runs successfully, When the workcenter summary endpoint is called for yesterday's date, Then data exists for all 4 workcenters (Roasting, Grinding, Filling, Packaging).

### 11-3-workcenter-seed-data-INT-001: All 4 workcenters have daily_summaries for T-1 after seed-data.mjs runs
- Priority: P0
- Type: integration
- Given: A clean database with schema migrations applied and seed-data.mjs has been executed successfully
- When: daily_summaries are queried joined with assets, filtered by report_date = CURRENT_DATE - 1, grouped by area
- Then: Exactly 4 distinct area values are returned: "Roasting", "Grinding", "Filling", "Packaging"
- Data: All 14 assets must have at least one daily_summary row for T-1

### 11-3-workcenter-seed-data-INT-002: All 4 workcenters have daily_summaries for T-1 after 0021_seed_data.sql runs
- Priority: P0
- Type: integration
- Given: A clean database with schema migrations applied via `supabase db reset` (which runs 0021_seed_data.sql)
- When: daily_summaries are queried joined with assets, filtered by report_date = CURRENT_DATE - 1, grouped by area
- Then: Exactly 4 distinct area values are returned: "Roasting", "Grinding", "Filling", "Packaging"
- Data: All 14 assets must have at least one daily_summary row for T-1

### 11-3-workcenter-seed-data-UNIT-001: seed-data.mjs generates daily_summaries entries for all 14 asset IDs
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for analysis
- When: The daily_summaries data array is inspected
- Then: All 14 asset UUIDs (a0000001-...-000000000001 through ...0014) appear in daily_summaries entries with at least a T-1 (daysAgo(1)) row each
- Data: Asset IDs: Roasters (0001, 0002, 0003), Grinders (0004, 0005, 0006, 0007, 0014), Fillers (0008, 0009, 0010), Packaging (0011, 0012, 0013)

### 11-3-workcenter-seed-data-UNIT-002: 0021_seed_data.sql generates daily_summaries INSERT statements for all 14 asset IDs at T-1
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is loaded for analysis
- When: The INSERT INTO daily_summaries statements are parsed
- Then: All 14 asset UUIDs appear in daily_summaries inserts with at least one row using CURRENT_DATE - 1
- Data: Same 14 asset UUIDs as UNIT-001

### 11-3-workcenter-seed-data-E2E-001: Workcenter summary API endpoint returns data for all 4 workcenters after seeding
- Priority: P0
- Type: e2e
- Given: The database has been seeded via seed-data.mjs and the API server is running
- When: GET /api/v1/production/workcenter-summary?date=<yesterday> is called with valid authentication
- Then: The response contains a "workcenters" array with exactly 4 entries, one each for "Roasting", "Grinding", "Filling", and "Packaging", and report_date matches yesterday
- Data: Authentication via valid JWT; date parameter = yesterday's date in ISO format

### 11-3-workcenter-seed-data-INT-003: No workcenter is missing from T-1 data (negative check)
- Priority: P1
- Type: integration
- Given: The seed script has run successfully
- When: The set of distinct area values from daily_summaries for T-1 is compared against the expected set {"Roasting", "Grinding", "Filling", "Packaging"}
- Then: The symmetric difference is empty (no missing workcenters, no extra workcenters)
- Data: Expected exactly 4 workcenters, no more, no less


## AC2: Given the seed script runs successfully, When the data is queried per workcenter, Then each workcenter has 2-4 assets with varied performance (some hit target, some miss).

### 11-3-workcenter-seed-data-INT-004: Roasting workcenter has exactly 3 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Roasting'
- Then: COUNT(DISTINCT asset_id) = 3
- Data: Roaster 1 (0001), Roaster 2 (0002), Roaster 3 (0003)

### 11-3-workcenter-seed-data-INT-005: Grinding workcenter has exactly 5 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Grinding'
- Then: COUNT(DISTINCT asset_id) = 5
- Data: Grinder 1 (0004), Grinder 2 (0005), Grinder 3 (0006), Grinder 4 (0007), Grinder 5 (0014)

### 11-3-workcenter-seed-data-INT-006: Filling workcenter has exactly 3 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Filling'
- Then: COUNT(DISTINCT asset_id) = 3
- Data: Filler A (0008), Filler B (0009), Filler C (0010)

### 11-3-workcenter-seed-data-INT-007: Packaging workcenter has exactly 3 assets with T-1 daily_summaries
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: daily_summaries for T-1 are queried and joined with assets WHERE area = 'Packaging'
- Then: COUNT(DISTINCT asset_id) = 3
- Data: Packaging 1 (0011), Packaging 2 (0012), Packaging 3 (0013)

### 11-3-workcenter-seed-data-INT-008: Each workcenter has at least one asset that hits target on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: For each workcenter, daily_summaries for T-1 are queried and actual_output >= target_output is evaluated per asset
- Then: Every workcenter (Roasting, Grinding, Filling, Packaging) has at least 1 asset where actual_output >= target_output
- Data: Expected hit-target assets: Roaster 2, Grinder 1 or 2, Filler B or C, Packaging 1 or 2

### 11-3-workcenter-seed-data-INT-009: Each workcenter has at least one asset that misses target on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: For each workcenter, daily_summaries for T-1 are queried and actual_output < target_output is evaluated per asset
- Then: Every workcenter (Roasting, Grinding, Filling, Packaging) has at least 1 asset where actual_output < target_output
- Data: Expected miss-target assets: Roaster 1, Grinder 3 or 5, Filler A, Packaging 3

### 11-3-workcenter-seed-data-UNIT-003: seed-data.mjs daily_summaries data array contains varied actual_output vs target_output for T-1
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The daily_summaries entries for daysAgo(1) are examined per workcenter
- Then: Within each workcenter grouping, at least one asset has actual_output >= target_output and at least one has actual_output < target_output
- Data: Verify variation exists in the data definitions, not just in runtime behavior


## AC3: Given the seed data populates all workcenters, When attainment is calculated per workcenter, Then attainment ranges from ~70% to ~100% across workcenters to show realistic variation.

### 11-3-workcenter-seed-data-INT-010: Roasting workcenter attainment is approximately 88% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Roasting assets on T-1
- Then: Attainment is between 82% and 95% (centered around ~88%)
- Data: Roaster 1 ~87.5% OEE (misses target), Roaster 2 ~96% (hits), Roaster 3 ~89% (hits)

### 11-3-workcenter-seed-data-INT-011: Grinding workcenter attainment is approximately 83% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Grinding assets on T-1
- Then: Attainment is between 75% and 90% (centered around ~83%)
- Data: Grinder 2 excellent (95%+), Grinder 3 and 5 drag average, Grinder 1 decent, Grinder 4 moderate

### 11-3-workcenter-seed-data-INT-012: Filling workcenter attainment is approximately 80% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Filling assets on T-1
- Then: Attainment is between 70% and 88% (centered around ~80%)
- Data: Filler A problem child (~72%), Filler B and C solid performers

### 11-3-workcenter-seed-data-INT-013: Packaging workcenter attainment is approximately 88% on T-1
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SUM(actual_output) / SUM(target_output) * 100 is calculated for Packaging assets on T-1
- Then: Attainment is between 82% and 95% (centered around ~88%)
- Data: Packaging 1 and 2 solid, Packaging 3 slightly misses

### 11-3-workcenter-seed-data-INT-014: Cross-workcenter attainment spread covers ~70% to ~100% range
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: Attainment percentages are calculated for all 4 workcenters on T-1
- Then: The minimum workcenter attainment is <= 85% AND the maximum workcenter attainment is >= 85%, demonstrating meaningful spread. No workcenter is below 70% or above 100%.
- Data: Expected ordering approximately: Filling (~80%) < Grinding (~83%) < Roasting (~88%) ≈ Packaging (~88%)

### 11-3-workcenter-seed-data-UNIT-004: No individual asset attainment is unrealistically extreme
- Priority: P1
- Type: unit
- Given: Seed data is loaded
- When: actual_output / target_output is calculated for each of the 14 assets on T-1
- Then: No asset has attainment below 50% or above 110% (guarding against data entry errors in seed data)
- Data: All 14 assets checked individually


## AC4: Given the existing seed data assets already have area assignments, When the seed data is reviewed, Then all 14 assets are assigned to their correct workcenter area (Roasting: 3, Grinding: 5, Filling: 3, Packaging: 3).

### 11-3-workcenter-seed-data-UNIT-005: seed-data.mjs assets array assigns correct area to all 14 assets
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The assets array is inspected for area field assignments
- Then: Roasting has exactly 3 assets (Roaster 1, 2, 3), Grinding has exactly 5 assets (Grinder 1, 2, 3, 4, 5), Filling has exactly 3 assets (Filler A, B, C), Packaging has exactly 3 assets (Packaging 1, 2, 3)
- Data: Asset count per area: Roasting=3, Grinding=5, Filling=3, Packaging=3, total=14

### 11-3-workcenter-seed-data-UNIT-006: 0021_seed_data.sql assets INSERT assigns correct area to all 14 assets
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is analyzed
- When: The INSERT INTO assets statements are parsed for area values
- Then: Area assignments match: Roasting=3, Grinding=5, Filling=3, Packaging=3, total=14 assets
- Data: Same distribution as UNIT-005; UUIDs must match between .mjs and .sql

### 11-3-workcenter-seed-data-INT-015: Database query confirms correct asset counts per workcenter area
- Priority: P0
- Type: integration
- Given: Seed data has been loaded via either mechanism
- When: SELECT area, COUNT(*) FROM assets GROUP BY area is executed
- Then: Result set contains exactly: Roasting=3, Grinding=5, Filling=3, Packaging=3
- Data: Total asset count should be exactly 14

### 11-3-workcenter-seed-data-UNIT-007: Asset UUIDs are consistent between seed-data.mjs and 0021_seed_data.sql
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: The set of asset UUIDs in seed-data.mjs is compared with those in 0021_seed_data.sql
- Then: The UUID sets are identical (same 14 UUIDs) and each UUID maps to the same asset name and area in both files
- Data: UUID format a0000001-0000-0000-0000-000000000001 through ...0014

### 11-3-workcenter-seed-data-UNIT-008: No asset has a NULL or empty area assignment
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: All asset entries are inspected for the area field
- Then: Every asset has a non-null, non-empty area value that is one of: "Roasting", "Grinding", "Filling", "Packaging"
- Data: Check all 14 assets in both files


## AC5: Given all assets exist in the assets table with area values, When shift_targets are queried, Then every asset has at least one shift target record so the workcenter scorecard can compute attainment.

### 11-3-workcenter-seed-data-INT-016: Every asset has at least one shift_target record after seeding
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SELECT a.id, a.name, COUNT(st.id) as target_count FROM assets a LEFT JOIN shift_targets st ON a.id = st.asset_id GROUP BY a.id, a.name is executed
- Then: Every asset (14 total) has target_count >= 1; no asset has 0 shift_target records
- Data: All 14 asset IDs must appear with at least one shift_target

### 11-3-workcenter-seed-data-UNIT-009: seed-data.mjs contains a shift_targets upsert/insert block
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The script is searched for shift_targets data insertion code
- Then: A shift_targets insert or upsert block exists that covers all 14 asset UUIDs
- Data: Previously this block was completely absent from seed-data.mjs; story 11.3 must add it

### 11-3-workcenter-seed-data-UNIT-010: 0021_seed_data.sql contains shift_targets INSERT for all 14 assets
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is analyzed
- When: The INSERT INTO shift_targets statements are parsed for distinct asset_id values
- Then: All 14 asset UUIDs appear in shift_targets INSERT statements
- Data: Each asset needs at least one row (morning, afternoon, and/or night shift)

### 11-3-workcenter-seed-data-INT-017: All workcenters have shift_target coverage
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: SELECT a.area, COUNT(DISTINCT st.asset_id) FROM shift_targets st JOIN assets a ON a.id = st.asset_id GROUP BY a.area is executed
- Then: Roasting=3, Grinding=5, Filling=3, Packaging=3 (all assets in each workcenter have targets)
- Data: Same distribution as asset counts per workcenter

### 11-3-workcenter-seed-data-INT-018: shift_targets have valid target_output values (> 0)
- Priority: P1
- Type: integration
- Given: Seed data has been loaded
- When: SELECT * FROM shift_targets WHERE target_output <= 0 is executed
- Then: Zero rows returned (all shift targets have positive target_output values)
- Data: target_output column is INTEGER NOT NULL, but values must also be positive

### 11-3-workcenter-seed-data-UNIT-011: seed-data.mjs handles shift_targets cleanup to prevent duplicates on re-run
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The shift_targets insertion section is inspected
- Then: A delete-before-insert or equivalent idempotency pattern exists for shift_targets (since the table has no unique constraint for upsert)
- Data: Pattern should match existing cleanup approach used for live_snapshots and safety_events

### 11-3-workcenter-seed-data-INT-019: Running seed-data.mjs twice does not create duplicate shift_target rows
- Priority: P0
- Type: integration
- Given: seed-data.mjs has been run once successfully
- When: seed-data.mjs is run a second time
- Then: The total number of shift_target rows is the same as after the first run (no duplicates created)
- Data: COUNT(*) FROM shift_targets should be identical after both runs


## AC6: Given daily_summaries and shift_targets exist for all assets, When the target_output in daily_summaries is compared to shift_targets.target_output, Then the values are aligned so that the workcenter summary API endpoint (Story 11.1) can use either source consistently without conflicting numbers.

### 11-3-workcenter-seed-data-INT-020: daily_summaries.target_output equals sum of shift_targets.target_output for each asset
- Priority: P0
- Type: integration
- Given: Seed data has been loaded with both daily_summaries and shift_targets
- When: For each asset, daily_summaries.target_output (for T-1) is compared against SUM(shift_targets.target_output) for that asset
- Then: The values are equal for all 14 assets (daily target = sum of all shift targets for that asset)
- Data: Roaster 1/2/3: 143 = 50+48+45; Grinder 1/2: 1950 = 1000+950; Grinder 3: 1950 = 900+1050; Grinder 4: 1950 = 850+1100; Grinder 5: 1950 = 1000+950; Filler A: 4600 = 2400+2200; Filler B: 4600 = 2400+2200; Filler C: 4000 = 2000+2000; Pack 1: 6200 = 3200+3000; Pack 2: 6200 = 3200+3000; Pack 3: 5600 = 2800+2800

### 11-3-workcenter-seed-data-UNIT-012: Roaster shift_targets sum to 143 in seed-data.mjs (previously mismatched)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: The shift_targets entries for Roaster 1, 2, and 3 are inspected
- Then: Each roaster's shift_targets sum to exactly 143 (matching daily_summaries.target_output = 143)
- Data: Expected: morning=50, afternoon=48, night=45 (sum=143) for each roaster. Previously Roasters summed to 93 (48+45) -- a known mismatch

### 11-3-workcenter-seed-data-UNIT-013: Roaster shift_targets sum to 143 in 0021_seed_data.sql (previously mismatched)
- Priority: P0
- Type: unit
- Given: The 0021_seed_data.sql file is analyzed
- When: The INSERT INTO shift_targets for Roaster 1, 2, and 3 are parsed and their target_output values summed
- Then: Each roaster's shift_targets sum to exactly 143
- Data: Same expected values as UNIT-012

### 11-3-workcenter-seed-data-UNIT-014: All Grinder shift_targets sum to their respective daily targets
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: Shift target values for Grinders 1-5 are summed per asset
- Then: Each grinder's shift_targets sum to 1950 (matching daily_summaries.target_output)
- Data: Grinder 1: 1000+950=1950, Grinder 2: 1000+950=1950, Grinder 3: 900+1050=1950, Grinder 4: 850+1100=1950, Grinder 5: 1000+950=1950

### 11-3-workcenter-seed-data-UNIT-015: All Filler shift_targets sum to their respective daily targets
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: Shift target values for Fillers A, B, C are summed per asset
- Then: Filler A: sum=4600, Filler B: sum=4600, Filler C: sum=4000 (matching respective daily_summaries.target_output)
- Data: Filler A: 2400+2200, Filler B: 2400+2200, Filler C: 2000+2000

### 11-3-workcenter-seed-data-UNIT-016: All Packaging shift_targets sum to their respective daily targets
- Priority: P1
- Type: unit
- Given: Both seed files are analyzed
- When: Shift target values for Packaging 1, 2, 3 are summed per asset
- Then: Pack 1: sum=6200, Pack 2: sum=6200, Pack 3: sum=5600 (matching respective daily_summaries.target_output)
- Data: Pack 1: 3200+3000, Pack 2: 3200+3000, Pack 3: 2800+2800

### 11-3-workcenter-seed-data-UNIT-017: target_output values are consistent across all 7 days per asset in seed-data.mjs
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source is analyzed
- When: daily_summaries entries for each asset across T-1 through T-7 are inspected
- Then: The target_output value is the same for every day for a given asset (targets don't change day-to-day)
- Data: Each asset uses a fixed daily target: Roasters=143, Grinders=1950, Filler A/B=4600, Filler C=4000, Pack 1/2=6200, Pack 3=5600

### 11-3-workcenter-seed-data-INT-021: Alignment query returns zero mismatches
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: A query compares daily_summaries.target_output for T-1 against the SUM of shift_targets.target_output for each asset: SELECT a.name, ds.target_output as daily_target, SUM(st.target_output) as shift_sum FROM daily_summaries ds JOIN assets a ON a.id = ds.asset_id JOIN shift_targets st ON st.asset_id = ds.asset_id WHERE ds.report_date = CURRENT_DATE - 1 GROUP BY a.name, ds.target_output HAVING ds.target_output != SUM(st.target_output)
- Then: Zero rows returned (no mismatches)
- Data: All 14 assets should have perfectly aligned targets

### 11-3-workcenter-seed-data-UNIT-018: Both seed files use identical target_output values for the same assets
- Priority: P0
- Type: unit
- Given: Both seed-data.mjs and 0021_seed_data.sql are analyzed
- When: The daily_summaries.target_output and shift_targets.target_output values are extracted from both files for each asset
- Then: The values match exactly between the two files for every asset
- Data: Cross-reference all 14 assets' target values across both files


## Additional Coverage: Data Completeness (7-day coverage)

### 11-3-workcenter-seed-data-INT-022: All 14 assets have daily_summaries for T-1 through T-7
- Priority: P1
- Type: integration
- Given: Seed data has been loaded
- When: SELECT a.name, COUNT(ds.id) as day_count FROM assets a LEFT JOIN daily_summaries ds ON a.id = ds.asset_id WHERE ds.report_date >= CURRENT_DATE - 7 AND ds.report_date <= CURRENT_DATE - 1 GROUP BY a.name is executed
- Then: Every asset has day_count = 7 (full 7-day coverage)
- Data: Previously missing: Roaster 3 (0 days), Grinder 4 (0 days), Filler C (0 days), Packaging 3 (0 days), Filler B (only 2), Packaging 2 (only 2)

### 11-3-workcenter-seed-data-INT-023: seed-data.mjs executes without errors
- Priority: P0
- Type: integration
- Given: A running Supabase instance with schema migrations applied
- When: `node scripts/seed-data.mjs` (or `node _bmad/scripts/seed-data.mjs`) is executed
- Then: The script completes with exit code 0 and no error output
- Data: Requires SUPABASE_URL and SUPABASE_KEY environment variables


edge_cases:
  - Running seed-data.mjs multiple times in succession produces identical data (idempotency) -- covered by INT-019
  - Asset with no shift_targets should not cause division-by-zero in attainment calculation (prevented by AC5)
  - Filler C and Packaging 3 have different target_output values than their workcenter peers (4000 vs 4600 and 5600 vs 6200) -- ensure attainment calculations handle non-uniform targets correctly
  - Roaster 3 shift_targets previously summed to 84 (42+42) which didn't match any known daily target -- must be corrected to sum to 143
  - The daily_summaries unique constraint on (asset_id, report_date) means duplicate inserts should be handled gracefully via upsert
  - SQL migration uses CURRENT_DATE - N which shifts with time, so test assertions should use relative dates not absolute dates
  - shift_targets table has NO unique constraint -- repeated inserts will create duplicates unless explicitly handled

error_scenarios:
  - Seed script runs against database missing schema migrations (assets table doesn't exist) -- should fail with clear error, not silently skip
  - Seed script runs with invalid/missing Supabase credentials -- should fail with authentication error
  - Partial seed failure mid-execution (e.g., first 7 assets seed, then connection drops) -- on re-run, upsert should recover gracefully for daily_summaries; shift_targets delete-then-insert should also recover
  - Database has stale seed data from previous schema version (e.g., column renamed) -- script should fail with clear column mismatch error rather than inserting into wrong columns
  - shift_targets insert attempted for an asset_id that doesn't exist yet (foreign key violation) -- seed ordering must ensure assets are inserted before shift_targets

test_file_mapping:
  - 11-3-workcenter-seed-data-E2E-*: apps/api/tests/api/test_workcenter_seed_e2e.py
  - 11-3-workcenter-seed-data-UNIT-*: supabase/tests/seed-data-validation.test.ts
  - 11-3-workcenter-seed-data-INT-*: supabase/tests/seed-data-integration.test.ts

TEST SPEC END
