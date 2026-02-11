-- Migration: Create Products & Schedule tables
-- Story: 12.1 - Products & Schedule Data Model
-- Date: 2026-02-11
--
-- This migration creates three new tables for product-level production tracking:
--   - products: Product catalog (name, SKU, family, unit of measure)
--   - production_schedule: Planned production quantities per asset/product/date/shift
--   - production_actuals: Actual production quantities per asset/product/date/shift
--
-- All tables include:
--   - UUID primary keys (auto-generated)
--   - created_at/updated_at timestamps with auto-update triggers
--   - Row Level Security (RLS) policies
--   - Performance indexes

-- ============================================================================
-- TABLE: products
-- ============================================================================
-- Product catalog for tracking what is produced on each asset.

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    sku TEXT,
    product_family TEXT,
    unit_of_measure TEXT DEFAULT 'units',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE products IS 'Product catalog for tracking what is produced on each asset';
COMMENT ON COLUMN products.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN products.name IS 'Human-readable product name (e.g., "Colombian Single Origin")';
COMMENT ON COLUMN products.sku IS 'Stock keeping unit code (e.g., "COL-SO-12OZ"), nullable for initial seed data';
COMMENT ON COLUMN products.product_family IS 'Product grouping (e.g., "Single Origin", "Blend", "Grind")';
COMMENT ON COLUMN products.unit_of_measure IS 'Unit for quantity tracking (e.g., "units", "lbs", "bags")';

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: production_schedule
-- ============================================================================
-- Planned production quantities linking assets to products on specific dates/shifts.

CREATE TABLE IF NOT EXISTS production_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    scheduled_quantity INTEGER NOT NULL,
    scheduled_date DATE NOT NULL,
    shift TEXT,
    production_order_ref TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE production_schedule IS 'Planned production quantities per asset/product/date/shift';
COMMENT ON COLUMN production_schedule.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN production_schedule.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN production_schedule.product_id IS 'Foreign key reference to products table';
COMMENT ON COLUMN production_schedule.scheduled_quantity IS 'Planned production quantity for this schedule entry';
COMMENT ON COLUMN production_schedule.scheduled_date IS 'Date of scheduled production';
COMMENT ON COLUMN production_schedule.shift IS 'Shift name (e.g., "morning", "afternoon", "night")';
COMMENT ON COLUMN production_schedule.production_order_ref IS 'Production order reference for future AX/D365 integration';

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_production_schedule_updated_at ON production_schedule;
CREATE TRIGGER update_production_schedule_updated_at
    BEFORE UPDATE ON production_schedule
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: production_actuals
-- ============================================================================
-- Actual production quantities linking assets to products on specific dates/shifts.

CREATE TABLE IF NOT EXISTS production_actuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    actual_quantity INTEGER NOT NULL,
    production_date DATE NOT NULL,
    shift TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE production_actuals IS 'Actual production quantities per asset/product/date/shift';
COMMENT ON COLUMN production_actuals.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN production_actuals.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN production_actuals.product_id IS 'Foreign key reference to products table';
COMMENT ON COLUMN production_actuals.actual_quantity IS 'Actual production quantity recorded';
COMMENT ON COLUMN production_actuals.production_date IS 'Date of actual production';
COMMENT ON COLUMN production_actuals.shift IS 'Shift name (e.g., "morning", "afternoon", "night")';

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_production_actuals_updated_at ON production_actuals;
CREATE TRIGGER update_production_actuals_updated_at
    BEFORE UPDATE ON production_actuals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Indexes on production_schedule for query performance
CREATE INDEX IF NOT EXISTS idx_production_schedule_asset_id ON production_schedule(asset_id);
CREATE INDEX IF NOT EXISTS idx_production_schedule_product_id ON production_schedule(product_id);
CREATE INDEX IF NOT EXISTS idx_production_schedule_scheduled_date ON production_schedule(scheduled_date);

-- Indexes on production_actuals for query performance
CREATE INDEX IF NOT EXISTS idx_production_actuals_asset_id ON production_actuals(asset_id);
CREATE INDEX IF NOT EXISTS idx_production_actuals_product_id ON production_actuals(product_id);
CREATE INDEX IF NOT EXISTS idx_production_actuals_production_date ON production_actuals(production_date);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Enable RLS on all tables and create policies:
--   - Authenticated users can SELECT all rows
--   - Only service_role can INSERT, UPDATE, DELETE

-- Enable RLS on all tables
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_actuals ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: products
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on products" ON products;
DROP POLICY IF EXISTS "Allow service_role full access on products" ON products;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on products"
    ON products FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on products"
    ON products FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: production_schedule
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on production_schedule" ON production_schedule;
DROP POLICY IF EXISTS "Allow service_role full access on production_schedule" ON production_schedule;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on production_schedule"
    ON production_schedule FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on production_schedule"
    ON production_schedule FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: production_actuals
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on production_actuals" ON production_actuals;
DROP POLICY IF EXISTS "Allow service_role full access on production_actuals" ON production_actuals;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on production_actuals"
    ON production_actuals FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on production_actuals"
    ON production_actuals FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check products table columns:
--   SELECT column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'products'
--   ORDER BY ordinal_position;
--
-- Check production_schedule table columns:
--   SELECT column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'production_schedule'
--   ORDER BY ordinal_position;
--
-- Check production_actuals table columns:
--   SELECT column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'production_actuals'
--   ORDER BY ordinal_position;
--
-- Check foreign keys on production_schedule:
--   SELECT tc.constraint_name, kcu.column_name,
--          ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
--   FROM information_schema.table_constraints tc
--   JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
--   JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
--   WHERE tc.table_name = 'production_schedule' AND tc.constraint_type = 'FOREIGN KEY';
--
-- Check foreign keys on production_actuals:
--   SELECT tc.constraint_name, kcu.column_name,
--          ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
--   FROM information_schema.table_constraints tc
--   JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
--   JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
--   WHERE tc.table_name = 'production_actuals' AND tc.constraint_type = 'FOREIGN KEY';
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename IN ('products', 'production_schedule', 'production_actuals');
--
-- Check RLS is enabled:
--   SELECT tablename, rowsecurity
--   FROM pg_tables
--   WHERE tablename IN ('products', 'production_schedule', 'production_actuals');
--
-- Check RLS policies:
--   SELECT tablename, policyname, permissive, roles, cmd, qual
--   FROM pg_policies
--   WHERE tablename IN ('products', 'production_schedule', 'production_actuals');
