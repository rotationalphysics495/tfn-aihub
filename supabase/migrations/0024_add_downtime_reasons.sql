-- Migration: Add downtime_reasons JSONB column to daily_summaries
-- Purpose: Store detailed downtime reason breakdown for Pareto analysis (Epic 5)
-- Date: 2026-01-31
--
-- This column stores JSON object with reason codes as keys and minutes as values.
-- Example: {"Mechanical Failure": 45, "Changeover": 20, "Material Shortage": 15}

-- Add the downtime_reasons column to daily_summaries
ALTER TABLE daily_summaries
ADD COLUMN IF NOT EXISTS downtime_reasons JSONB DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN daily_summaries.downtime_reasons IS 'JSON object mapping reason codes to downtime minutes for Pareto analysis. Example: {"Mechanical Failure": 45, "Changeover": 20}';

-- Create index for querying specific reason codes (optional, for future analytics)
CREATE INDEX IF NOT EXISTS idx_daily_summaries_downtime_reasons
ON daily_summaries USING GIN (downtime_reasons);
