-- Story 9.11: Briefing Accuracy Metrics Table
-- Stores daily prediction accuracy metrics for trend tracking (AC#4)
--
-- This table enables:
-- - AC#4: Accuracy trend tracking over time
-- - Action Engine tuning feedback based on prediction performance
--
-- References:
-- - [Source: epic-9.md#Story-9.11]
-- - [Source: 9-11-morning-vs-actual-comparison.md#Dev Notes]

-- Create briefing_accuracy_metrics table for tracking prediction accuracy
CREATE TABLE IF NOT EXISTS public.briefing_accuracy_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    morning_briefing_id UUID,  -- nullable if no morning briefing
    eod_summary_id UUID,
    accuracy_percentage DECIMAL(5,2),
    false_positives INTEGER DEFAULT 0,
    misses INTEGER DEFAULT 0,
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    averted_count INTEGER DEFAULT 0,
    escalated_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, date)
);

-- Index for efficient trend queries
CREATE INDEX IF NOT EXISTS idx_briefing_accuracy_user_date
    ON public.briefing_accuracy_metrics(user_id, date DESC);

-- Index for accuracy analysis
CREATE INDEX IF NOT EXISTS idx_briefing_accuracy_date
    ON public.briefing_accuracy_metrics(date DESC);

-- Enable RLS
ALTER TABLE public.briefing_accuracy_metrics ENABLE ROW LEVEL SECURITY;

-- RLS policy: Users can only see their own accuracy metrics
CREATE POLICY "Users can view own accuracy metrics"
    ON public.briefing_accuracy_metrics
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS policy: System can insert accuracy metrics
CREATE POLICY "System can insert accuracy metrics"
    ON public.briefing_accuracy_metrics
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLS policy: System can update accuracy metrics
CREATE POLICY "System can update accuracy metrics"
    ON public.briefing_accuracy_metrics
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_briefing_accuracy_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists to allow re-running migration
DROP TRIGGER IF EXISTS briefing_accuracy_metrics_updated_at ON public.briefing_accuracy_metrics;

CREATE TRIGGER briefing_accuracy_metrics_updated_at
    BEFORE UPDATE ON public.briefing_accuracy_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_briefing_accuracy_updated_at();

-- Comment on table
COMMENT ON TABLE public.briefing_accuracy_metrics IS 'Daily prediction accuracy metrics for morning briefing vs actual outcomes (Story 9.11)';
COMMENT ON COLUMN public.briefing_accuracy_metrics.accuracy_percentage IS 'Prediction accuracy as percentage (0-100)';
COMMENT ON COLUMN public.briefing_accuracy_metrics.false_positives IS 'Count of predicted issues that did not occur';
COMMENT ON COLUMN public.briefing_accuracy_metrics.misses IS 'Count of issues that occurred but were not predicted';
COMMENT ON COLUMN public.briefing_accuracy_metrics.total_predictions IS 'Total number of concerns flagged in morning briefing';
COMMENT ON COLUMN public.briefing_accuracy_metrics.correct_predictions IS 'Predictions that materialized or escalated (true positives)';
COMMENT ON COLUMN public.briefing_accuracy_metrics.averted_count IS 'Issues that were successfully prevented';
COMMENT ON COLUMN public.briefing_accuracy_metrics.escalated_count IS 'Issues that were worse than predicted';
