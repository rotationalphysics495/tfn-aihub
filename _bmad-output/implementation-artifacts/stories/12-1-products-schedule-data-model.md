# Story 12.1: Products & Schedule Data Model

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **database tables for products, production schedules, and production actuals**,
so that **the system can track what should have been produced vs. what was actually produced, enabling schedule attainment and product mix analysis**.

## Acceptance Criteria

1. **AC1: Products Table Created**
   - GIVEN the migration runs successfully
   - WHEN the `products` table is queried
   - THEN the table exists with the following columns:
     - `id`: UUID (Primary Key, auto-generated via `gen_random_uuid()`)
     - `name`: TEXT NOT NULL (e.g., "Colombian Single Origin")
     - `sku`: TEXT (e.g., "COL-SO-12OZ", nullable for initial seed data)
     - `product_family`: TEXT (e.g., "Single Origin", "Blend", "Grind")
     - `unit_of_measure`: TEXT DEFAULT 'units' (e.g., "units", "lbs", "bags")
     - `created_at`: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
     - `updated_at`: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   - AND the `update_updated_at_column()` trigger is attached

2. **AC2: Production Schedule Table Created**
   - GIVEN the `products` table and `assets` table exist
   - WHEN the `production_schedule` table is queried
   - THEN the table exists with the following columns:
     - `id`: UUID (Primary Key, auto-generated via `gen_random_uuid()`)
     - `asset_id`: UUID NOT NULL (Foreign Key -> `assets.id`, ON DELETE CASCADE)
     - `product_id`: UUID NOT NULL (Foreign Key -> `products.id`, ON DELETE CASCADE)
     - `scheduled_quantity`: INTEGER NOT NULL
     - `scheduled_date`: DATE NOT NULL
     - `shift`: TEXT (e.g., "morning", "afternoon", "night")
     - `production_order_ref`: TEXT (nullable, for future AX/D365 PO number link)
     - `created_at`: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
     - `updated_at`: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   - AND both foreign key constraints use CASCADE DELETE
   - AND the `update_updated_at_column()` trigger is attached

3. **AC3: Production Actuals Table Created**
   - GIVEN the `products` table and `assets` table exist
   - WHEN the `production_actuals` table is queried
   - THEN the table exists with the following columns:
     - `id`: UUID (Primary Key, auto-generated via `gen_random_uuid()`)
     - `asset_id`: UUID NOT NULL (Foreign Key -> `assets.id`, ON DELETE CASCADE)
     - `product_id`: UUID NOT NULL (Foreign Key -> `products.id`, ON DELETE CASCADE)
     - `actual_quantity`: INTEGER NOT NULL
     - `production_date`: DATE NOT NULL
     - `shift`: TEXT (e.g., "morning", "afternoon", "night")
     - `created_at`: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
     - `updated_at`: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   - AND both foreign key constraints use CASCADE DELETE
   - AND the `update_updated_at_column()` trigger is attached

4. **AC4: Row Level Security (RLS) Enabled**
   - GIVEN all three tables are created
   - WHEN RLS is checked
   - THEN RLS is enabled on `products`, `production_schedule`, and `production_actuals`
   - AND authenticated users can SELECT all rows
   - AND only service_role can INSERT, UPDATE, DELETE

5. **AC5: Performance Indexes Created**
   - GIVEN the tables exist
   - WHEN indexes are checked
   - THEN the following indexes exist:
     - `idx_production_schedule_asset_id` on `production_schedule(asset_id)`
     - `idx_production_schedule_product_id` on `production_schedule(product_id)`
     - `idx_production_schedule_scheduled_date` on `production_schedule(scheduled_date)`
     - `idx_production_actuals_asset_id` on `production_actuals(asset_id)`
     - `idx_production_actuals_product_id` on `production_actuals(product_id)`
     - `idx_production_actuals_production_date` on `production_actuals(production_date)`

6. **AC6: Migration File Created**
   - GIVEN the migration is needed
   - WHEN the migrations folder is checked
   - THEN `supabase/migrations/0026_products_and_schedule.sql` exists
   - AND it follows the established migration patterns from `0002_plant_object_model.sql`
   - AND it can run idempotently (uses `CREATE TABLE IF NOT EXISTS`, `DROP TRIGGER IF EXISTS`, `DROP POLICY IF EXISTS`)

## Tasks / Subtasks

- [ ] Task 1: Create migration file `supabase/migrations/0026_products_and_schedule.sql` (AC: 1-6)
  - [ ] Subtask 1.1: Add migration header comment with story reference and date
  - [ ] Subtask 1.2: Create `products` table with all specified columns
  - [ ] Subtask 1.3: Create `production_schedule` table with FK constraints to `assets` and `products`
  - [ ] Subtask 1.4: Create `production_actuals` table with FK constraints to `assets` and `products`
  - [ ] Subtask 1.5: Add `update_updated_at_column()` triggers to all three tables

- [ ] Task 2: Configure Row Level Security (AC: 4)
  - [ ] Subtask 2.1: Enable RLS on all three tables
  - [ ] Subtask 2.2: Create SELECT policy for authenticated users on each table
  - [ ] Subtask 2.3: Create ALL policy for service_role on each table

- [ ] Task 3: Create performance indexes (AC: 5)
  - [ ] Subtask 3.1: Add indexes on `production_schedule` (asset_id, product_id, scheduled_date)
  - [ ] Subtask 3.2: Add indexes on `production_actuals` (asset_id, product_id, production_date)

- [ ] Task 4: Add table and column comments for documentation (AC: 1-3)
  - [ ] Subtask 4.1: Add COMMENT ON TABLE for all three tables
  - [ ] Subtask 4.2: Add COMMENT ON COLUMN for key columns

- [ ] Task 5: Verify migration (AC: 6)
  - [ ] Subtask 5.1: Include verification queries as comments at bottom of migration
  - [ ] Subtask 5.2: Ensure idempotency patterns match `0002_plant_object_model.sql`

## Dev Notes

### Technical Requirements

**Database Platform:** Supabase PostgreSQL (version 15+)

**Table Relationships:**
```
products (1) ----< (N) production_schedule
products (1) ----< (N) production_actuals
assets (1) ----< (N) production_schedule
assets (1) ----< (N) production_actuals
```

**Data Types Rationale:**
- `UUID` for primary keys: Consistent with all existing tables (`assets`, `cost_centers`, `shift_targets`, etc.)
- `TEXT` instead of `VARCHAR`: The epic specifies TEXT for name, sku, product_family, shift columns. This is consistent with newer migrations like `0025_action_followups.sql` which use TEXT.
- `INTEGER` for quantities: Matches `shift_targets.target_output` pattern
- `DATE` for scheduled_date/production_date: Simple date without timezone (matches the daily granularity requirement)
- `TIMESTAMP WITH TIME ZONE` for created_at/updated_at: Consistent with all existing tables

**Key Design Decision -- TEXT vs VARCHAR:**
Earlier migrations (`0002`) use `VARCHAR(255)` while later migrations (`0025`) use `TEXT`. The epic explicitly specifies `TEXT` for columns. Follow the epic specification and use `TEXT`, which is also the PostgreSQL-idiomatic approach (TEXT and VARCHAR have identical performance in PostgreSQL).

### Architecture Compliance

**Migration Naming Convention:**
- Existing migrations use sequential numbering: `0001` through `0025`
- Epic specifies: `0026_products_and_schedule.sql`
- File path: `supabase/migrations/0026_products_and_schedule.sql`

**Migration Pattern (from `0002_plant_object_model.sql`):**
1. Header comment with story reference and date
2. Table creation with `CREATE TABLE IF NOT EXISTS`
3. Column comments via `COMMENT ON TABLE/COLUMN`
4. Index creation with `CREATE INDEX IF NOT EXISTS`
5. Trigger creation with `DROP TRIGGER IF EXISTS` then `CREATE TRIGGER`
6. RLS enable with `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
7. RLS policies with `DROP POLICY IF EXISTS` then `CREATE POLICY`
8. Verification queries as comments at bottom

**RLS Pattern (established in `0002`):**
- Authenticated users: SELECT only via `USING (true)`
- Service role: ALL operations via `USING (true) WITH CHECK (true)`

**Trigger Pattern:**
- Reuse the existing `update_updated_at_column()` function (already created in `0002`)
- Do NOT recreate the function -- just reference it
- Use `DROP TRIGGER IF EXISTS` before `CREATE TRIGGER` for idempotency

**FK Cascade Pattern:**
- All foreign keys use `ON DELETE CASCADE` (matches `cost_centers.asset_id` -> `assets.id` pattern)
- The epic explicitly requires CASCADE DELETE on both `assets(id)` and `products(id)` references

### Existing Schema Context

**The `assets` table already exists** (created in `0002_plant_object_model.sql`) with:
- `id` UUID PK, `name` VARCHAR(255), `source_id` VARCHAR(255), `area` VARCHAR(100)
- Used by: `cost_centers`, `shift_targets`, `daily_summaries`, `live_snapshots`, `safety_events`, `asset_history`, `alerts`

**The `products` table is NEW** -- no products/SKU concept exists in the current schema. The only product references are in unstructured `smart_summary_text` narrative. This migration introduces product-level tracking for the first time.

**Relationship to `daily_summaries`:**
- `daily_summaries` has `actual_output` as a single aggregate number per asset per day
- `production_actuals` provides product-level detail that supplements (not replaces) `daily_summaries`
- Future stories may reconcile these, but this story only creates the new tables

**Relationship to `shift_targets`:**
- `shift_targets` tracks quantity targets per asset per shift but has no product reference
- `production_schedule` adds the product dimension to scheduling
- These are complementary tables, not replacements

### File Structure Requirements

```
supabase/
  migrations/
    0001_enable_extensions.sql          # Existing
    0002_plant_object_model.sql         # Reference pattern (assets, cost_centers, shift_targets)
    ...
    0025_action_followups.sql           # Most recent migration
    0026_products_and_schedule.sql      # THIS STORY - New migration
```

**Single file:** All three tables, indexes, triggers, and RLS policies in one migration file. This matches the pattern from `0002` which created three tables in a single migration.

### Testing Requirements

**SQL Verification Queries (include as comments in migration):**
```sql
-- Check products table columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'products'
ORDER BY ordinal_position;

-- Check production_schedule foreign keys
SELECT tc.constraint_name, kcu.column_name,
       ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'production_schedule' AND tc.constraint_type = 'FOREIGN KEY';

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('products', 'production_schedule', 'production_actuals');

-- Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('products', 'production_schedule', 'production_actuals');
```

**Manual Verification:**
1. Run migration against Supabase (dashboard SQL editor or `supabase db push`)
2. Verify all three tables appear in Supabase Table Editor
3. Attempt INSERT as authenticated user -- should be denied (service_role only)
4. Attempt SELECT as authenticated user -- should succeed
5. Insert a product, then a schedule row referencing it, then delete the product -- cascade should remove schedule row
6. Insert a schedule row referencing a valid asset_id, then delete the asset -- cascade should remove schedule row

### Project Structure Notes

- This is the first story in Epic 12 (Products, Schedule & Attainment)
- Story 12.2 (Products & Schedule Seed Data) depends on these tables existing to populate seed data
- Story 12.3 (Schedule Upload API) will INSERT into `production_schedule` and `products`
- Story 12.5 (Schedule Attainment API) will JOIN `production_schedule` with `production_actuals` on (asset_id, date, shift)
- No conflicts with existing schema -- all table names are new and unique
- The `update_updated_at_column()` trigger function already exists from `0002` -- do not recreate it

### Anti-Pattern Prevention

- **DO NOT** recreate the `update_updated_at_column()` function. It already exists from migration `0002`. Just reference it in CREATE TRIGGER statements.
- **DO NOT** use `uuid_generate_v4()`. The project's established pattern (from `0002`) uses `gen_random_uuid()` for UUID generation.
- **DO NOT** add a UNIQUE constraint on `(asset_id, product_id, scheduled_date, shift)` on `production_schedule`. The epic does not specify it, and Story 12.3 (Upload) implements upsert behavior that replaces rows for a date range -- a UNIQUE constraint could interfere with bulk insert patterns.
- **DO NOT** add columns not specified in the epic. The schema is deliberately minimal for MVP. Additional columns (e.g., `notes`, `status`, `source_system`) can be added in future migrations.
- **DO NOT** create Pydantic models, API endpoints, or seed data in this story. Those are separate stories (12.2, 12.3, 12.5).

### References

- [Source: _bmad-output/planning-artifacts/epic-12.md#Story 12.1]
- [Source: docs/data-models.md#Supabase Schema]
- [Source: docs/architecture-api.md#Database Connections]
- [Source: docs/improvements.md#Schedule attainment & product mix]
- [Source: docs/improvements.md#Schedule upload (CSV/Excel) + seed data]
- [Source: supabase/migrations/0002_plant_object_model.sql] -- Reference migration pattern
- [Source: supabase/migrations/0025_action_followups.sql] -- Most recent migration pattern

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
