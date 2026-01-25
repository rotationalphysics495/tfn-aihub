-- Migration: Create Citation Logs table for audit trail
-- Story: 4.5 - Cited Response Generation
-- Date: 2026-01-07
--
-- This migration creates the citation audit log table:
--   - citation_logs: Stores all citation-response pairs for NFR1 compliance review
--
-- Implements:
--   - AC#7: Audit log records all citation-response pairs for compliance review
--   - AC#3: Grounding failures trigger alert for manual review
--
-- All tables include:
--   - UUID primary keys (auto-generated)
--   - Row Level Security (RLS) policies
--   - Performance indexes for common query patterns

-- ============================================================================
-- TABLE: citation_logs
-- ============================================================================
-- Stores all AI response citations for audit and compliance review.
-- Used for NFR1 compliance: Every factual recommendation must include at least one citation.

CREATE TABLE IF NOT EXISTS citation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id UUID,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    grounding_score DECIMAL(3,2) NOT NULL CHECK (grounding_score >= 0 AND grounding_score <= 1),
    ungrounded_claims JSONB DEFAULT '[]'::jsonb,
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE citation_logs IS 'Audit log for AI response citations (Story 4.5 - NFR1 compliance)';
COMMENT ON COLUMN citation_logs.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN citation_logs.response_id IS 'Unique identifier of the AI response';
COMMENT ON COLUMN citation_logs.user_id IS 'User who made the query (references auth.users)';
COMMENT ON COLUMN citation_logs.session_id IS 'Session identifier for conversation tracking';
COMMENT ON COLUMN citation_logs.query_text IS 'Original user query text';
COMMENT ON COLUMN citation_logs.response_text IS 'Full AI response text with citations';
COMMENT ON COLUMN citation_logs.citations IS 'Array of citation objects (JSONB)';
COMMENT ON COLUMN citation_logs.grounding_score IS 'Overall grounding confidence score (0.0-1.0)';
COMMENT ON COLUMN citation_logs.ungrounded_claims IS 'Array of claims that could not be grounded';
COMMENT ON COLUMN citation_logs.validated_at IS 'When grounding validation was performed';
COMMENT ON COLUMN citation_logs.created_at IS 'When the log entry was created';

-- ============================================================================
-- INDEXES: Performance optimization
-- ============================================================================

-- Index for filtering by grounding score (find low-grounding responses)
CREATE INDEX IF NOT EXISTS idx_citation_logs_grounding
ON citation_logs(grounding_score);

-- Index for user-based queries (compliance review by user)
CREATE INDEX IF NOT EXISTS idx_citation_logs_user
ON citation_logs(user_id);

-- Index for temporal queries (recent logs)
CREATE INDEX IF NOT EXISTS idx_citation_logs_created
ON citation_logs(created_at DESC);

-- Index for finding responses by ID
CREATE INDEX IF NOT EXISTS idx_citation_logs_response
ON citation_logs(response_id);

-- Composite index for user + time queries
CREATE INDEX IF NOT EXISTS idx_citation_logs_user_created
ON citation_logs(user_id, created_at DESC);

-- ============================================================================
-- TABLE: system_alerts (if not exists)
-- ============================================================================
-- Create system_alerts table for low grounding score notifications
-- This table may already exist from other stories

CREATE TABLE IF NOT EXISTS system_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES auth.users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for unacknowledged alerts
CREATE INDEX IF NOT EXISTS idx_system_alerts_unacknowledged
ON system_alerts(acknowledged, created_at DESC)
WHERE acknowledged = FALSE;

-- Add index for alert type
CREATE INDEX IF NOT EXISTS idx_system_alerts_type
ON system_alerts(alert_type);

COMMENT ON TABLE system_alerts IS 'System alerts for monitoring and notifications';

-- ============================================================================
-- TRIGGER FUNCTION: Alert on low grounding scores
-- ============================================================================
-- AC#3, AC#7: Grounding failures trigger alert for manual review

CREATE OR REPLACE FUNCTION alert_low_grounding()
RETURNS TRIGGER AS $$
BEGIN
    -- Alert if grounding score is below minimum threshold (0.6)
    IF NEW.grounding_score < 0.6 THEN
        INSERT INTO system_alerts (
            alert_type,
            severity,
            message,
            metadata
        )
        VALUES (
            'low_grounding_score',
            'warning',
            format(
                'Response %s has low grounding score: %s. Query: %s',
                NEW.response_id,
                NEW.grounding_score,
                LEFT(NEW.query_text, 100)
            ),
            jsonb_build_object(
                'response_id', NEW.response_id,
                'grounding_score', NEW.grounding_score,
                'user_id', NEW.user_id,
                'ungrounded_claims_count', jsonb_array_length(COALESCE(NEW.ungrounded_claims, '[]'::jsonb)),
                'query_preview', LEFT(NEW.query_text, 200)
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for low grounding alerts
DROP TRIGGER IF EXISTS citation_grounding_alert ON citation_logs;
CREATE TRIGGER citation_grounding_alert
AFTER INSERT ON citation_logs
FOR EACH ROW EXECUTE FUNCTION alert_low_grounding();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Enable RLS on citation_logs and create policies

ALTER TABLE citation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_alerts ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: citation_logs
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Authenticated users can view their own citation logs" ON citation_logs;
DROP POLICY IF EXISTS "Allow service_role full access on citation_logs" ON citation_logs;

-- Authenticated users can view their own logs
CREATE POLICY "Authenticated users can view their own citation logs"
    ON citation_logs FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Service role has full access for backend operations
CREATE POLICY "Allow service_role full access on citation_logs"
    ON citation_logs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: system_alerts
-- ============================================================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Authenticated users can view system alerts" ON system_alerts;
DROP POLICY IF EXISTS "Allow service_role full access on system_alerts" ON system_alerts;

-- Authenticated users can view alerts (for admin dashboards)
CREATE POLICY "Authenticated users can view system alerts"
    ON system_alerts FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access
CREATE POLICY "Allow service_role full access on system_alerts"
    ON system_alerts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- HELPER FUNCTION: Get citation audit summary
-- ============================================================================
-- Returns summary statistics for citation audit review

CREATE OR REPLACE FUNCTION get_citation_audit_summary(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '7 days',
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    p_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
    total_responses BIGINT,
    avg_grounding_score DECIMAL(3,2),
    low_grounding_count BIGINT,
    fully_grounded_count BIGINT,
    total_citations BIGINT,
    avg_citations_per_response DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT AS total_responses,
        ROUND(AVG(cl.grounding_score), 2)::DECIMAL(3,2) AS avg_grounding_score,
        COUNT(*) FILTER (WHERE cl.grounding_score < 0.6)::BIGINT AS low_grounding_count,
        COUNT(*) FILTER (WHERE cl.grounding_score >= 0.8)::BIGINT AS fully_grounded_count,
        SUM(jsonb_array_length(COALESCE(cl.citations, '[]'::jsonb)))::BIGINT AS total_citations,
        ROUND(
            AVG(jsonb_array_length(COALESCE(cl.citations, '[]'::jsonb)))::DECIMAL,
            2
        )::DECIMAL(5,2) AS avg_citations_per_response
    FROM citation_logs cl
    WHERE cl.created_at >= p_start_date
      AND cl.created_at <= p_end_date
      AND (p_user_id IS NULL OR cl.user_id = p_user_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check tables exist and have correct columns:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name IN ('citation_logs', 'system_alerts')
--   ORDER BY table_name, ordinal_position;
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename IN ('citation_logs', 'system_alerts');
--
-- Check RLS is enabled:
--   SELECT tablename, rowsecurity
--   FROM pg_tables
--   WHERE tablename IN ('citation_logs', 'system_alerts');
--
-- Test the audit summary function:
--   SELECT * FROM get_citation_audit_summary();
--
-- Check the trigger exists:
--   SELECT trigger_name, event_manipulation, action_statement
--   FROM information_schema.triggers
--   WHERE trigger_name = 'citation_grounding_alert';
