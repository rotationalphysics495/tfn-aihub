-- Migration: Create Shift Summaries table
-- Story: 17.3 - Shift Summaries Data Model
-- Date: 2026-02-12
--
-- This migration creates the shift_summaries table:
--   - Stores per-shift (morning, afternoon, night) performance data
--   - Sits alongside daily_summaries for drill-down analysis
--   - Includes OEE sub-components (availability, performance, quality)
--
-- All tables include:
--   - UUID primary keys (auto-generated)
--   - Foreign key relationships to assets table
--   - Row Level Security (RLS) policies
--   - Performance indexes for common query patterns

-- ============================================================================
-- TABLE: shift_summaries
-- ============================================================================
-- Stores per-shift performance breakdowns populated alongside daily_summaries.
-- Three shifts per day per asset: morning, afternoon, night.
-- Immutable data — no updated_at column or update trigger needed.

CREATE TABLE IF NOT EXISTS shift_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    shift TEXT NOT NULL CHECK (shift IN ('morning', 'afternoon', 'night')),
    oee DECIMAL(5, 2),
    availability DECIMAL(5, 2),
    performance DECIMAL(5, 2),
    quality DECIMAL(5, 2),
    downtime_minutes INTEGER,
    units_produced INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT shift_summaries_asset_date_shift_unique UNIQUE (asset_id, date, shift)
);

-- Add comments for documentation
COMMENT ON TABLE shift_summaries IS 'Stores per-shift performance breakdowns with OEE sub-components for drill-down analysis';
COMMENT ON COLUMN shift_summaries.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN shift_summaries.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN shift_summaries.date IS 'Date of the shift (matches daily_summaries.report_date semantics)';
COMMENT ON COLUMN shift_summaries.shift IS 'Shift identifier: morning, afternoon, or night';
COMMENT ON COLUMN shift_summaries.oee IS 'Overall Equipment Effectiveness percentage for this shift (0.00-100.00)';
COMMENT ON COLUMN shift_summaries.availability IS 'Availability component of OEE (0.00-100.00)';
COMMENT ON COLUMN shift_summaries.performance IS 'Performance component of OEE (0.00-100.00)';
COMMENT ON COLUMN shift_summaries.quality IS 'Quality component of OEE (0.00-100.00)';
COMMENT ON COLUMN shift_summaries.downtime_minutes IS 'Total downtime in minutes for this shift';
COMMENT ON COLUMN shift_summaries.units_produced IS 'Number of units produced during this shift';
COMMENT ON COLUMN shift_summaries.created_at IS 'Timestamp when the record was created';

-- Index on asset_id for asset-specific queries
CREATE INDEX IF NOT EXISTS idx_shift_summaries_asset_id ON shift_summaries(asset_id);

-- Index on date for date range queries
CREATE INDEX IF NOT EXISTS idx_shift_summaries_date ON shift_summaries(date);

-- Composite index on (asset_id, date) for the most common query pattern
CREATE INDEX IF NOT EXISTS idx_shift_summaries_asset_date ON shift_summaries(asset_id, date);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Enable RLS and create policies matching daily_summaries pattern:
--   - Authenticated users can SELECT all rows
--   - Only service_role can INSERT, UPDATE, DELETE (for backend pipelines)

ALTER TABLE shift_summaries ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on shift_summaries" ON shift_summaries;
DROP POLICY IF EXISTS "Allow service_role full access on shift_summaries" ON shift_summaries;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on shift_summaries"
    ON shift_summaries FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on shift_summaries"
    ON shift_summaries FOR ALL
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
--   WHERE table_name = 'shift_summaries'
--   ORDER BY ordinal_position;
--
-- Check unique constraint:
--   SELECT constraint_name, constraint_type
--   FROM information_schema.table_constraints
--   WHERE table_name = 'shift_summaries';
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
--   WHERE constraint_type = 'FOREIGN KEY'
--     AND tc.table_name = 'shift_summaries';
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename = 'shift_summaries';
--
-- Check RLS is enabled:
--   SELECT tablename, rowsecurity
--   FROM pg_tables
--   WHERE tablename = 'shift_summaries';
--
-- Check RLS policies:
--   SELECT tablename, policyname, cmd, roles
--   FROM pg_policies
--   WHERE tablename = 'shift_summaries';
--
-- Check CHECK constraint on shift column:
--   SELECT conname, pg_get_constraintdef(oid)
--   FROM pg_constraint
--   WHERE conrelid = 'shift_summaries'::regclass
--     AND contype = 'c';
