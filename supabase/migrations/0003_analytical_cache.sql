-- Migration: Create Analytical Cache tables
-- Story: 1.4 - Analytical Cache Schema
-- Date: 2026-01-06
--
-- This migration creates the Analytical Cache layer tables:
--   - daily_summaries: T-1 processed reports with OEE metrics, waste data, financial loss
--   - live_snapshots: 15-minute polling data for live production monitoring
--   - safety_events: Persistent log of safety incidents
--
-- All tables include:
--   - UUID primary keys (auto-generated)
--   - Foreign key relationships to assets table
--   - Row Level Security (RLS) policies
--   - Performance indexes for common query patterns

-- ============================================================================
-- TABLE: daily_summaries
-- ============================================================================
-- Stores T-1 processed daily reports populated by Pipeline A ("Morning Report")
-- at 06:00 AM via Railway Cron.

CREATE TABLE IF NOT EXISTS daily_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    oee_percentage DECIMAL(5, 2),
    actual_output INTEGER,
    target_output INTEGER,
    downtime_minutes INTEGER,
    waste_count INTEGER,
    financial_loss_dollars DECIMAL(12, 2),
    smart_summary_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT daily_summaries_asset_report_date_unique UNIQUE (asset_id, report_date)
);

-- Add comments for documentation
COMMENT ON TABLE daily_summaries IS 'Stores T-1 processed daily reports with OEE metrics, waste data, and financial loss calculations';
COMMENT ON COLUMN daily_summaries.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN daily_summaries.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN daily_summaries.report_date IS 'Date of the daily report (T-1 from processing date)';
COMMENT ON COLUMN daily_summaries.oee_percentage IS 'Overall Equipment Effectiveness percentage (0.00-100.00)';
COMMENT ON COLUMN daily_summaries.actual_output IS 'Actual production output count';
COMMENT ON COLUMN daily_summaries.target_output IS 'Target production output count';
COMMENT ON COLUMN daily_summaries.downtime_minutes IS 'Total downtime in minutes';
COMMENT ON COLUMN daily_summaries.waste_count IS 'Number of waste/rejected items';
COMMENT ON COLUMN daily_summaries.financial_loss_dollars IS 'Calculated financial loss in USD';
COMMENT ON COLUMN daily_summaries.smart_summary_text IS 'AI-generated summary text for the report';

-- Index on report_date for date range queries
CREATE INDEX IF NOT EXISTS idx_daily_summaries_report_date ON daily_summaries(report_date);

-- Composite index on (asset_id, report_date) for asset-specific date queries
CREATE INDEX IF NOT EXISTS idx_daily_summaries_asset_report_date ON daily_summaries(asset_id, report_date);

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_daily_summaries_updated_at ON daily_summaries;
CREATE TRIGGER update_daily_summaries_updated_at
    BEFORE UPDATE ON daily_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: live_snapshots
-- ============================================================================
-- Stores 15-minute polling data populated by Pipeline B ("Live Pulse")
-- via Python Background Scheduler. This is ephemeral/time-series data.

CREATE TABLE IF NOT EXISTS live_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    current_output INTEGER,
    target_output INTEGER,
    output_variance INTEGER GENERATED ALWAYS AS (current_output - target_output) STORED,
    status TEXT NOT NULL CHECK (status IN ('on_target', 'behind', 'ahead')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE live_snapshots IS 'Stores 15-minute polling data for live production monitoring';
COMMENT ON COLUMN live_snapshots.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN live_snapshots.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN live_snapshots.snapshot_timestamp IS 'Timestamp when the snapshot was taken';
COMMENT ON COLUMN live_snapshots.current_output IS 'Current production output at snapshot time';
COMMENT ON COLUMN live_snapshots.target_output IS 'Target production output at snapshot time';
COMMENT ON COLUMN live_snapshots.output_variance IS 'Calculated difference (current - target), auto-computed';
COMMENT ON COLUMN live_snapshots.status IS 'Production status: on_target, behind, or ahead';

-- Index on snapshot_timestamp for time-series queries (supports NFR2 <60s latency)
CREATE INDEX IF NOT EXISTS idx_live_snapshots_snapshot_timestamp ON live_snapshots(snapshot_timestamp);

-- Composite index on (asset_id, snapshot_timestamp) for asset-specific time queries
CREATE INDEX IF NOT EXISTS idx_live_snapshots_asset_snapshot_timestamp ON live_snapshots(asset_id, snapshot_timestamp);

-- ============================================================================
-- TABLE: safety_events
-- ============================================================================
-- Persistent log of safety incidents detected by Pipeline B when
-- reason_code = 'Safety Issue' is encountered.

CREATE TABLE IF NOT EXISTS safety_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    reason_code TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE safety_events IS 'Persistent log of safety incidents for tracking and resolution';
COMMENT ON COLUMN safety_events.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN safety_events.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN safety_events.event_timestamp IS 'Timestamp when the safety event occurred';
COMMENT ON COLUMN safety_events.reason_code IS 'Code identifying the type of safety event';
COMMENT ON COLUMN safety_events.severity IS 'Severity level: low, medium, high, or critical';
COMMENT ON COLUMN safety_events.description IS 'Detailed description of the safety event';
COMMENT ON COLUMN safety_events.is_resolved IS 'Whether the safety event has been resolved';
COMMENT ON COLUMN safety_events.resolved_at IS 'Timestamp when the event was resolved';
COMMENT ON COLUMN safety_events.resolved_by IS 'User ID who resolved the event (references auth.users)';

-- Index on event_timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_safety_events_event_timestamp ON safety_events(event_timestamp);

-- Composite index on (asset_id, is_resolved) for filtering unresolved events per asset
CREATE INDEX IF NOT EXISTS idx_safety_events_asset_is_resolved ON safety_events(asset_id, is_resolved);

-- Index on severity for filtering by severity level
CREATE INDEX IF NOT EXISTS idx_safety_events_severity ON safety_events(severity);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Enable RLS on all tables and create policies:
--   - Authenticated users can SELECT all rows
--   - Only service_role can INSERT, UPDATE, DELETE (for backend pipelines)

-- Enable RLS on all tables
ALTER TABLE daily_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE live_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE safety_events ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: daily_summaries
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on daily_summaries" ON daily_summaries;
DROP POLICY IF EXISTS "Allow service_role full access on daily_summaries" ON daily_summaries;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on daily_summaries"
    ON daily_summaries FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on daily_summaries"
    ON daily_summaries FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: live_snapshots
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on live_snapshots" ON live_snapshots;
DROP POLICY IF EXISTS "Allow service_role full access on live_snapshots" ON live_snapshots;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on live_snapshots"
    ON live_snapshots FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on live_snapshots"
    ON live_snapshots FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: safety_events
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read access on safety_events" ON safety_events;
DROP POLICY IF EXISTS "Allow service_role full access on safety_events" ON safety_events;

-- Authenticated users can SELECT
CREATE POLICY "Allow authenticated read access on safety_events"
    ON safety_events FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on safety_events"
    ON safety_events FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check tables exist and have correct columns:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name IN ('daily_summaries', 'live_snapshots', 'safety_events')
--   ORDER BY table_name, ordinal_position;
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
--     AND tc.table_name IN ('daily_summaries', 'live_snapshots', 'safety_events');
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename IN ('daily_summaries', 'live_snapshots', 'safety_events');
--
-- Check RLS is enabled:
--   SELECT tablename, rowsecurity
--   FROM pg_tables
--   WHERE tablename IN ('daily_summaries', 'live_snapshots', 'safety_events');
--
-- Check RLS policies:
--   SELECT tablename, policyname, cmd, roles
--   FROM pg_policies
--   WHERE tablename IN ('daily_summaries', 'live_snapshots', 'safety_events');
