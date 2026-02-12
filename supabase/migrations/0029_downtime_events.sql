-- Downtime Events Table
-- Stores individual downtime event records, decomposing the aggregate
-- downtime_minutes and downtime_reasons from daily_summaries into discrete,
-- queryable rows for Pareto analysis by reason code.

CREATE TABLE IF NOT EXISTS downtime_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    shift TEXT CHECK (shift IN ('morning', 'afternoon', 'night')),
    reason_code TEXT NOT NULL,
    reason_detail TEXT,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    is_planned BOOLEAN DEFAULT false,
    source_system TEXT DEFAULT 'manual',
    source_event_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_downtime_events_asset_id ON downtime_events(asset_id);
CREATE INDEX IF NOT EXISTS idx_downtime_events_event_date ON downtime_events(event_date);
CREATE INDEX IF NOT EXISTS idx_downtime_events_reason_code ON downtime_events(reason_code);
CREATE INDEX IF NOT EXISTS idx_downtime_events_asset_event_date ON downtime_events(asset_id, event_date);

-- Auto-update updated_at (reuses existing function from migration 0002)
CREATE TRIGGER update_downtime_events_updated_at
    BEFORE UPDATE ON downtime_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS
ALTER TABLE downtime_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated read access on downtime_events" ON downtime_events;
CREATE POLICY "Allow authenticated read access on downtime_events"
    ON downtime_events FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Allow service_role full access on downtime_events" ON downtime_events;
CREATE POLICY "Allow service_role full access on downtime_events"
    ON downtime_events FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Documentation
COMMENT ON TABLE downtime_events IS 'Individual downtime event records with reason codes for Pareto analysis';
COMMENT ON COLUMN downtime_events.id IS 'Unique identifier for the downtime event';
COMMENT ON COLUMN downtime_events.asset_id IS 'Foreign key to assets table - the machine that experienced downtime';
COMMENT ON COLUMN downtime_events.event_date IS 'Date the downtime event occurred';
COMMENT ON COLUMN downtime_events.shift IS 'Shift during which the event occurred: morning, afternoon, or night';
COMMENT ON COLUMN downtime_events.reason_code IS 'Standard reason code: Mechanical, Changeover, Material Shortage, Quality Hold, Operator Unavailable, Planned Maintenance';
COMMENT ON COLUMN downtime_events.reason_detail IS 'Freeform description of the downtime event';
COMMENT ON COLUMN downtime_events.duration_minutes IS 'Duration of the downtime event in minutes';
COMMENT ON COLUMN downtime_events.is_planned IS 'Whether the downtime was planned (true for Changeover and Planned Maintenance)';
COMMENT ON COLUMN downtime_events.source_system IS 'System that created the record (default: manual)';
COMMENT ON COLUMN downtime_events.source_event_id IS 'External system event ID for integration (e.g., Redzone)';
COMMENT ON COLUMN downtime_events.created_at IS 'Timestamp when the record was created';
COMMENT ON COLUMN downtime_events.updated_at IS 'Timestamp when the record was last updated';
