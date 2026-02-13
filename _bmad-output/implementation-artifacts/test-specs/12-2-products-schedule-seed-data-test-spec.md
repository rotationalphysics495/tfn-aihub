TEST SPEC START
story_id: 12-2-products-schedule-seed-data
generated: 2026-02-11

test_specifications:

## AC1: Given the seed script runs after the migration, When the products table is queried, Then ~10 coffee manufacturing products exist with correct families (Roasting: 5, Grinding: 3, Filling: 3)

### 12-2-products-schedule-seed-data-UNIT-001: seed-data.mjs defines exactly 11 products with deterministic UUIDs
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The products constant array is inspected
- Then: Exactly 11 product objects are defined, each with id, name, sku, product_family, and unit_of_measure fields, AND all ids follow the pattern `p0000001-0000-0000-0000-00000000XXXX`
- Data: Expected product IDs p0000001-0000-0000-0000-000000000001 through ...000000000011

### 12-2-products-schedule-seed-data-UNIT-002: Products array contains exactly 5 Roasting products
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The products array is filtered by product_family === 'Roasting'
- Then: Exactly 5 products are found: Colombian Single Origin, Brazilian Santos, Ethiopian Yirgacheffe, House Blend, Dark Roast Blend, AND all have unit_of_measure === 'lbs'
- Data: SKU prefixes RST-COL, RST-BRZ, RST-ETH, RST-HBL, RST-DRK

### 12-2-products-schedule-seed-data-UNIT-003: Products array contains exactly 3 Grinding products
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The products array is filtered by product_family === 'Grinding'
- Then: Exactly 3 products are found: Espresso Grind, Medium Grind, Coarse Grind, AND all have unit_of_measure === 'lbs'
- Data: SKU prefixes GRN-ESP, GRN-MED, GRN-CRS

### 12-2-products-schedule-seed-data-UNIT-004: Products array contains exactly 3 Filling products
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The products array is filtered by product_family === 'Filling'
- Then: Exactly 3 products are found: K-Cup, 12oz Bag, 5lb Bag, AND all have unit_of_measure === 'units'
- Data: SKU prefixes FIL-KCP, FIL-12B, FIL-5LB

### 12-2-products-schedule-seed-data-UNIT-005: All 11 product IDs are unique and deterministic
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: All product id values are extracted from the products array
- Then: Exactly 11 distinct UUIDs are found AND they follow the deterministic pattern `p0000001-0000-0000-0000-00000000XXXX` AND no duplicates exist
- Data: 11 unique UUID strings

### 12-2-products-schedule-seed-data-UNIT-006: Products upsert uses onConflict 'id' for idempotency
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The products insertion code is inspected
- Then: The script uses `supabase.from('products').upsert(data, { onConflict: 'id' })` pattern
- Data: String pattern matching for upsert with onConflict

### 12-2-products-schedule-seed-data-INT-001: Products table contains exactly 11 products after seeding
- Priority: P0
- Type: integration
- Given: The database has migration 0026 applied AND seed-data.mjs has been executed
- When: `SELECT COUNT(*) FROM products` is executed
- Then: Count equals 11
- Data: Requires running Supabase instance with seed data loaded

### 12-2-products-schedule-seed-data-INT-002: Products table has correct product_family distribution (Roasting:5, Grinding:3, Filling:3)
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: `SELECT product_family, COUNT(*) FROM products GROUP BY product_family` is executed
- Then: Roasting = 5, Grinding = 3, Filling = 3
- Data: Exactly 3 product_family values, 11 total rows

### 12-2-products-schedule-seed-data-INT-003: All expected product names exist in products table
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: Products table is queried for all names
- Then: All 11 names are present: Colombian Single Origin, Brazilian Santos, Ethiopian Yirgacheffe, House Blend, Dark Roast Blend, Espresso Grind, Medium Grind, Coarse Grind, K-Cup, 12oz Bag, 5lb Bag
- Data: Set comparison of expected vs actual product names

### 12-2-products-schedule-seed-data-INT-004: Re-running seed script does not duplicate products (idempotency)
- Priority: P0
- Type: integration
- Given: Seed data has been loaded once
- When: Seed script is run a second time, then `SELECT COUNT(*) FROM products` is executed
- Then: Count still equals 11 (no duplicates created)
- Data: Deterministic UUIDs ensure upsert overwrites rather than duplicates


## AC2: Given the production schedule is queried for the past 7 days, When results are returned, Then each asset has daily schedule entries with realistic product assignments logically mapped to workcenters

### 12-2-products-schedule-seed-data-UNIT-007: Production schedule entries exist for 7 days (daysAgo 1-7) across all 11 non-packaging assets
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The productionSchedule array is inspected
- Then: Schedule entries exist for each of the 11 non-packaging assets (Roaster 1-3, Grinder 1-5, Filler A-C) for daysAgo(1) through daysAgo(7)
- Data: 11 assets × 7 days = minimum 77 asset-day combinations (more if shift-level entries)

### 12-2-products-schedule-seed-data-UNIT-008: Roasting products are only assigned to Roaster assets (001-003)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: All production schedule entries with Roasting product IDs (p0000001-...-001 through -005) are inspected
- Then: Every entry references an asset_id from {a0000001-...-001, -002, -003} (Roasters only), AND no Roasting product appears on any Grinder, Filler, or Packaging asset
- Data: Cross-reference product_id to asset_id within schedule entries

### 12-2-products-schedule-seed-data-UNIT-009: Grinding products are only assigned to Grinder assets (004-007, 014)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: All production schedule entries with Grinding product IDs (p0000001-...-006 through -008) are inspected
- Then: Every entry references an asset_id from {a0000001-...-004, -005, -006, -007, -014} (Grinders only)
- Data: Cross-reference product_id to asset_id within schedule entries

### 12-2-products-schedule-seed-data-UNIT-010: Filling products are only assigned to Filler assets (008-010)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: All production schedule entries with Filling product IDs (p0000001-...-009 through -011) are inspected
- Then: Every entry references an asset_id from {a0000001-...-008, -009, -010} (Fillers only)
- Data: Cross-reference product_id to asset_id within schedule entries

### 12-2-products-schedule-seed-data-UNIT-011: No schedule entries exist for Packaging assets (011-013)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The production schedule entries are searched for asset IDs a0000001-...-000000000011, -012, -013
- Then: Zero schedule entries reference Packaging Line 1, 2, or 3
- Data: Negative assertion on packaging asset IDs in schedule array

### 12-2-products-schedule-seed-data-UNIT-012: Schedule entries include shift assignments (Day/Night)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The productionSchedule array is inspected for shift values
- Then: At least some entries include shift: 'Day' and shift: 'Night' values
- Data: Both shift values should appear in the schedule data

### 12-2-products-schedule-seed-data-UNIT-013: Schedule quantities are realistic for each asset type
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: Scheduled quantities are examined per asset family
- Then: Roaster scheduled quantities are approximately 130-143 lbs/day, Grinder quantities approximately 1,800-1,950 lbs/day, Filler quantities approximately 4,100-4,600 units/day
- Data: Quantities per schedule entry (or per Day+Night shift pair if split) should fall in realistic ranges

### 12-2-products-schedule-seed-data-UNIT-014: Schedule uses deterministic UUIDs for idempotent re-runs
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The schedule entry IDs are inspected
- Then: All schedule entry IDs are hardcoded deterministic UUIDs (not generated at runtime), AND all IDs are unique
- Data: UUID pattern consistency check across all schedule entries

### 12-2-products-schedule-seed-data-UNIT-015: Schedule includes weekly product rotation patterns
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: Schedule entries for a single asset (e.g., Roaster 1) are inspected across 7 days
- Then: At least one asset changes products mid-week (e.g., Colombian Mon-Wed, Brazilian Thu-Fri), demonstrating realistic scheduling rotation
- Data: Product_id changes for at least one asset across the 7-day window

### 12-2-products-schedule-seed-data-INT-005: Production schedule table has entries for all 11 non-packaging assets
- Priority: P0
- Type: integration
- Given: Seed data has been loaded into a running Supabase instance
- When: `SELECT DISTINCT asset_id FROM production_schedule` is executed
- Then: Exactly 11 distinct asset IDs are returned (Roasters 1-3, Grinders 1-5, Fillers A-C), AND none are packaging asset IDs
- Data: Expected asset IDs match the 11 non-packaging UUIDs

### 12-2-products-schedule-seed-data-INT-006: Production schedule covers 7 days for each asset
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: `SELECT asset_id, COUNT(DISTINCT scheduled_date) FROM production_schedule GROUP BY asset_id` is executed
- Then: Each of the 11 assets has scheduled_date entries spanning 7 distinct dates (daysAgo 1 through 7)
- Data: 7 distinct dates per asset

### 12-2-products-schedule-seed-data-INT-007: Product-to-workcenter mapping is enforced — no cross-family assignments
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: production_schedule is joined with products and assets, then checked for cross-family assignments
- Then: Every schedule entry where the product's product_family is 'Roasting' has an asset in area 'Roasting', every 'Grinding' product maps to 'Grinding' area, every 'Filling' product maps to 'Filling' area. Zero cross-family violations.
- Data: JOIN production_schedule ps JOIN products p ON ps.product_id = p.id JOIN assets a ON ps.asset_id = a.id; validate p.product_family corresponds to a.area

### 12-2-products-schedule-seed-data-INT-008: Re-running seed script does not duplicate schedule entries (idempotency)
- Priority: P0
- Type: integration
- Given: Seed data has been loaded once
- When: Seed script is run a second time, then `SELECT COUNT(*) FROM production_schedule` is executed
- Then: The count is the same as after the first run (no duplicates)
- Data: Deterministic UUIDs with upsert ensure idempotency


## AC3: Given the production actuals are queried, When compared against the schedule, Then variance patterns exist (on-schedule ~60%, product swaps ~15%, underproduction ~25%)

### 12-2-products-schedule-seed-data-UNIT-016: Production actuals entries exist for all 11 non-packaging assets across 7 days
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The productionActuals array is inspected
- Then: Actual entries exist for each of the 11 non-packaging assets for daysAgo(1) through daysAgo(7), with corresponding schedule entries
- Data: Same 11 assets and 7 days as schedule entries

### 12-2-products-schedule-seed-data-UNIT-017: Approximately 60% of actuals are on-schedule (same product, quantity within +/-5%)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: Each production actual entry is compared against its corresponding schedule entry
- Then: Approximately 60% of actuals have the same product_id as the schedule AND actual_quantity is within +/-5% of scheduled_quantity. The on-schedule percentage should be between 50% and 70%.
- Data: Cross-reference actuals to schedule by asset_id + date + shift

### 12-2-products-schedule-seed-data-UNIT-018: Approximately 15% of actuals are product swaps (different product_id than scheduled)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: Each production actual entry is compared against its corresponding schedule entry
- Then: Approximately 15% of actuals have a different product_id than the schedule entry for the same asset/date/shift. The swap percentage should be between 10% and 25%.
- Data: Product swap = actual product_id != scheduled product_id for same asset/date/shift

### 12-2-products-schedule-seed-data-UNIT-019: Approximately 25% of actuals are underproduction (same product, 60-85% of scheduled quantity)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: Each production actual entry is compared against its corresponding schedule entry
- Then: Approximately 25% of actuals have the same product_id as the schedule AND actual_quantity is between 60% and 85% of scheduled_quantity. The underproduction percentage should be between 15% and 35%.
- Data: Underproduction = same product_id AND actual_quantity/scheduled_quantity between 0.60 and 0.85

### 12-2-products-schedule-seed-data-UNIT-020: daysAgo(1) Roaster 1 has a product swap (Brazilian instead of Colombian)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The production actual for Roaster 1 (asset a0000001-...-001) on daysAgo(1) is compared to the schedule
- Then: The schedule shows Colombian Single Origin (p0000001-...-001) but the actual shows Brazilian Santos (p0000001-...-002) — a product swap
- Data: Specific scenario from story spec

### 12-2-products-schedule-seed-data-UNIT-021: daysAgo(1) Grinder 5 shows underproduction (actual ~1608 total)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The production actuals for Grinder 5 (asset a0000001-...-014) on daysAgo(1) are summed
- Then: The total actual_quantity is approximately 1,608 (matching existing daily_summaries actual_output), which is significantly below the scheduled quantity of ~1,900
- Data: Sum of actuals for Grinder 5 on daysAgo(1) should be approximately 1,608 (+/- 50)

### 12-2-products-schedule-seed-data-UNIT-022: daysAgo(2) Filler A exceeds K-Cup target
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The production actual for Filler A (asset a0000001-...-008) on daysAgo(2) is inspected
- Then: The actual_quantity exceeds the scheduled_quantity for K-Cups (overproduction scenario)
- Data: actual_quantity > scheduled_quantity for at least one shift entry

### 12-2-products-schedule-seed-data-UNIT-023: daysAgo(3) has multiple product swaps across grinders
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: Production actuals for all Grinder assets on daysAgo(3) are compared to their schedule
- Then: At least 2 different grinder assets show product swaps (different product_id than scheduled)
- Data: Multiple grinder swap scenario per story spec "bean availability issues"

### 12-2-products-schedule-seed-data-UNIT-024: At least one shift-level variance exists (Day on-target, Night underproduced)
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: Production actuals with shift = 'Day' and shift = 'Night' are compared for the same asset and date
- Then: At least one asset/date combination shows the Day shift actual within +/-5% of scheduled AND the Night shift actual at 60-85% of scheduled (or vice versa)
- Data: Demonstrates shift-level granularity of variance patterns

### 12-2-products-schedule-seed-data-UNIT-025: Actuals use deterministic UUIDs for idempotent re-runs
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The actuals entry IDs are inspected
- Then: All actuals entry IDs are hardcoded deterministic UUIDs (not generated at runtime), AND all IDs are unique
- Data: UUID pattern consistency check across all actuals entries

### 12-2-products-schedule-seed-data-UNIT-026: Actuals sums per asset per date are broadly consistent with daily_summaries actual_output
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: For each asset and date, the SUM of production_actuals.actual_quantity is compared against the daily_summaries.actual_output value in the same seed file
- Then: The sums are within +/-10% of each other (or exactly equal for single-product-per-day scenarios), ensuring data consistency across seed data sections
- Data: Cross-reference productionActuals sums with dailySummaries actual_output values for same asset_id and date

### 12-2-products-schedule-seed-data-INT-009: Production actuals table has entries for all 11 non-packaging assets
- Priority: P0
- Type: integration
- Given: Seed data has been loaded into a running Supabase instance
- When: `SELECT DISTINCT asset_id FROM production_actuals` is executed
- Then: Exactly 11 distinct asset IDs are returned (no packaging assets)
- Data: Expected 11 non-packaging asset UUIDs

### 12-2-products-schedule-seed-data-INT-010: Production actuals cover 7 days for each asset
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: `SELECT asset_id, COUNT(DISTINCT production_date) FROM production_actuals GROUP BY asset_id` is executed
- Then: Each of the 11 assets has production_date entries spanning 7 distinct dates
- Data: 7 distinct dates per asset

### 12-2-products-schedule-seed-data-INT-011: Product swap variance exists in actuals data
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: production_actuals is joined with production_schedule on (asset_id, production_date/scheduled_date, shift) and product_id is compared
- Then: At least 10% of joined rows have different product_id values (actuals product != scheduled product), confirming product swap scenarios exist
- Data: JOIN on asset_id + date + shift; compare product_id fields

### 12-2-products-schedule-seed-data-INT-012: Underproduction variance exists in actuals data
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: production_actuals is joined with production_schedule on (asset_id, date, shift) where product_id matches
- Then: At least 15% of on-product rows have actual_quantity < 0.90 * scheduled_quantity, confirming underproduction scenarios
- Data: Same-product entries where actual is significantly below scheduled

### 12-2-products-schedule-seed-data-INT-013: On-schedule entries exist in actuals data
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: production_actuals is joined with production_schedule on (asset_id, date, shift) where product_id matches
- Then: At least 40% of joined rows have same product_id AND actual_quantity within +/-5% of scheduled_quantity
- Data: On-schedule = same product AND quantity ratio between 0.95 and 1.05

### 12-2-products-schedule-seed-data-INT-014: Actuals sums per asset per date approximately match daily_summaries.actual_output
- Priority: P0
- Type: integration
- Given: Seed data has been loaded
- When: For each non-packaging asset and each date in the past 7 days, SUM(production_actuals.actual_quantity) is compared against daily_summaries.actual_output
- Then: The values are within +/-15% of each other for all asset/date combinations. The vast majority (>80%) are within +/-10%.
- Data: JOIN daily_summaries with aggregated production_actuals; compare values

### 12-2-products-schedule-seed-data-INT-015: Re-running seed script does not duplicate actuals entries (idempotency)
- Priority: P0
- Type: integration
- Given: Seed data has been loaded once
- When: Seed script is run a second time, then `SELECT COUNT(*) FROM production_actuals` is executed
- Then: The count is the same as after the first run
- Data: Deterministic UUIDs with upsert ensure idempotency


## Additional Coverage: FK Safety & Clear/Reset

### 12-2-products-schedule-seed-data-UNIT-027: Delete statements clear tables in correct FK-safe order
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The "Clear existing data" section is inspected for products/schedule/actuals delete statements
- Then: production_actuals is deleted BEFORE production_schedule, which is deleted BEFORE products (reverse FK dependency order)
- Data: Line order analysis of delete statements in the clearing section

### 12-2-products-schedule-seed-data-UNIT-028: Insert statements follow correct FK-safe order
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The insert/upsert sections for products, schedule, and actuals are inspected
- Then: Products are upserted BEFORE production_schedule, which is upserted BEFORE production_actuals (FK dependency order)
- Data: Section order analysis within the script

### 12-2-products-schedule-seed-data-UNIT-029: Seed section follows existing numbered comment pattern
- Priority: P1
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The new products/schedule/actuals section is inspected
- Then: It uses a numbered section comment like `// 5.5. Products, Schedule & Actuals (Epic 12)` AND is placed after the safety events section and before the test users section
- Data: Section comment pattern and placement validation

### 12-2-products-schedule-seed-data-UNIT-030: All FK references in schedule entries point to valid asset and product IDs
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: All asset_id and product_id values in productionSchedule are extracted
- Then: Every asset_id matches one of the 14 defined asset UUIDs AND every product_id matches one of the 11 defined product UUIDs
- Data: Cross-reference schedule FK values against defined constants

### 12-2-products-schedule-seed-data-UNIT-031: All FK references in actuals entries point to valid asset and product IDs
- Priority: P0
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: All asset_id and product_id values in productionActuals are extracted
- Then: Every asset_id matches one of the 14 defined asset UUIDs AND every product_id matches one of the 11 defined product UUIDs
- Data: Cross-reference actuals FK values against defined constants

### 12-2-products-schedule-seed-data-UNIT-032: Console logging follows emoji-prefixed pattern
- Priority: P2
- Type: unit
- Given: The seed-data.mjs script source code is loaded for static analysis
- When: The new products/schedule/actuals sections are inspected for console.log statements
- Then: Each major section (products insert, schedule insert, actuals insert) has emoji-prefixed console.log output following existing patterns
- Data: String pattern matching for console.log with emoji prefixes

### 12-2-products-schedule-seed-data-E2E-001: Full seed script runs without errors after migration 0026
- Priority: P0
- Type: e2e
- Given: A running Supabase instance with all migrations applied including 0026_products_and_schedule.sql
- When: `node _bmad/scripts/seed-data.mjs` is executed
- Then: The script completes with exit code 0 and no error output, AND all three tables (products, production_schedule, production_actuals) contain data
- Data: Requires SUPABASE_URL and SUPABASE_KEY environment variables


edge_cases:
  - Running seed-data.mjs multiple times in succession produces identical data counts (idempotency via deterministic UUIDs + upsert) — covered by INT-004, INT-008, INT-015
  - Product swap actuals reference product IDs from different product families than scheduled — FK integrity still valid since all products are inserted first — covered by UNIT-018, UNIT-030, UNIT-031
  - daysAgo() helper generates different absolute dates each day the script runs — schedule/actuals dates shift forward with time, so test assertions must use relative dates — covered by using daysAgo() in assertions
  - Grinder 5 uses asset ID a0000001-...-000000000014 (not sequential with 004-007) — tests must include this non-sequential ID — covered in all asset ID constants
  - Schedule entries with both Day and Night shifts for the same asset/date — must be handled as separate rows, not merged — covered by UNIT-012, UNIT-024
  - Filler C has a lower daily target (4,000 vs 4,600 for A/B) — schedule quantities should reflect this difference — covered by UNIT-013
  - Product swap scenarios where a Roasting product swaps for another Roasting product (not a cross-family swap) — this is the expected behavior, swaps stay within the same product family
  - An asset might have overproduction (actual > scheduled) in some entries — this is allowed and realistic, particularly for the Filler A daysAgo(2) scenario — covered by UNIT-022
  - If migration 0026 has not been applied, all three table inserts will fail — the script should log errors but not crash the entire seed process

error_scenarios:
  - Seed script runs against database missing migration 0026 (products, production_schedule, production_actuals tables don't exist) — should fail with "relation does not exist" error, not silently skip
  - Seed script runs with invalid/missing Supabase credentials — should fail with authentication error
  - Schedule entry references a non-existent product_id UUID — should fail with FK violation (prevented by inserting products first)
  - Actuals entry references a non-existent asset_id UUID — should fail with FK violation (prevented by assets being pre-seeded)
  - Deleting products before deleting schedule/actuals would cause FK cascade — prevented by correct delete order (actuals first, then schedule, then products)
  - Partial seed failure mid-execution (e.g., products insert succeeds but schedule insert fails) — on re-run, upsert should recover gracefully
  - Running seed with a product table that has additional non-seed products — delete-before-insert pattern should clear all products, potentially removing non-seed data (acceptable for seed script behavior)

test_file_mapping:
  - 12-2-products-schedule-seed-data-UNIT-*: supabase/tests/products-schedule-seed-validation.test.ts
  - 12-2-products-schedule-seed-data-INT-*: supabase/tests/products-schedule-seed-integration.test.ts
  - 12-2-products-schedule-seed-data-E2E-*: Manual verification via seed script execution or supabase/tests/products-schedule-seed-integration.test.ts

TEST SPEC END
