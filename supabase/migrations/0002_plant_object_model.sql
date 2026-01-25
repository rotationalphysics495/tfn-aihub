-- Migration: Create Plant Object Model tables
-- Story: 1.3 - Plant Object Model Schema
-- Date: 2026-01-06
--
-- This migration creates the foundational Plant Object Model tables:
--   - assets: Physical equipment in the manufacturing plant
--   - cost_centers: Financial tracking linked to assets
--   - shift_targets: Production targets per shift per asset
--
-- All tables include:
--   - UUID primary keys (auto-generated)
--   - created_at/updated_at timestamps with auto-update triggers
--   - Row Level Security (RLS) policies
--   - Performance indexes

-- ============================================================================
-- SETUP: Enable required extensions
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- HELPER FUNCTION: Auto-update updated_at timestamp
-- ============================================================================

-- Create or replace the trigger function for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TABLE: assets
-- ============================================================================
-- Represents physical equipment/machines in the manufacturing plant.
-- The source_id field maps to MSSQL locationName for data synchronization.

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    area VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comment for documentation
COMMENT ON TABLE assets IS 'Physical equipment/machines in the manufacturing plant';
COMMENT ON COLUMN assets.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN assets.name IS 'Human-readable asset name (e.g., "Grinder 5")';
COMMENT ON COLUMN assets.source_id IS 'Maps to MSSQL locationName for data sync';
COMMENT ON COLUMN assets.area IS 'Plant area where asset is located (e.g., "Grinding")';

-- Index on source_id for MSSQL mapping lookups
CREATE INDEX IF NOT EXISTS idx_assets_source_id ON assets(source_id);

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_assets_updated_at ON assets;
CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: cost_centers
-- ============================================================================
-- Links assets to financial cost center information for impact calculations.

CREATE TABLE IF NOT EXISTS cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    standard_hourly_rate DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comment for documentation
COMMENT ON TABLE cost_centers IS 'Financial cost center information linked to assets';
COMMENT ON COLUMN cost_centers.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN cost_centers.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN cost_centers.standard_hourly_rate IS 'Cost per hour for financial calculations (DECIMAL(10,2))';

-- Index on asset_id for join performance
CREATE INDEX IF NOT EXISTS idx_cost_centers_asset_id ON cost_centers(asset_id);

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_cost_centers_updated_at ON cost_centers;
CREATE TRIGGER update_cost_centers_updated_at
    BEFORE UPDATE ON cost_centers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: shift_targets
-- ============================================================================
-- Stores production targets per shift for each asset.

CREATE TABLE IF NOT EXISTS shift_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    target_output INTEGER NOT NULL,
    shift VARCHAR(50),
    effective_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comment for documentation
COMMENT ON TABLE shift_targets IS 'Production targets per shift for each asset';
COMMENT ON COLUMN shift_targets.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN shift_targets.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN shift_targets.target_output IS 'Production target count for the shift';
COMMENT ON COLUMN shift_targets.shift IS 'Shift name (e.g., "Day", "Night", "Swing")';
COMMENT ON COLUMN shift_targets.effective_date IS 'Date when this target becomes effective';

-- Index on asset_id for join performance
CREATE INDEX IF NOT EXISTS idx_shift_targets_asset_id ON shift_targets(asset_id);

-- Index on effective_date for date range queries
CREATE INDEX IF NOT EXISTS idx_shift_targets_effective_date ON shift_targets(effective_date);

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_shift_targets_updated_at ON shift_targets;
CREATE TRIGGER update_shift_targets_updated_at
    BEFORE UPDATE ON shift_targets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Enable RLS on all tables and create policies:
--   - Authenticated users can SELECT all rows
--   - Only service_role can INSERT, UPDATE, DELETE

-- Enable RLS on all tables
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE shift_targets ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: assets
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on assets" ON assets;
DROP POLICY IF EXISTS "Allow service_role full access on assets" ON assets;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on assets"
    ON assets FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on assets"
    ON assets FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: cost_centers
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on cost_centers" ON cost_centers;
DROP POLICY IF EXISTS "Allow service_role full access on cost_centers" ON cost_centers;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on cost_centers"
    ON cost_centers FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on cost_centers"
    ON cost_centers FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: shift_targets
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on shift_targets" ON shift_targets;
DROP POLICY IF EXISTS "Allow service_role full access on shift_targets" ON shift_targets;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on shift_targets"
    ON shift_targets FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on shift_targets"
    ON shift_targets FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check table exists and has correct columns:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name = 'assets';
--
-- Check foreign keys:
--   SELECT tc.constraint_name, tc.table_name, kcu.column_name,
--          ccu.table_name AS foreign_table_name,
--          ccu.column_name AS foreign_column_name
--   FROM information_schema.table_constraints AS tc
--   JOIN information_schema.key_column_usage AS kcu
--     ON tc.constraint_name = kcu.constraint_name
--   JOIN information_schema.constraint_column_usage AS ccu
--     ON ccu.constraint_name = tc.constraint_name
--   WHERE constraint_type = 'FOREIGN KEY';
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename IN ('assets', 'cost_centers', 'shift_targets');
