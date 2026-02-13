TEST SPEC START
story_id: 12-1-products-schedule-data-model
generated: 2026-02-11

test_specifications:

## AC1: Products Table Created — GIVEN the migration runs successfully, WHEN the `products` table is queried, THEN the table exists with columns id (UUID PK), name (TEXT NOT NULL), sku (TEXT nullable), product_family (TEXT), unit_of_measure (TEXT DEFAULT 'units'), created_at (TIMESTAMPTZ DEFAULT NOW()), updated_at (TIMESTAMPTZ DEFAULT NOW()), AND the update_updated_at_column() trigger is attached

### 12-1-products-schedule-data-model-UNIT-001: Migration creates products table with CREATE TABLE IF NOT EXISTS
- Priority: P0
- Type: unit
- Given: The migration file 0026_products_and_schedule.sql exists and is readable
- When: The migration SQL content is inspected
- Then: It contains `CREATE TABLE IF NOT EXISTS products` statement
- Data: Migration file at supabase/migrations/0026_products_and_schedule.sql

### 12-1-products-schedule-data-model-UNIT-002: Products table has id UUID primary key with gen_random_uuid()
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: The `id` column is defined as `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: Regex match within products table definition block

### 12-1-products-schedule-data-model-UNIT-003: Products table has name column as TEXT NOT NULL
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: The `name` column is defined as `TEXT NOT NULL`
- Data: Regex match within products table definition block

### 12-1-products-schedule-data-model-UNIT-004: Products table has sku column as nullable TEXT
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: The `sku` column is defined as `TEXT` without NOT NULL constraint (nullable for initial seed data)
- Data: Regex match confirming TEXT type and absence of NOT NULL

### 12-1-products-schedule-data-model-UNIT-005: Products table has product_family column as TEXT
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: The `product_family` column is defined as `TEXT`
- Data: Regex match within products table definition block

### 12-1-products-schedule-data-model-UNIT-006: Products table has unit_of_measure column as TEXT DEFAULT 'units'
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: The `unit_of_measure` column is defined as `TEXT DEFAULT 'units'`
- Data: Regex match for column name, type, and default value

### 12-1-products-schedule-data-model-UNIT-007: Products table has created_at TIMESTAMPTZ DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: The `created_at` column is defined as `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`
- Data: Regex match within products table definition block

### 12-1-products-schedule-data-model-UNIT-008: Products table has updated_at TIMESTAMPTZ DEFAULT NOW()
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: The `updated_at` column is defined as `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`
- Data: Regex match within products table definition block

### 12-1-products-schedule-data-model-UNIT-009: Products table has update_updated_at_column trigger
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The trigger definitions are inspected
- Then: A trigger `DROP TRIGGER IF EXISTS` followed by `CREATE TRIGGER` is defined on the `products` table executing `update_updated_at_column()` function AND the function is NOT recreated (only referenced)
- Data: Regex match for trigger referencing products table and update_updated_at_column function

### 12-1-products-schedule-data-model-UNIT-010: Products table does NOT use uuid_generate_v4()
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: The entire migration SQL is inspected
- Then: The string `uuid_generate_v4()` does NOT appear anywhere in the migration file
- Data: Negative assertion on migration content

### 12-1-products-schedule-data-model-UNIT-011: Products table does NOT use VARCHAR
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: The products table definition is inspected
- Then: No VARCHAR type is used — all string columns use TEXT
- Data: Negative assertion for VARCHAR within the products table block

### 12-1-products-schedule-data-model-E2E-001: Products table accepts valid insert via service_role
- Priority: P0
- Type: e2e
- Given: The migration has been applied and the products table exists
- When: A row is inserted with name='Colombian Single Origin', sku='COL-SO-12OZ', product_family='Single Origin', unit_of_measure='lbs'
- Then: The row is inserted successfully AND id is auto-generated as UUID AND created_at and updated_at are populated with current timestamp
- Data: Full product record with all columns populated

### 12-1-products-schedule-data-model-E2E-002: Products table enforces name NOT NULL constraint
- Priority: P0
- Type: e2e
- Given: The migration has been applied and the products table exists
- When: A row is inserted with name=NULL
- Then: The insert fails with a NOT NULL constraint violation error
- Data: Product record with null name field

### 12-1-products-schedule-data-model-E2E-003: Products table allows null sku
- Priority: P1
- Type: e2e
- Given: The migration has been applied and the products table exists
- When: A row is inserted with name='Test Product' and sku=NULL
- Then: The row is inserted successfully with sku as NULL
- Data: Product record with explicit null sku

### 12-1-products-schedule-data-model-E2E-004: Products table defaults unit_of_measure to 'units'
- Priority: P1
- Type: e2e
- Given: The migration has been applied and the products table exists
- When: A row is inserted with name='Test Product' without specifying unit_of_measure
- Then: The row is inserted successfully AND unit_of_measure equals 'units'
- Data: Product record omitting unit_of_measure column

### 12-1-products-schedule-data-model-E2E-005: Products updated_at trigger auto-updates on row modification
- Priority: P1
- Type: e2e
- Given: The migration has been applied and a product row exists with known created_at/updated_at
- When: The product row is updated (e.g., name changed) after a brief delay
- Then: The updated_at timestamp is greater than or equal to the original updated_at AND created_at remains unchanged
- Data: Existing product row, then UPDATE statement modifying name

## AC2: Production Schedule Table Created — GIVEN the products and assets tables exist, WHEN the production_schedule table is queried, THEN the table exists with columns id (UUID PK), asset_id (UUID NOT NULL FK->assets.id CASCADE), product_id (UUID NOT NULL FK->products.id CASCADE), scheduled_quantity (INTEGER NOT NULL), scheduled_date (DATE NOT NULL), shift (TEXT), production_order_ref (TEXT nullable), timestamps, AND triggers attached

### 12-1-products-schedule-data-model-UNIT-012: Migration creates production_schedule table with CREATE TABLE IF NOT EXISTS
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The migration SQL content is inspected
- Then: It contains `CREATE TABLE IF NOT EXISTS production_schedule` statement
- Data: Migration file content

### 12-1-products-schedule-data-model-UNIT-013: Production schedule has id UUID primary key with gen_random_uuid()
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: The `id` column is defined as `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-014: Production schedule has asset_id FK to assets with ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: The `asset_id` column is defined as `UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE`
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-015: Production schedule has product_id FK to products with ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: The `product_id` column is defined as `UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE`
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-016: Production schedule has scheduled_quantity as INTEGER NOT NULL
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: The `scheduled_quantity` column is defined as `INTEGER NOT NULL`
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-017: Production schedule has scheduled_date as DATE NOT NULL
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: The `scheduled_date` column is defined as `DATE NOT NULL`
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-018: Production schedule has shift as TEXT (nullable)
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: The `shift` column is defined as `TEXT` without NOT NULL constraint
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-019: Production schedule has production_order_ref as TEXT (nullable)
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: The `production_order_ref` column is defined as `TEXT` without NOT NULL constraint
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-020: Production schedule has created_at and updated_at timestamps
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_schedule table definition is inspected
- Then: Both `created_at` and `updated_at` are defined as `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`
- Data: Regex match within production_schedule table definition block

### 12-1-products-schedule-data-model-UNIT-021: Production schedule has update_updated_at_column trigger
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The trigger definitions are inspected
- Then: A trigger is defined on `production_schedule` executing `update_updated_at_column()` with idempotent DROP/CREATE pattern
- Data: Regex match for trigger referencing production_schedule table

### 12-1-products-schedule-data-model-E2E-006: Production schedule accepts valid insert with FK references
- Priority: P0
- Type: e2e
- Given: The migration has been applied AND a product row and an asset row exist
- When: A production_schedule row is inserted with valid asset_id, product_id, scheduled_quantity=500, scheduled_date='2026-01-15', shift='morning'
- Then: The row is inserted successfully with auto-generated UUID id and populated timestamps
- Data: Valid FK references to existing asset and product records

### 12-1-products-schedule-data-model-E2E-007: Production schedule rejects insert with invalid asset_id FK
- Priority: P0
- Type: e2e
- Given: The migration has been applied and a product exists but the referenced asset_id does not
- When: A production_schedule row is inserted with a non-existent asset_id UUID
- Then: The insert fails with a foreign key constraint violation error
- Data: Non-existent UUID for asset_id

### 12-1-products-schedule-data-model-E2E-008: Production schedule rejects insert with invalid product_id FK
- Priority: P0
- Type: e2e
- Given: The migration has been applied and an asset exists but the referenced product_id does not
- When: A production_schedule row is inserted with a non-existent product_id UUID
- Then: The insert fails with a foreign key constraint violation error
- Data: Non-existent UUID for product_id

### 12-1-products-schedule-data-model-E2E-009: CASCADE delete from products removes production_schedule rows
- Priority: P0
- Type: e2e
- Given: A product exists with one or more production_schedule rows referencing it
- When: The product row is deleted
- Then: All production_schedule rows referencing that product_id are automatically deleted via CASCADE
- Data: Product with 2+ schedule rows, then DELETE product

### 12-1-products-schedule-data-model-E2E-010: CASCADE delete from assets removes production_schedule rows
- Priority: P0
- Type: e2e
- Given: An asset exists with one or more production_schedule rows referencing it
- When: The asset row is deleted
- Then: All production_schedule rows referencing that asset_id are automatically deleted via CASCADE
- Data: Asset with 2+ schedule rows, then DELETE asset

### 12-1-products-schedule-data-model-E2E-011: Production schedule rejects null scheduled_quantity
- Priority: P1
- Type: e2e
- Given: The migration has been applied with valid asset and product rows
- When: A production_schedule row is inserted with scheduled_quantity=NULL
- Then: The insert fails with a NOT NULL constraint violation error
- Data: Schedule row with null scheduled_quantity

### 12-1-products-schedule-data-model-E2E-012: Production schedule allows null shift and production_order_ref
- Priority: P1
- Type: e2e
- Given: The migration has been applied with valid asset and product rows
- When: A production_schedule row is inserted with shift=NULL and production_order_ref=NULL
- Then: The row is inserted successfully
- Data: Schedule row omitting shift and production_order_ref columns

## AC3: Production Actuals Table Created — GIVEN the products and assets tables exist, WHEN the production_actuals table is queried, THEN the table exists with columns id (UUID PK), asset_id (UUID NOT NULL FK->assets.id CASCADE), product_id (UUID NOT NULL FK->products.id CASCADE), actual_quantity (INTEGER NOT NULL), production_date (DATE NOT NULL), shift (TEXT), timestamps, AND triggers attached

### 12-1-products-schedule-data-model-UNIT-022: Migration creates production_actuals table with CREATE TABLE IF NOT EXISTS
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The migration SQL content is inspected
- Then: It contains `CREATE TABLE IF NOT EXISTS production_actuals` statement
- Data: Migration file content

### 12-1-products-schedule-data-model-UNIT-023: Production actuals has id UUID primary key with gen_random_uuid()
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_actuals table definition is inspected
- Then: The `id` column is defined as `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Data: Regex match within production_actuals table definition block

### 12-1-products-schedule-data-model-UNIT-024: Production actuals has asset_id FK to assets with ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_actuals table definition is inspected
- Then: The `asset_id` column is defined as `UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE`
- Data: Regex match within production_actuals table definition block

### 12-1-products-schedule-data-model-UNIT-025: Production actuals has product_id FK to products with ON DELETE CASCADE
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_actuals table definition is inspected
- Then: The `product_id` column is defined as `UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE`
- Data: Regex match within production_actuals table definition block

### 12-1-products-schedule-data-model-UNIT-026: Production actuals has actual_quantity as INTEGER NOT NULL
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_actuals table definition is inspected
- Then: The `actual_quantity` column is defined as `INTEGER NOT NULL`
- Data: Regex match within production_actuals table definition block

### 12-1-products-schedule-data-model-UNIT-027: Production actuals has production_date as DATE NOT NULL
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_actuals table definition is inspected
- Then: The `production_date` column is defined as `DATE NOT NULL`
- Data: Regex match within production_actuals table definition block

### 12-1-products-schedule-data-model-UNIT-028: Production actuals has shift as TEXT (nullable)
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_actuals table definition is inspected
- Then: The `shift` column is defined as `TEXT` without NOT NULL constraint
- Data: Regex match within production_actuals table definition block

### 12-1-products-schedule-data-model-UNIT-029: Production actuals has created_at and updated_at timestamps
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The production_actuals table definition is inspected
- Then: Both `created_at` and `updated_at` are defined as `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`
- Data: Regex match within production_actuals table definition block

### 12-1-products-schedule-data-model-UNIT-030: Production actuals has update_updated_at_column trigger
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The trigger definitions are inspected
- Then: A trigger is defined on `production_actuals` executing `update_updated_at_column()` with idempotent DROP/CREATE pattern
- Data: Regex match for trigger referencing production_actuals table

### 12-1-products-schedule-data-model-E2E-013: Production actuals accepts valid insert with FK references
- Priority: P0
- Type: e2e
- Given: The migration has been applied AND a product row and an asset row exist
- When: A production_actuals row is inserted with valid asset_id, product_id, actual_quantity=480, production_date='2026-01-15', shift='morning'
- Then: The row is inserted successfully with auto-generated UUID id and populated timestamps
- Data: Valid FK references to existing asset and product records

### 12-1-products-schedule-data-model-E2E-014: CASCADE delete from products removes production_actuals rows
- Priority: P0
- Type: e2e
- Given: A product exists with one or more production_actuals rows referencing it
- When: The product row is deleted
- Then: All production_actuals rows referencing that product_id are automatically deleted via CASCADE
- Data: Product with 2+ actuals rows, then DELETE product

### 12-1-products-schedule-data-model-E2E-015: CASCADE delete from assets removes production_actuals rows
- Priority: P0
- Type: e2e
- Given: An asset exists with one or more production_actuals rows referencing it
- When: The asset row is deleted
- Then: All production_actuals rows referencing that asset_id are automatically deleted via CASCADE
- Data: Asset with 2+ actuals rows, then DELETE asset

### 12-1-products-schedule-data-model-E2E-016: Production actuals rejects null actual_quantity
- Priority: P1
- Type: e2e
- Given: The migration has been applied with valid asset and product rows
- When: A production_actuals row is inserted with actual_quantity=NULL
- Then: The insert fails with a NOT NULL constraint violation error
- Data: Actuals row with null actual_quantity

### 12-1-products-schedule-data-model-E2E-017: Production actuals rejects null production_date
- Priority: P1
- Type: e2e
- Given: The migration has been applied with valid asset and product rows
- When: A production_actuals row is inserted with production_date=NULL
- Then: The insert fails with a NOT NULL constraint violation error
- Data: Actuals row with null production_date

## AC4: Row Level Security (RLS) Enabled — GIVEN all three tables are created, WHEN RLS is checked, THEN RLS is enabled on products, production_schedule, and production_actuals AND authenticated users can SELECT all rows AND only service_role can INSERT, UPDATE, DELETE

### 12-1-products-schedule-data-model-UNIT-031: RLS is enabled on products table
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS statements are inspected
- Then: The migration contains `ALTER TABLE products ENABLE ROW LEVEL SECURITY`
- Data: String match in migration content

### 12-1-products-schedule-data-model-UNIT-032: RLS is enabled on production_schedule table
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS statements are inspected
- Then: The migration contains `ALTER TABLE production_schedule ENABLE ROW LEVEL SECURITY`
- Data: String match in migration content

### 12-1-products-schedule-data-model-UNIT-033: RLS is enabled on production_actuals table
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS statements are inspected
- Then: The migration contains `ALTER TABLE production_actuals ENABLE ROW LEVEL SECURITY`
- Data: String match in migration content

### 12-1-products-schedule-data-model-UNIT-034: Authenticated SELECT policy exists on products
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS policy statements are inspected
- Then: A CREATE POLICY for SELECT on products TO authenticated with USING (true) is present AND is preceded by DROP POLICY IF EXISTS for idempotency
- Data: Regex match for policy creation pattern

### 12-1-products-schedule-data-model-UNIT-035: Authenticated SELECT policy exists on production_schedule
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS policy statements are inspected
- Then: A CREATE POLICY for SELECT on production_schedule TO authenticated with USING (true) is present AND is preceded by DROP POLICY IF EXISTS
- Data: Regex match for policy creation pattern

### 12-1-products-schedule-data-model-UNIT-036: Authenticated SELECT policy exists on production_actuals
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS policy statements are inspected
- Then: A CREATE POLICY for SELECT on production_actuals TO authenticated with USING (true) is present AND is preceded by DROP POLICY IF EXISTS
- Data: Regex match for policy creation pattern

### 12-1-products-schedule-data-model-UNIT-037: Service role full access policy exists on products
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS policy statements are inspected
- Then: A CREATE POLICY for ALL on products TO service_role with USING (true) WITH CHECK (true) is present AND is preceded by DROP POLICY IF EXISTS
- Data: Regex match for policy creation pattern

### 12-1-products-schedule-data-model-UNIT-038: Service role full access policy exists on production_schedule
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS policy statements are inspected
- Then: A CREATE POLICY for ALL on production_schedule TO service_role with USING (true) WITH CHECK (true) is present AND is preceded by DROP POLICY IF EXISTS
- Data: Regex match for policy creation pattern

### 12-1-products-schedule-data-model-UNIT-039: Service role full access policy exists on production_actuals
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The RLS policy statements are inspected
- Then: A CREATE POLICY for ALL on production_actuals TO service_role with USING (true) WITH CHECK (true) is present AND is preceded by DROP POLICY IF EXISTS
- Data: Regex match for policy creation pattern

### 12-1-products-schedule-data-model-E2E-018: Authenticated user can SELECT from products
- Priority: P0
- Type: e2e
- Given: The migration has been applied AND products data exists AND user is authenticated (not service_role)
- When: A SELECT query is executed on the products table
- Then: The query succeeds and returns rows
- Data: Pre-seeded product rows, authenticated JWT

### 12-1-products-schedule-data-model-E2E-019: Authenticated user cannot INSERT into products
- Priority: P0
- Type: e2e
- Given: The migration has been applied AND user is authenticated (not service_role)
- When: An INSERT query is attempted on the products table
- Then: The insert is denied by RLS policy
- Data: Valid product data, authenticated JWT (non-service_role)

### 12-1-products-schedule-data-model-E2E-020: Authenticated user cannot UPDATE products
- Priority: P1
- Type: e2e
- Given: The migration has been applied AND products data exists AND user is authenticated (not service_role)
- When: An UPDATE query is attempted on the products table
- Then: The update is denied by RLS policy (0 rows affected)
- Data: Existing product row, authenticated JWT

### 12-1-products-schedule-data-model-E2E-021: Authenticated user cannot DELETE from products
- Priority: P1
- Type: e2e
- Given: The migration has been applied AND products data exists AND user is authenticated (not service_role)
- When: A DELETE query is attempted on the products table
- Then: The delete is denied by RLS policy (0 rows affected)
- Data: Existing product row, authenticated JWT

### 12-1-products-schedule-data-model-E2E-022: Service role can INSERT, UPDATE, DELETE on all three tables
- Priority: P0
- Type: e2e
- Given: The migration has been applied AND the service_role key is used
- When: INSERT, UPDATE, and DELETE operations are performed on products, production_schedule, and production_actuals
- Then: All operations succeed
- Data: Valid data for all three tables, service_role JWT

## AC5: Performance Indexes Created — GIVEN the tables exist, WHEN indexes are checked, THEN 6 specific indexes exist on production_schedule and production_actuals

### 12-1-products-schedule-data-model-UNIT-040: Index idx_production_schedule_asset_id exists
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The index creation statements are inspected
- Then: The migration contains `CREATE INDEX IF NOT EXISTS idx_production_schedule_asset_id ON production_schedule(asset_id)`
- Data: Regex match for index creation

### 12-1-products-schedule-data-model-UNIT-041: Index idx_production_schedule_product_id exists
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The index creation statements are inspected
- Then: The migration contains `CREATE INDEX IF NOT EXISTS idx_production_schedule_product_id ON production_schedule(product_id)`
- Data: Regex match for index creation

### 12-1-products-schedule-data-model-UNIT-042: Index idx_production_schedule_scheduled_date exists
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The index creation statements are inspected
- Then: The migration contains `CREATE INDEX IF NOT EXISTS idx_production_schedule_scheduled_date ON production_schedule(scheduled_date)`
- Data: Regex match for index creation

### 12-1-products-schedule-data-model-UNIT-043: Index idx_production_actuals_asset_id exists
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The index creation statements are inspected
- Then: The migration contains `CREATE INDEX IF NOT EXISTS idx_production_actuals_asset_id ON production_actuals(asset_id)`
- Data: Regex match for index creation

### 12-1-products-schedule-data-model-UNIT-044: Index idx_production_actuals_product_id exists
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The index creation statements are inspected
- Then: The migration contains `CREATE INDEX IF NOT EXISTS idx_production_actuals_product_id ON production_actuals(product_id)`
- Data: Regex match for index creation

### 12-1-products-schedule-data-model-UNIT-045: Index idx_production_actuals_production_date exists
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The index creation statements are inspected
- Then: The migration contains `CREATE INDEX IF NOT EXISTS idx_production_actuals_production_date ON production_actuals(production_date)`
- Data: Regex match for index creation

### 12-1-products-schedule-data-model-UNIT-046: All indexes use IF NOT EXISTS for idempotency
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: All CREATE INDEX statements are inspected
- Then: Every CREATE INDEX statement includes `IF NOT EXISTS`
- Data: Regex match ensuring no bare CREATE INDEX statements

## AC6: Migration File Created — GIVEN the migration is needed, WHEN the migrations folder is checked, THEN 0026_products_and_schedule.sql exists AND follows established patterns AND runs idempotently

### 12-1-products-schedule-data-model-UNIT-047: Migration file exists at correct path
- Priority: P0
- Type: unit
- Given: The project repository is available
- When: The file system is checked for supabase/migrations/0026_products_and_schedule.sql
- Then: The file exists and is non-empty
- Data: File system check

### 12-1-products-schedule-data-model-UNIT-048: Migration file has header comment with story reference
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: The file header is inspected
- Then: The migration begins with a comment block that includes a reference to Story 12.1 or 12-1
- Data: Regex match at start of file for comment block

### 12-1-products-schedule-data-model-UNIT-049: Migration uses CREATE TABLE IF NOT EXISTS for all three tables
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: All CREATE TABLE statements are inspected
- Then: All three tables (products, production_schedule, production_actuals) use `CREATE TABLE IF NOT EXISTS`
- Data: Count of CREATE TABLE IF NOT EXISTS should be exactly 3

### 12-1-products-schedule-data-model-UNIT-050: Migration uses DROP TRIGGER IF EXISTS before CREATE TRIGGER
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: All trigger statements are inspected
- Then: Every CREATE TRIGGER is preceded by a corresponding DROP TRIGGER IF EXISTS for the same trigger name
- Data: Matching pairs of DROP/CREATE trigger statements (3 pairs total)

### 12-1-products-schedule-data-model-UNIT-051: Migration uses DROP POLICY IF EXISTS before CREATE POLICY
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: All RLS policy statements are inspected
- Then: Every CREATE POLICY is preceded by a corresponding DROP POLICY IF EXISTS for the same policy name
- Data: Matching pairs of DROP/CREATE policy statements (6 pairs total: 2 per table x 3 tables)

### 12-1-products-schedule-data-model-UNIT-052: Migration does NOT recreate update_updated_at_column function
- Priority: P0
- Type: unit
- Given: The migration file exists
- When: The migration SQL is inspected for function creation
- Then: The migration does NOT contain `CREATE FUNCTION update_updated_at_column` or `CREATE OR REPLACE FUNCTION update_updated_at_column`
- Data: Negative assertion on migration content

### 12-1-products-schedule-data-model-UNIT-053: Migration has balanced parentheses (SQL syntax sanity)
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: Parentheses are counted in the migration SQL
- Then: The count of opening parentheses equals the count of closing parentheses
- Data: Character count comparison

### 12-1-products-schedule-data-model-UNIT-054: Migration has exactly 3 CREATE TABLE statements
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: CREATE TABLE statements are counted
- Then: There are exactly 3 CREATE TABLE statements (products, production_schedule, production_actuals)
- Data: Regex match count

### 12-1-products-schedule-data-model-UNIT-055: Migration has verification queries as comments
- Priority: P2
- Type: unit
- Given: The migration file exists
- When: The bottom section of the migration is inspected
- Then: Commented-out verification SQL queries are present (e.g., information_schema queries, pg_indexes queries, pg_tables rowsecurity check)
- Data: Comment block containing SELECT from information_schema or pg_indexes

### 12-1-products-schedule-data-model-UNIT-056: Migration has COMMENT ON TABLE for all three tables
- Priority: P2
- Type: unit
- Given: The migration file exists
- When: The documentation comments are inspected
- Then: The migration contains COMMENT ON TABLE for products, production_schedule, and production_actuals
- Data: String matches for COMMENT ON TABLE statements

### 12-1-products-schedule-data-model-E2E-023: Migration is idempotent — running twice does not error
- Priority: P0
- Type: e2e
- Given: The migration has been applied once successfully
- When: The same migration SQL is executed a second time
- Then: No errors occur AND all tables, indexes, triggers, and policies remain intact
- Data: Full migration SQL executed twice sequentially

### 12-1-products-schedule-data-model-UNIT-057: Migration does NOT add UNIQUE constraint on schedule composite key
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: The migration SQL is inspected for UNIQUE constraints on production_schedule
- Then: No UNIQUE constraint exists on (asset_id, product_id, scheduled_date, shift) or any composite key on production_schedule
- Data: Negative assertion — no UNIQUE keyword in production_schedule context (except PK)

### 12-1-products-schedule-data-model-UNIT-058: Migration does NOT add columns beyond spec
- Priority: P1
- Type: unit
- Given: The migration file exists
- When: The column lists for all three tables are inspected
- Then: Products has exactly 7 columns (id, name, sku, product_family, unit_of_measure, created_at, updated_at) AND production_schedule has exactly 9 columns (id, asset_id, product_id, scheduled_quantity, scheduled_date, shift, production_order_ref, created_at, updated_at) AND production_actuals has exactly 8 columns (id, asset_id, product_id, actual_quantity, production_date, shift, created_at, updated_at)
- Data: Column count or enumeration within each table definition block

edge_cases:
  - Products with very long name or sku TEXT values (no VARCHAR limit means no truncation)
  - Inserting production_schedule with scheduled_quantity of 0 (valid INTEGER but edge case for business logic)
  - Inserting production_actuals with actual_quantity of 0 (valid but edge case)
  - Multiple production_schedule rows for the same asset/product/date/shift combination (allowed since no UNIQUE constraint)
  - Deleting a product that is referenced by both production_schedule AND production_actuals rows simultaneously (CASCADE should handle both)
  - Running migration on a database where assets table has zero rows (tables should still create fine, FK references are structural)
  - Shift column with arbitrary text values (no CHECK constraint — accepts any string)
  - Large scheduled_date or production_date values (far future dates)
  - Concurrent inserts into production_schedule referencing the same product_id (no uniqueness conflict expected)

error_scenarios:
  - Insert into production_schedule with NULL asset_id — should fail NOT NULL constraint
  - Insert into production_schedule with NULL product_id — should fail NOT NULL constraint
  - Insert into production_schedule with NULL scheduled_date — should fail NOT NULL constraint
  - Insert into production_actuals with NULL asset_id — should fail NOT NULL constraint
  - Insert into production_actuals with NULL product_id — should fail NOT NULL constraint
  - Insert into products with NULL name — should fail NOT NULL constraint
  - Insert into production_schedule referencing non-existent asset_id — should fail FK constraint
  - Insert into production_schedule referencing non-existent product_id — should fail FK constraint
  - Insert into production_actuals referencing non-existent asset_id — should fail FK constraint
  - Insert into production_actuals referencing non-existent product_id — should fail FK constraint
  - Authenticated (non-service_role) user attempting INSERT on any of the three tables — should be denied by RLS
  - Authenticated (non-service_role) user attempting DELETE on any of the three tables — should be denied by RLS
  - Migration running before assets table exists — should fail on FK creation for production_schedule and production_actuals

test_file_mapping:
  - 12-1-products-schedule-data-model-UNIT-*: supabase/tests/products-schedule-schema.test.ts
  - 12-1-products-schedule-data-model-E2E-*: Manual verification via Supabase SQL Editor or supabase/tests/products-schedule-e2e.test.ts (if local Supabase instance available)
  - 12-1-products-schedule-data-model-INT-*: N/A (no integration tests for pure SQL migration)

TEST SPEC END
