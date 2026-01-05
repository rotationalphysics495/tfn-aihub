# Story 1.3: Plant Object Model Schema

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **the assets, cost_centers, and shift_targets tables created in Supabase PostgreSQL**,
so that **the system has a semantic data model to enable cross-domain analysis linking equipment to financial data and production targets**.

## Acceptance Criteria

1. **AC1: Assets Table Created**
   - GIVEN I have access to the Supabase PostgreSQL database
   - WHEN I query the `assets` table
   - THEN the table exists with the following columns:
     - `id`: UUID (Primary Key, auto-generated)
     - `name`: VARCHAR(255) NOT NULL (e.g., "Grinder 5")
     - `source_id`: VARCHAR(255) NOT NULL (Maps to MSSQL `locationName`)
     - `area`: VARCHAR(100) (e.g., "Grinding")
     - `created_at`: TIMESTAMP WITH TIME ZONE (default: NOW())
     - `updated_at`: TIMESTAMP WITH TIME ZONE (default: NOW())

2. **AC2: Cost Centers Table Created**
   - GIVEN the `assets` table exists
   - WHEN I query the `cost_centers` table
   - THEN the table exists with the following columns:
     - `id`: UUID (Primary Key, auto-generated)
     - `asset_id`: UUID (Foreign Key -> `assets.id`, NOT NULL)
     - `standard_hourly_rate`: DECIMAL(10, 2) NOT NULL (For financial calculations)
     - `created_at`: TIMESTAMP WITH TIME ZONE (default: NOW())
     - `updated_at`: TIMESTAMP WITH TIME ZONE (default: NOW())
   - AND the foreign key constraint CASCADE on DELETE is configured

3. **AC3: Shift Targets Table Created**
   - GIVEN the `assets` table exists
   - WHEN I query the `shift_targets` table
   - THEN the table exists with the following columns:
     - `id`: UUID (Primary Key, auto-generated)
     - `asset_id`: UUID (Foreign Key -> `assets.id`, NOT NULL)
     - `target_output`: INTEGER NOT NULL (Production target count)
     - `shift`: VARCHAR(50) (e.g., "Day", "Night", "Swing")
     - `effective_date`: DATE (When this target becomes effective)
     - `created_at`: TIMESTAMP WITH TIME ZONE (default: NOW())
     - `updated_at`: TIMESTAMP WITH TIME ZONE (default: NOW())
   - AND the foreign key constraint CASCADE on DELETE is configured

4. **AC4: Row Level Security (RLS) Policies**
   - GIVEN the tables are created
   - WHEN Row Level Security is enabled
   - THEN authenticated users can SELECT all rows
   - AND only service_role can INSERT, UPDATE, DELETE

5. **AC5: Indexes for Query Performance**
   - GIVEN the tables exist
   - WHEN I check for indexes
   - THEN indexes exist on:
     - `assets.source_id` (for MSSQL mapping lookups)
     - `cost_centers.asset_id` (for join performance)
     - `shift_targets.asset_id` (for join performance)
     - `shift_targets.effective_date` (for date range queries)

6. **AC6: Migration File Created**
   - GIVEN I need to track schema changes
   - WHEN I check the migrations folder
   - THEN a timestamped SQL migration file exists
   - AND it can be run idempotently (uses CREATE IF NOT EXISTS or checks)

## Tasks / Subtasks

- [ ] Task 1: Set up Supabase project connection (AC: 1-5)
  - [ ] Subtask 1.1: Verify Supabase project is created and accessible
  - [ ] Subtask 1.2: Create `.env` configuration for Supabase connection
  - [ ] Subtask 1.3: Set up Supabase CLI or migration tooling

- [ ] Task 2: Create `assets` table (AC: 1)
  - [ ] Subtask 2.1: Write SQL migration for `assets` table with all columns
  - [ ] Subtask 2.2: Add `updated_at` trigger function for auto-updates
  - [ ] Subtask 2.3: Apply migration to Supabase

- [ ] Task 3: Create `cost_centers` table (AC: 2)
  - [ ] Subtask 3.1: Write SQL migration with foreign key to `assets`
  - [ ] Subtask 3.2: Configure ON DELETE CASCADE constraint
  - [ ] Subtask 3.3: Apply migration to Supabase

- [ ] Task 4: Create `shift_targets` table (AC: 3)
  - [ ] Subtask 4.1: Write SQL migration with foreign key to `assets`
  - [ ] Subtask 4.2: Configure ON DELETE CASCADE constraint
  - [ ] Subtask 4.3: Apply migration to Supabase

- [ ] Task 5: Configure Row Level Security (AC: 4)
  - [ ] Subtask 5.1: Enable RLS on all three tables
  - [ ] Subtask 5.2: Create SELECT policy for authenticated users
  - [ ] Subtask 5.3: Create INSERT/UPDATE/DELETE policies for service_role

- [ ] Task 6: Create performance indexes (AC: 5)
  - [ ] Subtask 6.1: Add index on `assets.source_id`
  - [ ] Subtask 6.2: Add index on `cost_centers.asset_id`
  - [ ] Subtask 6.3: Add indexes on `shift_targets.asset_id` and `shift_targets.effective_date`

- [ ] Task 7: Verify and document (AC: 6)
  - [ ] Subtask 7.1: Verify all tables created correctly via Supabase dashboard
  - [ ] Subtask 7.2: Test RLS policies with different user roles
  - [ ] Subtask 7.3: Document migration file location and usage

## Dev Notes

### Technical Requirements

**Database Platform:** Supabase PostgreSQL (version 15+)

**Table Relationships:**
```
assets (1) ----< (N) cost_centers
assets (1) ----< (N) shift_targets
```

**Data Types Rationale:**
- `UUID` for primary keys: Recommended by Supabase, better for distributed systems
- `DECIMAL(10, 2)` for `standard_hourly_rate`: Precision for currency values
- `VARCHAR` with limits: Prevents excessive data storage while allowing flexibility
- `TIMESTAMP WITH TIME ZONE`: Consistent timezone handling across deployments

### Architecture Compliance

**From Architecture Document (Section 5):**
- Plant Object Model tables are defined as: `assets`, `cost_centers`, `shift_targets`
- These tables are stored in Supabase PostgreSQL
- The `assets.source_id` field maps to MSSQL `locationName` for data synchronization

**Security Requirements (Section 8):**
- All Supabase tables must have Row Level Security enabled
- API access is via Supabase Auth JWT tokens

### Library/Framework Requirements

**Supabase CLI (Optional but recommended):**
- Version: Latest (`supabase` npm package or standalone CLI)
- Used for: Local development, migrations, type generation

**Migration Approach Options:**
1. **Supabase Dashboard:** Direct SQL execution in SQL Editor
2. **Supabase CLI:** `supabase migration new` and `supabase db push`
3. **Raw SQL Files:** Store in `apps/api/migrations/` or `supabase/migrations/`

**Recommended:** Use Supabase CLI for version-controlled migrations.

### File Structure Requirements

Based on TurboRepo structure from Architecture (Section 4):

```
manufacturing-assistant/
├── supabase/                        # Supabase configuration (if using CLI)
│   ├── migrations/
│   │   └── 20260105000000_plant_object_model.sql
│   └── config.toml
├── apps/
│   └── api/
│       └── app/
│           └── models/              # Python SQLAlchemy models (if needed later)
└── .env                             # Supabase connection strings
```

### Testing Requirements

**Manual Verification:**
1. Query each table to confirm columns and types
2. Insert test data and verify constraints
3. Test foreign key cascades by deleting an asset
4. Test RLS policies with different auth states

**SQL Verification Queries:**
```sql
-- Check table exists and has correct columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'assets';

-- Check foreign keys
SELECT tc.constraint_name, tc.table_name, kcu.column_name,
       ccu.table_name AS foreign_table_name,
       ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY';

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('assets', 'cost_centers', 'shift_targets');
```

### Project Structure Notes

- This story creates the foundational data model for FR2 (Plant Object Model)
- The tables will be used by Story 1.4 (Analytical Cache Schema) which creates `daily_summaries`, `live_snapshots`, `safety_events`
- Story 1.5 (MSSQL Connection) will use `assets.source_id` to map imported data
- No conflicts detected with existing project structure

### SQL Migration Template

```sql
-- Migration: Create Plant Object Model tables
-- Story: 1.3 - Plant Object Model Schema
-- Date: 2026-01-05

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    area VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assets_source_id ON assets(source_id);

CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Cost Centers table
CREATE TABLE IF NOT EXISTS cost_centers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    standard_hourly_rate DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cost_centers_asset_id ON cost_centers(asset_id);

CREATE TRIGGER update_cost_centers_updated_at
    BEFORE UPDATE ON cost_centers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Shift Targets table
CREATE TABLE IF NOT EXISTS shift_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    target_output INTEGER NOT NULL,
    shift VARCHAR(50),
    effective_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_shift_targets_asset_id ON shift_targets(asset_id);
CREATE INDEX IF NOT EXISTS idx_shift_targets_effective_date ON shift_targets(effective_date);

CREATE TRIGGER update_shift_targets_updated_at
    BEFORE UPDATE ON shift_targets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE shift_targets ENABLE ROW LEVEL SECURITY;

-- RLS Policies for authenticated SELECT
CREATE POLICY "Allow authenticated read access on assets"
    ON assets FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access on cost_centers"
    ON cost_centers FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access on shift_targets"
    ON shift_targets FOR SELECT
    TO authenticated
    USING (true);

-- RLS Policies for service_role full access
CREATE POLICY "Allow service_role full access on assets"
    ON assets FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service_role full access on cost_centers"
    ON cost_centers FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service_role full access on shift_targets"
    ON shift_targets FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
```

### References

- [Source: _bmad/bmm/data/architecture.md#Section 5 - Data Models & Plant Object Model]
- [Source: _bmad/bmm/data/architecture.md#Section 8 - Security & Constraints]
- [Source: _bmad/bmm/data/prd.md#Section 2 - Requirements - FR2]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 1 - Story 1.3]
- [Source: _bmad-output/planning-artifacts/epic-1.md#Story 1.3]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
