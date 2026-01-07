-- Migration: Create smart_summaries and llm_usage tables
-- Story: 3.5 - Smart Summary Generator
-- AC: #6 - Summary Storage and Caching
-- AC: #10 - Token Usage Monitoring

-- =============================================================================
-- smart_summaries table
-- Stores AI-generated summaries with citations and metadata
-- =============================================================================

CREATE TABLE IF NOT EXISTS smart_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL UNIQUE,
    summary_text TEXT NOT NULL,
    citations_json JSONB DEFAULT '[]'::jsonb,  -- Structured citation references
    model_used VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    generation_duration_ms INTEGER DEFAULT 0,
    is_fallback BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast date lookup (primary access pattern)
CREATE INDEX IF NOT EXISTS idx_smart_summaries_date ON smart_summaries(date);

-- Index for created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_smart_summaries_created_at ON smart_summaries(created_at);

-- Enable Row Level Security
ALTER TABLE smart_summaries ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Authenticated users can read summaries
CREATE POLICY "Authenticated users can read summaries"
    ON smart_summaries FOR SELECT
    USING (auth.role() = 'authenticated');

-- RLS Policy: Service role can insert/update summaries (for API backend)
CREATE POLICY "Service role can manage summaries"
    ON smart_summaries FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_smart_summaries_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER smart_summaries_updated_at
    BEFORE UPDATE ON smart_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_smart_summaries_updated_at();

-- =============================================================================
-- llm_usage table
-- Tracks token usage for cost management (AC #10)
-- =============================================================================

CREATE TABLE IF NOT EXISTS llm_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for date-based aggregation queries
CREATE INDEX IF NOT EXISTS idx_llm_usage_date ON llm_usage(date);

-- Index for monthly aggregation
CREATE INDEX IF NOT EXISTS idx_llm_usage_date_provider ON llm_usage(date, provider);

-- Enable Row Level Security
ALTER TABLE llm_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Authenticated users can read usage data
CREATE POLICY "Authenticated users can read llm_usage"
    ON llm_usage FOR SELECT
    USING (auth.role() = 'authenticated');

-- RLS Policy: Service role can insert usage data
CREATE POLICY "Service role can insert llm_usage"
    ON llm_usage FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- =============================================================================
-- Comments for documentation
-- =============================================================================

COMMENT ON TABLE smart_summaries IS 'AI-generated daily summaries for Morning Report (Story 3.5)';
COMMENT ON COLUMN smart_summaries.date IS 'Report date (T-1), unique per day';
COMMENT ON COLUMN smart_summaries.summary_text IS 'Markdown-formatted summary text';
COMMENT ON COLUMN smart_summaries.citations_json IS 'Array of citation objects for NFR1 compliance';
COMMENT ON COLUMN smart_summaries.model_used IS 'LLM model identifier (e.g., gpt-4-turbo)';
COMMENT ON COLUMN smart_summaries.is_fallback IS 'True if fallback template was used instead of LLM';

COMMENT ON TABLE llm_usage IS 'Token usage tracking for LLM cost management (Story 3.5 AC#10)';
COMMENT ON COLUMN llm_usage.total_cost_usd IS 'Estimated cost based on token pricing';
